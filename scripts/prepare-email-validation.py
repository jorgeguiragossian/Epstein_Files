"""Reproduce 15 curated, visually checked email-candidate reviews."""
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
    associations=[]
    for key,record,field,name,address,corrected,quote in ASSOCIATIONS:
        r=records[record]
        associations.append({'id':key,'record_id':record,'field':field,'display_name':name,'address':address,
            'source_sha256':r['source_sha256'],'file_id':r['file_id'],'source_page':r['source_page'],
            'visible_header_reading':quote,'raw_extracted_field':r['headers'].get(field,''),
            'visual_correction':corrected,'status':'observed_name_address_association',
            'ownership_verified':False,'apply_globally':False})
    output={'schema_version':1,'parser_version':catalog['summary']['parser_version'],
        'review_method':'Codex visually compared 15 purposively selected candidates with 10 rendered PDF pages, including enlarged header crops. This is not human verification, authentication, or a corpus-wide accuracy estimate.',
        'scope':'Raw parser fields and flags are preserved. Reviews do not establish unique messages, account ownership, address aliases elsewhere, or contact rankings.',
        'reviews':reviews,'address_associations':associations}
    (PILOT/'email-validation.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
    print(f'Prepared {len(reviews)} reviews and {len(associations)} observed header associations.')


if __name__=='__main__':main()
