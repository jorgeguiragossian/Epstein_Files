"""The migration check must detect unrelated evidence or grouping changes."""
import copy
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('migration',Path(__file__).resolve().parents[1]/'scripts/check-email-date-migration.py')
migration=importlib.util.module_from_spec(spec);spec.loader.exec_module(migration)


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.before={'records':[dict(id='one',file_id='fixture',source_page=1,source_line=1,raw_date='July 1, 2020 7:00 PM',body='Original',parsed_timestamp_candidate='2020-07-01T07:00:00',flags=[])],'groups':[{'id':'group','record_ids':['one']}]}
        self.after=copy.deepcopy(self.before);self.after['summary']={'date_parser_version':'email-date-2'}
        self.after['records'][0]['parsed_timestamp_candidate']='2020-07-01T19:00:00'

    def test_records_clock_change(self):
        result=migration.compare(self.before,self.after)
        self.assertEqual(result['changed_timestamps'],1)
        self.assertTrue(result['raw_evidence_and_groups_unchanged'])

    def test_rejects_evidence_identity_flag_and_group_changes(self):
        for field in ('body','id','flags','groups'):
            value=copy.deepcopy(self.after)
            if field=='groups':value['groups']=[]
            else:value['records'][0][field]=['invented'] if field=='flags' else 'changed'
            with self.subTest(field=field),self.assertRaises(ValueError):migration.compare(self.before,value)
