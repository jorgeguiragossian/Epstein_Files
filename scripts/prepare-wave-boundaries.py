"""Materialize reviewed, lossless wave partitions locally; export metadata only."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from viewer.email_boundaries import apply_boundaries
from viewer.email_parser import VERSION


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def main(folder):
    metadata = json.loads((folder / 'candidate-boundary-reviews.json').read_text(encoding='utf-8'))
    metrics = {r['file_id']: r for r in json.loads((folder / 'metrics.json').read_text())['files']}
    records, prepared, annotations = [], [], []
    seen = set()
    for review in metadata['reviews']:
        key = review['file_id']
        if key in seen:
            raise ValueError('Duplicate reviewed document')
        seen.add(key)
        value = json.loads((folder / 'extractions/header-reviewed' / (key + '.json')).read_text(encoding='utf-8'))
        if len(value['candidates']) != 1:
            raise ValueError('Re-review required after candidate count changes')
        record = value['candidates'][0]
        for field in ('id', 'file_id', 'source_sha256', 'source_page', 'source_line', 'visible_fingerprint'):
            if review[field] != record[field]:
                raise ValueError('Stale wave candidate review')
        if fingerprint(record['derived_text_layer']) != review['source_layer_sha256']:
            raise ValueError('Changed reviewed source layer')
        if review['unique_message_verified'] or review['contact_count_eligible']:
            raise ValueError('Wave review cannot enable contact counting')
        record['source_review'] = dict(review)
        extraction = value['derived_extraction']
        prepared.append((metrics[key], None, extraction, None))
        records.append(record)
        spans = []
        for entry in review.get('spans', []):
            span = dict(entry, parent_record_id=record['id'])
            lines = extraction['pages'][entry['page'] - 1]['text'].splitlines()
            span['text'] = '\n'.join(line.strip() for line in lines[entry['line_start'] - 1:entry['line_end']] if line.strip())
            if hashlib.sha256(span['text'].encode()).hexdigest() != span['text_sha256']:
                raise ValueError('Changed body span text')
            spans.append(span)
        if spans:
            annotations.append(dict(record_id=record['id'], file_id=key, source_sha256=record['source_sha256'],
                                    visible_fingerprint=record['visible_fingerprint'], spans=spans))
    catalog = dict(records=records, summary=dict(parser_version=VERSION))
    apply_boundaries(catalog, dict(parser_version=metadata['parser_version'], annotations=annotations), prepared)
    for record in catalog['records']:
        if record.get('body_partition'):
            record['flags'] = sorted((set(record['flags']) - {'quoted_body_boundary_unresolved'}) | {'body_partition_source_reviewed'})
    out = folder / 'extractions/header-reviewed/reviewed-catalog.json'
    out.write_text(json.dumps(catalog, indent=2) + '\n', encoding='utf-8')
    summary = dict(reviewed_candidates=len(records), partitioned_candidates=len(annotations),
                   lossless_body_spans=sum(len(a['spans']) for a in annotations),
                   unique_messages_verified=False, contact_rankings_ready=False,
                   source_text_publication=False, public_site_integration=False,
                   interpretation='Source-assisted header/body scope only. Native and derived parent bodies remain intact; quoted content is not promoted to additional messages.')
    (folder / 'boundary-review-summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(summary)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    main(parser.parse_args().out)
