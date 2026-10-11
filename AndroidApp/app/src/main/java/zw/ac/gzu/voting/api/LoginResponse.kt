package zw.ac.gzu.voting.api

data class LoginResponse(
    val message: String,
    val student_id: String,
    val email: String
)
