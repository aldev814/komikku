package tachiyomi.presentation.core.theme

import androidx.compose.foundation.border
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.RectangleShape
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.window.DialogWindowProvider

/** Compose Dialog owns its own Android window; the activity's animation style is insufficient. */
@Composable
fun EInkDialogWindow() {
    val window = (LocalView.current.parent as? DialogWindowProvider)?.window
    val enabled = LocalEInkMode.current
    SideEffect {
        if (enabled) window?.setWindowAnimations(0)
    }
}

@Composable
fun Modifier.eInkOutline(shape: Shape = RectangleShape): Modifier =
    if (LocalEInkMode.current) border(EInkStyle.border(MaterialTheme.colorScheme.outline), shape) else this
