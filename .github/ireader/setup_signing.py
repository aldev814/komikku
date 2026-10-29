#!/usr/bin/env python3
"""Create a persistent local signing key; optionally upload through an existing gh login."""
import argparse
import base64
import os
from pathlib import Path
import secrets
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--upload', action='store_true')
    args = parser.parse_args()
    directory = ROOT / '.local-signing'
    directory.mkdir(mode=0o700, exist_ok=True)
    directory.chmod(0o700)
    key, password_file = directory / 'ireader.p12', directory / 'IREADER_KEYSTORE_PASSWORD'
    if key.exists() != password_file.exists():
        raise ValueError('Incomplete existing signing backup; restore it instead of replacing it')
    if not key.exists():
        keytool = shutil.which('keytool')
        if os.environ.get('JAVA_HOME'):
            keytool = str(Path(os.environ['JAVA_HOME']) / 'bin/keytool')
        if not keytool:
            raise ValueError('Install/use JDK 21 first')
        password = secrets.token_urlsafe(48)
        environment = {**os.environ, 'IREADER_KEYSTORE_PASSWORD': password}
        subprocess.run([
            keytool, '-genkeypair', '-keystore', str(key), '-storetype', 'PKCS12',
            '-alias', 'ireader', '-keyalg', 'RSA', '-keysize', '3072', '-validity', '10000',
            '-dname', 'CN=Komikku iReader, OU=aldev814',
            '-storepass:env', 'IREADER_KEYSTORE_PASSWORD', '-keypass:env', 'IREADER_KEYSTORE_PASSWORD',
        ], env=environment, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        key.chmod(0o600)
        password_file.write_text(password)
        password_file.chmod(0o600)
    encoded = directory / 'IREADER_KEYSTORE_BASE64'
    encoded.write_text(base64.b64encode(key.read_bytes()).decode())
    encoded.chmod(0o600)
    if args.upload:
        if not shutil.which('gh'):
            raise ValueError('GitHub CLI is required for upload: install gh and run gh auth login, then retry --upload')
        for name, value in [('IREADER_KEYSTORE_BASE64', encoded.read_text()), ('IREADER_KEYSTORE_PASSWORD', password_file.read_text())]:
            subprocess.run(['gh', 'secret', 'set', name, '--repo', 'aldev814/komikku'], input=value, text=True, check=True)
        print('Both signing secrets uploaded to aldev814/komikku.')
    print('Fixed signing key preserved at:', directory)
    print('Back up this directory privately; reruns reuse the same key. Secret values are not printed.')


if __name__ == '__main__':
    main()
