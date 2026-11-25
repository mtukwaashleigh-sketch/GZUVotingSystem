Blockchain Component

This folder contains the blockchain component of the GZU Election Management System. It uses Solidity smart contracts and the Hardhat development environment to support blockchain-based election and voting operations.

Purpose

The blockchain component adds a separate, verifiable record of supported election and voting transactions. It works alongside the Python backend rather than replacing the application's database.

Technologies

- Solidity – used to write the voting smart contract.
- Hardhat – used for smart contract development, testing and deployment.
- Web3.py – used by the backend to communicate with the deployed contract.
- Ethereum – provides the blockchain network on which the contract can be deployed.

Project structure

- "contracts/" – contains the Solidity smart contracts.
- "scripts/" – contains scripts used for blockchain-related tasks.
- "test/" – contains smart contract tests.
- "ignition/" – contains Hardhat Ignition deployment configuration.
- "hardhat.config.js" – Hardhat configuration.
- "contract-address.json" – stores the deployed contract's network and address information.

How it connects to the application

The Android application communicates with the Python backend through its API. The backend handles the application's database operations and uses Web3.py to interact with the deployed smart contract.

This arrangement separates the mobile interface, application logic and blockchain operations.

Development

Install the Node.js dependencies from this directory:

npm install

Compile the smart contracts:

npx hardhat compile

Run the available smart contract tests:

npx hardhat test

Additional network and deployment configuration may be required depending on the environment being used.

Security

Never commit private keys, seed phrases, passwords or RPC credentials to GitHub. Use environment variables for sensitive configuration.

Project context

This blockchain component was developed as part of an academic Computer Science dissertation project at Great Zimbabwe University. It is intended for development, testing and demonstration, not as a production election platform.