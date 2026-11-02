"""Export an explicitly authorized public pilot to a buildless GitHub Pages site."""
import argparse
import hashlib
import json
import re
import sys
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'viewer'))
from server import build_index,Catalog,STATIC,load


def replace_once(text,old,new):
    if text.count(old)!=1:raise ValueError('Static adaptation changed; inspect asset before publishing: '+old)
    return text.replace(old,new)


def build(out,base):
    if not base.startswith('/') or not base.endswith('/'):raise ValueError('Base must start and end with a slash.')
    build_index()
    catalog=Catalog();pilot=ROOT/'data/pilot/2026-11-01'
    metrics=load(pilot/'metrics.json')['files'];documents={}
    for metric in metrics:
        record=catalog.document(metric['file_id'],1)
        record.pop('page')
        record['pages']=[catalog.document(metric['file_id'],n)['page'] for n in range(1,metric['page_count']+1)]
        documents[record['id']]=record
    with catalog.connect() as connection:
        emails=json.loads(connection.execute('SELECT payload FROM email_catalog').fetchone()['payload'])
    data={'format_version':1,'publication_scope':'Full public pilot text and email candidates, explicitly authorized by repository owner. Source PDFs remain on DOJ.','overview':catalog.overview(),'people':catalog.people(),'documents':documents,'emails':emails}
    out.mkdir(parents=True,exist_ok=True);(out/'data').mkdir(exist_ok=True)
    data['coverage']=catalog.coverage()
    (out/'data/pilot.json').write_text(json.dumps(data,separators=(',',':'),ensure_ascii=False),encoding='utf-8')
    mapping={'/':base,'/emails':base+'emails.html','/coverage':base+'coverage.html'}
    for name in ['index.html','emails.html','coverage.html']:
        html=(STATIC/name).read_text(encoding='utf-8')
        html=re.sub(r'((?:href|src)=")(/[^"#]*)(")',lambda m:m[1]+mapping.get(m[2],base+m[2].lstrip('/'))+m[3],html)
        html=html.replace('<script src=',f'<script src="{base}static-api.js" defer></script><script src=',1)
        html=html.replace('LOCAL WORKSPACE','PUBLIC PILOT').replace('LOCAL EMAIL REVIEW','PUBLIC EMAIL REVIEW').replace('LOCAL RESEARCH WORKSPACE','PUBLIC PILOT WORKSPACE').replace('A local research workspace','A public research workspace')
        html=html.replace('Open PDF · page','DOJ PDF · page').replace('local email','published email').replace('Source: U.S. Department of Justice · Pilot sample only','Source: U.S. Department of Justice · Published pilot sample')
        (out/name).write_text(html,encoding='utf-8')
    app=(STATIC/'app.js').read_text(encoding='utf-8')
    app=replace_once(app,"$('#pdf-link').href = `/pdf/${encodeURIComponent(id)}#page=${page}`;","$('#pdf-link').href = window.PilotStatic.pdfUrl(id,page);")
    app=app.replace('Open PDF · page','DOJ PDF · page').replace('local pilot','published pilot').replace('local server','published data').replace('the local pilot','the published pilot')
    (out/'app.js').write_text(app,encoding='utf-8')
    emailjs=(STATIC/'emails.js').read_text(encoding='utf-8')
    emailjs=replace_once(emailjs,'`/pdf/${encodeURIComponent(source.file_id)}#page=${source.source_page}`','window.PilotStatic.pdfUrl(source.file_id,source.source_page)')
    emailjs=emailjs.replace('`/?doc=',f'`{base}?doc=').replace('Open PDF ↗','DOJ PDF ↗').replace('local email','published email').replace('local review','published review').replace('local email cache','published email data')
    (out/'emails.js').write_text(emailjs,encoding='utf-8')
    coveragejs=(STATIC/'coverage.js').read_text(encoding='utf-8').replace("'/emails?",f"'{base}emails.html?").replace("'/?doc=",f"'{base}?doc=")
    (out/'coverage.js').write_text(coveragejs,encoding='utf-8')
    for name in ['style.css','static-api.js']:(out/name).write_bytes((STATIC/name).read_bytes())
    # Pages caches assets independently; bind HTML to the exact built asset bytes.
    for name in ['index.html','emails.html','coverage.html']:
        html=(out/name).read_text(encoding='utf-8')
        for asset in ['app.js','emails.js','coverage.js','static-api.js','style.css']:
            digest=hashlib.sha256((out/asset).read_bytes()).hexdigest()[:12]
            html=html.replace(f'{base}{asset}"',f'{base}{asset}?v={digest}"')
        (out/name).write_text(html,encoding='utf-8')
    (out/'.nojekyll').write_text('',encoding='utf-8')
    manifest={'source_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'base_path':base,'documents':len(documents),'pages':sum(len(r['pages']) for r in documents.values()),'name_phrases':len(data['people']['people']),'email_candidates':emails['summary']['candidate_occurrences'],'data_bytes':(out/'data/pilot.json').stat().st_size,'publication':'public full pilot; no source PDF copies or credentials'}
    (out/'build-info.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(manifest,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=ROOT/'site-dist')
    parser.add_argument('--base',default='/Epstein_Files/')
    args=parser.parse_args();build(args.out,args.base)
