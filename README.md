GZU Blockchain-Based Mobile Voting System



Overview



This project is a blockchain-based mobile voting system developed as a Computer Science dissertation project for Great Zimbabwe University (GZU).



It combines an Android application, a Python backend, and Ethereum-compatible smart contracts to support election management, student voting, and election result handling.



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



