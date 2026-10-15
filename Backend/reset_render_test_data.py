
import argparse
from getpass import getpass

from sqlalchemy import inspect, text
from database import engine


# These safeguards are based on the Render database details
# previously identified for this project.
EXPECTED_HOST = (
    "dpg-db5varajnfac73bs26j0-a.oregon-postgres.render.com"
)
EXPECTED_DATABASE = "gzu_voting"

# Clear test/application records but preserve the official identity roster.
RESET_TABLES = [
    "votes",
    "voting_records",
    "candidate_profiles",
    "candidate_nominations",
    "candidates",
    "elections",
    "voters",
]

# Ensure every expected application table exists before changing anything.
REQUIRED_TABLES = RESET_TABLES + ["institutional_identities"]


def verify_database():
    url = engine.url

    print("\n=== DATABASE SAFETY CHECK ===")
    print("Database engine:", engine.dialect.name)
    print("Database host:", url.host)
    print("Database name:", url.database)
    print("Password: hidden")

    if engine.dialect.name != "postgresql":
        raise SystemExit("STOP: This is not a PostgreSQL connection.")

    if url.host != EXPECTED_HOST:
        raise SystemExit(
            "STOP: The host does not match the expected Render database. "
            "No changes were made."
        )

    if url.database != EXPECTED_DATABASE:
        raise SystemExit(
            "STOP: The database name does not match the expected database. "
            "No changes were made."
        )


def inspect_database(connection):
    inspector = inspect(connection)
    tables = set(inspector.get_table_names())

    missing = sorted(set(REQUIRED_TABLES) - tables)
    if missing:
        raise SystemExit(
            "STOP: Expected tables are missing: "
            + ", ".join(missing)
            + ". No reset was performed."
        )

    print("\n=== CURRENT RECORD COUNTS ===")
    for table in RESET_TABLES:
        count = connection.execute(
            text(f'SELECT COUNT(*) FROM "{table}"')
        ).scalar_one()
        print(f"{table}: {count}")

    roster_count = connection.execute(
        text('SELECT COUNT(*) FROM "institutional_identities"')
    ).scalar_one()
    print(f"institutional_identities (PRESERVED): {roster_count}")

    voter_columns = {
        column["name"]
        for column in inspector.get_columns("voters")
    }
    print("\n=== SCHEMA CHECK ===")
    print("voters.full_name exists:", "full_name" in voter_columns)
    print("voters.identity_type exists:", "identity_type" in voter_columns)

    for table, column in [
        ("elections", "is_deleted"),
        ("candidates", "is_withdrawn"),
    ]:
        columns = {
            item["name"]
            for item in inspector.get_columns(table)
        }
        print(f"{table}.{column} exists:", column in columns)


def apply_schema_fixes(connection):
    # Add only missing columns. Existing data is retained.
    migrations = [
        (
            "voters",
            "full_name",
            'ALTER TABLE voters ADD COLUMN full_name VARCHAR',
        ),
        (
            "voters",
            "identity_type",
            "ALTER TABLE voters ADD COLUMN identity_type "
            "VARCHAR NOT NULL DEFAULT 'student'",
        ),
        (
            "elections",
            "is_deleted",
            "ALTER TABLE elections ADD COLUMN is_deleted "
            "BOOLEAN NOT NULL DEFAULT FALSE",
        ),
        (
            "candidates",
            "is_withdrawn",
            "ALTER TABLE candidates ADD COLUMN is_withdrawn "
            "BOOLEAN NOT NULL DEFAULT FALSE",
        ),
    ]

    for table, column, statement in migrations:
        columns = {
            item["name"]
            for item in inspect(connection).get_columns(table)
        }
        if column not in columns:
            connection.execute(text(statement))
            print(f"Added missing column: {table}.{column}")
        else:
            print(f"Already present: {table}.{column}")


def reset_data():
    # Delete records inside one transaction. If a database error occurs,
    # PostgreSQL rolls the transaction back instead of leaving a partial reset.
    with engine.begin() as connection:
        apply_schema_fixes(connection)

        print("\n=== DELETING TEST RECORDS ===")
        for table in RESET_TABLES:
            result = connection.execute(
                text(f'DELETE FROM "{table}"')
            )
            print(f"{table}: deleted {result.rowcount} row(s)")

        print("\nAll requested deletes completed inside the transaction.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply schema fixes and delete test records.",
    )
    args = parser.parse_args()

    verify_database()

    with engine.connect() as connection:
        inspect_database(connection)

    if not args.apply:
        print("\nDRY RUN ONLY. Nothing was changed.")
        print("If the database and counts are correct, run:")
        print("python reset_render_test_data.py --apply")
        return

    print("\nWARNING: This permanently deletes the listed test records.")
    print("The official identity roster and blockchain are not deleted.")
    confirmation = getpass(
        'Type RESET GZU TEST DATA to continue: '
    )

    if confirmation != "RESET GZU TEST DATA":
        print("Cancelled. No reset was performed.")
        return

    reset_data()

    print("\n=== RESET COMPLETE ===")
    print("Test records cleared.")
    print("institutional_identities preserved.")
    print("Blockchain contract and admin environment were not changed.")

    with engine.connect() as connection:
        print("\n=== FINAL RECORD COUNTS ===")
        for table in RESET_TABLES:
            count = connection.execute(
                text(f'SELECT COUNT(*) FROM "{table}"')
            ).scalar_one()
            print(f"{table}: {count}")

        roster_count = connection.execute(
            text('SELECT COUNT(*) FROM "institutional_identities"')
        ).scalar_one()
        print(f"institutional_identities (PRESERVED): {roster_count}")


if __name__ == "__main__":
    main()
