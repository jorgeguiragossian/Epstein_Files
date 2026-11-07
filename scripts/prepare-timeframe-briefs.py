"""Reproduce curated AI-assisted page briefs and the original-batch source checks."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];PILOT=ROOT/'data/pilot/2026-11-01'
# Each point is deliberately limited to the cited page, not the whole PDF.
BRIEFS=[
 ('EFTA00039826','Request for filing redactions','The government letter requests redactions of third-party identifying information in filings concerning a proposed Rule 17(c) subpoena.','respectfully requests that the Court permit the redaction of the names and identifying information','This summarizes a request in the letter, not a court ruling that the request was granted.'),
 ('EFTA00039881','Discovery-media access correspondence','The letter to the detention center legal department discusses access credentials for discovery materials concerning Ghislaine Maxwell.','the password for the CD containing discovery materials pertinent to Ghislaine Maxwell is','Credential values are redacted; the brief does not reconstruct them or establish delivery.'),
 ('EFTA00009865','Filing schedule discussion','A quoted email says the filing is due the next day and proposes aiming for around 5 p.m. Eastern, with flexibility later in the evening.','The filing is due tomorrow, and we will likely aim to file it around 5pm ET, but we can file it later in the evening if needed.','This is a quoted scheduling statement within the document; it does not establish that a filing occurred at that time.'),
 ('EFTA00039419','Response to a reported lead','The top-level reply says the information will be passed to the FBI.','We will pass this on to the FBI.','The reply expresses an intended referral; it does not verify the quoted allegations or establish that follow-up occurred.'),
 ('EFTA02212946','Proposed call participants','The top-level message says Sir Nicholas Lloyd and John Watts will join the proposed call.','Please be advised that in addition to myself, Sir Nicholas Lloyd (Chairman) and John Watts (BLJDirector and former senior adviser to Prime Minister Blair) will be on the call.','This reports what the sender wrote; it does not establish that the call occurred or that the listed people participated.'),
 ('EFTA02209722','Quoted flight-booking discussion','A quoted reply says another flight booked the previous night was canceled.','done-canceled other flight I booked last night','This is a statement in a quoted chain, not independent confirmation of a booking, cancellation or completed travel.'),
 ('EFTA02730477','Report on potential defense-witness research','The report says FBI New York researched suspected defense witnesses to identify individuals and information relating to them.','FBI New York conducted research on suspected defense witnesses in order to identify the individuals and any derogatory information related to the individuals.','This attributes the description to the report. It does not authenticate its findings or establish the truth of allegations about any person.'),
 ('EFTA02212894','Quoted meeting inquiry','A quoted message asks whether Leon might come to see Jeffrey later that day or the next day.','Hi Melanie. Anything from Leon re coming to see Jeffrey either late today or sometime tomorrow?','The brief preserves the names as written and does not expand their identities or establish that a meeting occurred.')
]
EXTRA_BRIEFS=[
 ('EFTA00005705',1,'Report on photographs received','The report records receipt of eight photographs and says they will be forwarded separately.',
  ['Source also has received 8 current photographs of that were forwarded by to ATP-Jacksonville recently.These will be forwarded to MM under separate cover.'],
  'This summarizes what the report records; subjects and senders are redacted, and receipt or later forwarding is not independently confirmed.'),
 ('EFTA00009823',1,'Quoted publicity-value estimate','A quoted email estimates the article discussed in the chain has more than $4 million in publicity value.',
  ['This article is estimated to have over $4M in publicity value. Insane.'],
  'The figure is attributed to a quoted message. Its calculation, readership and monetary value are not verified by this brief.'),
 ('EFTA00009853',1,'Quoted meeting arrangements','A quoted message states that a meeting is confirmed for 3 p.m. on Monday.',
  ['We are confirmed for a meeting at 3:00 p.m. on Monday at See you then. Thanks.'],
  'This preserves the quoted scheduling statement. It does not identify redacted participants or locations, establish the meeting occurred, or resolve the outer reply mentioning 10/31.'),
 ('EFTA00009882',1,'Request for coordinator contact information','A quoted message requests contact information for a national trafficking coordinator who had reached out the previous day.',
  ['Can you send us contact info for the National trafficking coordinator who reached out to you yesterday?'],
  'This is a request within a quoted exchange. Redacted identities and contact details are not reconstructed.'),
 ('EFTA00009890',1,'Intended filing of an attached letter','The top-level sender says an attached letter is planned for filing that evening.',
  ['As discussed, attached is the letter that I plan to file this evening.'],
  'The brief reports an intention in the email; it does not authenticate the attachment or establish that the filing occurred.'),
 ('EFTA00039790',1,'Circulation of an opinion on pretrial motions','The sender says Judge Nathan’s opinion on most of Maxwell’s pretrial motions is attached.',
  ["Judge Nathan's opinion on the majority of Maxwell's pretrial motions is attached."],
  'This summarizes the cover email. The attached opinion and the sender’s account of its rulings have not been independently checked in this brief.'),
 ('EFTA00039806',2,'Quoted proposal for a Tuesday meeting','A reply within the forwarded chain says Tuesday at four is suitable.',
  ['Tuesday at 4 is good. Thanks.'],
  'The reply is part of an older quoted chain inside a reproduced outer email dated February 24, 2019. It does not establish that a meeting took place on that outer date.'),
 ('EFTA01263156',1,'Quoted change to travel plans','A quoted notice says the Paris trip was canceled and describes planned travel from New York to Palm Beach.',
  ["Mr. Epstein's trip to Paris has been canceled. He will travel today from his vacation home in New York, New York to his vacation home in Palm Beach, Florida"],
  'This is the quoted notice’s account and plan. The containing outer email is dated October 10, 2018; this brief does not verify completed travel or assign that date to the quoted events.'),
 ('EFTA00008892',12,'Older letter reproduced in a presentation','A reproduced letter says an envelope found while cleaning the Epstein Lodge is enclosed.',
  ['Enclosed is the envelope we recently found in cleaning the Epstein Lodge.','December 23, 1994'],
  'The embedded letter is dated December 23, 1994, while the containing presentation is dated June 29, 2020. The envelope’s contents and provenance are not authenticated by this brief.'),
 ('EFTA01263272',2,'Question about contacts before a subpoena','The court asks about contacts between the U.S. Attorney’s Office and Boies Schiller before issuance of the subpoena.',
  ["I would like to know about contacts between the United States Attorney's Office and the Boies Schiller firm prior to the issuance of the subpoena on the subject of your investigation."],
  'This describes a question recorded in the conference transcript. It is not a finding about improper contact or the merits of the subpoena.')
]

REVIEW_NOTES={
 'EFTA00039826':('supported_after_citation_expansion','Expanded the excerpt to include the third-party privacy and Rule 17(c) context; wording continues to describe a request, not a ruling.'),
 'EFTA00039881':('supported_after_citation_expansion','Added the recipient heading to the credential excerpt so both recipient and subject are supported. Redacted values remain unreconstructed.'),
 'EFTA00009865':('supported_as_scoped','Quoted scheduling language supports the brief. Its next-day timing remains attributed to the quoted email, not a verified filing.'),
 'EFTA00039419':('supported_as_scoped','The top-level intended referral supports the statement; the brief makes no finding about quoted allegations or later action.'),
 'EFTA02212946':('supported_as_scoped','The top-level sender explicitly lists proposed participants. Future intent and the absence of evidence the call occurred remain clear.'),
 'EFTA02209722':('supported_as_scoped','The cancellation claim is explicitly in a quoted reply; the brief attributes it rather than verifying travel or a booking.'),
 'EFTA02730477':('supported_as_scoped','The source describes the report’s research purpose. The brief does not repeat its allegations as established findings.'),
 'EFTA02212894':('supported_as_scoped','The excerpt supports a meeting inquiry; names are preserved without identity expansion or a claim the meeting occurred.')
}
# Pinned after the November 7 visual/editorial pass. Regeneration must not
# silently grant a fresh check to edited prose, citations, or source hashes.
REVIEWED_FINGERPRINTS={
 'EFTA00039826':'a4f72063d7a08138f9d705f9566b384b3e29cb43f49fb2fec55ea41a6e03cf34',
 'EFTA00039881':'8c47b600e5b3ed35ec328b57404d7b9b76f9f3c5a7d719288a8fdf9e155a92fa',
 'EFTA00009865':'876cbde46a7e14f45e7cf0e4ddb5d55bae80bf3e0f86425d2ed8a50b15b70da1',
 'EFTA00039419':'181778491a4af1882ed0ade1949a9bf4c1008f2be40622dc1a1bb78dfc341d4f',
 'EFTA02212946':'854a6369158168f9468221f71348054458bfd87d07fe113bbae4f16f2de64989',
 'EFTA02209722':'ab9208049e85903a9f48c7430a5f7db81a87a24fe9585295af9baa21eb14dafa',
 'EFTA02730477':'d8a92d854c50fd8034dc72e87c9890ff483519895f4794c0d9f1ab5e9df02c23',
 'EFTA02212894':'383330226152f0a1e1d5c9c41228df452efec7eff33a035b4d333d62ccb769bd',
}


def original_reviews(rows):
    reviews=[]
    for brief in rows:
        if brief['file_id'] not in REVIEW_NOTES:continue
        result,notes=REVIEW_NOTES[brief['file_id']]
        fingerprint=hashlib.sha256(json.dumps(brief,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
        if fingerprint!=REVIEWED_FINGERPRINTS[brief['file_id']]:
            raise ValueError('Edited brief requires a new editorial review: '+brief['file_id'])
        reviews.append(dict(file_id=brief['file_id'],source_sha256=brief['source_sha256'],brief_sha256=fingerprint,
            reviewed_on='2026-11-07',reviewer='Codex',result=result,notes=notes,
            checks=dict(statement_support=True,attribution=True,page_scope=True,limitations=True)))
    return reviews


def main():
    metrics={r['file_id']:r for r in json.loads((PILOT/'metrics.json').read_text())['files']};rows=[]
    original=[]
    for key,title,statement,quote,limitation in BRIEFS:
        if key=='EFTA00039826':quote='the Government seeks a limited number of redactions, which are narrowly tailored to protect the privacy interests of third parties.'
        quotes=[quote]
        if key=='EFTA00039826':quotes.append("contained in filings regarding the defense's proposed Rule 17(c) subpoena.")
        if key=='EFTA00039881':quotes.append('MDC—Metropolitan Detention Center Legal Department')
        original.append((key,1,title,statement,quotes,limitation))
    for key,page,title,statement,quotes,limitation in original+EXTRA_BRIEFS:
        metric=metrics[key];extracted=json.loads((PILOT/metric['extraction_path']).read_text(encoding='utf-8'));text=extracted['pages'][page-1]['text']
        for quote in quotes:assert ' '.join(quote.split()) in ' '.join(text.split()),key
        rows.append(dict(file_id=key,source_sha256=metric['sha256'],title=title,
            scope=f'PDF page {page} only; not a whole-document summary',status='ai_assisted_editorial_draft',
            points=[dict(statement=statement,limitation=limitation,citations=[dict(page=page,quote=quote,page_text_sha256=hashlib.sha256(text.encode()).hexdigest()) for quote in quotes])]))
    reviews=original_reviews(rows)
    (PILOT/'timeframe-briefs.json').write_text(json.dumps(dict(schema_version=1,prepared_on='2026-11-02',updated_on='2026-11-07',method='Prepared by Codex from cited native page text with source-context checks. Editorial AI-assisted drafts, not human-verified findings. Filtering selects existing briefs; no live AI call or cross-document narrative generation.',briefs=rows),indent=2)+'\n',encoding='utf-8')
    (PILOT/'timeframe-brief-reviews.json').write_text(json.dumps(dict(schema_version=1,
        method='Codex editorial comparison of the original eight briefs with rendered PDF pages and native text. Same-assistant review; not independent or human verification. Two citation spans expanded before recording results.',reviews=reviews),indent=2)+'\n',encoding='utf-8')
    print(f'Prepared {len(rows)} page-scoped briefs.')


if __name__=='__main__':main()
