"""Exercise tag publication and draft recovery against a local bare repo and fake gh."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PublishRecoveryTest(unittest.TestCase):
    def test_failed_upload_resumes_without_retagging_and_published_assets_are_immutable(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, control, artifacts, tools = [root / name for name in ['source', 'control', 'artifacts', 'tools']]
            for directory in [source, control, artifacts, tools]:
                directory.mkdir()
            environment = {**os.environ, 'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_CONFIG_NOSYSTEM': '1',
                           'GIT_AUTHOR_NAME': 'Test', 'GIT_COMMITTER_NAME': 'Test',
                           'GIT_AUTHOR_EMAIL': 'test@example.com', 'GIT_COMMITTER_EMAIL': 'test@example.com',
                           'GITHUB_WORKSPACE': str(root), 'RUNNER_TEMP': str(root),
                           'RELEASE_TAG': 'ireader-v1.0.0-p1', 'GH_REPO': 'aldev814/komikku',
                           'PATH': str(tools) + os.pathsep + os.environ['PATH'], 'FAKE_GH_ROOT': str(root)}

            def git(directory, *args):
                return subprocess.check_output(['git', *args], cwd=directory, env=environment, stderr=subprocess.DEVNULL, text=True).strip()

            git(root, 'init', '--bare', str(root / 'remote.git'))
            git(source, 'init')
            (source / 'source.txt').write_text('patched source\n')
            git(source, 'add', '.')
            git(source, 'commit', '-m', 'patched')
            commit = git(source, 'rev-parse', 'HEAD')
            git(source, 'update-ref', 'refs/heads/ireader-release', commit)
            git(source, 'bundle', 'create', str(artifacts / 'patched-source.bundle'), 'refs/heads/ireader-release')
            git(control, 'init')
            git(control, 'remote', 'add', 'origin', str(root / 'remote.git'))
            (artifacts / 'build-metadata.json').write_text(json.dumps({'source_commit': commit}))
            for name in ['fixture.apk', 'SHA256SUMS', 'RELEASE_NOTES.md', 'ireader-patches.zip']:
                (artifacts / name).write_text('fixture\n')
            fake = tools / 'gh'
            fake.write_text('''#!/usr/bin/env python3
import json,os,sys
from pathlib import Path
root=Path(os.environ['FAKE_GH_ROOT']); state=root/'state.json'; calls=root/'calls.txt'
command=sys.argv[2]
with calls.open('a') as out: out.write(command+'\\n')
if command=='view':
    if not state.exists(): sys.exit(1)
    print(state.read_text())
elif command=='create': state.write_text(json.dumps({'isDraft':True}))
elif command=='upload':
    if (root/'fail-upload').exists(): sys.exit(1)
elif command=='edit': state.write_text(json.dumps({'isDraft':False}))
else: sys.exit(2)
''')
            fake.chmod(0o700)
            failure = root / 'fail-upload'
            failure.touch()

            def publish():
                return subprocess.run(['bash', str(ROOT / 'publish.sh')], cwd=control, env=environment,
                                      text=True, capture_output=True)

            first = publish()
            self.assertNotEqual(first.returncode, 0)
            self.assertTrue(json.loads((root / 'state.json').read_text())['isDraft'])
            remote_tag = git(root, '--git-dir=' + str(root / 'remote.git'), 'rev-parse', 'refs/tags/ireader-v1.0.0-p1^{commit}')
            self.assertEqual(remote_tag, commit)
            failure.unlink()
            second = publish()
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertFalse(json.loads((root / 'state.json').read_text())['isDraft'])
            calls_before = (root / 'calls.txt').read_text().count('upload\n')
            third = publish()
            self.assertEqual(third.returncode, 0, third.stderr)
            self.assertEqual((root / 'calls.txt').read_text().count('upload\n'), calls_before)
            self.assertEqual(git(root, '--git-dir=' + str(root / 'remote.git'), 'rev-parse', 'refs/tags/ireader-v1.0.0-p1^{commit}'), commit)
