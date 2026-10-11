const hre = require("hardhat");
const fs = require("fs");
const path = require("path");


async function main() {

    console.log("");
    console.log("========================================");
    console.log(" GZU VOTING BLOCKCHAIN DEPLOYMENT");
    console.log("========================================");


    // ========================================================
    // COMPILE
    // ========================================================

    console.log("");
    console.log("Compiling contracts...");

    await hre.run("compile");


    // ========================================================
    // DEPLOYER
    // ========================================================

    const [deployer] =
        await hre.ethers.getSigners();


    console.log("");
    console.log("Deployer address:");
    console.log(deployer.address);


    const balance =
        await hre.ethers.provider.getBalance(
            deployer.address
        );


    console.log("");
    console.log("Deployer balance:");
    console.log(
        hre.ethers.formatEther(balance),
        "ETH"
    );


    // ========================================================
    // NETWORK
    // ========================================================

    console.log("");
    console.log("Network chain ID:");

    console.log(
        (await hre.ethers.provider.getNetwork())
            .chainId
            .toString()
    );


    // ========================================================
    // DEPLOY CONTRACT
    // ========================================================

    console.log("");
    console.log("Deploying Voting contract...");


    const Voting =
        await hre.ethers.getContractFactory(
            "Voting"
        );


    const voting =
        await Voting.deploy();


    await voting.waitForDeployment();


    const contractAddress =
        await voting.getAddress();


    console.log("");
    console.log(
        "Voting contract deployed to:"
    );

    console.log(
        contractAddress
    );


    // ========================================================
    // VERIFY CONTRACT CODE
    // ========================================================

    const code =
        await hre.ethers.provider.getCode(
            contractAddress
        );


    if (code === "0x") {

        throw new Error(
            "Deployment failed. "
            + "No contract bytecode found."
        );
    }


    console.log("");
    console.log(
        "Contract bytecode verified."
    );


    // ========================================================
    // TEST CONTRACT
    // ========================================================

    const electionCount =
        await voting.electionCount();


    console.log("");
    console.log(
        "Initial election count:"
    );

    console.log(
        electionCount.toString()
    );


    // ========================================================
    // SAVE CONTRACT ADDRESS
    // ========================================================

    const addressFile =
        path.join(
            __dirname,
            "..",
            "contract-address.json"
        );


    const addressData = {

        address: contractAddress,

        network: "localhost",

        chainId:
            (
                await hre.ethers.provider
                    .getNetwork()
            )
            .chainId
            .toString()

    };


    fs.writeFileSync(

        addressFile,

        JSON.stringify(
            addressData,
            null,
            2
        )

    );


    console.log("");
    console.log(
        "Contract address saved to:"
    );

    console.log(
        addressFile
    );


    console.log("");
    console.log("========================================");
    console.log(" DEPLOYMENT SUCCESSFUL");
    console.log("========================================");
    console.log("");

}


main().catch(

    (error) => {

        console.error("");
        console.error(
            "DEPLOYMENT FAILED:"
        );

        console.error(
            error
        );

        process.exitCode = 1;

    }

);