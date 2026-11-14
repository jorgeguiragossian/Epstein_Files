"""Inventory and verify a private evidence archive without deleting local sources."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tmp/r2-deps'))
BUCKET = 'epstein-files-archive'
DEFAULT = ROOT / 'data/archive/manifest-2026-11-14.json'
CACHE_LIMIT = 2 * 1024**3
FREE_RESERVE = 1024**3


def check_cache_budget(destination, rows):
    current = sum(p.stat().st_size for p in (destination/'data/pilot').rglob('*') if p.is_file())
    missing = sum(r['bytes'] for r in rows if not (destination/r['local_path']).exists())
    if current + missing > CACHE_LIMIT:
        raise ValueError('Restore would exceed the 2 GiB evidence cache limit')
    if shutil.disk_usage(ROOT).free < missing + FREE_RESERVE:
        raise ValueError('Restore would leave less than 1 GiB free disk space')


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


def make_client():
    import boto3
    from botocore.config import Config
    endpoint = os.environ.get('EPSTEIN_R2_ENDPOINT', '')
    if not re.fullmatch(r'https://[a-f0-9]{32}(?:\.(?:eu|us|fedramp))?\.r2\.cloudflarestorage\.com', endpoint):
        raise ValueError('Invalid R2 endpoint')
    return boto3.client('s3', endpoint_url=endpoint, region_name='auto',
        aws_access_key_id=os.environ['EPSTEIN_R2_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['EPSTEIN_R2_SECRET_ACCESS_KEY'],
        config=Config(signature_version='s3v4', connect_timeout=15, read_timeout=120,
                      retries={'max_attempts': 3}, s3={'addressing_style': 'path'}))


def restore(manifest_path, destination, batch=None):
    """Restore pinned evidence; refuse to replace an existing changed file."""
    trusted = json.loads((ROOT/'data/archive/verification-2026-11-14.json').read_text(encoding='utf-8'))
    if sha_file(manifest_path) != trusted['manifest_sha256']:
        raise ValueError('Manifest differs from verified archive receipt')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest['bucket'] != BUCKET:
        raise ValueError('Wrong archive bucket')
    destination = destination.resolve()
    if destination != ROOT and not destination.is_relative_to((ROOT/'tmp').resolve()):
        raise ValueError('Restore destination must be project root or an isolated tmp workspace')
    if batch and not re.fullmatch(r'[0-9a-z-]+', batch):
        raise ValueError('Invalid batch selector')
    rows = [r for r in manifest['files'] if not batch or PurePosixPath(r['local_path']).parts[2] == batch]
    if not rows:
        raise ValueError('No files match restore selection')
    check_cache_budget(destination,rows)
    client = make_client()
    def one(row):
        rel = PurePosixPath(row['local_path'])
        if rel.is_absolute() or '..' in rel.parts or rel.parts[:2] != ('data','pilot'):
            raise ValueError('Unsafe restore path')
        if not re.fullmatch(r'[a-f0-9]{64}', row['sha256']) or row['object_key'] != 'evidence/sha256/'+row['sha256']:
            raise ValueError('Invalid restore digest/key')
        path = destination.joinpath(*rel.parts).resolve()
        if not path.is_relative_to(destination):
            raise ValueError('Restore path escaped destination')
        if path.exists():
            if path.stat().st_size != row['bytes'] or sha_file(path) != row['sha256']:
                raise ValueError('Existing file differs; refusing overwrite')
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as out:
                tmp_path = Path(out.name)
                total = 0
                h = hashlib.sha256()
                with client.get_object(Bucket=BUCKET,Key=row['object_key'])['Body'] as stream:
                    for block in iter(lambda: stream.read(1024*1024), b''):
                        total += len(block)
                        if total > row['bytes']: raise ValueError('Oversize restore')
                        out.write(block); h.update(block)
            if total != row['bytes'] or h.hexdigest() != row['sha256']:
                raise ValueError('Restore checksum mismatch')
            # Hard-link installation is atomic and fails if a destination appeared.
            os.link(tmp_path, path)
        finally:
            if tmp_path is not None: tmp_path.unlink(missing_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(one,row) for row in rows]
        for n,future in enumerate(as_completed(futures),1):
            future.result()
            if n%40==0 or n==len(rows):print(f'Restored/verified {n}/{len(rows)} files',flush=True)
    for row in rows:
        if sha_file(destination/row['local_path']) != row['sha256']:
            raise ValueError('Post-restore hash changed')
    print(f'PASS: restored selection verified ({len(rows)} files). Existing evidence preserved.',flush=True)


def transfer(manifest, manifest_path):
    validate(manifest)
    folder = ROOT / 'tmp/r2-archive'
    folder.mkdir(parents=True, exist_ok=True)
    client = make_client()
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
    parser.add_argument('command', choices=['inventory', 'upload', 'restore'])
    parser.add_argument('--manifest', type=Path, default=DEFAULT)
    parser.add_argument('--destination',type=Path,default=ROOT)
    parser.add_argument('--batch')
    args = parser.parse_args()
    try:
        if args.command == 'inventory':
            value = inventory()
            args.manifest.parent.mkdir(parents=True, exist_ok=True)
            if args.manifest.exists():
                raise ValueError('Refusing to overwrite existing manifest')
            args.manifest.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
            print(json.dumps({k: v for k, v in value.items() if k != 'files'}, indent=2))
        elif args.command == 'restore':
            restore(args.manifest,args.destination,args.batch)
        else:
            transfer(json.loads(args.manifest.read_text(encoding='utf-8')), args.manifest)
    except Exception as error:
        code = type(error).__name__
        candidate = getattr(error, 'response', {}).get('Error', {}).get('Code', '')
        if re.fullmatch(r'[A-Za-z0-9_]{1,64}', str(candidate)):
            code = str(candidate)
        print('Archive stopped: ' + code + '. No originals removed.', file=sys.stderr)
        if isinstance(error, ValueError) and str(error) in {
            'Manifest differs from verified archive receipt','Wrong archive bucket',
            'Restore destination must be project root or an isolated tmp workspace',
            'Invalid batch selector','No files match restore selection','Unsafe restore path',
            'Invalid restore digest/key','Restore path escaped destination',
            'Existing file differs; refusing overwrite','Oversize restore',
            'Restore checksum mismatch','Post-restore hash changed',
            'Restore would exceed the 2 GiB evidence cache limit',
            'Restore would leave less than 1 GiB free disk space'}:
            print(str(error),file=sys.stderr)
        sys.exit(1)
