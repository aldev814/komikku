# 验证记录（2026-10-30）

上游正式版：`v1.14.1`；本地测试使用单独的上游源码检出目录，不改动 fork 默认分支。

- 自动应用两个补丁：通过。旧版 FlexibleAdapter 仅在精确匹配旧坐标时回退；AAR 的工作区和 Git 提交字节一致。
- `spotlessApply`、`spotlessCheck`、`assembleDebug`：通过。
- `assembleRelease -Pireader-patch-revision=1`：通过，保留上游 R8 混淆和资源压缩。
- `testReleaseUnitTest`：通过；76 项测试，0 失败、0 错误、1 跳过（包含水波纹测试）。
- 自动发布脚本测试：21 项通过，覆盖去重、草稿恢复、不覆盖已发布文件、补丁冲突、校验和及新版/旧版 apksigner 输出。
- actionlint v1.7.7：通过。
- 五个 Release APK：使用新建固定密钥签署并通过 apksigner 验证；独立包名 `app.komikku.ireader`。
- 公共签名证书 SHA-256：`85fd9a95df28496994fa4ad68eb204cbb6b4945c2a217c23b23adfb4f3699c3f`。
- GitHub 已实际运行过功能分支检查：[运行记录](https://github.com/aldev814/komikku/actions/runs/40907830059)。最终修正会触发新的分支检查。

本地使用 Android Studio 的 JBR 25；GitHub 工作流明确使用 JDK 21。上游现有的 Kotlin 元数据和 R8 警告未阻止构建或测试通过。

固定签名材料仅保存在已忽略的 `.local-signing/` 中，未提交 Git。用户已确认手动配置完成两个仓库 Secrets，功能分支将验证其实际可用性。配方仍在功能分支，尚未合并到默认分支，因此目前没有启用定时发布，也尚未执行真实 GitHub Release 发布。iReader 真机水波纹效果未在本轮测试。
