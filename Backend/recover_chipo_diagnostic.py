"""Read-only diagnostic for the previously successful Chipo candidate transaction.

Run from Backend after confirming Blockchain/.env and contract-address.json point
at the intended Sepolia deployment. This script DOES NOT send transactions or
modify the database.
"""

from blockchain import (
    web3,
    voting_contract,
    get_blockchain_candidate_count,
    get_blockchain_candidate,
    _normalise_chain_text,
)

TX_HASH = "0xb5b3f41be185d7e648d22993c5dc20a9728e4878a46c979fa0a1d7846b9d1d9d"
ELECTION_ID = 10
EXPECTED_NAME = "Chipo Muchengeti"
EXPECTED_POSITION = "Secretary General — Candidate 2"


def main():
    print("READ-ONLY CHIPO CANDIDATE RECOVERY DIAGNOSTIC")
    print("Chain ID:", web3.eth.chain_id)
    print("Contract:", voting_contract.address)
    print("Transaction:", TX_HASH)

    tx_hash = web3.to_bytes(hexstr=TX_HASH)
    try:
        tx = web3.eth.get_transaction(tx_hash)
    except Exception as exc:
        print("TRANSACTION LOOKUP FAILED:", repr(exc))
        return

    print("Transaction sender:", tx.get("from"))
    print("Transaction recipient:", tx.get("to"))
    print("Transaction block:", tx.get("blockNumber"))
    print("Transaction input:", tx.get("input", b"").hex())

    try:
        receipt = web3.eth.get_transaction_receipt(tx_hash)
    except Exception as exc:
        print("RECEIPT LOOKUP FAILED:", repr(exc))
        print("No recovery or retry performed.")
        return

    print("Receipt status:", receipt.get("status"))
    print("Receipt block:", receipt.get("blockNumber"))
    print("Gas used:", receipt.get("gasUsed"))
    print("Raw log count:", len(receipt.get("logs", [])))

    try:
        events = voting_contract.events.CandidateAdded().process_receipt(
            receipt, errors="DISCARD"
        )
        print("Decoded CandidateAdded events:", len(events))
        for event in events:
            print("Decoded event args:", dict(event.get("args", {})))
    except Exception as exc:
        print("CandidateAdded decoding failed:", repr(exc))

    # Print raw topics/data for manual ABI comparison if decoding failed.
    for index, log in enumerate(receipt.get("logs", []), start=1):
        print(f"RAW LOG {index}: address={log.get('address')}")
        print("  topics:", [topic.hex() for topic in log.get("topics", [])])
        print("  data:", log.get("data", b"").hex())

    if int(receipt.get("status", 0)) != 1:
        print("Transaction did not succeed. Do not map a candidate from it.")
        return

    try:
        count = int(get_blockchain_candidate_count(ELECTION_ID))
        print(f"Current candidate count for election {ELECTION_ID}:", count)
    except Exception as exc:
        print("Candidate count getter failed:", repr(exc))
        return

    matches = []
    for candidate_id in range(1, count + 1):
        try:
            candidate = get_blockchain_candidate(ELECTION_ID, candidate_id)
            print(f"Getter candidate {candidate_id}:", repr(candidate))
            if (
                _normalise_chain_text(candidate.get("name"))
                == _normalise_chain_text(EXPECTED_NAME)
                and _normalise_chain_text(candidate.get("position"))
                == _normalise_chain_text(EXPECTED_POSITION)
            ):
                matches.append(candidate_id)
        except Exception as exc:
            print(f"Getter failed for candidate {candidate_id}:", repr(exc))

    print("Exact normalized getter matches:", matches)
    if len(matches) == 1:
        print("RECOVERY RESULT: one unique getter match exists.")
        print("Candidate ID to reconcile after checking DB uniqueness:", matches[0])
        print("This script did not write the mapping to the database.")
    elif len(matches) > 1:
        print("RECOVERY RESULT: ambiguous duplicate on-chain candidates; do not map automatically.")
    else:
        print("RECOVERY RESULT: no exact getter match. Do not retry addCandidate.")
        print("Use receipt logs and deployed contract ABI/storage layout to investigate.")


if __name__ == "__main__":
    main()
