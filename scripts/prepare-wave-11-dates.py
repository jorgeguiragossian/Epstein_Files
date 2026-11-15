"""Record scoped wave 11 primary-date adjudications; preserve native text."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from viewer.server import validate_review

FOLDER = ROOT/'data/pilot/2026-11-15-wave-11'
DECISIONS = {
    'EFTA00039156': (None, None, 1, '12/6/2013',
        'Program statement issue-date field is numeric 12/6/2013. Month/day ordering is not established by a spelled-out month in inspected evidence; retain uncertainty rather than choosing December 6 or June 12. Repeated footer is not independent disambiguation. This does not date any underlying event.'),
    'EFTA00065579': ('2020-12-01', 'letter', 2, 'December C 2020',
        'Source-render date above the salutation visibly reads December 1st 2020. Native extraction misreads the day as C, and local OCR is also errorful. This editorial letter-date assignment follows the visible source; the exact damaged native evidence quote and all native text remain unchanged. Exhibit cover has no competing issue date. No authenticity or author identity verification.'),
    'EFTA00072576': ('2019-10-07', 'email_sent', 1, 'Date: Mon, 07 Oct 2019 19:31:16 +0000',
        'Outer email Date row visually confirmed. Meeting logistics in the body do not establish additional primary dates or participant identities. Sender and recipient remain redacted.'),
    'EFTA00077515': ('2019-08-19', 'email_sent', 1, 'Date: Mon, 19 Aug 2019 21:17:23 +0000',
        'Outer forwarding-email Date row visually confirmed. Article publication dates, described events and the embedded page-3 forwarded header are separate roles. This dates the containing email, not every clipping or event in the attachment. Long clipping body has only bounded content review.'),
    'EFTA00082124': ('2019-08-14', 'email_sent', 1, 'Date: Wed, 14 Aug 2019 20:41:00 +0000',
        'Outer email Date row visually confirmed despite merged native To/Subject labels. Earlier quoted emails, proposed calls and the August 19 meeting subject are not the primary transmission date. Message enumeration remains incomplete; no contact identity inferred.'),
}

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def main():
    metrics = read(FOLDER/'metrics.json')['files']
    downloads = {r['file_id']: r for r in read(FOLDER/'downloads.json')['files']}
    quality = {r['file_id']: r for r in read(FOLDER/'quality-review.json')['files']}
    reviews = []
    for metric in metrics:
        key = metric['file_id']
        extracted = read(FOLDER/metric['extraction_path'])
        day, role, page, quote, notes = DECISIONS[key]
        assert hashlib.sha256((FOLDER/downloads[key]['local_path']).read_bytes()).hexdigest() == metric['sha256'] == extracted['source_sha256']
        page_sha = hashlib.sha256(extracted['pages'][page-1]['text'].encode('utf-8')).hexdigest()
        assert quality[key]['inspected_page_text_sha256'][str(page)] == page_sha
        row = dict(file_id=key, dataset=9, source_sha256=metric['sha256'],
            status='dated' if day else 'uncertain', primary_date=day, date_type=role,
            precision='day' if day else None, evidence_page=page, evidence_quote=quote,
            notes=notes, review_method='Codex visual comparison of cited source PDF page with native UTF-8 extraction and acquisition/OCR findings; editorial primary-date adjudication, not independent authentication.',
            timezone_policy='Use the calendar day displayed in the source; no timezone conversion or inferred timezone.',
            inspected_pdf_pages=[page], supporting_evidence=[dict(pdf_page=page, quote=quote, native_text_sha256=page_sha)])
        validate_review(row, metric, extracted)
        reviews.append(row)
    target = FOLDER/'date-reviews.json'
    target.write_text(json.dumps(dict(schema_version=1, reviewed_on='2026-11-15',
        scope='Five primary-date reviews: three outer email dates, one source-read letter date, one uncertain numeric policy issue date. No native replacement, new briefs or message/contact verification.', reviews=reviews), indent=2)+'\n', encoding='utf-8')
    path = ROOT/'data/pilot/viewer-batches.json'
    registry = read(path)
    next(b for b in registry['batches'] if b['path'] == FOLDER.relative_to(ROOT).as_posix())['evidence_sha256']['date-reviews.json'] = hashlib.sha256(target.read_bytes()).hexdigest()
    path.write_text(json.dumps(registry, indent=2)+'\n', encoding='utf-8')
    print('Validated four dated and one uncertain source-bound reviews; native extraction unchanged.')

if __name__ == '__main__':
    main()
