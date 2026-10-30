# 验证记录（2026-10-30）

上游正式版：`v1.14.1`；本地测试使用单独的上游源码检出目录，不改动 fork 默认分支。

- 自动应用两个补丁：通过。旧版 FlexibleAdapter 仅在精确匹配旧坐标时回退；AAR 的工作区和 Git 提交字节一致。
- `spotlessApply`、`spotlessCheck`、`assembleDebug`：通过。
- `assembleRelease -Pireader-patch-revision=1`：通过，保留上游 R8 混淆和资源压缩。
- `testReleaseUnitTest`：通过；76 项测试，0 失败、0 错误、1 跳过（包含水波纹测试）。
- 自动发布脚本测试：23 项通过，覆盖去重、草稿恢复、不覆盖已发布文件、补丁冲突、校验和、新版/旧版 apksigner 输出，以及发布源码移除工作流和提交历史隔离。
- actionlint v1.7.7：通过。
- 五个 Release APK：使用新建固定密钥签署并通过 apksigner 验证；独立包名 `app.komikku.ireader`。
- 公共签名证书 SHA-256：`85fd9a95df28496994fa4ad68eb204cbb6b4945c2a217c23b23adfb4f3699c3f`。
- GitHub 完整云端验证：[上游检测、自动补丁、Release 构建、测试、固定密钥签名和产物上传全部通过](https://github.com/aldev814/komikku/actions/runs/40910828124)。本次是功能分支运行，发布步骤按设计跳过。
- 最终启用触发配置的脚本和 actionlint 检查：[通过](https://github.com/aldev814/komikku/actions/runs/40912351214)。

本地使用 Android Studio 的 JBR 25；GitHub 工作流明确使用 JDK 21。上游现有的 Kotlin 元数据和 R8 警告未阻止构建或测试通过。

固定签名材料仅保存在已忽略的 `.local-signing/` 中，未提交 Git。两个仓库 Secrets 已由用户手动配置，并在上述云端签名构建中实际使用成功。配方已获用户批准合并到默认分支，定时检测已启用。首次正式运行的构建、测试和签名全部成功，发布标签因上游工作流历史触发 GitHub 默认令牌权限限制而失败；按用户要求，修复改为不含 `.github/workflows`、不带上游 Git 历史的独立源码快照；fork 默认分支移除上游附带的九个工作流，仅保留本任务的两个工作流。修复后的真实发布已验证成功：

- [正式发布运行](https://github.com/aldev814/komikku/actions/runs/40923729696)：检测、构建、测试、固定签名、产物上传和发布全部成功。
- [Release `ireader-v1.14.1-p1`](https://github.com/aldev814/komikku/releases/tag/ireader-v1.14.1-p1)：公开正式版，共 8 个附件（5 个 APK、SHA256SUMS、build-metadata.json、ireader-patches.zip）。
- 五个 APK 的 GitHub 资产 SHA-256 与发布的 SHA256SUMS 全部一致；证书指纹与本地固定密钥相符。
- Release 标签指向源码提交 `111f5bee68420f8a593f3361c22986d60268057a`，无父提交，且 `.github/workflows` 不存在。
- 元数据上游提交 `e30ff83265d7affcc14e172ea9eadf469db1f4aa`，构建配方提交 `f54042721c13e63f068fb8e84e768eb5a81d2805`。

- 实际 API 去重检查返回 `needed=false`，不会重复构建已发布版本；发布工作流状态 `active`，默认每小时第 17 分钟检查正式 Release。

iReader 真机水波纹效果未在本轮测试。

## 墨水屏补丁 p2

- `0003-eink-ui.patch` 在干净的上游 `v1.14.1` 上接续水波纹和身份补丁重放通过；未包含本地 Debug 测试包身份。
- 自动化测试 31 项通过，新增三份补丁顺序与 16KB 原生库/ZIP 对齐失败阻断测试。
- p2 保留 p1 的正式包名和固定签名；不修改漫画翻页和 iReader 水波纹偏好。
- 云端完整构建与发布结果在执行后补充；真机残影、刷新与系统兼容性提示仍需设备复测。

- [p2 首次云端构建](https://github.com/aldev814/komikku/actions/runs/41068984357)：格式、Release 构建、单元测试及五包签名通过；16KB 门禁准确拦截旧 SQLite 4KB LOAD 段，未发布。补丁随后更新同源 SQLite 3.49.0，并补充失败时的原生检查报告。
- 本地最初构建遇到 DNS 下载失败；独立进程重试后 `spotlessCheck`、`assembleRelease` 与 `testReleaseUnitTest` 通过，81 项测试、0 失败、0 错误、1 跳过。R8 的 Kotlin 编译器诊断类提示未阻止成功；该次尚带旧 SQLite，不能作为修复后最终产物的通过证据。
