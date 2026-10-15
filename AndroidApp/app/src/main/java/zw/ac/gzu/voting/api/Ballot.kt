package zw.ac.gzu.voting.api

data class BallotSelection(
    val position: String,
    val candidate_id: Int
)

data class BallotSubmission(
    val student_id: String,
    val election_id: Int,
    val selections: List<BallotSelection>
)

data class BallotResponse(
    val message: String,
    val election_id: Int,
    val selections: List<BallotResult> = emptyList()
)

data class BallotResult(
    val position: String,
    val candidate_id: Int,
    val candidate_name: String,
    val blockchain_transaction: String
)
