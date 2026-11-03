"""Reproduce eight curated AI-assisted page briefs, never live AI generation."""
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


def main():
    metrics={r['file_id']:r for r in json.loads((PILOT/'metrics.json').read_text())['files']};rows=[]
    for key,title,statement,quote,limitation in BRIEFS:
        metric=metrics[key];extracted=json.loads((PILOT/metric['extraction_path']).read_text(encoding='utf-8'));text=extracted['pages'][0]['text']
        assert ' '.join(quote.split()) in ' '.join(text.split()),key
        rows.append(dict(file_id=key,source_sha256=metric['sha256'],title=title,
            scope='PDF page 1 only; not a whole-document summary',status='ai_assisted_editorial_draft',
            points=[dict(statement=statement,limitation=limitation,citations=[dict(page=1,quote=quote,page_text_sha256=hashlib.sha256(text.encode()).hexdigest())])]))
    (PILOT/'timeframe-briefs.json').write_text(json.dumps(dict(schema_version=1,prepared_on='2026-11-02',method='Prepared by Codex from cited native page text with source-context checks. Editorial AI-assisted drafts, not human-verified findings. Filtering selects existing briefs; no live AI call or cross-document narrative generation.',briefs=rows),indent=2)+'\n',encoding='utf-8')
    print(f'Prepared {len(rows)} page-scoped briefs.')


if __name__=='__main__':main()
