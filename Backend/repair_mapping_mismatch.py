"""Safely repair the known GZU Voting PostgreSQL/blockchain mapping mismatch.

Run from the Backend folder:
    python repair_mapping_mismatch.py

This script never creates/deletes elections or changes votes. It only repairs a
stored election title and candidate blockchain IDs when the already-stored
blockchain election mapping is confirmed by exact candidate name + position
matches. It aborts without writing if the evidence is ambiguous.
"""

from sqlalchemy.orm import Session

from database import SessionLocal
from models import Candidate, Election
from blockchain import (
    get_blockchain_candidate,
    get_blockchain_candidate_count,
    get_blockchain_election_count,
    get_blockchain_election_status,
)


def norm(value):
    return " ".join(str(value or "").strip().casefold().split())


def main():
    db: Session = SessionLocal()
    try:
        print("\n=== GZU VOTING MAPPING REPAIR ===")
        print("Checking PostgreSQL and the configured blockchain; no changes made yet.")

        chain_count = int(get_blockchain_election_count())
        elections = (
            db.query(Election)
            .filter(Election.is_deleted.is_(False))
            .order_by(Election.id)
            .all()
        )

        repairs = []
        for election in elections:
            chain_id = election.blockchain_election_id
            if chain_id is None:
                print(f"SKIP database election {election.id}: no blockchain ID is stored.")
                continue

            chain_id = int(chain_id)
            if chain_id < 1 or chain_id > chain_count:
                print(f"ABORT: database election {election.id} maps to invalid blockchain ID {chain_id}.")
                return

            chain_status = get_blockchain_election_status(chain_id)
            db_candidates = (
                db.query(Candidate)
                .filter(Candidate.election_id == election.id)
                .order_by(Candidate.id)
                .all()
            )
            chain_candidate_count = int(get_blockchain_candidate_count(chain_id))

            # Read every on-chain candidate so that matches are based on both name and position.
            chain_candidates = []
            for chain_candidate_id in range(1, chain_candidate_count + 1):
                chain_candidate = get_blockchain_candidate(chain_id, chain_candidate_id)
                chain_candidates.append((chain_candidate_id, chain_candidate))

            candidate_updates = []
            all_candidates_match = bool(db_candidates)
            used_chain_ids = set()

            for candidate in db_candidates:
                matches = [
                    (cid, cc)
                    for cid, cc in chain_candidates
                    if norm(cc.get("name")) == norm(candidate.name)
                    and norm(cc.get("position")) == norm(candidate.position)
                ]

                if len(matches) != 1:
                    all_candidates_match = False
                    print(
                        f"Candidate evidence is not unique for database candidate {candidate.id} "
                        f"({candidate.name!r}, {candidate.position!r}); found {len(matches)} chain matches."
                    )
                    break

                chain_candidate_id, _ = matches[0]
                if chain_candidate_id in used_chain_ids:
                    all_candidates_match = False
                    print("Candidate evidence is ambiguous: two database candidates match the same chain candidate.")
                    break
                used_chain_ids.add(chain_candidate_id)

                stored_candidate_id = candidate.blockchain_candidate_id
                if stored_candidate_id not in (None, 0, chain_candidate_id):
                    all_candidates_match = False
                    print(
                        f"ABORT: candidate {candidate.id} stores blockchain candidate ID "
                        f"{stored_candidate_id}, but exact name/position match is ID {chain_candidate_id}."
                    )
                    break

                if stored_candidate_id != chain_candidate_id:
                    candidate_updates.append((candidate, chain_candidate_id))

            title_matches = norm(election.title) == norm(chain_status.get("title"))
            if not all_candidates_match:
                if not title_matches:
                    print(
                        f"UNRESOLVED: database election {election.id} title {election.title!r} differs from "
                        f"blockchain election {chain_id} title {chain_status.get('title')!r}, and candidate "
                        "records do not prove this is the same election. No changes made for this election."
                    )
                else:
                    print(
                        f"UNRESOLVED: candidate data for database election {election.id} does not match "
                        "uniquely. No changes made for this election."
                    )
                continue

            if not title_matches and all_candidates_match:
                print(
                    f"VERIFIED BY CANDIDATES: database election {election.id} maps to blockchain "
                    f"election {chain_id}. Will align its PostgreSQL title to {chain_status.get('title')!r}."
                )
                repairs.append((election, chain_status.get("title"), candidate_updates))
            elif candidate_updates:
                print(f"Verified election {election.id}; will repair {len(candidate_updates)} candidate ID(s).")
                repairs.append((election, None, candidate_updates))
            else:
                print(f"OK: database election {election.id} maps to blockchain election {chain_id}.")

        if not repairs:
            print("\nNo safe repairs were identified. The database was not changed.")
            return

        # Apply all verified repairs in one PostgreSQL transaction.
        try:
            for election, corrected_title, candidate_updates in repairs:
                if corrected_title is not None:
                    election.title = corrected_title
                for candidate, corrected_candidate_id in candidate_updates:
                    candidate.blockchain_candidate_id = corrected_candidate_id
            db.commit()
        except Exception:
            db.rollback()
            raise

        print("\n=== REPAIR COMPLETE ===")
        for election, corrected_title, candidate_updates in repairs:
            if corrected_title is not None:
                print(f"Election {election.id}: PostgreSQL title aligned to {corrected_title!r}.")
            for candidate, corrected_candidate_id in candidate_updates:
                print(f"Candidate {candidate.id}: blockchain_candidate_id set to {corrected_candidate_id}.")
        print("No elections, candidates, or votes were deleted or created.")
        print("Restart the backend and check synchronization logs.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
