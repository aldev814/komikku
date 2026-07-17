package eu.kanade.presentation.theme

import androidx.compose.ui.graphics.Color
import eu.kanade.domain.ui.UiPreferences
import io.kotest.matchers.shouldBe
import io.mockk.every
import io.mockk.mockk
import org.junit.jupiter.api.Test
import tachiyomi.core.common.preference.InMemoryPreferenceStore
import tachiyomi.core.common.preference.InMemoryPreferenceStore.InMemoryPreference
import tachiyomi.core.common.preference.PreferenceStore
import tachiyomi.presentation.core.theme.EInkStyle

class EInkThemeTest {
    @Test
    fun `reader bars are opaque over manga pages in both eink themes`() {
        for (dark in listOf(false, true)) {
            val scheme = EInkStyle.colorScheme(dark)
            val color = EInkStyle.readerBarColor(scheme, true, dark)
            color shouldBe scheme.surface
            color.alpha shouldBe 1f
            (EInkStyle.readerBarColor(scheme, false, dark).alpha < 1f) shouldBe true
        }
    }

    @Test
    fun `new installs keep the original UI by default`() {
        UiPreferences(InMemoryPreferenceStore()).eInkMode().get() shouldBe false
    }

    @Test
    fun `mode survives preference owner recreation without changing saved cover settings`() {
        val store = mockk<PreferenceStore>()
        val booleans = mutableMapOf<String, InMemoryPreference<Boolean>>()
        every { store.getBoolean(any(), any()) } answers {
            booleans.getOrPut(firstArg<String>()) { InMemoryPreference(firstArg<String>(), null, secondArg<Boolean>()) }
        }
        val original = UiPreferences(store)
        original.themeCoverBased().set(true)
        original.eInkMode().set(true)

        val recreated = UiPreferences(store)
        recreated.eInkMode().get() shouldBe true
        recreated.themeCoverBased().get() shouldBe true
        EInkStyle.useCoverColors(recreated.eInkMode().get(), recreated.themeCoverBased().get()) shouldBe false

        recreated.eInkMode().set(false)
        EInkStyle.useCoverColors(recreated.eInkMode().get(), recreated.themeCoverBased().get()) shouldBe true
        recreated.themeCoverBased().set(false)
        EInkStyle.useCoverColors(false, recreated.themeCoverBased().get()) shouldBe false
    }

    @Test
    fun `all surfaces are solid and foregrounds contrast in both modes`() {
        for (dark in listOf(false, true)) {
            val scheme = EInkStyle.colorScheme(dark)
            val background = if (dark) Color.Black else Color.White
            val foreground = if (dark) Color.White else Color.Black
            listOf(
                scheme.background, scheme.surface, scheme.surfaceVariant,
                scheme.surfaceBright, scheme.surfaceDim, scheme.surfaceContainerLowest,
                scheme.surfaceContainerLow, scheme.surfaceContainer, scheme.surfaceContainerHigh,
                scheme.surfaceContainerHighest,
            ).forEach { it shouldBe background }
            listOf(
                scheme.onBackground, scheme.onSurface, scheme.onSurfaceVariant,
                scheme.primary, scheme.secondary, scheme.tertiary, scheme.outline, scheme.outlineVariant,
                scheme.primaryContainer, scheme.secondaryContainer, scheme.tertiaryContainer, scheme.error,
            ).forEach { it shouldBe foreground }
            listOf(scheme.onPrimary, scheme.onSecondary, scheme.onTertiary, scheme.onError).forEach {
                it shouldBe background
            }
            scheme.surfaceTint shouldBe Color.Transparent
        }
    }

    @Test
    fun `motion policy switches live and restores the current system scale`() {
        var enabled = false
        var systemScale = 1.5f
        val scale = EInkMotionDurationScale({ enabled }, { systemScale })
        scale.scaleFactor shouldBe 1.5f
        enabled = true
        scale.scaleFactor shouldBe 0f
        systemScale = 0.5f
        enabled = false
        scale.scaleFactor shouldBe 0.5f
        systemScale = 0f
        scale.scaleFactor shouldBe 0f
    }
}
