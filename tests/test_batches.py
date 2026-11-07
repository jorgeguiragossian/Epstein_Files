import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from viewer import batches
from viewer.email_parser import parse_document, group_records


class BatchTests(unittest.TestCase):
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
