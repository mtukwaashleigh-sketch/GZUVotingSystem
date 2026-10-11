import os
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
    CandidateProfile
)

from admin import router as admin_router
from admin_auth import auth_router
from admin_auth import api_router as admin_api_router, require_admin_api

from blockchain import (
    voting_contract,
    submit_vote,
    web3,
    sync_database_to_blockchain,
    add_candidate_to_blockchain
)


# ============================================================
# DATABASE
# ============================================================

Base.metadata.create_all(
    bind=engine
)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="GZU Student Voting System API"
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

    return {
        "message": "Login successful",
        "student_id": voter.student_id,
        "email": voter.email
    }


# ============================================================
# GET ELECTIONS
# ============================================================

@app.get("/elections")
def get_elections(
    db: Session = Depends(get_db)
):

    # Student-facing list excludes cancelled and archived elections. Closed
    # elections remain available so students can view final results.
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
    if election.blockchain_election_id is None:
        raise HTTPException(
                status_code=400,
                detail="This election is not linked to the blockchain"
                )
    blockchain_id = election.blockchain_election_id

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
        profile = db.query(CandidateProfile).filter(CandidateProfile.candidate_id == candidate.id).first()
        result.append({
            "id": candidate.id, "election_id": candidate.election_id,
            "name": candidate.name, "position": candidate.position,
            "blockchain_candidate_id": candidate.blockchain_candidate_id,
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

def _nomination_payload(item):
    return {
        "id": item.id, "student_id": item.student_id, "election_id": item.election_id,
        "position": item.position, "full_name": item.full_name, "faculty": item.faculty,
        "department": item.department, "programme": item.programme,
        "year_of_study": item.year_of_study, "manifesto": item.manifesto,
        "experience": item.experience, "photo_url": f"/candidate-photos/{item.photo_path}",
        "status": item.status, "admin_feedback": item.admin_feedback,
        "candidate_id": item.candidate_id, "created_at": item.created_at, "reviewed_at": item.reviewed_at,
    }


@app.post("/nominations")
async def submit_candidate_nomination(
    student_id: str = Form(...), election_id: int = Form(...), position: str = Form(...),
    full_name: str = Form(...), faculty: str = Form(...), department: str = Form(...),
    programme: str = Form(...), year_of_study: str = Form(...), manifesto: str = Form(...),
    experience: str = Form(""), photo: UploadFile = File(...), db: Session = Depends(get_db),
):
    required = [student_id, position, full_name, faculty, department, programme, year_of_study, manifesto]
    if any(not value.strip() for value in required):
        raise HTTPException(status_code=400, detail="Please complete all required nomination fields.")
    election = db.query(Election).filter(Election.id == election_id).first()
    if not election:
        raise HTTPException(status_code=404, detail="Election not found.")
    if election.status != "upcoming":
        raise HTTPException(status_code=400, detail="Nominations can only be submitted for an upcoming election.")
    if not db.query(Voter).filter(Voter.student_id == student_id).first():
        raise HTTPException(status_code=404, detail="Student account not found.")
    duplicate = db.query(CandidateNomination).filter(
        CandidateNomination.student_id == student_id, CandidateNomination.election_id == election_id,
        CandidateNomination.position == position, CandidateNomination.status.in_(["pending", "approved"])
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
    ext = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[content_type]
    filename = f"{uuid4().hex}{ext}"
    (UPLOAD_DIR / filename).write_bytes(data)
    item = CandidateNomination(
        student_id=student_id.strip(), election_id=election_id, position=position.strip(),
        full_name=full_name.strip(), faculty=faculty.strip(), department=department.strip(),
        programme=programme.strip(), year_of_study=year_of_study.strip(), manifesto=manifesto.strip(),
        experience=experience.strip(), photo_path=filename, status="pending",
        created_at=datetime.now(timezone.utc).isoformat()
    )
    db.add(item); db.commit(); db.refresh(item)
    return _nomination_payload(item)


@app.get("/students/{student_id}/nominations")
def get_student_nominations(student_id: str, db: Session = Depends(get_db)):
    if not db.query(Voter).filter(Voter.student_id == student_id).first():
        raise HTTPException(status_code=404, detail="Student account not found.")
    items = db.query(CandidateNomination).filter(CandidateNomination.student_id == student_id).order_by(CandidateNomination.id.desc()).all()
    return [_nomination_payload(item) for item in items]


@app.get("/candidates/{candidate_id}/profile")
def get_candidate_profile(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
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
    return [_nomination_payload(item) for item in query.order_by(CandidateNomination.id.desc()).all()]


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

        try:
            _receipt, chain_id = add_candidate_to_blockchain(
                blockchain_id,
                item.full_name,
                item.position
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
            detail="Student not found"
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

    if election.blockchain_election_id is None:
        raise HTTPException(
            status_code=400,
            detail="This election is not linked to the blockchain"
        )

    blockchain_id = election.blockchain_election_id
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
            detail=(
                "Candidate not found "
                "for this election"
            )
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

    blockchain_candidate_id = (
        candidate.blockchain_candidate_id
    )

    if blockchain_candidate_id is None:

        raise HTTPException(
            status_code=500,
            detail=(
                "Candidate is not correctly "
                "linked to the blockchain"
            )
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
        "SQLite candidate ID:",
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
    if election.blockchain_election_id is None:
        raise HTTPException(
            status_code=400,
            detail="This election is not linked to the blockchain"
        )

    blockchain_id = election.blockchain_election_id

    # Students can view live results while voting is ongoing and final results
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

        blockchain_candidate_id = (
            candidate.blockchain_candidate_id
        )

        if blockchain_candidate_id is None:

            raise HTTPException(
                status_code=500,
                detail=(
                    f"Candidate '{candidate.name}' "
                    "is not correctly linked "
                    "to the blockchain"
                )
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
                "SQLite candidate ID:",
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
