
from database import SessionLocal
from models import Election, Candidate


def audit_database():
    db = SessionLocal()

    try:
        # Confirm which database engine SQLAlchemy is connected to.
        bind = db.get_bind()
        print("\n==============================================")
        print("GZU DATABASE AUDIT")
        print("==============================================")
        print("Database engine:", bind.dialect.name)

        if bind.dialect.name != "postgresql":
            print(
                "WARNING: The active SQLAlchemy connection is not "
                "PostgreSQL."
            )
            return

        elections = (
            db.query(Election)
            .order_by(Election.id)
            .all()
        )

        print("\nTOTAL ELECTIONS:", len(elections))
        print("\n========== ELECTION RECORDS ==========")

        for election in elections:
            print({
                "database_election_id": election.id,
                "title": election.title,
                "status": election.status,
                "blockchain_election_id":
                    election.blockchain_election_id,
                "is_deleted": election.is_deleted,
            })

            candidates = (
                db.query(Candidate)
                .filter(Candidate.election_id == election.id)
                .order_by(Candidate.id)
                .all()
            )

            print("  Candidates:", len(candidates))

            for candidate in candidates:
                print({
                    "database_candidate_id": candidate.id,
                    "election_id": candidate.election_id,
                    "name": candidate.name,
                    "position": candidate.position,
                    "blockchain_candidate_id":
                        candidate.blockchain_candidate_id,
                })

        # Identify duplicate non-null blockchain election mappings.
        print("\n========== MAPPING CHECKS ==========")

        duplicate_election_mappings = (
            db.query(
                Election.blockchain_election_id,
                # Count elections assigned to the same blockchain ID.
            )
            .filter(
                Election.blockchain_election_id.isnot(None)
            )
            .group_by(Election.blockchain_election_id)
            .having(
                __import__("sqlalchemy").func.count(Election.id) > 1
            )
            .all()
        )

        if duplicate_election_mappings:
            print("DUPLICATE BLOCKCHAIN ELECTION IDs:")
            for row in duplicate_election_mappings:
                print("  Blockchain ID:", row[0])
        else:
            print("No duplicate blockchain election IDs in the database.")

        duplicate_candidate_mappings = (
            db.query(
                Candidate.election_id,
                Candidate.blockchain_candidate_id,
            )
            .filter(
                Candidate.blockchain_candidate_id.isnot(None)
            )
            .group_by(
                Candidate.election_id,
                Candidate.blockchain_candidate_id,
            )
            .having(
                __import__("sqlalchemy").func.count(Candidate.id) > 1
            )
            .all()
        )

        if duplicate_candidate_mappings:
            print("DUPLICATE CANDIDATE MAPPINGS:")
            for row in duplicate_candidate_mappings:
                print({
                    "database_election_id": row[0],
                    "blockchain_candidate_id": row[1],
                })
        else:
            print("No duplicate candidate mappings within elections.")

        print("\nDatabase audit complete. No records were modified.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    audit_database()
