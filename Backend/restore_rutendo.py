
from database import SessionLocal
from models import Candidate, Election
from blockchain import (
    get_blockchain_candidate,
    get_blockchain_candidate_count,
)

ELECTION_ID = 7
BLOCKCHAIN_ELECTION_ID = 10
BLOCKCHAIN_CANDIDATE_ID = 2

NAME = "Rutendo Ncube"
POSITION = "President — Candidate 2"

db = SessionLocal()

try:
    # Confirm the election mapping.
    election = db.query(Election).filter(
        Election.id == ELECTION_ID
    ).first()

    if election is None:
        raise RuntimeError("PostgreSQL election 7 was not found.")

    if election.blockchain_election_id != BLOCKCHAIN_ELECTION_ID:
        raise RuntimeError("Election blockchain mapping does not match.")

    # Verify that the existing blockchain candidate is correct.
    count = get_blockchain_candidate_count(BLOCKCHAIN_ELECTION_ID)

    if count < BLOCKCHAIN_CANDIDATE_ID:
        raise RuntimeError("Blockchain candidate ID 2 does not exist.")

    chain_candidate = get_blockchain_candidate(
        BLOCKCHAIN_ELECTION_ID,
        BLOCKCHAIN_CANDIDATE_ID,
    )

    if (
        chain_candidate["name"].strip() != NAME
        or chain_candidate["position"].strip() != POSITION
    ):
        raise RuntimeError(
            f"Blockchain candidate mismatch: {chain_candidate}"
        )

    # Check whether this database candidate already exists.
    existing = db.query(Candidate).filter(
        Candidate.election_id == ELECTION_ID,
        Candidate.name == NAME,
        Candidate.position == POSITION,
    ).first()

    if existing:
        if existing.blockchain_candidate_id == BLOCKCHAIN_CANDIDATE_ID:
            print("Already synchronized. No changes made.")
        else:
            raise RuntimeError(
                "Candidate already exists with a different blockchain ID. "
                "No changes made."
            )
    else:
        # Prevent assigning blockchain ID 2 twice in this election.
        claimed = db.query(Candidate).filter(
            Candidate.election_id == ELECTION_ID,
            Candidate.blockchain_candidate_id == BLOCKCHAIN_CANDIDATE_ID,
        ).first()

        if claimed:
            raise RuntimeError(
                f"Blockchain candidate ID 2 is already mapped to "
                f"database candidate {claimed.id}. No changes made."
            )

        candidate = Candidate(
            election_id=ELECTION_ID,
            name=NAME,
            position=POSITION,
            blockchain_candidate_id=BLOCKCHAIN_CANDIDATE_ID,
        )

        db.add(candidate)
        db.commit()
        db.refresh(candidate)

        print("SUCCESS: Candidate restored in PostgreSQL.")
        print("Database candidate ID:", candidate.id)
        print("Database election ID:", candidate.election_id)
        print("Blockchain election ID:", BLOCKCHAIN_ELECTION_ID)
        print("Blockchain candidate ID:", candidate.blockchain_candidate_id)
        print("No blockchain transaction was sent.")

except Exception:
    db.rollback()
    raise

finally:
    db.close()
