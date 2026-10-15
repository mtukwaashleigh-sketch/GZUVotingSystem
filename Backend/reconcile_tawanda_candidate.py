"""Safely restore Tawanda Moyo's missing PostgreSQL candidate row.

This script does NOT submit a blockchain transaction. It verifies the existing
on-chain candidate and election, checks for database conflicts, then inserts
one Candidate row mapped to blockchain candidate ID 1.
Run from the Backend directory with the project's configured environment.
"""
from database import SessionLocal
from models import Election, Candidate
from blockchain import (
    get_blockchain_candidate_count,
    get_blockchain_candidate,
    get_blockchain_election_status,
)

DB_ELECTION_ID = 7
CHAIN_ELECTION_ID = 10
CHAIN_CANDIDATE_ID = 1
EXPECTED_TITLE = "GZU Student Representative Council Election 2026"
EXPECTED_NAME = "Tawanda Moyo"
EXPECTED_POSITION = "President — Candidate 1"


def norm(value):
    return " ".join(str(value or "").split()).casefold()


db = SessionLocal()
try:
    print("=== SAFE DATABASE RECONCILIATION (NO BLOCKCHAIN TRANSACTION) ===")

    election = db.query(Election).filter(Election.id == DB_ELECTION_ID).first()
    if election is None:
        raise RuntimeError(f"Database election {DB_ELECTION_ID} does not exist.")
    if norm(election.title) != norm(EXPECTED_TITLE):
        raise RuntimeError(f"Unexpected database election title: {election.title!r}")
    if election.blockchain_election_id != CHAIN_ELECTION_ID:
        raise RuntimeError(
            f"Election mapping conflict: DB election {DB_ELECTION_ID} maps to "
            f"{election.blockchain_election_id!r}, not {CHAIN_ELECTION_ID}."
        )
    if election.is_deleted:
        raise RuntimeError("The database election is soft-deleted; no changes made.")

    chain_status = get_blockchain_election_status(CHAIN_ELECTION_ID)
    if norm(chain_status["title"]) != norm(EXPECTED_TITLE):
        raise RuntimeError(f"Unexpected on-chain election title: {chain_status['title']!r}")
    if chain_status["started"] or chain_status["closed"] or chain_status["cancelled"]:
        raise RuntimeError("The on-chain election has started or is terminal; no changes made.")

    count = int(get_blockchain_candidate_count(CHAIN_ELECTION_ID))
    if CHAIN_CANDIDATE_ID < 1 or CHAIN_CANDIDATE_ID > count:
        raise RuntimeError(f"On-chain candidate ID {CHAIN_CANDIDATE_ID} is out of range.")
    chain_candidate = get_blockchain_candidate(CHAIN_ELECTION_ID, CHAIN_CANDIDATE_ID)
    if (norm(chain_candidate["name"]) != norm(EXPECTED_NAME)
            or norm(chain_candidate["position"]) != norm(EXPECTED_POSITION)):
        raise RuntimeError(
            "On-chain candidate details do not match the expected candidate: "
            f"{chain_candidate!r}. No changes made."
        )

    # If the candidate already exists by name in this election, stop rather than duplicate it.
    same_name = [
        row for row in db.query(Candidate).filter(Candidate.election_id == DB_ELECTION_ID).all()
        if norm(row.name) == norm(EXPECTED_NAME)
    ]
    if same_name:
        raise RuntimeError(
            "A database row with this candidate name already exists in the election: "
            + repr([(row.id, row.position, row.blockchain_candidate_id) for row in same_name])
            + ". No changes made."
        )

    # A candidate mapping must not already be claimed in this election.
    claimant = db.query(Candidate).filter(
        Candidate.election_id == DB_ELECTION_ID,
        Candidate.blockchain_candidate_id == CHAIN_CANDIDATE_ID,
    ).first()
    if claimant is not None:
        raise RuntimeError(
            f"Blockchain candidate ID {CHAIN_CANDIDATE_ID} is already claimed by "
            f"database candidate {claimant.id} ({claimant.name!r}). No changes made."
        )

    new_candidate = Candidate(
        election_id=DB_ELECTION_ID,
        name=chain_candidate["name"],
        position=chain_candidate["position"],
        blockchain_candidate_id=CHAIN_CANDIDATE_ID,
        is_withdrawn=False,
    )
    db.add(new_candidate)
    db.commit()
    db.refresh(new_candidate)

    print("SUCCESS: restored the missing PostgreSQL candidate row.")
    print(f"Database candidate ID: {new_candidate.id}")
    print(f"Database election ID: {new_candidate.election_id}")
    print(f"Name: {new_candidate.name}")
    print(f"Position: {new_candidate.position}")
    print(f"Blockchain election ID: {CHAIN_ELECTION_ID}")
    print(f"Blockchain candidate ID: {new_candidate.blockchain_candidate_id}")
    print("No blockchain transaction was sent.")
except Exception as exc:
    db.rollback()
    print(f"STOPPED: {exc}")
    print("Database transaction rolled back; no candidate row was committed by this run.")
    raise
finally:
    db.close()
