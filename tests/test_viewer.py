"""Offline viewer checks with synthetic records; no PDF text in Git."""
import importlib.util
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('viewer_server', ROOT / 'viewer/server.py')
viewer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(viewer)


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # A small synthetic index makes tests independent of ignored pilot caches.
        cls.temp = tempfile.TemporaryDirectory()
        cls.db = Path(cls.temp.name) / 'index.sqlite'
        with closing(sqlite3.connect(cls.db)) as c:
            c.executescript('''
                CREATE TABLE documents(id TEXT PRIMARY KEY,dataset INTEGER,page_count INTEGER,low_text_pages INTEGER,
                    bytes INTEGER,date_count INTEGER,email_headers INTEGER,url TEXT,sha256 TEXT,pdf_path TEXT);
                CREATE TABLE pages(id INTEGER PRIMARY KEY,document_id TEXT,number INTEGER,text TEXT,low_text INTEGER,date_candidates TEXT);
                CREATE VIRTUAL TABLE search USING fts5(text,tokenize='unicode61');
                CREATE TABLE document_dates(document_id TEXT PRIMARY KEY,status TEXT,primary_date TEXT,date_type TEXT,review_json TEXT);
            ''')
            c.executemany('INSERT INTO documents VALUES (?,?,?,?,?,?,?,?,?,?)', [
                ('EFTA00000001',1,2,1,100,1,0,'https://www.justice.gov/example.pdf','abc','fixture.pdf'),
                ('EFTA00000002',2,1,0,200,0,0,'https://www.justice.gov/example2.pdf','def','fixture2.pdf'),
                ('EFTA00000003',3,1,0,200,0,0,'https://www.justice.gov/3.pdf','ghi','3.pdf'),
                ('EFTA00000004',4,1,0,200,0,0,'https://www.justice.gov/4.pdf','jkl','4.pdf')])
            rows = [(1,'EFTA00000001',1,'A report about a meeting in New York.',0,'[]'),
                (2,'EFTA00000001',2,'New York meeting continued on another page.',1,'[]'),
                (3,'EFTA00000002',1,'A different meeting in London.',0,'[]'),
                (4,'EFTA00000003',1,'Undated fixture.',0,'[]'),(5,'EFTA00000004',1,'Unreviewed fixture.',0,'[]')]
            c.executemany('INSERT INTO pages VALUES (?,?,?,?,?,?)',rows)
            c.executemany('INSERT INTO search(rowid,text) VALUES (?,?)',[(r[0],r[3]) for r in rows])
            c.executemany('INSERT INTO document_dates VALUES (?,?,?,?,?)',[
                ('EFTA00000001','dated','2019-06-18','transcript_session','{"status":"dated","primary_date":"2019-06-18"}'),
                ('EFTA00000002','uncertain',None,None,'{"status":"uncertain"}'),
                ('EFTA00000003','undated',None,None,'{"status":"undated"}')])
            c.commit()
        cls.catalog = viewer.Catalog(cls.db)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_search_groups_pages_and_links_to_first_match(self):
        response = self.catalog.search('New York')
        self.assertEqual(response['total_documents'],1)
        self.assertEqual(response['total_matching_pages'],2)
        self.assertEqual(response['results'][0]['matching_pages'],[1,2])
        self.assertEqual(response['results'][0]['first_page'],1)
        excerpt = viewer.snippet('injury ' + 'x '*100 + 'a jury was present', ['jury'])
        self.assertIn('a jury',excerpt)
        self.assertNotIn('injury',excerpt)

    def test_dataset_quality_and_exact_id(self):
        self.assertEqual(self.catalog.search('meeting',dataset='2')['total_documents'],1)
        self.assertEqual(self.catalog.search(quality='review')['total_documents'],1)
        self.assertEqual(self.catalog.search('efta00000001')['results'][0]['matching_pages'],[1,2])
        self.assertEqual(self.catalog.search('New London')['total_documents'],0)

    def test_input_is_literal_and_parameters_are_validated(self):
        self.assertEqual(self.catalog.search('"meeting"')['total_documents'],2)
        self.assertEqual(self.catalog.search('meeting OR nonexistent')['total_documents'],0)
        for kwargs in ({'q':'***'}, {'dataset':'1 OR 1=1'}, {'quality':'invalid'}, {'page':'0'}, {'q':'x'*201}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError): self.catalog.search(**kwargs)

    def test_page_references_and_missing_documents(self):
        response = self.catalog.document('EFTA00000001',2)
        self.assertEqual(response['page']['number'],2)
        self.assertTrue(response['page']['low_text'])
        self.assertNotIn('pdf_path',response)
        with self.assertRaises(ValueError): self.catalog.document('EFTA00000001',3)
        with self.assertRaises(LookupError): self.catalog.document('../../README.md')

    def test_pdf_byte_ranges(self):
        self.assertEqual(viewer.byte_range(None,100),(0,99,False))
        self.assertEqual(viewer.byte_range('bytes=0-9',100),(0,9,True))
        self.assertEqual(viewer.byte_range('bytes=-10',100),(90,99,True))
        self.assertEqual(viewer.byte_range('bytes=90-',100),(90,99,True))
        for value in ('bytes=100-', 'bytes=10-5','bytes=0-1,5-6','bytes=-0'):
            with self.subTest(value=value), self.assertRaises(ValueError): viewer.byte_range(value,100)

    def test_date_range_uses_reviewed_primary_date_and_inclusive_bounds(self):
        self.assertEqual(self.catalog.search(date_from='2019-06-18',date_to='2019-06-18')['total_documents'],1)
        self.assertEqual(self.catalog.search(date_to='2019-06-17')['total_documents'],0)
        self.assertEqual(self.catalog.search(date_from='2019-06-19')['total_documents'],0)
        self.assertEqual(self.catalog.search(q='meeting',dataset='1',date_from='2019-01-01')['total_documents'],1)
        self.assertEqual(self.catalog.search(q='meeting',dataset='2',date_from='2019-01-01')['total_documents'],0)

    def test_date_statuses_do_not_conflate_unreviewed_and_undated(self):
        for status in ('dated','uncertain','undated','unreviewed'):
            with self.subTest(status=status):
                self.assertEqual(self.catalog.search(date_status=status)['total_documents'],1)
        self.assertEqual(self.catalog.document('EFTA00000004')['date_review']['status'],'unreviewed')

    def test_invalid_dates_and_non_date_status_range_combinations(self):
        for kwargs in ({'date_from':'2021-02-29'},{'date_to':'2019-6-1'},{'date_from':'2020-01-01','date_to':'2019-01-01'},
            {'date_status':'uncertain','date_from':'2019-01-01'},{'date_status':'invented'}):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError): self.catalog.search(**kwargs)

    def test_review_rejects_source_changes_and_uncertain_primary_dates(self):
        record={'status':'dated','primary_date':'2019-06-18','date_type':'transcript_session','precision':'day','source_sha256':'abc','evidence_page':1,'evidence_quote':'June 18, 2019'}
        metric={'sha256':'abc','page_count':1}
        extracted={'pages':[{'text':'Session June 18, 2019. Mentions 2018-08-23.'}]}
        viewer.validate_review(record,metric,extracted)
        for changes in ({'source_sha256':'changed'},{'evidence_page':2},{'evidence_quote':'not present'},{'status':'uncertain'}):
            with self.subTest(changes=changes),self.assertRaises(ValueError): viewer.validate_review(dict(record,**changes),metric,extracted)


if __name__ == '__main__': unittest.main()
