package zw.ac.gzu.voting.api

import okhttp3.OkHttpClient
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object RetrofitClient {

    private const val BASE_URL = "https://gzuvotingsystem.onrender.com/"

    /**
     * Allows enough time for the Render backend to wake after inactivity.
     * These are request limits, not an app inactivity/session timeout.
     */
    private val httpClient: OkHttpClient by lazy {
        OkHttpClient.Builder()
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(90, TimeUnit.SECONDS)
            .writeTimeout(90, TimeUnit.SECONDS)
            .callTimeout(120, TimeUnit.SECONDS)
            .retryOnConnectionFailure(true)
            .build()
    }

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
            .client(httpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(VotingApi::class.java)
    }
}
