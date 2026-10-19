package zw.ac.gzu.voting.ui.theme

import android.app.Activity
import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.platform.LocalContext

private val DarkColorScheme = darkColorScheme(
    primary = androidx.compose.ui.graphics.Color(0xFF8FE3B1),
    onPrimary = androidx.compose.ui.graphics.Color(0xFF082A19),
    secondary = androidx.compose.ui.graphics.Color(0xFFB5DCC5),
    onSecondary = androidx.compose.ui.graphics.Color(0xFF14251B),
    tertiary = androidx.compose.ui.graphics.Color(0xFFD8C4F2),
    background = androidx.compose.ui.graphics.Color(0xFF111815),
    onBackground = androidx.compose.ui.graphics.Color(0xFFE5EEE8),
    surface = androidx.compose.ui.graphics.Color(0xFF19221D),
    onSurface = androidx.compose.ui.graphics.Color(0xFFE5EEE8),
    surfaceVariant = androidx.compose.ui.graphics.Color(0xFF29372F),
    onSurfaceVariant = androidx.compose.ui.graphics.Color(0xFFC5D2C9),
    outline = androidx.compose.ui.graphics.Color(0xFF8B9B90)
)

private val LightColorScheme = lightColorScheme(
    primary = androidx.compose.ui.graphics.Color(0xFF006B3F),
    onPrimary = androidx.compose.ui.graphics.Color.White,
    secondary = androidx.compose.ui.graphics.Color(0xFF315B46),
    onSecondary = androidx.compose.ui.graphics.Color.White,
    tertiary = androidx.compose.ui.graphics.Color(0xFF5C5477),
    background = androidx.compose.ui.graphics.Color(0xFFF4F7F5),
    onBackground = androidx.compose.ui.graphics.Color(0xFF17231B),
    surface = androidx.compose.ui.graphics.Color(0xFFFFFFFF),
    onSurface = androidx.compose.ui.graphics.Color(0xFF17231B),
    surfaceVariant = androidx.compose.ui.graphics.Color(0xFFE4EEE7),
    onSurfaceVariant = androidx.compose.ui.graphics.Color(0xFF42564A),
    outline = androidx.compose.ui.graphics.Color(0xFF6E8175)

    /* Other default colors to override
    background = Color(0xFFFFFBFE),
    surface = Color(0xFFFFFBFE),
    onPrimary = Color.White,
    onSecondary = Color.White,
    onTertiary = Color.White,
    onBackground = Color(0xFF1C1B1F),
    onSurface = Color(0xFF1C1B1F),
    */
)

@Composable
fun GZUVotingTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    // Dynamic color is available on Android 12+
    dynamicColor: Boolean = true,
    content: @Composable () -> Unit
) {
    val colorScheme = when {
        false && dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
            val context = LocalContext.current
            if (darkTheme) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
        }

        darkTheme -> DarkColorScheme
        else -> LightColorScheme
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
}