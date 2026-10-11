
from blockchain import (
    voting_contract,
    get_blockchain_election_status,
    start_election_on_blockchain,
)

election_id = 1

print("BEFORE TEST:")
print(get_blockchain_election_status(election_id))

print("\nTEST 1: Backend restart protection")
try:
    start_election_on_blockchain(election_id)
    print("FAILED: The backend did not reject the restart.")
except Exception as error:
    print("Restart rejected:", error)

print("\nTEST 2: Smart contract simulation")
try:
    voting_contract.functions.startElection(election_id).call()
    print("FAILED: The contract simulation did not revert.")
except Exception as error:
    print("Contract correctly rejected the simulated restart.")
    print("Reason:", error)

print("\nAFTER TEST:")
print(get_blockchain_election_status(election_id))
