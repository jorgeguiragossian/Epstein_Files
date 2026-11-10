"""Offline evidence-binding tests; synthetic text only."""
import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('ocr_review',ROOT/'scripts/check-ocr-review.py')
ocr=importlib.util.module_from_spec(spec)
spec.loader.exec_module(ocr)


class OcrReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder=Path(self.temp.name)
        (self.folder/'source.pdf').write_bytes(b'fixture PDF')
        (self.folder/'image.png').write_bytes(b'fixture image')
        self.sha=ocr.digest(self.folder/'source.pdf')
        self.save('downloads.json',dict(files=[dict(file_id='fixture',sha256=self.sha,local_path='source.pdf')]))
        self.save('metrics.json',dict(files=[dict(file_id='fixture',sha256=self.sha,page_count=1,extraction_path='native.json')]))
        self.save('native.json',dict(source_sha256=self.sha,pages=[dict(text='Native fixture')]))
        self.save('ocr.json',dict(image_sha256=ocr.digest(self.folder/'image.png'),engine='Windows.Media.Ocr',language='en-US',lines=[],text='',width=100,height=100))
        reading=dict(id='one',pdf_page=1,kind='literal',status='unresolved',image_path='image.png',region_pixels=[0,0,20,20],literal_reading='Example')
        self.save('layer.json',dict(source_sha256=self.sha,native_extraction_preserved=True,readings=[reading]))
        field={k:v for k,v in reading.items() if k!='literal_reading'}
        field['literal_sha256']=hashlib.sha256(b'Example').hexdigest()
        self.review=dict(file_id='fixture',source_sha256=self.sha,native_extraction_sha256=ocr.digest(self.folder/'native.json'),eligibility=dict(primary_date_assignment=False),
            page_findings=[dict(pdf_page=1,native_text_sha256=hashlib.sha256(b'Native fixture').hexdigest())],
            ocr_attempts=[dict(pdf_page=1,image_path='image.png',image_sha256=ocr.digest(self.folder/'image.png'),result_path='ocr.json',result_sha256=ocr.digest(self.folder/'ocr.json'),recognized_lines=0,recognized_characters=0)],
            transcription_layer=dict(local_path='layer.json',sha256=ocr.digest(self.folder/'layer.json')),reviewed_fields=[field])
        self.save('ocr-transcription-review.json',self.review)

    def save(self,name,value):
        (self.folder/name).write_text(json.dumps(value),encoding='utf-8')

    def test_validates_without_overwriting_native_text(self):
        before=(self.folder/'native.json').read_bytes()
        self.assertTrue(ocr.validate(self.folder)['native_extraction_preserved'])
        self.assertEqual((self.folder/'native.json').read_bytes(),before)

    def test_named_reviews_keep_same_bindings_and_reject_paths_outside_batch(self):
        self.save('second-review.json',self.review)
        self.assertEqual(ocr.validate(self.folder),ocr.validate(self.folder,'second-review.json'))
        with self.assertRaisesRegex(ValueError,'outside batch'):
            ocr.validate(self.folder,'../outside.json')
        self.review['reviewed_fields'][0]['literal_sha256']='changed'
        self.save('second-review.json',self.review)
        with self.assertRaises(ValueError):ocr.validate(self.folder,'second-review.json')

    def test_rejects_stale_review_and_eligibility_promotion(self):
        for field,value in [('source_sha256','changed'),('native_extraction_sha256','changed'),('eligibility',dict(primary_date_assignment=True))]:
            changed=copy.deepcopy(self.review);changed[field]=value
            self.save('ocr-transcription-review.json',changed)
            with self.subTest(field=field),self.assertRaises(ValueError):ocr.validate(self.folder)

    def test_rejects_changed_ocr_bytes(self):
        (self.folder/'image.png').write_bytes(b'changed')
        with self.assertRaises(ValueError):ocr.validate(self.folder)

    def test_rejects_changed_transcription_or_field_binding(self):
        self.review['reviewed_fields'][0]['literal_sha256']='changed'
        self.save('ocr-transcription-review.json',self.review)
        with self.assertRaises(ValueError):ocr.validate(self.folder)
