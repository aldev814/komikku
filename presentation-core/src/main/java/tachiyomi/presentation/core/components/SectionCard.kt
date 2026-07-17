package tachiyomi.presentation.core.components

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyItemScope
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import dev.icerock.moko.resources.StringResource
import tachiyomi.presentation.core.components.material.padding
import tachiyomi.presentation.core.i18n.stringResource
import tachiyomi.presentation.core.theme.EInkStyle
import tachiyomi.presentation.core.theme.LocalEInkMode

@Composable
fun LazyItemScope.SectionCard(
    titleRes: StringResource? = null,
    content: @Composable ColumnScope.() -> Unit,
) {
    if (titleRes != null) {
        Text(
            modifier = Modifier.padding(horizontal = MaterialTheme.padding.extraLarge),
            text = stringResource(titleRes),
            style = MaterialTheme.typography.titleSmall,
        )
    }

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(
                horizontal = MaterialTheme.padding.medium,
                vertical = MaterialTheme.padding.small,
            ),
        shape = if (LocalEInkMode.current) EInkStyle.cardShape else MaterialTheme.shapes.extraLarge,
        border = if (LocalEInkMode.current) EInkStyle.border(MaterialTheme.colorScheme.outline) else null,
        colors = if (LocalEInkMode.current) CardDefaults.cardColors() else CardDefaults.elevatedCardColors(),
        elevation = if (LocalEInkMode.current) CardDefaults.cardElevation() else CardDefaults.elevatedCardElevation(),
    ) {
        Column(modifier = Modifier.padding(MaterialTheme.padding.medium)) {
            content()
        }
    }
}
