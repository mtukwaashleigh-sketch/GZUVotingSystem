
const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("Voting Contract", function () {
    let voting;
    let owner;
    let voter1;
    let voter2;

    const electionTitle = "GZU Student Council Election";

    beforeEach(async function () {
        [owner, voter1, voter2] = await ethers.getSigners();

        const Voting = await ethers.getContractFactory("Voting");
        voting = await Voting.deploy();

        await voting.waitForDeployment();
    });

    async function createAndPrepareElection() {
        await voting.createElection(electionTitle);

        const electionId = 1;

        await voting.addCandidate(
            electionId,
            "Candidate A",
            "President"
        );

        await voting.addCandidate(
            electionId,
            "Candidate B",
            "President"
        );

        return electionId;
    }

    describe("Election creation", function () {
        it("should create an election and record its history", async function () {
            await expect(
                voting.createElection(electionTitle)
            )
                .to.emit(voting, "ElectionCreated")
                .withArgs(1, electionTitle);

            const election = await voting.elections(1);

            expect(election[0]).to.equal(electionTitle);
            expect(election[1]).to.equal(false);
            expect(await voting.electionCount()).to.equal(1);
        });

        it("should reject an empty election title", async function () {
            await expect(
                voting.createElection("")
            ).to.be.revertedWith(
                "Election title is required"
            );
        });
    });

    describe("Candidate registration", function () {
        it("should register candidates before voting starts", async function () {
            const electionId = await createAndPrepareElection();

            expect(
                await voting.candidateCount(electionId)
            ).to.equal(2);

            const candidate = await voting.candidates(
                electionId,
                1
            );

            expect(candidate[0]).to.equal("Candidate A");
            expect(candidate[1]).to.equal("President");
            expect(candidate[2]).to.equal(0);
        });

        it("should reject candidate changes after voting starts", async function () {
            const electionId = await createAndPrepareElection();

            await voting.startElection(electionId);

            await expect(
                voting.addCandidate(
                    electionId,
                    "Candidate C",
                    "President"
                )
            ).to.be.revertedWith(
                "Candidates cannot be changed after voting starts"
            );
        });
    });

    describe("Voting and live results", function () {
        it("should start an election and accept votes", async function () {
            const electionId = await createAndPrepareElection();

            await expect(
                voting.startElection(electionId)
            )
                .to.emit(voting, "ElectionStarted")
                .withArgs(electionId);

            const voterHash1 = ethers.keccak256(
                ethers.toUtf8Bytes("test-voter-1")
            );

            const voterHash2 = ethers.keccak256(
                ethers.toUtf8Bytes("test-voter-2")
            );

            await voting.connect(voter1).castVote(
                electionId,
                1,
                voterHash1
            );

            // Vote counts can be read while the election is active.
            expect(
                await voting.getVoteCount(electionId, 1)
            ).to.equal(1);

            await voting.connect(voter2).castVote(
                electionId,
                2,
                voterHash2
            );

            expect(
                await voting.getVoteCount(electionId, 2)
            ).to.equal(1);
        });

        it("should reject a second vote for the same position and voter", async function () {
            const electionId = await createAndPrepareElection();

            await voting.startElection(electionId);

            const voterHash = ethers.keccak256(
                ethers.toUtf8Bytes("test-voter-1")
            );

            await voting.connect(voter1).castVote(
                electionId,
                1,
                voterHash
            );

            await expect(
                voting.connect(voter1).castVote(
                    electionId,
                    2,
                    voterHash
                )
            ).to.be.revertedWith(
                "Voter has already voted for this position"
            );
        });

        it("should reject votes before the election starts", async function () {
            const electionId = await createAndPrepareElection();

            const voterHash = ethers.keccak256(
                ethers.toUtf8Bytes("test-voter-1")
            );

            await expect(
                voting.connect(voter1).castVote(
                    electionId,
                    1,
                    voterHash
                )
            ).to.be.revertedWith(
                "Election is not accepting votes"
            );
        });
    });

    describe("Election closure", function () {
        it("should close an election and preserve final results", async function () {
            const electionId = await createAndPrepareElection();

            await voting.startElection(electionId);

            const voterHash = ethers.keccak256(
                ethers.toUtf8Bytes("test-voter-1")
            );

            await voting.connect(voter1).castVote(
                electionId,
                1,
                voterHash
            );

            await expect(
                voting.endElection(electionId)
            )
                .to.emit(voting, "ElectionClosed")
                .withArgs(electionId);

            expect(
                await voting.electionClosed(electionId)
            ).to.equal(true);

            expect(
                await voting.getVoteCount(electionId, 1)
            ).to.equal(1);

            await expect(
                voting.connect(voter2).castVote(
                    electionId,
                    2,
                    ethers.keccak256(
                        ethers.toUtf8Bytes("test-voter-2")
                    )
                )
            ).to.be.revertedWith(
                "Election is not accepting votes"
            );
        });
    });

    describe("Election cancellation", function () {
        it("should cancel an election and retain its history", async function () {
            const electionId = await createAndPrepareElection();

            await voting.startElection(electionId);

            await expect(
                voting.cancelElection(electionId)
            )
                .to.emit(voting, "ElectionCancelled")
                .withArgs(electionId);

            expect(
                await voting.electionCancelled(electionId)
            ).to.equal(true);

            const election = await voting.elections(electionId);

            expect(election[0]).to.equal(electionTitle);
            expect(election[1]).to.equal(false);
        });

        it("should prevent voting after cancellation", async function () {
            const electionId = await createAndPrepareElection();

            await voting.startElection(electionId);
            await voting.cancelElection(electionId);

            const voterHash = ethers.keccak256(
                ethers.toUtf8Bytes("test-voter-1")
            );

            await expect(
                voting.connect(voter1).castVote(
                    electionId,
                    1,
                    voterHash
                )
            ).to.be.revertedWith(
                "Election is not accepting votes"
            );
        });

        it("should prevent restarting a cancelled election", async function () {
            const electionId = await createAndPrepareElection();

            await voting.startElection(electionId);
            await voting.cancelElection(electionId);

            await expect(
                voting.startElection(electionId)
            ).to.be.revertedWith(
                "Election has already started"
            );
        });

        it("should prevent cancelling a closed election", async function () {
            const electionId = await createAndPrepareElection();

            await voting.startElection(electionId);
            await voting.endElection(electionId);

            await expect(
                voting.cancelElection(electionId)
            ).to.be.revertedWith(
                "Closed election cannot be cancelled"
            );
        });
    });

    describe("Election history", function () {
        it("should retain election records after closure", async function () {
            const electionId = await createAndPrepareElection();

            await voting.startElection(electionId);
            await voting.endElection(electionId);

            const election = await voting.elections(electionId);

            expect(election[0]).to.equal(electionTitle);
            expect(
                await voting.electionClosed(electionId)
            ).to.equal(true);

            expect(
                await voting.candidateCount(electionId)
            ).to.equal(2);
        });
    });
});
