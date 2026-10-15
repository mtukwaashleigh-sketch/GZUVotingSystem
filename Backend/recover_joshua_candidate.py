"""Safely inspect and recover Joshua Malope if the candidate is verified on-chain.

Run from the Backend folder with the project's normal environment/configuration.
This script NEVER sends a blockchain transaction. It only reads the chain and,
when the exact candidate is uniquely verified by current contract getters, repairs
or creates the corresponding database row.
"""

from sqlalchemy.exc import SQLAlchemyError

from blockchain import (
    web3,
    voting_contract,
    CONTRACT_ADDRESS,
    _normalise_chain_text,
    get_blockchain_candidate_count,
    get_blockchain_candidate,
)
from database import SessionLocal
from models import Election, Candidate

TX_HASH = "0x21f12eb72c456f1ae056c2d9e4526c34e4b6ba1350f992f4762dcf87028f9d0c"
BLOCKCHAIN_ELECTION_ID = 10
CANDIDATE_NAME = "Joshua Malope"
CANDIDATE_POSITION = "Treasurer — Candidate 1"


def norm(value):
    return _normalise_chain_text(value or "")


def main():
    print("\n=== Candidate recovery: READ-ONLY chain inspection first ===")
    print(f"Chain ID: {web3.eth.chain_id}")
    print(f"Configured contract: {CONTRACT_ADDRESS}")
    print(f"Transaction: {TX_HASH}")

    try:
        receipt = web3.eth.get_transaction_receipt(TX_HASH)
    except Exception as exc:
        print(f"STOP: Could not retrieve transaction receipt: {exc}")
        print("No database changes were made.")
        return

    print(f"Receipt status: {receipt.get('status')}")
    print(f"Receipt block: {receipt.get('blockNumber')}")
    print(f"Receipt transaction destination: {receipt.get('to')}")

    try:
        tx = web3.eth.get_transaction(TX_HASH)
        print(f"Transaction sender: {tx.get('from')}")
        print(f"Transaction destination: {tx.get('to')}")
        try:
            fn, decoded = voting_contract.decode_function_input(tx.get("input", tx.get("data", "0x")))
            print(f"Decoded function: {fn.fn_name}")
            print(f"Decoded arguments: {decoded}")
        except Exception as exc:
            print(f"Could not decode transaction input with configured ABI: {exc}")
    except Exception as exc:
        print(f"Could not retrieve transaction details: {exc}")

    if int(receipt.get("status", 0)) != 1:
        print("STOP: The transaction did not succeed. No database changes were made.")
        return

    if (receipt.get("to") or "").lower() != CONTRACT_ADDRESS.lower():
        print("STOP: Receipt destination does not match the configured Voting contract.")
        print("This points to a contract/network configuration mismatch. No DB changes.")
        return

    event_ids = []
    try:
        decoded_events = voting_contract.events.CandidateAdded().process_receipt(receipt)
        for event in decoded_events:
            args = event.get("args", {})
            string_values = [v for v in args.values() if isinstance(v, str)]
            if (int(args.get("electionId", -1)) == BLOCKCHAIN_ELECTION_ID
                    and norm(args.get("name", "")) == norm(CANDIDATE_NAME)
                    and any(norm(v) == norm(CANDIDATE_POSITION) for v in string_values)):
                event_ids.append(int(args["candidateId"]))
                print(f"Receipt CandidateAdded match: candidate ID {int(args['candidateId'])}")
    except Exception as exc:
        print(f"Could not decode CandidateAdded event: {exc}")

    if not event_ids:
        print("WARNING: No matching CandidateAdded event was decoded from this receipt.")
    elif len(set(event_ids)) > 1:
        print(f"STOP: Receipt contains multiple candidate IDs for the requested candidate: {event_ids}")
        print("No database changes were made.")
        return

    try:
        receipt_block = int(receipt["blockNumber"])
        historical_count = voting_contract.functions.candidateCount(BLOCKCHAIN_ELECTION_ID).call(
            block_identifier=receipt_block
        )
        print(f"candidateCount(election 10) at receipt block {receipt_block}: {historical_count}")
        if event_ids:
            event_id = event_ids[0]
            try:
                historical = voting_contract.functions.candidates(BLOCKCHAIN_ELECTION_ID, event_id).call(
                    block_identifier=receipt_block
                )
                print(f"Historical candidate getter at ID {event_id}: {historical}")
            except Exception as exc:
                print(f"Historical getter failed for candidate ID {event_id}: {exc}")
    except Exception as exc:
        print(f"Historical block reads unavailable from this RPC: {exc}")

    # Current state is authoritative for creating/repairing a live DB mapping.
    try:
        count = int(get_blockchain_candidate_count(BLOCKCHAIN_ELECTION_ID))
    except Exception as exc:
        print(f"STOP: Could not read current candidate count: {exc}")
        print("No database changes were made.")
        return

    matches = []
    observed = []
    for cid in range(1, count + 1):
        try:
            item = get_blockchain_candidate(BLOCKCHAIN_ELECTION_ID, cid)
            observed.append(f"{cid}: {item.get('name')!r} / {item.get('position')!r}")
            if (norm(item.get("name")) == norm(CANDIDATE_NAME)
                    and norm(item.get("position")) == norm(CANDIDATE_POSITION)):
                matches.append(cid)
        except Exception as exc:
            observed.append(f"{cid}: getter error: {exc}")

    print(f"Current candidate count: {count}")
    print("Current candidates: " + (" | ".join(observed) if observed else "<none>"))
    print(f"Current exact getter matches: {matches}")

    if len(matches) != 1:
        print("\nRECOVERY PAUSED: The candidate is not uniquely visible in current on-chain state.")
        print("No database changes were made and no transaction was sent.")
        print("Use the receipt/block results above to diagnose the RPC, network, or contract mismatch first.")
        return

    chain_candidate_id = matches[0]
    db = SessionLocal()
    try:
        election = db.query(Election).filter(
            Election.blockchain_election_id == BLOCKCHAIN_ELECTION_ID
        ).one_or_none()
        if election is None:
            print("STOP: No unique database election maps to blockchain election ID 10.")
            print("No database changes were made.")
            return

        rows = db.query(Candidate).filter(
            Candidate.election_id == election.id,
            Candidate.name == CANDIDATE_NAME,
            Candidate.position == CANDIDATE_POSITION,
        ).all()
        if len(rows) > 1:
            print(f"STOP: Database already contains {len(rows)} exact candidate rows; manual cleanup needed.")
            print("No database changes were made.")
            return

        mapped_elsewhere = db.query(Candidate).filter(
            Candidate.election_id == election.id,
            Candidate.blockchain_candidate_id == chain_candidate_id,
        ).all()
        if any(not (len(rows) == 1 and row.id == rows[0].id) for row in mapped_elsewhere):
            print(f"STOP: Blockchain candidate ID {chain_candidate_id} is already mapped to another DB candidate.")
            print("No database changes were made.")
            return

        if rows:
            candidate = rows[0]
            if candidate.blockchain_candidate_id not in (None, chain_candidate_id):
                print(f"STOP: Existing DB row maps to blockchain ID {candidate.blockchain_candidate_id}, not {chain_candidate_id}.")
                print("No database changes were made.")
                return
            if candidate.blockchain_candidate_id == chain_candidate_id:
                print(f"Already recovered: DB candidate ID {candidate.id} maps to blockchain candidate ID {chain_candidate_id}.")
                return
            candidate.blockchain_candidate_id = chain_candidate_id
            action = "repaired existing candidate row"
        else:
            candidate = Candidate(
                election_id=election.id,
                name=CANDIDATE_NAME,
                position=CANDIDATE_POSITION,
                blockchain_candidate_id=chain_candidate_id,
            )
            db.add(candidate)
            action = "created missing candidate row"

        db.commit()
        print(f"\nRECOVERY SUCCESS: {action}.")
        print(f"Database election ID: {election.id}; blockchain election ID: {BLOCKCHAIN_ELECTION_ID}")
        print(f"Database candidate ID: {candidate.id}; blockchain candidate ID: {chain_candidate_id}")
        print("No blockchain transaction was sent.")
    except SQLAlchemyError as exc:
        db.rollback()
        print(f"DATABASE ERROR: {exc}")
        print("Database changes were rolled back; no blockchain transaction was sent.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
