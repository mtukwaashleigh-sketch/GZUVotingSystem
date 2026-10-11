// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title GZU Student Voting
/// @notice Election lifecycle is recorded on-chain. Elections and votes are never deleted.
contract Voting {
    struct Election {
        string title;
        bool active; // true only while accepting votes
    }

    struct Candidate {
        string name;
        string position;
        uint256 voteCount;
    }

    uint256 public electionCount;
    mapping(uint256 => Election) public elections;
    mapping(uint256 => uint256) public candidateCount;
    mapping(uint256 => mapping(uint256 => Candidate)) public candidates;
    mapping(uint256 => mapping(uint256 => bytes32)) public candidatePositionHash;
    mapping(uint256 => mapping(bytes32 => mapping(bytes32 => bool))) public hasVoted;

    mapping(uint256 => bool) public electionStarted;
    mapping(uint256 => bool) public electionClosed;
    mapping(uint256 => bool) public electionCancelled;

    event ElectionCreated(uint256 indexed electionId, string title);
    event ElectionStarted(uint256 indexed electionId);
    event ElectionClosed(uint256 indexed electionId);
    event ElectionCancelled(uint256 indexed electionId);
    event CandidateAdded(uint256 indexed electionId, uint256 indexed candidateId, string name, string position);
    event VoteCast(uint256 indexed electionId, uint256 indexed candidateId, bytes32 positionHash);

    modifier validElection(uint256 electionId) {
        require(electionId > 0 && electionId <= electionCount, "Invalid election");
        _;
    }

    function createElection(string memory title) public {
        require(bytes(title).length > 0, "Election title is required");
        electionCount++;
        elections[electionCount] = Election({title: title, active: false});
        emit ElectionCreated(electionCount, title);
    }

    function startElection(uint256 electionId) public validElection(electionId) {
        require(!electionStarted[electionId], "Election has already started");
        require(!electionClosed[electionId], "Election is closed");
        require(!electionCancelled[electionId], "Election is cancelled");
        electionStarted[electionId] = true;
        elections[electionId].active = true;
        emit ElectionStarted(electionId);
    }

    function addCandidate(uint256 electionId, string memory name, string memory position)
        public validElection(electionId)
    {
        require(!electionStarted[electionId], "Candidates cannot be changed after voting starts");
        require(!electionClosed[electionId] && !electionCancelled[electionId], "Election is terminal");
        require(bytes(name).length > 0 && bytes(position).length > 0, "Candidate details are required");
        candidateCount[electionId]++;
        uint256 candidateId = candidateCount[electionId];
        candidates[electionId][candidateId] = Candidate({name: name, position: position, voteCount: 0});
        candidatePositionHash[electionId][candidateId] = keccak256(bytes(position));
        emit CandidateAdded(electionId, candidateId, name, position);
    }

    function castVote(uint256 electionId, uint256 candidateId, bytes32 voterHash)
        public validElection(electionId)
    {
        require(elections[electionId].active, "Election is not accepting votes");
        require(!electionClosed[electionId] && !electionCancelled[electionId], "Election is terminal");
        require(candidateId > 0 && candidateId <= candidateCount[electionId], "Invalid candidate");
        bytes32 positionHash = candidatePositionHash[electionId][candidateId];
        require(!hasVoted[electionId][positionHash][voterHash], "Voter has already voted for this position");
        hasVoted[electionId][positionHash][voterHash] = true;
        candidates[electionId][candidateId].voteCount++;
        emit VoteCast(electionId, candidateId, positionHash);
    }

    function endElection(uint256 electionId) public validElection(electionId) {
        require(!electionClosed[electionId], "Election already closed");
        require(!electionCancelled[electionId], "Election already cancelled");
        elections[electionId].active = false;
        electionClosed[electionId] = true;
        emit ElectionClosed(electionId);
    }

    function cancelElection(uint256 electionId) public validElection(electionId) {
        require(!electionClosed[electionId], "Closed election cannot be cancelled");
        require(!electionCancelled[electionId], "Election already cancelled");
        elections[electionId].active = false;
        electionCancelled[electionId] = true;
        emit ElectionCancelled(electionId);
    }

    function getVoteCount(uint256 electionId, uint256 candidateId) public view returns (uint256) {
        return candidates[electionId][candidateId].voteCount;
    }
}
