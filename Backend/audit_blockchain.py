
from blockchain import (
    get_blockchain_election_count,
    get_blockchain_election_status,
    get_blockchain_candidate_count,
    get_blockchain_candidate,
)


def audit_blockchain():
    print("\n==============================================")
    print("GZU LIVE BLOCKCHAIN AUDIT")
    print("==============================================")

    election_count = get_blockchain_election_count()
    print("Total blockchain elections:", election_count)

    for election_id in range(1, election_count + 1):
        print(f"\n========== BLOCKCHAIN ELECTION {election_id} ==========")

        try:
            status = get_blockchain_election_status(election_id)
            print("Title:", status["title"])
            print("Active:", status["active"])
            print("Started:", status["started"])
            print("Closed:", status["closed"])
            print("Cancelled:", status["cancelled"])

            candidate_count = get_blockchain_candidate_count(
                election_id
            )
            print("Candidate count:", candidate_count)

            for candidate_id in range(1, candidate_count + 1):
                candidate = get_blockchain_candidate(
                    election_id, candidate_id
                )
                print({
                    "blockchain_election_id": election_id,
                    "blockchain_candidate_id": candidate_id,
                    "name": candidate["name"],
                    "position": candidate["position"],
                    "vote_count": candidate["vote_count"],
                })

        except Exception as exc:
            print(f"ERROR reading election {election_id}: {exc}")

    print("\nBlockchain audit complete. No transactions were sent.")


if __name__ == "__main__":
    audit_blockchain()
