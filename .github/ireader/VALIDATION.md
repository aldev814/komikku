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

固定签名材料仅保存在已忽略的 `.local-signing/` 中，未提交 Git。两个仓库 Secrets 已由用户手动配置，并在上述云端签名构建中实际使用成功。配方已获用户批准合并到默认分支，定时检测已启用。首次正式运行的构建、测试和签名全部成功，发布标签因上游工作流历史触发 GitHub 默认令牌权限限制而失败；按用户要求，修复改为不含 `.github/workflows`、不带上游 Git 历史的独立源码快照；fork 默认分支移除上游附带的九个工作流，仅保留本任务的两个工作流。修复后的真实发布结果待核验。iReader 真机水波纹效果未在本轮测试。
