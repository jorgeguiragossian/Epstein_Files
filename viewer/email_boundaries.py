"""Attach lossless, source-bound editorial partitions without changing grouping."""
import hashlib

KINDS={'uncertain_header_continuation','authored_text_candidate','signature','inline_quote',
       'forwarded_quote','inline_quote_header_only','forwarding_wrapper'}


def apply_boundaries(catalog,boundaries,prepared):
    if boundaries['parser_version']!=catalog['summary']['parser_version']:
        raise ValueError('Body partitions need re-review after a parser change.')
    records={r['id']:r for r in catalog['records']}
    sources={m['file_id']:(m,x) for m,item,x,pdf in prepared}
    seen=set();span_ids=set();quoted=0
    for annotation in boundaries['annotations']:
        key=annotation['record_id']
        if key in seen or key not in records:raise ValueError('Duplicate or missing partition parent.')
        seen.add(key);record=records[key]
        if not record.get('source_review'):raise ValueError('Body partitions require source review.')
        for field in ('file_id','source_sha256','visible_fingerprint'):
            if annotation[field]!=record[field]:raise ValueError('Stale body partition source.')
        metric,extraction=sources[record['file_id']]
        if metric['sha256']!=annotation['source_sha256']:raise ValueError('Partition PDF hash changed.')
        header_end=max((h['page'],h['line']) for h in record['header_evidence'])
        later=sorted((r for r in records.values() if r['file_id']==record['file_id']
            and (r['source_page'],r['source_line'])>(record['source_page'],record['source_line'])),
            key=lambda r:(r['source_page'],r['source_line']))
        next_start=(later[0]['source_page'],later[0]['source_line']) if later else None
        texts=[];last=header_end
        for span in annotation['spans']:
            position=(span['page'],span['line_start'])
            if (span['id'] in span_ids or span['parent_record_id']!=key or span['kind'] not in KINDS
                or position<=last or span['line_start']<1 or span['line_end']<span['line_start']
                or not 1<=span['page']<=len(extraction['pages'])
                or (next_start and (span['page'],span['line_end'])>=next_start)):
                raise ValueError('Invalid, overlapping, or duplicate body span.')
            lines=extraction['pages'][span['page']-1]['text'].splitlines()
            if span['line_end']>len(lines):raise ValueError('Body span exceeds source page.')
            text='\n'.join(line.strip() for line in lines[span['line_start']-1:span['line_end']] if line.strip())
            if text!=span['text'] or hashlib.sha256(text.encode()).hexdigest()!=span['text_sha256']:
                raise ValueError('Body span source text changed.')
            span_ids.add(span['id']);last=(span['page'],span['line_end']);texts.append(text)
            quoted+=span['kind'] in ('inline_quote','forwarded_quote','inline_quote_header_only')
        if not texts or '\n'.join(texts)!=record['body']:
            raise ValueError('Body partition must preserve the entire original detected body.')
        child_id=annotation.get('following_quoted_candidate_id')
        if child_id:
            child=records.get(child_id)
            if (not child or child['file_id']!=record['file_id'] or child['source_sha256']!=record['source_sha256']
                or (child['source_page'],child['source_line'])<=last
                or not later or child_id!=later[0]['id']):
                raise ValueError('Quoted child must follow its parent in the same source PDF.')
            # This is a containment/forwarding annotation, never an inferred reply relationship.
        record['body_partition']=dict(annotation)
        if child_id:
            record['body_partition']['following_quoted_source']={k:child[k] for k in ('id','file_id','source_page','source_line')}
    catalog['summary']['body_partitions']={'annotated_candidates':len(seen),'quoted_spans':quoted,
        'new_message_candidates':0,'grouping_changed':False,'contact_rankings_ready':False}
    return catalog
