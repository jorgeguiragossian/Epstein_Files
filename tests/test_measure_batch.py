import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('measure_batch', ROOT / 'scripts/measure-batch.py')
measure = importlib.util.module_from_spec(spec)
spec.loader.exec_module(measure)


class MeasureBatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        body = b'%PDF-fixture-source-bytes'
        self.hash = hashlib.sha256(body).hexdigest()
        (self.folder / 'source.pdf').write_bytes(body)
        url = 'https://www.justice.gov/epstein/files/DataSet%208/test.pdf'
        page = dict(page=1, text='Some native text', low_text_candidate=True, date_candidates=[])
        metrics = dict(status='extracted', page_count=1, pages_processed=1, characters=len(page['text']),
                       low_text_pages=1, zero_text_pages=0, email_header_candidate_count=0,
                       document_date=None, date_candidates=[], date_candidate_count=0,
                       page_metrics=[{k: v for k, v in page.items() if k not in ('text', 'date_candidates')}])
        self.save('selection.json', dict(files=[dict(url=url)]))
        self.save('downloads.json', dict(files=[dict(url=url, status='downloaded', local_path='source.pdf', bytes=len(body), sha256=self.hash)]))
        self.save('extraction.json', dict(source_sha256=self.hash, pages=[page], metrics=metrics, email_header_candidates=[]))
        self.save('metrics.json', dict(files=[dict(metrics, url=url, file_id='test', sha256=self.hash, extraction_path='extraction.json')]))

    def save(self, name, value):
        (self.folder / name).write_text(json.dumps(value), encoding='utf-8')

    def tearDown(self):
        self.temp.cleanup()

    def test_verified_summary_and_duplicate_baseline_scope(self):
        self.save('baseline.json', dict(files=[dict(sha256=self.hash)]))
        result = measure.summarize(self.folder, self.folder / 'baseline.json')
        self.assertEqual((result['downloaded_files'], result['extracted_files'], result['pdf_pages']), (1, 1, 1))
        self.assertEqual(result['source_hashes_matching_baseline'], ['test'])
        self.assertFalse(result['ocr_performed'])

    def test_modified_source_or_missing_record_is_rejected(self):
        (self.folder / 'source.pdf').write_bytes(b'changed')
        with self.assertRaises(ValueError):
            measure.summarize(self.folder)
        self.save('downloads.json', dict(files=[]))
        with self.assertRaises(ValueError):
            measure.summarize(self.folder)

    def test_changed_page_evidence_and_injected_reviewed_date_are_rejected(self):
        original = measure.read(self.folder / 'metrics.json')
        for field in ('characters', 'document_date'):
            changed = copy.deepcopy(original)
            changed['files'][0][field] = 999 if field == 'characters' else '2020-01-01'
            self.save('metrics.json', changed)
            with self.subTest(field=field), self.assertRaises(ValueError):
                measure.summarize(self.folder)
