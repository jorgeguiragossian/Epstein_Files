"""Offline checks for stale review evidence and preservation of native candidates."""
import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('wave_correspondence',ROOT/'scripts/check-wave-correspondence.py')
wave = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wave)


class WaveCorrespondenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        pdf = b'%PDF-fixture-for-source-hash'
        self.sha = hashlib.sha256(pdf).hexdigest()
        (self.folder/'source.pdf').write_bytes(pdf)
        self.text = 'From: Alice Example\nTo: Bob Example\nSubject: Meeting\nDate: Wed, 14 Aug 2019 16:59:58 +0000\nYes.\n'
        extraction = dict(source_sha256=self.sha,pages=[dict(page=1,text=self.text)])
        metric = dict(file_id='EFTA00000001',dataset=9,url='fixture',sha256=self.sha,page_count=1,extraction_path='extraction.json')
        self.save('metrics.json',dict(files=[metric]))
        self.save('downloads.json',dict(files=[dict(url='fixture',sha256=self.sha,local_path='source.pdf')]))
        self.save('extraction.json',extraction)
        self.native = wave.parse_document(extraction,metric['file_id'],9,self.sha)[0]
        review = {key:self.native[key] for key in ('file_id','source_sha256','source_page','source_line','visible_fingerprint')}
        review.update(record_id=self.native['id'],unique_message_verified=False,contact_count_eligible=False,
                      page_evidence=[dict(pdf_page=1,native_text_sha256=hashlib.sha256(self.text.encode()).hexdigest())],spans=[])
        self.metadata = dict(parser_version=wave.VERSION,date_parser_version=wave.DATE_VERSION,reviews=[review])
        self.save('correspondence-reviews.json',self.metadata)

    def save(self,name,value):
        (self.folder/name).write_text(json.dumps(value),encoding='utf-8')

    def test_preserves_native_candidate_fields(self):
        catalog,summary = wave.build_catalog(self.folder)
        reviewed = dict(catalog['records'][0])
        reviewed.pop('source_review')
        self.assertEqual(reviewed,self.native)
        self.assertEqual(summary['reviewed_candidates'],1)
        self.assertFalse(summary['contact_rankings_ready'])

    def test_rejects_changed_evidence_and_contact_promotion(self):
        for changes in ({'visible_fingerprint':'changed'},{'source_sha256':'changed'},
                        {'unique_message_verified':True},{'contact_count_eligible':True},
                        {'page_evidence':[dict(pdf_page=1,native_text_sha256='changed')]},
                        {'page_evidence':[]}):
            metadata = copy.deepcopy(self.metadata)
            metadata['reviews'][0].update(changes)
            self.save('correspondence-reviews.json',metadata)
            with self.subTest(changes=changes),self.assertRaises(ValueError):
                wave.build_catalog(self.folder)

    def test_rejects_changed_source_bytes(self):
        (self.folder/'source.pdf').write_bytes(b'changed')
        with self.assertRaises(ValueError):
            wave.build_catalog(self.folder)
