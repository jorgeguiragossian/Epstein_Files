"""Validate source-bound layout/date-role observations, without creating a ledger."""
import argparse
import hashlib
import json
from datetime import date
from pathlib import Path

ROLES={'application_signature_date','court_order_signature_date','form_version_marker','document_year',
       'preliminary_print_timestamp','planned_settlement_date','statement_reporting_period',
       'portfolio_as_of_date','transaction_reporting_period','handwritten_date_unresolved'}


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def validate(folder):
    review=read(folder/'table-date-role-reviews.json')
    metrics={r['file_id']:r for r in read(folder/'metrics.json')['files']}
    downloads={r['file_id']:r for r in read(folder/'downloads.json')['files']}
    rows=review['reviews']
    if len({r['file_id'] for r in rows})!=len(rows) or {r['file_id'] for r in rows}!=set(metrics):
        raise ValueError('Duplicate or incomplete layout/date review coverage')
    page_count=0;observations=0
    for row in rows:
        key=row['file_id'];metric=metrics[key];item=downloads[key]
        if (hashlib.sha256((folder/item['local_path']).read_bytes()).hexdigest()!=row['source_sha256']
                or metric['sha256']!=row['source_sha256'] or item['sha256']!=row['source_sha256']):
            raise ValueError('Changed layout/date source PDF')
        extraction=read(folder/metric['extraction_path'])
        if extraction['source_sha256']!=row['source_sha256'] or len(extraction['pages'])!=metric['page_count']:
            raise ValueError('Changed layout/date extraction binding')
        evidence={p['pdf_page']:p for p in row['page_evidence']}
        if len(evidence)!=len(row['page_evidence']) or set(evidence)!=set(range(1,metric['page_count']+1)):
            raise ValueError('Review must cover every PDF page')
        for n,entry in evidence.items():
            text=extraction['pages'][n-1]['text']
            if hashlib.sha256(text.encode()).hexdigest()!=entry['native_text_sha256']:
                raise ValueError('Changed reviewed table/date page')
        page_count+=len(evidence)
        if any(row['eligibility'].values()):
            raise ValueError('Layout/date-role review cannot promote a ledger, identity or primary date')
        for observation in row['date_observations']:
            if observation['role'] not in ROLES:
                raise ValueError('Unsupported date role')
            n=observation['pdf_page'];quote=observation['native_quote']
            if n not in evidence or not quote or quote not in extraction['pages'][n-1]['text']:
                raise ValueError('Date-role evidence absent from cited page')
            if observation.get('normalized_day'):
                date.fromisoformat(observation['normalized_day'])
            if observation.get('period_start') or observation.get('period_end'):
                start=date.fromisoformat(observation['period_start']);end=date.fromisoformat(observation['period_end'])
                if start>end:
                    raise ValueError('Reversed reporting period')
            observations+=1
        for anchor in row['layout_evidence']:
            n=anchor['pdf_page']
            if n not in evidence or not anchor['native_quote'] or anchor['native_quote'] not in extraction['pages'][n-1]['text']:
                raise ValueError('Layout evidence absent from cited page')
    return dict(documents_reviewed=len(rows),pdf_pages_reviewed=page_count,date_role_observations=observations,
                structured_financial_data_verified=False,primary_dates_assigned=False,native_text_replaced=False,
                public_site_integration=read(folder/'processing-status.json').get('public_search_integration',False) if (folder/'processing-status.json').exists() else False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    print(json.dumps(validate(parser.parse_args().out),indent=2))
