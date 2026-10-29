# iReader 自动补丁与 Release

此 fork 的自动发布配方。上游：`komikku-app/komikku`；发布目标：`aldev814/komikku`。

## 自动流程

`.github/workflows/ireader-release.yml` 每小时第 17 分钟检查上游最新的**已发布正式 Release**，不追踪预览版。也支持 Actions → **iReader - Patch and release upstream stable** → Run workflow；`upstream_tag` 留空取最新版，或填写已发布的正式标签。

每次都从上游 Release 对应的 Git 标签重新检出完整源码，然后依次：

1. 用 `git apply --3way --index` 应用本目录的两个补丁。三方合并允许无冲突的上下文变化；有冲突立即失败。
2. 仅当旧坐标 `com.github.arkon.FlexibleAdapter:flexible-adapter:c8013533` 仍存在时，使用带 SHA-256 校验、源码构建补丁、许可证和来源记录的本地 AAR。`master` 使用的官方依赖不受影响。
3. `spotlessApply` → `spotlessCheck` → 记录带补丁的源码提交 → `assembleRelease` → `testReleaseUnitTest`。
4. 用固定签名生成并验证 universal、arm64-v8a、armeabi-v7a、x86、x86_64 五个 APK。
5. 发布 `ireader-v上游版本-p补丁修订号` 标签和正式 Release，附 APK、SHA256SUMS、源码/签名元数据和补丁配方 ZIP。标签指向**实际打补丁后的源码提交**。

同一个上游版本与补丁修订号已经正式发布时直接跳过；失败不发布，未完成的 draft 可以重跑恢复。发布后不覆盖 APK，不强推标签。更改补丁、依赖回退或构建行为后，将 `config.json` 中 `patch_revision` 加一以发布新修订。

构建任务只有只读仓库权限；只有最后的发布任务有 `contents: write`。不需要 PAT，也不需要上游的 Firebase/Google Secrets。默认分支的并发锁防止定时和手动运行同时发布；功能分支的新提交会取消该分支的旧验证运行。上游原有的 master CI 在此 fork 中跳过，避免索取原项目的 Google 和签名 Secrets。

fork 的默认分支保存配方；每次上游新版的补丁源码保存在其 `ireader-*` 标签中，自动化不会覆盖默认分支，也不需要逐次把上游合并进默认分支。

## 应用身份与升级

独立包名 **`app.komikku.ireader`**，版本名追加 `-ireader.pN`，可以与原版并存。使用应用内备份/恢复迁移书库。本 fork 使用独立签名，后续本 fork 的 APK 使用同一密钥可覆盖升级；不能覆盖原版签名的 APK。

不启用 `-Penable-updater` 或 `-Pinclude-telemetry`，避免更新到原版并消除对原仓库私有构建 Secrets 的依赖。新版本由本 fork 的 Releases 提供，应用内自动更新不在本次范围内。

水波纹开关默认关闭，检测到兼容的 iReader SmartOS 4+ 设备才显示；仅作用于横向分页。新增 UI 文字使用 KMR base 资源。

功能分支推送还会自动运行完整的签名构建并保存 Actions artifacts，供启用前验证 Secrets；此时发布任务被明确跳过，不创建 GitHub Release。正式发布只允许默认分支上的定时或手动运行。

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

补丁文件在 `patches/`；`0001` 来自 Shihon，适配基线 `1656575e8fdaaef010c652f9758130c2a01d8890`；`0002` 设置独立包名和版本后缀。原补丁基于 master，但已验证三方合并可以应用于正式版 `v1.14.1`。

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
./gradlew assembleRelease -Pireader-patch-revision=1
./gradlew testReleaseUnitTest
```

CI 使用 JDK 21、Gradle wrapper 和上游 SDK 配置。补丁冲突时，在工作流日志中查看文件名，修正本 fork 的补丁、增加修订号，再手动重跑。不要绕过补丁应用、格式、测试或签名检查去发布。

## GitHub 平台限制

定时运行可能延迟，不能保证上游发布后的精确一小时内完成；只构建检查时的最新正式版，短时间内连续发布时可能跳过中间版。公共仓库长期没有活动时 GitHub 可能暂停定时工作流，届时在 Actions 中重新启用。

参考：[GitHub Actions schedule](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)。
