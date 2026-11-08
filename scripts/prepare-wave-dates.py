"""Materialize ten editorial date assignments checked against the source PDFs.

Quotes are checked against native extraction; this does not authenticate documents.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'data/pilot/2026-11-07-wave-01'
ASSIGNMENTS = [
    ('EFTA00014597','2019-07-16','email_sent','Date: Tue, 16 Jul 2019 19:25:59 +0000','Containing email header; quoted correspondence dates are not assigned as the primary date.'),
    ('EFTA00021826','2020-07-02','email_sent','Date: Thu, 02 Jul 2020 18:22:03 +0000','Containing email header, rather than quoted correspondence or the reproduced press release.'),
    ('EFTA00026433','2020-07-10','email_sent','Date: Fri, 10 Jul 2020 20:56:14 +0000','Containing email header; an attachment filename is not used as the primary date.'),
    ('EFTA00029421','2021-11-28','email_sent','Date: Sun, 28 Nov 2021 23:14:53 +0000','Containing email header; discussion of a future trial day is not the document date.'),
    ('EFTA00032045','2020-07-06','email_sent','Date: Mon, 06 Jul 2020 15:47:22 +0000','Containing email header; earlier quoted messages and a future July 20 event are separate.'),
    ('EFTA00037008','2022-11-30','email_sent','Date: Wed, 30 Nov 2022 18:24:25 +0000','Containing email header; forwarded query timestamps are separate and are not authenticated by this review.'),
    ('EFTA00039023','2023-06-28','email_sent','Date: Wed, 28 Jun 2023 20:29:48 +0000','Containing email header on PDF page 1; earlier forwarded messages are separate. Page 2 contains only a stamp.'),
    ('EFTA00018844','2021-10-05','court_order','Dated: October 5, 2021','Signed order date, consistent with the docket filing date; future trial and deadline dates are not assigned.'),
    ('EFTA00034623','2019-07-24','report','July 24, 2019','Memorandum issue date; its activity report concerns July 23, a separate date.'),
    ('EFTA00009713',None,None,'Monday July 22, 2019','Multi-day roster compilation: PDF page 1 says Monday July 22, 2019; page 18 says Friday August 09, 2019; page 25 says Saturday August 10, 2019. No single containing-document or assembly date is established. Repeated print timestamps do not establish it.'),
]


def main():
    metrics = {r['file_id']:r for r in json.loads((FOLDER/'metrics.json').read_text(encoding='utf-8'))['files']}
    reviews = []
    for key, day, role, quote, notes in ASSIGNMENTS:
        metric = metrics[key]
        extracted = json.loads((FOLDER/metric['extraction_path']).read_text(encoding='utf-8'))
        if extracted['source_sha256'] != metric['sha256'] or quote not in extracted['pages'][0]['text']:
            raise ValueError('Stale or missing date evidence: ' + key)
        if key == 'EFTA00009713':
            for page, text in [(18,'Friday August 09, 2019'),(25,'Saturday August 10, 2019')]:
                if text not in extracted['pages'][page-1]['text']:
                    raise ValueError('Missing roster evidence')
        reviews.append(dict(file_id=key,dataset=metric['dataset'],source_sha256=metric['sha256'],
            status='dated' if day else 'uncertain',primary_date=day,date_type=role,precision='day' if day else None,
            evidence_page=1,evidence_quote=quote,notes=notes,
            review_method='Codex visual comparison of cited PDF pages with native extracted text; editorial date assignment, not independent authentication',
            timezone_policy='Use calendar day as displayed in source; do not infer or convert an unspecified timezone.'))
    path = FOLDER/'date-reviews.json'
    path.write_text(json.dumps(dict(schema_version=1,reviewed_on='2026-11-07',scope='Ten expansion PDFs: nine primary dates and one uncertain multi-day roster. No new document briefs.',reviews=reviews),indent=2)+'\n',encoding='utf-8')
    registry_path = ROOT/'data/pilot/viewer-batches.json'
    registry = json.loads(registry_path.read_text(encoding='utf-8'))
    next(b for b in registry['batches'] if b['path']==FOLDER.relative_to(ROOT).as_posix())['evidence_sha256']['date-reviews.json'] = hashlib.sha256(path.read_bytes()).hexdigest()
    registry_path.write_text(json.dumps(registry,indent=2)+'\n',encoding='utf-8')
    print('Prepared nine dated reviews and one uncertain roster review.')


if __name__ == '__main__':
    main()
