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
EXTRA_BRIEFS = [('EFTA00005705',
  1,
  'Report on photographs received',
  'The report records receipt of eight photographs and says they will be forwarded separately.',
  ['Source also has received 8 current photographs of that were forwarded by to ATP-Jacksonville '
   'recently.These will be forwarded to MM under separate cover.'],
  'This summarizes what the report records; subjects and senders are redacted, and receipt or later '
  'forwarding is not independently confirmed.'),
 ('EFTA00009823',
  1,
  'Quoted publicity-value estimate',
  'A quoted email estimates the article discussed in the chain has more than $4 million in publicity value.',
  ['This article is estimated to have over $4M in publicity value. Insane.'],
  'The figure is attributed to a quoted message. Its calculation, readership and monetary value are not '
  'verified by this brief.'),
 ('EFTA00009853',
  1,
  'Quoted meeting arrangements',
  'A quoted message states that a meeting is confirmed for 3 p.m. on Monday.',
  ['We are confirmed for a meeting at 3:00 p.m. on Monday at See you then. Thanks.'],
  'This preserves the quoted scheduling statement. It does not identify redacted participants or locations, '
  'establish the meeting occurred, or resolve the outer reply mentioning 10/31.'),
 ('EFTA00009882',
  1,
  'Request for coordinator contact information',
  'A quoted message requests contact information for a national trafficking coordinator who had reached out '
  'the previous day.',
  ['Can you send us contact info for the National trafficking coordinator who reached out to you yesterday?'],
  'This is a request within a quoted exchange. Redacted identities and contact details are not '
  'reconstructed.'),
 ('EFTA00009890',
  1,
  'Intended filing of an attached letter',
  'The top-level sender says an attached letter is planned for filing that evening.',
  ['As discussed, attached is the letter that I plan to file this evening.'],
  'The brief reports an intention in the email; it does not authenticate the attachment or establish that '
  'the filing occurred.'),
 ('EFTA00039790',
  1,
  'Circulation of an opinion on pretrial motions',
  'The sender says Judge Nathan’s opinion on most of Maxwell’s pretrial motions is attached.',
  ["Judge Nathan's opinion on the majority of Maxwell's pretrial motions is attached."],
  'This summarizes the cover email. The attached opinion and the sender’s account of its rulings have not '
  'been independently checked in this brief.'),
 ('EFTA00039806',
  2,
  'Quoted proposal for a Tuesday meeting',
  'A reply within the forwarded chain says Tuesday at four is suitable.',
  ['Tuesday at 4 is good. Thanks.'],
  'The reply is part of an older quoted chain inside a reproduced outer email dated February 24, 2019. It '
  'does not establish that a meeting took place on that outer date.'),
 ('EFTA01263156',
  1,
  'Quoted change to travel plans',
  'A quoted notice says the Paris trip was canceled and describes planned travel from New York to Palm '
  'Beach.',
  ["Mr. Epstein's trip to Paris has been canceled. He will travel today from his vacation home in New York, "
   'New York to his vacation home in Palm Beach, Florida'],
  'This is the quoted notice’s account and plan. The containing outer email is dated October 10, 2018; this '
  'brief does not verify completed travel or assign that date to the quoted events.'),
 ('EFTA00008892',
  12,
  'Older letter reproduced in a presentation',
  'A reproduced letter says an envelope found while cleaning the Epstein Lodge is enclosed.',
  ['Enclosed is the envelope we recently found in cleaning the Epstein Lodge.', 'December 23, 1994'],
  'The embedded letter is dated December 23, 1994, while the containing presentation is dated June 29, 2020. '
  'The envelope’s contents and provenance are not authenticated by this brief.'),
 ('EFTA01263272',
  2,
  'Question about contacts before a subpoena',
  'The court asks about contacts between the U.S. Attorney’s Office and Boies Schiller before issuance of '
  'the subpoena.',
  ["I would like to know about contacts between the United States Attorney's Office and the Boies Schiller "
   'firm prior to the issuance of the subpoena on the subject of your investigation.'],
  'This describes a question recorded in the conference transcript. It is not a finding about improper '
  'contact or the merits of the subpoena.'),
 ('EFTA00008529',
  2,
  'Witness background in the June 2019 session',
  'The witness identifies their employer as the FBI, their title as special agent, and their assignment as '
  'the Violent Crimes Against Children squad.',
  ['A. The FBI.', 'A. Special Agent.', 'A. The Violent Crimes Against Children squad.'],
  'This covers introductory testimony only. The witness’s redacted identity is not reconstructed and later '
  'testimony is not summarized.'),
 ('EFTA00008585',
  2,
  'Witness reports an earlier appearance',
  'The witness states that they testified before the grand jury on June 18, 2019.',
  ['Q. Did you testify before this grand jury on June 18th, 2019? A. I did.'],
  'This attributes the answer to the witness in the July 2 session; it does not compare or assess the two '
  'sessions’ testimony.'),
 ('EFTA00008631',
  2,
  'Microphone instructions and witness background',
  'The examiner asks the masked witness behind Plexiglas to speak into the microphone; the witness '
  'identifies their employer as the FBI and title as special agent.',
  ['you are wearing a mask',
   "behind Plexiglas. There's a microphone in front of you",
   'A. The Federal Bureau of Investigation.',
   'A. Special agent.',
   'you could just make an effort to speak into the mic and keep your voice up that would be great.'],
  'This describes introductory courtroom arrangements and answers only, without identifying the redacted '
  'witness or summarizing later testimony.'),
 ('EFTA00008708',
  2,
  'Proposed correction of indictment errors',
  'The prosecutor says the proposed superseding indictment corrects two clerical errors in Counts Five and '
  'Six and says no new evidence or witnesses will be presented that day.',
  ['it corrects two clerical errors, or two typographical errors that were contained in Counts Five and Six '
   'which are the perjury charges.',
   'As a result, I will not be presenting any new evidence or new witnesses today.'],
  'This records the prosecutor’s explanation and intended procedure, not a finding on the charges or '
  'confirmation of the session’s eventual outcome.'),
 ('EFTA00008744',
  2,
  'Detective’s introductory testimony',
  'The witness identifies their employer as the New York City Police Department, their title as detective, '
  'and their service as about fifteen years.',
  ['A. New York City Police Department.', 'A. Detective.', 'A. About 15 years.'],
  'This covers introductory answers only. It does not reconstruct the redacted identity or assess later '
  'testimony.'),
 ('EFTA00009229',
  3,
  'Opening of the Acosta interview',
  'The transcript records Acosta being sworn, and an examiner identifies herself as counsel with DOJ’s '
  'Office of Professional Responsibility.',
  ['was called as a witness and, having been first duly sworn,',
   'I am a counsel with the Office of Professional',
   'Responsibility here at the Department of Justice, and with me'],
  'This is an opening-procedure brief, not a summary of Acosta’s substantive account or OPR findings.'),
 ('EFTA02212961',
  1,
  'Itinerary details in an email',
  'The message lists proposed departures and arrivals involving VKO, St. Petersburg and CDG, followed by an '
  'incomplete line for a CDG-to-SVO leg.',
  ['Depart St. Petersburg 8:35am arrive CDG 3:30pm',
   'May 17th: Depart CDG 6:10pm arrive SVO (not',
   'May 16th: departing VKO 11:55pm'],
  'These are itinerary statements, not evidence of completed travel. The incomplete final line and redacted '
  'participants are not reconstructed.'),
 ('EFTA02212972',
  1,
  'Forwarded store contact information',
  'A forwarded message attributed to Karyna Shuliak says store contact information is provided and '
  'references a screenshot.',
  ['Here is their store contact info. Thank you.',
   '<Screen Shot 2017-05-01 at 2.26.04 PM.png>',
   'From: Karyna Shuliak'],
  'The brief describes the forwarded message only; it does not authenticate or summarize the referenced '
  'screenshot or establish a transaction.'),
 ('EFTA02730265',
  1,
  'Requested changes to proposed points',
  'The top-level message attributed to Boris Nikolic requests changing a date to the end of January and '
  'changing the last point about help finding a job.',
  ['In addition to changing date to the end of January, the last point need to total change re helping me '
   'find a job',
   'From: Boris Nikolic'],
  'This is a request concerning proposed wording. It does not establish acceptance, execution of an '
  'agreement, or authenticity of the quoted terms or signature text.'),
 ('EFTA02731485',
  1,
  'Referral-update email lists records',
  'The sender says conversation notes, initial referral-call notes and correspondence with counsel are '
  'attached for recipients’ records.',
  ["I'm attaching notes of today's conversation with counsel, notes of the initial referral call, and the "
   "email correspondence I've had with counsel for your records."],
  'This summarizes the cover email’s account only. It does not verify attachments, allegations, follow-up '
  'actions or investigative conclusions.'),
 ('EFTA00008920',
  2,
  'Introductory FBI testimony reproduced in a transcript',
  'The witness identifies their employer as the FBI, their title as special agent, and their service as '
  'about three years.',
  ['A. The Federal Bureau of Investigation.', 'A. Special agent.', 'A. About three years, three years now.'],
  'This covers introductory answers only. This page resembles the opening in EFTA00008631; the two PDF '
  'records do not establish separate testimony or independent corroboration. The redacted identity is not '
  'reconstructed.'),
 ('EFTA00009440',
  4,
  'Witness describes records returned under subpoenas',
  'The witness says documents covering two bank subpoenas were received from Colonial Bank on April 25, '
  '2007, and describes records returned by Western Union in two packages.',
  ['We did receive documents back from Colonial',
   'Bank, which covered both subpoenas, on April 25, 2007.',
   'received items back from western Union on two separate',
   'dates, and two packages, the first on April 9, 2007, and',
   'the second on April 11, 2007.'],
  'This attributes the account to testimony in the May 8 session. The brief does not authenticate the '
  'returned records, infer their contents, or treat the session date as a transaction date.'),
 ('EFTA00009448',
  3,
  'Witness corrects an earlier age statement',
  'The witness says an earlier statement confused Epstein’s age with another person’s and gives his age '
  'during 2004–2005 as about 51 or 52 rather than 45.',
  ["I did. I was asked by one of you Mr. Epstein's",
   'age, and I confused him with another individual in another',
   'one of my cases.',
   'are looking at the time period of 2004 and 2005. So',
   'Mr. Epstein would have been about 51 or 52-years-old, and',
   "I believe I told you he was 45. So at the time we're",
   'looking during this investigation, he is 51 or 52.'],
  'This reports the witness’s correction in the February 27, 2007 session. It does not independently verify '
  'biographical details or summarize the earlier testimony.'),
 ('EFTA00009478',
  3,
  'Witness says photographs were obtained',
  'Asked whether photographs of the two people discussed in prior testimony were obtained, the witness '
  'answers yes.',
  ['Q Did you obtain photographs of those', 'girls?', 'A Yes, I did.'],
  'This reports a question and answer in the March 20 session. It does not identify the redacted people, '
  'authenticate or reproduce photographs, or independently confirm earlier testimony.'),
 ('EFTA00009502',
  3,
  'FBI agent’s introductory identification',
  'The witness describes themself as an FBI special agent working in Palm Beach.',
  ['a special agent with the FBI and I work here in Palm Beach.'],
  'This covers an introductory answer only. The redacted name is not reconstructed, and later testimony and '
  'allegations are not summarized.'),
 ('EFTA00009512',
  2,
  'Witness identifies the investigation',
  'The witness says they work for the FBI in West Palm Beach and confirms appearing for the continuing '
  'investigation called Operation Leap Year.',
  ['A The FBI here in West Palm Beach.',
   'Q And are you here today on the continuing',
   'investigation known as Operation Leap Year?',
   'A Yes, I am.'],
  'This covers introductory testimony in the May 15 session. It does not identify the redacted witness or '
  'evaluate investigative findings.'),
 ('EFTA00009586',
  4,
  'Witness confirms receiving a grand-jury subpoena',
  'Asked whether they were served with a subpoena to appear before the grand jury that day, the witness '
  'answers yes.',
  ['Q Were you served with a subpoena to appear before the grand jury today? A Yes.'],
  'This covers a procedural question and answer in the April 24 session. PDF page 4 carries internal '
  'transcript page 3. The witness’s identity and redacted address are not reconstructed, and substantive '
  'testimony is not summarized.'),
 ('EFTA00009632',
  2,
  'Witness identifies FBI employment',
  'In the introductory exchange, the witness says they work for the FBI in Palm Beach County.',
  ['the FBI in Palm Beach County.'],
  'This covers the introductory employment answer in the February 6 session only. The redacted identity is '
  'not reconstructed; later testimony is outside this brief.')]


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

REVIEW_NOTES.update({'EFTA00005705': ('supported_as_scoped', 'The report records eight photographs and intended forwarding; redacted subjects remain unidentified.'), 'EFTA00009823': ('supported_as_scoped', 'The publicity estimate is quoted opinion, not a verified valuation or readership count.'), 'EFTA00009853': ('supported_as_scoped', 'The quoted Monday arrangement and outer 10/31 reply remain distinct; attendance is not established.'), 'EFTA00009882': ('supported_as_scoped', 'The quoted contact-information request is supported; redacted identities are not reconstructed.'), 'EFTA00009890': ('supported_as_scoped', 'The top-level intended filing is supported; actual filing and attachment contents are not established.'), 'EFTA00039790': ('supported_as_scoped', 'The excerpt supports circulation of an opinion; the brief does not adopt the email’s characterization of rulings.'), 'EFTA00039806': ('supported_as_scoped', 'The Tuesday reply belongs to the older quoted chain, not the February 2019 outer date.'), 'EFTA01263156': ('supported_as_scoped', 'The quoted notice describes canceled and planned travel; the outer October date is not assigned to those events.'), 'EFTA00008892': ('supported_as_scoped', 'The reproduced December 1994 letter is distinct from the June 2020 presentation; provenance is not authenticated.'), 'EFTA01263272': ('supported_as_scoped', 'The court asks about pre-subpoena contacts; this question is not a finding of misconduct.')})
REVIEWED_FINGERPRINTS.update({'EFTA00005705': '60e21bbd26291d74d10fbe426ff1ba90208894dfde4f4742d65a7383b5fea537', 'EFTA00009823': '819e930e6467c22daba9fbffb67135fe45ffbafee5ee4d6b65006c041ead2345', 'EFTA00009853': '6216fecfc5c6e1927d5e1d5be4419a507552dea9c3245f80a9b6bb7593ff33a6', 'EFTA00009882': 'c59f3206feaee3b98f326f387afacf3c0605a71c1f4bed2e35c29fb6d1f1dda6', 'EFTA00009890': '4129b493e5543c81f995738b26b44dc13e2953128ecbebc8dcb2f64a29a6cbf1', 'EFTA00039790': 'e0407fc70258d83dc5057d2553b1d5c921c7be7208dfcc961cb3356544690146', 'EFTA00039806': '008d1a486faffd69faf086a5a081b072d7b013f4a9954064e7bfd2be855c2518', 'EFTA01263156': 'de987715efe95341711d04120fc20e09145cbdd353d798a621d32a7d431d38d4', 'EFTA00008892': 'a1d1fb0436719aa86d3b970fa146178d302fa3d9a66c0909f92d963dac1b9ad8', 'EFTA01263272': 'b82fe8edd7e0dc104ef40f12ed55b25c21e81c7f75138b1999c2102744852dba'})


# Third source-check batch: reviewed against rendered pages and native text.
REVIEW_NOTES.update({'EFTA00008529': ('supported_as_scoped',
                  'Introductory answers support employer, title and squad assignment. Redacted identity and '
                  'later testimony remain outside scope.'),
 'EFTA00008585': ('supported_as_scoped',
                  'The question and answer support the claimed earlier appearance as witness testimony, '
                  'without assessing either session.'),
 'EFTA00008631': ('supported_after_citation_expansion',
                  'Added the microphone instruction to the cited mask, Plexiglas and employment excerpts. '
                  'The brief remains limited to introductory arrangements and answers.'),
 'EFTA00008708': ('supported_as_scoped',
                  'The prosecutor explains proposed clerical corrections and intended procedure. The brief '
                  'does not convert this explanation into a finding or completed outcome.'),
 'EFTA00008744': ('supported_as_scoped',
                  'The introductory answers support NYPD employment, detective title and approximate '
                  'service. The redacted identity remains unreconstructed.'),
 'EFTA00009229': ('supported_after_citation_expansion',
                  'Expanded the citation with the rest of the OPR office name. Rendered page confirms the '
                  'sworn opening; the brief does not summarize substantive testimony.'),
 'EFTA02212961': ('supported_after_citation_expansion',
                  'Added the VKO departure excerpt to support all airports named in the statement. Itinerary '
                  'lines remain plans; the incomplete SVO line is preserved.'),
 'EFTA02212972': ('supported_after_citation_expansion',
                  'Added the forwarded sender heading to support attribution. The brief describes '
                  'contact-information circulation, without authenticating the screenshot or inferring a '
                  'transaction.'),
 'EFTA02730265': ('supported_after_citation_expansion',
                  'Added the top-level sender heading to support attribution. Requested draft changes are '
                  'not treated as an accepted or executed agreement.'),
 'EFTA02731485': ('supported_as_scoped',
                  'The cover-email sentence supports the list of attached records. The brief does not '
                  'authenticate attachments or adopt allegations or investigative conclusions.')})
REVIEWED_FINGERPRINTS.update({'EFTA00008529': '2a0d25ed4fb8b13265ac9dde7c18b1767e909d37d9cb99c0f455691f3bbfaab9',
 'EFTA00008585': 'f34f0b757764c5995a94cd3cf2ac5d0735fe3bfc89982906b70fe5e7ffd0d4c3',
 'EFTA00008631': '15d9a2daed83afc14756c55ffd80e931de54c3d02a7c3d47585514250873dfab',
 'EFTA00008708': '9c98bd3bd8ed83a6a8c2cb1407c1ebf7c8b915e42ff55d7ec11239ba88ebfb54',
 'EFTA00008744': '695471d7b181ceb62988f33cdef77ea6b37ea8a1c3500456a013e36cc4438c16',
 'EFTA00009229': '1483f390752e70b54c2983162ebe3b20325c0238282c16317c2198bbad6be408',
 'EFTA02212961': 'afe63a11bfbff1b3d98d0e7b6cc7d0981739f2200ef786878f3b40cb1ba141ea',
 'EFTA02212972': '99b8a354d461af836fc1dec38c9d11e3be854481c70d5b0a9e4880b3bff98c9c',
 'EFTA02730265': 'daa58727ec92cb9ab0baad4572867195c919cfa96fe83ca962f8a7b99b4bf1c2',
 'EFTA02731485': 'f79c1ef7cbf44a4e6f4141477ef28cab6161a65824db947e4db2949fd0bf34c1'})

def recorded_reviews(rows):
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
    reviews=recorded_reviews(rows)
    (PILOT/'timeframe-briefs.json').write_text(json.dumps(dict(schema_version=1,prepared_on='2026-11-02',updated_on='2026-11-07',method='Prepared by Codex from cited native page text with source-context checks. Editorial AI-assisted drafts, not human-verified findings. Filtering selects existing briefs; no live AI call or cross-document narrative generation.',briefs=rows),indent=2)+'\n',encoding='utf-8')
    (PILOT/'timeframe-brief-reviews.json').write_text(json.dumps(dict(schema_version=1,
        method='Codex editorial comparison of twenty-eight briefs with rendered PDF pages and native text. Same-assistant review; not independent or human verification. Recorded checks are pinned to the reviewed prose, citations and source hashes; newly prepared briefs await a separate pass.',reviews=reviews),indent=2)+'\n',encoding='utf-8')
    print(f'Prepared {len(rows)} page-scoped briefs.')


if __name__=='__main__':main()
