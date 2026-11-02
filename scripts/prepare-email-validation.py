"""Reproduce three curated, visually checked email-candidate review batches."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PILOT=ROOT/'data/pilot/2026-11-01'
# Existing parser IDs are pinned: edits that change candidate boundaries require re-review.
CASES=[
 ('022880aeabb821e3cb47','supported_segment','supported_header','March 11, 2020','Top-level header and body segment before the next From header are supported; participants are redacted.'),
 ('66eff07cc17a5fd96448','contains_unseparated_quote','supported_header','March 11, 2020','Body includes an On Mar 11 ... wrote inline quote that has not been separated into its own candidate.'),
 ('ca7aba4de49390514990','supported_segment','supported_header','December 15, 2020','Top-level header/body plus signature are supported; sender name is visible but address is redacted.'),
 ('dcdfb98c39e661acdd56','supported_segment','supported_header','December 15, 2020','Quoted From/Sent/To header is distinct from the enclosing email; recipient name does not recover its redacted address.'),
 ('19aa0f3f34706fc3d55c','supported_segment','supported_header','April 20, 2021','Top-level body ends before a new quoted From header; attachments and their contents are not authenticated by this review.'),
 ('2bfc50c1f44c7b6a75ae','supported_segment','supported_header','April 14, 2021','Top-level short reply is separated from the quoted lead; missing extracted recipient data stays unresolved.'),
 ('e9da69973d30a4f07596','supported_segment','supported_header','April 16, 2021','Wrapped recipient header belongs to one visible email; this review does not review the referenced attachment.'),
 ('b9ff80e2590d56273c86','contains_unseparated_quote','supported_header','February 24, 2019','Body still contains a forwarded March 3, 2016 header that the parser does not separate reliably.'),
 ('388ffd1fe06f04125bc9','supported_segment','visual_reading_needed','October 10, 2018','Visible Sent header reads Wednesday, October 10, 2018 4:37 PM. Extracted month text is damaged; raw parser output remains unchanged.'),
 ('9bb8c3740897e64ccced','supported_segment','supported_header','September 30, 2018','Quoted travel-notice header is visible and distinct; native source-stamp artifacts remain in the body and participant addresses are redacted.'),
 ('07a75fa3cb927f8462f2','supported_segment','sent_date_unresolved',None,'Visible inline May 18, 2017 body date is not a labeled Sent value. No sent date or participants are assigned.'),
 ('d96e7b11d461cd95865e','contains_unseparated_quote','numeric_context_supported','May 1, 2017','Quoted textual May 1 dates support this source-specific interpretation of 5/1/2017. The body includes an unseparated inline quoted reply; no global US date assumption is made.'),
 ('753db62ec7c78cb9166b','contains_unseparated_quote','supported_header','May 1, 2017','Forwarded header is supported, but its body includes an On May 1 ... wrote inline quote. Visible sender and recipient associations are recorded separately.'),
 ('2892ff7d0d642ac60543','supported_segment','supported_header','August 24, 2013','Top-level body is distinct from the forwarded thread. To-address is readable visually although native extraction damages the @ sign.'),
 ('e158e5711ea1a7e5ec98','forwarding_wrapper_only','supported_header','August 24, 2013','The authored body segment is only a forwarding wrapper; the substantive message is quoted content. Do not count it as an independently validated communication.')
]
ASSOCIATIONS=[
 ('jeffrey-epstein-header','2892ff7d0d642ac60543','to','Jeffrey Epstein','jeevacation@gmail.com',True,'Jeffrey Epstein <jeevacation@gmail.com>'),
 ('karyna-shuliak-header','753db62ec7c78cb9166b','from','Karyna Shuliak','karynashuliak@icloud.com',False,'Karyna Shuliak <karynashuliak@icloud.com>'),
 ('richard-kahn-header','753db62ec7c78cb9166b','to','Richard Kahn','richardkahn12@gmail.com',True,'Richard Kahn <richardkahn12@gmail.com>')
]

# Batch 2: prioritize unreviewed candidates with address-like headers, then
# document/page/line order. This deliberately favors readable material.
SECOND_CASES=[
 ('c291eeac30d73cc90e11','supported_segment','September 29, 2018','Quoted travel-notice header and visible body are supported. Recipient addresses are redacted; source stamps remain in native body text.'),
 ('c8ae0d938c81d8f82cbb','continuation_unverified','September 20, 2018','Quoted header is readable, but the detected body ends mid-sentence on this PDF page. Continuation is not established by this review.'),
 ('9cf5407ca855a7a4d363','supported_segment','August 28, 2018','Quoted header and visible travel-notice body are supported. A visible recipient name does not recover its redacted address.'),
 ('e13447c87449af4edeab','supported_segment','August 25, 2018','Visible header supports the displayed sender label and date; native extraction damages the sender address. Redacted recipients remain unresolved.'),
 ('ab0a503da83cba1cc31c','supported_segment','July 27, 2018','Quoted From/Sent header and travel-notice body are visible. Redacted To and Cc addresses remain unresolved.'),
 ('28984839a8f9503eef64','supported_segment','July 18, 2018','Quoted header and visible travel-notice body are supported; the source date reading does not replace the parser timestamp.'),
 ('194c5439a3112fafc567','continuation_unverified','July 10, 2018','Visible quoted header is supported, but the detected body ends mid-sentence at the page boundary; full continuation remains unverified.'),
 ('660e0dd9e03db8685564','continuation_unverified','March 27, 2018','Visible quoted header is supported; native extraction damages its sender address. Body ends mid-sentence and continuation remains unverified.'),
 ('82133ccb2a72e269e411','supported_segment','March 12, 2018','Quoted header, body and closing signature are visible. Repeated sender/address observations are not additional unique contacts.'),
 ('4cb9069cf27fc96220af','contains_unseparated_quote','May 1, 2017','Forwarded header begins on PDF page 1 and its recipient/body continue on pages 2 and 3. Body includes another inline quote and duplicated disclaimer text; unique message and boundaries remain unverified.'),
 ('6bf18e2f12fd90426c42','supported_segment','March 11, 2020','Distinct forwarded header and short body are visible before the next From block. Wrapped subject text is misplaced in the native body; no participant is reconstructed.'),
 ('5cfa5b370c0bc48d0f58','supported_segment','March 11, 2020','Critical Mention alert header on page 1 and alert content on page 2 are visible. Sender extraction is damaged; this automated alert is not evidence of a personal correspondent.'),
 ('229b0912ae9c1a3d0c0f','contains_unseparated_quote','October 28, 2019','Top-level header is visible, but body contains two inline quoted replies. Sender and recipient addresses are redacted.'),
 ('bea9a420b2163bebf321','supported_segment','December 15, 2020','Quoted sender name, Sent header and short reply are visible. Signature continues on page 2 before the next From header; email addresses remain redacted.'),
 ('d5854f1cfc605aeed1d1','supported_segment','December 15, 2020','Quoted header and short body are supported by the PDF layout. Recipient name is visible but the address is redacted.')
]
CASES += [(key,boundary,'visual_source_reading',day,notes) for key,boundary,day,notes in SECOND_CASES]
# Explicit PDF clock readings where the existing parsed candidate has lost PM.
CLOCK_CONFLICTS={
 '66eff07cc17a5fd96448':'7:03 PM',
 'e13447c87449af4edeab':'7:30 PM',
 '28984839a8f9503eef64':'2:32 PM',
 '6bf18e2f12fd90426c42':'6:25 PM',
 '5cfa5b370c0bc48d0f58':'6:02 PM',
}
for key in ('c291eeac30d73cc90e11','ab0a503da83cba1cc31c','28984839a8f9503eef64','82133ccb2a72e269e411'):
    ASSOCIATIONS.append((f'darren-header-{key}',key,'from','Darren Indyke','dkiesq@aol.com',False,'Darren Indyke [mailto:dkiesq@aol.com]'))
for key in ('c8ae0d938c81d8f82cbb','9cf5407ca855a7a4d363','e13447c87449af4edeab','194c5439a3112fafc567','660e0dd9e03db8685564'):
    ASSOCIATIONS.append((f'jeffrey-e-header-{key}',key,'from','jeffrey E.','jeevacation@gmail.com',key in ('e13447c87449af4edeab','660e0dd9e03db8685564'),'jeffrey E. [mailto:jeevacation@gmail.com]'))
ASSOCIATIONS.append(('richard-forwarded-header','4cb9069cf27fc96220af','from','Richard Kahn','richardkahn12@gmail.com',True,'Richard Kahn <richardkahn12@gmail.com>'))

# Batch 3: one unreviewed candidate per non-travel-notice document in source
# order, then a second pass through documents, stopping at fifteen candidates.
THIRD_CASES=[
 ('c798a9eaea11eb5c32c0','supported_segment','December 15, 2020','legal_or_investigative','Quoted header and body are distinct from neighboring emails. Recipient display name Sigrid McCawley is visible; participant addresses remain redacted.'),
 ('11eecac9a796472952ff','supported_segment','February 26, 2019','legal_or_investigative','Top-level header and short body are visible before an Original Message block. Native extraction damages the subject; redacted coordinator contact details remain unresolved.'),
 ('fb61f87c39749a7119f6','supported_segment','April 20, 2021','legal_or_investigative','Quoted header and body continue from PDF page 1 onto page 2 before the next header. Visible Sent time is 2:05 PM; extraction joins the year and time. Attachments are referenced, not authenticated.'),
 ('593293562bc919b11538','supported_segment','April 14, 2021','legal_or_investigative','Quoted header and referral body are visible. Allegations in the body are not findings verified by this layout review; redacted participants and contact details remain unresolved.'),
 ('579aea33f4b2a17ced01','supported_segment','March 3, 2016','legal_or_investigative','Visible quoted header has a March 3, 2016 5:05 PM Sent value and a short reply before the next header. OCR damages the date and subject; source reading stays separate.'),
 ('1b356869537054b44603','contains_unseparated_quote','April 6, 2017','scheduling_or_logistics','Top-level To label Larry Visoski is visible but address is redacted. Several inline replies with increasing quote markers remain in the detected body. Textual April 6 dates support this source-specific reading of 4/6.'),
 ('c669ce63be2e9e4248b8','contains_unseparated_quote','May 3, 2017','scheduling_or_logistics','Visible recipient label Melanie Spinella is absent from native To extraction. Body contains inline and Original Message quotes on page 1 and repeated disclaimers on page 2. Redacted addresses are not reconstructed.'),
 ('91f790caeb30aa66bf06','supported_segment',None,'reminder','Visible item is a reminder-like Alert with a May 23, 2017 2:00 PM event in its body. No labeled sent date is visible; the event date is not assigned as a message timestamp or proof of a completed call.'),
 ('99401e883858025e2c23','contains_unseparated_quote','May 3, 2017','scheduling_or_logistics','Top-level From Oliver Lloyd and To Lesley Groff labels are visible; addresses remain redacted. Body spans three PDF pages with inline replies and a forwarded message. Mentioned names do not establish direct correspondence with those people.'),
 ('997943e85ddc97fd238f','contains_unseparated_quote','May 16, 2017','scheduling_or_logistics','Visible Sent header reads Tuesday 5/16/2017 2:13:52 PM; extraction loses much of it and a From field. Body includes an inline quoted reply. Flight text does not verify that travel occurred.'),
 ('13f7e4c60b42a1597702','supported_segment',None,'forwarded_document','Forwarded header and document-like body span two PDF pages. Date is partly obscured or damaged; no full sent date is assigned. Different visible signature labels and disclaimer text are retained without attributing authorship or authenticating the apparent terms.'),
 ('d79029b99b16df494822','supported_segment','June 12, 2023','legal_or_investigative','Visible header, body and listed attachment filenames are supported. Participants are redacted; names in the subject or body are not inferred to be correspondents. Referenced attachments and underlying allegations are not authenticated.'),
 ('cb028137229099c414b0','supported_segment','December 14, 2020','legal_or_investigative','Quoted email begins on PDF page 2 and continues onto page 3 with an embedded statement, closing signature and disclaimer. The statement is quoted document content, not an independently counted email or verified factual account.'),
 ('59a4ffec2970fcaa5f43','supported_segment','February 26, 2019','legal_or_investigative','Original Message header and short request are visible. The source shows a To label omitted by native parsing, but its value and participant addresses remain redacted.'),
 ('483ab91c287adab14175','supported_segment','April 19, 2021','legal_or_investigative','Quoted header on PDF page 2 reads Monday April 19, 2021 8:27 PM. Short body and closing continue onto page 3 before the next header; damaged raw date remains unchanged.')
]
CASES += [(key,boundary,'sent_date_unresolved' if day is None else 'visual_source_reading',day,notes)
          for key,boundary,day,kind,notes in THIRD_CASES]
THIRD_KINDS={key:kind for key,boundary,day,kind,notes in THIRD_CASES}
ASSOCIATIONS.append(('jeffrey-recipient-forwarded-points','13f7e4c60b42a1597702','to','Jeffrey Epstein','jeevacation@gmail.com',True,'Jeffrey Epstein <jeevacation@gmail.com>'))


def main():
    catalog=json.loads((ROOT/'data/viewer/emails.json').read_text(encoding='utf-8'))
    records={r['id']:r for r in catalog['records']}
    metrics={r['file_id']:r for r in json.loads((PILOT/'metrics.json').read_text(encoding='utf-8'))['files']}
    reviews=[]
    for key,boundary,date_status,source_day,notes in CASES:
        r=records[key];metric=metrics[r['file_id']]
        extracted=json.loads((PILOT/metric['extraction_path']).read_text(encoding='utf-8'))
        anchor=extracted['pages'][r['source_page']-1]['text'].splitlines()[r['source_line']-1].strip()
        reviews.append({'record_id':key,'file_id':r['file_id'],'source_sha256':r['source_sha256'],'visible_fingerprint':r['visible_fingerprint'],
            'source_page':r['source_page'],'source_line':r['source_line'],'extracted_anchor':anchor,
            'header_status':'source_layout_supported','boundary_status':boundary,'date_status':date_status,
            'source_day_reading':source_day,'notes':notes,'review_status':'source_assisted_editorial_review',
            'unique_message_verified':False,'contact_count_eligible':False})
        if key in CLOCK_CONFLICTS:
            reviews[-1]['source_clock_reading']=CLOCK_CONFLICTS[key]
            reviews[-1]['parsed_clock_conflict']=True
        if key in THIRD_KINDS:
            reviews[-1]['review_batch']='batch-3-broader-correspondence'
            reviews[-1]['correspondence_kind']=THIRD_KINDS[key]
    associations=[]
    for key,record,field,name,address,corrected,quote in ASSOCIATIONS:
        r=records[record]
        associations.append({'id':key,'record_id':record,'field':field,'display_name':name,'address':address,
            'source_sha256':r['source_sha256'],'file_id':r['file_id'],'source_page':r['source_page'],
            'visible_header_reading':quote,'raw_extracted_field':r['headers'].get(field,''),
            'visual_correction':corrected,'status':'observed_name_address_association',
            'ownership_verified':False,'apply_globally':False})
    output={'schema_version':1,'parser_version':catalog['summary']['parser_version'],
        'review_method':'Codex visually compared three purposive batches of 15 candidates each with rendered PDF pages and selected body continuations. Batch 2 prioritizes readable address-like headers; batch 3 samples across non-travel-notice documents in source order. This is not human verification, authentication, or a corpus-wide accuracy estimate.',
        'scope':'Raw parser fields and flags are preserved. Reviews do not establish unique messages, account ownership, address aliases elsewhere, or contact rankings.',
        'reviews':reviews,'address_associations':associations}
    (PILOT/'email-validation.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
    print(f'Prepared {len(reviews)} reviews and {len(associations)} observed header associations.')


if __name__=='__main__':main()
