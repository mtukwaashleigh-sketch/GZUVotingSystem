package zw.ac.gzu.voting.api

import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

object RetrofitClient {

    private const val BASE_URL = "https://gzuvotingsystem.onrender.com/"

    /**
     * Converts backend-relative photo paths (for example /uploads/photo.jpg)
     * into absolute URLs that Coil can load.
     */
    fun baseUrlFor(path: String?): String? {
        if (path.isNullOrBlank()) return null
        if (path.startsWith("http://") || path.startsWith("https://")) return path
        return BASE_URL.trimEnd('/') + "/" + path.trimStart('/')
    }

    val api: VotingApi by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .addConverterFactory(
                GsonConverterFactory.create()
            )
            .build()
            .create(VotingApi::class.java)
    }
}
