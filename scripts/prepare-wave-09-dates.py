"""Prepare source-bound wave 9 dates; keep compound records uncertain."""
import hashlib
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from viewer.server import validate_review
FOLDER=ROOT/'data/pilot/2026-11-09-wave-09'
NOTES={
'EFTA00005707':'Header Date: 03/14/2011 dates this four-page FBI administrative communication. March 14-21 travel interval and referenced email are separate roles, not proof of completed travel or an extracted email. Calendar day interpreted in explicit US month/day/year context.',
'EFTA00005910':'Folder cover and two sampled blacked-out pages do not establish a complete primary date. Scope is PDF pages 1/7/14 only, not all fourteen pages; handwriting/location and hidden content do not supply an issue date.',
'EFTA00006085':'Compound certification, inventory, four event reports and settlement sheet. Handwritten certification execution date and February 1-2, 2005 event dates have different roles. No single issue/assembly day established for the entire PDF; no event date substituted for certification or collection date.',
'EFTA00006387':'Only PDF pages 1/50/100 inspected in this 100-page telephone-statement collection. Sampled statement headings span June/July/August 2006 and rows have their own dates; no single primary date or complete reporting period established. Calls/columns not validated.',
'EFTA00007501':'Only PDF pages 1/21/42 inspected. Source page 1 heading reads Aug 20, 2005 although native and focused OCR read 2006; later sampled statement headings differ. The local provisional heading reading does not date the whole collection. No single primary date or complete reporting period established; no native correction.',
'EFTA00007606':'Folder, order/shipment record and shipping label contain order, ship, delivery and page-print dates in different roles. No single primary date established for the compound PDF; folder identifier is not a date and shipping-label text does not verify shipment completion.',
'EFTA00007684':'Invoice photograph has printed invoice/shipped fields and a separate handwritten packaging marking. Faint/reflected text and missing native date fields do not establish which date governs the photographed evidence record. No primary date or verified transaction assigned.',
'EFTA00007763':'Evidence packaging, handwritten form, digitization notice, unscanned-item placeholder and cassette photo have distinct handling/template/label roles. Handwritten form date is not established as receipt, capture or creation. April 2018 and July 27, 2020 template markers do not date the evidence event or underlying audio. No single primary day established.',
'EFTA00007968':'Evidence form date is damaged in native/OCR text; the source handwritten form date is distinct from July 27, 2020 placeholder revision and cassette-label markings. Date field alone does not establish receipt, capture or media creation. No single primary date or audio date assigned.',
'EFTA00008320':'Only PDF pages 1/45/89 inspected in an 89-page publication extract/marked cover collection. Publication page numbers, prose and final handwritten marking do not establish a complete issue/assembly day. No date inferred from subject matter, ownership or unseen components.'}
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
 metrics={m['file_id']:m for m in read(FOLDER/'metrics.json')['files']};downloads={m['file_id']:m for m in read(FOLDER/'downloads.json')['files']};quality=read(FOLDER/'quality-review.json')['files'];reviews=[]
 for q in quality:
  key=q['file_id'];m=metrics[key];e=read(FOLDER/m['extraction_path']);assert hashlib.sha256((FOLDER/downloads[key]['local_path']).read_bytes()).hexdigest()==m['sha256']==q['source_sha256']==e['source_sha256']
  evidence=[]
  for n in q['visually_inspected_pdf_pages']:
   text=e['pages'][n-1]['text'];h=hashlib.sha256(text.encode('utf-8')).hexdigest();assert h==q['inspected_page_text_sha256'][str(n)]
   evidence.append(dict(pdf_page=n,quote=text.strip(),native_text_sha256=h))
  dated=key=='EFTA00005707';quote='Date: 03/14/2011' if dated else e['pages'][0]['text'].strip()
  row=dict(file_id=key,dataset=4,source_sha256=m['sha256'],status='dated' if dated else 'uncertain',primary_date='2011-03-14' if dated else None,date_type='communication' if dated else None,precision='day' if dated else None,evidence_page=1,evidence_quote=quote,notes=NOTES[key],review_method='Codex bounded source comparison with native UTF-8 evidence and prior quality/OCR findings; same-assistant editorial adjudication, not independent authentication',timezone_policy='Use source calendar day; no timezone inference or conversion.',inspected_pdf_pages=q['visually_inspected_pdf_pages'],supporting_evidence=evidence)
  validate_review(row,m,e);reviews.append(row)
 target=FOLDER/'date-reviews.json';target.write_text(json.dumps(dict(schema_version=1,reviewed_on='2026-11-09',scope='Ten wave 9 documents: one communication date, nine uncertain primary dates; prior 37-page bounded comparison preserved. No native replacement or new briefs.',reviews=reviews),indent=2)+'\n',encoding='utf-8')
 p=ROOT/'data/pilot/viewer-batches.json';registry=read(p);next(b for b in registry['batches'] if b['path']==FOLDER.relative_to(ROOT).as_posix())['evidence_sha256']['date-reviews.json']=hashlib.sha256(target.read_bytes()).hexdigest();p.write_text(json.dumps(registry,indent=2)+'\n',encoding='utf-8')
 print('Prepared one communication date and nine uncertain reviews with 37 pinned page-text hashes.')
if __name__=='__main__':main()
