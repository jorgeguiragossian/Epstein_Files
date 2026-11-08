"""Synthetic layout/date-role evidence checks; no financial source text."""
import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('table_review',ROOT/'scripts/check-table-date-review.py')
checker=importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class TableDateReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder=Path(self.temp.name)
        (self.folder/'source.pdf').write_bytes(b'fixture PDF')
        sha=hashlib.sha256(b'fixture PDF').hexdigest()
        text='Statement period: January 1 to January 31, 2020\nDate Description Amount'
        self.save('downloads.json',dict(files=[dict(file_id='fixture',sha256=sha,local_path='source.pdf')]))
        self.save('metrics.json',dict(files=[dict(file_id='fixture',sha256=sha,page_count=1,extraction_path='native.json')]))
        self.save('native.json',dict(source_sha256=sha,pages=[dict(text=text)]))
        self.review=dict(reviews=[dict(file_id='fixture',source_sha256=sha,
            page_evidence=[dict(pdf_page=1,native_text_sha256=hashlib.sha256(text.encode()).hexdigest())],
            eligibility=dict(structured_ledger=False,primary_date_assignment=False),
            date_observations=[dict(role='statement_reporting_period',pdf_page=1,native_quote='January 1 to January 31, 2020',period_start='2020-01-01',period_end='2020-01-31')],
            layout_evidence=[dict(pdf_page=1,native_quote='Date Description Amount')])])
        self.save('table-date-role-reviews.json',self.review)

    def save(self,name,value):
        (self.folder/name).write_text(json.dumps(value),encoding='utf-8')

    def test_preserves_native_text_and_separates_roles_from_primary_dates(self):
        before=(self.folder/'native.json').read_bytes()
        result=checker.validate(self.folder)
        self.assertEqual(result['date_role_observations'],1)
        self.assertFalse(result['primary_dates_assigned'])
        self.assertFalse(result['structured_financial_data_verified'])
        self.assertEqual((self.folder/'native.json').read_bytes(),before)

    def test_rejects_changed_source_bytes(self):
        (self.folder/'source.pdf').write_bytes(b'changed')
        with self.assertRaises(ValueError):checker.validate(self.folder)

    def test_rejects_missing_page_and_ledger_promotion(self):
        for changes in ({'page_evidence':[]},{'eligibility':dict(structured_ledger=True)}):
            review=copy.deepcopy(self.review)
            review['reviews'][0].update(changes)
            self.save('table-date-role-reviews.json',review)
            with self.subTest(changes=changes),self.assertRaises(ValueError):checker.validate(self.folder)

    def test_rejects_wrong_quotes_roles_and_reversed_periods(self):
        for changes in ({'native_quote':'absent'},{'role':'invented'},{'period_start':'2020-02-01'}):
            review=copy.deepcopy(self.review)
            review['reviews'][0]['date_observations'][0].update(changes)
            self.save('table-date-role-reviews.json',review)
            with self.subTest(changes=changes),self.assertRaises(ValueError):checker.validate(self.folder)
