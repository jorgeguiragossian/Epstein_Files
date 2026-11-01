"""Offline viewer checks using the pilot's real page index; no PDF text in Git."""
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
            ''')
            c.executemany('INSERT INTO documents VALUES (?,?,?,?,?,?,?,?,?,?)', [
                ('EFTA00000001',1,2,1,100,1,0,'https://www.justice.gov/example.pdf','abc','fixture.pdf'),
                ('EFTA00000002',2,1,0,200,0,0,'https://www.justice.gov/example2.pdf','def','fixture2.pdf')])
            rows = [(1,'EFTA00000001',1,'A report about a meeting in New York.',0,'[]'),
                (2,'EFTA00000001',2,'New York meeting continued on another page.',1,'[]'),
                (3,'EFTA00000002',1,'A different meeting in London.',0,'[]')]
            c.executemany('INSERT INTO pages VALUES (?,?,?,?,?,?)',rows)
            c.executemany('INSERT INTO search(rowid,text) VALUES (?,?)',[(r[0],r[3]) for r in rows])
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


if __name__ == '__main__': unittest.main()
