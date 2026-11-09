"""Materialize source-reviewed issue/sent dates without assigning a compound-file date."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from viewer.server import validate_review

FOLDER = ROOT/'data/pilot/2026-11-08-wave-05'
ASSIGNMENTS = [('EFTA02730267',
  '2022-02-14',
  'report',
  '14 February 2022',
  None,
  'Report issue date in the heading. Template effective date October 1, 2021 and referenced case/event dates '
  'are separate; do not use the template date.'),
 ('EFTA02731200',
  '2020-04-14',
  'report',
  'April 14, 2020',
  None,
  'Memorandum issue date in the first-page heading, not a prosecution outcome or date of every incident '
  'discussed. Redactions remain unchanged.'),
 ('EFTA02731477',
  '2023-06-12',
  'email_sent',
  'Monday. June 12.2023 1:59 PM',
  None,
  'Outer Sent row, displaced below native labels. Quoted 1:53 PM message is separate; no native clock or '
  'header repair.'),
 ('EFTA02731511',
  '2024-03-07',
  'email_sent',
  'Date: Thursday, March 7, 2024 7:10:20 PM',
  None,
  'Outer Date row. Attachment titles and Year 18 text are not primary dates or proof that attachments were '
  'separately acquired.'),
 ('EFTA02731593',
  '2023-06-22',
  'email_sent',
  'Date: Thursday,',
  'Thursday, June 22, 2023 8:20:45 AM',
  'Outer Date row clearly readable in source, severely damaged and displaced in native text. June 21 '
  'inline/quoted timestamps and later pages of earlier messages are distinct; native fields remain '
  'unchanged.'),
 ('EFTA02731646',
  '2021-08-24',
  'email_sent',
  'Date: Tuesday, August 24, 2021 10:50:11 NI',
  None,
  'Outer Date row supplies August 24 despite damaged native AM marker. August 17 quoted message and '
  'prospective end-of-year contact are separate. No native repair.'),
 ('EFTA02731708',
  None,
  None,
  'EFTA02731708',
  None,
  'One-page photograph with source stamp only and no visible date. Capture/issue date is not established; do '
  'not infer it from adjacent files, image appearance or filename.'),
 ('EFTA02731736',
  '2023-06-28',
  'email_sent',
  'Wednesday. June 28. 2023 2:',
  None,
  'Outer Sent calendar day is legible in source despite truncated native clock and displaced values. Quoted '
  'June 12 message is separate; no missing clock value is inferred.'),
 ('EFTA02857524',
  None,
  None,
  'May 1, 2007',
  None,
  'Compound PDF contains original/revised memorandum, addenda, amendment dates and indictment-form material. '
  'No assembly/issue date for the entire compound file is established. Do not promote the opening May 1 '
  'date, latest amendment or an event/table date to one primary date for all components. See bounded '
  'component assessment; this is not full-content review.'),
 ('EFTA02858497',
  '2019-07-08',
  'report',
  'Date: 07/08/2019',
  None,
  'Crisis intake Date row is July 8 in the displayed US context, consistent with received timestamp and '
  'Monday reference. Template revision and alleged historic events are separate. This dates the intake '
  'report, not its allegations.')]


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
        row = dict(file_id=key, dataset=12, source_sha256=metric['sha256'],
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
        scope='Ten wave 5 PDFs: eight issue/sent dates; photograph and compound file uncertain. No new briefs or native email repairs.', reviews=reviews), indent=2)+'\n', encoding='utf-8')
    path = ROOT/'data/pilot/viewer-batches.json'
    registry = read(path)
    next(b for b in registry['batches'] if b['path'] == FOLDER.relative_to(ROOT).as_posix())['evidence_sha256']['date-reviews.json'] = hashlib.sha256(target.read_bytes()).hexdigest()
    path.write_text(json.dumps(registry, indent=2)+'\n', encoding='utf-8')
    print('Prepared eight dated and two uncertain source-bound reviews.')


if __name__ == '__main__':
    main()
