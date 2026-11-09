"""Materialize source-bound uncertain date reviews for photograph pages with absent or partial dates."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from viewer.server import validate_review

FOLDER = ROOT/'data/pilot/2026-11-08-wave-07'
ASSIGNMENTS = [('EFTA00003160',
  None,
  None,
  'EFTA00003160',
  None,
  'Photographic page has no established complete capture/issue date. Source stamp identifies the page, not '
  'its date. Do not date the photograph from appearance, neighboring records or PDF/file order.'),
 ('EFTA00003324',
  None,
  None,
  'EFTA00003324',
  None,
  'Photographic page has no established complete capture/issue date. Source stamp identifies the page, not '
  'its date. Do not date the photograph from appearance, neighboring records or PDF/file order.'),
 ('EFTA00003388',
  None,
  None,
  'EFTA00003388',
  None,
  'Photographic page has no established complete capture/issue date. Source stamp identifies the page, not '
  'its date. Do not date the photograph from appearance, neighboring records or PDF/file order.'),
 ('EFTA00003458',
  None,
  None,
  'EFTA00003458',
  None,
  'Photographic page has no established complete capture/issue date. Source stamp identifies the page, not '
  'its date. Do not date the photograph from appearance, neighboring records or PDF/file order.'),
 ('EFTA00003520',
  None,
  None,
  'EFTA00003520',
  None,
  'Photographic page has no established complete capture/issue date. Source stamp identifies the page, not '
  'its date. Do not date the photograph from appearance, neighboring records or PDF/file order.'),
 ('EFTA00003601',
  None,
  None,
  'EFTA00003601',
  None,
  'Both PDF pages inspected. Visually similar image presentations do not establish a capture/issue date, '
  'chronology or verified duplicate status. No complete calendar date is established; preserve both pages '
  'and their source order.'),
 ('EFTA00003664',
  None,
  None,
  'EFTA00003664',
  None,
  'Photographic page has no established complete capture/issue date. Source stamp identifies the page, not '
  'its date. Do not date the photograph from appearance, neighboring records or PDF/file order.'),
 ('EFTA00003726',
  None,
  None,
  'EFTA00003726',
  None,
  'Partial camera overlay contains a day-number/time fragment but no complete month/year/calendar date. '
  'Native text omits the overlay. Camera clock accuracy and timezone are not established. Do not infer '
  'missing date components or assign a primary day from this fragment.'),
 ('EFTA00003792',
  None,
  None,
  'EFTA00003792',
  None,
  'Partial camera overlay contains a day-number/time fragment but no complete month/year/calendar date. '
  'Native text omits the overlay. Camera clock accuracy and timezone are not established. Do not infer '
  'missing date components or assign a primary day from this fragment.'),
 ('EFTA00003857',
  None,
  None,
  'EFTA00003857',
  None,
  'Photographic page has no established complete capture/issue date. Source stamp identifies the page, not '
  'its date. Do not date the photograph from appearance, neighboring records or PDF/file order.')]


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
        row = dict(file_id=key, dataset=2, source_sha256=metric['sha256'],
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
        row['inspected_pdf_pages'] = [p['page'] for p in extracted['pages']]
        row['review_method'] = 'Codex visual comparison of all cited photograph PDF pages with native UTF-8 extraction; editorial date assessment, not independent authentication'
        for page in extracted['pages'][1:]:
            expected=quality[key]['inspected_page_text_sha256'][str(page['page'])]
            if hashlib.sha256(page['text'].encode()).hexdigest()!=expected:
                raise ValueError('Changed reviewed continuation page')
            row['supporting_evidence'].append(dict(pdf_page=page['page'],quote=page['text'].strip(),native_text_sha256=expected))
        validate_review(row, metric, extracted)
        reviews.append(row)
    target = FOLDER/'date-reviews.json'
    target.write_text(json.dumps(dict(schema_version=1, reviewed_on='2026-11-08',
        scope='Ten wave 7 photograph PDFs retain uncertain primary dates; two have incomplete camera overlays. No new briefs or native email repairs.', reviews=reviews), indent=2)+'\n', encoding='utf-8')
    path = ROOT/'data/pilot/viewer-batches.json'
    registry = read(path)
    next(b for b in registry['batches'] if b['path'] == FOLDER.relative_to(ROOT).as_posix())['evidence_sha256']['date-reviews.json'] = hashlib.sha256(target.read_bytes()).hexdigest()
    path.write_text(json.dumps(registry, indent=2)+'\n', encoding='utf-8')
    print('Prepared ten uncertain primary-date reviews; no date cohort promotion.')


if __name__ == '__main__':
    main()
