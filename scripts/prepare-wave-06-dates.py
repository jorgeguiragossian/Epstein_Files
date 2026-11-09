"""Materialize source-bound uncertain date reviews for photographs and handwritten log."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from viewer.server import validate_review

FOLDER = ROOT/'data/pilot/2026-11-08-wave-06'
ASSIGNMENTS = [('EFTA00000002',
  None,
  None,
  'EFTA00000002',
  None,
  'Single-page photograph: no visible capture or issue date is established. Source stamp is an identifier, '
  'not a date. Do not infer a date from neighboring files, visual appearance, incidental objects or the '
  'separate photographic log.'),
 ('EFTA00000356',
  None,
  None,
  'EFTA00000356',
  None,
  'Single-page photograph: no visible capture or issue date is established. Source stamp is an identifier, '
  'not a date. Do not infer a date from neighboring files, visual appearance, incidental objects or the '
  'separate photographic log.'),
 ('EFTA00000708',
  None,
  None,
  'EFTA00000708',
  None,
  'Single-page photograph: no visible capture or issue date is established. Source stamp is an identifier, '
  'not a date. Do not infer a date from neighboring files, visual appearance, incidental objects or the '
  'separate photographic log.'),
 ('EFTA00001057',
  None,
  None,
  'EFTA00001057',
  None,
  'Single-page photograph: no visible capture or issue date is established. Source stamp is an identifier, '
  'not a date. Do not infer a date from neighboring files, visual appearance, incidental objects or the '
  'separate photographic log.'),
 ('EFTA00001407',
  None,
  None,
  'EFTA00001407',
  None,
  'Single-page photograph: no visible capture or issue date is established. Source stamp is an identifier, '
  'not a date. Do not infer a date from neighboring files, visual appearance, incidental objects or the '
  'separate photographic log.'),
 ('EFTA00001756',
  None,
  None,
  'EFTA00001756',
  None,
  'Single-page photograph: no visible capture or issue date is established. Source stamp is an identifier, '
  'not a date. Do not infer a date from neighboring files, visual appearance, incidental objects or the '
  'separate photographic log.'),
 ('EFTA00002109',
  None,
  None,
  'EFTA00002109',
  None,
  'Single-page photograph: no visible capture or issue date is established. Source stamp is an identifier, '
  'not a date. Do not infer a date from neighboring files, visual appearance, incidental objects or the '
  'separate photographic log.'),
 ('EFTA00002459',
  None,
  None,
  'EFTA00002459',
  None,
  'Single-page photograph: no visible capture or issue date is established. Source stamp is an identifier, '
  'not a date. Do not infer a date from neighboring files, visual appearance, incidental objects or the '
  'separate photographic log.'),
 ('EFTA00002809',
  None,
  None,
  'EFTA00002809',
  None,
  'Single-page photograph: no visible capture or issue date is established. Source stamp is an identifier, '
  'not a date. Do not infer a date from neighboring files, visual appearance, incidental objects or the '
  'separate photographic log.'),
 ('EFTA00003158',
  None,
  None,
  'EFTA00003158',
  None,
  'Photographed handwritten log: a numeric handwritten DATE entry is visible, but normalized day/date '
  'interpretation and its role as log creation versus photo capture are not established in this scoped '
  'review. Native text and local OCR are inadequate for the handwritten field. No provisional date literal '
  'is published or promoted, and log row numbers do not establish links to these PDFs. Retain an uncertain '
  'primary date pending a dedicated field-level source adjudication.')]


def main():
    read = lambda p: json.loads(p.read_text(encoding='utf-8'))
    metrics = {m['file_id']: m for m in read(FOLDER/'metrics.json')['files']}
    downloads = {d['file_id']: d for d in read(FOLDER/'downloads.json')['files']}
    quality = {r['file_id']: r for r in read(FOLDER/'quality-review.json')['files']}
    reviews = []
    for key, day, role, quote, source_reading, notes in ASSIGNMENTS:
        metric = metrics[key]
        extracted = read(FOLDER/metric['extraction_path'])
        page_text = extracted['pages'][0]['text']
        if (hashlib.sha256((FOLDER/downloads[key]['local_path']).read_bytes()).hexdigest() != metric['sha256']
                or extracted['source_sha256'] != metric['sha256']
                or quality[key]['source_sha256'] != metric['sha256']
                or hashlib.sha256(page_text.encode()).hexdigest() != quality[key]['inspected_page_text_sha256']['1']):
            raise ValueError('Changed source/native evidence; re-review required')
        row = dict(file_id=key, dataset=1, source_sha256=metric['sha256'],
                   status='dated' if day else 'uncertain', primary_date=day,
                   date_type=role, precision='day' if day else None,
                   evidence_page=1, evidence_quote=quote, notes=notes,
                   review_method='Codex visual comparison of PDF page 1 with native UTF-8 extraction; same-assistant editorial date assignment, not independent authentication',
                   timezone_policy='Use the calendar day displayed in the source; no timezone inference or conversion.',
                   inspected_pdf_pages=[1],
                   supporting_evidence=[dict(pdf_page=1, quote=quote, native_text_sha256=hashlib.sha256(page_text.encode()).hexdigest())])
        if source_reading:
            row['source_date_reading'] = source_reading
            row['notes'] += ' Source header reading: ' + source_reading + '. No timezone is inferred.'
        validate_review(row, metric, extracted)
        reviews.append(row)
    target = FOLDER/'date-reviews.json'
    target.write_text(json.dumps(dict(schema_version=1, reviewed_on='2026-11-08',
        scope='Ten wave 6 PDFs: nine photographs and one handwritten log retain uncertain primary dates. No new briefs or native email repairs.', reviews=reviews), indent=2)+'\n', encoding='utf-8')
    path = ROOT/'data/pilot/viewer-batches.json'
    registry = read(path)
    next(b for b in registry['batches'] if b['path'] == FOLDER.relative_to(ROOT).as_posix())['evidence_sha256']['date-reviews.json'] = hashlib.sha256(target.read_bytes()).hexdigest()
    path.write_text(json.dumps(registry, indent=2)+'\n', encoding='utf-8')
    print('Prepared ten uncertain primary-date reviews; no date cohort promotion.')


if __name__ == '__main__':
    main()
