"""Deterministic English word frequencies with page-level source references."""
import re
import unicodedata
from collections import Counter
from datetime import date

STOP=set('''the and for that this with from are was were have has had not but you your our their they them she his her him who what when where which will would could should can may shall into about after before also any all each more most some such than then there these those been being its itself here how out over under very well does did doing said say says just only other same through upon within without please thank thanks dear regards sincerely subject sent date mailto http https www com org net pdf page pages mon tue wed thu fri sat sun monday tuesday wednesday thursday friday saturday sunday january february march april june july august september october november december jan feb mar apr jun jul aug sep oct nov dec am pm est edt utc gmt efta sdny gm'''.split())
STAMP=re.compile(r'^\s*(?:EFTA\S*|(?:SDNY|GM)[_\s]\S*|\d+)\s*$',re.I)
STOP.update('yes no during now one like ever get got much many really don doesn didn isn wasn weren wouldn couldn shouldn'.split())
VENDOR=re.compile(r'^\s*(?:free state reporting,? inc\.?|court reporting(?: and| &)? transcription|d\.?c\.? area\s+[\d() -]+|balt\..*annap\..*\d[\d() -]*)\s*$',re.I)


def frequencies(text):
    text='\n'.join(line for line in text.splitlines() if not STAMP.fullmatch(line) and not VENDOR.fullmatch(line))
    text=re.sub(r'https?://\S+|www\.\S+|\S+@\S+',' ',text,flags=re.I)
    text=''.join(c for c in unicodedata.normalize('NFD',text.lower()) if unicodedata.category(c)!='Mn')
    # Digit-bearing IDs and artifacts must not become partial words.
    words=re.findall(r'\b[a-z]{3,}\b',text)
    return dict(sorted(Counter(w for w in words if w not in STOP).items()))


def reviewed_periods(doc):
    result=[]
    for observation in doc.get('source_quality_review',{}).get('date_observations',[]):
        if observation['role'] not in ('statement_reporting_period','transaction_reporting_period'):
            continue
        start=observation.get('period_start');end=observation.get('period_end')
        if not start or not end:continue
        if date.fromisoformat(start).isoformat()!=start or date.fromisoformat(end).isoformat()!=end or start>end:
            raise ValueError('Invalid reviewed reporting period.')
        result.append(dict(start=start,end=end,pdf_page=observation.get('pdf_page')))
    return result


def build_word_index(documents):
    rows=[]
    for doc in documents:
        review=doc['date_review'];dated=review['status']=='dated' and bool(review.get('primary_date'))
        periods=reviewed_periods(doc)
        row=dict(id=doc['id'],dataset=doc['dataset'],date_status=review['status'],primary_date=review.get('primary_date'),
            pages=[dict(number=p['number'],people=sorted(m['id'] for m in p['name_mentions']),terms=frequencies(p['text'])) for p in doc['pages']] if dated or periods else [])
        if periods:row['reporting_periods']=periods
        rows.append(row)
    return dict(version='word-frequency-2',stop_words=sorted(STOP),documents=rows)


def word_cloud(index,people,date_from='',date_to='',dataset='',person='',exclude='',date_basis='primary'):
    date_basis=date_basis or 'primary'
    if date_basis not in ('primary','reporting_period'):raise ValueError('Unknown word-cloud date basis.')
    for value in (date_from,date_to):
        if value:
            try:valid=date.fromisoformat(value).isoformat()==value
            except ValueError:valid=False
            if not valid:raise ValueError('Use a real date in YYYY-MM-DD format.')
    if date_from and date_to and date_from>date_to:raise ValueError('Start date must be on or before end date.')
    if dataset and (not str(dataset).isdigit() or not 1<=int(dataset)<=12):raise ValueError('Invalid dataset.')
    if person and person not in people:raise ValueError('Unknown person-name filter.')
    if len(exclude)>300:raise ValueError('Keep extra exclusions to 300 characters or fewer.')
    normalized=''.join(c for c in unicodedata.normalize('NFD',exclude.lower()) if unicodedata.category(c)!='Mn')
    excluded=set(re.findall(r'[a-z]+',normalized));totals=Counter();sources={};documents=0;pages=0
    scope=[r for r in index['documents'] if not dataset or r['dataset']==int(dataset)]
    dated=[r for r in scope if r['date_status']=='dated' and r['primary_date']]
    periods=[r for r in scope if r.get('reporting_periods')]
    if date_basis=='reporting_period':
        within=[r for r in periods if any((not date_from or p['end']>=date_from) and (not date_to or p['start']<=date_to) for p in r['reporting_periods'])]
    else:
        within=[r for r in dated if (not date_from or r['primary_date']>=date_from) and (not date_to or r['primary_date']<=date_to)]
    for doc in within:
        selected=[p for p in doc['pages'] if not person or person in p['people']]
        if not selected:continue
        documents+=1;pages+=len(selected)
        for page in selected:
            for term,count in page['terms'].items():
                if term in excluded:continue
                totals[term]+=count;sources.setdefault(term,[]).append(dict(file_id=doc['id'],page=page['number'],count=count))
    terms=[dict(term=term,count=count,documents=len({r['file_id'] for r in sources[term]}),sources=sorted(sources[term],key=lambda r:(r['file_id'],r['page']))) for term,count in sorted(totals.items(),key=lambda item:(-item[1],item[0]))[:50]]
    result=dict(version=index['version'],stop_words=index['stop_words'],scope_documents=len(scope),eligible_dated_documents=len(dated),excluded_without_reviewed_date=len(scope)-len(dated),documents_in_date_range=len(within),selected_documents=documents,selected_pages=pages,total_tokens=sum(totals.values()),distinct_terms=len(totals),terms=terms)
    if date_basis=='reporting_period':
        result.update(date_basis=date_basis,eligible_reporting_period_documents=len(periods),excluded_without_reviewed_period=len(scope)-len(periods),documents_in_period_range=len(within))
    return result
