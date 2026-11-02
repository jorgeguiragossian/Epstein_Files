"""Reproduce curated body partitions and adjacent-page continuation checks."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PILOT=ROOT/'data/pilot/2026-11-01'
# These are explicit editorial ranges, not general quote-detection rules.
CASES={
 '66eff07cc17a5fd96448':([(13,13,'uncertain_header_continuation'),(14,15,'authored_text_candidate'),(16,16,'signature'),(17,19,'inline_quote')],None),
 'b9ff80e2590d56273c86':([(7,7,'signature'),(8,13,'forwarded_quote')],None),
 'd96e7b11d461cd95865e':([(6,6,'authored_text_candidate'),(7,14,'inline_quote')],None),
 '753db62ec7c78cb9166b':([(21,23,'authored_text_candidate'),(24,25,'inline_quote_header_only')],'4cb9069cf27fc96220af'),
 'e158e5711ea1a7e5ec98':([(11,11,'forwarding_wrapper')],'13f7e4c60b42a1597702'),
 '229b0912ae9c1a3d0c0f':([(6,6,'authored_text_candidate'),(7,7,'signature'),(8,10,'inline_quote'),(11,14,'inline_quote')],None),
 '4cb9069cf27fc96220af':([(2,2,3,'authored_text_candidate'),(2,4,10,'signature'),(2,11,15,'inline_quote'),(2,16,28,'disclaimer'),(2,29,30,'disclaimer'),(3,1,11,'disclaimer')],None),
}
CONTINUATIONS={
 'c8ae0d938c81d8f82cbb':(6,'0695bb4eaad9e9f39eb0','September 20 notice ends mid-sentence on PDF page 5. Page 6 contains a separate September 12 notice beneath a new forwarding header; it does not supply the missing continuation.'),
 '194c5439a3112fafc567':(16,'ec75f35adf47d4dd6fa6','July 10 notice ends mid-sentence on PDF page 15. Page 16 contains a separate June 26 notice beneath a new forwarding header; it does not supply the missing continuation.'),
 '660e0dd9e03db8685564':(26,'8bb3b4c04c20f996f907','March 27 notice ends mid-sentence on PDF page 25. Page 26 contains a separate March 26 notice beneath a new forwarding header; it does not supply the missing continuation.'),
}


def main():
    catalog=json.loads((ROOT/'data/viewer/emails.json').read_text(encoding='utf-8'))
    records={r['id']:r for r in catalog['records']}
    metrics={r['file_id']:r for r in json.loads((PILOT/'metrics.json').read_text())['files']}
    annotations=[]
    for key,(ranges,child) in CASES.items():
        r=records[key];metric=metrics[r['file_id']]
        extraction=json.loads((PILOT/metric['extraction_path']).read_text(encoding='utf-8'))
        spans=[]
        for span_range in ranges:
            page,start,end,kind=span_range if len(span_range)==4 else (r['source_page'],*span_range)
            lines=extraction['pages'][page-1]['text'].splitlines()
            text='\n'.join(line.strip() for line in lines[start-1:end] if line.strip())
            spans.append(dict(id=f'{key}-p{page}-l{start}-{end}',parent_record_id=key,
                page=page,line_start=start,line_end=end,kind=kind,text=text,
                text_sha256=hashlib.sha256(text.encode()).hexdigest()))
        annotations.append(dict(record_id=key,file_id=r['file_id'],source_sha256=r['source_sha256'],
            visible_fingerprint=r['visible_fingerprint'],spans=spans,following_quoted_candidate_id=child,
            review_status='editorial_partition_not_verified_messages'))
    checks=[]
    for key,(page,other,notes) in CONTINUATIONS.items():
        r=records[key];neighbor=records[other];metric=metrics[r['file_id']]
        extraction=json.loads((PILOT/metric['extraction_path']).read_text(encoding='utf-8'))
        lines=extraction['pages'][page-1]['text'].splitlines()
        # Pin the new forwarded-message header without inferring account identity.
        end=max(h['line'] for h in neighbor['header_evidence'] if h['page']==page)
        text='\n'.join(line.strip() for line in lines[neighbor['source_line']-1:end])
        checks.append(dict(record_id=key,file_id=r['file_id'],source_sha256=r['source_sha256'],
            visible_fingerprint=r['visible_fingerprint'],next_page=page,neighbor_record_id=other,
            neighbor_fingerprint=neighbor['visible_fingerprint'],line_start=neighbor['source_line'],line_end=end,
            header_text=text,header_sha256=hashlib.sha256(text.encode()).hexdigest(),
            finding='adjacent_page_is_different_message',notes=notes))
    output=dict(schema_version=1,parser_version=catalog['summary']['parser_version'],
        method='Codex editorial partitions of previously visually inspected PDF pages, bound to exact extraction ranges. Quoted spans are not new verified messages; participant/date extraction is not inferred from these spans.',
        annotations=annotations,continuation_checks=checks)
    (PILOT/'email-boundaries.json').write_text(json.dumps(output,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f'Prepared {len(annotations)} source-bound body partitions.')


if __name__=='__main__':main()
