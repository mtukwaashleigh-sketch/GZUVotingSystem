"""Read-only inspection of GZU Voting PostgreSQL and blockchain state.
Run from Backend: python inspect_voting_state.py
This script does not create, update, or delete records or send transactions.
"""
from sqlalchemy import text
from database import SessionLocal
from models import Election, Candidate, Vote

try:
    from blockchain import (
        web3,
        CHAIN_ID,
        CONTRACT_ADDRESS,
        get_blockchain_election_count,
        get_blockchain_election_status,
        get_blockchain_candidate_count,
        get_blockchain_candidate,
        get_blockchain_vote_count,
    )
except Exception as exc:
    print("ERROR: Could not initialize blockchain connection:", repr(exc))
    print("Database inspection can still be run separately; see instructions in chat.")
    raise


def safe(value):
    return str(value).replace("\n", " ")


db = SessionLocal()
try:
    print("\n" + "=" * 78)
    print("GZU VOTING - READ-ONLY DATABASE + BLOCKCHAIN INSPECTION")
    print("=" * 78)
    print(f"Blockchain chain ID : {CHAIN_ID}")
    print(f"Voting contract     : {CONTRACT_ADDRESS}")
    print(f"Latest block        : {web3.eth.block_number}")
    print("\n--- DATABASE: ELECTIONS AND CANDIDATES ---")

    elections = db.query(Election).order_by(Election.id).all()
    if not elections:
        print("No elections found in database.")

    for election in elections:
        print(
            f"\nDB Election ID={election.id} | title={safe(election.title)!r}"
            f" | status={safe(election.status)!r}"
            f" | deleted={getattr(election, 'is_deleted', None)}"
            f" | blockchain_election_id={election.blockchain_election_id}"
        )
        candidates = (
            db.query(Candidate)
            .filter(Candidate.election_id == election.id)
            .order_by(Candidate.id)
            .all()
        )
        if not candidates:
            print("  (no database candidates)")
        for c in candidates:
            print(
                f"  DB Candidate ID={c.id} | name={safe(c.name)!r}"
                f" | position={safe(c.position)!r}"
                f" | blockchain_candidate_id={c.blockchain_candidate_id}"
                f" | withdrawn={getattr(c, 'is_withdrawn', None)}"
            )

    try:
        vote_rows = db.query(Vote).count()
        print(f"\nDatabase Vote rows: {vote_rows}")
        for v in db.query(Vote).order_by(Vote.id).all():
            print(
                f"  Vote DB ID={v.id} | DB election_id={v.election_id}"
                f" | DB candidate_id={v.candidate_id}"
            )
    except Exception as exc:
        print("Could not inspect database Vote rows:", repr(exc))

    print("\n--- BLOCKCHAIN: ALL ELECTIONS AND CANDIDATES ---")
    chain_election_count = int(get_blockchain_election_count())
    print(f"On-chain electionCount={chain_election_count}")
    if chain_election_count == 0:
        print("No elections found on this configured contract.")

    for election_id in range(1, chain_election_count + 1):
        try:
            status = get_blockchain_election_status(election_id)
            count = int(get_blockchain_candidate_count(election_id))
            print(
                f"\nCHAIN Election ID={election_id}"
                f" | title={status['title']!r}"
                f" | active={status['active']}"
                f" | started={status['started']}"
                f" | closed={status['closed']}"
                f" | cancelled={status['cancelled']}"
                f" | candidateCount={count}"
            )
            if count == 0:
                print("  (no on-chain candidates)")
            for candidate_id in range(1, count + 1):
                try:
                    c = get_blockchain_candidate(election_id, candidate_id)
                    try:
                        votes = get_blockchain_vote_count(election_id, candidate_id)
                    except Exception as vote_exc:
                        votes = f"unavailable: {vote_exc}"
                    print(
                        f"  CHAIN Candidate ID={candidate_id}"
                        f" | name={c['name']!r}"
                        f" | position={c['position']!r}"
                        f" | vote_count={c['vote_count']}"
                        f" | getVoteCount={votes}"
                    )
                except Exception as exc:
                    print(f"  ERROR reading candidate {candidate_id}: {exc!r}")
        except Exception as exc:
            print(f"\nERROR reading chain election {election_id}: {exc!r}")

    print("\n" + "=" * 78)
    print("Inspection complete. No changes were made.")
    print("Compare each DB candidate using (blockchain_election_id, blockchain_candidate_id).")
    print("=" * 78)
finally:
    db.close()
