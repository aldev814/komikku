package tachiyomi.presentation.core.components.material

import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.SwitchColors
import androidx.compose.material3.SwitchDefaults
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.drawWithContent
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import tachiyomi.presentation.core.theme.EInkStyle
import tachiyomi.presentation.core.theme.LocalEInkMode
import androidx.compose.material3.Switch as MaterialSwitch

/** Rectangular rendering of the existing switch, including switches controlled by a whole row. */
@Composable
fun EInkSwitch(
    checked: Boolean,
    onCheckedChange: ((Boolean) -> Unit)?,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    colors: SwitchColors = SwitchDefaults.colors(),
    interactionSource: MutableInteractionSource? = null,
) {
    val eInkMode = LocalEInkMode.current
    val rtl = LocalLayoutDirection.current == LayoutDirection.Rtl
    val background = MaterialTheme.colorScheme.surface
    val foreground = MaterialTheme.colorScheme.onSurface.copy(alpha = if (enabled) 1f else DISABLED_ALPHA)
    MaterialSwitch(
        checked = checked,
        onCheckedChange = onCheckedChange,
        enabled = enabled,
        colors = colors,
        interactionSource = interactionSource,
        modifier = if (!eInkMode) {
            modifier
        } else {
            modifier.drawWithContent {
                // Match the standard 52 x 32 dp track, centered in Material's original touch target.
                val track = Size(minOf(52.dp.toPx(), size.width), minOf(32.dp.toPx(), size.height))
                val origin = Offset((size.width - track.width) / 2, (size.height - track.height) / 2)
                val stroke = EInkStyle.borderWidth.toPx()
                drawRect(background, origin, track)
                if (checked) drawRect(foreground, origin, track)
                drawRect(
                    foreground,
                    origin + Offset(stroke / 2, stroke / 2),
                    Size((track.width - stroke).coerceAtLeast(0f), (track.height - stroke).coerceAtLeast(0f)),
                    style = Stroke(stroke),
                )
                val inset = minOf(4.dp.toPx(), track.height / 4, track.width / 4)
                val thumb = (track.height - inset * 2).coerceIn(0f, (track.width - inset * 2).coerceAtLeast(0f))
                val thumbX = if (checked != rtl) track.width - inset - thumb else inset
                drawRect(
                    if (checked) background else foreground,
                    origin + Offset(thumbX, (track.height - thumb) / 2),
                    Size(thumb, thumb),
                )
            }
        },
    )
}
