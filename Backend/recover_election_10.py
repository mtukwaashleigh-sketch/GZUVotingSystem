
from database import SessionLocal
from models import Election
from blockchain import get_blockchain_election_status

BLOCKCHAIN_ID = 10
TITLE = "GZU Student Representative Council Election 2026"

db = SessionLocal()

try:
    # Verify the existing on-chain election before making changes.
    chain_status = get_blockchain_election_status(BLOCKCHAIN_ID)

    if chain_status.get("title", "").strip() != TITLE:
        raise RuntimeError(
            "Blockchain title does not match. No database changes made."
        )

    # Never overwrite an existing mapping.
    mapped = (
        db.query(Election)
        .filter(
            Election.blockchain_election_id == BLOCKCHAIN_ID
        )
        .first()
    )

    if mapped:
        raise RuntimeError(
            f"Blockchain ID {BLOCKCHAIN_ID} is already mapped "
            f"to database election {mapped.id}: {mapped.title}. "
            "No changes made."
        )

    # Avoid creating a duplicate title.
    existing_title = (
        db.query(Election)
        .filter(Election.title == TITLE)
        .first()
    )

    if existing_title:
        raise RuntimeError(
            f"An election with this title already exists "
            f"(database ID {existing_title.id}). No changes made."
        )

    election = Election(
        title=TITLE,
        description=(
            "Election to select student representatives "
            "for the Great Zimbabwe University student body."
        ),
        status="upcoming",
        blockchain_election_id=BLOCKCHAIN_ID,
        is_deleted=False,
    )

    db.add(election)
    db.commit()
    db.refresh(election)

    print("Election recovery successful.")
    print(f"Database ID: {election.id}")
    print(f"Title: {election.title}")
    print(f"Status: {election.status}")
    print(f"Blockchain ID: {election.blockchain_election_id}")

except Exception:
    db.rollback()
    raise

finally:
    db.close()
