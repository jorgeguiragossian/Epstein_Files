import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('r2_archive', Path(__file__).resolve().parents[1] / 'scripts/r2-archive.py')
archive = importlib.util.module_from_spec(spec)
spec.loader.exec_module(archive)


class ClientError(Exception):
    def __init__(self, code):
        self.response = {'Error': {'Code': code}}


class FakeClient:
    def __init__(self, payload=None):
        self.payload = payload
        self.uploads = 0

    def head_object(self, **kwargs):
        if self.payload is None:
            raise ClientError('404')

    def put_object(self, **kwargs):
        assert kwargs['IfNoneMatch'] == '*'
        self.payload = kwargs['Body'].read()
        self.uploads += 1

    def get_object(self, **kwargs):
        return {'Body': io.BytesIO(self.payload)}


class ArchiveTests(unittest.TestCase):
    def test_incremental_batch_coverage(self):
        with tempfile.TemporaryDirectory() as td, patch.object(archive,'ROOT',Path(td)):
            root=Path(td);file=root/'data/pilot/new/cache/a.pdf';file.parent.mkdir(parents=True);file.write_bytes(b'a')
            other=root/'data/pilot/old/cache/b.pdf';other.parent.mkdir(parents=True);other.write_bytes(b'b')
            sha=archive.sha_file(file)
            manifest=dict(bucket=archive.BUCKET,batch='new',file_count=1,total_bytes=1,
                files=[dict(local_path='data/pilot/new/cache/a.pdf',bytes=1,sha256=sha,object_key='evidence/sha256/'+sha)])
            archive.validate(manifest)
            (file.parent/'extra').write_bytes(b'extra')
            with self.assertRaises(ValueError):archive.validate(manifest)
            manifest['batch']='../old'
            with self.assertRaises(ValueError):archive.validate(manifest)

    def test_cache_budget(self):
        with tempfile.TemporaryDirectory() as td, patch.object(archive,'ROOT',Path(td)):
            root=Path(td); rows=[dict(local_path='data/pilot/batch/missing',bytes=20)]
            with patch.object(archive,'CACHE_LIMIT',10):
                with self.assertRaises(ValueError):archive.check_cache_budget(root,rows)
            with patch.object(archive.shutil,'disk_usage',return_value=types.SimpleNamespace(free=10)):
                with self.assertRaises(ValueError):archive.check_cache_budget(root,rows)

    def test_pinned_restore_and_overwrite_refusal(self):
        with tempfile.TemporaryDirectory() as td, patch.object(archive,'ROOT',Path(td)):
            root=Path(td); (root/'data/archive').mkdir(parents=True)
            payload=b'restored evidence'; sha=hashlib.sha256(payload).hexdigest()
            relative='data/pilot/batch/extractions/sample.json'
            manifest=root/'data/archive/manifest.json'
            manifest.write_text(json.dumps(dict(bucket=archive.BUCKET,files=[dict(
                local_path=relative,bytes=len(payload),sha256=sha,object_key='evidence/sha256/'+sha)])))
            receipt=root/'data/archive/verification-2026-11-14.json'
            receipt.write_text(json.dumps(dict(manifest_sha256=archive.sha_file(manifest))))
            destination=root/'tmp/restored'
            with patch.object(archive,'make_client',return_value=FakeClient(payload)):
                archive.restore(manifest,destination,'batch')
                self.assertEqual((destination/relative).read_bytes(),payload)
                (destination/relative).write_bytes(b'local edit')
                with self.assertRaises(ValueError):archive.restore(manifest,destination)
                self.assertEqual((destination/relative).read_bytes(),b'local edit')
                with self.assertRaises(ValueError):archive.restore(manifest,root.parent/'outside')
                manifest.write_bytes(b'changed manifest')
                with self.assertRaises(ValueError):archive.restore(manifest,destination)

    def test_restore_and_corruption(self):
        with tempfile.TemporaryDirectory() as td, patch.object(archive, 'ROOT', Path(td)), patch.dict(
            'sys.modules', {'botocore.exceptions': types.SimpleNamespace(ClientError=ClientError)}):
            root = Path(td)
            (root/'tmp/r2-archive').mkdir(parents=True)
            source = root/'data/pilot/batch/cache/source.pdf'
            source.parent.mkdir(parents=True)
            payload = b'%PDF-example-evidence'
            source.write_bytes(payload)
            sha = hashlib.sha256(payload).hexdigest()
            row = dict(local_path='data/pilot/batch/cache/source.pdf', bytes=len(payload),
                       sha256=sha, object_key='evidence/sha256/'+sha)
            client = FakeClient()
            self.assertEqual(archive.verify_object(client, row)['sha256'], sha)
            self.assertEqual(client.uploads, 1)
            archive.verify_object(client, row)
            self.assertEqual(client.uploads, 1)
            for bad in [b'corrupt', payload+b'extra']:
                with self.assertRaises(ValueError):
                    archive.verify_object(FakeClient(bad), row)
            self.assertEqual(source.read_bytes(), payload)
            self.assertEqual(list((root/'tmp/r2-archive').iterdir()), [])

    def test_manifest_paths_coverage_and_changes(self):
        with tempfile.TemporaryDirectory() as td, patch.object(archive, 'ROOT', Path(td)):
            root = Path(td)
            file = root/'data/pilot/batch/sample.json'
            file.parent.mkdir(parents=True)
            file.write_bytes(b'{}')
            sha = archive.sha_file(file)
            row = dict(local_path='data/pilot/batch/sample.json', bytes=2, sha256=sha,
                       object_key='evidence/sha256/'+sha)
            manifest = dict(bucket=archive.BUCKET, file_count=1, total_bytes=2, files=[row])
            archive.validate(manifest)
            for path in ['../outside', 'data/pilot/../../secret', 'scripts/secret']:
                with self.assertRaises(ValueError): archive.source_path(path)
            (file.parent/'new.json').write_bytes(b'new')
            with self.assertRaises(ValueError): archive.validate(manifest)
            (file.parent/'new.json').unlink()
            file.write_bytes(b'changed')
            with self.assertRaises(ValueError): archive.validate(manifest)
