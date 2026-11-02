"""Source-bound review overlays. Never overwrite parsed fields or merge messages."""
import re


def apply_validation(catalog,validation,prepared):
    if validation['parser_version']!=catalog['summary']['parser_version']:
        raise ValueError('Email reviews require re-review after a parser version change.')
    records={r['id']:r for r in catalog['records']}
    sources={m['file_id']:(m,x) for m,item,x,pdf in prepared}
    seen=set()
    for review in validation['reviews']:
        key=review['record_id']
        if key in seen or key not in records:raise ValueError('Duplicate or missing reviewed email candidate.')
        seen.add(key);record=records[key]
        for field in ('file_id','source_sha256','source_page','source_line','visible_fingerprint'):
            if review[field]!=record[field]:raise ValueError('Stale email review source reference.')
        metric,extraction=sources[review['file_id']]
        if review['source_sha256']!=metric['sha256']:raise ValueError('Email review source hash changed.')
        try:anchor=extraction['pages'][review['source_page']-1]['text'].splitlines()[review['source_line']-1].strip()
        except IndexError:raise ValueError('Email review source anchor is out of range.') from None
        if anchor!=review['extracted_anchor']:raise ValueError('Email review source text changed.')
        if review['boundary_status'] not in ('supported_segment','contains_unseparated_quote','forwarding_wrapper_only','continuation_unverified'):
            raise ValueError('Unknown reviewed boundary status.')
        if review['unique_message_verified'] or review['contact_count_eligible']:
            raise ValueError('Pilot source review cannot silently enable contact rankings.')
        record['source_review']=dict(review)
    association_ids=set()
    for association in validation['address_associations']:
        key=association['record_id']
        if association['id'] in association_ids or key not in seen:raise ValueError('Address association needs a unique ID and reviewed candidate.')
        association_ids.add(association['id']);record=records[key]
        for field in ('file_id','source_sha256','source_page'):
            if association[field]!=record[field]:raise ValueError('Stale header association source.')
        if association['field'] not in ('from','to','cc','bcc') or not re.fullmatch(r'[^\s@<>]+@[^\s@<>]+\.[A-Za-z]{2,}',association['address']):
            raise ValueError('Invalid header association field or address.')
        if association['raw_extracted_field']!=record['headers'].get(association['field'],''):
            raise ValueError('Raw associated header changed; repeat visual review.')
        if association['ownership_verified'] or association['apply_globally']:
            raise ValueError('Observed header pairs cannot be promoted to verified ownership or global aliases.')
        record.setdefault('reviewed_address_associations',[]).append(dict(association))
    catalog['summary']['source_review']={'reviewed_candidates':len(seen),
        'supported_segments':sum(r['boundary_status']=='supported_segment' for r in validation['reviews']),
        'boundary_attention':sum(r['boundary_status']!='supported_segment' for r in validation['reviews']),
        'observed_address_associations':len(association_ids),'verified_unique_messages':None,'contact_rankings_ready':False}
    return catalog
