import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from viewer.batches import load_ocr_assessments


class IndexedOcrTests(unittest.TestCase):
    def test_pinned_named_reviews_expose_only_scope_not_literals(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)
            review=dict(file_id='doc',ocr_improvement_accepted=False,
                        page_findings=[dict(pdf_page=1,finding='OCR incomplete')],
                        reviewed_fields=[dict(literal_sha256='private metadata')])
            def write_review():
                (folder/'review.json').write_text(json.dumps(review))
                sha=hashlib.sha256((folder/'review.json').read_bytes()).hexdigest()
                index=dict(reviews=[dict(file_id='doc',review_file='review.json',review_sha256=sha)])
                (folder/'ocr-review-index.json').write_text(json.dumps(index))
                return {'ocr-review-index.json':'pinned upstream','review.json':sha}
            pinned=write_review()
            with patch('viewer.batches.script',return_value=SimpleNamespace(validate=lambda folder,name:{})):
                result=load_ocr_assessments(folder,pinned)
            self.assertEqual(result,{'doc':dict(notes=['OCR incomplete'],inspected_pdf_pages=[1],native_replacement_accepted=False)})
            with self.assertRaises(ValueError):load_ocr_assessments(folder,{'ocr-review-index.json':'pin'})
            (folder/'review.json').write_text('changed')
            with self.assertRaises(ValueError):load_ocr_assessments(folder,pinned)
            review['ocr_improvement_accepted']=True
            pinned=write_review()
            with self.assertRaisesRegex(ValueError,'replacement promotion'):load_ocr_assessments(folder,pinned)

    def test_rejects_duplicate_and_outside_index_entries(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)
            (folder/'ocr-review-index.json').write_text(json.dumps(dict(reviews=[dict(file_id='doc',review_file='../outside.json',review_sha256='x')])))
            with self.assertRaisesRegex(ValueError,'Invalid or duplicate'):
                load_ocr_assessments(folder,{'ocr-review-index.json':'pin'})
