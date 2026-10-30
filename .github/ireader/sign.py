#!/usr/bin/env python3
"""Sign every release APK using one fixed, secret-backed PKCS12 key."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile


def signing_certificate(verification):
    fingerprints = set(re.findall(
        r'^(?:Signer #\d+|V[\d.]+ Signer):? certificate SHA-256 digest: ([0-9a-fA-F]{64})$',
        verification, re.MULTILINE,
    ))
    if len(fingerprints) != 1:
        raise ValueError('Expected exactly one signing certificate')
    return fingerprints.pop().lower()


def sign(source, output, release_tag, plan_file):
    if not re.fullmatch(r'ireader-v[0-9][A-Za-z0-9._+-]*-p[0-9]+', release_tag):
        raise ValueError('Invalid release tag')
    sdk = Path(os.environ.get('ANDROID_HOME') or os.environ['ANDROID_SDK_ROOT'])
    tools = [p for p in (sdk / 'build-tools').iterdir() if (p / 'apksigner').is_file() and re.fullmatch(r'\d+(\.\d+)+', p.name)]
    tool = max(tools, key=lambda p: tuple(map(int, p.name.split('.'))))
    apksigner, zipalign = tool / 'apksigner', tool / 'zipalign'
    apks = sorted((source / 'app/build/outputs/apk/release').glob('app-*-release-unsigned.apk'))
    if len(apks) != 5:
        raise ValueError(f'Expected five unsigned release APKs, found {len(apks)}')
    output.mkdir(parents=True, exist_ok=True)
    metadata = json.loads(plan_file.read_text())
    metadata['source_commit'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip()
    metadata['automation_commit'] = os.environ.get('GITHUB_SHA', '')
    metadata['application_id'] = 'app.komikku.ireader'
    certificates = set()
    with tempfile.TemporaryDirectory() as temporary:
        key = Path(temporary) / 'release.p12'
        key.write_bytes(base64.b64decode(os.environ['IREADER_KEYSTORE_BASE64'], validate=True))
        key.chmod(0o600)
        for apk in apks:
            abi = apk.name.removeprefix('app-').removesuffix('-release-unsigned.apk')
            badging = subprocess.check_output([str(tool / 'aapt'), 'dump', 'badging', str(apk)], text=True)
            if not re.search(r"package: name='app\.komikku\.ireader'", badging):
                raise ValueError('Unexpected APK application ID')
            aligned = Path(temporary) / apk.name
            destination = output / f'Komikku-{release_tag}-{abi}.apk'
            subprocess.run([str(zipalign), '-P', '16', '-f', '4', str(apk), str(aligned)], check=True)
            subprocess.run([
                str(apksigner), 'sign', '--ks', str(key), '--ks-key-alias', 'ireader',
                '--ks-pass', 'env:IREADER_KEYSTORE_PASSWORD', '--key-pass', 'env:IREADER_KEYSTORE_PASSWORD',
                '--out', str(destination), str(aligned),
            ], check=True)
            verification = subprocess.check_output([str(apksigner), 'verify', '--verbose', '--print-certs', str(destination)], text=True)
            certificates.add(signing_certificate(verification))
            subprocess.run([str(zipalign), '-c', '-P', '16', '4', str(destination)], check=True)
    if len(certificates) != 1:
        raise ValueError('APK signing certificates differ')
    metadata['signing_certificate_sha256'] = certificates.pop()
    (output / 'build-metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    with (output / 'SHA256SUMS').open('w') as checksums:
        for apk in sorted(output.glob('*.apk')):
            checksums.write(hashlib.sha256(apk.read_bytes()).hexdigest() + '  ' + apk.name + '\n')
    print('Signed and verified all five APKs; certificate SHA-256:', metadata['signing_certificate_sha256'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('release_tag')
    parser.add_argument('plan_file', type=Path)
    args = parser.parse_args()
    sign(args.source.resolve(), args.output.resolve(), args.release_tag, args.plan_file)
