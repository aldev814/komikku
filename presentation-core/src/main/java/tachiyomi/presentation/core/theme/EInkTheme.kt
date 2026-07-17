package tachiyomi.presentation.core.theme

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.IndicationNodeFactory
import androidx.compose.foundation.interaction.InteractionSource
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.ColorScheme
import androidx.compose.material3.Shapes
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.material3.surfaceColorAtElevation
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.node.DelegatableNode
import androidx.compose.ui.unit.dp

/** UI policy only. Reader page rendering and vendor page-turn effects are independent. */
val LocalEInkMode = staticCompositionLocalOf { false }

object EInkStyle {
    val borderWidth = 1.dp
    val cardShape = RoundedCornerShape(8.dp)
    val panelShape = RoundedCornerShape(12.dp)
    val shapes = Shapes(
        extraSmall = RoundedCornerShape(4.dp),
        small = RoundedCornerShape(6.dp),
        medium = cardShape,
        large = RoundedCornerShape(10.dp),
        extraLarge = panelShape,
    )

    fun readerBarColor(scheme: ColorScheme, enabled: Boolean, dark: Boolean): Color =
        if (enabled) scheme.surface else scheme.surfaceColorAtElevation(3.dp).copy(alpha = if (dark) 0.9f else 0.95f)

    fun border(color: Color) = BorderStroke(borderWidth, color)
    fun useCoverColors(enabled: Boolean, coverColors: Boolean) = !enabled && coverColors

    fun colorScheme(dark: Boolean): ColorScheme {
        val background = if (dark) Color.Black else Color.White
        val foreground = if (dark) Color.White else Color.Black
        val scheme = if (dark) darkColorScheme() else lightColorScheme()
        return scheme.copy(
            primary = foreground, onPrimary = background,
            primaryContainer = foreground, onPrimaryContainer = background,
            inversePrimary = background,
            secondary = foreground, onSecondary = background,
            secondaryContainer = foreground, onSecondaryContainer = background,
            tertiary = foreground, onTertiary = background,
            tertiaryContainer = foreground, onTertiaryContainer = background,
            background = background, onBackground = foreground,
            surface = background, onSurface = foreground,
            surfaceVariant = background, onSurfaceVariant = foreground,
            surfaceTint = Color.Transparent,
            inverseSurface = foreground, inverseOnSurface = background,
            error = foreground, onError = background,
            errorContainer = foreground, onErrorContainer = background,
            outline = foreground, outlineVariant = foreground,
            scrim = Color.Black,
            surfaceBright = background, surfaceDim = background,
            surfaceContainer = background, surfaceContainerHigh = background,
            surfaceContainerHighest = background, surfaceContainerLow = background,
            surfaceContainerLowest = background,
            primaryFixed = Color.Black, primaryFixedDim = Color.Black,
            onPrimaryFixed = Color.White, onPrimaryFixedVariant = Color.White,
            secondaryFixed = Color.Black, secondaryFixedDim = Color.Black,
            onSecondaryFixed = Color.White, onSecondaryFixedVariant = Color.White,
            tertiaryFixed = Color.Black, tertiaryFixedDim = Color.Black,
            onTertiaryFixed = Color.White, onTertiaryFixedVariant = Color.White,
        )
    }
}

/** Foundation clickables require a non-null factory; Material ripples are disabled separately. */
object NoEInkIndication : IndicationNodeFactory {
    override fun create(interactionSource: InteractionSource): DelegatableNode = object : Modifier.Node() {}
    override fun equals(other: Any?) = other === this
    override fun hashCode() = javaClass.hashCode()
}
