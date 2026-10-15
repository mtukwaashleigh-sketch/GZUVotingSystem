"""
Safely reconcile an already-successful candidate-add transaction into PostgreSQL.

This script NEVER sends a blockchain transaction. It reads the transaction receipt,
extracts the CandidateAdded event, verifies the candidate using the deployed
contract getter, validates the election mapping, then inserts one DB row only
when the evidence is unambiguous.

Run from the Backend directory:
    python reconcile_successful_candidate_tx.py
"""
from web3 import Web3
from database import SessionLocal
from models import Election, Candidate
from blockchain import web3, voting_contract, get_blockchain_candidate_count, get_blockchain_candidate

TX_HASH = "0x1763c3ffcffa79acf5b4f0f9eba4c23eb1e81a7782ce900a761b885dd963f77f"
EXPECTED_DB_ELECTION_ID = 7
EXPECTED_CHAIN_ELECTION_ID = 10
EXPECTED_ELECTION_TITLE = "GZU Student Representative Council Election 2026"


def norm(value):
    import unicodedata
    value = unicodedata.normalize("NFKC", str(value or ""))
    for dash in ("\u2010", "\u2011", "\u2012", "\u2013", "\u2014", "\u2212"):
        value = value.replace(dash, "-")
    return " ".join(value.replace("\u00a0", " ").split()).casefold()


def get_event_arg(args, *names):
    for name in names:
        if name in args:
            return args[name]
    return None


db = SessionLocal()
try:
    print("=== RECONCILE EXISTING TRANSACTION (NO NEW BLOCKCHAIN TX) ===")
    tx_hash = Web3.to_hex(hexstr=TX_HASH)
    receipt = web3.eth.get_transaction_receipt(tx_hash)

    if int(receipt.status) != 1:
        raise RuntimeError(
            f"Transaction status is {receipt.status}, not success. No DB changes made."
        )

    tx = web3.eth.get_transaction(tx_hash)
    if Web3.to_checksum_address(tx["to"]) != Web3.to_checksum_address(voting_contract.address):
        raise RuntimeError("Transaction target is not the configured voting contract.")

    # Decode only CandidateAdded events in this successful receipt.
    try:
        events = voting_contract.events.CandidateAdded().process_receipt(
            receipt, errors=__import__("web3").logs.DISCARD
        )
    except Exception as exc:
        raise RuntimeError(
            "Could not decode CandidateAdded from the receipt using the configured ABI. "
            "No DB changes made. Inspect the deployed contract ABI/log before proceeding. "
            f"Decoder detail: {exc}"
        ) from exc

    parsed = []
    for event in events:
        args = dict(event["args"])
        election_id = get_event_arg(args, "electionId", "_electionId")
        candidate_id = get_event_arg(args, "candidateId", "_candidateId")
        name = get_event_arg(args, "name", "candidateName", "_CandidateName")
        position = get_event_arg(args, "position", "party", "_party", "photoUrl")
        if election_id is not None and candidate_id is not None:
            parsed.append((int(election_id), int(candidate_id), name, position, args))

    parsed = [item for item in parsed if item[0] == EXPECTED_CHAIN_ELECTION_ID]
    if len(parsed) != 1:
        raise RuntimeError(
            f"Expected exactly one CandidateAdded event for chain election "
            f"{EXPECTED_CHAIN_ELECTION_ID}; found {len(parsed)}. No DB changes made. "
            f"Decoded events: {[item[4] for item in parsed]!r}"
        )

    chain_election_id, chain_candidate_id, event_name, event_position, event_args = parsed[0]

    election = db.query(Election).filter(
        Election.id == EXPECTED_DB_ELECTION_ID
    ).first()
    if election is None:
        raise RuntimeError(f"DB election {EXPECTED_DB_ELECTION_ID} does not exist.")
    if norm(election.title) != norm(EXPECTED_ELECTION_TITLE):
        raise RuntimeError(f"Unexpected DB election title: {election.title!r}")
    if int(election.blockchain_election_id or 0) != EXPECTED_CHAIN_ELECTION_ID:
        raise RuntimeError(
            f"DB election mapping conflict: DB {election.id} maps to "
            f"{election.blockchain_election_id!r}, expected {EXPECTED_CHAIN_ELECTION_ID}."
        )
    if election.is_deleted:
        raise RuntimeError("DB election is soft-deleted. No changes made.")

    count = int(get_blockchain_candidate_count(chain_election_id))
    if not 1 <= chain_candidate_id <= count:
        raise RuntimeError(
            f"Event candidate ID {chain_candidate_id} is outside getter count {count}."
        )

    chain_candidate = get_blockchain_candidate(chain_election_id, chain_candidate_id)
    chain_name = chain_candidate.get("name")
    chain_position = chain_candidate.get("position")
    if not chain_name or not chain_position:
        raise RuntimeError(f"Getter returned incomplete candidate data: {chain_candidate!r}")

    # If event data has strings, they must agree with the getter. Never trust event ID alone.
    if event_name is not None and norm(event_name) != norm(chain_name):
        raise RuntimeError(
            f"Event/getter name mismatch: event={event_name!r}, getter={chain_name!r}. "
            "No DB changes made."
        )
    if event_position is not None and norm(event_position) != norm(chain_position):
        raise RuntimeError(
            f"Event/getter position mismatch: event={event_position!r}, "
            f"getter={chain_position!r}. No DB changes made."
        )

    rows = db.query(Candidate).filter(Candidate.election_id == election.id).all()
    for row in rows:
        if row.blockchain_candidate_id == chain_candidate_id:
            if norm(row.name) == norm(chain_name) and norm(row.position) == norm(chain_position):
                print("ALREADY RECONCILED: matching DB candidate row already exists.")
                print(f"Database candidate ID: {row.id}")
                print(f"Blockchain candidate ID: {chain_candidate_id}")
                raise SystemExit(0)
            raise RuntimeError(
                f"Blockchain candidate ID {chain_candidate_id} is already mapped to "
                f"DB candidate {row.id} ({row.name!r}, {row.position!r}). No changes made."
            )
        if norm(row.name) == norm(chain_name) and norm(row.position) == norm(chain_position):
            raise RuntimeError(
                f"A same-name-and-position DB row already exists (ID {row.id}) but has "
                f"blockchain ID {row.blockchain_candidate_id!r}. Manual reconciliation "
                "is required; no changes made."
            )

    new_row = Candidate(
        election_id=election.id,
        name=chain_name,
        position=chain_position,
        blockchain_candidate_id=chain_candidate_id,
        is_withdrawn=False,
    )
    db.add(new_row)
    db.commit()
    db.refresh(new_row)

    print("SUCCESS: candidate row added to PostgreSQL from verified on-chain data.")
    print(f"Database candidate ID: {new_row.id}")
    print(f"Database election ID: {new_row.election_id}")
    print(f"Name: {new_row.name}")
    print(f"Position: {new_row.position}")
    print(f"Blockchain election ID: {chain_election_id}")
    print(f"Blockchain candidate ID: {chain_candidate_id}")
    print(f"Transaction: {tx_hash}")
    print("No blockchain transaction was sent.")
except SystemExit:
    raise
except Exception as exc:
    db.rollback()
    print(f"STOPPED SAFELY: {exc}")
    print("No database candidate row was committed by this run.")
    raise
finally:
    db.close()
