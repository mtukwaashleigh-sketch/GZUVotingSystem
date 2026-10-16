package zw.ac.gzu.voting

import com.google.gson.JsonObject
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import android.content.Context
import android.content.ClipboardManager
import android.content.ClipData
import android.net.Uri
import android.os.Bundle
import android.view.WindowManager
import android.util.Base64
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import java.nio.charset.StandardCharsets
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.navigationBars
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBars
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Checkbox
import androidx.compose.material3.Switch
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TextFieldDefaults
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.role
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.selected
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.platform.LocalSoftwareKeyboardController
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextAlign
import coil.compose.AsyncImage
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import zw.ac.gzu.voting.api.Candidate
import zw.ac.gzu.voting.api.ElectionResult
import zw.ac.gzu.voting.api.Nomination
import zw.ac.gzu.voting.api.RetrofitClient


// ============================================================
// GZU BRAND COLOURS
// ============================================================

private val GzuGreen = Color(0xFF006B3F)
private val GzuDarkGreen = Color(0xFF004D2C)
private val GzuLightGreen = Color(0xFFEAF6EF)
private val GzuSelectedLight = Color(0xFFD7F0E1)
private val GzuSelectedDark = Color(0xFF254B38)
private val GzuVeryLightGreen = Color(0xFFF5FBF7)

private val GzuDarkBackground = Color(0xFF101614)
private val GzuDarkSurface = Color(0xFF18211D)
private val GzuDarkSurface2 = Color(0xFF202B26)
private val GzuDarkText = Color(0xFFF1F5F2)
private val GzuDarkSecondaryText = Color(0xFFB9C5BE)

private val DangerRed = Color(0xFFB42318)
private val DangerBackground = Color(0xFFFDECEC)

private val DarkDangerBackground = Color(0xFF351A18)
private val WarningText = Color(0xFF9A6700)
private val WarningBackground = Color(0xFFFFF7DF)

private val DarkWarningBackground = Color(0xFF352B12)


// ============================================================
// THEME MODES
// ============================================================

enum class ThemeMode {
    SYSTEM,
    LIGHT,
    DARK
}


// ============================================================
// MATERIAL LIGHT THEME
// ============================================================

private val GzuLightColorScheme =
    lightColorScheme(
        primary = GzuGreen,
        onPrimary = Color.White,

        secondary = GzuDarkGreen,
        onSecondary = Color.White,

        background = Color(0xFFF5F7F6),
        onBackground = Color(0xFF102018),

        surface = Color(0xFFFFFFFF),
        onSurface = Color(0xFF102018),

        surfaceVariant = Color(0xFFE4F1E9),
        onSurfaceVariant = Color(0xFF46594D),
        outline = Color(0xFF77877D),
        outlineVariant = Color(0xFFB8C8BE),

        error = DangerRed,
        onError = Color.White
    )


// ============================================================
// MATERIAL DARK THEME
// ============================================================

private val GzuDarkColorScheme =
    darkColorScheme(
        primary = Color(0xFF69D99A),
        onPrimary = Color(0xFF082A19),

        secondary = Color(0xFF9AE6B8),
        onSecondary = Color(0xFF082A19),

        background = GzuDarkBackground,
        onBackground = GzuDarkText,

        surface = GzuDarkSurface,
        onSurface = GzuDarkText,

        surfaceVariant = GzuDarkSurface2,
        onSurfaceVariant = Color(0xFFD0DAD4),
        outline = Color(0xFF82958A),
        outlineVariant = Color(0xFF43564B),

        error = Color(0xFFFF8A80),
        onError = Color(0xFF3B0805)
    )


// High-contrast scheme: deliberately uses black/white and a strong blue accent.
private val GzuHighContrastLight = lightColorScheme(
    primary = Color(0xFF0033CC), onPrimary = Color.White,
    secondary = Color.Black, onSecondary = Color.White,
    background = Color.White, onBackground = Color.Black,
    surface = Color.White, onSurface = Color.Black,
    surfaceVariant = Color(0xFFF0F0F0), onSurfaceVariant = Color.Black,
    outline = Color.Black, outlineVariant = Color(0xFF333333),
    error = Color(0xFFB00020), onError = Color.White
)

private val GzuHighContrastDark = darkColorScheme(
    primary = Color(0xFFFFFF00), onPrimary = Color.Black,
    secondary = Color.White, onSecondary = Color.Black,
    background = Color.Black, onBackground = Color.White,
    surface = Color(0xFF000000), onSurface = Color.White,
    surfaceVariant = Color(0xFF202020), onSurfaceVariant = Color.White,
    outline = Color.White, outlineVariant = Color(0xFFCCCCCC),
    error = Color(0xFFFF8080), onError = Color.Black
)


// ============================================================
// THEME PREFERENCE
// ============================================================

private const val THEME_PREFS = "gzu_voting_preferences"
private const val THEME_KEY = "theme_mode"
private const val LARGE_TEXT_KEY = "accessibility_large_text"
private const val HIGH_CONTRAST_KEY = "accessibility_high_contrast"
private const val PRIVACY_MODE_KEY = "accessibility_privacy_mode"

private fun loadAccessibilityPreference(context: Context, key: String, default: Boolean = false): Boolean =
    context.getSharedPreferences(THEME_PREFS, Context.MODE_PRIVATE).getBoolean(key, default)

private fun saveAccessibilityPreference(context: Context, key: String, value: Boolean) {
    context.getSharedPreferences(THEME_PREFS, Context.MODE_PRIVATE).edit().putBoolean(key, value).apply()
}


private fun loadThemeMode(context: Context): ThemeMode {

    val preferences =
        context.getSharedPreferences(
            THEME_PREFS,
            Context.MODE_PRIVATE
        )

    return when (
        preferences.getString(
            THEME_KEY,
            ThemeMode.SYSTEM.name
        )
    ) {

        ThemeMode.LIGHT.name ->
            ThemeMode.LIGHT

        ThemeMode.DARK.name ->
            ThemeMode.DARK

        else ->
            ThemeMode.SYSTEM
    }
}


private fun saveThemeMode(
    context: Context,
    mode: ThemeMode
) {

    context
        .getSharedPreferences(
            THEME_PREFS,
            Context.MODE_PRIVATE
        )
        .edit()
        .putString(
            THEME_KEY,
            mode.name
        )
        .apply()
}


// ============================================================
// ACTIVITY
// ============================================================

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {

        super.onCreate(savedInstanceState)

        // Resize every screen when the software keyboard opens. The root imePadding
        // below keeps forms and text fields visible above the keyboard throughout the app.
        window.setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE)

        setContent {
            Box(modifier = Modifier.fillMaxSize().imePadding()) {
                VotingApp()
            }
        }
    }
}


// ============================================================
// MAIN APPLICATION
// ============================================================

@Composable
fun VotingApp() {

    val context = LocalContext.current

    val systemDark =
        isSystemInDarkTheme()

    var themeMode by remember {
        mutableStateOf(
            loadThemeMode(context)
        )
    }

    val darkTheme = when (themeMode) {
        ThemeMode.SYSTEM -> systemDark
        ThemeMode.LIGHT -> false
        ThemeMode.DARK -> true
    }
    var largeText by remember { mutableStateOf(loadAccessibilityPreference(context, LARGE_TEXT_KEY)) }
    var highContrast by remember { mutableStateOf(loadAccessibilityPreference(context, HIGH_CONTRAST_KEY)) }
    var privacyMode by remember { mutableStateOf(loadAccessibilityPreference(context, PRIVACY_MODE_KEY, true)) }
    val baseDensity = LocalDensity.current

    CompositionLocalProvider(
        LocalDensity provides androidx.compose.ui.unit.Density(
            baseDensity.density,
            baseDensity.fontScale * if (largeText) 1.25f else 1f
        )
    ) {
        MaterialTheme(
            colorScheme = when {
                highContrast && darkTheme -> GzuHighContrastDark
                highContrast -> GzuHighContrastLight
                darkTheme -> GzuDarkColorScheme
                else -> GzuLightColorScheme
            }
        ) {

            var currentScreen by remember {
                mutableStateOf("welcome")
            }

            var studentId by remember {
                mutableStateOf("")
            }

            var institutionalFullName by remember {
                mutableStateOf("")
            }

            var selectedElectionId by remember {
                mutableStateOf(0)
            }

            if (currentScreen == "welcome") {

                WelcomeScreen(
                    onGetStarted = {
                        currentScreen = "login"
                    },

                    onExit = {
                        (context as? ComponentActivity)?.finish()
                    }
                )

            } else if (currentScreen == "login") {

                LoginScreen(
                    onBack = {
                        currentScreen = "welcome"
                    },

                    onLoginSuccess = { registrationNumber, verifiedFullName ->

                        studentId = registrationNumber
                        institutionalFullName = verifiedFullName.trim()

                        currentScreen =
                            "dashboard"
                    }
                )

            } else if (currentScreen == "dashboard") {

                StudentDashboardScreen(

                    studentId =
                        studentId,

                    themeMode =
                        themeMode,

                    onThemeChange = { newMode ->
                        themeMode = newMode
                        saveThemeMode(context, newMode)
                    },
                    largeText = largeText,
                    highContrast = highContrast,
                    privacyMode = privacyMode,
                    onLargeTextChange = { enabled ->
                        largeText = enabled
                        saveAccessibilityPreference(context, LARGE_TEXT_KEY, enabled)
                    },
                    onHighContrastChange = { enabled ->
                        highContrast = enabled
                        saveAccessibilityPreference(context, HIGH_CONTRAST_KEY, enabled)
                    },
                    onPrivacyModeChange = { enabled ->
                        privacyMode = enabled
                        saveAccessibilityPreference(context, PRIVACY_MODE_KEY, enabled)
                    },

                    onVote = { electionId ->

                        selectedElectionId =
                            electionId

                        currentScreen =
                            "voting"
                    },

                    onResults = { electionId ->

                        selectedElectionId =
                            electionId

                        currentScreen =
                            "results"
                    },

                    onNominate = { currentScreen = "nomination" },
                    onMyNominations = { currentScreen = "my_nominations" },
                    onAssistant = { currentScreen = "assistant" },

                    onLogout = {

                        studentId = ""
                        institutionalFullName = ""

                        selectedElectionId = 0

                        currentScreen =
                            "welcome"
                    }
                )

            } else if (currentScreen == "assistant") {
                ElectionAssistantScreen(
                    onBack = { currentScreen = "dashboard" }
                )
            } else if (currentScreen == "nomination") {
                NominationScreen(
                    studentId = studentId,
                    fullName = institutionalFullName,
                    onBack = { currentScreen = "dashboard" }
                )
            } else if (currentScreen == "my_nominations") {
                MyNominationsScreen(
                    studentId = studentId,
                    onBack = { currentScreen = "dashboard" }
                )
            } else if (currentScreen == "voting") {

                VotingScreen(

                    studentId =
                        studentId,

                    electionId =
                        selectedElectionId,
                    privacyMode = privacyMode,

                    onBack = {
                        currentScreen =
                            "dashboard"
                    },

                    onViewResults = {
                        currentScreen =
                            "results"
                    }
                )

            } else if (currentScreen == "results") {

                LiveResultsScreen(

                    electionId =
                        selectedElectionId,

                    onBack = {
                        currentScreen =
                            "dashboard"
                    }
                )
            }
        }
    } // MaterialTheme
} // CompositionLocalProvider


// ============================================================
// AI ELECTION ASSISTANT
// ============================================================

@Composable
fun ElectionAssistantScreen(onBack: () -> Unit) {
    data class ChatMessage(val text: String, val fromUser: Boolean)
    var messages by remember {
        mutableStateOf(listOf(ChatMessage(
            "Welcome to the GZU AI Election Assistant. Ask a question about voting procedures, election information, nominations, vote receipts, or blockchain verification.",
            false
        )))
    }
    var input by remember { mutableStateOf("") }
    var sending by remember { mutableStateOf(false) }
    var status by remember { mutableStateOf("") }
    val scope = rememberCoroutineScope()
    val keyboardController = LocalSoftwareKeyboardController.current
    val chatListState = androidx.compose.foundation.lazy.rememberLazyListState()

    fun sendQuestion(question: String) {
        val cleaned = question.trim()
        if (cleaned.isEmpty() || sending) return
        messages = messages + ChatMessage(cleaned, true)
        input = ""
        keyboardController?.hide()
        sending = true
        status = "Preparing a response…"
        scope.launch {
            try {
                val payload = JsonObject().apply { addProperty("message", cleaned) }
                val response = RetrofitClient.api.askElectionAssistant(payload)
                if (response.isSuccessful) {
                    val body = response.body()
                    val answer = body?.get("answer")?.asString
                        ?: "The assistant could not prepare a response. Please try again."
                    messages = messages + ChatMessage(answer, false)
                    status = if (body?.get("mode")?.asString == "faq_fallback") {
                        "The assistant is using its built-in guidance because the AI service is unavailable."
                    } else ""
                } else {
                    val detail = try { response.errorBody()?.string().orEmpty() } catch (_: Exception) { "" }
                    messages = messages + ChatMessage(
                        if (detail.isNotBlank()) "The assistant could not process your question. Please try again later." else "The assistant is temporarily unavailable. Please try again later.",
                        false
                    )
                    status = "Request failed (${response.code()})."
                }
            } catch (_: Exception) {
                messages = messages + ChatMessage(
                    "Unable to connect to the election assistant. Check your connection and try again.", false
                )
                status = "Connection unavailable."
            } finally {
                sending = false
            }
        }
    }

    Column(
        modifier = Modifier.fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .windowInsetsPadding(WindowInsets.statusBars)
            .windowInsetsPadding(WindowInsets.navigationBars)
            .padding(horizontal = 16.dp, vertical = 10.dp)
    ) {
        Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth()) {
            TextButton(onClick = onBack) { Text("Back") }
            Column(Modifier.weight(1f)) {
                Text("AI Election Assistant", fontSize = 21.sp, fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.onBackground)
                Text("GZU Voting System support", fontSize = 13.sp,
                    color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }
        Spacer(Modifier.height(8.dp))
        LazyColumn(
            state = chatListState,
            modifier = Modifier.weight(1f).fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(10.dp),
            contentPadding = androidx.compose.foundation.layout.PaddingValues(vertical = 8.dp)
        ) {
            items(messages) { message ->
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = if (message.fromUser) Arrangement.End else Arrangement.Start
                ) {
                    Surface(
                        modifier = Modifier.fillMaxWidth(0.88f),
                        shape = RoundedCornerShape(14.dp),
                        color = if (message.fromUser) MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.surfaceVariant
                    ) {
                        Text(
                            message.text,
                            modifier = Modifier.padding(13.dp),
                            color = if (message.fromUser) MaterialTheme.colorScheme.onPrimaryContainer else MaterialTheme.colorScheme.onSurfaceVariant,
                            fontSize = 14.sp
                        )
                    }
                }
            }
            if (sending) {
                item { Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    CircularProgressIndicator(modifier = Modifier.size(18.dp), strokeWidth = 2.dp)
                    Text("Preparing a response…", color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 13.sp)
                } }
            }
        }
        LaunchedEffect(messages.size, sending) {
            if (messages.isNotEmpty()) chatListState.animateScrollToItem(messages.size - 1)
        }
        if (status.isNotBlank()) {
            Text(status, modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
                color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 12.sp)
        }
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            OutlinedTextField(
                value = input,
                onValueChange = { if (it.length <= 1200) input = it },
                modifier = Modifier.weight(1f),
                enabled = !sending,
                placeholder = { Text("Ask an election question") },
                maxLines = 4,
                keyboardOptions = KeyboardOptions(imeAction = ImeAction.Send),
                keyboardActions = KeyboardActions(
                    onSend = { if (!sending && input.isNotBlank()) sendQuestion(input) }
                ),
                shape = RoundedCornerShape(12.dp)
            )
            Button(onClick = { sendQuestion(input) }, enabled = !sending && input.isNotBlank(),
                shape = RoundedCornerShape(12.dp)) { Text("Send") }
        }
        Text(
            "Do not enter passwords or private voter information. The assistant provides guidance and cannot cast votes or manage elections.",
            modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
            fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}


// ============================================================
// REUSABLE APP HEADER
// ============================================================

@Composable
fun AppHeader(
    title: String,
    subtitle: String? = null,
    onBack: (() -> Unit)? = null
) {

    Row(
        modifier =
            Modifier
                .fillMaxWidth()
                .padding(bottom = 18.dp),

        verticalAlignment =
            Alignment.CenterVertically
    ) {

        if (onBack != null) {

            TextButton(
                onClick =
                    onBack
            ) {

                Text(
                    text =
                        "‹",

                    fontSize =
                        36.sp,

                    color =
                        MaterialTheme
                            .colorScheme
                            .primary,

                    fontWeight =
                        FontWeight.Bold
                )
            }

            Spacer(
                modifier =
                    Modifier.width(4.dp)
            )
        }

        Column(
            modifier =
                Modifier.weight(1f)
        ) {

            Text(
                text =
                    title,

                fontSize =
                    25.sp,

                fontWeight =
                    FontWeight.Bold,

                color =
                    MaterialTheme
                        .colorScheme
                        .onBackground
            )

            if (subtitle != null) {

                Spacer(
                    modifier =
                        Modifier.height(4.dp)
                )

                Text(
                    text =
                        subtitle,

                    fontSize =
                        15.sp,

                    color =
                        MaterialTheme
                            .colorScheme
                            .onSurfaceVariant
                )
            }
        }
    }
}


// ============================================================
// WELCOME SCREEN
// ============================================================

@Composable
fun WelcomeScreen(
    onGetStarted: () -> Unit,
    onExit: () -> Unit
) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(
                Brush.verticalGradient(
                    colors = listOf(
                        Color(0xFF062D1D),
                        GzuDarkGreen,
                        Color(0xFF087447)
                    )
                )
            )
            .windowInsetsPadding(WindowInsets.statusBars)
            .windowInsetsPadding(WindowInsets.navigationBars)
            .padding(horizontal = 26.dp, vertical = 24.dp)
    ) {
        Column(
            modifier = Modifier.fillMaxSize(),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Surface(
                modifier = Modifier.size(118.dp),
                shape = RoundedCornerShape(30.dp),
                color = Color.White,
                shadowElevation = 10.dp
            ) {
                Box(contentAlignment = Alignment.Center) {
                    Image(
                        painter = painterResource(id = R.drawable.gzu_logo),
                        contentDescription = "Great Zimbabwe University logo",
                        modifier = Modifier.padding(12.dp).fillMaxSize(),
                        contentScale = ContentScale.Fit
                    )
                }
            }

            Spacer(Modifier.height(10.dp))
            Text(
                text = "INSTITUTIONAL VOTING",
                color = Color(0xFFD4F3E1),
                fontSize = 15.sp,
                fontWeight = FontWeight.SemiBold,
                letterSpacing = 2.sp,
                textAlign = TextAlign.Center
            )
            Spacer(Modifier.height(16.dp))
            Text(
                text = "Your voice. Your choice. Your university.",
                color = Color.White.copy(alpha = 0.84f),
                fontSize = 15.sp,
                textAlign = TextAlign.Center,
                lineHeight = 23.sp
            )
            Spacer(Modifier.height(42.dp))
            Button(
                onClick = onGetStarted,
                modifier = Modifier.fillMaxWidth().height(56.dp),
                shape = RoundedCornerShape(16.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color.White,
                    contentColor = GzuDarkGreen
                )
            ) {
                Text("Get started", fontSize = 16.sp, fontWeight = FontWeight.Bold)
            }
            Spacer(Modifier.height(14.dp))
            TextButton(onClick = onExit) {
                Text("Exit app", color = Color.White.copy(alpha = 0.85f), fontSize = 14.sp)
            }
        }
        Text(
            text = "SECURE  •  TRANSPARENT  •  BLOCKCHAIN-SECURED",
            modifier = Modifier.align(Alignment.BottomCenter).padding(bottom = 8.dp),
            color = Color.White.copy(alpha = 0.68f),
            fontSize = 10.sp,
            letterSpacing = 0.7.sp,
            textAlign = TextAlign.Center
        )
    }
}


// ============================================================
// SECURE SAVED LOGIN CREDENTIALS
// Passwords are encrypted with an AES key stored in Android Keystore.
// The password is never written to ordinary SharedPreferences as plaintext.
// ============================================================

private data class SavedLoginCredentials(
    val email: String,
    val password: String
)

private object LoginCredentialVault {
    private const val PREFS_NAME = "gzu_secure_login"
    private const val EMAIL_KEY = "saved_email"
    private const val PASSWORD_KEY = "saved_password"
    private const val KEYSTORE_ALIAS = "gzu_voting_login_aes_key"
    private const val ANDROID_KEYSTORE = "AndroidKeyStore"
    private const val TRANSFORMATION = "AES/GCM/NoPadding"

    fun load(context: Context): SavedLoginCredentials? {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val encryptedEmail = prefs.getString(EMAIL_KEY, null) ?: return null
        val encryptedPassword = prefs.getString(PASSWORD_KEY, null) ?: return null

        return try {
            val email = decrypt(encryptedEmail)
            val password = decrypt(encryptedPassword)
            if (email.isBlank() || password.isBlank()) null
            else SavedLoginCredentials(email, password)
        } catch (_: Exception) {
            // If the encrypted values or Android Keystore key are no longer valid,
            // discard them and let the user sign in normally.
            clear(context)
            null
        }
    }

    fun save(context: Context, email: String, password: String) {
        val encryptedEmail = encrypt(email)
        val encryptedPassword = encrypt(password)
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .edit()
            .putString(EMAIL_KEY, encryptedEmail)
            .putString(PASSWORD_KEY, encryptedPassword)
            .apply()
    }

    fun clear(context: Context) {
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .edit()
            .clear()
            .apply()
    }

    private fun getOrCreateSecretKey(): SecretKey {
        val keyStore = KeyStore.getInstance(ANDROID_KEYSTORE).apply { load(null) }
        (keyStore.getKey(KEYSTORE_ALIAS, null) as? SecretKey)?.let { return it }

        val generator = KeyGenerator.getInstance(
            KeyProperties.KEY_ALGORITHM_AES,
            ANDROID_KEYSTORE
        )
        generator.init(
            KeyGenParameterSpec.Builder(
                KEYSTORE_ALIAS,
                KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
            )
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setRandomizedEncryptionRequired(true)
                .build()
        )
        return generator.generateKey()
    }

    private fun encrypt(value: String): String {
        val cipher = Cipher.getInstance(TRANSFORMATION)
        cipher.init(Cipher.ENCRYPT_MODE, getOrCreateSecretKey())
        val encryptedBytes = cipher.doFinal(value.toByteArray(StandardCharsets.UTF_8))
        val iv = Base64.encodeToString(cipher.iv, Base64.NO_WRAP)
        val ciphertext = Base64.encodeToString(encryptedBytes, Base64.NO_WRAP)
        return "$iv:$ciphertext"
    }

    private fun decrypt(value: String): String {
        val parts = value.split(":", limit = 2)
        require(parts.size == 2) { "Invalid saved credential format" }
        val iv = Base64.decode(parts[0], Base64.NO_WRAP)
        val ciphertext = Base64.decode(parts[1], Base64.NO_WRAP)
        val cipher = Cipher.getInstance(TRANSFORMATION)
        cipher.init(
            Cipher.DECRYPT_MODE,
            getOrCreateSecretKey(),
            GCMParameterSpec(128, iv)
        )
        return String(cipher.doFinal(ciphertext), StandardCharsets.UTF_8)
    }
}

// ============================================================
// LOGIN SCREEN
// ============================================================

@Composable
fun LoginScreen(
    onBack: () -> Unit,
    onLoginSuccess: (String, String) -> Unit
) {
    val context = LocalContext.current
    val savedCredentials = remember { LoginCredentialVault.load(context) }

    var studentEmail by remember {
        mutableStateOf(savedCredentials?.email.orEmpty())
    }

    var password by remember {
        mutableStateOf(savedCredentials?.password.orEmpty())
    }

    var rememberLogin by remember {
        mutableStateOf(savedCredentials != null)
    }

    var showPassword by remember {
        mutableStateOf(false)
    }

    var message by remember {
        mutableStateOf("")
    }

    var isLoading by remember {
        mutableStateOf(false)
    }

    val scope =
        rememberCoroutineScope()


    Box(
        modifier =
            Modifier
                .fillMaxSize()
                .background(
                    Brush.verticalGradient(
                        colors =
                            listOf(
                                GzuDarkGreen,
                                GzuGreen,
                                Color(0xFF0C8A57)
                            )
                    )
                )
                .windowInsetsPadding(
                    WindowInsets.statusBars
                )
                .padding(
                    horizontal = 18.dp,
                    vertical = 12.dp
                )
    ) {

        // ====================================================
        // DECORATIVE TOP CIRCLES
        // ====================================================

        Surface(
            modifier =
                Modifier
                    .size(190.dp)
                    .align(Alignment.TopEnd),

            shape =
                CircleShape,

            color =
                Color.White.copy(
                    alpha = 0.08f
                )
        ) {}


        Surface(
            modifier =
                Modifier
                    .size(120.dp)
                    .align(Alignment.TopStart)
                    .padding(15.dp),

            shape =
                CircleShape,

            color =
                Color.White.copy(
                    alpha = 0.06f
                )
        ) {}


        Column(
            modifier =
                Modifier
                    .fillMaxSize()
                    .windowInsetsPadding(
                        WindowInsets.navigationBars
                    )
        ) {

            // ====================================================
            // BACK BUTTON
            // ====================================================

            TextButton(
                onClick =
                    onBack,

                modifier =
                    Modifier
                        .height(48.dp)
            ) {

                Text(
                    text =
                        "‹  Back",

                    color =
                        Color.White,

                    fontSize =
                        16.sp,

                    fontWeight =
                        FontWeight.SemiBold
                )
            }


            Spacer(
                modifier =
                    Modifier.height(4.dp)
            )


            // ====================================================
            // LOGIN CARD
            // ====================================================

            Card(
                modifier =
                    Modifier
                        .fillMaxWidth()
                        .weight(1f),

                shape =
                    RoundedCornerShape(28.dp),

                colors =
                    CardDefaults.cardColors(
                        containerColor =
                            MaterialTheme
                                .colorScheme
                                .surface
                    ),

                elevation =
                    CardDefaults.cardElevation(
                        defaultElevation =
                            12.dp
                    )
            ) {

                LazyColumn(
                    modifier =
                        Modifier
                            .fillMaxSize()
                            .padding(25.dp),

                    horizontalAlignment =
                        Alignment.CenterHorizontally
                ) {

                    item {

                        Spacer(
                            modifier =
                                Modifier.height(8.dp)
                        )


                        // ====================================================
                        // LOGO
                        // ====================================================

                        Surface(
                            modifier =
                                Modifier.size(85.dp),

                            shape =
                                CircleShape,

                            color =
                                GzuLightGreen,

                            shadowElevation =
                                3.dp
                        ) {

                            Box(
                                contentAlignment =
                                    Alignment.Center
                            ) {

                                Image(
                                    painter =
                                        painterResource(
                                            id =
                                                R.drawable.gzu_logo
                                        ),

                                    contentDescription =
                                        "GZU Logo",

                                    modifier =
                                        Modifier.size(68.dp)
                                )
                            }
                        }


                        Spacer(
                            modifier =
                                Modifier.height(22.dp)
                        )


                        Text(
                            text =
                                "Welcome Back",

                            fontSize =
                                30.sp,

                            fontWeight =
                                FontWeight.Bold,

                            color =
                                MaterialTheme
                                    .colorScheme
                                    .onSurface,

                            textAlign =
                                TextAlign.Center
                        )


                        Spacer(
                            modifier =
                                Modifier.height(8.dp)
                        )


                        Text(
                            text =
                                "Sign in to participate in institutional elections.",

                            fontSize =
                                15.sp,

                            color =
                                MaterialTheme
                                    .colorScheme
                                    .onSurfaceVariant,

                            textAlign =
                                TextAlign.Center,

                            lineHeight =
                                21.sp
                        )


                        Spacer(
                            modifier =
                                Modifier.height(28.dp)
                        )


                        Text(
                            text =
                                "Institutional Email",

                            modifier =
                                Modifier.fillMaxWidth(),

                            fontSize =
                                15.sp,

                            fontWeight =
                                FontWeight.SemiBold,

                            color =
                                MaterialTheme
                                    .colorScheme
                                    .onSurface
                        )


                        Spacer(
                            modifier =
                                Modifier.height(8.dp)
                        )


                        OutlinedTextField(
                            value =
                                studentEmail,

                            onValueChange = {

                                studentEmail =
                                    it

                                message =
                                    ""
                            },

                            placeholder = {

                                Text(
                                    text =
                                        "Enter your institutional email",

                                    fontSize =
                                        14.sp
                                )
                            },

                            modifier =
                                Modifier.fillMaxWidth(),

                            singleLine =
                                true,

                            shape =
                                RoundedCornerShape(13.dp),

                            keyboardOptions =
                                KeyboardOptions(
                                    keyboardType =
                                        KeyboardType.Email
                                ),

                            colors =
                                TextFieldDefaults.colors(
                                    focusedIndicatorColor =
                                        GzuGreen,

                                    unfocusedIndicatorColor =
                                        MaterialTheme
                                            .colorScheme
                                            .outline,

                                    focusedContainerColor =
                                        MaterialTheme
                                            .colorScheme
                                            .surface,

                                    unfocusedContainerColor =
                                        MaterialTheme
                                            .colorScheme
                                            .surface
                                )
                        )


                        Spacer(
                            modifier =
                                Modifier.height(19.dp)
                        )


                        Text(
                            text =
                                "Password",

                            modifier =
                                Modifier.fillMaxWidth(),

                            fontSize =
                                15.sp,

                            fontWeight =
                                FontWeight.SemiBold,

                            color =
                                MaterialTheme
                                    .colorScheme
                                    .onSurface
                        )


                        Spacer(
                            modifier =
                                Modifier.height(8.dp)
                        )


                        OutlinedTextField(
                            value =
                                password,

                            onValueChange = {

                                password =
                                    it

                                message =
                                    ""
                            },

                            placeholder = {

                                Text(
                                    text =
                                        "Enter your password",

                                    fontSize =
                                        14.sp
                                )
                            },

                            modifier =
                                Modifier.fillMaxWidth(),

                            singleLine =
                                true,

                            shape =
                                RoundedCornerShape(13.dp),

                            visualTransformation =
                                if (showPassword) {
                                    VisualTransformation.None
                                } else {
                                    PasswordVisualTransformation()
                                },

                            trailingIcon = {

                                TextButton(
                                    onClick = {

                                        showPassword =
                                            !showPassword
                                    }
                                ) {

                                    Text(
                                        text =
                                            if (showPassword) {
                                                "Hide"
                                            } else {
                                                "Show"
                                            },

                                        color =
                                            MaterialTheme
                                                .colorScheme
                                                .primary,

                                        fontSize =
                                            13.sp,

                                        fontWeight =
                                            FontWeight.SemiBold
                                    )
                                }
                            },

                            keyboardOptions =
                                KeyboardOptions(
                                    keyboardType =
                                        KeyboardType.Password
                                ),

                            colors =
                                TextFieldDefaults.colors(
                                    focusedIndicatorColor =
                                        GzuGreen,

                                    unfocusedIndicatorColor =
                                        MaterialTheme
                                            .colorScheme
                                            .outline,

                                    focusedContainerColor =
                                        MaterialTheme
                                            .colorScheme
                                            .surface,

                                    unfocusedContainerColor =
                                        MaterialTheme
                                            .colorScheme
                                            .surface
                                )
                        )


                        Spacer(
                            modifier =
                                Modifier.height(22.dp)
                        )


                        if (message.isNotEmpty()) {

                            Surface(
                                modifier =
                                    Modifier.fillMaxWidth(),

                                shape =
                                    RoundedCornerShape(12.dp),

                                color =
                                    if (MaterialTheme.colorScheme.background == GzuDarkBackground) {
                                        DarkDangerBackground
                                    } else {
                                        DangerBackground
                                    }
                            ) {

                                Text(
                                    text =
                                        message,

                                    color =
                                        if (MaterialTheme.colorScheme.background == GzuDarkBackground) {
                                            Color(0xFFFF8A80)
                                        } else {
                                            DangerRed
                                        },

                                    fontSize =
                                        14.sp,

                                    fontWeight =
                                        FontWeight.Medium,

                                    modifier =
                                        Modifier.padding(13.dp)
                                )
                            }


                            Spacer(
                                modifier =
                                    Modifier.height(15.dp)
                            )
                        }


                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Checkbox(
                                checked = rememberLogin,
                                onCheckedChange = { checked ->
                                    rememberLogin = checked
                                    if (!checked) {
                                        LoginCredentialVault.clear(context)
                                    }
                                }
                            )
                            Column(modifier = Modifier.weight(1f)) {
                                Text(
                                    text = "Remember me",
                                    fontWeight = FontWeight.SemiBold,
                                    color = MaterialTheme.colorScheme.onSurface
                                )
                                Text(
                                    text = "Save this login securely on this device",
                                    fontSize = 12.sp,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            }
                        }

                        Spacer(Modifier.height(8.dp))

                        Button(
                            onClick = {

                                if (
                                    studentEmail.isBlank() ||
                                    password.isBlank()
                                ) {

                                    message =
                                        "Please enter your email and password."

                                } else {

                                    isLoading =
                                        true

                                    message =
                                        ""

                                    scope.launch {

                                        try {

                                            val response =
                                                RetrofitClient
                                                    .api
                                                    .login(
                                                        email =
                                                            studentEmail.trim(),

                                                        password =
                                                            password
                                                    )


                                            if (
                                                response
                                                    .isSuccessful
                                            ) {

                                                val loginResponse =
                                                    response.body()

                                                if (
                                                    loginResponse != null
                                                ) {
                                                    if (rememberLogin) {
                                                        runCatching {
                                                            LoginCredentialVault.save(
                                                                context,
                                                                studentEmail.trim(),
                                                                password
                                                            )
                                                        }.onFailure {
                                                            // Do not fail an otherwise successful login
                                                            // if this device cannot save credentials.
                                                        }
                                                    } else {
                                                        LoginCredentialVault.clear(context)
                                                    }

                                                    onLoginSuccess(
                                                        loginResponse.student_id,
                                                        loginResponse.full_name.orEmpty()
                                                    )

                                                } else {

                                                    message =
                                                        "Login failed. Please try again."
                                                }

                                            } else {

                                                message =
                                                    "Invalid email or password."
                                            }

                                        } catch (
                                            e: Exception
                                        ) {

                                            message =
                                                "Unable to connect to the voting server."

                                        } finally {

                                            isLoading =
                                                false
                                        }
                                    }
                                }
                            },

                            modifier =
                                Modifier
                                    .fillMaxWidth()
                                    .height(57.dp),

                            shape =
                                RoundedCornerShape(13.dp),

                            colors =
                                ButtonDefaults.buttonColors(
                                    containerColor =
                                        GzuGreen,

                                    contentColor =
                                        Color.White
                                )
                        ) {

                            if (isLoading) {

                                CircularProgressIndicator(
                                    color =
                                        Color.White,

                                    modifier =
                                        Modifier.size(23.dp),

                                    strokeWidth =
                                        2.5.dp
                                )

                            } else {

                                Text(
                                    text =
                                        "SIGN IN",

                                    fontWeight =
                                        FontWeight.Bold,

                                    fontSize =
                                        16.sp
                                )
                            }
                        }


                        Spacer(
                            modifier =
                                Modifier.height(20.dp)
                        )


                        Surface(
                            modifier =
                                Modifier.fillMaxWidth(),

                            shape =
                                RoundedCornerShape(12.dp),

                            color =
                                if (MaterialTheme.colorScheme.background == GzuDarkBackground) {
                                    Color(0xFF193426)
                                } else {
                                    GzuVeryLightGreen
                                }
                        ) {

                            Row(
                                modifier =
                                    Modifier.padding(13.dp),

                                verticalAlignment =
                                    Alignment.CenterVertically
                            ) {

                                Text(
                                    text =
                                        "✓",

                                    fontSize =
                                        20.sp,

                                    fontWeight =
                                        FontWeight.Bold,

                                    color =
                                        MaterialTheme
                                            .colorScheme
                                            .primary
                                )


                                Spacer(
                                    modifier =
                                        Modifier.width(10.dp)
                                )


                                Text(
                                    text =
                                        "Your voting credentials are handled securely.",

                                    fontSize =
                                        13.sp,

                                    color =
                                        MaterialTheme
                                            .colorScheme
                                            .onSurfaceVariant,

                                    lineHeight =
                                        18.sp
                                )
                            }
                        }


                        Spacer(
                            modifier =
                                Modifier.height(15.dp)
                        )


                        Text(
                            text =
                                "Great Zimbabwe University",

                            fontSize =
                                13.sp,

                            color =
                                MaterialTheme
                                    .colorScheme
                                    .onSurfaceVariant
                        )


                        Spacer(
                            modifier =
                                Modifier.height(10.dp)
                        )
                    }
                }
            }
        }
    }
}


// ============================================================
// VOTER DASHBOARD
// ============================================================

@Composable
fun StudentDashboardScreen(
    studentId: String,
    themeMode: ThemeMode,
    onThemeChange: (ThemeMode) -> Unit,
    largeText: Boolean,
    highContrast: Boolean,
    privacyMode: Boolean,
    onLargeTextChange: (Boolean) -> Unit,
    onHighContrastChange: (Boolean) -> Unit,
    onPrivacyModeChange: (Boolean) -> Unit,
    onVote: (Int) -> Unit,
    onResults: (Int) -> Unit,
    onNominate: () -> Unit,
    onMyNominations: () -> Unit,
    onAssistant: () -> Unit,
    onLogout: () -> Unit
) {
    var elections by remember {
        mutableStateOf<List<zw.ac.gzu.voting.api.Election>>(emptyList())
    }
    var message by remember { mutableStateOf("") }
    var isLoading by remember { mutableStateOf(true) }
    var isRefreshing by remember { mutableStateOf(false) }
    var showAppearanceDialog by remember { mutableStateOf(false) }
    var showSettingsDialog by remember { mutableStateOf(false) }
    var showAccessibilityDialog by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    fun loadElections() {
        scope.launch {
            isRefreshing = true
            message = ""
            try {
                val response = RetrofitClient.api.getElections()
                if (response.isSuccessful) {
                    elections = response.body() ?: emptyList()
                    if (elections.isEmpty()) message = "There are currently no elections available."
                } else {
                    message = "Unable to load elections."
                }
            } catch (e: Exception) {
                message = "Unable to connect to the voting server."
            } finally {
                isLoading = false
                isRefreshing = false
            }
        }
    }

    LaunchedEffect(Unit) { loadElections() }

    Box(
        modifier = Modifier.fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .windowInsetsPadding(WindowInsets.statusBars)
    ) {
        Column(modifier = Modifier.fillMaxSize()) {
            Surface(
                modifier = Modifier.fillMaxWidth(),
                color = MaterialTheme.colorScheme.surface,
                shadowElevation = 2.dp
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth().padding(horizontal = 20.dp, vertical = 15.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Surface(
                        modifier = Modifier.size(46.dp),
                        shape = CircleShape,
                        color = GzuLightGreen
                    ) {
                        Box(contentAlignment = Alignment.Center) {
                            Image(
                                painter = painterResource(id = R.drawable.gzu_logo),
                                contentDescription = "GZU logo",
                                modifier = Modifier.size(39.dp)
                            )
                        }
                    }
                    Spacer(Modifier.width(12.dp))
                    Column(modifier = Modifier.weight(1f)) {
                        Text("GZU Voting", fontSize = 18.sp, fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.onSurface)
                        Text("Institutional Election Portal", fontSize = 12.sp,
                            color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                    TextButton(onClick = onLogout) {
                        Text("Logout", color = MaterialTheme.colorScheme.error, fontWeight = FontWeight.SemiBold)
                    }
                }
            }

            LazyColumn(
                modifier = Modifier.weight(1f).fillMaxWidth().padding(horizontal = 18.dp),
                contentPadding = androidx.compose.foundation.layout.PaddingValues(bottom = 90.dp)
            ) {
                item {
                    Spacer(Modifier.height(25.dp))
                    Text("Welcome back", fontSize = 15.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    Spacer(Modifier.height(3.dp))
                    Text(studentId, fontSize = 27.sp, fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.onBackground)
                    Spacer(Modifier.height(7.dp))
                    Text("View elections and make your voice count.",
                        fontSize = 14.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    Spacer(Modifier.height(16.dp))
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text("Available elections", modifier = Modifier.weight(1f),
                            fontSize = 20.sp, fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.onBackground)
                        TextButton(onClick = { loadElections() }, enabled = !isRefreshing) {
                            Text(if (isRefreshing) "Refreshing…" else "Refresh")
                        }
                    }
                    Spacer(Modifier.height(8.dp))
                    if (isLoading) {
                        Box(Modifier.fillMaxWidth().padding(vertical = 35.dp), contentAlignment = Alignment.Center) {
                            CircularProgressIndicator(color = MaterialTheme.colorScheme.primary)
                        }
                    }
                    if (!isLoading && message.isNotEmpty()) {
                        Card(
                            modifier = Modifier.fillMaxWidth(),
                            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                            shape = RoundedCornerShape(14.dp)
                        ) {
                            Text(message, modifier = Modifier.padding(18.dp),
                                color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                        Spacer(Modifier.height(12.dp))
                    }
                }
                items(elections) { election ->
                    ElectionCard(
                        title = election.title,
                        description = election.description ?: "No description provided.",
                        status = election.status,
                        onVote = { onVote(election.id) },
                        onResults = { onResults(election.id) }
                    )
                    Spacer(Modifier.height(14.dp))
                }
                item {
                    Spacer(Modifier.height(12.dp))
                    Text(
                        "GZU Institutional Voting System • Blockchain-secured",
                        modifier = Modifier.fillMaxWidth().padding(vertical = 12.dp),
                        textAlign = TextAlign.Center,
                        fontSize = 12.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        }

        // Assistant shortcut sits directly above Settings in the bottom-right corner.
        androidx.compose.material3.FloatingActionButton(
            onClick = onAssistant,
            modifier = Modifier.align(Alignment.BottomEnd)
                .windowInsetsPadding(WindowInsets.navigationBars)
                .padding(end = 20.dp, bottom = 88.dp),
            containerColor = MaterialTheme.colorScheme.secondaryContainer,
            contentColor = MaterialTheme.colorScheme.onSecondaryContainer
        ) {
            Text("AI", fontSize = 18.sp, fontWeight = FontWeight.Bold)
        }

        // Settings stays in the bottom-right corner, below the AI shortcut.
        androidx.compose.material3.FloatingActionButton(
            onClick = { showSettingsDialog = true },
            modifier = Modifier.align(Alignment.BottomEnd)
                .windowInsetsPadding(WindowInsets.navigationBars)
                .padding(end = 20.dp, bottom = 20.dp),
            containerColor = MaterialTheme.colorScheme.primary,
            contentColor = MaterialTheme.colorScheme.onPrimary
        ) {
            Text("⚙", fontSize = 26.sp)
        }
    }

    if (showSettingsDialog) {
        AlertDialog(
            onDismissRequest = { showSettingsDialog = false },
            title = {
                Text("Settings", fontSize = 22.sp, fontWeight = FontWeight.Bold)
            },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    OutlinedButton(
                        onClick = { showSettingsDialog = false; onNominate() },
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(12.dp)
                    ) { Text("Apply to Become a Candidate") }
                    OutlinedButton(
                        onClick = { showSettingsDialog = false; onMyNominations() },
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(12.dp)
                    ) { Text("My Nominations") }
                    OutlinedButton(
                        onClick = { showSettingsDialog = false; showAppearanceDialog = true },
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(12.dp)
                    ) { Text("Appearance") }
                    OutlinedButton(
                        onClick = { showSettingsDialog = false; showAccessibilityDialog = true },
                        modifier = Modifier.fillMaxWidth().semantics { contentDescription = "Open accessibility settings" },
                        shape = RoundedCornerShape(12.dp)
                    ) { Text("Accessibility settings") }
                }
            },
            confirmButton = {
                TextButton(onClick = { showSettingsDialog = false }) { Text("CLOSE") }
            }
        )
    }

    if (showAccessibilityDialog) {
        AlertDialog(
            onDismissRequest = { showAccessibilityDialog = false },
            title = { Text("Accessibility settings", fontWeight = FontWeight.Bold) },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
                    Text("These settings are saved on this device. TalkBack can be enabled in Android Settings.")
                    Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth()) {
                        Column(Modifier.weight(1f)) {
                            Text("Larger text", fontWeight = FontWeight.SemiBold)
                            Text("Increase app text size by 25%.", color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                        Switch(checked = largeText, onCheckedChange = onLargeTextChange,
                            modifier = Modifier.semantics { contentDescription = "Larger text, ${if (largeText) "on" else "off"}" })
                    }
                    Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth()) {
                        Column(Modifier.weight(1f)) {
                            Text("High contrast", fontWeight = FontWeight.SemiBold)
                            Text("Use stronger foreground and background contrast.", color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                        Switch(checked = highContrast, onCheckedChange = onHighContrastChange,
                            modifier = Modifier.semantics { contentDescription = "High contrast, ${if (highContrast) "on" else "off"}" })
                    }
                    Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth()) {
                        Column(Modifier.weight(1f)) {
                            Text("Private ballot review", fontWeight = FontWeight.SemiBold)
                            Text("Hide candidate names on the review screen until you choose to reveal them.", color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                        Switch(checked = privacyMode, onCheckedChange = onPrivacyModeChange,
                            modifier = Modifier.semantics { contentDescription = "Private ballot review, ${if (privacyMode) "on" else "off"}" })
                    }
                    Text("For screen reading, turn on TalkBack in Android Settings → Accessibility. Test voting in a private place before an official election.",
                        color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            },
            confirmButton = { TextButton(onClick = { showAccessibilityDialog = false }) { Text("DONE") } }
        )
    }

    if (showAppearanceDialog) {
        AlertDialog(
            onDismissRequest = { showAppearanceDialog = false },
            title = { Text("Appearance", fontSize = 21.sp, fontWeight = FontWeight.Bold) },
            text = {
                Column(modifier = Modifier.fillMaxWidth()) {
                    Text("Choose how the app should look.", fontSize = 14.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant)
                    Spacer(Modifier.height(18.dp))
                    ThemeOptionButton("System", themeMode == ThemeMode.SYSTEM, Modifier.fillMaxWidth()) {
                        onThemeChange(ThemeMode.SYSTEM); showAppearanceDialog = false
                    }
                    Spacer(Modifier.height(9.dp))
                    ThemeOptionButton("Light", themeMode == ThemeMode.LIGHT, Modifier.fillMaxWidth()) {
                        onThemeChange(ThemeMode.LIGHT); showAppearanceDialog = false
                    }
                    Spacer(Modifier.height(9.dp))
                    ThemeOptionButton("Dark", themeMode == ThemeMode.DARK, Modifier.fillMaxWidth()) {
                        onThemeChange(ThemeMode.DARK); showAppearanceDialog = false
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = { showAppearanceDialog = false }) { Text("CLOSE") }
            }
        )
    }
}


// ============================================================
// THEME OPTION BUTTON
// ============================================================

@Composable
fun ThemeOptionButton(
    text: String,
    selected: Boolean,
    modifier: Modifier,
    onClick: () -> Unit
) {

    if (selected) {

        Button(
            onClick =
                onClick,

            modifier =
                modifier.height(43.dp),

            shape =
                RoundedCornerShape(10.dp),

            colors =
                ButtonDefaults.buttonColors(
                    containerColor =
                        MaterialTheme
                            .colorScheme
                            .primary,

                    contentColor =
                        MaterialTheme
                            .colorScheme
                            .onPrimary
                ),

            contentPadding =
                androidx.compose.foundation.layout.PaddingValues(
                    horizontal = 6.dp
                )
        ) {

            Text(
                text =
                    text,

                fontSize =
                    12.sp,

                fontWeight =
                    FontWeight.Bold
            )
        }

    } else {

        OutlinedButton(
            onClick =
                onClick,

            modifier =
                modifier.height(43.dp),

            shape =
                RoundedCornerShape(10.dp),

            border =
                BorderStroke(
                    1.dp,
                    MaterialTheme
                        .colorScheme
                        .outline
                ),

            contentPadding =
                androidx.compose.foundation.layout.PaddingValues(
                    horizontal = 6.dp
                )
        ) {

            Text(
                text =
                    text,

                fontSize =
                    12.sp,

                color =
                    MaterialTheme
                        .colorScheme
                        .onSurface
            )
        }
    }
}


// ============================================================
// ELECTION CARD
// ============================================================

@Composable
fun ElectionCard(
    title: String,
    description: String,
    status: String?,
    onVote: () -> Unit,
    onResults: () -> Unit
) {

    val normalizedStatus =
        status?.lowercase()
            ?: "unknown"


    val statusColor =
        when (normalizedStatus) {

            "ongoing" ->
                MaterialTheme
                    .colorScheme
                    .primary

            "upcoming" ->
                if (MaterialTheme.colorScheme.background == GzuDarkBackground) {
                    Color(0xFFFFD166)
                } else {
                    WarningText
                }

            "closed" ->
                MaterialTheme
                    .colorScheme
                    .error

            else ->
                MaterialTheme
                    .colorScheme
                    .onSurfaceVariant
        }


    val statusBackground =
        when (normalizedStatus) {

            "ongoing" ->
                if (MaterialTheme.colorScheme.background == GzuDarkBackground) {
                    Color(0xFF193E2B)
                } else {
                    GzuLightGreen
                }

            "upcoming" ->
                if (MaterialTheme.colorScheme.background == GzuDarkBackground) {
                    DarkWarningBackground
                } else {
                    WarningBackground
                }

            "closed" ->
                if (MaterialTheme.colorScheme.background == GzuDarkBackground) {
                    DarkDangerBackground
                } else {
                    DangerBackground
                }

            else ->
                MaterialTheme
                    .colorScheme
                    .surfaceVariant
        }


    Card(
        modifier =
            Modifier.fillMaxWidth(),

        shape =
            RoundedCornerShape(17.dp),

        colors =
            CardDefaults.cardColors(
                containerColor =
                    MaterialTheme
                        .colorScheme
                        .surface
            ),

        elevation =
            CardDefaults.cardElevation(
                defaultElevation =
                    2.dp
            )
    ) {

        Column(
            modifier =
                Modifier.padding(20.dp)
        ) {

            Row(
                modifier =
                    Modifier.fillMaxWidth(),

                verticalAlignment =
                    Alignment.CenterVertically
            ) {

                Surface(
                    modifier =
                        Modifier.size(48.dp),

                    shape =
                        RoundedCornerShape(12.dp),

                    color =
                        if (MaterialTheme.colorScheme.background == GzuDarkBackground) {
                            Color(0xFF193E2B)
                        } else {
                            GzuLightGreen
                        }
                ) {

                    Box(
                        contentAlignment =
                            Alignment.Center
                    ) {

                        Text(
                            text =
                                "E",

                            fontSize =
                                19.sp,

                            fontWeight =
                                FontWeight.Bold,

                            color =
                                MaterialTheme
                                    .colorScheme
                                    .primary
                        )
                    }
                }


                Spacer(
                    modifier =
                        Modifier.width(12.dp)
                )


                Column(
                    modifier =
                        Modifier.weight(1f)
                ) {

                    Text(
                        text =
                            title,

                        fontSize =
                            18.sp,

                        fontWeight =
                            FontWeight.Bold,

                        color =
                            MaterialTheme
                                .colorScheme
                                .onSurface
                    )


                    Spacer(
                        modifier =
                            Modifier.height(5.dp)
                    )


                    Surface(
                        shape =
                            RoundedCornerShape(20.dp),

                        color =
                            statusBackground
                    ) {

                        Text(
                            text =
                                normalizedStatus.uppercase(),

                            modifier =
                                Modifier.padding(
                                    horizontal = 11.dp,
                                    vertical = 6.dp
                                ),

                            fontSize =
                                11.sp,

                            fontWeight =
                                FontWeight.Bold,

                            color =
                                statusColor
                        )
                    }
                }
            }


            Spacer(
                modifier =
                    Modifier.height(16.dp)
            )


            Text(
                text =
                    description,

                fontSize =
                    14.sp,

                lineHeight =
                    21.sp,

                color =
                    MaterialTheme
                        .colorScheme
                        .onSurfaceVariant
            )


            Spacer(
                modifier =
                    Modifier.height(19.dp)
            )


            Row(
                modifier =
                    Modifier.fillMaxWidth(),

                horizontalArrangement =
                    Arrangement.spacedBy(10.dp)
            ) {

                Button(
                    onClick =
                        onVote,

                    enabled =
                        normalizedStatus ==
                                "ongoing",

                    modifier =
                        Modifier
                            .weight(1f)
                            .height(49.dp),

                    shape =
                        RoundedCornerShape(10.dp),

                    colors =
                        ButtonDefaults.buttonColors(
                            containerColor =
                                MaterialTheme
                                    .colorScheme
                                    .primary,

                            contentColor =
                                MaterialTheme
                                    .colorScheme
                                    .onPrimary,

                            disabledContainerColor =
                                MaterialTheme
                                    .colorScheme
                                    .surfaceVariant,

                            disabledContentColor =
                                MaterialTheme
                                    .colorScheme
                                    .onSurfaceVariant
                        )
                ) {

                    Text(
                        text =
                            if (
                                normalizedStatus ==
                                "ongoing"
                            ) {
                                "VOTE NOW"
                            } else if (
                                normalizedStatus ==
                                "upcoming"
                            ) {
                                "NOT OPEN"
                            } else {
                                "CLOSED"
                            },

                        fontSize =
                            12.sp,

                        fontWeight =
                            FontWeight.Bold
                    )
                }


                OutlinedButton(
                    onClick =
                        onResults,

                    modifier =
                        Modifier
                            .weight(1f)
                            .height(49.dp),

                    shape =
                        RoundedCornerShape(10.dp),

                    border =
                        BorderStroke(
                            1.dp,
                            MaterialTheme
                                .colorScheme
                                .primary
                        )
                ) {

                    Text(
                        text =
                            "RESULTS",

                        fontSize =
                            12.sp,

                        fontWeight =
                            FontWeight.Bold,

                        color =
                            MaterialTheme
                                .colorScheme
                                .primary
                    )
                }
            }
        }
    }
}


// ============================================================
// VOTING SCREEN
// ============================================================

@Composable
fun VotingScreen(
    studentId: String,
    electionId: Int,
    privacyMode: Boolean = true,
    onBack: () -> Unit,
    onViewResults: () -> Unit
) {
    var candidates by remember { mutableStateOf<List<Candidate>>(emptyList()) }
    var selectedByPosition by remember { mutableStateOf<Map<String, Int>>(emptyMap()) }
    var message by remember { mutableStateOf("") }
    var isLoading by remember { mutableStateOf(true) }
    var isSubmitting by remember { mutableStateOf(false) }
    var showConfirmation by remember { mutableStateOf(false) }
    var revealBallotSelections by remember { mutableStateOf(false) }
    var hasVoted by remember { mutableStateOf(false) }
    var profileCandidate by remember { mutableStateOf<Candidate?>(null) }
    var receiptCode by remember { mutableStateOf("") }
    var showReceiptDialog by remember { mutableStateOf(false) }
    var receiptVerificationMessage by remember { mutableStateOf("") }
    var isVerifyingReceipt by remember { mutableStateOf(false) }
    val context = LocalContext.current
    val scope = rememberCoroutineScope()

    LaunchedEffect(electionId, studentId) {
        try {
            val status = RetrofitClient.api.getVoterStatus(electionId, studentId)
            if (status.isSuccessful && status.body()?.has_voted == true) {
                hasVoted = true
                message = "Our records show that you have already voted in this election. Candidate selection is disabled."
            } else if (!status.isSuccessful) {
                message = status.errorBody()?.string()?.take(240) ?: "Unable to verify your voting status."
            } else {
                val response = RetrofitClient.api.getCandidates(electionId)
                if (response.isSuccessful) {
                    candidates = response.body().orEmpty()
                    if (candidates.isEmpty()) message = "No candidates are available for this election."
                } else message = "Failed to load candidates."
            }
        } catch (e: Exception) {
            message = "Unable to connect to the voting server. Please try again."
        } finally {
            isLoading = false
        }
    }

    profileCandidate?.let { candidate ->
        AlertDialog(
            onDismissRequest = { profileCandidate = null },
            title = { Text(candidate.name, fontWeight = FontWeight.Bold) },
            text = {
                LazyColumn(modifier = Modifier.height(430.dp)) {
                    item {
                        if (!candidate.photo_url.isNullOrBlank()) {
                            AsyncImage(
                                model = RetrofitClient.baseUrlFor(candidate.photo_url),
                                contentDescription = "Portrait of ${candidate.name}",
                                modifier = Modifier.fillMaxWidth().height(250.dp).clip(RoundedCornerShape(12.dp)),
                                contentScale = ContentScale.Crop
                            )
                        }
                        Spacer(Modifier.height(12.dp))
                        Text("Position: ${candidate.position}", fontWeight = FontWeight.SemiBold)
                        candidate.faculty?.takeIf { it.isNotBlank() }?.let { Text("Faculty: $it") }
                        candidate.department?.takeIf { it.isNotBlank() }?.let { Text("Department: $it") }
                        candidate.programme?.takeIf { it.isNotBlank() }?.let { Text("Programme: $it") }
                        candidate.year_of_study?.takeIf { it.isNotBlank() }?.let { Text("Year: $it") }
                        Spacer(Modifier.height(8.dp))
                        Text("Manifesto", fontWeight = FontWeight.Bold)
                        Text(candidate.manifesto?.takeIf { it.isNotBlank() } ?: "No manifesto supplied.")
                        Spacer(Modifier.height(8.dp))
                        Text("Experience", fontWeight = FontWeight.Bold)
                        Text(candidate.experience?.takeIf { it.isNotBlank() } ?: "No experience information supplied.")
                    }
                }
            },
            confirmButton = { TextButton(onClick = { profileCandidate = null }) { Text("Close") } }
        )
    }

    if (showConfirmation) {
        AlertDialog(
            onDismissRequest = { if (!isSubmitting) showConfirmation = false },
            title = { Text("Confirm your ballot") },
            text = {
                Column {
                    Text("Review your selections. Each position is submitted as one vote.")
                    Spacer(Modifier.height(10.dp))
                    if (privacyMode && !revealBallotSelections) {
                        Text("Your selected candidate names are hidden for privacy. Reveal them only when you are ready to review your ballot.")
                        OutlinedButton(onClick = { revealBallotSelections = true }, modifier = Modifier.fillMaxWidth()) {
                            Text("Reveal selections")
                        }
                    } else {
                        selectedByPosition.forEach { (position, candidateId) ->
                            val candidate = candidates.firstOrNull { it.id == candidateId }
                            Text(
                                "$position: ${candidate?.name ?: "Candidate"}",
                                fontWeight = FontWeight.SemiBold,
                                modifier = Modifier.semantics { contentDescription = "Selected candidate for $position: ${candidate?.name ?: "Candidate"}." }
                            )
                        }
                        if (privacyMode) {
                            TextButton(onClick = { revealBallotSelections = false }) { Text("Hide selections again") }
                        }
                    }
                    Spacer(Modifier.height(8.dp))
                    Text("Submitted votes cannot be changed.")
                    if (message.isNotBlank()) Text(message, color = MaterialTheme.colorScheme.error)
                }
            },
            confirmButton = {
                Button(
                    enabled = !isSubmitting,
                    onClick = {
                        isSubmitting = true
                        message = ""
                        scope.launch {
                            try {
                                // Recheck immediately before sending, so stale screens cannot submit a second ballot.
                                val status = RetrofitClient.api.getVoterStatus(electionId, studentId)
                                if (!status.isSuccessful || status.body()?.has_voted == true) {
                                    hasVoted = true
                                    message = "You have already voted in this election, or your voting status could not be verified. No new votes were submitted."
                                } else {
                                    if (selectedByPosition.isEmpty()) {
                                        message = "Select one candidate for at least one position."
                                    } else {
                                        val ballot = zw.ac.gzu.voting.api.BallotSubmission(
                                            student_id = studentId,
                                            election_id = electionId,
                                            selections = selectedByPosition.map { (position, candidateId) ->
                                                zw.ac.gzu.voting.api.BallotSelection(position, candidateId)
                                            }
                                        )
                                        val response = RetrofitClient.api.castBallot(ballot)
                                        if (response.isSuccessful) {
                                            val returnedReceipt = response.body()?.get("receipt_code")?.asString.orEmpty()
                                            receiptCode = returnedReceipt
                                            message = if (returnedReceipt.isNotBlank()) {
                                                "Your ballot was submitted. Save your receipt code to verify the transaction status later."
                                            } else {
                                                "Your ballot was submitted, but the server did not return a receipt code. Contact election support before leaving this screen."
                                            }
                                            hasVoted = true
                                            showConfirmation = false
                                            showReceiptDialog = returnedReceipt.isNotBlank()
                                        } else {
                                            message = response.errorBody()?.string()?.take(300)
                                                ?: "The ballot could not be submitted. Verify your status before retrying."
                                            // Refresh status so a completed ballot cannot return to candidate selection.
                                            val refreshed = RetrofitClient.api.getVoterStatus(electionId, studentId)
                                            if (refreshed.isSuccessful && refreshed.body()?.has_voted == true) {
                                                hasVoted = true
                                            }
                                        }
                                    }
                                }
                            } catch (e: Exception) {
                                message = "The server connection failed. Please verify your ballot status before retrying."
                            } finally {
                                isSubmitting = false
                            }
                        }
                    }
                ) {
                    if (isSubmitting) CircularProgressIndicator(modifier = Modifier.size(18.dp), strokeWidth = 2.dp)
                    else Text("Submit ballot")
                }
            },
            dismissButton = {
                TextButton(enabled = !isSubmitting, onClick = { showConfirmation = false }) { Text("Back") }
            }
        )
    }

    if (showReceiptDialog) {
        AlertDialog(
            onDismissRequest = { showReceiptDialog = false },
            title = { Text("Your voting receipt", fontWeight = FontWeight.Bold) },
            text = {
                Column {
                    Text("Keep this code private. You can use it to check whether the blockchain transactions associated with your ballot were confirmed.")
                    Spacer(Modifier.height(12.dp))
                    Text(
                        receiptCode,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.primary,
                        modifier = Modifier.semantics { contentDescription = "Your private voting receipt code: $receiptCode" }
                    )
                    Spacer(Modifier.height(12.dp))
                    if (receiptVerificationMessage.isNotBlank()) Text(receiptVerificationMessage)
                }
            },
            confirmButton = {
                TextButton(onClick = {
                    val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                    clipboard.setPrimaryClip(ClipData.newPlainText("GZU voting receipt", receiptCode))
                    receiptVerificationMessage = "Receipt code copied. Store it safely; it is needed for verification."
                }) { Text("Copy receipt") }
            },
            dismissButton = {
                Row {
                    TextButton(
                        enabled = !isVerifyingReceipt,
                        onClick = {
                            isVerifyingReceipt = true
                            receiptVerificationMessage = "Checking blockchain transaction status…"
                            scope.launch {
                                try {
                                    val result = RetrofitClient.api.verifyVoterReceipt(receiptCode)
                                    if (result.isSuccessful) {
                                        val body = result.body()
                                        val status = body?.get("status")?.asString ?: "unknown"
                                        val detail = body?.get("message")?.asString ?: "No additional details returned."
                                        receiptVerificationMessage = "Verification status: $status. $detail"
                                    } else {
                                        receiptVerificationMessage = if (result.code() == 404) {
                                            "Receipt not found. Check that the code was copied correctly."
                                        } else {
                                            "Verification could not be completed (HTTP ${result.code()}). Try again later."
                                        }
                                    }
                                } catch (_: Exception) {
                                    receiptVerificationMessage = "Could not reach the verification service. Your receipt is still saved; try again when online."
                                } finally {
                                    isVerifyingReceipt = false
                                }
                            }
                        }
                    ) { Text(if (isVerifyingReceipt) "Checking…" else "Verify") }
                    TextButton(onClick = { showReceiptDialog = false }) { Text("Close") }
                }
            }
        )
    }

    Column(
        modifier = Modifier.fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .windowInsetsPadding(WindowInsets.statusBars)
            .windowInsetsPadding(WindowInsets.navigationBars)
            .padding(horizontal = 16.dp, vertical = 10.dp)
    ) {
        AppHeader(
            title = "GZU Election Management System",
            subtitle = "Choose one candidate for each position",
            onBack = onBack
        )
        Spacer(Modifier.height(10.dp))
        if (isLoading) {
            Box(Modifier.fillMaxWidth().weight(1f), contentAlignment = Alignment.Center) {
                CircularProgressIndicator()
            }
        } else if (hasVoted) {
            Text(message, color = MaterialTheme.colorScheme.error, modifier = Modifier.padding(12.dp))
            Button(onClick = onViewResults, modifier = Modifier.fillMaxWidth()) { Text("View results") }
        } else {
            if (message.isNotBlank()) Text(
                message,
                color = MaterialTheme.colorScheme.error,
                modifier = Modifier.semantics { liveRegion = LiveRegionMode.Polite }
            )
            Text(
                "Accessibility: use your phone's screen reader (TalkBack) to hear candidate names, positions, selection status, and action labels. Candidate cards can be selected by double-tapping.",
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                style = MaterialTheme.typography.bodyMedium,
                modifier = Modifier.fillMaxWidth().padding(vertical = 6.dp)
            )
            LazyColumn(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                val positions = candidates.groupBy { it.position }.toList()
                items(positions, key = { it.first }) { (position, positionCandidates) ->
                    Column {
                        Text(position, fontSize = 20.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
                        Spacer(Modifier.height(6.dp))
                        positionCandidates.forEach { candidate ->
                            Column(
                                modifier = Modifier.fillMaxWidth().padding(bottom = 8.dp)
                            ) {
                                CandidateCard(
                                    candidate = candidate,
                                    selected = selectedByPosition[position] == candidate.id,
                                    onClick = { selectedByPosition = selectedByPosition + (position to candidate.id) }
                                )
                                TextButton(onClick = { profileCandidate = candidate }) { Text("View ${candidate.name}'s profile") }
                            }
                        }
                    }
                }
            }
            Spacer(Modifier.height(8.dp))
            Button(
                onClick = { revealBallotSelections = false; showConfirmation = true },
                enabled = selectedByPosition.isNotEmpty() && selectedByPosition.size == candidates.map { it.position }.distinct().size,
                modifier = Modifier.fillMaxWidth()
            ) {
                Text(
                    "Review and submit ballot. ${selectedByPosition.size} of ${candidates.map { it.position }.distinct().size} positions selected",
                    modifier = Modifier.semantics { contentDescription = "Review and submit ballot. ${selectedByPosition.size} of ${candidates.map { it.position }.distinct().size} positions selected." }
                )
            }
        }
        if (message.isNotBlank() && !isLoading && !hasVoted) {
            Text(message, color = if (message.contains("success", true)) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.error)
        }
    }
}


@Composable
fun CandidateCard(
    candidate: Candidate,
    selected: Boolean,
    onClick: () -> Unit
) {

    val borderColor =
        if (selected) {

            MaterialTheme
                .colorScheme
                .primary

        } else {

            MaterialTheme
                .colorScheme
                .outline
        }


    val background =
        if (selected) {

            if (MaterialTheme.colorScheme.background == GzuDarkBackground) {
                GzuSelectedDark
            } else {
                GzuSelectedLight
            }

        } else {

            MaterialTheme
                .colorScheme
                .surface
        }


    Card(
        onClick =
            onClick,

        modifier =
            Modifier
                .fillMaxWidth()
                .semantics(mergeDescendants = true) {
                    contentDescription = "${candidate.name}, ${candidate.position}. ${if (selected) "Selected" else "Not selected"}. Double tap to ${if (selected) "keep selected" else "select this candidate"}."
                    this.selected = selected
                    this.role = Role.RadioButton
                }
                .border(
                    width =
                        if (selected) {
                            2.dp
                        } else {
                            1.dp
                        },

                    color =
                        borderColor,

                    shape =
                        RoundedCornerShape(15.dp)
                ),

        shape =
            RoundedCornerShape(15.dp),

        colors =
            CardDefaults.cardColors(
                containerColor =
                    background
            ),

        elevation =
            CardDefaults.cardElevation(
                defaultElevation =
                    if (selected) {
                        3.dp
                    } else {
                        1.dp
                    }
            )
    ) {

        Row(
            modifier =
                Modifier
                    .fillMaxWidth()
                    .padding(18.dp),

            verticalAlignment =
                Alignment.CenterVertically
        ) {

            if (!candidate.photo_url.isNullOrBlank()) {
                AsyncImage(
                    model = RetrofitClient.baseUrlFor(candidate.photo_url),
                    contentDescription = "Photo of ${candidate.name}",
                    modifier = Modifier
                        .width(124.dp)
                        .height(160.dp)
                        .clip(RoundedCornerShape(12.dp)),
                    contentScale = ContentScale.Crop
                )
            } else {
                Surface(
                    modifier = Modifier.width(124.dp).height(160.dp),
                    shape = RoundedCornerShape(12.dp),
                    color = if (selected) MaterialTheme.colorScheme.primary
                    else if (MaterialTheme.colorScheme.background == GzuDarkBackground) Color(0xFF26352E)
                    else Color(0xFFEFF3F0)
                ) {
                    Box(contentAlignment = Alignment.Center) {
                        Text(
                            text = candidate.name.firstOrNull()?.uppercase() ?: "C",
                            fontSize = 19.sp,
                            fontWeight = FontWeight.Bold,
                            color = if (selected) MaterialTheme.colorScheme.onPrimary
                            else MaterialTheme.colorScheme.primary
                        )
                    }
                }
            }

            Spacer(
                modifier =
                    Modifier.width(14.dp)
            )


            Column(
                modifier =
                    Modifier.weight(1f)
            ) {

                Text(
                    text =
                        candidate.name,

                    fontSize =
                        18.sp,

                    fontWeight =
                        FontWeight.Bold,

                    color =
                        MaterialTheme
                            .colorScheme
                            .onSurface
                )


                Spacer(
                    modifier =
                        Modifier.height(4.dp)
                )


                Text(
                    text =
                        candidate.position,

                    fontSize =
                        13.sp,

                    color =
                        MaterialTheme
                            .colorScheme
                            .onSurfaceVariant
                )

                val academicDetails = listOfNotNull(
                    candidate.faculty?.takeIf { it.isNotBlank() }?.let { "Faculty: $it" },
                    candidate.department?.takeIf { it.isNotBlank() }?.let { "Department: $it" },
                    candidate.programme?.takeIf { it.isNotBlank() }?.let { "Programme: $it" },
                    candidate.year_of_study?.takeIf { it.isNotBlank() }?.let { "Year: $it" }
                )
                if (academicDetails.isNotEmpty()) {
                    Spacer(modifier = Modifier.height(5.dp))
                    Text(
                        text = academicDetails.joinToString(" • "),
                        fontSize = 12.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }

                candidate.manifesto?.takeIf { it.isNotBlank() }?.let { plan ->
                    Spacer(modifier = Modifier.height(6.dp))
                    Text(
                        text = "What I Plan to Do",
                        fontSize = 12.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = MaterialTheme.colorScheme.onSurface
                    )
                    Text(
                        text = plan,
                        fontSize = 12.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        maxLines = 3
                    )
                }
            }


            if (selected) {

                Surface(
                    modifier =
                        Modifier.size(31.dp),

                    shape =
                        CircleShape,

                    color =
                        MaterialTheme
                            .colorScheme
                            .primary
                ) {

                    Box(
                        contentAlignment =
                            Alignment.Center
                    ) {

                        Text(
                            text =
                                "✓",

                            color =
                                MaterialTheme
                                    .colorScheme
                                    .onPrimary,

                            fontWeight =
                                FontWeight.Bold
                        )
                    }
                }

            } else {

                Surface(
                    modifier =
                        Modifier.size(31.dp),

                    shape =
                        CircleShape,

                    color =
                        MaterialTheme
                            .colorScheme
                            .surface,

                    border =
                        BorderStroke(
                            1.dp,
                            MaterialTheme
                                .colorScheme
                                .outline
                        )
                ) {}
            }
        }
    }
}


// ============================================================
// LIVE RESULTS SCREEN
// ============================================================

private fun formPart(value: String): okhttp3.RequestBody =
    okhttp3.RequestBody.create(okhttp3.MultipartBody.FORM, value)

@Composable
fun NominationScreen(studentId: String, fullName: String, onBack: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var elections by remember { mutableStateOf<List<zw.ac.gzu.voting.api.Election>>(emptyList()) }
    var selectedElection by remember { mutableStateOf<zw.ac.gzu.voting.api.Election?>(null) }
    var position by remember { mutableStateOf("President") }
    var faculty by remember { mutableStateOf("") }
    var department by remember { mutableStateOf("") }
    var programme by remember { mutableStateOf("") }
    var year by remember { mutableStateOf("") }
    var manifesto by remember { mutableStateOf("") }
    var experience by remember { mutableStateOf("") }
    var photoUri by remember { mutableStateOf<Uri?>(null) }
    var message by remember { mutableStateOf("") }
    var loading by remember { mutableStateOf(false) }
    val photoPicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri -> photoUri = uri }

    LaunchedEffect(Unit) {
        try {
            val r = RetrofitClient.api.getElections()
            if (r.isSuccessful) elections = (r.body() ?: emptyList()).filter { it.status.equals("upcoming", true) }
            if (elections.isEmpty()) message = "There are no upcoming elections accepting nominations."
        } catch (_: Exception) { message = "Could not load elections. Check your connection to the server." }
    }

    Column(Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background).windowInsetsPadding(WindowInsets.statusBars).windowInsetsPadding(WindowInsets.navigationBars).padding(18.dp)) {
        AppHeader("Candidate Nomination", "Submit your details for admin review", onBack)
        LazyColumn(verticalArrangement = Arrangement.spacedBy(10.dp)) {
            item { Text("Institutional ID: $studentId", fontWeight = FontWeight.Bold) }
            item { Text("Select election", fontWeight = FontWeight.SemiBold) }
            items(elections) { e ->
                OutlinedButton(onClick = { selectedElection = e }, modifier = Modifier.fillMaxWidth(), border = BorderStroke(1.dp, if (selectedElection?.id == e.id) GzuGreen else MaterialTheme.colorScheme.outline)) {
                    Text((if (selectedElection?.id == e.id) "✓  " else "") + e.title)
                }
            }
            item { OutlinedTextField(position, { position = it }, label = { Text("Position (e.g. President)") }, modifier = Modifier.fillMaxWidth(), singleLine = true) }
            item {
                OutlinedTextField(
                    value = fullName,
                    onValueChange = {},
                    readOnly = true,
                    label = { Text("Official nominator name") },
                    placeholder = { Text("Sign in with a verified GZU account") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )
                if (fullName.isBlank()) {
                    Text(
                        "Identity not verified. The official GZU Registry/HR roster must contain this ID before you can nominate.",
                        color = MaterialTheme.colorScheme.error
                    )
                }
            }
            item { OutlinedTextField(faculty, { faculty = it }, label = { Text("Faculty / Division") }, modifier = Modifier.fillMaxWidth(), singleLine = true) }
            item { OutlinedTextField(department, { department = it }, label = { Text("Department / Unit") }, modifier = Modifier.fillMaxWidth(), singleLine = true) }
            item { OutlinedTextField(programme, { programme = it }, label = { Text("Programme / Role") }, modifier = Modifier.fillMaxWidth(), singleLine = true) }
            item { OutlinedTextField(year, { year = it }, label = { Text("Year of study / Service years (enter N/A if not applicable)") }, modifier = Modifier.fillMaxWidth(), singleLine = true) }
            item { OutlinedTextField(manifesto, { manifesto = it }, label = { Text("Manifesto") }, modifier = Modifier.fillMaxWidth(), minLines = 3) }
            item { OutlinedTextField(experience, { experience = it }, label = { Text("Experience (optional)") }, modifier = Modifier.fillMaxWidth(), minLines = 2) }
            item {
                OutlinedButton(onClick = { photoPicker.launch("image/*") }, modifier = Modifier.fillMaxWidth()) {
                    Text(if (photoUri == null) "Choose candidate photo" else "Photo selected — choose another")
                }
                photoUri?.let { Text("Selected image: ${it.lastPathSegment ?: "photo"}", color = MaterialTheme.colorScheme.onSurfaceVariant) }
            }
            item {
                Button(enabled = !loading && selectedElection != null && faculty.isNotBlank() && department.isNotBlank() && programme.isNotBlank() && manifesto.isNotBlank() && photoUri != null,
                    onClick = {
                        scope.launch {
                            loading = true; message = ""
                            try {
                                val uri = photoUri!!
                                val bytes = context.contentResolver.openInputStream(uri)?.use { it.readBytes() } ?: throw Exception("Could not read selected photo")
                                val mime = context.contentResolver.getType(uri) ?: "image/jpeg"
                                val fileBody = bytes.toRequestBody(mime.toMediaType())
                                val photo = okhttp3.MultipartBody.Part.createFormData("photo", "candidate_photo.${if (mime.contains("png")) "png" else if (mime.contains("webp")) "webp" else "jpg"}", fileBody)
                                val response = RetrofitClient.api.submitNomination(
                                    formPart(studentId), formPart(selectedElection!!.id.toString()), formPart(position), formPart(fullName),
                                    formPart(faculty), formPart(department), formPart(programme), formPart(year), formPart(manifesto), formPart(experience), photo
                                )
                                message = if (response.isSuccessful) "Nomination submitted successfully. Status: PENDING. You can check updates under My Nominations." else "Submission failed (${response.code()}): ${response.errorBody()?.string() ?: "Please check your details and try again."}"
                            } catch (e: Exception) { message = "Could not submit nomination: ${e.message ?: "connection error"}" }
                            finally { loading = false }
                        }
                    }, modifier = Modifier.fillMaxWidth().height(50.dp)) {
                    if (loading) CircularProgressIndicator(Modifier.size(20.dp), strokeWidth = 2.dp) else Text("Submit Nomination")
                }
            }
            if (message.isNotBlank()) item { Text(message, color = if (message.contains("successfully")) GzuGreen else MaterialTheme.colorScheme.error) }
        }
    }
}

@Composable
fun MyNominationsScreen(studentId: String, onBack: () -> Unit) {
    var nominations by remember { mutableStateOf<List<Nomination>>(emptyList()) }
    var message by remember { mutableStateOf("Loading nominations...") }
    var loading by remember { mutableStateOf(true) }
    val scope = rememberCoroutineScope()
    fun reload() {
        scope.launch {
            loading = true
            try {
                val r = RetrofitClient.api.getStudentNominations(studentId)
                if (r.isSuccessful) { nominations = r.body() ?: emptyList(); message = if (nominations.isEmpty()) "You have not submitted any nominations yet." else "" }
                else message = "Could not load nominations (${r.code()})."
            } catch (_: Exception) { message = "Could not connect to the server. Check the backend URL and Wi-Fi connection." }
            finally { loading = false }
        }
    }
    LaunchedEffect(studentId) { reload() }
    Column(Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background).windowInsetsPadding(WindowInsets.statusBars).windowInsetsPadding(WindowInsets.navigationBars).padding(18.dp)) {
        AppHeader("My Nominations", "Review status and administrator feedback", onBack)
        OutlinedButton(onClick = { reload() }, modifier = Modifier.fillMaxWidth()) { Text("Refresh status") }
        if (loading) CircularProgressIndicator(Modifier.padding(20.dp))
        if (message.isNotBlank()) Text(message, Modifier.padding(vertical = 14.dp), color = MaterialTheme.colorScheme.onSurfaceVariant)
        LazyColumn(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            items(nominations) { n ->
                Card(Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)) {
                    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        Text(n.full_name, fontWeight = FontWeight.Bold, fontSize = 18.sp)
                        Text("Position: ${n.position}")
                        Text("Election ID: ${n.election_id}")
                        Text("Status: ${n.status.uppercase()}", color = when (n.status.lowercase()) { "approved" -> GzuGreen; "rejected" -> MaterialTheme.colorScheme.error; else -> WarningText }, fontWeight = FontWeight.Bold)
                        if (!n.admin_feedback.isNullOrBlank()) Text("Administrator feedback: ${n.admin_feedback}")
                    }
                }
            }
        }
    }
}

@Composable
fun LiveResultsScreen(
    electionId: Int,
    onBack: () -> Unit
) {

    var electionTitle by remember {
        mutableStateOf("")
    }

    var results by remember {
        mutableStateOf<List<ElectionResult>>(
            emptyList()
        )
    }

    var message by remember {
        mutableStateOf("")
    }

    var isLoading by remember {
        mutableStateOf(true)
    }

    var lastUpdated by remember {
        mutableStateOf("")
    }


    LaunchedEffect(electionId) {

        while (true) {

            try {

                val response =
                    RetrofitClient
                        .api
                        .getElectionResults(
                            electionId
                        )


                if (response.isSuccessful) {

                    val resultData =
                        response.body()


                    if (resultData != null) {

                        electionTitle =
                            resultData
                                .election_title

                        results =
                            resultData.results


                        val currentTime =
                            java.text
                                .SimpleDateFormat(
                                    "HH:mm:ss",
                                    java.util.Locale
                                        .getDefault()
                                )
                                .format(
                                    java.util.Date()
                                )


                        lastUpdated =
                            currentTime

                        message =
                            ""
                    }

                } else {

                    message =
                        "Unable to load election results."
                }

            } catch (
                e: Exception
            ) {

                message =
                    "Unable to connect to the voting server."

            } finally {

                isLoading =
                    false
            }


            delay(3000)
        }
    }


    Column(
        modifier =
            Modifier
                .fillMaxSize()
                .background(
                    MaterialTheme
                        .colorScheme
                        .background
                )
                .windowInsetsPadding(
                    WindowInsets.statusBars
                )
                .windowInsetsPadding(
                    WindowInsets.navigationBars
                )
                .padding(
                    horizontal = 20.dp
                )
    ) {

        Spacer(
            modifier =
                Modifier.height(15.dp)
        )


        AppHeader(
            title =
                "Election Results",

            subtitle =
                "Live blockchain-based results.",

            onBack =
                onBack
        )


        if (electionTitle.isNotEmpty()) {

            Card(
                modifier =
                    Modifier.fillMaxWidth(),

                shape =
                    RoundedCornerShape(15.dp),

                colors =
                    CardDefaults.cardColors(
                        containerColor =
                            MaterialTheme
                                .colorScheme
                                .primary
                    )
            ) {

                Column(
                    modifier =
                        Modifier.padding(19.dp)
                ) {

                    Text(
                        text =
                            "CURRENT ELECTION",

                        fontSize =
                            11.sp,

                        fontWeight =
                            FontWeight.Bold,

                        color =
                            MaterialTheme
                                .colorScheme
                                .onPrimary
                                .copy(
                                    alpha =
                                        0.75f
                                )
                    )


                    Spacer(
                        modifier =
                            Modifier.height(6.dp)
                    )


                    Text(
                        text =
                            electionTitle,

                        fontSize =
                            20.sp,

                        fontWeight =
                            FontWeight.Bold,

                        color =
                            MaterialTheme
                                .colorScheme
                                .onPrimary
                    )


                    Spacer(
                        modifier =
                            Modifier.height(9.dp)
                    )


                    Row(
                        verticalAlignment =
                            Alignment.CenterVertically
                    ) {

                        Surface(
                            modifier =
                                Modifier.size(9.dp),

                            shape =
                                CircleShape,

                            color =
                                Color(0xFF75E39A)
                        ) {}


                        Spacer(
                            modifier =
                                Modifier.width(7.dp)
                        )


                        Text(
                            text =
                                "Results updating automatically",

                            fontSize =
                                12.sp,

                            color =
                                MaterialTheme
                                    .colorScheme
                                    .onPrimary
                                    .copy(
                                        alpha =
                                            0.85f
                                    )
                        )
                    }
                }
            }


            Spacer(
                modifier =
                    Modifier.height(15.dp)
            )
        }


        if (lastUpdated.isNotEmpty()) {

            Text(
                text =
                    "Last updated: $lastUpdated",

                fontSize =
                    12.sp,

                color =
                    MaterialTheme
                        .colorScheme
                        .onSurfaceVariant
            )


            Spacer(
                modifier =
                    Modifier.height(12.dp)
            )
        }


        if (isLoading) {

            Column(
                modifier =
                    Modifier
                        .fillMaxWidth()
                        .weight(1f),

                horizontalAlignment =
                    Alignment.CenterHorizontally,

                verticalArrangement =
                    Arrangement.Center
            ) {

                CircularProgressIndicator(
                    color =
                        MaterialTheme
                            .colorScheme
                            .primary
                )


                Spacer(
                    modifier =
                        Modifier.height(12.dp)
                )


                Text(
                    text =
                        "Loading results...",

                    color =
                        MaterialTheme
                            .colorScheme
                            .onSurfaceVariant,

                    fontSize =
                        14.sp
                )
            }

        } else if (results.isEmpty()) {

            Column(
                modifier =
                    Modifier
                        .fillMaxWidth()
                        .weight(1f),

                horizontalAlignment =
                    Alignment.CenterHorizontally,

                verticalArrangement =
                    Arrangement.Center
            ) {

                Text(
                    text =
                        "No results available",

                    fontSize =
                        20.sp,

                    fontWeight =
                        FontWeight.Bold,

                    color =
                        MaterialTheme
                            .colorScheme
                            .onBackground
                )


                Spacer(
                    modifier =
                        Modifier.height(8.dp)
                )


                Text(
                    text =
                        "Results will appear here when available.",

                    fontSize =
                        14.sp,

                    color =
                        MaterialTheme
                            .colorScheme
                            .onSurfaceVariant,

                    textAlign =
                        TextAlign.Center
                )
            }

        } else {

            LazyColumn(
                modifier =
                    Modifier
                        .fillMaxWidth()
                        .weight(1f)
            ) {

                items(results) { result ->

                    ResultCard(
                        position =
                            result.position,

                        candidateName =
                            result.name,

                        votes =
                            result.votes
                    )


                    Spacer(
                        modifier =
                            Modifier.height(10.dp)
                    )
                }
            }
        }


        if (message.isNotEmpty()) {

            Surface(
                modifier =
                    Modifier.fillMaxWidth(),

                shape =
                    RoundedCornerShape(11.dp),

                color =
                    if (MaterialTheme.colorScheme.background == GzuDarkBackground) {
                        DarkDangerBackground
                    } else {
                        DangerBackground
                    }
            ) {

                Text(
                    text =
                        message,

                    modifier =
                        Modifier.padding(12.dp),

                    color =
                        MaterialTheme
                            .colorScheme
                            .error,

                    fontSize =
                        13.sp
                )
            }


            Spacer(
                modifier =
                    Modifier.height(10.dp)
            )
        }


        OutlinedButton(
            onClick =
                onBack,

            modifier =
                Modifier
                    .fillMaxWidth()
                    .height(52.dp),

            shape =
                RoundedCornerShape(11.dp)
        ) {

            Text(
                text =
                    "BACK TO ELECTIONS",

                color =
                    MaterialTheme
                        .colorScheme
                        .primary,

                fontWeight =
                    FontWeight.Bold,

                fontSize =
                    14.sp
            )
        }


        Spacer(
            modifier =
                Modifier.height(15.dp)
        )
    }
}


// ============================================================
// RESULT CARD
// ============================================================

@Composable
fun ResultCard(
    position: String,
    candidateName: String,
    votes: Int
) {

    Card(
        modifier =
            Modifier.fillMaxWidth(),

        shape =
            RoundedCornerShape(15.dp),

        colors =
            CardDefaults.cardColors(
                containerColor =
                    MaterialTheme
                        .colorScheme
                        .surface
            ),

        elevation =
            CardDefaults.cardElevation(
                defaultElevation =
                    1.dp
            )
    ) {

        Column(
            modifier =
                Modifier.padding(18.dp)
        ) {

            Text(
                text =
                    position.uppercase(),

                fontSize =
                    11.sp,

                fontWeight =
                    FontWeight.Bold,

                color =
                    MaterialTheme
                        .colorScheme
                        .primary,

                letterSpacing =
                    0.8.sp
            )


            Spacer(
                modifier =
                    Modifier.height(7.dp)
            )


            Row(
                modifier =
                    Modifier.fillMaxWidth(),

                verticalAlignment =
                    Alignment.CenterVertically
            ) {

                Surface(
                    modifier =
                        Modifier.size(46.dp),

                    shape =
                        CircleShape,

                    color =
                        if (MaterialTheme.colorScheme.background == GzuDarkBackground) {
                            Color(0xFF193E2B)
                        } else {
                            GzuLightGreen
                        }
                ) {

                    Box(
                        contentAlignment =
                            Alignment.Center
                    ) {

                        Text(
                            text =
                                candidateName
                                    .firstOrNull()
                                    ?.uppercase()
                                    ?: "C",

                            color =
                                MaterialTheme
                                    .colorScheme
                                    .primary,

                            fontWeight =
                                FontWeight.Bold,

                            fontSize =
                                18.sp
                        )
                    }
                }


                Spacer(
                    modifier =
                        Modifier.width(12.dp)
                )


                Column(
                    modifier =
                        Modifier.weight(1f)
                ) {

                    Text(
                        text =
                            candidateName,

                        fontSize =
                            17.sp,

                        fontWeight =
                            FontWeight.Bold,

                        color =
                            MaterialTheme
                                .colorScheme
                                .onSurface
                    )


                    Spacer(
                        modifier =
                            Modifier.height(4.dp)
                    )


                    Text(
                        text =
                            "$votes votes",

                        fontSize =
                            13.sp,

                        color =
                            MaterialTheme
                                .colorScheme
                                .onSurfaceVariant
                    )
                }


                Text(
                    text =
                        votes.toString(),

                    fontSize =
                        23.sp,

                    fontWeight =
                        FontWeight.Bold,

                    color =
                        MaterialTheme
                            .colorScheme
                            .primary
                )
            }


            Spacer(
                modifier =
                    Modifier.height(12.dp)
            )


            LinearProgressIndicator(
                progress = {

                    if (votes > 0) {
                        1f
                    } else {
                        0f
                    }
                },

                modifier =
                    Modifier
                        .fillMaxWidth()
                        .height(5.dp)
                        .clip(
                            RoundedCornerShape(10.dp)
                        ),

                color =
                    MaterialTheme
                        .colorScheme
                        .primary,

                trackColor =
                    if (MaterialTheme.colorScheme.background == GzuDarkBackground) {
                        Color(0xFF26352E)
                    } else {
                        GzuLightGreen
                    }
            )
        }
    }
}