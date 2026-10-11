package zw.ac.gzu.voting.api

data class Nomination(
    val id: Int,
    val student_id: String,
    val election_id: Int,
    val position: String,
    val full_name: String,
    val faculty: String,
    val department: String,
    val programme: String,
    val year_of_study: String,
    val manifesto: String,
    val experience: String? = null,
    val photo_url: String? = null,
    val status: String,
    val admin_feedback: String? = null,
    val candidate_id: Int? = null
)
