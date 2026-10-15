package zw.ac.gzu.voting.api

data class VoterStatus(
    val student_id: String,
    val election_id: Int,
    val has_voted: Boolean,
    val voted_positions: List<String> = emptyList()
)
