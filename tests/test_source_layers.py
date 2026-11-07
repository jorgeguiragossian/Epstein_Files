import copy
import hashlib
import unittest
from viewer.source_layers import header_label_layer, header_fragment_layer
from viewer.email_parser import parse_document


class SourceLayerTests(unittest.TestCase):
    def setUp(self):
        text = 'Front \nTo \nSubject: Re: example\nDate: Mon, 06 Jul 2020 15:47:22 +0000\nBody remains unchanged.'
        self.extracted = dict(source_sha256='pdf-hash', pages=[dict(page=1, text=text)])
        self.review = dict(file_id='one', source_sha256='pdf-hash', reviewer='Codex', reviewed_on='2026-11-07', labels=[
            dict(page=1, line=n, native_line=line, field=field, page_text_sha256=hashlib.sha256(text.encode()).hexdigest())
            for n, line, field in [(1, 'Front ', 'from'), (2, 'To ', 'to')]])

    def test_opt_in_layer_preserves_native_and_body_without_identity_reconstruction(self):
        before = copy.deepcopy(self.extracted)
        self.assertEqual(parse_document(before, 'one', 8, 'pdf-hash'), [])
        derived = header_label_layer(self.extracted, 'one', 'pdf-hash', self.review)
        self.assertEqual(before, self.extracted)
        self.assertEqual(derived['pages'][0]['text'].splitlines()[2:], before['pages'][0]['text'].splitlines()[2:])
        rows = parse_document(derived, 'one', 8, 'pdf-hash')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['sender_addresses'], [])
        self.assertEqual(rows[0]['recipient_addresses'], [])
        self.assertFalse(rows[0]['strong_visible_key'])

    def test_changed_source_page_line_and_nonlabel_edits_are_rejected(self):
        for field in ('source', 'page', 'line', 'label'):
            extracted, review = copy.deepcopy(self.extracted), copy.deepcopy(self.review)
            if field == 'source':review['source_sha256'] = 'changed'
            elif field == 'page':extracted['pages'][0]['text'] += ' Changed.'
            elif field == 'line':review['labels'][0]['native_line'] = 'From'
            else:review['labels'][0]['field'] = 'sender@example.org'
            with self.subTest(field=field), self.assertRaises(ValueError):
                header_label_layer(extracted, 'one', 'pdf-hash', review)


class FragmentLayerTests(unittest.TestCase):
    def setUp(self):
        text = 'From:\nTo:\nUnresolved header fragment \nCc:\nSubject: link\nDate: Tue, 16 Jul 2019 19:25:59 +0000\nBody link remains unchanged.'
        self.extracted = dict(source_sha256='pdf-hash', pages=[dict(page=1, text=text)])
        self.review = dict(file_id='one', source_sha256='pdf-hash', reviewer='Codex', reviewed_on='2026-11-07',
                           fragments=[dict(page=1, line=3, native_line='Unresolved header fragment ',
                                           page_text_sha256=hashlib.sha256(text.encode()).hexdigest())])

    def test_unassigned_fragment_retained_and_body_untouched(self):
        original = copy.deepcopy(self.extracted)
        self.assertEqual(parse_document(original, 'one', 8, 'pdf-hash'), [])
        derived = header_fragment_layer(self.extracted, 'one', 'pdf-hash', self.review)
        self.assertEqual(original, self.extracted)
        self.assertEqual(derived['derived_text_layer']['unresolved_fragments'], self.review['fragments'])
        self.assertEqual(derived['pages'][0]['text'].splitlines()[3:], original['pages'][0]['text'].splitlines()[3:])
        rows = parse_document(derived, 'one', 8, 'pdf-hash')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['headers']['to'], '')
        self.assertEqual(rows[0]['sender_addresses'], [])
        self.assertEqual(rows[0]['body'], 'Body link remains unchanged.')

    def test_only_reviewed_header_interval_and_unchanged_evidence_are_accepted(self):
        for field in ('hash', 'source', 'interval'):
            extracted, review = copy.deepcopy(self.extracted), copy.deepcopy(self.review)
            if field == 'hash':review['fragments'][0]['page_text_sha256'] = 'changed'
            elif field == 'source':review['source_sha256'] = 'changed'
            else:
                extracted['pages'][0]['text'] = extracted['pages'][0]['text'].replace('Cc:', 'Body:')
                review['fragments'][0]['page_text_sha256'] = hashlib.sha256(extracted['pages'][0]['text'].encode()).hexdigest()
            with self.subTest(field=field), self.assertRaises(ValueError):
                header_fragment_layer(extracted, 'one', 'pdf-hash', review)
