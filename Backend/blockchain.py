import unicodedata
import os
import json
import time
from pathlib import Path

from dotenv import load_dotenv
from web3 import Web3
from web3.logs import DISCARD


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
BLOCKCHAIN_PROJECT_DIR = BASE_DIR.parent / "Blockchain"
CONTRACT_ADDRESS_FILE = BLOCKCHAIN_PROJECT_DIR / "contract-address.json"


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv(BLOCKCHAIN_PROJECT_DIR / ".env", override=True)

BLOCKCHAIN_PRIVATE_KEY = os.getenv("BLOCKCHAIN_PRIVATE_KEY")

if not BLOCKCHAIN_PRIVATE_KEY:
    raise RuntimeError(
        "BLOCKCHAIN_PRIVATE_KEY was not found in "
        f"{BLOCKCHAIN_PROJECT_DIR / '.env'}"
    )

BLOCKCHAIN_RPC_URL = os.getenv("SEPOLIA_RPC_URL", "").strip()

if not BLOCKCHAIN_RPC_URL:
    raise RuntimeError("SEPOLIA_RPC_URL is missing from Blockchain/.env")


# ============================================================
# BLOCKCHAIN CONNECTION
# ============================================================

web3 = Web3(Web3.HTTPProvider(BLOCKCHAIN_RPC_URL))

if not web3.is_connected():
    raise RuntimeError(
        "Unable to connect to the configured blockchain RPC endpoint."
    )

CHAIN_ID = web3.eth.chain_id

print("\n==============================================")
print("GZU BLOCKCHAIN CONNECTION")
print("==============================================")
print("Chain ID:", CHAIN_ID)

account = web3.eth.account.from_key(BLOCKCHAIN_PRIVATE_KEY)
BLOCKCHAIN_ACCOUNT = account.address

print("Blockchain account:", BLOCKCHAIN_ACCOUNT)

if not CONTRACT_ADDRESS_FILE.exists():
    raise FileNotFoundError(
        "contract-address.json was not found at "
        f"{CONTRACT_ADDRESS_FILE}"
    )

with open(CONTRACT_ADDRESS_FILE, "r", encoding="utf-8") as file:
    contract_data = json.load(file)

CONTRACT_ADDRESS = contract_data.get("address")

if not CONTRACT_ADDRESS:
    raise RuntimeError(
        "contract-address.json does not contain an 'address' value."
    )

CONTRACT_ADDRESS = Web3.to_checksum_address(CONTRACT_ADDRESS)

contract_code = web3.eth.get_code(CONTRACT_ADDRESS)

if not contract_code or contract_code == b"":
    raise RuntimeError(
        f"No contract bytecode found at {CONTRACT_ADDRESS} "
        f"on chain {CHAIN_ID}. Check the network and contract address."
    )

print("Using Voting contract:", CONTRACT_ADDRESS)
print("Contract bytecode verified.")
print("==============================================\n")


# ============================================================
# CONTRACT ABI
# ============================================================

VOTING_ABI = [
    {
        "inputs": [{"internalType": "string", "name": "_title", "type": "string"}],
        "name": "createElection",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "_electionId", "type": "uint256"}],
        "name": "startElection",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "_electionId", "type": "uint256"},
            {"internalType": "string", "name": "_name", "type": "string"},
            {"internalType": "string", "name": "_position", "type": "string"},
        ],
        "name": "addCandidate",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "_electionId", "type": "uint256"},
            {"internalType": "uint256", "name": "_candidateId", "type": "uint256"},
            {"internalType": "bytes32", "name": "_voterHash", "type": "bytes32"},
        ],
        "name": "castVote",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "_electionId", "type": "uint256"}],
        "name": "endElection",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "_electionId", "type": "uint256"}],
        "name": "cancelElection",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "", "type": "uint256"},
            {"internalType": "uint256", "name": "", "type": "uint256"},
        ],
        "name": "candidatePositionHash",
        "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "", "type": "uint256"},
            {"internalType": "bytes32", "name": "", "type": "bytes32"},
            {"internalType": "bytes32", "name": "", "type": "bytes32"},
        ],
        "name": "hasVoted",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "name": "electionStarted",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "name": "electionClosed",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "name": "electionCancelled",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "_electionId", "type": "uint256"},
            {"internalType": "uint256", "name": "_candidateId", "type": "uint256"},
        ],
        "name": "getVoteCount",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "name": "elections",
        "outputs": [
            {"internalType": "string", "name": "title", "type": "string"},
            {"internalType": "bool", "name": "active", "type": "bool"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "electionCount",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "name": "candidateCount",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "", "type": "uint256"},
            {"internalType": "uint256", "name": "", "type": "uint256"},
        ],
        "name": "candidates",
        "outputs": [
            {"internalType": "string", "name": "name", "type": "string"},
            {"internalType": "string", "name": "position", "type": "string"},
            {"internalType": "uint256", "name": "voteCount", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "electionId", "type": "uint256"},
            {"indexed": False, "internalType": "string", "name": "title", "type": "string"},
        ],
        "name": "ElectionCreated",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "electionId", "type": "uint256"},
            {"indexed": True, "internalType": "uint256", "name": "candidateId", "type": "uint256"},
            {"indexed": False, "internalType": "string", "name": "name", "type": "string"},
            {"indexed": False, "internalType": "string", "name": "position", "type": "string"},
        ],
        "name": "CandidateAdded",
        "type": "event",
    },
]


# ============================================================
# CONTRACT OBJECT
# ============================================================

voting_contract = web3.eth.contract(
    address=CONTRACT_ADDRESS,
    abi=VOTING_ABI,
)


# ============================================================
# TRANSACTION HELPER
# ============================================================

def send_transaction(function):
    """
    Build and send a transaction using an RPC gas estimate plus a safety
    margin. A fixed gas limit can be too small as contract storage grows.

    This reduces out-of-gas failures, but no client-side setting can guarantee
    that a transaction will never run out of gas on every future contract state.
    """
    nonce = web3.eth.get_transaction_count(
        BLOCKCHAIN_ACCOUNT,
        "pending",
    )

    # Build first without a hard-coded gas limit, then estimate against the
    # current chain state. If estimation fails, stop before spending gas.
    transaction = function.build_transaction({
        "from": BLOCKCHAIN_ACCOUNT,
        "nonce": nonce,
        "gasPrice": web3.eth.gas_price,
        "chainId": web3.eth.chain_id,
    })

    try:
        estimated_gas = int(web3.eth.estimate_gas(transaction))
    except Exception as exc:
        raise RuntimeError(
            "Blockchain gas estimation failed; transaction was NOT sent. "
            "Check the contract requirements, account permissions, balance, "
            f"and RPC endpoint. Details: {exc}"
        ) from exc

    # Use a 50% buffer, with a minimum 10,000 gas allowance above the estimate.
    gas_limit = max(
        estimated_gas + 10_000,
        (estimated_gas * 150 + 99) // 100,
    )

    # Keep below the latest block gas limit to avoid submitting a transaction
    # that cannot fit in a block. Leave a small additional margin.
    latest_block = web3.eth.get_block("latest")
    block_gas_limit = int(latest_block["gasLimit"])
    max_transaction_gas = int(block_gas_limit * 95 // 100)

    if gas_limit > max_transaction_gas:
        raise RuntimeError(
            "Estimated gas plus the 50% safety margin exceeds the safe "
            f"per-transaction limit ({max_transaction_gas:,} gas; estimate "
            f"{estimated_gas:,}). Transaction was NOT sent. This may indicate "
            "an unusually expensive operation or a contract/RPC issue."
        )

    transaction["gas"] = gas_limit
    print(
        f"Gas estimate: {estimated_gas:,}; "
        f"gas limit with 50% safety margin: {gas_limit:,}"
    )

    signed_transaction = web3.eth.account.sign_transaction(
        transaction,
        BLOCKCHAIN_PRIVATE_KEY,
    )

    transaction_hash = web3.eth.send_raw_transaction(
        signed_transaction.raw_transaction
    )

    tx_hash_hex = transaction_hash.hex()
    print("Blockchain transaction sent:", tx_hash_hex)

    receipt = web3.eth.wait_for_transaction_receipt(transaction_hash)

    if receipt.status != 1:
        print("BLOCKCHAIN TRANSACTION FAILED")
        print("Transaction hash:", tx_hash_hex)
        print("Transaction receipt:", dict(receipt))
        print("Chain ID:", web3.eth.chain_id)
        print("Contract address:", voting_contract.address)
        print("Gas limit used:", gas_limit)
        raise RuntimeError(
            f"Blockchain transaction reverted. Hash: {tx_hash_hex}. "
            "The receipt should be inspected for the revert reason; "
            "do not blindly retry."
        )

    print("Blockchain transaction confirmed:", tx_hash_hex)
    return receipt


# ============================================================
# CREATE ELECTION
# ============================================================

def create_election_on_blockchain(title):
    """Create an election and return the ID emitted by this transaction."""
    print("\nCreating election on blockchain:", title)

    receipt = send_transaction(
        voting_contract.functions.createElection(title)
    )

    try:
        events = voting_contract.events.ElectionCreated().process_receipt(
            receipt,
            errors=DISCARD,
        )
    except Exception as exc:
        raise RuntimeError(
            "The transaction succeeded, but ElectionCreated could not be "
            "decoded. Do not retry automatically. Transaction hash: "
            f"{receipt['transactionHash'].hex()}"
        ) from exc

    matches = [
        event for event in events
        if event["args"]["title"].strip() == title.strip()
    ]
    if len(matches) != 1:
        raise RuntimeError(
            "The transaction succeeded, but exactly one matching "
            "ElectionCreated event was not found. Do not retry automatically. "
            f"Transaction hash: {receipt['transactionHash'].hex()}"
        )

    election_id = int(matches[0]["args"]["electionId"])

    # A receipt may be visible before a load-balanced RPC read endpoint has
    # caught up. Retry only the read/verification, never createElection itself.
    deadline = time.monotonic() + 12.0
    chain_status = None
    last_read_error = None
    while True:
        try:
            chain_status = get_blockchain_election_status(election_id)
            if _normalise_chain_text(chain_status["title"]) == _normalise_chain_text(title):
                break
        except Exception as exc:
            last_read_error = exc

        if time.monotonic() >= deadline:
            raise RuntimeError(
                f"ElectionCreated transaction succeeded, but election {election_id} "
                f"was not visible/verified by the RPC read endpoint within 12 seconds. "
                f"Chain ID={web3.eth.chain_id}; contract={CONTRACT_ADDRESS}; "
                f"receipt block={receipt.get('blockNumber')}; "
                f"last read error={last_read_error!r}. Do not retry automatically. "
                f"Transaction hash: {receipt['transactionHash'].hex()}"
            )
        time.sleep(0.75)

    print("Verified blockchain election ID:", election_id)
    return receipt, election_id


# ============================================================
# START ELECTION
# ============================================================

def start_election_on_blockchain(election_id):
    status = get_blockchain_election_status(election_id)

    if status["active"]:
        raise RuntimeError(f"Election {election_id} is already active.")

    if status["started"] or status["closed"] or status["cancelled"]:
        raise RuntimeError(f"Election {election_id} cannot be restarted.")

    return send_transaction(
        voting_contract.functions.startElection(election_id)
    )


# ============================================================
# ADD CANDIDATE
# ============================================================

def add_candidate_to_blockchain(election_id, name, position, expected_title=None):
    """Add a candidate once; recover its ID from the receipt/on-chain state.

    Never retry a transaction just because event decoding or a subsequent
    getter check fails. A successful receipt may already have changed state.
    """
    election_id = int(election_id)
    status = get_blockchain_election_status(election_id)
    if expected_title is not None and _normalise_chain_text(status["title"]) != _normalise_chain_text(expected_title):
        raise RuntimeError(
            f"Election mapping mismatch: expected title {expected_title!r}, "
            f"but blockchain election {election_id} is titled {status['title']!r}."
        )
    if status["started"] or status["closed"] or status["cancelled"]:
        raise RuntimeError("Candidates can only be added before voting starts.")

    # Guard against retrying a candidate that already exists from a previous
    # transaction whose database save or verification failed.
    before_count = int(get_blockchain_candidate_count(election_id))
    existing = []
    for cid in range(1, before_count + 1):
        try:
            item = get_blockchain_candidate(election_id, cid)
            if (_normalise_chain_text(item["name"]) == _normalise_chain_text(name)
                    and _normalise_chain_text(item["position"]) == _normalise_chain_text(position)):
                existing.append(cid)
        except Exception as exc:
            print(f"Could not inspect existing candidate {cid}: {exc}")
    if len(existing) == 1:
        print(f"Candidate already exists on-chain as ID {existing[0]}; no transaction sent.")
        return None, existing[0]
    if len(existing) > 1:
        raise RuntimeError(
            f"Multiple on-chain candidates already match {name!r} / {position!r}: {existing}. "
            "No transaction sent; manual reconciliation required."
        )

    receipt = send_transaction(
        voting_contract.functions.addCandidate(election_id, name, position)
    )
    tx_hash = receipt["transactionHash"].hex()
    if int(receipt.get("status", 0)) != 1:
        raise RuntimeError(f"Candidate transaction failed on-chain. Transaction hash: {tx_hash}")

    # Event parameter names can differ between the deployed contract ABI and
    # source names (e.g. photoUrl vs position). Match the actual string value
    # without assuming a particular ABI output name.
    try:
        events = voting_contract.events.CandidateAdded().process_receipt(receipt, errors=DISCARD)
    except Exception as exc:
        raise RuntimeError(
            "Candidate transaction succeeded, but its event could not be decoded. "
            f"Do not retry. Verify transaction {tx_hash} and reconcile the database."
        ) from exc

    matches = []
    for event in events:
        args = event.get("args", {})
        if int(args.get("electionId", -1)) != election_id:
            continue
        event_name = args.get("name", "")
        string_values = [v for v in args.values() if isinstance(v, str)]
        if (_normalise_chain_text(event_name) == _normalise_chain_text(name)
                and any(_normalise_chain_text(v) == _normalise_chain_text(position)
                        for v in string_values)):
            matches.append(event)

    event_id = int(matches[0]["args"]["candidateId"]) if len(matches) == 1 else None
    # RPC providers can acknowledge a mined transaction before every backend
    # used by subsequent eth_call requests has caught up. Poll READS only; never
    # resend the transaction. Use the event candidate ID as a useful lower bound
    # when the event was decoded unambiguously.
    event_candidate_id = event_id
    deadline = time.monotonic() + 12.0
    after_count = 0
    exact_ids = []
    last_read_error = None

    while True:
        try:
            after_count = int(get_blockchain_candidate_count(election_id))
            exact_ids = []
            for cid in range(1, after_count + 1):
                try:
                    item = get_blockchain_candidate(election_id, cid)
                    if (_normalise_chain_text(item["name"]) == _normalise_chain_text(name)
                            and _normalise_chain_text(item["position"]) == _normalise_chain_text(position)):
                        exact_ids.append(cid)
                except Exception as exc:
                    last_read_error = exc

            # Stop early when the expected candidate is uniquely visible.
            if len(exact_ids) == 1:
                break

            # If the receipt clearly identifies a new candidate ID but the
            # read endpoint is behind, continue waiting for the state to appear.
            if event_candidate_id is not None and after_count >= event_candidate_id:
                # Candidate count has caught up; a mismatch is no longer just
                # explained by a stale count, so one short final polling window
                # is still allowed for candidate getter consistency.
                pass
        except Exception as exc:
            last_read_error = exc

        if time.monotonic() >= deadline:
            break
        time.sleep(0.75)

    if len(exact_ids) == 1:
        actual_id = exact_ids[0]
        if event_id is not None and event_id != actual_id:
            print(f"WARNING: event candidate ID {event_id} differs from getter match {actual_id}; using getter-verified ID.")
        print(f"Candidate verified on-chain as ID {actual_id}. Transaction: {tx_hash}")
        return receipt, actual_id

    # Include the observed getter state in the error. This is essential for
    # safe recovery: the event proves a transaction emitted a candidate ID,
    # but it is not sufficient to map a DB row when the getter disagrees.
    observed = []
    for cid in range(1, after_count + 1):
        try:
            item = get_blockchain_candidate(election_id, cid)
            observed.append(
                f"{cid}: name={item.get('name')!r}, "
                f"position={item.get('position')!r}"
            )
        except Exception as exc:
            observed.append(f"{cid}: getter error={type(exc).__name__}: {exc}")

    raise RuntimeError(
        "The blockchain transaction succeeded, but the candidate could not be "
        "uniquely verified by name and position. "
        f"Election ID={election_id}; requested name={name!r}; "
        f"requested position={position!r}; event ID={event_id}; "
        f"exact getter matches={exact_ids}; on-chain candidate count={after_count}; "
        f"observed candidates=[{' | '.join(observed)}]. "
        f"Chain ID={web3.eth.chain_id}; contract={CONTRACT_ADDRESS}; "
        f"receipt block={receipt.get('blockNumber')}; "
        f"last read error={last_read_error!r}. "
        "Do not retry automatically. Inspect the transaction receipt and deployed "
        f"contract ABI before reconciling. Transaction hash: {tx_hash}"
    )


# ============================================================
# SUBMIT VOTE
# ============================================================

def submit_vote(election_id, candidate_id, voter_hash):
    election_id = int(election_id)
    candidate_id = int(candidate_id)

    if candidate_id < 1:
        raise ValueError(
            f"Invalid blockchain candidate ID {candidate_id}. "
            "Candidate IDs start at 1; verify the candidate's on-chain mapping."
        )

    if isinstance(voter_hash, str):
        voter_hash = voter_hash.encode("utf-8")
    if not isinstance(voter_hash, bytes) or len(voter_hash) != 32:
        raise ValueError("voter_hash must contain exactly 32 bytes.")

    candidate_count = int(get_blockchain_candidate_count(election_id))
    if candidate_id > candidate_count:
        raise ValueError(
            f"Blockchain candidate ID {candidate_id} does not exist in "
            f"election {election_id}; on-chain candidate count is {candidate_count}."
        )

    candidate = get_blockchain_candidate(election_id, candidate_id)
    if not candidate["name"] or not candidate["position"]:
        raise ValueError(
            f"Blockchain candidate {candidate_id} is not registered "
            f"for election {election_id}."
        )

    status = get_blockchain_election_status(election_id)
    if not status["started"] or status["closed"] or status["cancelled"]:
        raise ValueError("Votes can only be submitted while the election is ongoing.")

    print("\nSubmitting vote to blockchain")
    print("Election:", election_id)
    print("Candidate:", candidate_id)
    print("Candidate name:", candidate["name"])
    print("Position:", candidate["position"])

    receipt = send_transaction(
        voting_contract.functions.castVote(election_id, candidate_id, voter_hash)
    )
    print("Vote successfully recorded.")
    return receipt


# ============================================================
# END ELECTION
# ============================================================

def end_election_on_blockchain(election_id):
    status = get_blockchain_election_status(election_id)
    if status["closed"]:
        return None
    if status["cancelled"]:
        raise RuntimeError(
            f"Election {election_id} was cancelled and cannot be closed."
        )
    return send_transaction(voting_contract.functions.endElection(int(election_id)))


# ============================================================
# CANCEL ELECTION
# ============================================================

def cancel_election_on_blockchain(election_id):
    status = get_blockchain_election_status(election_id)
    if status["cancelled"]:
        return None
    if status["closed"]:
        raise RuntimeError(
            f"Election {election_id} is already closed and cannot be cancelled."
        )
    return send_transaction(voting_contract.functions.cancelElection(int(election_id)))


# ============================================================
# GET ELECTION STATUS
# ============================================================

def get_blockchain_election_status(election_id):
    election_id = int(election_id)
    election = voting_contract.functions.elections(election_id).call()
    return {
        "title": election[0],
        "active": bool(election[1]),
        "started": bool(voting_contract.functions.electionStarted(election_id).call()),
        "closed": bool(voting_contract.functions.electionClosed(election_id).call()),
        "cancelled": bool(voting_contract.functions.electionCancelled(election_id).call()),
    }


# ============================================================
# GET VOTE COUNT
# ============================================================

def get_blockchain_vote_count(election_id, candidate_id):
    return voting_contract.functions.getVoteCount(
        int(election_id), int(candidate_id)
    ).call()


def get_candidate_vote_count(election_id, candidate_id):
    return get_blockchain_vote_count(election_id, candidate_id)


# ============================================================
# GET ELECTION COUNT
# ============================================================

def get_blockchain_election_count():
    return voting_contract.functions.electionCount().call()


# ============================================================
# GET CANDIDATE COUNT
# ============================================================

def get_blockchain_candidate_count(election_id):
    return voting_contract.functions.candidateCount(election_id).call()


# ============================================================
# GET CANDIDATE
# ============================================================

def get_blockchain_candidate(election_id, candidate_id):
    candidate = voting_contract.functions.candidates(
        election_id,
        candidate_id,
    ).call()

    return {
        "name": candidate[0],
        "position": candidate[1],
        "vote_count": candidate[2],
    }


# ============================================================
# SYNCHRONIZE POSTGRESQL WITH BLOCKCHAIN
# ============================================================

def _normalise_chain_text(value):
    """Canonicalise harmless Unicode/whitespace differences for mapping checks.

    NFKC handles compatibility characters; common Unicode dash characters are
    mapped to ASCII hyphen. This does not remove words or punctuation broadly,
    so distinct candidate positions are not silently treated as equivalent.
    """
    value = unicodedata.normalize("NFKC", str(value or ""))
    # Normalize actual Unicode characters, not the literal text \uXXXX.
    value = value.replace("\u00a0", " ")
    for dash in ("\u2010", "\u2011", "\u2012", "\u2013", "\u2014", "\u2212"):
        value = value.replace(dash, "-")
    return " ".join(value.split()).casefold()


def sync_database_to_blockchain(db):
    from models import Election, Candidate

    print("\n==============================================")
    print("BLOCKCHAIN DATABASE SYNCHRONIZATION")
    print("Database: PostgreSQL via SQLAlchemy")
    print("==============================================")

    try:
        elections = (
            db.query(Election)
            .filter(Election.is_deleted.is_(False))
            .order_by(Election.id)
            .all()
        )

        if not elections:
            print("No non-deleted elections found.")
            return

        blockchain_election_count = int(
            get_blockchain_election_count()
        )

        print("Database elections:", len(elections))
        print("Blockchain elections:", blockchain_election_count)

        # Existing election mappings must not be assigned to another
        # database election.
        mapped_election_ids = {
            int(row[0])
            for row in db.query(Election.blockchain_election_id)
            .filter(Election.blockchain_election_id.isnot(None))
            .all()
        }

        for election in elections:
            blockchain_id = election.blockchain_election_id

            # Verify an existing election mapping before using it.
            if blockchain_id is not None:
                blockchain_id = int(blockchain_id)

                if not 1 <= blockchain_id <= blockchain_election_count:
                    print(
                        f"INVALID MAPPING: Database election {election.id} "
                        f"has blockchain ID {blockchain_id}. Skipping."
                    )
                    continue

                try:
                    blockchain_status = get_blockchain_election_status(
                        blockchain_id
                    )
                except Exception as exc:
                    print(
                        f"Unable to read blockchain election "
                        f"{blockchain_id}: {exc}"
                    )
                    continue

                if (
                    _normalise_chain_text(blockchain_status["title"])
                    != _normalise_chain_text(election.title)
                ):
                    print(
                        f"ELECTION MISMATCH: Database election "
                        f"{election.id} is titled {election.title!r}, "
                        f"but blockchain election {blockchain_id} is "
                        f"titled {blockchain_status['title']!r}. "
                        "Existing mapping preserved; skipping."
                    )
                    continue

            else:
                # Find an unclaimed blockchain election with the same
                # title. Duplicate titles are not sufficient to identify
                # the correct election.
                matched_ids = []

                for on_chain_id in range(
                    1, blockchain_election_count + 1
                ):
                    if on_chain_id in mapped_election_ids:
                        continue

                    try:
                        chain_status = get_blockchain_election_status(
                            on_chain_id
                        )

                        if (
                            _normalise_chain_text(chain_status["title"])
                            == _normalise_chain_text(election.title)
                        ):
                            matched_ids.append(on_chain_id)

                    except Exception as exc:
                        print(
                            f"Unable to inspect blockchain election "
                            f"{on_chain_id}: {exc}"
                        )

                if len(matched_ids) != 1:
                    if len(matched_ids) > 1:
                        print(
                            f"AMBIGUOUS ELECTION MAPPING: Database "
                            f"election {election.id} ({election.title!r}) "
                            f"matches blockchain IDs {matched_ids}. "
                            "No mapping was changed."
                        )
                    else:
                        print(
                            f"NO SAFE ELECTION MATCH: Database election "
                            f"{election.id} ({election.title!r}) has no "
                            "unique unclaimed blockchain match. "
                            "No election was created automatically."
                        )

                    continue

                blockchain_id = matched_ids[0]

                try:
                    election.blockchain_election_id = blockchain_id
                    db.commit()
                    mapped_election_ids.add(blockchain_id)

                    print(
                        f"Mapped database election {election.id} "
                        f"to blockchain election {blockchain_id}."
                    )
                except Exception as exc:
                    db.rollback()
                    print(
                        f"Unable to save election mapping for "
                        f"database election {election.id}: {exc}"
                    )
                    continue

                # Refresh the ORM object after a successful commit.
                try:
                    blockchain_status = get_blockchain_election_status(
                        blockchain_id
                    )
                except Exception as exc:
                    print(
                        f"Unable to verify blockchain election "
                        f"{blockchain_id}: {exc}"
                    )
                    continue

            # Load candidates belonging to this database election.
            candidates = (
                db.query(Candidate)
                .filter(Candidate.election_id == election.id)
                .order_by(Candidate.id)
                .all()
            )

            blockchain_candidate_count = int(
                get_blockchain_candidate_count(blockchain_id)
            )

            for candidate in candidates:
                # Withdrawal is a database eligibility flag, not an on-chain deletion.
                # Never register a withdrawn candidate as a new on-chain candidate.
                # If it already has a mapping, leave that historical mapping untouched.
                if bool(getattr(candidate, "is_withdrawn", False)) and not candidate.blockchain_candidate_id:
                    print(
                        f"Skipping withdrawn candidate {candidate.id} "
                        f"({candidate.name!r}); no blockchain record will be created."
                    )
                    continue

                stored_id = candidate.blockchain_candidate_id

                # IDs assigned to other database candidates in this
                # election must not be reused.
                mapped_candidate_ids = {
                    int(row[0])
                    for row in db.query(
                        Candidate.blockchain_candidate_id
                    )
                    .filter(
                        Candidate.election_id == election.id,
                        Candidate.blockchain_candidate_id.isnot(None),
                        Candidate.id != candidate.id,
                    )
                    .all()
                }

                # Verify an existing candidate mapping. Never silently
                # overwrite a conflicting stored ID.
                # Older records may store 0 as a placeholder. Blockchain
                # candidate IDs are 1-based, so 0 means "unmapped".
                if stored_id is not None and int(stored_id) > 0:
                    stored_id = int(stored_id)

                    if stored_id in mapped_candidate_ids:
                        print(
                            f"CANDIDATE ID CONFLICT: Database candidate "
                            f"{candidate.id} shares blockchain candidate "
                            f"ID {stored_id} with another database "
                            "candidate in the same election. Skipping."
                        )
                        continue

                    if 1 <= stored_id <= blockchain_candidate_count:
                        try:
                            chain_candidate = get_blockchain_candidate(
                                blockchain_id, stored_id
                            )

                            if (
                                _normalise_chain_text(
                                    chain_candidate["name"]
                                )
                                == _normalise_chain_text(candidate.name)
                                and _normalise_chain_text(
                                    chain_candidate["position"]
                                )
                                == _normalise_chain_text(candidate.position)
                            ):
                                # The existing mapping is verified.
                                continue

                        except Exception as exc:
                            print(
                                f"Unable to verify candidate "
                                f"{candidate.id}, blockchain ID "
                                f"{stored_id}: {exc}"
                            )

                    print(
                        f"CANDIDATE MISMATCH: Database candidate "
                        f"{candidate.id} has blockchain ID {stored_id}, "
                        "but the on-chain record does not match. "
                        "Existing mapping preserved for investigation."
                    )
                    continue

                # No stored mapping: look for every matching, unclaimed
                # on-chain candidate.
                matched_candidate_ids = []

                for on_chain_id in range(
                    1, blockchain_candidate_count + 1
                ):
                    if on_chain_id in mapped_candidate_ids:
                        continue

                    try:
                        chain_candidate = get_blockchain_candidate(
                            blockchain_id, on_chain_id
                        )

                        if (
                            _normalise_chain_text(
                                chain_candidate["name"]
                            )
                            == _normalise_chain_text(candidate.name)
                            and _normalise_chain_text(
                                chain_candidate["position"]
                            )
                            == _normalise_chain_text(candidate.position)
                        ):
                            matched_candidate_ids.append(on_chain_id)

                    except Exception as exc:
                        print(
                            f"Unable to read blockchain candidate "
                            f"{on_chain_id}: {exc}"
                        )

                if len(matched_candidate_ids) == 1:
                    candidate.blockchain_candidate_id = (
                        matched_candidate_ids[0]
                    )

                    try:
                        db.commit()
                        print(
                            f"Mapped database candidate {candidate.id} "
                            f"to blockchain candidate "
                            f"{matched_candidate_ids[0]} in election "
                            f"{blockchain_id}."
                        )
                    except Exception as exc:
                        db.rollback()
                        print(
                            f"Unable to save candidate mapping for "
                            f"{candidate.id}: {exc}"
                        )

                    continue

                if len(matched_candidate_ids) > 1:
                    print(
                        f"AMBIGUOUS CANDIDATE MAPPING: Database "
                        f"candidate {candidate.id} matches blockchain "
                        f"candidate IDs {matched_candidate_ids} in "
                        f"election {blockchain_id}. Manual review needed."
                    )
                    continue

                # Only register a new candidate before the election
                # starts and while it is neither closed nor cancelled.
                if (
                    not blockchain_status["started"]
                    and not blockchain_status["closed"]
                    and not blockchain_status["cancelled"]
                ):
                    try:
                        _, new_candidate_id = add_candidate_to_blockchain(
                            blockchain_id,
                            candidate.name,
                            candidate.position,
                            expected_title=election.title,
                        )

                        candidate.blockchain_candidate_id = int(
                            new_candidate_id
                        )
                        db.commit()

                        blockchain_candidate_count = int(
                            get_blockchain_candidate_count(blockchain_id)
                        )

                        print(
                            f"Registered database candidate "
                            f"{candidate.id} as blockchain candidate "
                            f"{new_candidate_id} in election "
                            f"{blockchain_id}."
                        )

                    except Exception as exc:
                        db.rollback()
                        print(
                            f"Unable to register candidate "
                            f"{candidate.name!r} in blockchain election "
                            f"{blockchain_id}: {exc}"
                        )
                else:
                    print(
                        f"UNMATCHED CANDIDATE: {candidate.name!r} was "
                        f"not found in blockchain election {blockchain_id}. "
                        "No automatic changes made because the election "
                        "has started or is closed/cancelled."
                    )

            # Reconcile terminal on-chain states into PostgreSQL. A cancelled
            # or closed election must not remain labelled as ongoing in the UI.
            # This never reopens an election and does not alter blockchain data.
            try:
                blockchain_status = get_blockchain_election_status(
                    blockchain_id
                )

                chain_cancelled = bool(blockchain_status.get("cancelled"))
                chain_closed = bool(blockchain_status.get("closed"))

                if chain_cancelled and election.status not in ("cancelled", "closed"):
                    election.status = "cancelled"
                    db.commit()
                    print(
                        f"Reconciled election {election.id} to CANCELLED "
                        "from its blockchain status."
                    )
                elif chain_closed and election.status not in ("closed", "cancelled"):
                    election.status = "closed"
                    db.commit()
                    print(
                        f"Reconciled election {election.id} to CLOSED "
                        "from its blockchain status."
                    )
                elif bool(blockchain_status.get("active")) != (
                    election.status == "ongoing"
                ):
                    print(
                        f"LIFECYCLE DIFFERENCE: Database election "
                        f"{election.id} status={election.status!r}; "
                        f"blockchain active="
                        f"{blockchain_status.get('active')!r}."
                    )
            except Exception as exc:
                db.rollback()
                print(
                    f"Unable to compare/reconcile lifecycle status for election "
                    f"{election.id}: {exc}"
                )

    except Exception as exc:
        db.rollback()
        print(f"BLOCKCHAIN SYNCHRONIZATION ERROR: {exc}")
        raise

    print("\nBlockchain synchronization complete.")
    print("==============================================")
