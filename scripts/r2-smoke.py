"""Upload and restore four bounded evidence samples; never remove originals."""
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
DEPS = ROOT / 'tmp/r2-deps'
sys.path.insert(0, str(DEPS))
BUCKET = 'epstein-files-archive'
ENDPOINT = re.compile(r'https://[a-f0-9]{32}(?:\.(?:eu|us|fedramp))?\.r2\.cloudflarestorage\.com/?')
SAMPLES = [
    'data/pilot/2026-11-09-wave-09/cache/ds04-EFTA00005707.pdf',
    'data/pilot/2026-11-09-wave-09/extractions/ds04-EFTA00005707.json',
    'data/pilot/2026-11-09-wave-09/extractions/ocr-review/EFTA00007501-page-1-crop.png',
    'data/pilot/2026-11-09-wave-09/extractions/ocr-review/EFTA00007501-page-1-crop.json',
]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def plan():
    rows = []
    for relative in SAMPLES:
        path = (ROOT / relative).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():
            raise ValueError('Missing or invalid sample path')
        if path.stat().st_size > 16 * 1024 * 1024:
            raise ValueError('Sample exceeds size limit')
        payload = path.read_bytes()
        sha = digest(payload)
        rows.append(dict(local_path=relative, bytes=len(payload), sha256=sha,
                         object_key=f'archive-smoke/sha256/{sha}/{path.name}'))
    if sum(row['bytes'] for row in rows) > 32 * 1024 * 1024:
        raise ValueError('Sample total exceeds size limit')
    return rows


def run():
    rows = plan()
    if '--plan' in sys.argv:
        print(json.dumps(dict(bucket=BUCKET, files=rows), indent=2))
        return
    endpoint = os.environ.get('EPSTEIN_R2_ENDPOINT', '')
    if not ENDPOINT.fullmatch(endpoint):
        raise ValueError('Use the exact HTTPS R2 S3 account endpoint')
    import boto3
    from botocore.config import Config
    from botocore.exceptions import ClientError
    client = boto3.client('s3', endpoint_url=endpoint.rstrip('/'), region_name='auto',
        aws_access_key_id=os.environ['EPSTEIN_R2_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['EPSTEIN_R2_SECRET_ACCESS_KEY'],
        config=Config(signature_version='s3v4', connect_timeout=15, read_timeout=60,
                      retries={'max_attempts': 2}, s3={'addressing_style': 'path'}))
    output = ROOT / 'tmp/r2-smoke' / uuid.uuid4().hex
    output.mkdir(parents=True)
    for i, row in enumerate(rows):
        payload = (ROOT / row['local_path']).read_bytes()
        if digest(payload) != row['sha256']:
            raise ValueError('Sample changed after planning')
        try:
            client.put_object(Bucket=BUCKET, Key=row['object_key'], Body=payload,
                              IfNoneMatch='*', Metadata={'sha256': row['sha256']})
        except ClientError as error:
            if str(error.response['Error']['Code']) not in ('PreconditionFailed', '412'):
                raise
        response = client.get_object(Bucket=BUCKET, Key=row['object_key'])
        with response['Body'] as stream:
            restored = stream.read(row['bytes'] + 1)
        if len(restored) != row['bytes'] or digest(restored) != row['sha256']:
            raise ValueError('Restored bytes do not match local source')
        if digest((ROOT / row['local_path']).read_bytes()) != row['sha256']:
            raise ValueError('Original source changed during verification')
        (output / f'{i}-{Path(row["local_path"]).name}').write_bytes(restored)
        row['restored_sha256'] = digest(restored)
        print(f'Verified sample {i + 1}/{len(rows)}', flush=True)
    receipt = dict(bucket=BUCKET, status='four_sample_restore_verified',
                   originals_preserved=True, files=rows,
                   scope='Four samples only; full archive backup is not yet complete.')
    (output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print('PASS: all four restored samples match SHA-256. Originals remain in place.')
    print('Receipt: ' + str(output / 'receipt.json'))


if __name__ == '__main__':
    try:
        run()
    except Exception as error:
        # Do not log exception text, HTTP headers or credentials.
        print('Test stopped: ' + type(error).__name__ + '. No originals removed.', file=sys.stderr)
        sys.exit(1)
