"""Rebuild local email candidates and publish metadata-only pilot measurements."""
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'viewer'))
from email_parser import build_email_catalog


def main():
    pilot=ROOT/'data/pilot/2026-11-01'
    metrics=json.loads((pilot/'metrics.json').read_text(encoding='utf-8'))['files']
    downloads={r['file_id']:r for r in json.loads((pilot/'downloads.json').read_text(encoding='utf-8'))['files']}
    prepared=[]
    for metric in metrics:
        item=downloads[metric['file_id']]
        extracted=json.loads((pilot/metric['extraction_path']).read_text(encoding='utf-8'))
        pdf=pilot/item['local_path']
        if extracted['source_sha256']!=metric['sha256'] or hashlib.sha256(pdf.read_bytes()).hexdigest()!=metric['sha256']:
            raise ValueError('Source hash mismatch; rebuild pilot before parsing email candidates.')
        prepared.append((metric,item,extracted,pdf))
    catalog=build_email_catalog(prepared)
    folder=ROOT/'data/viewer';folder.mkdir(parents=True,exist_ok=True)
    (folder/'emails.json').write_text(json.dumps(catalog,indent=2)+'\n',encoding='utf-8')
    records={r['id']:r for r in catalog['records']}
    metadata={'summary':catalog['summary'],'metrics_sha256':hashlib.sha256((pilot/'metrics.json').read_bytes()).hexdigest(),
        'groups':[dict(g,sources=[{k:records[key][k] for k in ('id','file_id','source_sha256','source_page','source_line','flags')} for key in g['record_ids']]) for g in catalog['groups']]}
    (pilot/'email-summary.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(catalog['summary'],indent=2))


if __name__=='__main__':main()
