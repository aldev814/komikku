#!/usr/bin/env python3
"""Apply maintained patches and the narrowly scoped legacy dependency fallback."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent
OLD_DEPENDENCY = 'com.github.arkon.FlexibleAdapter:flexible-adapter:c8013533'
LOCAL_DEPENDENCY = OLD_DEPENDENCY + '-local-properties1.0.3'


def legacy_flexible_adapter(source):
    catalog = source / 'gradle/libs.versions.toml'
    content = catalog.read_text()
    if OLD_DEPENDENCY + '"' not in content:
        return False
    legacy = ROOT / 'legacy'
    provenance = json.loads((legacy / 'flexible-adapter/provenance.json').read_text())
    # Verify the exact vendored binary before using it; also ship its build patch and license.
    aars = list((legacy / 'maven').rglob('*.aar'))
    if len(aars) != 1:
        raise ValueError('Expected exactly one vendored AAR')
    expected = json.loads((ROOT / 'legacy-checksums.json').read_text())
    for relative, checksum in expected.items():
        if hashlib.sha256((legacy / relative).read_bytes()).hexdigest() != checksum:
            raise ValueError('Vendored dependency checksum mismatch: ' + relative)
    if not provenance:
        raise ValueError('Missing dependency provenance')
    target = source / 'third-party/ireader-legacy'
    if target.exists():
        raise ValueError('Refusing to overwrite existing third-party/ireader-legacy')
    shutil.copytree(legacy, target)
    attributes = source / '.gitattributes'
    with attributes.open('a') as output:
        output.write('\n# Preserve vendored iReader dependency bytes.\n'
                     '/third-party/ireader-legacy/**/*.aar binary\n'
                     '/third-party/ireader-legacy/**/*.patch -whitespace\n'
                     '/third-party/ireader-legacy/flexible-adapter/LICENSE -whitespace\n')
    catalog.write_text(content.replace(OLD_DEPENDENCY + '"', LOCAL_DEPENDENCY + '"'))
    settings = source / 'settings.gradle.kts'
    text = settings.read_text()
    anchor = '    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)\n    repositories {\n'
    if text.count(anchor) != 1:
        raise ValueError('Repository configuration changed; update the legacy fallback manually')
    text = text.replace(anchor, anchor + '''        exclusiveContent {
            forRepository {
                maven { url = uri(rootDir.resolve("third-party/ireader-legacy/maven")) }
            }
            filter { includeModule("com.github.arkon.FlexibleAdapter", "flexible-adapter") }
        }
''')
    settings.write_text(text)
    notice = source / 'NOTICE'
    with notice.open('a') as output:
        output.write('\nThis iReader build includes arkon/FlexibleAdapter c8013533 rebuilt with '
                     'java-ordered-properties 1.0.3. License and provenance: '
                     'third-party/ireader-legacy/flexible-adapter/.\n')
    return True


def prepare(source):
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=source, text=True).strip():
        raise ValueError('Source checkout must be clean')
    for patch in sorted((ROOT / 'patches').glob('*.patch')):
        subprocess.run(['git', 'apply', '--3way', '--index', str(patch)], cwd=source, check=True)
    legacy = legacy_flexible_adapter(source)
    subprocess.run(['git', 'diff', '--check'], cwd=source, check=True)
    subprocess.run(['git', 'diff', '--cached', '--check'], cwd=source, check=True)
    print('Water-ripple and fork identity applied; legacy FlexibleAdapter fallback:', legacy)
    return legacy


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    prepare(parser.parse_args().source.resolve())
