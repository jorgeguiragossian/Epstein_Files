"""Offline viewer checks with synthetic records; no PDF text in Git."""
import importlib.util
import sqlite3
import tempfile
import unittest
import json
import hashlib
import sys
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'viewer'))
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
                CREATE TABLE people(id TEXT PRIMARY KEY,label TEXT,forms_json TEXT,evidence_json TEXT);
                CREATE TABLE name_mentions(page_id INTEGER,person_id TEXT,occurrences INTEGER,hits_json TEXT,PRIMARY KEY(page_id,person_id));
            ''')
            c.executemany('INSERT INTO documents VALUES (?,?,?,?,?,?,?,?,?,?)', [
                ('EFTA00000001',1,2,1,100,1,0,'https://www.justice.gov/example.pdf','abc','fixture.pdf'),
                ('EFTA00000002',2,1,0,200,0,0,'https://www.justice.gov/example2.pdf','def','fixture2.pdf'),
                ('EFTA00000003',3,1,0,200,0,0,'https://www.justice.gov/3.pdf','ghi','3.pdf'),
                ('EFTA00000004',4,1,0,200,0,0,'https://www.justice.gov/4.pdf','jkl','4.pdf')])
            rows = [(1,'EFTA00000001',1,'Alice Example and Bob Person: a report about a meeting in New York.',0,'[]'),
                (2,'EFTA00000001',2,'Alice\nExample: New York meeting continued on another page. Alice Example.',1,'[]'),
                (3,'EFTA00000002',1,'A different meeting in London.',0,'[]'),
                (4,'EFTA00000003',1,'Undated fixture.',0,'[]'),(5,'EFTA00000004',1,'Unreviewed fixture.',0,'[]')]
            c.executemany('INSERT INTO pages VALUES (?,?,?,?,?,?)',rows)
            c.executemany('INSERT INTO search(rowid,text) VALUES (?,?)',[(r[0],r[3]) for r in rows])
            c.executemany('INSERT INTO document_dates VALUES (?,?,?,?,?)',[
                ('EFTA00000001','dated','2019-06-18','transcript_session','{"status":"dated","primary_date":"2019-06-18"}'),
                ('EFTA00000002','uncertain',None,None,'{"status":"uncertain"}'),
                ('EFTA00000003','undated',None,None,'{"status":"undated"}')])
            c.executemany('INSERT INTO people VALUES (?,?,?,?)',[
                ('alice-example','Alice Example','["Alice Example"]','{}'),('bob-person','Bob Person','["Bob Person"]','{}')])
            for row in rows:
                for key,name in [('alice-example','Alice Example'),('bob-person','Bob Person')]:
                    hits=viewer.name_occurrences(row[3],[name])
                    if hits:
                        import json
                        c.execute('INSERT INTO name_mentions VALUES (?,?,?,?)',(row[0],key,len(hits),json.dumps(hits)))
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
        for role in ('letter','presentation','court_order'):
            viewer.validate_review(dict(record,date_type=role),metric,extracted)
        with self.assertRaises(ValueError):viewer.validate_review(dict(record,date_type='invented'),metric,extracted)
        for changes in ({'source_sha256':'changed'},{'evidence_page':2},{'evidence_quote':'not present'},{'status':'uncertain'}):
            with self.subTest(changes=changes),self.assertRaises(ValueError): viewer.validate_review(dict(record,**changes),metric,extracted)
        supporting=dict(pdf_page=1,quote='June 18, 2019',native_text_sha256=hashlib.sha256(extracted['pages'][0]['text'].encode()).hexdigest())
        viewer.validate_review(dict(record,supporting_evidence=[supporting]),metric,extracted)
        for changes in ({'pdf_page':2},{'quote':'absent'},{'native_text_sha256':'changed'}):
            with self.subTest(supporting=changes),self.assertRaises(ValueError):
                viewer.validate_review(dict(record,supporting_evidence=[dict(supporting,**changes)]),metric,extracted)

    def test_person_matches_are_page_scoped_and_combine_with_dates(self):
        response=self.catalog.search(person='alice-example')
        self.assertEqual(response['total_documents'],1)
        self.assertEqual(response['results'][0]['matching_pages'],[1,2])
        self.assertEqual(self.catalog.search(person='bob-person',q='continued')['total_documents'],0)
        self.assertEqual(self.catalog.search(person='alice-example',date_from='2019-06-18',date_to='2019-06-18')['total_documents'],1)
        self.assertEqual(self.catalog.search(person='alice-example',dataset='2')['total_documents'],0)
        with self.assertRaises(ValueError):self.catalog.search(person="' OR 1=1")

    def test_name_occurrences_are_not_contact_counts(self):
        people={p['id']:p for p in self.catalog.people()['people']}
        self.assertEqual((people['alice-example']['documents'],people['alice-example']['pages'],people['alice-example']['occurrences']),(1,2,3))
        mentions=self.catalog.document('EFTA00000001',2)['page']['name_mentions']
        self.assertEqual(mentions[0]['occurrences'],2)

    def test_full_names_boundaries_linebreaks_and_overlapping_forms(self):
        text='JEFFREY\nEPSTEIN; Jeffrey Epsteins; notJeffrey Epstein; JE; Epstein.'
        hits=viewer.name_occurrences(text,['Jeffrey Epstein','JEFFREY EPSTEIN'])
        self.assertEqual(len(hits),1)
        self.assertEqual(text[hits[0]['start']:hits[0]['end']],'JEFFREY\nEPSTEIN')
        self.assertEqual(len(viewer.name_occurrences('João\nSilva',['João Silva'])),1)

    def test_person_vocabulary_requires_source_evidence(self):
        person={'id':'alice-example','label':'Alice Example','forms':['Alice Example'],
            'evidence':{'file_id':'example','pdf_page':1,'quote':'Alice Example','source_sha256':'abc'}}
        prepared=[({'file_id':'example','sha256':'abc','page_count':1},{},{'pages':[{'text':'Alice Example was named.'}]},None)]
        viewer.validate_people([person],prepared)
        with self.assertRaises(ValueError):viewer.validate_people([person,person],prepared)
        for evidence in ({'source_sha256':'changed'},{'quote':'Bob Person'},{'pdf_page':2}):
            with self.subTest(evidence=evidence),self.assertRaises(ValueError):
                viewer.validate_people([dict(person,evidence=dict(person['evidence'],**evidence))],prepared)


class VocabularyArtifactTests(unittest.TestCase):
    def test_coverage_is_bound_to_sources_and_vocabulary(self):
        pilot=ROOT/'data/pilot/2026-11-01'
        vocabulary=json.loads((pilot/'people.json').read_text(encoding='utf-8'))['people']
        coverage=json.loads((pilot/'people-coverage.json').read_text(encoding='utf-8'))
        for key,filename in [('vocabulary_sha256','people.json'),('metrics_sha256','metrics.json'),('selection_sha256','selection.json')]:
            self.assertEqual(coverage[key],hashlib.sha256((pilot/filename).read_bytes()).hexdigest())
        self.assertEqual({p['id'] for p in vocabulary},{p['id'] for p in coverage['people']})
        self.assertEqual(len(vocabulary),22)
        metrics={r['file_id']:r for r in json.loads((pilot/'metrics.json').read_text(encoding='utf-8'))['files']}
        for person in vocabulary:
            evidence=person['evidence'];source=metrics[evidence['file_id']]
            self.assertEqual(evidence['source_sha256'],source['sha256'])
            self.assertTrue(1<=evidence['pdf_page']<=source['page_count'])
        alan=next(p for p in vocabulary if p['id']=='alan-dershowitz')
        self.assertEqual((alan['evidence']['file_id'],alan['evidence']['pdf_page']),('EFTA00009329',14))

    def test_deferred_spelling_and_initial_forms_are_not_silently_merged(self):
        pilot=ROOT/'data/pilot/2026-11-01'
        notes=json.loads((pilot/'name-review-notes.json').read_text(encoding='utf-8'))['decisions']
        pairs={'Jeffery Epstein':'Jeffrey Epstein','Lillian Sanchez':'Lilly Ann Sanchez','Darren K. Indyke':'Darren Indyke'}
        self.assertEqual({n['observed_form'] for n in notes},set(pairs))
        for note in notes:
            self.assertEqual(note['status'],'deferred_not_in_filter')
            self.assertEqual(viewer.name_occurrences(note['evidence']['quote'],[pairs[note['observed_form']]]),[])


if __name__ == '__main__': unittest.main()
