package zw.ac.gzu.voting.api

import retrofit2.Response
import retrofit2.http.GET
import retrofit2.http.Multipart
import retrofit2.http.Part
import okhttp3.MultipartBody
import okhttp3.RequestBody
import retrofit2.http.POST
import retrofit2.http.PUT
import retrofit2.http.Path
import retrofit2.http.Query

interface VotingApi {

    @POST("login")
    suspend fun login(
        @Query("email") email: String,
        @Query("password") password: String
    ): Response<LoginResponse>

    @Multipart
    @POST("nominations")
    suspend fun submitNomination(
        @Part("student_id") studentId: RequestBody,
        @Part("election_id") electionId: RequestBody,
        @Part("position") position: RequestBody,
        @Part("full_name") fullName: RequestBody,
        @Part("faculty") faculty: RequestBody,
        @Part("department") department: RequestBody,
        @Part("programme") programme: RequestBody,
        @Part("year_of_study") yearOfStudy: RequestBody,
        @Part("manifesto") manifesto: RequestBody,
        @Part("experience") experience: RequestBody,
        @Part photo: MultipartBody.Part
    ): Response<Nomination>

    @GET("students/{student_id}/nominations")
    suspend fun getStudentNominations(
        @Path("student_id") studentId: String
    ): Response<List<Nomination>>

    @GET("elections")
    suspend fun getElections(): Response<List<Election>>

    @GET("elections/{election_id}/candidates")
    suspend fun getCandidates(
        @Path("election_id") electionId: Int
    ): Response<List<Candidate>>

    @POST("vote")
    suspend fun castVote(
        @Query("student_id") studentId: String,
        @Query("election_id") electionId: Int,
        @Query("candidate_id") candidateId: Int
    ): Response<Unit>

    @GET("elections/{election_id}/results")
    suspend fun getElectionResults(
        @Path("election_id") electionId: Int
    ): Response<ElectionResultsResponse>

    @PUT("elections/{election_id}/status")
    suspend fun updateElectionStatus(
        @Path("election_id") electionId: Int,
        @Query("status") status: String
    ): Response<Unit>
}
