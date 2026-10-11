package zw.ac.gzu.voting.api

data class Candidate(
    val id: Int,
    val election_id: Int,
    val name: String,
    val position: String,
    val photo_url: String? = null,
    val faculty: String? = null,
    val department: String? = null,
    val programme: String? = null,
    val year_of_study: String? = null,
    val manifesto: String? = null,
    val experience: String? = null
)
