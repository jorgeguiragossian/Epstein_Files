"""Validate pilot evidence and write aggregate measurements; no network access."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/pilot/2026-11-01'


def read(name):
    return json.loads((OUT / name).read_text(encoding='utf-8'))


selection = read('selection.json')
downloads = read('downloads.json')['files']
metrics = read('metrics.json')['files']
assert len(selection['files']) == len(downloads) == len(metrics) == 100
assert {r['url'] for r in selection['files']} == {r['url'] for r in downloads} == {r['url'] for r in metrics}
for item in downloads:
    assert item['status'] == 'downloaded', item['file_id']
    path = OUT / item['local_path']
    assert path.stat().st_size == item['bytes']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256']
for item in metrics:
    assert item['status'] == 'extracted', item['file_id']
    extraction = read(item['extraction_path'])
    assert extraction['source_sha256'] == item['sha256']
    assert item['page_count'] == item['pages_processed'] == len(extraction['pages'])
    assert [p['page'] for p in extraction['pages']] == list(range(1, item['page_count'] + 1))
    assert item['characters'] == sum(len(p['text']) for p in extraction['pages'])
    assert item['document_date'] is None
    assert all(not d['validated'] and 1 <= d['page'] <= item['page_count'] for d in item['date_candidates'])
    assert item['email_header_candidate_count'] == len(extraction['email_header_candidates'])
summary = {
    'sample_documents': len(metrics), 'datasets': len({r['dataset'] for r in metrics}),
    'downloaded_bytes': sum(r['bytes'] for r in downloads),
    'minimum_document_bytes': min(r['bytes'] for r in downloads),
    'maximum_document_bytes': max(r['bytes'] for r in downloads),
    'pdf_pages': sum(r['page_count'] for r in metrics),
    'pages_processed': sum(r['pages_processed'] for r in metrics),
    'low_text_pages': sum(r['low_text_pages'] for r in metrics),
    'zero_alphanumeric_text_pages': sum(r['zero_text_pages'] for r in metrics),
    'documents_with_low_text_pages': sum(r['low_text_pages'] > 0 for r in metrics),
    'documents_with_only_low_text_pages': sum(r['low_text_pages'] == r['page_count'] for r in metrics),
    'date_candidate_occurrences': sum(r['date_candidate_count'] for r in metrics),
    'documents_with_date_candidates': sum(r['date_candidate_count'] > 0 for r in metrics),
    'email_header_candidate_blocks': sum(r['email_header_candidate_count'] for r in metrics),
    'documents_with_email_header_candidates': sum(r['email_header_candidate_count'] > 0 for r in metrics),
    'exact_duplicate_sha256_groups': sum(n > 1 for n in Counter(r['sha256'] for r in metrics).values()),
    'word_tokens_english_regex': sum(r['word_tokens'] for r in metrics),
    'ocr_performed': False, 'source_hashes_and_page_evidence_verified': True,
    'scope_warning': 'Non-random, first-page-biased sample. Low text is a review flag, not an OCR diagnosis. Dates and header blocks are unvalidated; header counts are not contact counts.'
}
(OUT / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
rows = []
for dataset in range(1, 13):
    group = [r for r in metrics if r['dataset'] == dataset]
    rows.append({'dataset': dataset, 'documents': len(group), 'pages': sum(r['page_count'] for r in group),
        'bytes': sum(r['bytes'] for r in group), 'low_text_pages': sum(r['low_text_pages'] for r in group),
        'documents_with_date_candidates': sum(r['date_candidate_count'] > 0 for r in group),
        'email_header_candidate_blocks': sum(r['email_header_candidate_count'] for r in group)})
with (OUT / 'dataset-summary.csv').open('w', encoding='utf-8', newline='') as stream:
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
print(json.dumps(summary, indent=2))
