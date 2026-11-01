"""Prepare a bounded, page-sourced name vocabulary; not identity resolution."""
import json
import re
import argparse
import hashlib
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
 ('prince-andrew','Prince Andrew','EFTA00009823',1),
 ('alan-dershowitz','Alan Dershowitz','EFTA00009329',14),
 ('alexander-acosta','Alexander Acosta','EFTA00009229',1),
 ('darren-indyke','Darren Indyke','EFTA01263156',1),
 ('reid-weingarten','Reid Weingarten','EFTA00009658',5),
 ('larry-cohen','Larry Cohen','EFTA02730265',1),
 ('audrey-strauss','Audrey Strauss','EFTA00008874',18),
 ('barry-krischer','Barry Krischer','EFTA00009229',37),
 ('jay-lefkowitz','Jay Lefkowitz','EFTA00009016',67),
 ('ken-starr','Ken Starr','EFTA00009016',34),
 ('roy-black','Roy Black','EFTA00009329',14),
 ('gerald-lefcourt','Gerald Lefcourt','EFTA00009329',14),
 ('guy-lewis','Guy Lewis','EFTA00009329',29),
 ('lilly-ann-sanchez','Lilly Ann Sanchez','EFTA00009329',23),
 ('jeanne-christensen','Jeanne Christensen','EFTA02731485',1)]
DEFERRED=[('Jeffery Epstein','EFTA00008529',1,'A different spelling from the selected Jeffrey Epstein phrase. No automatic spelling or identity merge.'),
 ('Lillian Sanchez','EFTA00009329',14,'Different phrase from Lilly Ann Sanchez. Possible variant requires separate alias evidence; keep it out of that filter.'),
 ('Darren K. Indyke','EFTA01263156',1,'Middle-initial form is distinct from the selected Darren Indyke phrase. It is not silently merged.')]


def main(render=False):
    metrics={r['file_id']:r for r in json.loads((PILOT/'metrics.json').read_text(encoding='utf-8'))['files']}
    extractions={key:json.loads((PILOT/metric['extraction_path']).read_text(encoding='utf-8')) for key,metric in metrics.items()}
    people=[]
    for key,name,doc,page in NAMES:
        metric=metrics[doc]
        extracted=extractions[doc]
        pattern=r'(?<!\w)'+r'\s+'.join(re.escape(w) for w in name.split())+r'(?!\w)'
        match=re.search(pattern,extracted['pages'][page-1]['text'],re.I)
        assert match,name
        people.append({'id':key,'label':name,'forms':[name],
            'evidence':{'file_id':doc,'pdf_page':page,'quote':match.group(0),'source_sha256':metric['sha256']},
            'review_method':'Cited PDF page visually reviewed and name quote checked against extracted text. Matches elsewhere are lexical candidates, not confirmed identity assertions.'})
    vocabulary=PILOT/'people.json'
    vocabulary.write_text(json.dumps({'schema_version':1,'scope':f'{len(people)} curated name strings; incomplete pilot vocabulary. No initials, surnames alone, email-address aliases, or fuzzy identity matching.','people':people},indent=2)+'\n',encoding='utf-8')
    coverage=[]
    for person in people:
        pattern=re.compile(r'(?<!\w)'+r'\s+'.join(map(re.escape,person['label'].split()))+r'(?!\w)',re.I)
        hits=[(key,page['page'],len(pattern.findall(page['text']))) for key,extraction in extractions.items() for page in extraction['pages']]
        hits=[hit for hit in hits if hit[2]]
        coverage.append({'id':person['id'],'label':person['label'],'documents':len({hit[0] for hit in hits}),'pages':len(hits),'occurrences':sum(hit[2] for hit in hits)})
    (PILOT/'people-coverage.json').write_text(json.dumps({'schema_version':1,'vocabulary_sha256':hashlib.sha256(vocabulary.read_bytes()).hexdigest(),
        'metrics_sha256':hashlib.sha256((PILOT/'metrics.json').read_bytes()).hexdigest(),'selection_sha256':hashlib.sha256((PILOT/'selection.json').read_bytes()).hexdigest(),
        'pilot_documents':len(extractions),'pilot_pages':sum(len(x['pages']) for x in extractions.values()),
        'scope':'Full-name lexical coverage in the non-random 100-document pilot. Occurrences include repetitions and quoted threads; not identities, contacts, or relationships.',
        'people':sorted(coverage,key=lambda row:row['label'])},indent=2)+'\n',encoding='utf-8')
    deferred=[]
    for form,doc,page,reason in DEFERRED:
        pattern=r'(?<!\w)'+r'\s+'.join(map(re.escape,form.split()))+r'(?!\w)'
        match=re.search(pattern,extractions[doc]['pages'][page-1]['text'],re.I)
        assert match,form
        deferred.append({'observed_form':form,'status':'deferred_not_in_filter','reason':reason,
            'evidence':{'file_id':doc,'pdf_page':page,'quote':match.group(0),'source_sha256':metrics[doc]['sha256']}})
    (PILOT/'name-review-notes.json').write_text(json.dumps({'schema_version':1,'scope':'Source-observed forms intentionally not merged with selected vocabulary entries. These are review decisions, not established aliases.','decisions':deferred},indent=2)+'\n',encoding='utf-8')
    print(f'Prepared {len(people)} sourced name entries.')
    if render:
        import pypdfium2 as pdfium
        from PIL import Image,ImageDraw
        downloads={r['file_id']:r for r in json.loads((PILOT/'downloads.json').read_text(encoding='utf-8'))['files']}
        pages={}
        for key,name,doc,page in NAMES[8:]:pages.setdefault((doc,page),[]).append(name)
        selected=list(pages.items())
        folder=ROOT/'tmp/name-expansion'
        folder.mkdir(parents=True,exist_ok=True)
        for start in range(0,len(selected),4):
            canvas=Image.new('RGB',(1600,2160),'#dddddd');draw=ImageDraw.Draw(canvas)
            for offset,((key,number),names) in enumerate(selected[start:start+4]):
                doc=pdfium.PdfDocument(str(PILOT/downloads[key]['local_path']));page=doc[number-1]
                bitmap=page.render(scale=1.5);image=bitmap.to_pil().convert('RGB');image.thumbnail((780,1030))
                x,y=(offset%2)*800,(offset//2)*1080
                draw.text((x+8,y+8),f'{key} PDF p{number}: '+', '.join(names),fill='black')
                canvas.paste(image,(x,y+35));bitmap.close();page.close();doc.close()
            canvas.save(folder/f'sheet-{start//4+1}.jpg')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--render-expansion',action='store_true')
    main(parser.parse_args().render_expansion)
