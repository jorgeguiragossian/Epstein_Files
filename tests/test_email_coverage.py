"""Coverage denominators and overlapping uncertainty categories."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'viewer'))
from email_coverage import review_coverage
from email_parser import review_page


class CoverageTests(unittest.TestCase):
    def test_zero_candidate_documents_and_overlapping_categories(self):
        records=[dict(id='one',file_id='EFTA00000001',flags=['sender_address_unresolved','date_missing'],source_review={'boundary_status':'contains_unseparated_quote'},body_partition={'spans':[]}),
                 dict(id='two',file_id='EFTA00000001',flags=['recipient_address_unresolved','date_ambiguous_numeric']),
                 dict(id='three',file_id='EFTA00000002',flags=['date_timezone_unspecified'],source_review={'boundary_status':'supported_segment'})]
        documents=[dict(id=f'EFTA0000000{i}',dataset=1 if i<3 else 2) for i in (1,2,3)]
        result=review_coverage({'records':records},documents);t=result['totals']
        self.assertEqual((t['documents'],t['documents_with_candidates'],t['candidates'],t['reviewed'],t['unreviewed']),(3,2,3,2,1))
        self.assertEqual((t['boundary'],t['date_unresolved'],t['sender_unresolved'],t['recipient_unresolved']),(1,2,1,1))
        self.assertEqual(result['datasets'][1]['candidates'],0)
        self.assertEqual(result['documents'][2]['reviewed'],0)
        for field in ('documents','candidates','reviewed','unreviewed','boundary','date_unresolved'):
            self.assertEqual(sum(r[field] for r in result['datasets']),t[field])

    def test_layout_and_trailing_issues_remain_in_boundary_drilldown(self):
        records=[dict(id=str(i),file_id='doc',source_page=1,source_line=i+1,flags=[],source_review={'boundary_status':status}) for i,status in enumerate(('source_order_mismatch','unresolved_trailing_material','calendar_alert_not_correspondence'))]
        catalog=dict(records=records,summary={},groups=[dict(id=r['id'],record_ids=[r['id']],occurrences=1) for r in records])
        self.assertEqual(review_coverage(catalog,[dict(id='doc',dataset=11)])['totals']['boundary'],2)
        result=review_page(catalog,'boundary')
        self.assertEqual(result['total_groups'],2)
        self.assertEqual({r['representative']['id'] for r in result['results']},{'0','1'})

    def test_unknown_source_rejected(self):
        with self.assertRaises(ValueError):review_coverage({'records':[{'file_id':'missing'}]},[])

    def test_brief_and_date_denominators_are_document_counts(self):
        documents=[dict(id=f'doc{i}',dataset=1 if i<3 else 2) for i in range(4)]
        index={'documents':[dict(id='doc0',date_status='dated',primary_date='2020-01-01',brief={'editorial_review':{'reviewer':'Codex'}}),dict(id='doc1',date_status='dated',primary_date='2020-01-01',brief={'status':'draft'}),dict(id='doc2',date_status='dated',primary_date='2020-01-01',brief=None),dict(id='doc3',date_status='uncertain',primary_date=None,brief=None)]}
        result=review_coverage({'records':[]},documents,index);t=result['totals']
        self.assertEqual((t['eligible_dated_documents'],t['prepared_briefs'],t['source_checked_briefs'],t['date_evidence_only'],t['excluded_without_reviewed_date']),(3,2,1,1,1))
        self.assertEqual(t['prepared_briefs']+t['date_evidence_only'],t['eligible_dated_documents'])
        self.assertLessEqual(t['source_checked_briefs'],t['prepared_briefs'])
        for field in ('eligible_dated_documents','prepared_briefs','source_checked_briefs','date_evidence_only','excluded_without_reviewed_date'):
            self.assertEqual(sum(r[field] for r in result['datasets']),t[field])
        self.assertEqual(t['candidates'],0)

    def test_drilldowns_preserve_group_sources(self):
        first=dict(id='one',file_id='EFTA00000001',source_page=1,source_line=1,flags=['sender_address_unresolved','date_missing'],source_review={'boundary_status':'supported_segment'})
        second=dict(id='two',file_id='EFTA00000002',source_page=1,source_line=1,flags=['recipient_address_unresolved'])
        catalog=dict(records=[first,second],summary={},groups=[dict(id='copy',record_ids=['one','two'],occurrences=2)])
        for focus in ('sender','recipient','date','unreviewed'):
            result=review_page(catalog,focus)
            self.assertEqual(result['total_groups'],1)
            self.assertEqual(len(result['results'][0]['sources']),2)
