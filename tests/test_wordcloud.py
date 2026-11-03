"""Token rules, reviewed-date scope and exact page-level evidence."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'viewer'))
from wordcloud import frequencies,build_word_index,word_cloud


class WordTests(unittest.TestCase):
    def setUp(self):
        self.docs=[dict(id='EFTA00000001',dataset=1,date_review={'status':'dated','primary_date':'2020-01-01'},pages=[dict(number=1,text='Café apple apple and court EFTA0009',name_mentions=[{'id':'person'}]),dict(number=2,text='banana court',name_mentions=[])]),
            dict(id='EFTA00000002',dataset=2,date_review={'status':'dated','primary_date':'2020-02-01'},pages=[dict(number=1,text='banana banana court',name_mentions=[])]),
            dict(id='EFTA00000003',dataset=1,date_review={'status':'uncertain','primary_date':None},pages=[dict(number=1,text='secret secret secret',name_mentions=[])])]
        self.index=build_word_index(self.docs)

    def test_tokens_exclude_artifacts_and_normalize_accents(self):
        self.assertEqual(frequencies('The café CAFÉ\nEFTA00000001\nSDNY_GM_123\n123\nhttp://example.com a@example.com ID999 x9word'),{'cafe':2})
        self.assertEqual(frequencies('FREE STATE REPORTING, INC.\nCourt Reporting Transcription\nD.C. Area 301-261-1902\nBalt. & Annap. 410-974-0947\nSource reporting matters'),{'matters':1,'reporting':1,'source':1})

    def test_date_denominators_and_source_counts(self):
        result=word_cloud(self.index,['person'])
        self.assertEqual((result['scope_documents'],result['eligible_dated_documents'],result['excluded_without_reviewed_date'],result['selected_pages']),(3,2,1,3))
        court=next(r for r in result['terms'] if r['term']=='court')
        self.assertEqual((court['count'],court['documents']),(3,2))
        self.assertEqual(sum(r['count'] for r in court['sources']),court['count'])
        self.assertNotIn('secret',[r['term'] for r in result['terms']])
        single=word_cloud(self.index,['person'],date_from='2020-01-01',date_to='2020-01-01')
        self.assertEqual(single['selected_documents'],1)

    def test_person_filters_pages_and_exclusions_preserve_sources(self):
        result=word_cloud(self.index,['person'],person='person',exclude='apple')
        self.assertEqual((result['selected_documents'],result['selected_pages']),(1,1))
        self.assertEqual([r['term'] for r in result['terms']],['cafe','court'])
        self.assertTrue(all(s['page']==1 for r in result['terms'] for s in r['sources']))
        self.assertEqual(word_cloud(self.index,[],dataset='2')['selected_documents'],1)
        self.assertNotIn('cafe',[r['term'] for r in word_cloud(self.index,[],exclude='CAFÉ')['terms']])

    def test_empty_scope_and_invalid_filters(self):
        self.assertEqual(word_cloud(self.index,[],date_to='1900-01-01')['terms'],[])
        for query in [dict(date_from='2020-02-30'),dict(date_from='2021-01-01',date_to='2020-01-01'),dict(dataset='13'),dict(person='missing'),dict(exclude='x'*301)]:
            with self.subTest(query=query),self.assertRaises(ValueError):word_cloud(self.index,[],**query)
