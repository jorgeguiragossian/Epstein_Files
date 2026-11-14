"""Inventory and verify a private evidence archive without deleting local sources."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tmp/r2-deps'))
BUCKET = 'epstein-files-archive'
DEFAULT = ROOT / 'data/archive/manifest-2026-11-14.json'


def sha_file(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def source_path(relative):
    p = PurePosixPath(relative)
    if p.is_absolute() or '..' in p.parts or p.parts[:2] != ('data', 'pilot'):
        raise ValueError('Invalid archive source path')
    result = (ROOT / relative).resolve()
    if not result.is_relative_to((ROOT / 'data/pilot').resolve()):
        raise ValueError('Archive source escaped evidence directory')
    if result.is_symlink() or not result.is_file():
        raise ValueError('Missing archive evidence')
    return result


def inventory():
    files = []
    for path in sorted((ROOT / 'data/pilot').rglob('*')):
        if path.is_symlink():
            raise ValueError('Symlinks require explicit review')
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT).as_posix()
        path = source_path(relative)
        if path.stat().st_size > 256 * 1024 * 1024:
            raise ValueError('File exceeds bounded archive limit')
        sha = sha_file(path)
        files.append(dict(local_path=relative, bytes=path.stat().st_size,
                          sha256=sha, object_key='evidence/sha256/' + sha))
    total = sum(f['bytes'] for f in files)
    if not files or total > 2 * 1024**3:
        raise ValueError('Inventory exceeds bounded migration scope')
    return dict(schema_version=1, bucket=BUCKET, source_revision=subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        scope='Every current file under data/pilot, including PDFs, native/OCR evidence and metadata. '
              'Excludes Downloads, temporary QA sheets, software dependencies, credentials and Git internals.',
        files=files, file_count=len(files), total_bytes=total)


def validate(manifest):
    if manifest['bucket'] != BUCKET or manifest['file_count'] != len(manifest['files']):
        raise ValueError('Invalid archive manifest')
    paths = set()
    for row in manifest['files']:
        path = source_path(row['local_path'])
        if row['local_path'] in paths or not re.fullmatch('[0-9a-f]{64}', row['sha256']):
            raise ValueError('Duplicate path or invalid digest')
        paths.add(row['local_path'])
        if row['object_key'] != 'evidence/sha256/' + row['sha256']:
            raise ValueError('Invalid content-addressed object key')
        if path.stat().st_size != row['bytes'] or sha_file(path) != row['sha256']:
            raise ValueError('Local evidence changed since inventory')
    actual = {p.relative_to(ROOT).as_posix() for p in (ROOT / 'data/pilot').rglob('*') if p.is_file()}
    if paths != actual or sum(f['bytes'] for f in manifest['files']) != manifest['total_bytes']:
        raise ValueError('Archive coverage changed')


def verify_object(client, row):
    from botocore.exceptions import ClientError
    path = source_path(row['local_path'])
    try:
        client.head_object(Bucket=BUCKET, Key=row['object_key'])
    except ClientError as error:
        if str(error.response['Error']['Code']) not in ('404', 'NoSuchKey', 'NotFound'):
            raise
        with path.open('rb') as stream:
            try:
                client.put_object(Bucket=BUCKET, Key=row['object_key'], Body=stream,
                                  IfNoneMatch='*', Metadata={'sha256': row['sha256']})
            except ClientError as put_error:
                if str(put_error.response['Error']['Code']) not in ('412', 'PreconditionFailed'):
                    raise
    response = client.get_object(Bucket=BUCKET, Key=row['object_key'])
    count = 0
    # Restore one object to temporary disk and hash that restored file, then
    # release only this disposable copy. Original evidence is never removed.
    with tempfile.TemporaryFile(dir=ROOT / 'tmp/r2-archive') as restored:
        with response['Body'] as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                count += len(block)
                if count > row['bytes']:
                    raise ValueError('Remote object exceeds expected size')
                restored.write(block)
        restored.seek(0)
        h = hashlib.sha256()
        for block in iter(lambda: restored.read(1024 * 1024), b''):
            h.update(block)
    if count != row['bytes'] or h.hexdigest() != row['sha256']:
        raise ValueError('Restored archive checksum mismatch')
    return dict(object_key=row['object_key'], bytes=count, sha256=h.hexdigest())


def transfer(manifest, manifest_path):
    import boto3
    from botocore.config import Config
    endpoint = os.environ.get('EPSTEIN_R2_ENDPOINT', '')
    if not re.fullmatch(r'https://[a-f0-9]{32}(?:\.(?:eu|us|fedramp))?\.r2\.cloudflarestorage\.com', endpoint):
        raise ValueError('Invalid R2 endpoint')
    validate(manifest)
    folder = ROOT / 'tmp/r2-archive'
    folder.mkdir(parents=True, exist_ok=True)
    client = boto3.client('s3', endpoint_url=endpoint, region_name='auto',
        aws_access_key_id=os.environ['EPSTEIN_R2_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['EPSTEIN_R2_SECRET_ACCESS_KEY'],
        config=Config(signature_version='s3v4', connect_timeout=15, read_timeout=120,
                      retries={'max_attempts': 3}, s3={'addressing_style': 'path'}))
    unique = {f['object_key']: f for f in manifest['files']}
    verified = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(verify_object, client, row) for row in unique.values()]
        for future in as_completed(futures):
            verified.append(future.result())
            if len(verified) % 20 == 0 or len(verified) == len(unique):
                print(f'Uploaded/restored/verified {len(verified)}/{len(unique)} objects', flush=True)
    validate(manifest)
    payload = manifest_path.read_bytes()
    manifest_sha = hashlib.sha256(payload).hexdigest()
    key = 'manifests/sha256/' + manifest_sha + '.json'
    from botocore.exceptions import ClientError
    try:
        client.put_object(Bucket=BUCKET, Key=key, Body=payload, IfNoneMatch='*')
    except ClientError as error:
        if str(error.response['Error']['Code']) not in ('412', 'PreconditionFailed'):
            raise
    with client.get_object(Bucket=BUCKET, Key=key)['Body'] as stream:
        remote = stream.read(len(payload) + 1)
    if remote != payload:
        raise ValueError('Remote manifest mismatch')
    receipt = dict(schema_version=1, bucket=BUCKET, status='complete_inventory_restore_verified',
        completed_at_utc=datetime.now(timezone.utc).isoformat(), manifest_sha256=manifest_sha,
        remote_manifest_key=key, files=manifest['file_count'], bytes=manifest['total_bytes'],
        unique_objects=len(unique), originals_preserved=True,
        verification='Every unique evidence object restored to temporary disk and SHA-256 checked; '
                     'complete local inventory revalidated after transfer; remote manifest checked byte-for-byte.',
        objects=sorted(verified, key=lambda x: x['object_key']))
    target = folder / ('receipt-' + manifest_sha + '.json')
    target.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print('PASS: complete inventory restored and verified. All originals preserved.', flush=True)
    print('Receipt: ' + str(target), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['inventory', 'upload'])
    parser.add_argument('--manifest', type=Path, default=DEFAULT)
    args = parser.parse_args()
    try:
        if args.command == 'inventory':
            value = inventory()
            args.manifest.parent.mkdir(parents=True, exist_ok=True)
            if args.manifest.exists():
                raise ValueError('Refusing to overwrite existing manifest')
            args.manifest.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
            print(json.dumps({k: v for k, v in value.items() if k != 'files'}, indent=2))
        else:
            transfer(json.loads(args.manifest.read_text(encoding='utf-8')), args.manifest)
    except Exception as error:
        code = type(error).__name__
        candidate = getattr(error, 'response', {}).get('Error', {}).get('Code', '')
        if re.fullmatch(r'[A-Za-z0-9_]{1,64}', str(candidate)):
            code = str(candidate)
        print('Archive stopped: ' + code + '. No originals removed.', file=sys.stderr)
        sys.exit(1)
