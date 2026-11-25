GZU Election Management System

A mobile voting and election management application developed as a Computer Science dissertation project at Great Zimbabwe University.

The project explores how a university election process can be supported by an Android application, a Python backend and blockchain-based vote recording. It brings the main parts of the system together in one project: the mobile interface, application API, database operations and smart contracts.

This is an academic prototype for development, testing and demonstration. It has not been approved for use in official university elections.

Project overview

The system is designed around the university election process. It includes functionality for managing elections and nominations, presenting candidates to eligible users, recording votes and displaying election results.

The application uses a conventional backend and database for application data, while the blockchain component provides an additional record of voting transactions. The two parts serve different purposes and work together.

Main components

Component| Purpose| Main technologies
Android application| Mobile interface for users to access election functions| Kotlin, Android, Jetpack Compose
Backend| API and application logic connecting the mobile app, database and blockchain| Python, FastAPI, SQLAlchemy
Blockchain| Smart contracts for election and vote-related operations| Solidity, Hardhat, Web3.py

Repository structure

- "AndroidApp/" — Android application source code and Gradle project files.
- "Backend/" — Python API, database models, authentication and blockchain integration.
- "Blockchain/" — Solidity contracts and Hardhat project files.
- "docs/" — Project documentation and screenshots (to be added).

Technologies

- Kotlin and Jetpack Compose
- Python and FastAPI
- SQLAlchemy and PostgreSQL
- Solidity and Hardhat
- Web3.py
- Retrofit
- Git and GitHub

Blockchain in the project

The blockchain component is implemented through Solidity smart contracts. The backend communicates with the deployed contract using Web3.py.

The backend remains responsible for application operations and database access. Blockchain transactions provide a separate record for supported election and voting operations. This design allows the project to demonstrate how a mobile application can interact with a smart contract rather than treating the blockchain as a replacement for the entire application database.

Development and testing

The project contains separate Android, backend and blockchain components. Each component has its own dependencies and configuration.

Before running the project, configure the required environment variables and service connections for your local setup. Do not commit private keys, passwords, database credentials, API keys or real personal information to the repository.

The file "Backend/gzu_identity_roster.csv" contains fictional demonstration data. It is not an official Great Zimbabwe University student register.

Detailed setup instructions for each component will be documented separately as the project documentation is completed.

Project status

This repository represents an academic software project. Features and deployment configuration may change as development, testing and documentation continue.

The application should be tested in a controlled environment. It should not be used to conduct official elections or to make decisions based on real student voting data.

Author

Ashleigh Mutukwa
Computer Science student, Great Zimbabwe University

"GitHub profile" (https://github.com/mtukwaashleigh-sketch)