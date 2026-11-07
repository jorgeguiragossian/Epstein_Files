"""Candidate-level review coverage, never message or contact counts."""

BOUNDARY={'contains_unseparated_quote','forwarding_wrapper_only','continuation_unverified'}
DATE_FLAGS={'date_missing','date_unparsed','date_ambiguous_numeric'}
FIELDS=('documents','documents_with_candidates','documents_with_reviews','candidates','reviewed','unreviewed',
        'boundary','sender_unresolved','recipient_unresolved','date_unresolved','breakdowns','adjacent_checks',
        'eligible_dated_documents','prepared_briefs','source_checked_briefs','date_evidence_only','excluded_without_reviewed_date')


def review_coverage(catalog,documents,timeframes=None):
    dated_sources={r['id']:r for r in (timeframes or {}).get('documents',[])}
    by_document={d['id']:[] for d in documents}
    for record in catalog['records']:
        if record['file_id'] not in by_document:raise ValueError('Email candidate has no source document.')
        by_document[record['file_id']].append(record)
    rows=[]
    for document in sorted(documents,key=lambda d:(d['dataset'],d['id'])):
        records=by_document[document['id']];reviewed=sum(bool(r.get('source_review')) for r in records)
        timeframe=dated_sources.get(document['id'],{});dated=bool(timeframe.get('date_status')=='dated' and timeframe.get('primary_date'))
        brief=timeframe.get('brief')
        rows.append(dict(id=document['id'],dataset=document['dataset'],documents=1,
            primary_date=timeframe.get('primary_date') if dated else None,
            eligible_dated_documents=int(dated),prepared_briefs=int(dated and bool(brief)),
            source_checked_briefs=int(dated and bool(brief and brief.get('editorial_review'))),
            date_evidence_only=int(dated and not brief),excluded_without_reviewed_date=int(not dated),
            documents_with_candidates=int(bool(records)),documents_with_reviews=int(reviewed>0),
            candidates=len(records),reviewed=reviewed,unreviewed=len(records)-reviewed,
            boundary=sum(r.get('source_review',{}).get('boundary_status') in BOUNDARY for r in records),
            sender_unresolved=sum('sender_address_unresolved' in r['flags'] for r in records),
            recipient_unresolved=sum('recipient_address_unresolved' in r['flags'] for r in records),
            date_unresolved=sum(bool(DATE_FLAGS.intersection(r['flags'])) for r in records),
            breakdowns=sum(bool(r.get('body_partition')) for r in records),
            adjacent_checks=sum(bool(r.get('continuation_review')) for r in records)))
    def totals(items):return {field:sum(r[field] for r in items) for field in FIELDS}
    return dict(scope='100-document pilot only. Counts are source candidate occurrences, not unique messages or people. Categories overlap; reviewed does not mean verified. Missing-field counts describe parser output, not editorial source readings.',
        totals=totals(rows),datasets=[dict(dataset=dataset,**totals([r for r in rows if r['dataset']==dataset])) for dataset in sorted({r['dataset'] for r in rows})],documents=rows)
