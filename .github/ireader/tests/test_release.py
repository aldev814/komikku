import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


release = load('release')
prepare_source = load('prepare_source')
signer = load('sign')
packager = load('package_source')


class ReleasePlanTest(unittest.TestCase):
    def setUp(self):
        self.config = {'upstream': 'komikku-app/komikku', 'fork': 'aldev814/komikku', 'patch_revision': 1}
        self.upstream = {'tag_name': 'v1.14.1', 'draft': False, 'prerelease': False,
                         'published_at': '2026-07-17T00:00:00Z', 'html_url': 'https://github.com/komikku-app/komikku/releases/tag/v1.14.1'}

    def result(self, existing=None, upstream=None, tag=''):
        def get(route):
            if route.startswith('repos/komikku-app/'):
                return upstream or self.upstream
            return existing
        return release.plan(self.config, tag, get)

    def test_new_stable_release_builds_and_uses_namespaced_tag(self):
        result = self.result()
        self.assertEqual(result['needed'], 'true')
        self.assertEqual(result['release_tag'], 'ireader-v1.14.1-p1')

    def test_published_release_is_never_replaced(self):
        self.assertEqual(self.result({'draft': False})['needed'], 'false')

    def test_partial_draft_release_can_resume(self):
        self.assertEqual(self.result({'draft': True})['needed'], 'true')

    def test_patch_revision_allows_rebuilding_same_upstream_version(self):
        self.config['patch_revision'] = 2
        self.assertEqual(self.result()['release_tag'], 'ireader-v1.14.1-p2')

    def test_requested_tag_is_explicitly_queried(self):
        calls = []
        def get(route):
            calls.append(route)
            return self.upstream if len(calls) == 1 else None
        release.plan(self.config, 'v1.14.1', get)
        self.assertEqual(calls[0], 'repos/komikku-app/komikku/releases/tags/v1.14.1')

    def test_unpublished_prerelease_and_draft_are_rejected(self):
        for overrides in [{'prerelease': True}, {'draft': True}, {'published_at': None}]:
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                self.result(upstream={**self.upstream, **overrides})

    def test_missing_upstream_is_an_error(self):
        with self.assertRaises(ValueError):
            release.plan(self.config, get=lambda route: None)

    def test_api_errors_do_not_look_like_new_releases(self):
        with self.assertRaises(PermissionError):
            release.plan(self.config, get=lambda route: (_ for _ in ()).throw(PermissionError('403')))

    def test_unsafe_tags_and_revisions_are_rejected(self):
        for tag in ['../master', 'v1\ninjected=true', 'v1;echo hacked', '--help']:
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                self.result(tag=tag)
        for revision in [0, -1, 10000, '1\nneeded=true']:
            self.config['patch_revision'] = revision
            with self.subTest(revision=revision), self.assertRaises(ValueError):
                self.result()


class LegacyFallbackTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.source = Path(self.temporary.name)
        (self.source / 'gradle').mkdir()
        self.catalog = self.source / 'gradle/libs.versions.toml'
        self.settings = self.source / 'settings.gradle.kts'
        self.settings.write_text('    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)\n    repositories {\n    }\n')

    def test_old_dependency_is_replaced_with_verified_local_binary(self):
        self.catalog.write_text('flexible-adapter-core = "' + prepare_source.OLD_DEPENDENCY + '"\n')
        self.assertTrue(prepare_source.legacy_flexible_adapter(self.source))
        self.assertIn(prepare_source.LOCAL_DEPENDENCY, self.catalog.read_text())
        self.assertIn('exclusiveContent', self.settings.read_text())
        self.assertEqual(len(list((self.source / 'third-party').rglob('*.aar'))), 1)
        self.assertTrue((self.source / 'NOTICE').is_file())

    def test_git_stores_binary_aar_without_newline_conversion(self):
        self.catalog.write_text('adapter = "' + prepare_source.OLD_DEPENDENCY + '"\n')
        (self.source / '.gitattributes').write_text('* text eol=lf\n')
        subprocess.run(['git', 'init', '-q'], cwd=self.source, check=True)
        prepare_source.legacy_flexible_adapter(self.source)
        aar = next((self.source / 'third-party').rglob('*.aar'))
        relative = aar.relative_to(self.source).as_posix()
        subprocess.run(['git', 'add', relative], cwd=self.source, check=True)
        staged = subprocess.check_output(['git', 'show', ':' + relative], cwd=self.source)
        self.assertEqual(staged, aar.read_bytes())

    def test_current_master_dependency_is_untouched(self):
        original = 'flexibleAdapter = { module = "eu.davidea:flexible-adapter", version = "5.1.0" }\n'
        self.catalog.write_text(original)
        self.assertFalse(prepare_source.legacy_flexible_adapter(self.source))
        self.assertEqual(self.catalog.read_text(), original)
        self.assertFalse((self.source / 'third-party').exists())

    def test_no_substring_replacement_for_other_versions(self):
        original = 'adapter = "' + prepare_source.OLD_DEPENDENCY + '-other"\n'
        self.catalog.write_text(original)
        self.assertFalse(prepare_source.legacy_flexible_adapter(self.source))
        self.assertEqual(self.catalog.read_text(), original)

    def test_checksum_mismatch_stops_before_copy(self):
        self.catalog.write_text('adapter = "' + prepare_source.OLD_DEPENDENCY + '"\n')
        real_loads = json.loads
        def loads(value):
            data = real_loads(value)
            if any(str(key).endswith('.aar') for key in data):
                return {key: '0' * 64 for key in data}
            return data
        with patch.object(prepare_source.json, 'loads', side_effect=loads), self.assertRaises(ValueError):
            prepare_source.legacy_flexible_adapter(self.source)
        self.assertFalse((self.source / 'third-party').exists())

    def test_existing_dependency_directory_is_not_overwritten(self):
        self.catalog.write_text('adapter = "' + prepare_source.OLD_DEPENDENCY + '"\n')
        (self.source / 'third-party/ireader-legacy').mkdir(parents=True)
        with self.assertRaises(ValueError):
            prepare_source.legacy_flexible_adapter(self.source)


class WorkflowSnapshotTest(unittest.TestCase):
    def test_snapshot_uses_only_identical_approved_workflows(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, control = root / 'source', root / 'control'
            for directory in [source / '.github/workflows', control / '.github/workflows']:
                directory.mkdir(parents=True)
            (source / '.github/workflows/build.yml').write_text('historical upstream workflow\n')
            (source / '.github/workflows/removed.yml').write_text('obsolete workflow\n')
            (control / '.github/workflows/build.yml').write_text('approved fork workflow\n')
            (control / '.github/workflows/ireader.yml').write_text('approved release workflow\n')
            app = source / 'app.kt'
            app.write_text('patched app remains untouched\n')
            packager.sync_approved_workflows(source, control)
            actual = {p.name: p.read_bytes() for p in (source / '.github/workflows').iterdir()}
            expected = {p.name: p.read_bytes() for p in (control / '.github/workflows').iterdir()}
            self.assertEqual(actual, expected)
            self.assertEqual(app.read_text(), 'patched app remains untouched\n')


class ReleaseSnapshotHistoryTest(unittest.TestCase):
    def test_new_upstream_workflow_history_is_not_pushed_with_release_snapshot(self):
        import os
        environment = {'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_CONFIG_NOSYSTEM': '1',
                       'GIT_AUTHOR_NAME': 'Test', 'GIT_COMMITTER_NAME': 'Test',
                       'GIT_AUTHOR_EMAIL': 'test@example.com', 'GIT_COMMITTER_EMAIL': 'test@example.com'}
        with tempfile.TemporaryDirectory() as temporary, patch.dict(os.environ, environment):
            root = Path(temporary)
            source, control = root / 'source', root / 'control'
            for directory, workflow in [(source, 'new upstream workflow'), (control, 'approved fork workflow')]:
                (directory / '.github/workflows').mkdir(parents=True)
                (directory / '.github/workflows/build.yml').write_text(workflow + '\n')
                (directory / 'app.kt').write_text('upstream app' if directory == source else 'fork app')
                subprocess.run(['git', 'init', '-q'], cwd=directory, check=True)
                subprocess.run(['git', 'add', '.'], cwd=directory, check=True)
                subprocess.run(['git', 'commit', '-q', '-m', workflow], cwd=directory, check=True)
            upstream = packager.git(source, 'rev-parse', 'HEAD')
            approved = packager.git(control, 'rev-parse', 'HEAD')
            (source / 'app.kt').write_text('upstream app plus water ripple')
            plan = root / 'plan.json'
            plan.write_text(json.dumps({'upstream_tag': 'v1.0.0', 'patch_revision': '1',
                                        'upstream_url': 'https://github.com/komikku-app/komikku/releases/tag/v1.0.0'}))
            with patch.dict(os.environ, {'GITHUB_SHA': approved}):
                packager.package(source, root / 'artifacts', plan, control=control)
            self.assertEqual(packager.git(source, 'rev-parse', 'HEAD^'), approved)
            self.assertEqual(len(packager.git(source, 'rev-list', 'HEAD', '^' + approved).splitlines()), 1)
            ancestor = subprocess.run(['git', 'merge-base', '--is-ancestor', upstream, 'HEAD'], cwd=source)
            self.assertEqual(ancestor.returncode, 1)
            self.assertEqual(packager.git(source, 'show', 'HEAD:app.kt'), 'upstream app plus water ripple')
            self.assertEqual(packager.git(source, 'show', 'HEAD:.github/workflows/build.yml'), 'approved fork workflow')
            self.assertEqual(json.loads(plan.read_text())['upstream_commit'], upstream)
            self.assertEqual(json.loads(plan.read_text())['workflow_snapshot_commit'], approved)


class SigningOutputTest(unittest.TestCase):
    def test_legacy_apksigner_certificate_format(self):
        fingerprint = 'a' * 64
        self.assertEqual(signer.signing_certificate('Signer #1 certificate SHA-256 digest: ' + fingerprint), fingerprint)

    def test_new_build_tools_v3_certificate_format(self):
        fingerprint = 'b' * 64
        self.assertEqual(signer.signing_certificate('V3.0 Signer: certificate SHA-256 digest: ' + fingerprint), fingerprint)

    def test_missing_or_multiple_certificates_are_rejected(self):
        for output in ['Verifies', 'Signer #1 certificate SHA-256 digest: ' + 'a' * 64 + '\nSigner #2 certificate SHA-256 digest: ' + 'b' * 64]:
            with self.subTest(output=output), self.assertRaises(ValueError):
                signer.signing_certificate(output)


class PrepareSourceTest(unittest.TestCase):
    def test_dirty_checkout_is_rejected_before_patching(self):
        with patch.object(prepare_source.subprocess, 'check_output', return_value=' M app.kt\n'):
            with patch.object(prepare_source.subprocess, 'run') as run:
                with self.assertRaises(ValueError):
                    prepare_source.prepare(Path('/unused'))
                run.assert_not_called()

    def test_patch_conflict_stops_before_fallback(self):
        with patch.object(prepare_source.subprocess, 'check_output', return_value=''):
            with patch.object(prepare_source.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, 'git apply')):
                with patch.object(prepare_source, 'legacy_flexible_adapter') as fallback:
                    with self.assertRaises(subprocess.CalledProcessError):
                        prepare_source.prepare(Path('/unused'))
                    fallback.assert_not_called()


if __name__ == '__main__':
    unittest.main()
