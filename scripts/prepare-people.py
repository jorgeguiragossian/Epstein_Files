"""Prepare a bounded, page-sourced name vocabulary; not identity resolution."""
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PILOT=ROOT/'data/pilot/2026-11-01'
NAMES=[('jeffrey-epstein','Jeffrey Epstein','EFTA00008585',1),
 ('ghislaine-maxwell','Ghislaine Maxwell','EFTA00008631',1),
 ('sigrid-mccawley','Sigrid McCawley','EFTA00009865',1),
 ('richard-kahn','Richard Kahn','EFTA02212972',1),
 ('boris-nikolic','Boris Nikolic','EFTA02730265',1),
 ('leon-black','Leon Black','EFTA02731485',1),
 ('bill-gates','Bill Gates','EFTA02730265',1),
 ('prince-andrew','Prince Andrew','EFTA00009823',1)]


def main():
    metrics={r['file_id']:r for r in json.loads((PILOT/'metrics.json').read_text(encoding='utf-8'))['files']}
    people=[]
    for key,name,doc,page in NAMES:
        metric=metrics[doc]
        extracted=json.loads((PILOT/metric['extraction_path']).read_text(encoding='utf-8'))
        pattern=r'(?<!\w)'+r'\s+'.join(re.escape(w) for w in name.split())+r'(?!\w)'
        match=re.search(pattern,extracted['pages'][page-1]['text'],re.I)
        assert match,name
        people.append({'id':key,'label':name,'forms':[name],
            'evidence':{'file_id':doc,'pdf_page':page,'quote':match.group(0),'source_sha256':metric['sha256']},
            'review_method':'Name string checked against a previously visually reviewed pilot page; matches elsewhere are lexical candidates, not confirmed identity assertions.'})
    (PILOT/'people.json').write_text(json.dumps({'schema_version':1,'scope':'Eight curated name strings; incomplete pilot vocabulary. No initials, surnames alone, email-address aliases, or fuzzy identity matching.','people':people},indent=2)+'\n',encoding='utf-8')
    print(f'Prepared {len(people)} sourced name entries.')


if __name__=='__main__':main()
