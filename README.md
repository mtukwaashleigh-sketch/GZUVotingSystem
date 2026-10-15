GZU Election Management System



Overview



This project is a blockchain-based mobile voting system developed as a Computer Science dissertation project for Great Zimbabwe University (GZU).



It combines an Android application, a Python backend, and Ethereum-compatible smart contracts to support election management, student and employee voting, nominations, and election result handling.



This is an academic prototype intended for development, testing, and demonstration. It is not approved or intended for real university elections.



Project Structure



\- `AndroidApp/` — Android application built with Kotlin and Jetpack Compose.

\- `Backend/` — Python backend and API endpoints for application functionality.

\- `Blockchain/` — Solidity smart contracts, Hardhat configuration, deployment scripts, and contract tests.



Technologies



\- Kotlin and Android Jetpack Compose

\- Python

\- Solidity

\- Hardhat

\- Ethereum-compatible local development blockchain

\- Retrofit for Android API communication



Development Notes



The blockchain configuration currently references a local development network with chain ID `31337`. The contract address in `Blockchain/contract-address.json` is specific to that local test setup and may not be valid after the local blockchain is restarted or redeployed.



The Android application must be configured to communicate with a backend reachable from the device running the app. The backend and blockchain development node should only be used in a controlled development environment.

Security and Privacy



Do not commit `.env` files, passwords, private keys, real voter information, database files, or other confidential records.



The root `.gitignore` excludes common local configuration files, generated build files, and database files.



Academic Use



This project is intended for learning, research, software testing, and academic demonstration. Further security assessment, privacy review, usability testing, and deployment work would be required before any real election use.





## GZU Election Management System updates

### Institutional identity verification

Voter creation now requires a matching entry in the authoritative GZU Registry/HR identity roster. The roster is the trust source; an admin cannot create an account for an arbitrary registration/EC number or supply a different name for an existing ID. Student registration numbers and employee EC numbers share the same identifier field, with an explicit identity type.

Prepare a UTF-8 CSV obtained from the official Registry/HR system with these headers:

`identifier,full_name,identity_type,institutional_email`

`identity_type` must be `student` or `employee`. From the `Backend` directory, run:

`python import_identity_roster.py path/to/gzu_identity_roster.csv`

Do not build this roster from data entered by election admins. Protect the CSV and restrict access to it. Existing voter accounts should be reconciled against the official roster before deployment.

### Voting and candidate profiles

The Android voting screen now groups candidates by position, lets the voter choose one candidate per position, displays nomination profile details, and performs a server-side voter-status preflight before candidate selection. Candidate portraits have been enlarged. The nomination form uses the label **Manifesto** and no longer asks the nominator to type their name; the API resolves the name from the verified institutional ID.

### Blockchain and personal information

The database is the authoritative mapping for institutional identifiers and names. Do not write names, registration numbers, EC numbers, or email addresses directly to a public blockchain: blockchain data is difficult or impossible to erase and can expose personal information. Keep the chain limited to election/vote audit data or use a carefully designed non-reversible commitment if an independently reviewed contract upgrade is required.

Before production, configure and test the deployment's database migrations, roster import, email/identity proofing process, and blockchain failure/recovery procedures. The current roster gate verifies membership in the official roster and exact name/type match; it does not itself prove that the person holding a password is the rightful owner. For stronger proofing, integrate GZU single sign-on/MFA or a verified institutional email/phone challenge tied to contact details held by Registry/HR.
