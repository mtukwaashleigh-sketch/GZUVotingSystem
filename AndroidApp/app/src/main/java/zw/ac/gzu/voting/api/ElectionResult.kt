package zw.ac.gzu.voting.api

data class ElectionResultsResponse(
    val election_id: Int,
    val election_title: String,
    val results: List<ElectionResult>
)

data class ElectionResult(
    val candidate_id: Int,
    val name: String,
    val position: String,
    val votes: Int
)

