"""Validate source-bound native correspondence reviews; keep text in ignored caches."""
import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from viewer.email_parser import parse_document, VERSION, DATE_VERSION
from viewer.email_boundaries import apply_boundaries


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def build_catalog(folder):
    metadata = read(folder/'correspondence-reviews.json')
    if metadata['parser_version'] != VERSION or metadata['date_parser_version'] != DATE_VERSION:
        raise ValueError('Parser changed; re-review correspondence')
    metrics = read(folder/'metrics.json')['files']
    downloads = {r['url']:r for r in read(folder/'downloads.json')['files']}
    records, prepared = [], []
    for metric in metrics:
        item = downloads[metric['url']]
        pdf = folder/item['local_path']
        extraction = read(folder/metric['extraction_path'])
        if (hashlib.sha256(pdf.read_bytes()).hexdigest() != metric['sha256']
                or item['sha256'] != metric['sha256'] or extraction['source_sha256'] != metric['sha256']
                or len(extraction['pages']) != metric['page_count']):
            raise ValueError('Changed correspondence source bytes or extraction binding')
        prepared.append((metric,item,extraction,pdf))
        records.extend(parse_document(extraction,metric['file_id'],metric['dataset'],metric['sha256']))
    by_id = {r['id']:r for r in records}
    sources = {m['file_id']:x for m,item,x,pdf in prepared}
    seen, annotations = set(), []
    for review in metadata['reviews']:
        key = review['record_id']
        if key in seen or key not in by_id:
            raise ValueError('Duplicate or unknown reviewed candidate')
        seen.add(key)
        record = by_id[key]
        for field in ('file_id','source_sha256','source_page','source_line','visible_fingerprint'):
            if review[field] != record[field]:
                raise ValueError('Stale correspondence review')
        if review['unique_message_verified'] or review['contact_count_eligible']:
            raise ValueError('Editorial scope cannot establish unique messages or contact counts')
        extraction = sources[record['file_id']]
        for evidence in review['page_evidence']:
            number = evidence['pdf_page']
            if not isinstance(number,int) or not 1 <= number <= len(extraction['pages']):
                raise ValueError('Invalid review page')
            text = extraction['pages'][number-1]['text']
            if hashlib.sha256(text.encode()).hexdigest() != evidence['native_text_sha256']:
                raise ValueError('Changed reviewed native page')
        if record['source_page'] not in {e['pdf_page'] for e in review['page_evidence']}:
            raise ValueError('Review requires candidate source page evidence')
        if review.get('coverage') == 'detected_header_and_body_pages':
            required = {record['source_page'], *record['body_pages'],
                        *(h['page'] for h in record['header_evidence'])}
            if not required <= {e['pdf_page'] for e in review['page_evidence']}:
                raise ValueError('Review must cover all detected header and body pages')
            if review.get('detected_body_sha256') != hashlib.sha256(record['body'].encode()).hexdigest():
                raise ValueError('Changed reviewed detected body')
        record['source_review'] = dict(review)
        if review.get('spans'):
            spans = []
            for entry in review['spans']:
                lines = extraction['pages'][entry['page']-1]['text'].splitlines()
                text = '\n'.join(line.strip() for line in lines[entry['line_start']-1:entry['line_end']] if line.strip())
                spans.append(dict(entry,parent_record_id=key,text=text))
            annotation = dict(record_id=key,file_id=record['file_id'],source_sha256=record['source_sha256'],
                              visible_fingerprint=record['visible_fingerprint'],spans=spans)
            if review.get('following_quoted_candidate_id'):
                annotation['following_quoted_candidate_id'] = review['following_quoted_candidate_id']
            annotations.append(annotation)
    catalog = dict(records=records,summary=dict(parser_version=VERSION))
    apply_boundaries(catalog,dict(parser_version=VERSION,annotations=annotations),prepared)
    summary = dict(candidate_occurrences=len(records),reviewed_candidates=len(seen),
                   unreviewed_candidates=len(records)-len(seen),body_partitions=len(annotations),
                   header_status_counts=dict(Counter(r['source_review'].get('header_status','unspecified') for r in records if r.get('source_review'))),
                   boundary_status_counts=dict(Counter(r['source_review'].get('boundary_status','unspecified') for r in records if r.get('source_review'))),
                   unique_messages=None,contact_rankings_ready=False,
                   public_site_integration=read(folder/'processing-status.json').get('public_search_integration',False) if (folder/'processing-status.json').exists() else False,
                   parser_version=VERSION,date_parser_version=DATE_VERSION,
                   scope=metadata.get('scope','Scoped candidate reviews; native fields and bodies preserved; no primary dates assigned.'))
    return catalog, summary


def main(folder):
    catalog, summary = build_catalog(folder)
    target = folder/'extractions/correspondence-reviewed'
    target.mkdir(parents=True,exist_ok=True)
    (target/'catalog.json').write_text(json.dumps(catalog,indent=2)+'\n',encoding='utf-8')
    (folder/'correspondence-review-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    main(parser.parse_args().out)
