import copy
import hashlib
import unittest
from viewer.source_quality import attach_quality


class SourceQualityTests(unittest.TestCase):
    def test_bindings_scope_and_no_promotion(self):
        text = 'Memorandum'
        sha = hashlib.sha256(text.encode()).hexdigest()
        prepared = [(dict(file_id='doc',sha256='source'),{},dict(pages=[dict(page=1,text=text)]),None)]
        quality = dict(method='Bounded review',files=[dict(file_id='doc',source_sha256='source',notes='Scope',
            visually_inspected_pdf_pages=[1],inspected_page_text_sha256={'1':sha})])
        component = dict(file_id='doc',source_sha256='source',pdf_pages=1,visually_inspected_pdf_pages=[1],
            page_evidence=[dict(pdf_page=1,native_text_sha256=sha)],
            component_start_observations=[dict(pdf_page=1,native_text_sha256=sha,native_quote=text)])
        attach_quality(prepared,quality,component)
        self.assertEqual(prepared[0][0]['source_quality_review']['component_assessment'],component)
        self.assertEqual(prepared[0][0]['source_quality_review']['date_observations'],[])
        for change in ({'source_sha256':'changed'},{'whole_document_review':True},
                       {'primary_date_assigned':True},{'verified_legal_status':True},
                       {'page_evidence':[dict(pdf_page=1,native_text_sha256='changed')]},
                       {'visually_inspected_pdf_pages':[]}):
            with self.subTest(change=change),self.assertRaises(ValueError):
                attach_quality(copy.deepcopy(prepared),quality,dict(component,**change))
        stale=copy.deepcopy(quality)
        stale['files'][0]['inspected_page_text_sha256']['1']='changed'
        with self.assertRaises(ValueError):attach_quality(prepared,stale,component)
