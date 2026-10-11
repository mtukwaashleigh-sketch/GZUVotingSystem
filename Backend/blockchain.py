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

CONTRACT_ADDRESS_FILE = (
    BLOCKCHAIN_PROJECT_DIR / "contract-address.json"
)


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv(BLOCKCHAIN_PROJECT_DIR / ".env", override=True)

BLOCKCHAIN_PRIVATE_KEY = os.getenv(
    "BLOCKCHAIN_PRIVATE_KEY"
)

if not BLOCKCHAIN_PRIVATE_KEY:

    raise Exception(
        "BLOCKCHAIN_PRIVATE_KEY was not found in "
        f"{BASE_DIR / '.env'}"
    )


# ============================================================
# BLOCKCHAIN CONNECTION
# ============================================================

BLOCKCHAIN_RPC_URL = os.getenv("SEPOLIA_RPC_URL", "").strip()

if not BLOCKCHAIN_RPC_URL:
    raise Exception(
        "SEPOLIA_RPC_URL is missing from Blockchain/.env"
    )

web3 = Web3(
    Web3.HTTPProvider(BLOCKCHAIN_RPC_URL)
)


if not web3.is_connected():
    raise Exception(
        "Unable to connect to the configured Sepolia RPC endpoint. "
        "Check your RPC configuration and internet connection."
    )


print("")
print("==============================================")
print("GZU BLOCKCHAIN CONNECTION")
print("==============================================")
print("Connected to: Sepolia RPC endpoint (URL hidden)")
print(
    "Chain ID:",
    web3.eth.chain_id
)


# ============================================================
# BLOCKCHAIN ACCOUNT
# ============================================================

account = web3.eth.account.from_key(
    BLOCKCHAIN_PRIVATE_KEY
)

BLOCKCHAIN_ACCOUNT = account.address

print(
    "Blockchain account:",
    BLOCKCHAIN_ACCOUNT
)


# ============================================================
# CONTRACT ADDRESS
# ============================================================

if not CONTRACT_ADDRESS_FILE.exists():

    raise Exception(
        "contract-address.json was not found.\n"
        f"Expected location:\n"
        f"{CONTRACT_ADDRESS_FILE}\n\n"
        "Deploy the Voting contract first."
    )


with open(
    CONTRACT_ADDRESS_FILE,
    "r",
    encoding="utf-8"
) as file:

    contract_data = json.load(file)


CONTRACT_ADDRESS = contract_data.get("address")


if not CONTRACT_ADDRESS:

    raise Exception(
        "contract-address.json does not contain "
        "an 'address' value."
    )


CONTRACT_ADDRESS = Web3.to_checksum_address(
    CONTRACT_ADDRESS
)


# ============================================================
# VERIFY CONTRACT EXISTS
# ============================================================

contract_code = web3.eth.get_code(
    CONTRACT_ADDRESS
)


if contract_code == b"" or contract_code.hex() == "0x":

    raise Exception(
        "\n"
        "NO CONTRACT CODE FOUND AT:\n"
        f"{CONTRACT_ADDRESS}\n\n"
        "The contract address is stale or belongs "
        "to another Hardhat blockchain session.\n\n"
        "Fix:\n"
        "1. Start 'npx hardhat node'\n"
        "2. Deploy the contract again\n"
        "3. Make sure contract-address.json is updated."
    )


print(
    "Using Voting contract:",
    CONTRACT_ADDRESS
)

print(
    "Contract bytecode verified."
)

print("==============================================")
print("")


# ============================================================
# CONTRACT ABI
# ============================================================

VOTING_ABI = [

    # --------------------------------------------------------
    # createElection
    # --------------------------------------------------------

    {
        "inputs": [
            {
                "internalType": "string",
                "name": "_title",
                "type": "string"
            }
        ],
        "name": "createElection",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },


    # --------------------------------------------------------
    # startElection
    # --------------------------------------------------------

    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "_electionId",
                "type": "uint256"
            }
        ],
        "name": "startElection",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },


    # --------------------------------------------------------
    # addCandidate
    # --------------------------------------------------------

    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "_electionId",
                "type": "uint256"
            },
            {
                "internalType": "string",
                "name": "_name",
                "type": "string"
            },
            {
                "internalType": "string",
                "name": "_position",
                "type": "string"
            }
        ],
        "name": "addCandidate",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },


    # --------------------------------------------------------
    # castVote
    # --------------------------------------------------------

    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "_electionId",
                "type": "uint256"
            },
            {
                "internalType": "uint256",
                "name": "_candidateId",
                "type": "uint256"
            },
            {
                "internalType": "bytes32",
                "name": "_voterHash",
                "type": "bytes32"
            }
        ],
        "name": "castVote",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },


    # --------------------------------------------------------
    # endElection
    # --------------------------------------------------------

    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "_electionId",
                "type": "uint256"
            }
        ],
        "name": "endElection",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },


    # --------------------------------------------------------
    # cancelElection
    # --------------------------------------------------------
    {
        "inputs": [{"internalType": "uint256", "name": "_electionId", "type": "uint256"}],
        "name": "cancelElection", "outputs": [], "stateMutability": "nonpayable", "type": "function"
    },
    {"inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}, {"internalType": "uint256", "name": "", "type": "uint256"}], "name": "candidatePositionHash",
     "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}, {"internalType": "bytes32", "name": "", "type": "bytes32"}, {"internalType": "bytes32", "name": "", "type": "bytes32"}], "name": "hasVoted",
     "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "name": "electionStarted",
     "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "name": "electionClosed",
     "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "name": "electionCancelled",
     "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "view", "type": "function"},

    # --------------------------------------------------------
    # getVoteCount
    # --------------------------------------------------------

    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "_electionId",
                "type": "uint256"
            },
            {
                "internalType": "uint256",
                "name": "_candidateId",
                "type": "uint256"
            }
        ],
        "name": "getVoteCount",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },


    # --------------------------------------------------------
    # elections
    # --------------------------------------------------------

    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "name": "elections",
        "outputs": [
            {
                "internalType": "string",
                "name": "title",
                "type": "string"
            },
            {
                "internalType": "bool",
                "name": "active",
                "type": "bool"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },


    # --------------------------------------------------------
    # electionCount
    # --------------------------------------------------------

    {
        "inputs": [],
        "name": "electionCount",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },


    # --------------------------------------------------------
    # candidateCount
    # --------------------------------------------------------

    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "name": "candidateCount",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },


    # --------------------------------------------------------
    # candidates
    # --------------------------------------------------------

    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            },
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "name": "candidates",
        "outputs": [
            {
                "internalType": "string",
                "name": "name",
                "type": "string"
            },
            {
                "internalType": "string",
                "name": "position",
                "type": "string"
            },
            {
                "internalType": "uint256",
                "name": "voteCount",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]


# ============================================================
# CONTRACT OBJECT
# ============================================================

voting_contract = web3.eth.contract(
    address=CONTRACT_ADDRESS,
    abi=VOTING_ABI
)


# ============================================================
# TRANSACTION HELPER
# ============================================================

def send_transaction(function):

    nonce = web3.eth.get_transaction_count(
        BLOCKCHAIN_ACCOUNT,
        "pending"
    )

    transaction = function.build_transaction({

        "from": BLOCKCHAIN_ACCOUNT,

        "nonce": nonce,

        "gas": 500000,

        "gasPrice": web3.eth.gas_price,

        "chainId": web3.eth.chain_id
    })


    signed_transaction = (
        web3.eth.account.sign_transaction(
            transaction,
            BLOCKCHAIN_PRIVATE_KEY
        )
    )


    transaction_hash = (
        web3.eth.send_raw_transaction(
            signed_transaction.raw_transaction
        )
    )


    print(
        "Blockchain transaction sent:",
        transaction_hash.hex()
    )


    receipt = (
        web3.eth.wait_for_transaction_receipt(
            transaction_hash
        )
    )


    if receipt.status != 1:
        print("BLOCKCHAIN TRANSACTION FAILED")
        print("Transaction hash:", transaction_hash.hex())
        print("Transaction receipt:", dict(receipt))
        print("Chain ID:", web3.eth.chain_id)
        print("Contract address:", voting_contract.address)

    raise Exception(
        f"Blockchain transaction reverted. "
        f"Hash: {transaction_hash.hex()}"
    )



    print(
        "Blockchain transaction confirmed:",
        transaction_hash.hex()
    )


    return receipt


# ============================================================
# CREATE ELECTION
# ============================================================

def create_election_on_blockchain(title):

    print("")
    print(
        "Creating election on blockchain:",
        title
    )


    function = (
        voting_contract
        .functions
        .createElection(title)
    )


    receipt = send_transaction(function)


    election_id = (
        voting_contract
        .functions
        .electionCount()
        .call()
    )


    print(
        "Blockchain election ID:",
        election_id
    )


    return (
        receipt,
        election_id
    )


# ============================================================
# START ELECTION
# ============================================================

def start_election_on_blockchain(election_id):
    status = get_blockchain_election_status(election_id)
    if status["active"]:
        raise Exception(f"Election {election_id} is already active.")
    if status["started"] or status["closed"] or status["cancelled"]:
        raise Exception(f"Election {election_id} cannot be restarted.")
    function = voting_contract.functions.startElection(election_id)
    return send_transaction(function)


# ============================================================
# ADD CANDIDATE
# ============================================================

def add_candidate_to_blockchain(
    election_id,
    name,
    position
):

    print("")
    print(
        "Adding candidate to blockchain"
    )

    print(
        "Election:",
        election_id
    )

    print(
        "Name:",
        name
    )

    print(
        "Position:",
        position
    )


    # Verify election exists.

    status = get_blockchain_election_status(
        election_id
    )


    if status["started"] or status["closed"] or status["cancelled"]:
        raise Exception("Candidates can only be added before voting starts.")

    function = (
        voting_contract
        .functions
        .addCandidate(
            election_id,
            name,
            position
        )
    )


    receipt = send_transaction(
        function
    )


    blockchain_candidate_id = (
        voting_contract
        .functions
        .candidateCount(
            election_id
        )
        .call()
    )


    print(
        "Blockchain candidate ID:",
        blockchain_candidate_id
    )


    return (
        receipt,
        blockchain_candidate_id
    )


# ============================================================
# SUBMIT VOTE
# ============================================================

def submit_vote(
    election_id,
    candidate_id,
    voter_hash
):

    if isinstance(voter_hash, str):

        voter_hash = voter_hash.encode(
            "utf-8"
        )


    if len(voter_hash) != 32:

        raise ValueError(
            "voter_hash must contain exactly "
            "32 bytes."
        )


    print("")
    print(
        "Submitting vote to blockchain"
    )

    print(
        "Election:",
        election_id
    )

    print(
        "Candidate:",
        candidate_id
    )


    function = (
        voting_contract
        .functions
        .castVote(
            election_id,
            candidate_id,
            voter_hash
        )
    )


    receipt = send_transaction(
        function
    )


    print(
        "Vote successfully recorded."
    )


    return receipt


# ============================================================
# END ELECTION
# ============================================================

def end_election_on_blockchain(election_id):
    status = get_blockchain_election_status(election_id)
    if status["closed"]:
        return None
    if status["cancelled"]:
        raise Exception(f"Election {election_id} was cancelled and cannot be closed.")
    return send_transaction(voting_contract.functions.endElection(election_id))


def cancel_election_on_blockchain(election_id):
    status = get_blockchain_election_status(election_id)
    if status["cancelled"]:
        return None
    if status["closed"]:
        raise Exception(f"Election {election_id} is already closed and cannot be cancelled.")
    return send_transaction(voting_contract.functions.cancelElection(election_id))


# ============================================================
# GET ELECTION STATUS
# ============================================================

def get_blockchain_election_status(election_id):
    election = voting_contract.functions.elections(election_id).call()
    return {
        "title": election[0],
        "active": bool(election[1]),
        "started": bool(voting_contract.functions.electionStarted(election_id).call()),
        "closed": bool(voting_contract.functions.electionClosed(election_id).call()),
        "cancelled": bool(voting_contract.functions.electionCancelled(election_id).call()),
    }


# ============================================================
# GET BLOCKCHAIN VOTE COUNT
# ============================================================

def get_blockchain_vote_count(
    election_id,
    candidate_id
):

    return (
        voting_contract
        .functions
        .getVoteCount(
            election_id,
            candidate_id
        )
        .call()
    )


# ============================================================
# COMPATIBILITY FUNCTION
# ============================================================

def get_candidate_vote_count(
    election_id,
    candidate_id
):

    return get_blockchain_vote_count(
        election_id,
        candidate_id
    )


# ============================================================
# GET ELECTION COUNT
# ============================================================

def get_blockchain_election_count():

    return (
        voting_contract
        .functions
        .electionCount()
        .call()
    )


# ============================================================
# GET CANDIDATE COUNT
# ============================================================

def get_blockchain_candidate_count(
    election_id
):

    return (
        voting_contract
        .functions
        .candidateCount(
            election_id
        )
        .call()
    )


# ============================================================
# GET CANDIDATE
# ============================================================

def get_blockchain_candidate(
    election_id,
    candidate_id
):

    candidate = (
        voting_contract
        .functions
        .candidates(
            election_id,
            candidate_id
        )
        .call()
    )


    return {
        "name": candidate[0],
        "position": candidate[1],
        "vote_count": candidate[2]
    }


# ============================================================
# SYNCHRONIZE SQLITE WITH BLOCKCHAIN
# ============================================================


def sync_database_to_blockchain(db):
    from models import Election, Candidate

    print("")
    print("==============================================")
    print("BLOCKCHAIN DATABASE SYNCHRONIZATION")
    print("==============================================")

    elections = (
        db.query(Election)
        .filter(Election.is_deleted == False)
        .order_by(Election.id)
        .all()
    )

    if not elections:
        print("No active SQLite elections found.")
        return

    blockchain_election_count = get_blockchain_election_count()

    print("SQLite elections:", len(elections))
    print("Blockchain elections:", blockchain_election_count)

    # First, assign a blockchain ID to each election.
    for election in elections:
        blockchain_id = election.blockchain_election_id

        if blockchain_id is not None:
            if blockchain_id < 1 or blockchain_id > blockchain_election_count:
                print(
                    f"WARNING: SQLite election {election.id} has invalid "
                    f"blockchain ID {blockchain_id}. Skipping it."
                )
                continue

            try:
                chain_status = get_blockchain_election_status(blockchain_id)
                if chain_status["title"] != election.title:
                    print(
                        f"WARNING: Title mismatch for SQLite election "
                        f"{election.id} and blockchain election {blockchain_id}. "
                        "Skipping it."
                    )
                    continue
            except Exception as exc:
                print(
                    f"Unable to verify blockchain election {blockchain_id}: {exc}"
                )
                continue

        else:
            # Match an existing on-chain election by title before creating one.
            matched_id = None

            for candidate_id in range(1, blockchain_election_count + 1):
                try:
                    chain_status = get_blockchain_election_status(candidate_id)
                    if chain_status["title"] == election.title:
                        matched_id = candidate_id
                        break
                except Exception:
                    continue

            
            if matched_id is None:
                print("Creating blockchain election:", election.title)
                try:
                    _, matched_id = create_election_on_blockchain(
                        election.title
                    )
                    blockchain_election_count = (
                        get_blockchain_election_count()
                    )
                except Exception as exc:
                    print(
                        f"Unable to create blockchain election for "
                        f"SQLite election {election.id}: {exc}"
                    )
                    continue

            # Prevent two SQLite elections from sharing one blockchain ID.
            existing_mapping = (
                db.query(Election)
                .filter(
                    Election.blockchain_election_id == matched_id,
                    Election.id != election.id
                )
                .first()
            )

            if existing_mapping:
                print(
                    f"WARNING: Blockchain election {matched_id} is already "
                    f"mapped to SQLite election {existing_mapping.id}. "
                    f"SQLite election {election.id} will not be mapped."
                )
                continue

            election.blockchain_election_id = matched_id

            try:
                db.commit()
            except Exception as exc:
                db.rollback()
                print(
                    f"Unable to save blockchain mapping for SQLite "
                    f"election {election.id}: {exc}"
                )
                continue

            blockchain_id = matched_id

            print(
                f"Mapped SQLite election {election.id} "
                f"to blockchain election {blockchain_id}"
            )

                

        # Synchronize candidates using the blockchain ID, not SQLite ID.
        try:
            blockchain_status = get_blockchain_election_status(blockchain_id)
        except Exception as exc:
            print(
                f"Unable to read blockchain election {blockchain_id}: {exc}"
            )
            continue

        candidates = (
            db.query(Candidate)
            .filter(Candidate.election_id == election.id)
            .order_by(Candidate.id)
            .all()
        )

        blockchain_candidate_count = get_blockchain_candidate_count(blockchain_id)

        for index, candidate in enumerate(candidates, start=1):
            if index <= blockchain_candidate_count:
                try:
                    chain_candidate = get_blockchain_candidate(
                        blockchain_id, index
                    )

                    if (
                        chain_candidate["name"] == candidate.name
                        and chain_candidate["position"] == candidate.position
                    ):
                        candidate.blockchain_candidate_id = index
                        db.commit()
                    else:
                        print(
                            f"Candidate mismatch for SQLite candidate "
                            f"{candidate.id} in election {election.id}; "
                            "not changing the blockchain."
                        )
                except Exception as exc:
                    print(
                        f"Unable to verify candidate {index} in blockchain "
                        f"election {blockchain_id}: {exc}"
                    )
                continue

            if (
                not blockchain_status["started"]
                and not blockchain_status["closed"]
                and not blockchain_status["cancelled"]
            ):
                try:
                    _, chain_candidate_id = add_candidate_to_blockchain(
                        blockchain_id,
                        candidate.name,
                        candidate.position,
                    )
                    candidate.blockchain_candidate_id = chain_candidate_id
                    db.commit()
                    blockchain_candidate_count = get_blockchain_candidate_count(
                        blockchain_id
                    )
                except Exception as exc:
                    print(
                        f"Unable to add candidate {candidate.name!r} "
                        f"to blockchain election {blockchain_id}: {exc}"
                    )

        # Report lifecycle differences without automatically starting,
        # closing, or cancelling elections during startup.
        if bool(blockchain_status.get("active")) != (
            election.status == "ongoing"
        ):
            print(
                f"Lifecycle reconciliation needed for SQLite election "
                f"{election.id}: SQLite={election.status!r}, "
                f"blockchain_active={blockchain_status.get('active')!r}"
            )

    print("")
    print("Blockchain synchronization complete.")
    print("==============================================")
