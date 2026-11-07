"""Validated prepared briefs and document-date selection, without live AI calls."""
import hashlib
import json
from datetime import date


def brief_fingerprint(brief):
    content={k:v for k,v in brief.items() if k!='editorial_review'}
    return hashlib.sha256(json.dumps(content,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()


def validate_briefs(prepared,sources,reviews=None):
    result={}
    for brief in prepared['briefs']:
        key=brief['file_id']
        if 'editorial_review' in brief:raise ValueError('Editorial checks require separate pinned review records.')
        if key in result or key not in sources:raise ValueError('Duplicate or unknown brief source.')
        source=sources[key]
        if brief['source_sha256']!=source['sha256']:raise ValueError('Stale brief PDF hash.')
        if brief['status']!='ai_assisted_editorial_draft' or not brief['title'] or not brief['scope'] or not brief['points']:
            raise ValueError('Brief requires draft status, scope and cited points.')
        for point in brief['points']:
            if not point['statement'] or not point['limitation'] or not point['citations']:raise ValueError('Brief point needs evidence and limitations.')
            for citation in point['citations']:
                text=source['pages'].get(citation['page'])
                if text is None or hashlib.sha256(text.encode()).hexdigest()!=citation['page_text_sha256']:
                    raise ValueError('Stale brief page evidence.')
                if not citation['quote'].strip() or ' '.join(citation['quote'].split()) not in ' '.join(text.split()):
                    raise ValueError('Brief quotation is absent from source page.')
        result[key]=dict(brief)
    seen=set()
    for review in (reviews or {}).get('reviews',[]):
        key=review['file_id']
        if key in seen or key not in result:raise ValueError('Duplicate or unknown brief review.')
        seen.add(key);brief=result[key]
        if review['source_sha256']!=brief['source_sha256'] or review['brief_sha256']!=brief_fingerprint(brief):
            raise ValueError('Brief content changed; repeat the editorial source check.')
        if review['reviewer']!='Codex' or review['result'] not in ('supported_as_scoped','supported_after_citation_expansion'):
            raise ValueError('Unsupported editorial review status.')
        if set(review['checks'])!={'statement_support','attribution','page_scope','limitations'} or not all(v is True for v in review['checks'].values()):
            raise ValueError('Brief source check must record all four editorial checks.')
        date.fromisoformat(review['reviewed_on'])
        brief['editorial_review']=dict(review)
    return result


def timeframe_index(word_index,reviews,briefs):
    return dict(version='timeframe-brief-1',documents=[dict(id=r['id'],dataset=r['dataset'],date_status=r['date_status'],primary_date=r['primary_date'],people=sorted({key for p in r['pages'] for key in p['people']}),date_review=reviews.get(r['id']),brief=briefs.get(r['id'])) for r in word_index['documents']])


def select_timeframe(index,people,date_from='',date_to='',dataset='',person=''):
    for value in (date_from,date_to):
        if value:
            try:valid=date.fromisoformat(value).isoformat()==value
            except ValueError:valid=False
            if not valid:raise ValueError('Use a real date in YYYY-MM-DD format.')
    if date_from and date_to and date_from>date_to:raise ValueError('Start date must be on or before end date.')
    if dataset and (not str(dataset).isdigit() or not 1<=int(dataset)<=12):raise ValueError('Invalid dataset.')
    if person and person not in people:raise ValueError('Unknown person-name filter.')
    scope=[r for r in index['documents'] if not dataset or r['dataset']==int(dataset)]
    dated=[r for r in scope if r['date_status']=='dated' and r['primary_date']]
    within=[r for r in dated if (not date_from or r['primary_date']>=date_from) and (not date_to or r['primary_date']<=date_to)]
    selected=sorted([r for r in within if not person or person in r['people']],key=lambda r:(r['primary_date'],r['id']),reverse=True)
    return dict(version=index['version'],scope_documents=len(scope),eligible_dated_documents=len(dated),excluded_without_reviewed_date=len(scope)-len(dated),documents_in_date_range=len(within),selected_documents=len(selected),prepared_briefs=sum(bool(r['brief']) for r in selected),source_checked_briefs=sum(bool(r['brief'] and r['brief'].get('editorial_review')) for r in selected),date_evidence_only=sum(not r['brief'] for r in selected),results=selected)
