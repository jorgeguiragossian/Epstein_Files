"""Materialize visually reviewed outer sent dates, keeping calendar alerts uncertain."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from viewer.server import validate_review

FOLDER = ROOT/'data/pilot/2026-11-08-wave-04'
ASSIGNMENTS = [
    ('EFTA02212883', '2017-05-30', 'Sent Tue 5/3012017 12:05:38 PM',
     'Tue 5/30/2017 12:05:38 PM',
     'Outer Sent row is legible in the PDF; native text loses the slash before the year. Earlier inline/forwarded timestamps are separate. No native timestamp repair.'),
    ('EFTA02213471', '2017-05-19', 'Sent 9/2017 1:35:02 PM',
     'Fri 5/19/2017 1:35:02 PM',
     'Outer Sent row is legible in the PDF, although the native text loses weekday/month and part of the day. The source reading supplies the editorial day; native fields remain damaged and unchanged.'),
    ('EFTA02213987', None, 'June 10, 2017 : Larry in 7J June 10-16', None,
     'Calendar alert: the displayed June 10 event text and June 10-16 range do not establish a sent or issue date. No separate primary document date is visible; do not promote the event day.'),
    ('EFTA02214639', '2017-06-09', 'Fri 6/9/2017 5:41:46 PM', None,
     'Outer Sent row. Native sender/date/subject values are displaced below labels, but the source date is clear. The earlier quoted same-day exchange and disclaimer copyright year are separate.'),
    ('EFTA02215291', '2017-06-12', 'Sent Mon 6/12/2017 11:40:30 AM', None,
     'Outer Sent row; June 15 schedule dates and the quoted earlier message are separate. Known body-order mismatch remains unresolved and does not obscure the visible outer header.'),
    ('EFTA02215926', '2017-06-14', 'Sent: Wed 6/14/2017 6:28:06 PM', None,
     'Outer Sent row. June 8 quoted messages and future training/travel date ranges are separate. Damaged nested headers do not change this outer date.'),
    ('EFTA02216544', None, 'June 16, 2017 5:00 AM : Can Jude Hess see JE today around 12/12:30?', None,
     'Calendar alert: displayed event/reminder timestamp is not a separately established sent or issue date. No primary date assignment from this timestamp; redacted participants remain unresolved.'),
    ('EFTA02217241', '2017-06-16', 'Fri 6/16/2017 11:41:52 AM', None,
     'Outer Sent row is legible despite native label/value displacement. Earlier inline and forwarded timestamps are distinct; unresolved trailing material remains unchanged.'),
    ('EFTA02217799', '2017-07-12', 'Wed 7/12/2017 12:22:55 PM', None,
     'Outer Sent row. The subject/body 5pm appointment and earlier inline quoted timestamps are not the primary sent timestamp.'),
    ('EFTA02218280', '2017-07-31', 'Sent: Mon 7/31/2017 4:04:50 PM', None,
     'Outer Sent row. Relative future Wednesday/Thursday appointment requests are separate; no event date or participant identity is inferred.'),
]


def main():
    read = lambda p: json.loads(p.read_text(encoding='utf-8'))
    metrics = {m['file_id']: m for m in read(FOLDER/'metrics.json')['files']}
    downloads = {d['file_id']: d for d in read(FOLDER/'downloads.json')['files']}
    quality = {r['file_id']: r for r in read(FOLDER/'quality-review.json')['files']}
    reviews = []
    for key, day, quote, source_reading, notes in ASSIGNMENTS:
        metric = metrics[key]
        extracted = read(FOLDER/metric['extraction_path'])
        page_text = extracted['pages'][0]['text']
        if (hashlib.sha256((FOLDER/downloads[key]['local_path']).read_bytes()).hexdigest() != metric['sha256']
                or extracted['source_sha256'] != metric['sha256']
                or quality[key]['source_sha256'] != metric['sha256']
                or hashlib.sha256(page_text.encode()).hexdigest() != quality[key]['inspected_page_text_sha256']['1']):
            raise ValueError('Changed source/native evidence; re-review required')
        row = dict(file_id=key, dataset=11, source_sha256=metric['sha256'],
                   status='dated' if day else 'uncertain', primary_date=day,
                   date_type='email_sent' if day else None, precision='day' if day else None,
                   evidence_page=1, evidence_quote=quote, notes=notes,
                   review_method='Codex visual comparison of PDF page 1 with native UTF-8 extraction; same-assistant editorial date assignment, not independent authentication',
                   timezone_policy='Use the calendar day displayed in the source; no timezone inference or conversion.',
                   inspected_pdf_pages=[1],
                   supporting_evidence=[dict(pdf_page=1, quote=quote, native_text_sha256=hashlib.sha256(page_text.encode()).hexdigest())])
        if source_reading:
            row['source_date_reading'] = source_reading
            row['notes'] += ' Source Sent reading: ' + source_reading + '. No timezone is inferred.'
        validate_review(row, metric, extracted)
        reviews.append(row)
    target = FOLDER/'date-reviews.json'
    target.write_text(json.dumps(dict(schema_version=1, reviewed_on='2026-11-08',
        scope='Ten wave 4 PDFs: eight outer sent dates, two uncertain calendar alerts. No new briefs or native email repairs.', reviews=reviews), indent=2)+'\n', encoding='utf-8')
    path = ROOT/'data/pilot/viewer-batches.json'
    registry = read(path)
    next(b for b in registry['batches'] if b['path'] == FOLDER.relative_to(ROOT).as_posix())['evidence_sha256']['date-reviews.json'] = hashlib.sha256(target.read_bytes()).hexdigest()
    path.write_text(json.dumps(registry, indent=2)+'\n', encoding='utf-8')
    print('Prepared eight dated and two uncertain source-bound reviews.')


if __name__ == '__main__':
    main()
