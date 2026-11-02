"""Compare rebuilt dates with an explicitly supplied pre-migration email cache."""
import argparse
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def compare(before,after):
    old={r['id']:r for r in before['records']};new={r['id']:r for r in after['records']}
    if old.keys()!=new.keys():raise ValueError('Candidate identity changed during date-only migration.')
    allowed={'parsed_timestamp_candidate','flags','date_parser_version','source_review'}
    changes=[]
    for key,r in new.items():
        previous=old[key]
        if {k:v for k,v in r.items() if k not in allowed}!={k:v for k,v in previous.items() if k not in allowed}:
            raise ValueError('Non-date evidence changed: '+key)
        review_fields={'parsed_clock_conflict','source_clock_matches_candidate'}
        if {k:v for k,v in r.get('source_review',{}).items() if k not in review_fields}!={k:v for k,v in previous.get('source_review',{}).items() if k not in review_fields}:
            raise ValueError('Source review evidence changed: '+key)
        difference=set(r['flags'])^set(previous['flags'])
        if difference-{'date_unparsed','date_timezone_unspecified'}:raise ValueError('Non-date flags changed.')
        if r['parsed_timestamp_candidate']!=previous['parsed_timestamp_candidate']:
            changes.append({k:r[k] for k in ('id','file_id','source_page','source_line','raw_date')}|{
                'before':previous['parsed_timestamp_candidate'],'after':r['parsed_timestamp_candidate']})
    if before['groups']!=after['groups']:raise ValueError('Visible-copy grouping changed.')
    return {'date_parser_version':after['summary']['date_parser_version'],'candidate_occurrences':len(new),
        'changed_timestamps':len(changes),'unchanged_timestamps':len(new)-len(changes),
        'raw_evidence_and_groups_unchanged':True,'changes':changes,
        'reviewed_clock_checks':[{'id':r['id'],'source_clock_reading':r['source_review']['source_clock_reading'],
            'matches':r['source_review']['source_clock_matches_candidate']} for r in new.values() if r.get('source_review',{}).get('source_clock_reading')]}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--baseline',type=Path,required=True);args=parser.parse_args()
    result=compare(json.loads(args.baseline.read_text(encoding='utf-8')),json.loads((ROOT/'data/viewer/emails.json').read_text(encoding='utf-8')))
    (ROOT/'data/pilot/2026-11-01/email-date-migration.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
