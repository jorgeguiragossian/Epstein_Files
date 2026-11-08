import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
from viewer import batches
from viewer.email_parser import parse_document, group_records


class BatchTests(unittest.TestCase):
    def test_native_mode_preserves_multiple_reviewed_candidates_in_one_document(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root/'data/pilot/test'
            folder.mkdir(parents=True)
            raw = b'%PDF-fixture'
            sha = hashlib.sha256(raw).hexdigest()
            (folder/'source.pdf').write_bytes(raw)
            text = 'From:\nTo:\nSubject: First\nDate: Wed, 14 Aug 2019 16:59:58 +0000\nYes.\nFrom:\nTo:\nSubject: Second\nDate: Wed, 14 Aug 2019 15:59:58 +0000\nEarlier.'
            extraction = dict(source_sha256=sha,pages=[dict(page=1,text=text)])
            metric = dict(file_id='EFTA00000001',dataset=9,url='fixture',sha256=sha,page_count=1,status='extracted',extraction_path='extraction.json')
            def save(name,value):
                (folder/name).write_text(json.dumps(value),encoding='utf-8')
            save('extraction.json',extraction)
            save('metrics.json',dict(files=[metric]))
            save('downloads.json',dict(files=[dict(url='fixture',sha256=sha,status='downloaded',local_path='source.pdf')]))
            save('selection.json',dict(files=[dict(url='fixture')]))
            save('correspondence-reviews.json',dict(reviews=[]))
            records = parse_document(extraction,metric['file_id'],9,sha)
            self.assertEqual(len(records),2)
            records[0]['source_review'] = dict(boundary_status='supported_segment')
            registry = dict(batches=[dict(path='data/pilot/test',documents=1,review_mode='native_correspondence_v1',
                evidence_sha256={'correspondence-reviews.json':hashlib.sha256((folder/'correspondence-reviews.json').read_bytes()).hexdigest()})])
            (root/'data/pilot/viewer-batches.json').write_text(json.dumps(registry))
            helper = SimpleNamespace(build_catalog=lambda path:(dict(records=records),{}))
            with patch.object(batches,'ROOT',root),patch.object(batches,'script',return_value=helper) as dispatch:
                prepared,loaded = batches.load_expansions()
            self.assertEqual(len(prepared),1)
            self.assertEqual(loaded,records)
            dispatch.assert_called_once_with('check-wave-correspondence')

    def test_merge_preserves_old_records_and_counts_reviews_without_enabling_contacts(self):
        def candidate(key):
            text = 'From:\nTo:\nSubject: ' + key + '\nDate: Tue, 16 Jul 2019 19:25:59 +0000\nBody.'
            return parse_document(dict(pages=[dict(page=1, text=text)]), key, 8, key + '-hash')[0]
        old, new = candidate('old'), candidate('new')
        new['source_review'] = dict(boundary_status='supported_segment')
        base = dict(records=[old], groups=group_records([old]), summary=dict(source_review=dict(
            observed_address_associations=0, contact_rankings_ready=False), body_partitions=dict(adjacent_page_checks=0),
            unique_messages=None, contact_rankings_ready=False))
        before = copy.deepcopy(base)
        merged = batches.merge_catalog(base, [new], 2)
        self.assertEqual(base, before)
        self.assertEqual(merged['records'][0], old)
        self.assertEqual(merged['summary']['candidate_occurrences'], 2)
        self.assertEqual(merged['summary']['source_review']['reviewed_candidates'], 1)
        self.assertFalse(merged['summary']['contact_rankings_ready'])
        with self.assertRaises(ValueError):
            batches.merge_catalog(base, [old], 2)

    def test_unregistered_changed_evidence_is_rejected_before_loading_sources(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / 'data/pilot/test'
            folder.mkdir(parents=True)
            (folder / 'metrics.json').write_text('{}')
            (root / 'data/pilot/viewer-batches.json').write_text(json.dumps(dict(batches=[dict(
                path='data/pilot/test', documents=1, evidence_sha256={'metrics.json': 'wrong-hash'})])))
            with patch.object(batches, 'ROOT', root), self.assertRaises(ValueError):
                batches.load_expansions()
