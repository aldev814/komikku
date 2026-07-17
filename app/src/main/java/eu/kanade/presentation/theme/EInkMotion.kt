package eu.kanade.presentation.theme

import android.provider.Settings
import androidx.compose.ui.InternalComposeUiApi
import androidx.compose.ui.MotionDurationScale
import androidx.compose.ui.platform.WindowRecomposerPolicy
import androidx.compose.ui.platform.createLifecycleAwareWindowRecomposer
import eu.kanade.domain.ui.UiPreferences

/** Installs before the first UI window. Does not write Android's global animation settings. */
@OptIn(InternalComposeUiApi::class)
fun installEInkMotionPolicy(preferences: UiPreferences) {
    WindowRecomposerPolicy.setFactory { root ->
        root.createLifecycleAwareWindowRecomposer(
            coroutineContext = EInkMotionDurationScale(
                enabled = { preferences.eInkMode().get() },
                systemScale = {
                    Settings.Global.getFloat(root.context.contentResolver, Settings.Global.ANIMATOR_DURATION_SCALE, 1f)
                },
            ),
        )
    }
}

internal class EInkMotionDurationScale(
    private val enabled: () -> Boolean,
    private val systemScale: () -> Float,
) : MotionDurationScale {
    override val scaleFactor: Float
        get() = if (enabled()) 0f else systemScale()
}
