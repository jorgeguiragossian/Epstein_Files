"""Adjudicate wave 10 primary dates without conflating media/custody roles."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from viewer.server import validate_review
FOLDER=ROOT/'data/pilot/2026-11-14-wave-10'
NOTES={
'EFTA00008410':'Photographed box has log/case markings with a year-like identifier, not an established complete photograph/record issue date. Do not convert an identifier into a calendar day or infer box contents.',
'EFTA00008423':'Packaged drive has evidence/clone labels and date-like handwriting. Label handling dates do not establish photograph capture, media creation or record issue date; OCR is inadequate and no single primary day established.',
'EFTA00008437':'Envelope case/item identifiers are not established calendar dates. Photograph capture/record issue date is not established; enclosed contents not inferred.',
'EFTA00008451':'Envelope handwriting identifies a case/item, not a complete primary day. No date inferred from adjacent filenames or identifier numbers.',
'EFTA00008464':'Packaged drive photograph lacks an established complete primary date. Packaging/manufacturer/identifier fragments do not date the photograph or underlying media contents.',
'EFTA00008477':'Handwritten case/item markings on envelope do not establish capture, assembly or issue day. No primary date inferred from identifier fragments.',
'EFTA00008489':'Photographed custody envelope has a form-revision marker and distinct handwritten intercept, permanent-storage transfer and accepted/released custody entries. These record different events; none is established as the photograph/whole record issue date. Native and OCR date recognition/column associations are unreliable. No single primary day assigned, no authenticated chain of custody or media date inferred. Source date fields remain visible through the cited PDF; native text unchanged.',
'EFTA00008501':'Equipment case/item labels and handwritten markings do not establish a complete photograph/record date. Do not infer dates from device/model identifiers or noisy native text.',
'EFTA00008515':'Collection photograph includes product packaging, labels and media. Product/label date-like fragments cannot establish a single photograph/assembly/issue day or dates of every underlying media item. No identity/contents inference.',
'EFTA00008528':'Wrapped equipment tag contains case/item markings, not an established primary calendar day. No capture, handling or media creation date inferred from identifiers.'}
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
 metrics={m['file_id']:m for m in read(FOLDER/'metrics.json')['files']};downloads={d['file_id']:d for d in read(FOLDER/'downloads.json')['files']};reviews=[]
 for q in read(FOLDER/'quality-review.json')['files']:
  key=q['file_id'];m=metrics[key];e=read(FOLDER/m['extraction_path']);text=e['pages'][0]['text'];sha=hashlib.sha256(text.encode('utf-8')).hexdigest()
  assert hashlib.sha256((FOLDER/downloads[key]['local_path']).read_bytes()).hexdigest()==m['sha256']==q['source_sha256']==e['source_sha256'];assert q['inspected_page_text_sha256']['1']==sha
  row=dict(file_id=key,dataset=5,source_sha256=m['sha256'],status='uncertain',primary_date=None,date_type=None,precision=None,evidence_page=1,evidence_quote=text.strip(),notes=NOTES[key],review_method='Codex comparison of cited source photograph with native UTF-8 evidence, acquisition triage and local OCR findings; editorial primary-date adjudication, not independent authentication',timezone_policy='No date or timezone inferred.',inspected_pdf_pages=[1],supporting_evidence=[dict(pdf_page=1,quote=text.strip(),native_text_sha256=sha)])
  validate_review(row,m,e);reviews.append(row)
 target=FOLDER/'date-reviews.json';target.write_text(json.dumps(dict(schema_version=1,reviewed_on='2026-11-14',scope='All ten single-page photographs: uncertain primary dates; custody events, form revision, labels and identifiers kept distinct. No native replacement or new briefs.',reviews=reviews),indent=2)+'\n',encoding='utf-8')
 p=ROOT/'data/pilot/viewer-batches.json';v=read(p);next(b for b in v['batches'] if b['path']==FOLDER.relative_to(ROOT).as_posix())['evidence_sha256']['date-reviews.json']=hashlib.sha256(target.read_bytes()).hexdigest();p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8');print('Validated ten uncertain primary-date reviews with source/page hashes.')
if __name__=='__main__':main()
