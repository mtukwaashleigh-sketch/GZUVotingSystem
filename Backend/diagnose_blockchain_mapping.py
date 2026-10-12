"""Read-only diagnostic for SQLite-to-blockchain election/candidate mappings.

Run from the Backend directory:
    python diagnose_blockchain_mapping.py

This script never changes SQLite or submits blockchain transactions.
"""
from database import SessionLocal
from models import Election, Candidate
from blockchain import (
    get_blockchain_election_count,
    get_blockchain_election_status,
    get_blockchain_candidate_count,
    get_blockchain_candidate,
)


def normalise(value):
    return " ".join(str(value or "").split()).casefold()


def main():
    db = SessionLocal()
    try:
        elections = db.query(Election).order_by(Election.id).all()
        chain_count = int(get_blockchain_election_count())

        print("\n=== SQLITE ELECTIONS AND MAPPINGS ===")
        for election in elections:
            print(
                f"SQLite election ID={election.id} | title={election.title!r} | "
                f"blockchain_election_id={election.blockchain_election_id!r} | "
                f"status={election.status!r} | archived={bool(election.is_deleted)}"
            )
            local_candidates = (
                db.query(Candidate)
                .filter(Candidate.election_id == election.id)
                .order_by(Candidate.id)
                .all()
            )
            for candidate in local_candidates:
                print(
                    f"  SQLite candidate ID={candidate.id} | name={candidate.name!r} | "
                    f"position={candidate.position!r} | "
                    f"blockchain_candidate_id={candidate.blockchain_candidate_id!r}"
                )

        print("\n=== BLOCKCHAIN ELECTIONS AND CANDIDATES ===")
        print("Connected blockchain election count:", chain_count)
        for chain_id in range(1, chain_count + 1):
            try:
                status = get_blockchain_election_status(chain_id)
                print(
                    f"Blockchain election ID={chain_id} | title={status['title']!r} | "
                    f"active={status['active']} | started={status['started']} | "
                    f"closed={status['closed']} | cancelled={status['cancelled']}"
                )
                candidate_count = int(get_blockchain_candidate_count(chain_id))
                for candidate_id in range(1, candidate_count + 1):
                    candidate = get_blockchain_candidate(chain_id, candidate_id)
                    print(
                        f"  Blockchain candidate ID={candidate_id} | "
                        f"name={candidate['name']!r} | position={candidate['position']!r} | "
                        f"votes={candidate['vote_count']}"
                    )
            except Exception as exc:
                print(f"  ERROR reading blockchain election {chain_id}: {type(exc).__name__}: {exc}")

        print("\n=== TITLE MATCH CHECK ===")
        for election in elections:
            chain_id = election.blockchain_election_id
            if chain_id is None or not (1 <= int(chain_id) <= chain_count):
                print(f"SQLite election {election.id}: no valid mapped blockchain election")
                continue
            status = get_blockchain_election_status(int(chain_id))
            same = normalise(election.title) == normalise(status["title"])
            print(
                f"SQLite election {election.id} -> blockchain election {chain_id}: "
                f"{'TITLE MATCH' if same else 'TITLE MISMATCH'} "
                f"(SQLite={election.title!r}; blockchain={status['title']!r})"
            )

        print("\nREAD-ONLY CHECK COMPLETE. No database or blockchain data was changed.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
