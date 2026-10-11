package zw.ac.gzu.voting.api

data class Election(
    val id: Int,
    val title: String,
    val description: String?,
    val status: String
)