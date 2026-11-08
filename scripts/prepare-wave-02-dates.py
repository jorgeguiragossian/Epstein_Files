"""Materialize source-inspected primary-date reviews for the second expansion wave."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from viewer.server import validate_review

FOLDER = ROOT/'data/pilot/2026-11-08-wave-02'
ASSIGNMENTS = [
    ('EFTA00059374','2019-08-10','email_sent',1,'Saturday, August 10, 2019 10:20:14 PM',
     'Containing-email Date row visually confirmed despite separated native labels/values. Earlier forwarded message and handwritten annotation are not primary dates. No timezone is inferred.'),
    ('EFTA00064578','2022-03-10','email_sent',1,'Date: Thursday, March 10, 2022 3:19:38 PM',
     'Outer email sent date; quoted 2021 messages, 2018 purchase dates and 2019 installation dates are separate. Native subject/attachment damage does not obscure this date row. No timezone is inferred.'),
    ('EFTA00067452','2008-06-18','email_sent',1,'Date: Wed, 18 Jun 2008 17:53:07 +0000',
     'Outer email sent date; the future July 7 deadline mentioned in the body is not the primary document date.'),
    ('EFTA00070036','2019-08-12','letter',1,'August 12, 2019',
     'Letter issue date above the salutation. Referenced August 10 correspondence and July 23 incident are separate dates; SENT VIA EMAIL does not make this a parsed email message.'),
    ('EFTA00073640','2021-12-01','email_sent',1,'Date: Wed, 01 Dec 2021 04:32:29 +0000',
     'Outer email Date row uses December 1 as displayed at +0000. Earlier November 30 quoted local-clock messages and the attachment filename do not control the date. Known body-order problems remain unresolved and do not change this visible header date.'),
    ('EFTA00075976','2021-07-30','court_order',3,'Dated: July 30, 2021',
     'Order date on the final PDF page, consistent with the July 30 docket filing stamp. Dates in cited authorities and news coverage are separate.'),
    ('EFTA00079911','2019-08-23','email_sent',1,'Date: Fri, 23 Aug 2019 20:40:59 +0000',
     'Outer email sent date; July 5 in the subject identifies a subpoena and proposed September meetings are future events. The known clock discrepancy in a later quoted message is separate from this outer header.'),
    ('EFTA00082128','2019-08-14','email_sent',1,'Date: Wed, 14 Aug 2019 16:59:58 +0000',
     'Outer email sent date. August 19 in the subject is a proposed meeting, and 2017/2018 in signature graphics are not document dates.'),
    ('EFTA00039153',None,None,1,'LIST OF EXHIBITS - CHAPTER 2',
     'All three PDF pages were inspected. Each footer DATE field is blank; dates in the numbered list refer to exhibits, statutes or other records. No assembly/issue date for this list is established. The case number is not a primary-date assignment.'),
    ('EFTA00078194',None,None,1,'RECORDED 10/23/2020 09:56:41',
     'Both PDF pages inspected. Recording occurred October 23, 2020; page 2 separately states acknowledgment on March 9, 2019. The March 2019 made/execution-day text on page 1 is obscured by a watermark and absent from native extraction. Retain an uncertain primary execution date rather than substitute the recording or acknowledgment date. No legal effect or authenticity is inferred.'),
]


def main():
    metrics = {r['file_id']:r for r in json.loads((FOLDER/'metrics.json').read_text(encoding='utf-8'))['files']}
    rows = []
    for key,day,role,page,quote,notes in ASSIGNMENTS:
        metric = metrics[key]
        extracted = json.loads((FOLDER/metric['extraction_path']).read_text(encoding='utf-8'))
        row = dict(file_id=key,dataset=metric['dataset'],source_sha256=metric['sha256'],status='dated' if day else 'uncertain',
                   primary_date=day,date_type=role,precision='day' if day else None,evidence_page=page,evidence_quote=quote,notes=notes,
                   review_method='Codex visual comparison of cited PDF pages with native UTF-8 extraction; editorial date assignment, not independent authentication',
                   timezone_policy='Use the calendar day as displayed in the source; do not infer or convert an unspecified timezone.')
        if key=='EFTA00039153':
            row['inspected_pdf_pages']=[1,2,3]
        if key=='EFTA00078194':
            row['inspected_pdf_pages']=[1,2]
            text=extracted['pages'][1]['text']
            row['supporting_evidence']=[dict(pdf_page=2,quote='on this 9th day of March. 2019',native_text_sha256=hashlib.sha256(text.encode()).hexdigest())]
        if extracted['source_sha256']!=metric['sha256']:
            raise ValueError('Changed extraction binding')
        validate_review(row,metric,extracted)
        rows.append(row)
    target=FOLDER/'date-reviews.json'
    target.write_text(json.dumps(dict(schema_version=1,reviewed_on='2026-11-08',scope='Ten wave 2 PDFs: eight primary dates, two uncertain; no new briefs or email field repairs.',reviews=rows),indent=2)+'\n',encoding='utf-8')
    registry_path=ROOT/'data/pilot/viewer-batches.json'
    registry=json.loads(registry_path.read_text(encoding='utf-8'))
    next(b for b in registry['batches'] if b['path']==FOLDER.relative_to(ROOT).as_posix())['evidence_sha256']['date-reviews.json']=hashlib.sha256(target.read_bytes()).hexdigest()
    registry_path.write_text(json.dumps(registry,indent=2)+'\n',encoding='utf-8')
    print('Prepared eight dated and two uncertain source-bound reviews.')


if __name__=='__main__':
    main()
