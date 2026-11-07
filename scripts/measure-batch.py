"""Validate source/extraction evidence and summarize a bounded acquisition batch."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def summarize(folder, baseline=None):
    selection = read(folder / 'selection.json')['files']
    downloads = read(folder / 'downloads.json')['files']
    metrics = read(folder / 'metrics.json')['files']
    expected = {row['url'] for row in selection}
    if len(expected) != len(selection) or any(len(rows) != len(expected) or {r['url'] for r in rows} != expected for rows in (downloads, metrics)):
        raise ValueError('Batch URL coverage does not match selection')
    by_url = {row['url']: row for row in downloads}
    successful = []
    for row in metrics:
        download = by_url[row['url']]
        if download['status'] == 'downloaded':
            path = folder / download['local_path']
            if path.stat().st_size != download['bytes'] or hashlib.sha256(path.read_bytes()).hexdigest() != download['sha256']:
                raise ValueError('Cached source hash/size mismatch: ' + row['file_id'])
        if row['status'] != 'extracted':
            continue
        if download['status'] != 'downloaded' or row['sha256'] != download['sha256']:
            raise ValueError('Extraction without matching source')
        extracted = read(folder / row['extraction_path'])
        pages = extracted['pages']
        if any(row.get(key) != value for key, value in extracted['metrics'].items()):
            raise ValueError('Metrics differ from extraction evidence')
        if extracted['source_sha256'] != row['sha256']:
            raise ValueError('Extraction source hash mismatch')
        if not row['page_count'] == row['pages_processed'] == len(pages) or [p['page'] for p in pages] != list(range(1, len(pages) + 1)):
            raise ValueError('Page count or ordering mismatch')
        if row['characters'] != sum(len(p['text']) for p in pages):
            raise ValueError('Character count mismatch')
        if row['low_text_pages'] != sum(p['low_text_candidate'] for p in pages):
            raise ValueError('Low-text count mismatch')
        if row['page_metrics'] != [{k: v for k, v in p.items() if k not in ('text', 'date_candidates')} for p in pages]:
            raise ValueError('Page metrics differ from extraction evidence')
        if row['email_header_candidate_count'] != len(extracted['email_header_candidates']):
            raise ValueError('Header candidate count mismatch')
        if row['date_candidate_count'] != len(row['date_candidates']) or row['document_date'] is not None or any(d['validated'] or not 1 <= d['page'] <= len(pages) for d in row['date_candidates']):
            raise ValueError('Native extraction must not imply reviewed dates')
        successful.append(row)
    prior = read(baseline)['files'] if baseline else []
    prior_hashes = {r['sha256'] for r in prior if r.get('sha256')}
    duplicates = Counter(r['sha256'] for r in successful)
    low_pages = [dict(file_id=r['file_id'], page=p['page']) for r in successful for p in r['page_metrics'] if p['low_text_candidate']]
    return dict(selected_files=len(selection), downloaded_files=sum(r['status'] == 'downloaded' for r in downloads),
                extracted_files=len(successful), download_status_counts=dict(Counter(r['status'] for r in downloads)),
                extraction_status_counts=dict(Counter(r['status'] for r in metrics)),
                downloaded_bytes=sum(r.get('bytes', 0) for r in downloads if r['status'] == 'downloaded'),
                pdf_pages=sum(r['page_count'] for r in successful), low_text_pages=low_pages,
                zero_alphanumeric_text_pages=sum(r['zero_text_pages'] for r in successful),
                email_header_candidate_blocks=sum(r['email_header_candidate_count'] for r in successful),
                documents_with_email_header_candidates=sum(r['email_header_candidate_count'] > 0 for r in successful),
                date_candidate_occurrences=sum(r['date_candidate_count'] for r in successful),
                exact_duplicate_source_hash_groups_within_batch=sum(n > 1 for n in duplicates.values()),
                source_hashes_matching_baseline=[r['file_id'] for r in successful if r['sha256'] in prior_hashes],
                source_hashes_and_page_evidence_verified=True, ocr_performed=False,
                interpretation='Native-text extraction only. Low text is a review flag, not an OCR diagnosis. Header/date candidates are unvalidated and not message/contact counts. No automatic public-site integration.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, default=ROOT / 'data/pilot/2026-11-01/metrics.json')
    args = parser.parse_args()
    value = summarize(args.out, args.baseline)
    (args.out / 'summary.json').write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(value, indent=2))
