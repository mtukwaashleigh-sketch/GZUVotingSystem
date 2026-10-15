
package zw.ac.gzu.voting.api

data class LoginResponse(
    val message: String,
    val student_id: String,
    val email: String,
    val full_name: String? = null,
    val identity_type: String? = null,
    val identity_verified: Boolean = false
)