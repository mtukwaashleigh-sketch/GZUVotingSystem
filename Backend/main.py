import os
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form
)

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles

from starlette.middleware.sessions import SessionMiddleware

import bcrypt

from database import (
    SessionLocal,
    engine,
    Base
)

from models import (
    Voter,
    Election,
    Candidate,
    VotingRecord,
    Vote,
    CandidateNomination,
    CandidateProfile,
    InstitutionalIdentity
)

from admin import router as admin_router
from admin_auth import auth_router
from admin_auth import api_router as admin_api_router, require_admin_api

from blockchain import (
    voting_contract,
    submit_vote,
    web3,
    sync_database_to_blockchain,
    add_candidate_to_blockchain,
    get_blockchain_election_count,
    get_blockchain_election_status,
    get_blockchain_candidate_count,
    get_blockchain_candidate,
)


# ============================================================
# DATABASE
# ============================================================

Base.metadata.create_all(
    bind=engine
)

# Add the withdrawal flag to existing installations without dropping or resetting data.
# create_all() does not add columns to tables that already exist.
try:
    candidate_columns = {column["name"] for column in inspect(engine).get_columns("candidates")}
    if "is_withdrawn" not in candidate_columns:
        with engine.begin() as connection:
            connection.execute(text(
                "ALTER TABLE candidates ADD COLUMN is_withdrawn BOOLEAN NOT NULL DEFAULT FALSE"
            ))
except Exception as migration_error:
    # Fail loudly rather than run the application with withdrawal checks unavailable.
    raise RuntimeError(
        "Could not apply the candidates.is_withdrawn database migration. "
        "Check database permissions and schema."
    ) from migration_error

# Add the nomination identity mapping hash without deleting or resetting records.
try:
    nomination_columns = {column["name"] for column in inspect(engine).get_columns("candidate_nominations")}
    if "identity_mapping_hash" not in nomination_columns:
        with engine.begin() as connection:
            connection.execute(text(
                "ALTER TABLE candidate_nominations ADD COLUMN identity_mapping_hash VARCHAR NULL"
            ))
except Exception as migration_error:
    raise RuntimeError(
        "Could not apply the candidate_nominations.identity_mapping_hash migration. "
        "Check database permissions and schema."
    ) from migration_error


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="GZU Election Management System API"
)

UPLOAD_DIR = BASE_DIR / "uploads" / "candidate_photos"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/candidate-photos", StaticFiles(directory=str(UPLOAD_DIR)), name="candidate-photos")


# ============================================================
# SESSION MIDDLEWARE
# ============================================================

SESSION_SECRET = os.getenv("SESSION_SECRET", "")
if len(SESSION_SECRET) < 32:
    raise RuntimeError(
        "SESSION_SECRET is missing or too short. Set a random secret of at least 32 characters in .env."
    )

COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").strip().lower() == "true"

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    max_age=30 * 60,
    same_site="lax",
    https_only=COOKIE_SECURE,
)


# ============================================================
# ADMIN ROUTES
# ============================================================

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(admin_api_router)


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    if request.url.path.startswith("/admin"):
        response.headers.setdefault("Cache-Control", "no-store")
    return response


# ============================================================
# DATABASE SESSION
# ============================================================

def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ============================================================
# SAFE BLOCKCHAIN MAPPING VALIDATION
# ============================================================

def _normalise_mapping_text(value):
    """Normalise labels for comparison without treating different titles as equal."""
    return " ".join(str(value or "").split()).casefold()


def _verify_blockchain_election_mapping(election):
    """Return the mapped chain ID/status only when the election title agrees.

    This deliberately does not guess or silently remap elections. A candidate
    appearing on another election is not proof that the elections are the same.
    """
    chain_id = election.blockchain_election_id
    if chain_id is None or int(chain_id) < 1:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Election '{election.title}' (SQLite ID {election.id}) has no valid "
                "blockchain election mapping. No vote was submitted. Run the mapping "
                "diagnostic and verify the correct election before repairing it."
            ),
        )

    try:
        chain_count = int(get_blockchain_election_count())
        if int(chain_id) > chain_count:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Election mapping conflict: PostgreSQL election {election.id} points "
                    f"to blockchain election {chain_id}, but the connected blockchain "
                    f"contains only {chain_count} elections. No transaction was sent."
                ),
            )
        chain_status = get_blockchain_election_status(int(chain_id))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not verify the blockchain election mapping: {type(exc).__name__}: {exc}",
        ) from exc

    if _normalise_mapping_text(chain_status.get("title")) != _normalise_mapping_text(election.title):
        raise HTTPException(
            status_code=409,
            detail=(
                f"Election mapping conflict: PostgreSQL election {election.id} is titled "
                f"'{election.title}', but its stored blockchain mapping points to "
                f"blockchain election {chain_id}, titled '{chain_status.get('title')}'. "
                "No blockchain transaction was sent. Do not change this mapping just "
                "because a candidate name matches; verify the election identity first."
            ),
        )

    return int(chain_id), chain_status


def _ensure_candidate_blockchain_mapping(db, election, candidate, verified_chain_id=None):
    """Validate or safely repair a candidate ID inside the verified election only."""
    if verified_chain_id is None:
        verified_chain_id, _ = _verify_blockchain_election_mapping(election)

    try:
        count = int(get_blockchain_candidate_count(verified_chain_id))
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not read blockchain candidates: {type(exc).__name__}: {exc}",
        ) from exc

    expected_name = _normalise_mapping_text(candidate.name)
    expected_position = _normalise_mapping_text(candidate.position)
    stored_id = candidate.blockchain_candidate_id

    # Candidate IDs are scoped to an election. Never return an ID that is
    # already mapped to another database candidate in this same election.
    mapped_elsewhere = {
        int(row[0])
        for row in db.query(Candidate.blockchain_candidate_id)
        .filter(
            Candidate.election_id == election.id,
            Candidate.blockchain_candidate_id.isnot(None),
            Candidate.id != candidate.id,
        )
        .all()
    }

    if (
        stored_id is not None
        and int(stored_id) > 0
        and int(stored_id) <= count
        and int(stored_id) not in mapped_elsewhere
    ):
        try:
            chain_candidate = get_blockchain_candidate(verified_chain_id, int(stored_id))
            if (
                _normalise_mapping_text(chain_candidate.get("name")) == expected_name
                and _normalise_mapping_text(chain_candidate.get("position")) == expected_position
            ):
                return int(stored_id)
        except Exception:
            # The exact-name search below can repair a stale candidate ID safely.
            pass

    matches = []
    for on_chain_id in range(1, count + 1):
        if on_chain_id in mapped_elsewhere:
            continue
        try:
            chain_candidate = get_blockchain_candidate(verified_chain_id, on_chain_id)
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=(
                    f"Could not verify blockchain candidate {on_chain_id}: "
                    f"{type(exc).__name__}: {exc}"
                ),
            ) from exc
        if (
            _normalise_mapping_text(chain_candidate.get("name")) == expected_name
            and _normalise_mapping_text(chain_candidate.get("position")) == expected_position
        ):
            matches.append(on_chain_id)

    if len(matches) == 1:
        candidate.blockchain_candidate_id = matches[0]
        try:
            db.commit()
            db.refresh(candidate)
        except Exception as exc:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="The verified candidate mapping could not be saved to SQLite.",
            ) from exc
        print(
            f"Repaired candidate mapping: SQLite candidate {candidate.id} -> "
            f"blockchain election {verified_chain_id}, candidate {matches[0]}"
        )
        return matches[0]

    if len(matches) > 1:
        detail = (
            f"Candidate '{candidate.name}' ({candidate.position}) appears more than "
            f"once on blockchain election {verified_chain_id}. The system will not "
            "guess which on-chain candidate is correct."
        )
    else:
        detail = (
            f"Candidate '{candidate.name}' ({candidate.position}) is not present on "
            f"the verified blockchain election {verified_chain_id}. The system will "
            "not submit a vote using candidate ID 0 or a candidate from another election."
        )
    raise HTTPException(status_code=409, detail=detail)


# ============================================================
# STARTUP SYNCHRONIZATION
# ============================================================

@app.on_event("startup")
def synchronize_blockchain():

    print("")
    print("==============================================")
    print("STARTING BLOCKCHAIN SYNCHRONIZATION")
    print("==============================================")

    db = SessionLocal()

    try:

        sync_database_to_blockchain(
            db
        )

    except Exception as e:

        print("")
        print(
            "WARNING: Blockchain synchronization "
            "failed."
        )

        print(
            type(e).__name__
        )

        print(
            str(e)
        )

        print(
            "The FastAPI server will continue running."
        )

    finally:

        db.close()

    print("==============================================")
    print(
        "BLOCKCHAIN SYNCHRONIZATION FINISHED"
    )
    print("==============================================")
    print("")


# ============================================================
# LOGIN
# ============================================================

@app.post("/login")
def login(
    email: str,
    password: str,
    db: Session = Depends(get_db)
):

    voter = (
        db.query(Voter)
        .filter(
            Voter.email == email
        )
        .first()
    )

    if not voter:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    password_matches = bcrypt.checkpw(
        password.encode("utf-8"),
        voter.password.encode("utf-8")
    )

    if not password_matches:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    identifier = (voter.student_id or "").strip().upper()
    identity = (
        db.query(InstitutionalIdentity)
        .filter(InstitutionalIdentity.identifier == identifier)
        .first()
    )

    # Do not invent or trust a manually entered name when Registry/HR has no
    # matching record. The user may sign in, but cannot submit a nomination
    # until the official roster is imported and this identity is verified.
    if identity:
        official_name = (identity.full_name or "").strip()
        if not official_name:
            identity = None
        else:
            voter.full_name = official_name
            voter.identity_type = identity.identity_type
            db.commit()

    return {
        "message": "Login successful",
        "student_id": identifier,
        "full_name": (identity.full_name or "").strip() if identity else "",
        "identity_type": identity.identity_type if identity else None,
        "identity_verified": bool(identity),
        "email": voter.email
    }


# ============================================================
# GET ELECTIONS
# ============================================================

@app.get("/elections")
def get_elections(
    db: Session = Depends(get_db)
):

    # Voter-facing list excludes cancelled and archived elections. Closed
    # elections remain available so eligible voters can view final results.
    elections = (
        db.query(Election)
        .filter(Election.is_deleted == False, Election.status != "cancelled")
        .order_by(Election.id)
        .all()
    )

    return elections


# ============================================================
# GET CANDIDATES
# ============================================================

@app.get(
    "/elections/{election_id}/candidates"
)
def get_candidates(
    election_id: int,
    db: Session = Depends(get_db)
):

    election = (
        db.query(Election)
        .filter(
            Election.id == election_id
        )
        .first()
    )

    if not election or election.is_deleted:
        raise HTTPException(status_code=404, detail="Election not found")
    blockchain_id, _chain_status = _verify_blockchain_election_mapping(election)

    if election.status == "cancelled":
        raise HTTPException(
            status_code=409,
            detail="Candidates are not available for a cancelled election."
        )

    candidates = (
        db.query(Candidate)
        .filter(
            Candidate.election_id == election_id
        )
        .order_by(Candidate.id)
        .all()
    )

    result = []
    for candidate in candidates:
        verified_candidate_id = _ensure_candidate_blockchain_mapping(
            db, election, candidate, verified_chain_id=blockchain_id
        )
        profile = db.query(CandidateProfile).filter(CandidateProfile.candidate_id == candidate.id).first()
        result.append({
            "id": candidate.id, "election_id": candidate.election_id,
            "name": candidate.name, "position": candidate.position,
            "blockchain_candidate_id": verified_candidate_id,
            "photo_url": f"/candidate-photos/{profile.photo_path}" if profile and profile.photo_path else None,
            "faculty": profile.faculty if profile else None,
            "department": profile.department if profile else None,
            "programme": profile.programme if profile else None,
            "year_of_study": profile.year_of_study if profile else None,
            "manifesto": profile.manifesto if profile else None,
            "experience": profile.experience if profile else None,
        })
    return result


# ============================================================
# ============================================================
# CANDIDATE NOMINATIONS AND PROFILES
# ============================================================

def _nomination_payload(item, db=None):
    linked_candidate = None
    if db is not None and item.candidate_id is not None:
        linked_candidate = db.query(Candidate).filter(Candidate.id == item.candidate_id).first()
    return {
        "id": item.id, "student_id": item.student_id, "election_id": item.election_id,
        "position": item.position, "full_name": item.full_name, "faculty": item.faculty,
        "department": item.department, "programme": item.programme,
        "year_of_study": item.year_of_study, "manifesto": item.manifesto,
        "experience": item.experience, "photo_url": f"/candidate-photos/{item.photo_path}",
        "status": item.status, "admin_feedback": item.admin_feedback,
        "candidate_id": item.candidate_id,
        "candidate_withdrawn": bool(linked_candidate and linked_candidate.is_withdrawn),
        "created_at": item.created_at, "reviewed_at": item.reviewed_at,
    }


@app.post("/nominations")
async def submit_candidate_nomination(
    student_id: str = Form(...), election_id: int = Form(...), position: str = Form(...),
    full_name: str = Form(""), faculty: str = Form(...), department: str = Form(...),
    programme: str = Form(...), year_of_study: str = Form(...), manifesto: str = Form(...),
    experience: str = Form(""), photo: UploadFile = File(...), db: Session = Depends(get_db),
):
    # full_name is intentionally ignored: the client is not allowed to choose
    # the nominator's identity. Registry/HR supplies the authoritative name.
    required = [student_id, position, faculty, department, programme, year_of_study, manifesto]
    if any(not value.strip() for value in required):
        raise HTTPException(status_code=400, detail="Please complete all required nomination fields.")

    election = db.query(Election).filter(Election.id == election_id).first()
    if not election:
        raise HTTPException(status_code=404, detail="Election not found.")
    if election.status != "upcoming":
        raise HTTPException(status_code=400, detail="Nominations can only be submitted for an upcoming election.")

    student_id = " ".join(student_id.strip().upper().split())
    identity = (
        db.query(InstitutionalIdentity)
        .filter(InstitutionalIdentity.identifier == student_id)
        .first()
    )
    if not identity:
        raise HTTPException(
            status_code=409,
            detail="Identity not verified: this institutional ID is not in the official GZU Registry/HR roster. Import the authoritative roster before nominating."
        )
    linked_name = " ".join((identity.full_name or "").split())
    if not linked_name:
        raise HTTPException(status_code=409, detail="The official Registry/HR record has no name. Contact Registry/HR.")

    nominator = db.query(Voter).filter(Voter.student_id == student_id).first()
    if not nominator:
        raise HTTPException(status_code=404, detail="No institutional account is linked to this ID. Sign in with the account registered to this ID.")

    # Synchronise the account's stored identity with the official roster.
    nominator.full_name = linked_name
    nominator.identity_type = identity.identity_type

    duplicate = db.query(CandidateNomination).filter(
        CandidateNomination.student_id == student_id,
        CandidateNomination.election_id == election_id,
        CandidateNomination.position == position.strip(),
        CandidateNomination.status.in_(["pending", "approved"])
    ).first()
    if duplicate:
        raise HTTPException(status_code=409, detail="You already have a pending or approved nomination for this position.")

    content_type = (photo.content_type or "").lower()
    if content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(status_code=400, detail="Photo must be JPG, PNG, or WebP.")
    data = await photo.read(5 * 1024 * 1024 + 1)
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Photo must be 5 MB or smaller.")
    valid_signature = (
        (content_type == "image/jpeg" and data.startswith(b"\xff\xd8\xff")) or
        (content_type == "image/png" and data.startswith(b"\x89PNG\r\n\x1a\n")) or
        (content_type == "image/webp" and len(data) > 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP")
    )
    if not valid_signature:
        raise HTTPException(status_code=400, detail="The uploaded file is not a valid image of the declared type.")

    # Keep a private database integrity fingerprint for the authoritative
    # ID/name/type association. It contains no plaintext identity fields.
    canonical_link = f"{student_id.casefold()}|{linked_name.casefold()}|{identity.identity_type.casefold()}"
    identity_mapping_hash = hashlib.sha256(canonical_link.encode("utf-8")).hexdigest()

    ext = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[content_type]
    filename = f"{uuid4().hex}{ext}"
    (UPLOAD_DIR / filename).write_bytes(data)
    item = CandidateNomination(
        student_id=student_id,
        election_id=election_id,
        position=position.strip(),
        full_name=linked_name,
        faculty=faculty.strip(),
        department=department.strip(),
        programme=programme.strip(),
        year_of_study=year_of_study.strip(),
        manifesto=manifesto.strip(),
        experience=experience.strip(),
        photo_path=filename,
        status="pending",
        created_at=datetime.now(timezone.utc).isoformat(),
        identity_mapping_hash=identity_mapping_hash,
    )
    db.add(item)
    try:
        db.commit()
        db.refresh(item)
    except Exception:
        db.rollback()
        try:
            (UPLOAD_DIR / filename).unlink(missing_ok=True)
        except Exception:
            pass
        raise
    return _nomination_payload(item, db)


@app.get("/students/{student_id}/nominations")
def get_student_nominations(student_id: str, db: Session = Depends(get_db)):
    if not db.query(Voter).filter(Voter.student_id == student_id).first():
        raise HTTPException(status_code=404, detail="Voter account not found.")
    items = db.query(CandidateNomination).filter(CandidateNomination.student_id == student_id).order_by(CandidateNomination.id.desc()).all()
    return [_nomination_payload(item, db) for item in items]


@app.get("/candidates/{candidate_id}/profile")
def get_candidate_profile(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate or candidate.is_withdrawn:
        raise HTTPException(status_code=404, detail="Candidate not found.")
    profile = db.query(CandidateProfile).filter(CandidateProfile.candidate_id == candidate_id).first()
    return {
        "id": candidate.id, "election_id": candidate.election_id, "name": candidate.name,
        "position": candidate.position,
        "photo_url": f"/candidate-photos/{profile.photo_path}" if profile and profile.photo_path else None,
        "faculty": profile.faculty if profile else None, "department": profile.department if profile else None,
        "programme": profile.programme if profile else None, "year_of_study": profile.year_of_study if profile else None,
        "manifesto": profile.manifesto if profile else None, "experience": profile.experience if profile else None,
    }


@app.get("/admin/api/nominations")
def admin_list_nominations(status: str = "pending", _admin: dict = Depends(require_admin_api), db: Session = Depends(get_db)):
    if status not in {"pending", "approved", "rejected", "corrections_requested", "all"}:
        raise HTTPException(status_code=400, detail="Invalid nomination status.")
    query = db.query(CandidateNomination)
    if status != "all":
        query = query.filter(CandidateNomination.status == status)
    return [_nomination_payload(item, db) for item in query.order_by(CandidateNomination.id.desc()).all()]


@app.post("/admin/api/nominations/{nomination_id}/review")

def admin_review_nomination(
    nomination_id: int,
    decision: str = Form(...),
    feedback: str = Form(""),
    _admin: dict = Depends(require_admin_api),
    db: Session = Depends(get_db),
):
    if decision not in {"approve", "reject", "request_corrections"}:
        raise HTTPException(
            status_code=400,
            detail="Decision must be approve, reject, or request_corrections."
        )

    item = (
        db.query(CandidateNomination)
        .filter(CandidateNomination.id == nomination_id)
        .first()
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Nomination not found."
        )

    if item.status == "approved" and decision == "approve":
        return {
            "message": "Nomination was already approved.",
            "candidate_id": item.candidate_id
        }

    if item.status != "pending" and decision == "approve":
        raise HTTPException(
            status_code=409,
            detail="Only pending nominations can be approved."
        )

    if decision == "approve":
        election = (
            db.query(Election)
            .filter(Election.id == item.election_id)
            .first()
        )

        if not election or election.status != "upcoming":
            raise HTTPException(
                status_code=400,
                detail="Candidate can only be registered while the election is upcoming."
            )

        if election.blockchain_election_id is None:
            raise HTTPException(
                status_code=400,
                detail="This election is not linked to the blockchain."
            )

        blockchain_id = election.blockchain_election_id

        # Do not recreate a candidate that was deliberately withdrawn. Its on-chain
        # record remains immutable and must not be duplicated by nomination review.
        existing_candidate = (
            db.query(Candidate)
            .filter(
                Candidate.election_id == item.election_id,
                Candidate.name == item.full_name,
                Candidate.position == item.position,
            )
            .first()
        )
        if existing_candidate is not None and existing_candidate.is_withdrawn:
            raise HTTPException(
                status_code=409,
                detail=(
                    "A matching candidate has been withdrawn. The existing blockchain "
                    "record is preserved, so this nomination cannot create a duplicate."
                ),
            )

        try:
            _receipt, chain_id = add_candidate_to_blockchain(
                blockchain_id,
                item.full_name,
                item.position,
                expected_title=election.title,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=(
                    "Blockchain candidate registration failed: "
                    f"{type(exc).__name__}"
                )
            )

        candidate = Candidate(
            election_id=item.election_id,
            name=item.full_name,
            position=item.position,
            blockchain_candidate_id=int(chain_id)
        )

        db.add(candidate)
        db.flush()

        db.add(
            CandidateProfile(
                candidate_id=candidate.id,
                photo_path=item.photo_path,
                faculty=item.faculty,
                department=item.department,
                programme=item.programme,
                year_of_study=item.year_of_study,
                manifesto=item.manifesto,
                experience=item.experience
            )
        )

        item.candidate_id = candidate.id
        item.status = "approved"

    elif decision == "reject":
        item.status = "rejected"

    else:
        item.status = "corrections_requested"

    item.admin_feedback = feedback.strip() or None
    item.reviewed_at = datetime.now(timezone.utc).isoformat()

    db.commit()

    return {
        "message": f"Nomination {item.status.replace('_', ' ')}.",
        "candidate_id": item.candidate_id
    }



# CAST VOTE
# ============================================================

@app.get("/elections/{election_id}/voter-status")
def get_voter_status(election_id: int, student_id: str, db: Session = Depends(get_db)):
    """Fast preflight check so a voter who has already cast a ballot is stopped before candidate selection."""
    voter = db.query(Voter).filter(Voter.student_id == student_id).first()
    if not voter:
        raise HTTPException(status_code=404, detail="Voter identity was not found.")
    election = db.query(Election).filter(Election.id == election_id, Election.is_deleted == False).first()
    if not election or election.status == "cancelled":
        raise HTTPException(status_code=404, detail="Election not found or unavailable.")
    voted_positions = [
        row.position for row in db.query(VotingRecord).filter(
            VotingRecord.student_id == student_id,
            VotingRecord.election_id == election_id
        ).all()
    ]
    return {"student_id": student_id, "election_id": election_id,
            "has_voted": bool(voted_positions), "voted_positions": voted_positions}


@app.post("/vote")
def cast_vote(
    student_id: str,
    election_id: int,
    candidate_id: int,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # CHECK VOTER
    # --------------------------------------------------------

    voter = (
        db.query(Voter)
        .filter(
            Voter.student_id == student_id
        )
        .first()
    )

    if not voter:

        raise HTTPException(
            status_code=404,
            detail="Voter not found"
        )

    # --------------------------------------------------------
    # CHECK ELECTION
    # --------------------------------------------------------

    election = (
        db.query(Election)
        .filter(
            Election.id == election_id
        )
        .first()
    )

    if not election:
        raise HTTPException(
            status_code=404,
            detail="Election not found"
        )

    if election.is_deleted:
        raise HTTPException(
            status_code=409,
            detail="Archived elections cannot accept votes."
        )

    if election.status in ("cancelled", "closed"):
        raise HTTPException(
            status_code=409,
            detail="Cancelled or closed elections cannot accept votes."
        )

    blockchain_id, _chain_status = _verify_blockchain_election_mapping(election)
    # --------------------------------------------------------
    # CHECK ELECTION STATUS
    # --------------------------------------------------------

    if election.status != "ongoing":

        raise HTTPException(
            status_code=400,
            detail=(
                "Election is not currently "
                "open for voting"
            )
        )

    # --------------------------------------------------------
    # CHECK CANDIDATE
    # --------------------------------------------------------

    candidate = (
        db.query(Candidate)
        .filter(
            Candidate.id == candidate_id,
            Candidate.election_id == election_id
        )
        .first()
    )

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found for this election"
        )

    if candidate.is_withdrawn:
        raise HTTPException(
            status_code=409,
            detail="This candidate has withdrawn and cannot receive votes."
        )

    # --------------------------------------------------------
    # CHECK POSITION
    # --------------------------------------------------------

    position = candidate.position

    if not position:

        raise HTTPException(
            status_code=500,
            detail=(
                "Candidate does not "
                "have a position"
            )
        )

    # --------------------------------------------------------
    # CHECK BLOCKCHAIN CANDIDATE ID
    # --------------------------------------------------------

    blockchain_candidate_id = _ensure_candidate_blockchain_mapping(
        db, election, candidate, verified_chain_id=blockchain_id
    )

    # --------------------------------------------------------
    # CHECK DUPLICATE VOTE
    # --------------------------------------------------------

    existing_vote = (
        db.query(VotingRecord)
        .filter(
            VotingRecord.student_id == student_id,
            VotingRecord.election_id == election_id,
            VotingRecord.position == position
        )
        .first()
    )

    if existing_vote:

        raise HTTPException(
            status_code=400,
            detail=(
                f"You have already voted "
                f"for {position} in this election"
            )
        )

    # --------------------------------------------------------
    # CREATE VOTER HASH
    # --------------------------------------------------------

    voter_hash = web3.keccak(
        text=(
            f"{student_id}:"
            f"{election_id}:"
            f"{position}"
        )
    )

    print("")
    print("========== VOTE MAPPING ==========")

    print(
        "Student ID:",
        student_id
    )

    print(
        "Election ID:",
        election_id
    )

    print(
        "Position:",
        position
    )

    print(
        "PostgreSQL candidate ID:",
        candidate.id
    )

    print(
        "Candidate name:",
        candidate.name
    )

    print(
        "Blockchain candidate ID:",
        blockchain_candidate_id
    )

    print(
        "=================================="
    )

    # --------------------------------------------------------
    # SEND VOTE TO BLOCKCHAIN
    # --------------------------------------------------------

    try:

        receipt = submit_vote(
            election_id=blockchain_id,
            candidate_id=blockchain_candidate_id,
            voter_hash=voter_hash
        )

    except Exception as e:

        print("")
        print(
            "========== BLOCKCHAIN ERROR =========="
        )

        print(
            type(e).__name__
        )

        print(
            str(e)
        )

        print(
            "======================================"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Blockchain vote failed: "
                f"{type(e).__name__}: {str(e)}"
            )
        )

    # --------------------------------------------------------
    # SAVE VOTE TO SQLITE
    # --------------------------------------------------------

    voting_record = VotingRecord(
        student_id=student_id,
        election_id=election_id,
        position=position
    )

    vote = Vote(
        election_id=election_id,
        candidate_id=candidate_id
    )

    db.add(
        voting_record
    )

    db.add(
        vote
    )

    db.commit()

    return {
        "message": "Vote cast successfully",
        "election_id": election_id,
        "position": position,
        "candidate_id": candidate_id,
        "candidate_name": candidate.name,
        "blockchain_candidate_id": (
            blockchain_candidate_id
        ),
        "blockchain_transaction": (
            receipt["transactionHash"].hex()
        )
    }


# ============================================================
# GET RESULTS
# ============================================================

@app.get(
    "/elections/{election_id}/results"
)
def get_election_results(
    election_id: int,
    db: Session = Depends(get_db)
):

    election = (
        db.query(Election)
        .filter(
            Election.id == election_id
        )
        .first()
    )

    if not election or election.is_deleted:
        raise HTTPException(status_code=404, detail="Election not found")
    blockchain_id, _chain_status = _verify_blockchain_election_mapping(election)

    # Eligible voters can view live results while voting is ongoing and final results
    # after closure. Upcoming, cancelled, and archived elections do not expose results.
    if election.status not in ("ongoing", "closed"):
        raise HTTPException(
            status_code=409,
            detail="Results are available while voting is ongoing and after the election closes."
        )

    candidates = (
        db.query(Candidate)
        .filter(
            Candidate.election_id == election_id
        )
        .order_by(Candidate.id)
        .all()
    )

    results = []

    for candidate in candidates:

        blockchain_candidate_id = _ensure_candidate_blockchain_mapping(
            db, election, candidate, verified_chain_id=blockchain_id
        )

        try:

            vote_count = (
                voting_contract
                .functions
                .getVoteCount(
                    blockchain_id,
                    blockchain_candidate_id
                )
                .call()
            )

        except Exception as e:

            print(
                "========== RESULTS ERROR =========="
            )

            print(
                "Election:",
                election_id
            )

            print(
                "Candidate:",
                candidate.name
            )

            print(
                "PostgreSQL candidate ID:",
                candidate.id
            )

            print(
                "Blockchain candidate ID:",
                blockchain_candidate_id
            )

            print(
                type(e).__name__
            )

            print(
                str(e)
            )

            print(
                "==================================="
            )

            raise HTTPException(
                status_code=500,
                detail=(
                    "Unable to retrieve "
                    "blockchain vote count"
                )
            )

        results.append({
            "candidate_id": candidate.id,
            "blockchain_candidate_id": (
                blockchain_candidate_id
            ),
            "name": candidate.name,
            "position": candidate.position,
            "votes": vote_count
        })

    return {
        "election_id": election_id,
        "election_title": election.title,
        "results": results
    }


# ============================================================
# UPDATE ELECTION STATUS
# ============================================================

@app.put("/elections/{election_id}/status")
def update_election_status(
    election_id: int,
    status: str,
    admin_claims: dict = Depends(require_admin_api),
    db: Session = Depends(get_db),
):
    allowed_statuses = {"upcoming", "ongoing", "closed", "cancelled"}
    if status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Invalid election status.")

    election = db.query(Election).filter(Election.id == election_id).first()
    if not election:
        raise HTTPException(status_code=404, detail="Election not found.")
    if election.is_deleted:
        raise HTTPException(status_code=409, detail="Archived elections cannot be changed.")
    if election.blockchain_election_id is None:
        raise HTTPException(
            status_code=400,
            detail="This election is not linked to the blockchain.",
        )
    _verified_chain_id, _verified_chain_status = _verify_blockchain_election_mapping(election)

    allowed_transitions = {
        "upcoming": {"upcoming", "ongoing", "closed", "cancelled"},
        "ongoing": {"ongoing", "closed", "cancelled"},
        "closed": {"closed"},
        "cancelled": {"cancelled"},
    }
    if status not in allowed_transitions.get(election.status, set()):
        raise HTTPException(
            status_code=409,
            detail="This election status transition is not allowed.",
        )

    # No blockchain transaction is needed when the database already has this status.
    if election.status == status:
        return {
            "message": "Election status is already set.",
            "election_id": election.id,
            "status": election.status,
        }

    from blockchain import (
        end_election_on_blockchain,
        cancel_election_on_blockchain,
        start_election_on_blockchain,
        get_blockchain_election_status,
    )

    blockchain_id = election.blockchain_election_id
    try:
        chain_status = get_blockchain_election_status(blockchain_id)

        if status == "ongoing":
            if chain_status.get("closed") or chain_status.get("cancelled"):
                raise HTTPException(
                    status_code=409,
                    detail="A closed or cancelled blockchain election cannot be started.",
                )
            if not chain_status.get("active"):
                start_election_on_blockchain(blockchain_id)

        elif status == "closed":
            if chain_status.get("cancelled"):
                raise HTTPException(
                    status_code=409,
                    detail="A cancelled election cannot be closed.",
                )
            if not chain_status.get("closed"):
                end_election_on_blockchain(blockchain_id)

        elif status == "cancelled":
            if chain_status.get("closed"):
                raise HTTPException(
                    status_code=409,
                    detail="A closed election cannot be cancelled.",
                )
            if not chain_status.get("cancelled"):
                cancel_election_on_blockchain(blockchain_id)

    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=502,
            detail=(
                "Blockchain transaction failed; election status was not changed. "
                "Check the transaction and blockchain state before retrying."
            ),
        ) from exc

    try:
        election.status = status
        db.commit()
        db.refresh(election)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Election status could not be saved to the database.",
        )

    return {
        "message": "Election status updated successfully.",
        "election_id": election.id,
        "status": election.status,
    }
