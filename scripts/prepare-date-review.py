"""Reproduce two curated 20-document date review batches and optional QA sheets."""
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
SECOND_REVIEWS=[
 ('EFTA00008892','dated','2020-06-29','presentation',1,'June 29, 2020 Grand Jury Presentation','Date printed on the presentation cover. Dates depicted within slides are not assigned to the whole document.'),
 ('EFTA00008920','dated','2020-06-29','transcript_session',1,'June 29, 2020','Session date below courthouse address. November 19, 2019 Additional is a separate jury designation.'),
 ('EFTA00009229','dated','2019-10-18','transcript_session',1,'Friday, October 18, 2019','Date of the OPR interview session on the transcript cover, not the date of historical events discussed.'),
 ('EFTA00009440','dated','2007-05-08','transcript_session',1,'May 8, 2007','Grand jury testimony session date on the cover; 07-103 is a jury identifier.'),
 ('EFTA00009448','dated','2007-02-27','transcript_session',1,'February 27, 2007','Grand jury testimony session date on the cover.'),
 ('EFTA00009478','dated','2007-03-20','transcript_session',1,'Tuesday, March 20, 2007','Session date below the courthouse location; COPY and ORIGINAL stamps are not dates.'),
 ('EFTA00009502','dated','2007-04-24','transcript_session',1,'Tuesday, April 24, 2007','Grand jury session date on the transcript cover.'),
 ('EFTA00009512','dated','2007-05-15','transcript_session',1,'Tuesday, May 15, 2007','Grand jury testimony session date on the cover.'),
 ('EFTA00009586','dated','2007-04-24','transcript_session',1,'April 24, 2007','Transcript date visible on the rotated cover. Preserve native extraction and do not infer another document assembly date.'),
 ('EFTA00009632','dated','2007-02-06','transcript_session',1,'Tuesday, February 6, 2007','Grand jury session date printed below the location.'),
 ('EFTA00039826','dated','2021-04-23','letter',1,'April 23, 2021','Letter date above the delivery method; April 21 court order and April 19 correspondence are references within its text.'),
 ('EFTA00039881','dated','2020-11-18','letter',1,'November 18, 2020','Date printed at the top of the letter. This does not establish when delivery occurred.'),
 ('EFTA02209722','dated','2017-04-06','email_sent',1,'Sent Thur 4/6/2017 1:14:59 PM','Top-level Sent header. Repeated textual Apr 6, 2017 dates in the chain support this source-specific month/day interpretation.'),
 ('EFTA02212894','dated','2017-05-03','email_sent',1,'Wed 5/3/2017 12:40:05 PM','Top-level header date printed beside Sent. Textual May 3, 2017 quoted headers support this source-specific month/day reading.'),
 ('EFTA02212924','uncertain',None,None,1,'May 23, 2017 2:00 PM','Reminder event date in the body; no labeled sent or creation date is visible. Keep the document outside primary-date range analysis.'),
 ('EFTA02212946','dated','2017-05-03','email_sent',1,'Sent Wed 5/3/2017 12:42:47 PM','Top-level Sent header. Quoted May 2 correspondence and tomorrow context support May 3; quoted dates are not selected as primary.'),
 ('EFTA02212961','dated','2017-05-16','email_sent',1,'Sent all i2:13:52 PM','Visible PDF header reads Tue 5/16/2017 2:13:52 PM, despite severe extraction loss in the date. Use the displayed calendar day; raw extraction remains unchanged.'),
 ('EFTA02730477','dated','2022-01-19','report',1,'19 January 2022','Report issue date at upper right. Template effective 10-1-2021 and historical dates in the report are not its primary date. This date review does not authenticate report claims.'),
 ('EFTA01263156','dated','2018-10-10','email_sent',1,'Sent: cipher 10, 2018 4:37 PM','Visible outer Sent header reads Wednesday October 10, 2018 4:37 PM. Native month recognition is damaged. Quoted September 30 notice and travel-plan dates are not the primary outer email date; exhibit assembly date is unknown.'),
 ('EFTA01263272','dated','2019-04-09','transcript_session',1,'April 9, 2019','Conference session date under New York, N.Y. on the transcript cover; 19 Misc. 149 is a case identifier.')
]
REVIEWS+=SECOND_REVIEWS


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
        if any(r[0]==doc for r in SECOND_REVIEWS):records[-1]['reviewed_on']='2026-11-02'
    path = PILOT/'date-reviews.json'
    path.write_text(json.dumps({'schema_version':1,'reviewed_on':'2026-11-02','scope':'40 purposively selected documents in two batches; all other pilot documents remain unreviewed. Only primary dates with status dated participate in range filters.','reviews':records},indent=2)+'\n',encoding='utf-8')
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
