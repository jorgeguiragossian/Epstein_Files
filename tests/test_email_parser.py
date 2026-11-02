"""Synthetic checks for email extraction, source references, and safe grouping."""
import sys
import unittest
import json
import hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'viewer'))
import email_parser as emails


def extract(pages,key='fixture'):
    return emails.parse_document({'pages':[{'page':i+1,'text':text} for i,text in enumerate(pages)]},key,1,'source-hash')


class EmailTests(unittest.TestCase):
    def test_meridiem_is_preserved_including_noon_and_midnight(self):
        for clock,hour in [('7:03 PM',19),('7:03 AM',7),('12:03 PM',12),('12:03 AM',0)]:
            with self.subTest(clock=clock):
                stamp,flags=emails.parse_date('Wednesday, March 11, 2020 '+clock)
                self.assertEqual(stamp,f'2020-03-11T{hour:02}:03:00')
                self.assertEqual(flags,['date_timezone_unspecified'])
        self.assertEqual(emails.parse_date('March 11, 2020 6:25:42 PM')[0],'2020-03-11T18:25:42')
        self.assertEqual(emails.parse_date('Wednesday, Jul 18 2018 2:32 PM')[0],'2018-07-18T14:32:00')

    def test_unsupported_meridiem_forms_do_not_fall_through_to_rfc(self):
        for raw in ['March 11, 2020 19:03 PM','March 11, 2020 7:03 PM EDT','cipher 10, 2018 4:37 PM']:
            with self.subTest(raw=raw):self.assertEqual(emails.parse_date(raw),(None,['date_unparsed']))
        self.assertEqual(emails.parse_date('Mon 5/1/2017 6:43 PM'),(None,['date_ambiguous_numeric']))
        self.assertEqual(emails.parse_date('Wed, 11 Mar 2020 23:04:47 +0000')[0],'2020-03-11T23:04:47+00:00')

    def test_header_order_date_context_and_redacted_values(self):
        rows=extract(['To:\nFrom:\nSubject: Meeting\nMay 18, 2017 1:00 PM: a date in the body\nEFTA00000001'])
        self.assertEqual(len(rows),1)
        self.assertIn('date_missing',rows[0]['flags'])
        self.assertIsNone(rows[0]['parsed_timestamp_candidate'])
        self.assertIn('May 18',rows[0]['body'])
        self.assertIn('sender_address_unresolved',rows[0]['flags'])

    def test_separate_sent_value_and_ambiguous_numeric_date(self):
        row=extract(['To: b@example.org\nFrom: a@example.org\nSent\nSubject Re: example\nMon 5/1/2017 6:43:26 PM\nA real body with an earlier quoted mention.'])[0]
        self.assertEqual(row['raw_date'],'Mon 5/1/2017 6:43:26 PM')
        self.assertIn('date_ambiguous_numeric',row['flags'])
        self.assertIsNone(row['parsed_timestamp_candidate'])

    def test_cross_page_body_and_quoted_header_provenance(self):
        rows=extract(['From: a@example.org\nTo: b@example.org\nDate: Wed, 11 Mar 2020 23:04:47 +0000\nSubject: First\nBody begins.',
            'Body continues.\nFrom: b@example.org\nTo: a@example.org\nSent: March 10, 2020 6:00 PM\nSubject: Previous\nEarlier message body.'])
        self.assertEqual(len(rows),2)
        self.assertEqual(rows[0]['body_pages'],[1,2])
        self.assertIn('Body continues',rows[0]['body'])
        self.assertEqual((rows[1]['source_page'],rows[1]['source_line']),(2,2))
        self.assertIn('later_or_nested_header',rows[1]['flags'])
        self.assertEqual(rows[0]['parsed_timestamp_candidate'],'2020-03-11T23:04:47+00:00')

    def test_exact_copy_groups_retain_all_occurrences(self):
        text='From: a@example.org\nTo: b@example.org\nDate: Wed, 11 Mar 2020 23:04:47 +0000\nSubject: Example\nThis is a long, identical message body for conservative copy comparison.'
        one=extract([text+'\nEFTA00000001'],'one')
        two=extract([text+'\nEFTA00000002'],'two')
        groups=emails.group_records(one+two)
        self.assertEqual(len(groups),1)
        self.assertEqual(groups[0]['kind'],'exact_visible_copies')
        self.assertEqual(len(groups[0]['record_ids']),2)
        self.assertEqual(groups[0]['distinct_documents'],2)
        different=extract([text+' Different final sentence.'],'three')
        self.assertEqual(len(emails.group_records(one+different)),2)

    def test_redacted_repeat_is_not_promoted_to_unique_message(self):
        text='From:\nTo:\nSubject: Same\nDate: Wed, 11 Mar 2020 23:04:47 +0000\nThe same visible body could have different redacted participants.'
        groups=emails.group_records(extract([text],'one')+extract([text],'two'))
        self.assertEqual(groups[0]['kind'],'possible_repeat_incomplete')
        self.assertIn('not_a_unique_message',groups[0]['status'])

    def test_body_mentions_and_phone_signature_do_not_create_headers(self):
        self.assertEqual(extract(['To: readers\nDate: 2020-01-01\nThis is a report.']),[])
        row=extract(['From: a@example.org\nTo: b@example.org\nSubject: Hi\nDate: Wed, 11 Mar 2020 23:04:47 +0000\nBody.\nSent from my iPhone'])[0]
        self.assertNotIn('sent',row['headers'])

    def test_scrambled_exhibit_header_keeps_page_evidence(self):
        row=extract(['EXHIBIT M','From:\nU\nSubject:\nDate:\nFwd: Next week\nSunday. February 24, 2019 8:18:01 PM\nMessage body.'])[0]
        self.assertEqual(row['source_page'],2)
        self.assertEqual(row['headers']['subject'],'Fwd: Next week')
        self.assertEqual(row['raw_date'],'Sunday. February 24, 2019 8:18:01 PM')
        self.assertIn('header_fragments_unresolved',row['flags'])

    def test_wrapped_recipient_lines_do_not_lose_subject_and_date(self):
        row=extract(['From: a@example.org\nTo: b@example.org\n(OFFICE)\nSubject: An opinion\nDate: Fri, 16 Apr 2021 22:09:33 +0000\nAn attachment is discussed in the body.'])[0]
        self.assertEqual(row['headers']['to'],'b@example.org (OFFICE)')
        self.assertEqual(row['parsed_timestamp_candidate'],'2021-04-16T22:09:33+00:00')

    def test_body_before_nested_header_is_not_appended_to_subject(self):
        records=extract(['From: a@example.org\nTo: b@example.org\nSent: March 11, 2020 6:00 PM\nSubject: First\nA short body.\nFrom: b@example.org\nTo: a@example.org\nSent: March 10, 2020 5:00 PM\nSubject: Earlier\nEarlier body.'])
        self.assertEqual(records[0]['headers']['subject'],'First')
        self.assertEqual(records[0]['body'],'A short body.')

    def test_review_filters_and_group_source_retention(self):
        text='From:\nTo:\nDate: Wed, 11 Mar 2020 23:04:47 +0000\nSubject: Same\nThe same visible text, with unresolved participants.'
        records=extract([text],'EFTA00000001')+extract([text],'EFTA00000002')
        catalog={'summary':{'candidate_occurrences':2},'records':records,'groups':emails.group_records(records)}
        result=emails.review_page(catalog,'repeats','EFTA00000002')
        self.assertEqual(result['total_groups'],1)
        self.assertEqual(result['results'][0]['representative']['file_id'],'EFTA00000002')
        self.assertEqual(len(result['results'][0]['sources']),2)
        with self.assertRaises(ValueError):emails.review_page(catalog,'invented')
        with self.assertRaises(ValueError):emails.review_page(catalog,document='../../README.md')
        with self.assertRaises(ValueError):emails.review_page(catalog,page=0)

    def test_committed_summary_has_provenance_without_raw_messages(self):
        pilot=Path(__file__).resolve().parents[1]/'data/pilot/2026-11-01'
        metadata=json.loads((pilot/'email-summary.json').read_text(encoding='utf-8'))
        metrics_path=pilot/'metrics.json'
        self.assertEqual(metadata['metrics_sha256'],hashlib.sha256(metrics_path.read_bytes()).hexdigest())
        self.assertIsNone(metadata['summary']['unique_messages'])
        self.assertFalse(metadata['summary']['contact_rankings_ready'])
        sources=[s for group in metadata['groups'] for s in group['sources']]
        self.assertEqual(len(sources),metadata['summary']['candidate_occurrences'])
        self.assertEqual(len({s['id'] for s in sources}),len(sources))
        metrics={m['file_id']:m for m in json.loads(metrics_path.read_text(encoding='utf-8'))['files']}
        for source in sources:
            self.assertEqual(source['source_sha256'],metrics[source['file_id']]['sha256'])
            self.assertTrue(1<=source['source_page']<=metrics[source['file_id']]['page_count'])
            self.assertGreater(source['source_line'],0)
        def inspect(value):
            if isinstance(value,dict):
                self.assertFalse(set(value)&{'headers','header_evidence','body','sender_addresses','recipient_addresses'})
                for item in value.values():inspect(item)
            elif isinstance(value,list):
                for item in value:inspect(item)
        inspect(metadata)


if __name__=='__main__':unittest.main()
