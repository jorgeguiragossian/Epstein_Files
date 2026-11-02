"""Conservative PDF email candidates and visible-copy groups, not unique messages.

No identity resolution, OCR repair, fuzzy deduplication, or contact rankings.
"""
import hashlib
import json
import re
from datetime import datetime
from email.utils import parsedate_to_datetime

VERSION='email-pilot-1'
DATE_VERSION='email-date-2'
ADDRESS=re.compile(r'(?<![\w.+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?![\w.-])')
FIELD=re.compile(r'^\s*(From|To|Cc|Bcc|Date|Sent|Subject|Message-ID)\s*:\s*(.*)$',re.I)
LOOSE=re.compile(r'^\s*(Sent|Subject)\b\s*:?[ \t]*(.*)$',re.I)
FOOTER=re.compile(r'^\s*(?:EFTA(?:_R\d+_\d+|\d+)|(?:SDNY|GM)[_A-Z0-9]+)\s*$',re.I)


def compact(text):
    return ' '.join(text.split())


def header(line):
    if re.match(r'^\s*Sent from my\b',line,re.I):return None
    match=FIELD.match(line) or LOOSE.match(line)
    return (match.group(1).lower(),match.group(2).strip()) if match else None


def parse_date(raw):
    """Parsed timestamp candidate only. Ambiguous numeric dates stay unresolved."""
    if not raw:return None,['date_missing']
    numeric=re.search(r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b',raw)
    if numeric and int(numeric[1])<=12 and int(numeric[2])<=12:
        return None,['date_ambiguous_numeric']
    cleaned=re.sub(r'^(?:Mon\w*|Tue\w*|Wed\w*|Thu\w*|Fri\w*|Sat\w*|Sun\w*)[,.]?\s*','',raw,flags=re.I)
    for fmt in ('%B %d, %Y %I:%M %p','%B %d %Y %I:%M %p','%B %d, %Y %I:%M:%S %p',
                '%b %d, %Y %I:%M %p','%b %d %Y %I:%M %p','%b %d, %Y %I:%M:%S %p',
                '%m/%d/%Y %I:%M %p','%m/%d/%Y %I:%M:%S %p'):
        try:return datetime.strptime(cleaned,fmt).isoformat(),['date_timezone_unspecified']
        except ValueError:pass
    # The RFC parser can accept a 12-hour string while silently discarding PM.
    # Only use it for strings without a meridiem marker; unsupported forms stay unresolved.
    if re.search(r'\b(?:AM|PM)\b',raw,re.I):return None,['date_unparsed']
    try:
        value=parsedate_to_datetime(raw)
        if value:return value.isoformat(),([] if value.tzinfo else ['date_timezone_unspecified'])
    except (ValueError,TypeError,OverflowError):pass
    return None,['date_unparsed']


def looks_date(text):
    return bool(re.search(r'(?:\d{1,2}/\d{1,2}/\d{4}|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d)',text,re.I))


def parse_document(extracted,file_id,dataset,source_sha256):
    lines=[]
    for page in extracted['pages']:
        for number,text in enumerate(page['text'].splitlines(),1):
            if text.strip() and not FOOTER.fullmatch(text):
                lines.append({'page':page['page'],'line':number,'text':text.strip()})
    blocks=[];i=0
    while i<len(lines):
        first=header(lines[i]['text'])
        if not first or first[0] not in ('from','to'):
            i+=1;continue
        fields={};evidence=[];j=i;last=None;fragments=[]
        while j<len(lines) and j-i<24:
            item=header(lines[j]['text'])
            if item:
                key,value=item
                if key in fields:break
                fields[key]=value;last=key
                evidence.append({'field':key,'value':value,'page':lines[j]['page'],'line':lines[j]['line']})
                j+=1;continue
            # Preserve wrapped date values, including Sent/Subject/date layouts.
            if looks_date(lines[j]['text']) and (('sent' in fields and not fields['sent']) or ('date' in fields and not fields['date'])):
                key='sent' if 'sent' in fields and not fields['sent'] else 'date'
                fields[key]=lines[j]['text']
                evidence.append({'field':key,'value':lines[j]['text'],'page':lines[j]['page'],'line':lines[j]['line']})
                j+=1;continue
            if fields.get('subject')=='' and ('date' in fields or 'sent' in fields) and re.match(r'^(?:Fwd?|Re):',lines[j]['text'],re.I):
                fields['subject']=lines[j]['text']
                evidence.append({'field':'subject','value':lines[j]['text'],'page':lines[j]['page'],'line':lines[j]['line']})
                j+=1;continue
            if len(lines[j]['text'])<=2 and j+1<len(lines) and header(lines[j+1]['text']) and len(fragments)<2:
                fragments.append(lines[j]);j+=1;continue
            upcoming=[header(x['text']) for x in lines[j+1:j+3]]
            first_upcoming=next((x for x in upcoming if x),None)
            wraps_subject=last=='subject' and not ({'date','sent'}&set(fields)) and first_upcoming and first_upcoming[0] in ('date','sent')
            wraps_address=last in ('from','to','cc','bcc') and (lines[j]['text'].startswith(('<','>')) or (first_upcoming and first_upcoming[0] in ('subject','date','sent')))
            if wraps_subject or wraps_address:
                fields[last]+=' '+lines[j]['text']
                evidence.append({'field':last,'value':lines[j]['text'],'page':lines[j]['page'],'line':lines[j]['line']})
                j+=1;continue
            break
        keys=set(fields)
        valid=({'from','to'}<=keys and bool(keys&{'subject','date','sent'})) or ('subject' in keys and bool(keys&{'date','sent'}) and bool(keys&{'from','to'}))
        if not valid:
            i+=1;continue
        blocks.append({'start':i,'end':j,'headers':fields,'header_evidence':evidence,'fragments':fragments})
        i=max(j,i+1)
    records=[]
    for ordinal,block in enumerate(blocks):
        end=blocks[ordinal+1]['start'] if ordinal+1<len(blocks) else len(lines)
        body_lines=lines[block['end']:end]
        # Forward/quote separators are boundaries, not body text used for grouping.
        while body_lines and re.match(r'^(?:[-_ ]*(?:Original Message|Forwarded message|Begin forwarded message)[: -]*|On .+wrote:)\s*$',body_lines[-1]['text'],re.I):
            body_lines=body_lines[:-1]
        body='\n'.join(row['text'] for row in body_lines)
        fields=block['headers'];flags=['candidate_not_verified_message','body_boundary_unverified']
        if block['fragments']:flags.append('header_fragments_unresolved')
        raw_date=fields.get('date') or fields.get('sent') or ''
        timestamp,date_flags=parse_date(raw_date);flags+=date_flags
        sender=ADDRESS.findall(fields.get('from',''))
        recipients=ADDRESS.findall(fields.get('to',''))
        if not sender:flags.append('sender_address_unresolved')
        if not recipients:flags.append('recipient_address_unresolved')
        if not compact(fields.get('subject','')):flags.append('subject_missing')
        if not body:flags.append('body_empty')
        if ordinal:flags.append('later_or_nested_header')
        source=lines[block['start']]
        record_id=hashlib.sha256(f'{VERSION}|{file_id}|{source_sha256}|{source["page"]}|{source["line"]}'.encode()).hexdigest()[:20]
        visible={'headers':{k:compact(v) for k,v in sorted(fields.items())},'body':compact(body),'fragments':[r['text'] for r in block['fragments']]}
        fingerprint=hashlib.sha256(json.dumps(visible,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        # Missing participants can make distinct messages look identical; retain all records.
        eligible=bool(len(sender)==1 and recipients and timestamp and fields.get('subject') and len(compact(body))>=40)
        records.append({'id':record_id,'file_id':file_id,'dataset':dataset,'source_sha256':source_sha256,
            'source_page':source['page'],'source_line':source['line'],'header_evidence':block['header_evidence'],'unresolved_header_fragments':block['fragments'],
            'headers':fields,'sender_addresses':sender,'recipient_addresses':recipients,'raw_date':raw_date,
            'parsed_timestamp_candidate':timestamp,'body':body,
            'body_pages':sorted({row['page'] for row in body_lines}),'flags':sorted(set(flags)),
            'visible_fingerprint':fingerprint,'strong_visible_key':eligible,'parser_version':VERSION,'date_parser_version':DATE_VERSION})
    return records


def group_records(records):
    groups={}
    for record in records:groups.setdefault(record['visible_fingerprint'],[]).append(record)
    result=[]
    for fingerprint,members in groups.items():
        if len(members)==1:kind='single_occurrence'
        elif all(r['strong_visible_key'] for r in members):kind='exact_visible_copies'
        else:kind='possible_repeat_incomplete'
        result.append({'id':fingerprint[:20],'kind':kind,'record_ids':[r['id'] for r in members],
            'occurrences':len(members),'distinct_documents':len({r['file_id'] for r in members}),
            'status':'unreviewed_visible_copy_group_not_a_unique_message'})
    by_id={r['id']:r for r in records}
    return sorted(result,key=lambda group:(-group['occurrences'],min((by_id[key]['file_id'],by_id[key]['source_page'],by_id[key]['source_line']) for key in group['record_ids']),group['id']))


def build_email_catalog(prepared,validation=None,boundaries=None):
    records=[]
    for metric,item,extracted,pdf in prepared:
        records+=parse_document(extracted,metric['file_id'],metric['dataset'],metric['sha256'])
    groups=group_records(records)
    flags={flag:sum(flag in r['flags'] for r in records) for flag in sorted({f for r in records for f in r['flags']})}
    summary={'parser_version':VERSION,'date_parser_version':DATE_VERSION,'documents_scanned':len(prepared),'candidate_occurrences':len(records),
        'documents_with_candidates':len({r['file_id'] for r in records}),'visible_groups':len(groups),
        'repeat_groups':sum(g['occurrences']>1 for g in groups),
        'exact_visible_copy_groups':sum(g['kind']=='exact_visible_copies' for g in groups),
        'possible_repeat_groups':sum(g['kind']=='possible_repeat_incomplete' for g in groups),
        'unique_messages':None,'contact_rankings_ready':False,'flag_counts':flags,
        'scope':'Unverified email-layout candidates and visible-copy groups. Every source occurrence is retained. No identity resolution or unique-message/contact claims.'}
    catalog={'summary':summary,'records':records,'groups':groups}
    if validation is not None:
        try:from .email_validation import apply_validation
        except ImportError:from email_validation import apply_validation
        apply_validation(catalog,validation,prepared)
    if boundaries is not None:
        try:from .email_boundaries import apply_boundaries
        except ImportError:from email_boundaries import apply_boundaries
        apply_boundaries(catalog,boundaries,prepared)
    return catalog


def review_page(catalog,filter_name='all',document='',page=1):
    if filter_name not in ('all','unresolved','repeats','reviewed','boundary'):raise ValueError('Unknown email review filter.')
    if document and not re.fullmatch(r'EFTA\d{8}',document):raise ValueError('Invalid email source document ID.')
    try:page=int(page)
    except (TypeError,ValueError):raise ValueError('Email result page must be a whole number.') from None
    if page<1 or page>10000:raise ValueError('Invalid email result page.')
    records={r['id']:r for r in catalog['records']}
    rows=[]
    unresolved={'sender_address_unresolved','recipient_address_unresolved','date_missing','date_unparsed','date_ambiguous_numeric'}
    for group in catalog['groups']:
        members=[records[key] for key in group['record_ids']]
        if document and not any(r['file_id']==document for r in members):continue
        if filter_name=='repeats' and group['occurrences']<2:continue
        if filter_name=='unresolved' and not any(unresolved.intersection(r['flags']) for r in members):continue
        if filter_name=='reviewed' and not any(r.get('source_review') for r in members):continue
        if filter_name=='boundary' and not any(r.get('source_review',{}).get('boundary_status') in ('contains_unseparated_quote','forwarding_wrapper_only','continuation_unverified') for r in members):continue
        representative=next((r for r in members if r['file_id']==document),members[0])
        rows.append(dict(group,representative=representative,sources=[{k:r[k] for k in ('id','file_id','source_page','source_line','flags')} for r in members]))
    return {'summary':catalog['summary'],'documents':sorted({r['file_id'] for r in catalog['records']}),
        'total_groups':len(rows),'page':page,'page_size':12,'results':rows[(page-1)*12:page*12]}
