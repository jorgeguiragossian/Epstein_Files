"""Review overlays must fail closed when source evidence changes."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'viewer'))
from email_parser import build_email_catalog, review_page


class ValidationTests(unittest.TestCase):
    def setUp(self):
        text='From: a@example.org\nTo: b@example.org\nSubject: Test\nBody text.'
        self.prepared=[({'file_id':'EFTA00000001','dataset':1,'sha256':'hash'},None,{'pages':[{'page':1,'text':text}]},None)]
        self.base=build_email_catalog(self.prepared)
        r=self.base['records'][0]
        review={k:r[k] for k in ('file_id','source_sha256','source_page','source_line','visible_fingerprint')}
        review.update(record_id=r['id'],extracted_anchor='From: a@example.org',boundary_status='contains_unseparated_quote',unique_message_verified=False,contact_count_eligible=False)
        association=dict(id='pair',record_id=r['id'],file_id=r['file_id'],source_sha256='hash',source_page=1,field='from',address='a@example.org',raw_extracted_field=r['headers']['from'],ownership_verified=False,apply_globally=False)
        self.validation=dict(parser_version=self.base['summary']['parser_version'],reviews=[review],address_associations=[association])

    def test_overlay_preserves_evidence_and_groups(self):
        result=build_email_catalog(self.prepared,self.validation)
        original=copy.deepcopy(result['records'][0]);original.pop('source_review');original.pop('reviewed_address_associations')
        self.assertEqual(original,self.base['records'][0])
        self.assertEqual(result['groups'],self.base['groups'])
        for focus in ('reviewed','boundary'):
            self.assertEqual(review_page(result,focus)['total_groups'],1)
        self.assertFalse(result['summary']['contact_rankings_ready'])

    def test_stale_evidence_and_duplicate_reviews_rejected(self):
        for field in ('source_sha256','visible_fingerprint','extracted_anchor'):
            with self.subTest(field=field):
                value=copy.deepcopy(self.validation);value['reviews'][0][field]='changed'
                with self.assertRaises(ValueError):build_email_catalog(self.prepared,value)
        value=copy.deepcopy(self.validation);value['reviews']*=2
        with self.assertRaises(ValueError):build_email_catalog(self.prepared,value)

    def test_identity_and_count_promotions_rejected(self):
        for section,field in [('reviews','unique_message_verified'),('reviews','contact_count_eligible'),('address_associations','ownership_verified'),('address_associations','apply_globally')]:
            with self.subTest(field=field):
                value=copy.deepcopy(self.validation);value[section][0][field]=True
                with self.assertRaises(ValueError):build_email_catalog(self.prepared,value)

    def test_changed_raw_header_association_rejected(self):
        self.validation['address_associations'][0]['raw_extracted_field']='repaired text'
        with self.assertRaises(ValueError):build_email_catalog(self.prepared,self.validation)

    def test_unverified_continuation_stays_in_boundary_review(self):
        self.validation['reviews'][0]['boundary_status']='continuation_unverified'
        result=build_email_catalog(self.prepared,self.validation)
        self.assertEqual(review_page(result,'boundary')['total_groups'],1)
        self.assertEqual(result['summary']['source_review']['boundary_attention'],1)
        self.assertFalse(result['summary']['contact_rankings_ready'])
