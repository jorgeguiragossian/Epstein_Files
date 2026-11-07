"""Citations fail closed on changed sources; date scope excludes uncertain files."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'viewer'))
from timeframes import validate_briefs,timeframe_index,select_timeframe,brief_fingerprint


class TimeframeTests(unittest.TestCase):
    def setUp(self):
        text='A source statement.\nFurther context.'
        self.sources={'one':{'sha256':'pdf-hash','pages':{1:text}}}
        self.prepared={'briefs':[dict(file_id='one',source_sha256='pdf-hash',title='Source brief',scope='Page 1 only',status='ai_assisted_editorial_draft',points=[dict(statement='The source makes a statement.',limitation='Not independently verified.',citations=[dict(page=1,quote='A source statement.',page_text_sha256=hashlib.sha256(text.encode()).hexdigest())])])]}

    def test_valid_citations_preserve_scope_and_limitations(self):
        result=validate_briefs(self.prepared,self.sources)
        self.assertEqual(result['one']['points'][0]['limitation'],'Not independently verified.')

    def test_changed_hash_page_quote_and_missing_citation_rejected(self):
        for field in ('pdf','page_hash','quote','missing','status'):
            value=copy.deepcopy(self.prepared);brief=value['briefs'][0];citation=brief['points'][0]['citations'][0]
            if field=='pdf':brief['source_sha256']='changed'
            elif field=='page_hash':citation['page_text_sha256']='changed'
            elif field=='quote':citation['quote']='Not in the source'
            elif field=='missing':brief['points'][0]['citations']=[]
            else:brief['status']='verified'
            with self.subTest(field=field),self.assertRaises(ValueError):validate_briefs(value,self.sources)
        value=copy.deepcopy(self.prepared);value['briefs']*=2
        with self.assertRaises(ValueError):validate_briefs(value,self.sources)

    def test_document_name_scope_metadata_only_and_inclusive_dates(self):
        words={'documents':[dict(id='one',dataset=1,date_status='dated',primary_date='2020-01-01',pages=[{'people':[]},{'people':['person']}]),dict(id='two',dataset=2,date_status='dated',primary_date='2021-01-01',pages=[{'people':[]}]),dict(id='three',dataset=1,date_status='uncertain',primary_date=None,pages=[])]}
        index=timeframe_index(words,{'one':{'evidence_page':1},'two':{'evidence_page':1}},validate_briefs(self.prepared,self.sources))
        result=select_timeframe(index,['person'])
        self.assertEqual((result['eligible_dated_documents'],result['excluded_without_reviewed_date'],result['prepared_briefs'],result['date_evidence_only']),(2,1,1,1))
        self.assertEqual([r['id'] for r in result['results']],['two','one'])
        result=select_timeframe(index,['person'],date_from='2020-01-01',date_to='2020-01-01',person='person')
        self.assertEqual(result['selected_documents'],1)
        self.assertEqual(result['results'][0]['brief']['points'][0]['citations'][0]['page'],1)
        self.assertEqual(select_timeframe(index,[],dataset='2')['prepared_briefs'],0)
        self.assertEqual(select_timeframe(index,[],date_to='1900-01-01')['results'],[])
        for query in [dict(date_from='2020-02-30'),dict(dataset='13'),dict(person='unknown'),dict(date_from='2021-01-01',date_to='2020-01-01')]:
            with self.subTest(query=query),self.assertRaises(ValueError):select_timeframe(index,[],**query)

    def test_editorial_check_expires_when_statement_or_citations_change(self):
        brief=self.prepared['briefs'][0]
        review=dict(file_id='one',source_sha256='pdf-hash',brief_sha256=brief_fingerprint(brief),reviewer='Codex',reviewed_on='2026-11-07',result='supported_as_scoped',checks=dict(statement_support=True,attribution=True,page_scope=True,limitations=True))
        result=validate_briefs(self.prepared,self.sources,{'reviews':[review]})
        self.assertIn('editorial_review',result['one'])
        self.assertNotIn('editorial_review',brief)
        for field in ('statement','citation'):
            changed=copy.deepcopy(self.prepared)
            if field=='statement':changed['briefs'][0]['points'][0]['statement']='An altered claim.'
            else:changed['briefs'][0]['points'][0]['citations'][0]['quote']='Further context.'
            with self.subTest(field=field),self.assertRaises(ValueError):validate_briefs(changed,self.sources,{'reviews':[review]})
        false_check=copy.deepcopy(review);false_check['checks']['attribution']=False
        with self.assertRaises(ValueError):validate_briefs(self.prepared,self.sources,{'reviews':[false_check]})
        injected=copy.deepcopy(self.prepared);injected['briefs'][0]['editorial_review']=review
        with self.assertRaises(ValueError):validate_briefs(injected,self.sources)

    def test_regeneration_cannot_renew_an_edited_briefs_review(self):
        root=Path(__file__).resolve().parents[1]
        spec=importlib.util.spec_from_file_location('prepare_briefs',root/'scripts/prepare-timeframe-briefs.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        rows=json.loads((root/'data/pilot/2026-11-01/timeframe-briefs.json').read_text(encoding='utf-8'))['briefs']
        self.assertEqual(len(module.recorded_reviews(rows)),28)
        changed=copy.deepcopy(rows);changed[0]['points'][0]['statement']+=' Changed.'
        with self.assertRaises(ValueError):module.recorded_reviews(changed)
