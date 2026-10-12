
import os
import json
from pathlib import Path

from dotenv import load_dotenv
from web3 import Web3


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
    nonce = web3.eth.get_transaction_count(
        BLOCKCHAIN_ACCOUNT,
        "pending",
    )

    transaction = function.build_transaction({
        "from": BLOCKCHAIN_ACCOUNT,
        "nonce": nonce,
        "gas": 500000,
        "gasPrice": web3.eth.gas_price,
        "chainId": web3.eth.chain_id,
    })

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

        raise RuntimeError(
            f"Blockchain transaction reverted. Hash: {tx_hash_hex}"
        )

    print("Blockchain transaction confirmed:", tx_hash_hex)
    return receipt


# ============================================================
# CREATE ELECTION
# ============================================================

def create_election_on_blockchain(title):
    print("\nCreating election on blockchain:", title)

    receipt = send_transaction(
        voting_contract.functions.createElection(title)
    )

    election_id = voting_contract.functions.electionCount().call()

    print("Blockchain election ID:", election_id)
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
    print("\nAdding candidate to blockchain")
    print("Election:", election_id)
    print("Name:", name)
    print("Position:", position)

    status = get_blockchain_election_status(election_id)

    if expected_title is not None and _normalise_chain_text(status["title"]) != _normalise_chain_text(expected_title):
        raise RuntimeError(
            f"Election mapping mismatch: expected title {expected_title!r}, "
            f"but blockchain election {election_id} is titled {status['title']!r}."
        )

    if status["started"] or status["closed"] or status["cancelled"]:
        raise RuntimeError(
            "Candidates can only be added before voting starts."
        )

    receipt = send_transaction(
        voting_contract.functions.addCandidate(
            election_id,
            name,
            position,
        )
    )

    blockchain_candidate_id = (
        voting_contract.functions.candidateCount(election_id).call()
    )

    if blockchain_candidate_id < 1:
        raise RuntimeError(
            "Candidate registration transaction succeeded, but the "
            "blockchain candidate count is invalid."
        )

    print("Blockchain candidate ID:", blockchain_candidate_id)
    return receipt, blockchain_candidate_id


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

    candidate_count = get_blockchain_candidate_count(election_id)

    if candidate_id > candidate_count:
        raise ValueError(
            f"Blockchain candidate ID {candidate_id} does not exist in "
            f"election {election_id}; on-chain candidate count is "
            f"{candidate_count}."
        )

    candidate = get_blockchain_candidate(election_id, candidate_id)

    if not candidate["name"] or not candidate["position"]:
        raise ValueError(
            f"Blockchain candidate {candidate_id} is not registered "
            f"for election {election_id}."
        )

    print("\nSubmitting vote to blockchain")
    print("Election:", election_id)
    print("Candidate:", candidate_id)
    print("Candidate name:", candidate["name"])
    print("Position:", candidate["position"])

    receipt = send_transaction(
        voting_contract.functions.castVote(
            election_id,
            candidate_id,
            voter_hash,
        )
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

    return send_transaction(
        voting_contract.functions.endElection(election_id)
    )


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

    return send_transaction(
        voting_contract.functions.cancelElection(election_id)
    )


# ============================================================
# GET ELECTION STATUS
# ============================================================

def get_blockchain_election_status(election_id):
    election = voting_contract.functions.elections(election_id).call()

    return {
        "title": election[0],
        "active": bool(election[1]),
        "started": bool(
            voting_contract.functions.electionStarted(election_id).call()
        ),
        "closed": bool(
            voting_contract.functions.electionClosed(election_id).call()
        ),
        "cancelled": bool(
            voting_contract.functions.electionCancelled(election_id).call()
        ),
    }


# ============================================================
# GET VOTE COUNT
# ============================================================

def get_blockchain_vote_count(election_id, candidate_id):
    return voting_contract.functions.getVoteCount(
        election_id,
        candidate_id,
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
    """Normalise text for safe, case-insensitive comparison."""
    return " ".join(str(value or "").split()).casefold()


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

            # Report lifecycle differences without changing either side.
            try:
                blockchain_status = get_blockchain_election_status(
                    blockchain_id
                )

                if bool(blockchain_status.get("active")) != (
                    election.status == "ongoing"
                ):
                    print(
                        f"LIFECYCLE DIFFERENCE: Database election "
                        f"{election.id} status={election.status!r}; "
                        f"blockchain active="
                        f"{blockchain_status.get('active')!r}."
                    )
            except Exception as exc:
                print(
                    f"Unable to compare lifecycle status for election "
                    f"{election.id}: {exc}"
                )

    except Exception as exc:
        db.rollback()
        print(f"BLOCKCHAIN SYNCHRONIZATION ERROR: {exc}")
        raise

    print("\nBlockchain synchronization complete.")
    print("==============================================")
