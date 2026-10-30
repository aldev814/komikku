# iReader 自动补丁与 Release

此 fork 的自动发布配方。上游：`komikku-app/komikku`；发布目标：`aldev814/komikku`。

## 自动流程

`.github/workflows/ireader-release.yml` 每小时第 17 分钟检查上游最新的**已发布正式 Release**，不追踪预览版。也支持 Actions → **iReader - Patch and release upstream stable** → Run workflow；`upstream_tag` 留空取最新版，或填写已发布的正式标签。

每次都从上游 Release 对应的 Git 标签重新检出完整源码，然后依次：

1. 用 `git apply --3way --index` 应用本目录的三个补丁。三方合并允许无冲突的上下文变化；有冲突立即失败。
2. 仅当旧坐标 `com.github.arkon.FlexibleAdapter:flexible-adapter:c8013533` 仍存在时，使用带 SHA-256 校验、源码构建补丁、许可证和来源记录的本地 AAR。`master` 使用的官方依赖不受影响。
3. `spotlessApply` → `spotlessCheck` → 记录带补丁的源码提交 → `assembleRelease` → `testReleaseUnitTest`。只使用上游已发布正式 Release 的标签，不跟随 master 最新 push。发布源码移除 `.github/workflows`，以不带父提交的独立快照记录，不导入上游工作流或 Git 历史；准确的上游提交 SHA 仍保存在元数据中。上游已通过测试，但补丁后的源码仍需重新编译并检查。
4. 用固定签名生成并验证 universal、arm64-v8a、armeabi-v7a、x86、x86_64 五个 APK。
5. 对 universal APK 的全部 64 位原生库执行 LOAD 段和 ZIP 16KB 对齐检查；各架构 APK 在签名后也需通过 zipalign 检查。
6. 发布 `ireader-v上游版本-p补丁修订号` 标签和正式 Release，附 APK、SHA256SUMS、源码/签名元数据、16KB 检查报告和补丁配方 ZIP。标签指向**实际打补丁后的源码提交**。

同一个上游版本与补丁修订号已经正式发布时直接跳过；失败不发布，未完成的 draft 可以重跑恢复。发布后不覆盖 APK，不强推标签。更改补丁、依赖回退或构建行为后，将 `config.json` 中 `patch_revision` 加一以发布新修订。

构建任务只有只读仓库权限；只有最后的发布任务有 `contents: write`。不需要 PAT、workflows 权限或上游的 Firebase/Google Secrets。发布前再次确认源码快照不包含工作流且仅有一个提交。默认分支的并发锁防止定时、手动和配方推送同时发布，不中断正在进行的发布。fork 默认分支只保留 `ireader-release.yml` 和 `ireader-ci.yml` 两个自动化工作流，上游附带的构建、镜像、网站和 PR 工作流已移除。

fork 的默认分支保存配方；每次上游新版的补丁源码保存在其 `ireader-*` 标签中，自动化不会覆盖默认分支，也不需要逐次把上游合并进默认分支。

## 应用身份与升级

独立包名 **`app.komikku.ireader`**，版本名追加 `-ireader.pN`，可以与原版并存。使用应用内备份/恢复迁移书库。本 fork 使用独立签名，后续本 fork 的 APK 使用同一密钥可覆盖升级；不能覆盖原版签名的 APK。

不启用 `-Penable-updater` 或 `-Pinclude-telemetry`，避免更新到原版并消除对原仓库私有构建 Secrets 的依赖。新版本由本 fork 的 Releases 提供，应用内自动更新不在本次范围内。

水波纹开关默认关闭，检测到兼容的 iReader SmartOS 4+ 设备才显示；仅作用于横向分页。

墨水屏模式也默认关闭，入口是「设置 → 外观 → 墨水屏模式」，普通手机也可使用。界面跟随明暗设置，使用黑白高对比配色、矩形滑动开关、描边与减少动画；保留普通按钮、封面原色以及漫画翻页效果的独立设置。新增文案含英文和简体中文。

本配方从 p2 起同时包含水波纹和墨水屏适配。正式包继续使用 `app.komikku.ireader` 与原固定签名，可覆盖升级 p1；本地试用包 `app.komikku.eink.dev` 属于不同应用，需使用备份/恢复迁移。

启用前已在功能分支运行完整签名验证，发布任务被明确跳过。启用后，默认分支的配方更新、定时检查或手动运行都可以发布；非默认分支的手动运行只验证并保存 Actions artifacts，不创建 Release。第一次合并配方到 master 会主动运行，无需等到下一个整点检查。

## 首次启用

1. 将本分支的配方文件合并进 fork 的默认分支 `master`，因为 GitHub 的定时任务只读取默认分支。
2. 如果 fork 的 Actions 被禁用，在仓库 Actions 页面点击启用。
3. 配置下面两个 **Repository secrets**：

   | Secret | 含义 |
   | --- | --- |
   | `IREADER_KEYSTORE_BASE64` | 固定 PKCS12 密钥的 Base64 文本 |
   | `IREADER_KEYSTORE_PASSWORD` | 该密钥的密码（store/key 共用） |

4. 手动运行一次发布工作流，验证当前正式版的完整流程。后续每小时自动检查。

创建或复用本地签名材料：

```sh
python3 .github/ireader/setup_signing.py
# 如果已安装并登录 GitHub CLI，也可直接上传两个 Secrets：
python3 .github/ireader/setup_signing.py --upload
```

此脚本重复运行会复用固定密钥，不会更换签名。文件保存在仓库已忽略的 `.local-signing/`（目录权限 700、文件 600）；私下备份该目录，**不要提交 Git**。其中两个与 Secret 同名的文本文件可直接复制到 GitHub 的 Secrets 输入框，脚本不打印其内容。运行工作流时若未配置这两个 Secrets，会在下载/编译前明确失败。

## 修改与验证

补丁文件在 `patches/`；`0001` 来自 Shihon，适配基线 `1656575e8fdaaef010c652f9758130c2a01d8890`；`0002` 设置独立包名和版本后缀；`0003-eink-ui.patch` 基于 `v1.14.1` 应用前两份补丁后的源码，包含已确认的墨水屏界面、矩形滑动开关和 16KB 图像解码器修复。原补丁基于 master，但已验证三方合并可以应用于正式版 `v1.14.1`。

自动化逻辑测试与工作流检查：

```sh
python3 -m unittest discover -s .github/ireader/tests -v
go run github.com/rhysd/actionlint/cmd/actionlint@v1.7.7 .github/workflows/ireader-ci.yml .github/workflows/ireader-release.yml
```

本地完整验证时，在一个**干净、完整历史**的上游标签检出目录执行：

```sh
python3 /path/to/fork/.github/ireader/prepare_source.py /path/to/upstream-source
cd /path/to/upstream-source
./gradlew spotlessApply
./gradlew spotlessCheck
./gradlew assembleDebug
./gradlew assembleRelease -Pireader-patch-revision=2
./gradlew testReleaseUnitTest
```

CI 使用 JDK 21 和 Gradle wrapper，并安装墨水屏补丁所需的 Android SDK Platform 37.0 与 Build Tools 35.0.0；target SDK 36、min SDK 26 保持不变。当前 AGP 对高于其已测试范围的 compile SDK 会发出警告，未屏蔽该警告。补丁冲突时，在工作流日志中查看文件名，修正本 fork 的补丁、增加修订号，再手动重跑。不要绕过补丁应用、格式、测试或签名检查去发布。

## GitHub 平台限制

定时运行可能延迟，不能保证上游发布后的精确一小时内完成；只构建检查时的最新正式版，短时间内连续发布时可能跳过中间版。公共仓库长期没有活动时 GitHub 可能暂停定时工作流，届时在 Actions 中重新启用。

参考：[GitHub Actions schedule](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)。

## 16KB 验证边界

`check_apk_alignment.py` 仅验证 64 位 ELF LOAD 段和 ZIP 内存储对齐，不代表已在所有 16KB 设备上运行验证，也不能保证厂商安全中心不再显示“未知错误”。检查失败将阻止发布；报告随 Release 提供。它不会添加关闭或隐藏系统兼容性检查的选项。

现有机制是每小时检查最新正式 Release，并非上游发布事件的即时推送；上游变更导致补丁冲突或构建失败时会停止，需修复配方后增加修订号，不能保证任意未来版本无人工干预。
