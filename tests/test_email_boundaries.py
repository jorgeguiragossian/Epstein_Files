"""Lossless quote partitions must reject stale or incomplete evidence."""
import copy
import hashlib
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'viewer'))
from email_parser import build_email_catalog
from email_boundaries import apply_boundaries


class BoundaryTests(unittest.TestCase):
    def setUp(self):
        text='From: a@example.org\nTo: b@example.org\nSubject: Example\nMy reply.\nOn Wednesday, someone wrote:\nQuoted text.\nFrom: b@example.org\nTo: a@example.org\nSubject: Earlier\nEarlier body.'
        self.prepared=[({'file_id':'EFTA00000001','dataset':1,'sha256':'hash'},None,{'pages':[{'page':1,'text':text}]},None)]
        self.catalog=build_email_catalog(self.prepared)
        record,child=self.catalog['records'];record['source_review']={'status':'fixture'}
        spans=[]
        for start,end,kind in [(4,4,'authored_text_candidate'),(5,6,'inline_quote')]:
            value='\n'.join(text.splitlines()[start-1:end])
            spans.append(dict(id=str(start),parent_record_id=record['id'],page=1,line_start=start,line_end=end,kind=kind,text=value,text_sha256=hashlib.sha256(value.encode()).hexdigest()))
        self.overlay=dict(parser_version=self.catalog['summary']['parser_version'],annotations=[dict(record_id=record['id'],file_id=record['file_id'],source_sha256='hash',visible_fingerprint=record['visible_fingerprint'],spans=spans,following_quoted_candidate_id=child['id'])])

    def test_partition_preserves_raw_and_grouping_and_links_existing_child(self):
        before=copy.deepcopy(self.catalog)
        result=apply_boundaries(self.catalog,self.overlay,self.prepared)
        self.assertEqual(result['groups'],before['groups'])
        self.assertEqual(len(result['records']),2)
        record=copy.deepcopy(result['records'][0]);partition=record.pop('body_partition')
        self.assertEqual(record,before['records'][0])
        self.assertEqual(partition['following_quoted_source']['source_line'],7)
        self.assertEqual(result['summary']['body_partitions']['quoted_spans'],1)
        self.assertFalse(result['summary']['contact_rankings_ready'])

    def test_changed_evidence_rejected(self):
        for field in ('source_sha256','visible_fingerprint'):
            value=copy.deepcopy(self.overlay);value['annotations'][0][field]='changed'
            with self.assertRaises(ValueError):apply_boundaries(copy.deepcopy(self.catalog),value,self.prepared)
        for field in ('text','text_sha256'):
            value=copy.deepcopy(self.overlay);value['annotations'][0]['spans'][0][field]='changed'
            with self.assertRaises(ValueError):apply_boundaries(copy.deepcopy(self.catalog),value,self.prepared)

    def test_missing_overlapping_and_out_of_range_spans_rejected(self):
        for mutation in ('missing','overlap','range','duplicate'):
            value=copy.deepcopy(self.overlay);spans=value['annotations'][0]['spans']
            if mutation=='missing':spans.pop()
            elif mutation=='overlap':spans[1]['line_start']=4
            elif mutation=='range':spans[1]['page']=2
            else:spans[1]['id']=spans[0]['id']
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):
                apply_boundaries(copy.deepcopy(self.catalog),value,self.prepared)

    def test_missing_review_duplicate_parent_and_invalid_child_rejected(self):
        catalog=copy.deepcopy(self.catalog);catalog['records'][0].pop('source_review')
        with self.assertRaises(ValueError):apply_boundaries(catalog,self.overlay,self.prepared)
        value=copy.deepcopy(self.overlay);value['annotations']*=2
        with self.assertRaises(ValueError):apply_boundaries(copy.deepcopy(self.catalog),value,self.prepared)
        value=copy.deepcopy(self.overlay);value['annotations'][0]['following_quoted_candidate_id']=value['annotations'][0]['record_id']
        with self.assertRaises(ValueError):apply_boundaries(copy.deepcopy(self.catalog),value,self.prepared)
