package zw.ac.gzu.voting.api


data class ElectionPositionsResponse(
    val election_id: Int,
    val positions: List<String> = emptyList()
)
