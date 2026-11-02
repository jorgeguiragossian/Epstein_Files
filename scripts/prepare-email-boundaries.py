"""Reproduce curated source-line partitions of five reviewed candidate bodies."""
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
}


def main():
    catalog=json.loads((ROOT/'data/viewer/emails.json').read_text(encoding='utf-8'))
    records={r['id']:r for r in catalog['records']}
    metrics={r['file_id']:r for r in json.loads((PILOT/'metrics.json').read_text())['files']}
    annotations=[]
    for key,(ranges,child) in CASES.items():
        r=records[key];metric=metrics[r['file_id']]
        extraction=json.loads((PILOT/metric['extraction_path']).read_text(encoding='utf-8'))
        lines=extraction['pages'][r['source_page']-1]['text'].splitlines()
        spans=[]
        for start,end,kind in ranges:
            text='\n'.join(line.strip() for line in lines[start-1:end] if line.strip())
            spans.append(dict(id=f'{key}-p{r["source_page"]}-l{start}-{end}',parent_record_id=key,
                page=r['source_page'],line_start=start,line_end=end,kind=kind,text=text,
                text_sha256=hashlib.sha256(text.encode()).hexdigest()))
        annotations.append(dict(record_id=key,file_id=r['file_id'],source_sha256=r['source_sha256'],
            visible_fingerprint=r['visible_fingerprint'],spans=spans,following_quoted_candidate_id=child,
            review_status='editorial_partition_not_verified_messages'))
    output=dict(schema_version=1,parser_version=catalog['summary']['parser_version'],
        method='Codex editorial partitions of previously visually inspected PDF pages, bound to exact extraction ranges. Quoted spans are not new verified messages; participant/date extraction is not inferred from these spans.',
        annotations=annotations)
    (PILOT/'email-boundaries.json').write_text(json.dumps(output,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f'Prepared {len(annotations)} source-bound body partitions.')


if __name__=='__main__':main()
