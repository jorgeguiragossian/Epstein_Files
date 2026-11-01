"""Reproduce the curated 20-document date review and optional local QA sheets."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / 'data/pilot/2026-11-01'
# Dates are curated from source context, not the first regex match.
# id, status, ISO day, role, PDF page, exact extracted evidence, reason
REVIEWS = [
 ('EFTA00008529','dated','2019-06-18','transcript_session',1,'June 18, 2019','Session date below courthouse address; earlier cover date is not the session date.'),
 ('EFTA00008585','dated','2019-07-02','transcript_session',1,'July 2, 2019','Session date below courthouse address; August 2018 is a jury designation.'),
 ('EFTA00008631','dated','2020-06-29','transcript_session',1,'June 29, 2020','Session date; November 19, 2019 Additional is a different cover reference.'),
 ('EFTA00008708','dated','2020-07-08','transcript_session',1,'July 8, 2020','Session date; preserve the separate jury designation as context.'),
 ('EFTA00008744','dated','2021-03-29','transcript_session',1,'March 29, 2021','Session date; January 19, 2021 Additional is not selected.'),
 ('EFTA00005705','dated','2010-12-10','report',1,'Date of Report 2010-12-10','Report date is primary; Date of Contact has the same day but a different role.'),
 ('EFTA00005740','uncertain',None,None,1,'EFTA00005740','Compilation with a sparse cover and dated material later in the file. No single primary document date established.'),
 ('EFTA00005967','uncertain',None,None,3,'Friday, 11/26/2021','Shipment compilation contains receipt and delivery dates. Delivery date is an event date, not an established compilation date.'),
 ('EFTA00009823','dated','2020-03-11','email_sent',1,'Date: Wed, 11 Mar 2020 23:04:47 +0000','Top-level email header date; quoted messages are separate evidence. Day uses the displayed header timezone.'),
 ('EFTA00009853','dated','2019-10-28','email_sent',1,'Date: Mon, 28 Oct 2019 21:25:21 +0000','Top-level email header date; body scheduling references are not selected.'),
 ('EFTA00009865','dated','2020-12-15','email_sent',1,'Date: Tue, 15 Dec 2020 14:59:37 +0000','Top-level header date; quoted filing discussion does not establish another primary date.'),
 ('EFTA00009882','dated','2019-02-26','email_sent',1,'Date: Tue, 26 Feb 2019 19:46:04 +0000','Top-level header date; participant redactions do not change the visible date evidence.'),
 ('EFTA00009890','dated','2021-04-20','email_sent',1,'Date: Tue, 20 Apr 2021 23:13:00 +0000','Top-level email date, not a date extracted from an attachment filename.'),
 ('EFTA00039419','dated','2021-04-14','email_sent',1,'Date: Wed, 14 Apr 2021 16:01:41 +0000','Top-level header date; the quoted message has its own sent time.'),
 ('EFTA00039790','dated','2021-04-16','email_sent',1,'Date: Fri, 16 Apr 2021 22:09:33 +0000','Email date, not the date of the attached opinion.'),
 ('EFTA00039806','dated','2019-02-24','email_sent',2,'Sunday. February 24, 2019 8:18:01 PM','Date of the outermost email reproduced on PDF page 2; date of exhibit assembly is unknown. Quoted 2016 messages are not primary.'),
 ('EFTA02212905','uncertain',None,None,1,'May 18, 2017 1:00 PM','Date is inline in the message body without a clear sent-date label. Preserve as a mention; do not assume this is the sent date.'),
 ('EFTA02212972','dated','2017-05-01','email_sent',1,'Mon 5/1/2017 6:43:26 PM','Date below the Sent/Subject header. Quoted May 1 messages support US month/day interpretation; timezone is unspecified.'),
 ('EFTA02730265','dated','2013-08-24','email_sent',1,'Date: Sat, 24 Aug 2013 14:02:57 +0000','Top-level email header date; dates in the quoted agreement are not selected.'),
 ('EFTA02731485','dated','2023-06-12','email_sent',1,'Sent: Monda June 12 2023 1:53 PM','Visible Sent header supports June 12, 2023 despite recognition loss in the weekday; attachment dates are separate.')
]


def main(render=False):
    metrics = {r['file_id']:r for r in json.loads((PILOT/'metrics.json').read_text(encoding='utf-8'))['files']}
    downloads = {r['file_id']:r for r in json.loads((PILOT/'downloads.json').read_text(encoding='utf-8'))['files']}
    records = []
    for doc,status,day,role,page,quote,note in REVIEWS:
        metric = metrics[doc]
        extraction = json.loads((PILOT/metric['extraction_path']).read_text(encoding='utf-8'))
        assert quote in extraction['pages'][page-1]['text'], doc
        records.append({'file_id':doc,'dataset':metric['dataset'],'source_sha256':metric['sha256'],
            'status':status,'primary_date':day,'date_type':role,'precision':'day' if day else None,
            'evidence_page':page,'evidence_quote':quote,'notes':note,
            'review_method':'Codex visual comparison of cited PDF page with extracted text; editorial date assignment, not independent authentication',
            'timezone_policy':'Use calendar day as displayed in source; do not infer or convert an unspecified timezone.'})
    path = PILOT/'date-reviews.json'
    path.write_text(json.dumps({'schema_version':1,'reviewed_on':'2026-11-01','scope':'20 purposively selected documents; all other pilot documents remain unreviewed. Only primary dates with status dated participate in range filters.','reviews':records},indent=2)+'\n',encoding='utf-8')
    print(f'Prepared {len(records)} date reviews.')
    if render:
        import pypdfium2 as pdfium
        from PIL import Image,ImageDraw
        folder = ROOT/'tmp/date-review'
        folder.mkdir(parents=True,exist_ok=True)
        for start in range(0,len(records),4):
            canvas = Image.new('RGB',(1600,2160),'#dddddd')
            draw = ImageDraw.Draw(canvas)
            for offset,r in enumerate(records[start:start+4]):
                doc = pdfium.PdfDocument(str(PILOT/downloads[r['file_id']]['local_path']))
                page = doc[r['evidence_page']-1]
                bitmap = page.render(scale=1.5)
                im = bitmap.to_pil().convert('RGB')
                im.thumbnail((780,1035))
                x,y = (offset%2)*800,(offset//2)*1080
                draw.text((x+8,y+8),f"{r['file_id']} PDF p{r['evidence_page']} | {r['primary_date'] or 'UNCERTAIN'}",fill='black')
                canvas.paste(im,(x,y+30))
                bitmap.close();page.close();doc.close()
            canvas.save(folder/f'sheet-{start//4+1}.jpg')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--render',action='store_true')
    main(parser.parse_args().render)
