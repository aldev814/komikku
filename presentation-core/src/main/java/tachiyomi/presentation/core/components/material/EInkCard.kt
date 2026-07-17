package tachiyomi.presentation.core.components.material

import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Shape
import tachiyomi.presentation.core.theme.EInkStyle
import tachiyomi.presentation.core.theme.LocalEInkMode
import androidx.compose.material3.ElevatedCard as MaterialElevatedCard

@Composable
fun ElevatedCard(
    modifier: Modifier = Modifier,
    shape: Shape = CardDefaults.elevatedShape,
    content: @Composable ColumnScope.() -> Unit,
) {
    if (LocalEInkMode.current) {
        Card(
            modifier = modifier,
            shape = EInkStyle.cardShape,
            border = EInkStyle.border(MaterialTheme.colorScheme.outline),
            colors = CardDefaults.cardColors(),
            content = content,
        )
    } else {
        MaterialElevatedCard(modifier = modifier, shape = shape, content = content)
    }
}
