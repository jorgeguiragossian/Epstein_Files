"""Materialize source-bound receipt/date-role reviews with bounded album uncertainty."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from viewer.server import validate_review

FOLDER = ROOT/'data/pilot/2026-11-08-wave-08'
ASSIGNMENTS = [('EFTA00003434',
  None,
  None,
  'EFTA00003434',
  None,
  'Photograph has no established complete capture/issue date. Source stamp identifies a page, not a day. No '
  'image/neighboring-file date inference.'),
 ('EFTA00003858',
  None,
  None,
  'EFTA00003858',
  None,
  'Four-page item/package record: scanned object, item-not-scanned placeholder and package images. Template '
  'revision and product copyright are distinct from record creation/acquisition. No single primary issue '
  'date established.'),
 ('EFTA00003931',
  None,
  None,
  'ITEM',
  None,
  'Placeholder and framed photograph: template revision dates the form version, not the object/photo/record '
  'issue. No complete primary date established.'),
 ('EFTA00004012',
  None,
  None,
  'Date :',
  None,
  'Only PDF pages 1/14/27 visually inspected. Photo-processing sleeve date field is blank; sampled photos do '
  'not establish album assembly/issue/capture date. Not a whole-album date review.'),
 ('EFTA00004060',
  None,
  None,
  'EFTA00004060',
  None,
  'Publication/advertisement covers and reverse sides. Month, anniversary and weekly promotion text do not '
  'establish a full primary day. No year/day inferred from publication styling or marketing claims.'),
 ('EFTA00004231',
  '2020-07-17',
  'evidence_received',
  'Date Received',
  '7/17/20',
  'Handwritten Date Received row reads 7/17/20, interpreted as July 17, 2020 in the contemporary US '
  'evidence-receipt context. This is the recorded receipt-handling date for the evidence record, not photo '
  'capture, media creation or authenticated chain of custody. Form revision and item-not-scanned template '
  'revision are separate. Native date text remains damaged and unchanged.'),
 ('EFTA00004577',
  None,
  None,
  'EFTA00004577',
  None,
  'Only PDF pages 1/43/86 visually inspected. Contact-sheet filenames/captions and disc label do not '
  'establish a single assembly/issue date or dates of every image/media item. No date inferred from '
  'caption/filename fragments; not full-album review.'),
 ('EFTA00005091',
  None,
  None,
  'BOOK 20',
  None,
  'Only PDF pages 1/50/100 visually inspected. Index labels contain year/month/event-like fragments, not a '
  'single established issue/assembly day. Disc labels and contact sheets do not establish photo/media dates '
  'or contents; no forced day precision.'),
 ('EFTA00005536',
  None,
  None,
  'Looking',
  None,
  'Two redacted image/publication pages have no established complete issue/assembly/capture date. '
  'Title/appearance is not a date. Redacted content is not reconstructed.'),
 ('EFTA00005586',
  None,
  None,
  'Grand Jury-NY',
  None,
  'Only PDF pages 1/60/119 visually inspected. Blacked-out content and Grand Jury-NY labels/stamps do not '
  'establish a full primary day. Do not infer hidden dates or hearing/filing status; not review of all 119 '
  'source pages.')]


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
        row = dict(file_id=key, dataset=3, source_sha256=metric['sha256'],
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
        row['inspected_pdf_pages'] = quality[key]['visually_inspected_pdf_pages']
        row['review_method'] = 'Codex scoped source comparison of cited PDF pages with native UTF-8 evidence and prior quality/OCR review; editorial date adjudication, not authentication'
        for number in row['inspected_pdf_pages'][1:]:
            text=extracted['pages'][number-1]['text']
            expected=quality[key]['inspected_page_text_sha256'][str(number)]
            if hashlib.sha256(text.encode()).hexdigest()!=expected:
                raise ValueError('Changed reviewed supporting page')
            row['supporting_evidence'].append(dict(pdf_page=number,quote=text.strip(),native_text_sha256=expected))
        validate_review(row, metric, extracted)
        reviews.append(row)
    target = FOLDER/'date-reviews.json'
    target.write_text(json.dumps(dict(schema_version=1, reviewed_on='2026-11-09',
        scope='Ten wave 8 PDFs: one evidence-received date and nine uncertain primary dates; bounded album review preserved. No new briefs or native email repairs.', reviews=reviews), indent=2)+'\n', encoding='utf-8')
    path = ROOT/'data/pilot/viewer-batches.json'
    registry = read(path)
    next(b for b in registry['batches'] if b['path'] == FOLDER.relative_to(ROOT).as_posix())['evidence_sha256']['date-reviews.json'] = hashlib.sha256(target.read_bytes()).hexdigest()
    path.write_text(json.dumps(registry, indent=2)+'\n', encoding='utf-8')
    print('Prepared one evidence-received date and nine uncertain reviews.')


if __name__ == '__main__':
    main()
