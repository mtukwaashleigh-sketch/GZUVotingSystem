"""
READ-ONLY reconciliation diagnostic for Tawanda Moyo.
This script does NOT insert, update, or delete database/blockchain records.
Run from the Backend directory with the project's normal environment configured.
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
TARGET_NAME = "Tawanda Moyo"


def norm(value):
    return " ".join(str(value or "").split()).casefold()


db = SessionLocal()
try:
    print("=== READ-ONLY CANDIDATE RECONCILIATION ===")
    election = db.query(Election).filter(Election.id == DB_ELECTION_ID).first()

    if election is None:
        print(f"ERROR: PostgreSQL election ID {DB_ELECTION_ID} was not found.")
        raise SystemExit(1)

    print("\nPOSTGRESQL ELECTION")
    print(f"DB election ID: {election.id}")
    print(f"Title: {election.title!r}")
    print(f"Status: {election.status!r}")
    print(f"Deleted: {election.is_deleted!r}")
    print(f"Mapped blockchain election ID: {election.blockchain_election_id!r}")

    chain_status = get_blockchain_election_status(CHAIN_ELECTION_ID)
    print("\nBLOCKCHAIN ELECTION")
    print(f"Chain election ID: {CHAIN_ELECTION_ID}")
    print(f"Title: {chain_status['title']!r}")
    print(f"Started: {chain_status['started']}")
    print(f"Closed: {chain_status['closed']}")
    print(f"Cancelled: {chain_status['cancelled']}")

    if norm(election.title) != norm(chain_status["title"]):
        print("\nSTOP: DB election title does not match chain election 10.")
        print("No changes have been made.")
        raise SystemExit(2)

    count = int(get_blockchain_candidate_count(CHAIN_ELECTION_ID))
    print(f"\nOn-chain candidate count: {count}")

    print("\nON-CHAIN CANDIDATES")
    for chain_id in range(1, count + 1):
        try:
            item = get_blockchain_candidate(CHAIN_ELECTION_ID, chain_id)
            print(
                f"Chain candidate ID={chain_id} | "
                f"name={item['name']!r} | position={item['position']!r} | "
                f"votes={item['vote_count']}"
            )
        except Exception as exc:
            print(f"Could not read chain candidate {chain_id}: {exc}")

    print("\nPOSTGRESQL CANDIDATES FOR THIS ELECTION")
    db_candidates = (
        db.query(Candidate)
        .filter(Candidate.election_id == DB_ELECTION_ID)
        .order_by(Candidate.id)
        .all()
    )
    for item in db_candidates:
        print(
            f"DB candidate ID={item.id} | name={item.name!r} | "
            f"position={item.position!r} | "
            f"blockchain_candidate_id={item.blockchain_candidate_id!r} | "
            f"withdrawn={getattr(item, 'is_withdrawn', False)!r}"
        )

    print("\nALL DATABASE ROWS CLAIMING CHAIN CANDIDATE ID 1 IN THIS ELECTION")
    claimants = (
        db.query(Candidate)
        .filter(
            Candidate.election_id == DB_ELECTION_ID,
            Candidate.blockchain_candidate_id == CHAIN_CANDIDATE_ID,
        )
        .all()
    )
    if claimants:
        for item in claimants:
            print(
                f"DB candidate ID={item.id} | name={item.name!r} | "
                f"position={item.position!r}"
            )
    else:
        print("No PostgreSQL candidate currently claims blockchain candidate ID 1.")

    print("\nDATABASE ROWS MATCHING THE NAME TAWANDA MOYO")
    name_rows = (
        db.query(Candidate)
        .filter(Candidate.election_id == DB_ELECTION_ID)
        .all()
    )
    name_rows = [item for item in name_rows if norm(item.name) == norm(TARGET_NAME)]
    if name_rows:
        for item in name_rows:
            print(
                f"DB candidate ID={item.id} | position={item.position!r} | "
                f"blockchain_candidate_id={item.blockchain_candidate_id!r}"
            )
    else:
        print("Tawanda Moyo is not currently stored as a candidate for this DB election.")

    print("\nDIAGNOSTIC COMPLETE. READ-ONLY: NO CHANGES MADE.")
finally:
    db.close()
