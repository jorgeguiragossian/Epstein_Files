"""Materialize scoped primary-date adjudication without promoting period endpoints."""
import hashlib
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from viewer.server import validate_review
FOLDER=ROOT/'data/pilot/2026-11-08-wave-03'


def main():
    read=lambda p:json.loads(p.read_text(encoding='utf-8'))
    metrics={m['file_id']:m for m in read(FOLDER/'metrics.json')['files']}
    layouts=read(FOLDER/'table-date-role-reviews.json')['reviews'];reviews=[]
    for layout in layouts:
        key=layout['file_id'];metric=metrics[key];extracted=read(FOLDER/metric['extraction_path'])
        observation=layout['date_observations'][0]
        day=role=None;page=observation['pdf_page'];quote=observation['native_quote']
        if key=='EFTA01262784':
            day='2019-06-27';role='court_order';page=7;quote='June 27, 2019'
            notes='Combined application and signed order: use the court order date on PDF page 7, consistent with the application signature on page 4. Repeated 2017.02.06 footers are form/version markers, not the signed date.'
        elif key=='EFTA01268630':
            notes='The tax heading supplies a year only. No complete primary calendar day is established; do not invent January 1 or December 31 from the year.'
        elif key=='EFTA01280083':
            notes='Preliminary statement: the print timestamp and planned settlement/proration/disbursement date have different roles. Signature fields are blank; no completed settlement or primary issue/execution date is established by this review. Retain the separate date-role observations without choosing one as primary.'
        elif key=='EFTA01281641':
            notes='Handwritten date has a provisional local literal reading but its format/century remains unresolved, and native/OCR date text is inadequate. No primary date is assigned. Source-assisted financial readings remain separate from native text.'
        else:
            notes='The visible dates describe a statement reporting period or portfolio as-of/activity period. No separate issue date is established. Keep these source-backed observations available through reporting-period search; do not silently substitute an endpoint for a primary document date.'
        row=dict(file_id=key,dataset=metric['dataset'],source_sha256=metric['sha256'],status='dated' if day else 'uncertain',primary_date=day,date_type=role,precision='day' if day else None,evidence_page=page,evidence_quote=quote,notes=notes,
                 review_method='Codex adjudication from source-inspected pages and native UTF-8 quotes; editorial date assignment, not independent authentication',timezone_policy='Use the calendar day displayed in the source; do not infer unspecified timezones or force reporting periods into a single day.')
        if key=='EFTA01262784':
            row['supporting_evidence']=[dict(pdf_page=4,quote='June 27, 2019',native_text_sha256=hashlib.sha256(extracted['pages'][3]['text'].encode()).hexdigest())]
        validate_review(row,metric,extracted);reviews.append(row)
    target=FOLDER/'date-reviews.json';target.write_text(json.dumps(dict(schema_version=1,reviewed_on='2026-11-08',scope='Ten wave 3 PDFs: one primary court-order date and nine uncertain primary dates. Reporting-period/date-role observations remain separate.',reviews=reviews),indent=2)+'\n',encoding='utf-8')
    path=ROOT/'data/pilot/viewer-batches.json';registry=read(path)
    next(b for b in registry['batches'] if b['path']==FOLDER.relative_to(ROOT).as_posix())['evidence_sha256']['date-reviews.json']=hashlib.sha256(target.read_bytes()).hexdigest()
    path.write_text(json.dumps(registry,indent=2)+'\n',encoding='utf-8')
    print('Prepared one dated and nine uncertain primary-date reviews.')


if __name__=='__main__':main()
