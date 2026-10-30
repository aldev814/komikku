#!/usr/bin/env python3
"""Make a deterministic patched commit and a source bundle for the release tag."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parent


def git(source, *args, **kwargs):
    return subprocess.check_output(['git', *args], cwd=source, text=True, **kwargs).strip()


def remove_upstream_workflows(source):
    workflows = source / '.github/workflows'
    if workflows.exists():
        shutil.rmtree(workflows)


def package(source, artifacts, plan_file, control=None):
    control = control or ROOT.parents[1]
    plan = json.loads(plan_file.read_text())
    plan['upstream_commit'] = git(source, 'rev-parse', 'HEAD')
    timestamp = git(source, 'log', '-1', '--format=%cI')
    automation_commit = git(control, 'rev-parse', 'HEAD')
    if os.environ.get('GITHUB_SHA') and os.environ['GITHUB_SHA'] != automation_commit:
        raise ValueError('Control checkout does not match the workflow commit')
    remove_upstream_workflows(source)
    identity = {'GIT_AUTHOR_NAME': 'github-actions[bot]', 'GIT_COMMITTER_NAME': 'github-actions[bot]',
                'GIT_AUTHOR_EMAIL': '41898282+github-actions[bot]@users.noreply.github.com',
                'GIT_COMMITTER_EMAIL': '41898282+github-actions[bot]@users.noreply.github.com',
                'GIT_AUTHOR_DATE': timestamp, 'GIT_COMMITTER_DATE': timestamp}
    git(source, 'add', '--all')
    for aar in (source / 'third-party/ireader-legacy').rglob('*.aar'):
        relative = aar.relative_to(source).as_posix()
        staged = subprocess.check_output(['git', 'show', ':' + relative], cwd=source)
        if staged != aar.read_bytes():
            raise ValueError('Git filters changed vendored AAR bytes: ' + relative)
    # Publish only this source tree. An independent root commit keeps all
    # upstream workflow files AND their history out of the release tag.
    tree = git(source, 'write-tree')
    message = (f"Apply iReader p{plan['patch_revision']} to {plan['upstream_tag']}\n\n"
               f"Upstream: {plan['upstream_commit']}\nAutomation: {automation_commit}")
    commit = git(source, 'commit-tree', tree, '-m', message,
                 env={**os.environ, **identity})
    git(source, 'reset', '--soft', commit)
    plan_file.write_text(json.dumps(plan, indent=2) + '\n')
    git(source, 'update-ref', 'refs/heads/ireader-release', 'HEAD')
    artifacts.mkdir(parents=True, exist_ok=True)
    git(source, 'bundle', 'create', str(artifacts / 'patched-source.bundle'), 'refs/heads/ireader-release')
    files = subprocess.check_output(['git', 'ls-files', '-z', '.github/ireader'], cwd=control).decode().split('\0')
    with zipfile.ZipFile(artifacts / 'ireader-patches.zip', 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name in files:
            if name:
                archive.write(control / name, name)
    (artifacts / 'RELEASE_NOTES.md').write_text(f'''基于上游正式版 [{plan['upstream_tag']}]({plan['upstream_url']})，自动应用 iReader 水波纹与墨水屏界面补丁 p{plan['patch_revision']}。

- 水波纹默认关闭；兼容 iReader SmartOS 4+ 的横向分页，支持 RTL、旋转和三档速度。
- 墨水屏模式默认关闭；在「设置 → 外观」启用，支持明暗模式、矩形滑动开关和减少界面动画；保留封面原色与独立翻页设置。
- 包含同源维护版图像解码器，并对正式 APK 执行 64 位原生库 LOAD 段及 ZIP 16KB 对齐检查；实机兼容性仍需设备验证。
- 独立应用包名 `app.komikku.ireader`，可与原版并存；已有书库可使用应用内备份/恢复迁移。
- 使用本 fork 的固定签名，后续本 fork 版本可覆盖升级；不能覆盖原版签名。
- 未启用原版应用内更新和遥测；新版本从本仓库 Releases 下载。
- 不确定 CPU 架构时下载文件名包含 `universal` 的 APK。

源码提交、补丁摘要、签名证书指纹见 `build-metadata.json`；APK 摘要见 `SHA256SUMS`。
完整补丁与旧版依赖的构建来源、许可证随 `ireader-patches.zip` 提供。
''')
    print('Patched source commit:', git(source, 'rev-parse', 'HEAD'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('artifacts', type=Path)
    parser.add_argument('plan_file', type=Path)
    args = parser.parse_args()
    package(args.source.resolve(), args.artifacts.resolve(), args.plan_file.resolve())
