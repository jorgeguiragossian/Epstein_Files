"""Local-only pilot explorer. Run: python viewer/server.py

Uses the existing ignored extraction/PDF cache; no network ingestion or AI calls.
The derived SQLite index is ignored by Git and rebuilt at startup.
"""
import argparse
import hashlib
import json
import re
import sqlite3
from contextlib import closing
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
try:
    from .email_parser import build_email_catalog,review_page
    from .email_coverage import review_coverage
    from .wordcloud import build_word_index,word_cloud
    from .timeframes import validate_briefs,timeframe_index,select_timeframe
except ImportError:
    from email_parser import build_email_catalog,review_page
    from email_coverage import review_coverage
    from wordcloud import build_word_index,word_cloud
    from timeframes import validate_briefs,timeframe_index,select_timeframe

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / 'data/pilot/2026-11-01'
STATIC = Path(__file__).resolve().parent / 'static'
DB = ROOT / 'data/viewer/pilot.sqlite'
ASSETS = {'/': ('index.html', 'text/html; charset=utf-8'),
           '/timeframes': ('timeframes.html', 'text/html; charset=utf-8'),
           '/timeframes.js': ('timeframes.js', 'text/javascript; charset=utf-8'),
           '/words': ('words.html', 'text/html; charset=utf-8'),
           '/words.js': ('words.js', 'text/javascript; charset=utf-8'),
           '/coverage': ('coverage.html', 'text/html; charset=utf-8'),
           '/coverage.js': ('coverage.js', 'text/javascript; charset=utf-8'),
           '/emails': ('emails.html', 'text/html; charset=utf-8'),
           '/emails.js': ('emails.js', 'text/javascript; charset=utf-8'),
           '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
           '/style.css': ('style.css', 'text/css; charset=utf-8')}


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def iso_day(value, label='Date'):
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',value):
        raise ValueError(f'{label} must use YYYY-MM-DD.')
    try: date.fromisoformat(value)
    except ValueError: raise ValueError(f'{label} must be a real calendar date.') from None
    return value


def validate_review(review, metric, extracted):
    if review['status'] not in ('dated','uncertain','undated'):
        raise ValueError('Unknown date review status.')
    if review['source_sha256'] != metric['sha256']:
        raise ValueError('Date review refers to different source bytes.')
    page = integer(review['evidence_page'],1,metric['page_count'],'Evidence page')
    if not review['evidence_quote'] or review['evidence_quote'] not in extracted['pages'][page-1]['text']:
        raise ValueError('Date evidence is absent from the cited page.')
    if review['status']=='dated':
        iso_day(review['primary_date'])
        if review['date_type'] not in ('email_sent','report','transcript_session','letter','presentation') or review['precision']!='day':
            raise ValueError('A dated record requires a supported date type and day precision.')
    elif review['primary_date'] is not None or review['date_type'] is not None:
        raise ValueError('Uncertain and undated reviews cannot assign a primary date.')


def name_pattern(form):
    return r'(?<!\w)' + r'\s+'.join(re.escape(word) for word in form.split()) + r'(?!\w)'


def name_occurrences(text, forms):
    spans={}
    for form in forms:
        for match in re.finditer(name_pattern(form),text,re.I):
            spans[(match.start(),match.end())]={'start':match.start(),'end':match.end(),'text':match.group(0)}
    return [spans[key] for key in sorted(spans)]


def validate_people(people, prepared):
    sources={metric['file_id']:(metric,extracted) for metric,item,extracted,pdf in prepared}
    seen_ids,seen_forms=set(),set()
    for person in people:
        if not re.fullmatch(r'[a-z][a-z-]{1,60}',person['id']) or person['id'] in seen_ids:
            raise ValueError('Duplicate or invalid person vocabulary ID.')
        seen_ids.add(person['id'])
        evidence=person['evidence']
        if evidence['file_id'] not in sources: raise ValueError('Unknown person-evidence document.')
        metric,extracted=sources[evidence['file_id']]
        if evidence['source_sha256']!=metric['sha256']: raise ValueError('Stale person-evidence source hash.')
        page=integer(evidence['pdf_page'],1,metric['page_count'],'Person evidence page')
        if not evidence['quote'] or evidence['quote'] not in extracted['pages'][page-1]['text']:
            raise ValueError('Name evidence is absent from cited page.')
        # This pilot vocabulary allows one literal full-name form per entry.
        if person['forms']!=[person['label']] or len(person['label'])>100 or not re.fullmatch(name_pattern(person['label']),evidence['quote'],re.I):
            raise ValueError('Name form requires matching source evidence.')
        normalized=' '.join(person['label'].casefold().split())
        if normalized in seen_forms: raise ValueError('Duplicate name form across vocabulary entries.')
        seen_forms.add(normalized)


def build_index(pilot=PILOT, database=DB):
    downloads = {r['url']: r for r in load(pilot / 'downloads.json')['files']}
    metrics = load(pilot / 'metrics.json')['files']
    selected = load(pilot / 'selection.json')['files']
    review_rows = load(pilot / 'date-reviews.json')['reviews']
    reviews = {r['file_id']:r for r in review_rows}
    if len(reviews)!=len(review_rows) or not set(reviews).issubset({m['file_id'] for m in metrics}):
        raise ValueError('Duplicate or unknown date review document.')
    if {r['url'] for r in metrics} != {r['url'] for r in selected} or any(r['status'] != 'extracted' for r in metrics):
        raise ValueError('Pilot extraction is incomplete. Finish the pilot before starting the viewer.')
    prepared = []
    for metric in metrics:
        if metric['status'] != 'extracted':
            continue
        item = downloads[metric['url']]
        extraction_file, pdf = pilot / metric['extraction_path'], pilot / item['local_path']
        if not extraction_file.is_file() or not pdf.is_file():
            raise ValueError('Pilot cache missing. Run the download and analyze commands in docs/viewer.md first.')
        extracted = load(extraction_file)
        sha = hashlib.sha256(pdf.read_bytes()).hexdigest()
        if sha != item['sha256'] or extracted.get('source_sha256') != sha:
            raise ValueError(f"Cache checksum mismatch for {metric['file_id']}; regenerate the pilot extraction.")
        if len(extracted['pages']) != metric['page_count']:
            raise ValueError('Page coverage mismatch')
        if metric['file_id'] in reviews: validate_review(reviews[metric['file_id']],metric,extracted)
        prepared.append((metric, item, extracted, pdf))
    if not prepared:
        raise ValueError('No extracted pilot documents available.')
    people=load(pilot/'people.json')['people']
    validate_people(people,prepared)
    database.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(database)) as connection:
        connection.executescript('''
            DROP TABLE IF EXISTS search;
            DROP TABLE IF EXISTS pages;
            DROP TABLE IF EXISTS documents;
            DROP TABLE IF EXISTS document_dates;
            DROP TABLE IF EXISTS people;
            DROP TABLE IF EXISTS name_mentions;
            DROP TABLE IF EXISTS email_catalog;
            CREATE TABLE documents (id TEXT PRIMARY KEY, dataset INTEGER, page_count INTEGER,
                low_text_pages INTEGER, bytes INTEGER, date_count INTEGER, email_headers INTEGER,
                url TEXT, sha256 TEXT, pdf_path TEXT);
            CREATE TABLE pages (id INTEGER PRIMARY KEY, document_id TEXT, number INTEGER,
                text TEXT, low_text INTEGER, date_candidates TEXT, UNIQUE(document_id, number));
            CREATE VIRTUAL TABLE search USING fts5(text, tokenize='unicode61');
            CREATE TABLE document_dates(document_id TEXT PRIMARY KEY,status TEXT,primary_date TEXT,date_type TEXT,review_json TEXT);
            CREATE TABLE people(id TEXT PRIMARY KEY,label TEXT,forms_json TEXT,evidence_json TEXT);
            CREATE TABLE name_mentions(page_id INTEGER,person_id TEXT,occurrences INTEGER,hits_json TEXT,PRIMARY KEY(page_id,person_id));
            CREATE INDEX mentions_person ON name_mentions(person_id,page_id);
            CREATE TABLE email_catalog(payload TEXT);
        ''')
        for person in people:
            connection.execute('INSERT INTO people VALUES (?,?,?,?)',(person['id'],person['label'],json.dumps(person['forms']),json.dumps(person['evidence'])))
        for metric, item, extracted, pdf in prepared:
            connection.execute('INSERT INTO documents VALUES (?,?,?,?,?,?,?,?,?,?)',
                (metric['file_id'], metric['dataset'], metric['page_count'], metric['low_text_pages'],
                 item['bytes'], metric['date_candidate_count'], metric['email_header_candidate_count'],
                 metric['url'], item['sha256'], str(pdf.resolve())))
            review = reviews.get(metric['file_id'])
            if review:
                connection.execute('INSERT INTO document_dates VALUES (?,?,?,?,?)',
                    (metric['file_id'],review['status'],review['primary_date'],review['date_type'],json.dumps(review)))
            for page in extracted['pages']:
                cursor = connection.execute('INSERT INTO pages(document_id,number,text,low_text,date_candidates) VALUES (?,?,?,?,?)',
                    (metric['file_id'], page['page'], page['text'], int(page['low_text_candidate']), json.dumps(page['date_candidates'])))
                connection.execute('INSERT INTO search(rowid,text) VALUES (?,?)', (cursor.lastrowid, page['text']))
                for person in people:
                    hits=name_occurrences(page['text'],person['forms'])
                    if hits:
                        connection.execute('INSERT INTO name_mentions VALUES (?,?,?,?)',(cursor.lastrowid,person['id'],len(hits),json.dumps(hits)))
        connection.execute('INSERT INTO email_catalog VALUES (?)',(json.dumps(build_email_catalog(prepared,load(pilot/'email-validation.json'),load(pilot/'email-boundaries.json'))),))
        connection.commit()
    return len(prepared)


def integer(value, minimum, maximum, label):
    try:
        parsed = int(value)
    except (ValueError, TypeError):
        raise ValueError(f'{label} must be a whole number.') from None
    if not minimum <= parsed <= maximum:
        raise ValueError(f'{label} must be between {minimum} and {maximum}.')
    return parsed


def snippet(text, words):
    matches = [re.search(name_pattern(word), text, re.I) for word in words]
    positions = [match.start() for match in matches if match]
    start = max(0, min(positions) - 75) if positions else 0
    compact = re.sub(r'\s+', ' ', text[start:start + 300]).strip()
    return ('…' if start else '') + compact + ('…' if start + 300 < len(text) else '')


class Catalog:
    def __init__(self, database=DB):
        self.database = database

    def connect(self):
        connection = sqlite3.connect(f'file:{self.database.as_posix()}?mode=ro', uri=True)
        connection.row_factory = sqlite3.Row
        return closing(connection)

    def overview(self):
        with self.connect() as c:
            return {'documents': c.execute('SELECT COUNT(*) FROM documents').fetchone()[0],
                'pages': c.execute('SELECT COUNT(*) FROM pages').fetchone()[0],
                'low_text_pages': c.execute('SELECT COUNT(*) FROM pages WHERE low_text=1').fetchone()[0],
                'date_status_counts': {r['status']:r['count'] for r in c.execute("SELECT COALESCE(v.status,'unreviewed') AS status,COUNT(*) AS count FROM documents d LEFT JOIN document_dates v ON v.document_id=d.id GROUP BY COALESCE(v.status,'unreviewed')")},
                'datasets': [dict(r) for r in c.execute('SELECT dataset,COUNT(*) AS documents,SUM(page_count) AS pages FROM documents GROUP BY dataset ORDER BY dataset')]}

    def people(self):
        with self.connect() as c:
            rows=c.execute('''SELECT n.id,n.label,n.forms_json,n.evidence_json,COUNT(DISTINCT p.document_id) AS documents,
                COUNT(m.page_id) AS pages,COALESCE(SUM(m.occurrences),0) AS occurrences FROM people n
                LEFT JOIN name_mentions m ON m.person_id=n.id LEFT JOIN pages p ON p.id=m.page_id
                GROUP BY n.id ORDER BY n.label COLLATE NOCASE''')
            return {'scope':'Curated full-name text matches in this pilot; not verified identities or relationship counts.',
                'people':[{'id':r['id'],'label':r['label'],'forms':json.loads(r['forms_json']),
                    'evidence':json.loads(r['evidence_json']),'documents':r['documents'],'pages':r['pages'],'occurrences':r['occurrences']} for r in rows]}

    def emails(self,filter_name='all',document='',page=1):
        with self.connect() as c:
            catalog=json.loads(c.execute('SELECT payload FROM email_catalog').fetchone()['payload'])
        return review_page(catalog,filter_name,document,page)

    def coverage(self):
        with self.connect() as c:
            catalog=json.loads(c.execute('SELECT payload FROM email_catalog').fetchone()['payload'])
            documents=[dict(r) for r in c.execute('SELECT id,dataset FROM documents')]
        return review_coverage(catalog,documents,self.timeframe_index())

    def word_index(self):
        with self.connect() as c:
            docs={r['id']:dict(id=r['id'],dataset=r['dataset'],date_review={'status':r['status'],'primary_date':r['primary_date']},pages=[]) for r in c.execute("SELECT d.id,d.dataset,COALESCE(v.status,'unreviewed') status,v.primary_date FROM documents d LEFT JOIN document_dates v ON v.document_id=d.id ORDER BY d.dataset,d.id")}
            names={}
            for r in c.execute('SELECT page_id,person_id FROM name_mentions'):names.setdefault(r['page_id'],[]).append({'id':r['person_id']})
            for r in c.execute("SELECT p.id,p.document_id,p.number,p.text FROM pages p JOIN document_dates v ON v.document_id=p.document_id WHERE v.status='dated' ORDER BY p.document_id,p.number"):
                docs[r['document_id']]['pages'].append(dict(number=r['number'],text=r['text'],name_mentions=names.get(r['id'],[])))
        return build_word_index(docs.values())

    def words(self,**query):
        return word_cloud(self.word_index(),[r['id'] for r in self.people()['people']],**query)

    def timeframe_index(self):
        with self.connect() as c:
            sources={r['id']:dict(sha256=r['sha256'],pages={}) for r in c.execute('SELECT id,sha256 FROM documents')}
            for r in c.execute('SELECT document_id,number,text FROM pages'):sources[r['document_id']]['pages'][r['number']]=r['text']
            reviews={r['document_id']:json.loads(r['review_json']) for r in c.execute('SELECT document_id,review_json FROM document_dates')}
        briefs=validate_briefs(load(PILOT/'timeframe-briefs.json'),sources,load(PILOT/'timeframe-brief-reviews.json'))
        return timeframe_index(self.word_index(),reviews,briefs)

    def timeframes(self,**query):
        return select_timeframe(self.timeframe_index(),[r['id'] for r in self.people()['people']],**query)

    def search(self, q='', dataset='', quality='all', page=1, date_from='', date_to='', date_status='all',person=''):
        q = q.strip()
        if len(q) > 200:
            raise ValueError('Keep search text to 200 characters or fewer.')
        page = integer(page, 1, 10000, 'Result page')
        where, params = [], []
        person_forms=[]
        if person:
            with self.connect() as c:
                entry=c.execute('SELECT forms_json FROM people WHERE id=?',(person,)).fetchone()
            if not entry: raise ValueError('Unknown person-name filter.')
            person_forms=json.loads(entry['forms_json'])
            where.append('p.id IN (SELECT page_id FROM name_mentions WHERE person_id=?)')
            params.append(person)
        if date_status not in ('all','dated','uncertain','undated','unreviewed'):
            raise ValueError('Unknown date status.')
        if date_from: iso_day(date_from,'Start date')
        if date_to: iso_day(date_to,'End date')
        if date_from and date_to and date_from>date_to:
            raise ValueError('Start date must be on or before end date.')
        if (date_from or date_to) and date_status not in ('all','dated'):
            raise ValueError('Date ranges apply only to reviewed dated documents. Clear the range to browse other statuses.')
        if date_status!='all':
            where.append("COALESCE(v.status,'unreviewed')=?")
            params.append(date_status)
        if date_from or date_to: where.append("v.status='dated'")
        if date_from:
            where.append('v.primary_date>=?');params.append(date_from)
        if date_to:
            where.append('v.primary_date<=?');params.append(date_to)
        words = re.findall(r'\w+', q, flags=re.UNICODE)
        if q:
            if not words:
                raise ValueError('Enter at least one word or document ID.')
            if re.fullmatch(r'EFTA\d{8}', q, flags=re.I):
                where.append('d.id=?')
                params.append(q.upper())
                words = []
            else:
                where.append('p.id IN (SELECT rowid FROM search WHERE search MATCH ?)')
                params.append(' AND '.join('"' + word + '"' for word in words))
        if dataset:
            where.append('d.dataset=?')
            params.append(integer(dataset, 1, 12, 'Dataset'))
        if quality not in ('all', 'review', 'substantial'):
            raise ValueError('Unknown quality filter.')
        if quality == 'review': where.append('d.low_text_pages>0')
        if quality == 'substantial': where.append('d.low_text_pages<d.page_count')
        sql = '''SELECT d.id,d.dataset,d.page_count,d.low_text_pages,d.bytes,d.date_count,d.email_headers,
            COALESCE(v.status,'unreviewed') AS date_status,v.primary_date,v.date_type,
            p.number,p.text,p.low_text FROM pages p JOIN documents d ON d.id=p.document_id
            LEFT JOIN document_dates v ON v.document_id=d.id'''
        if where: sql += ' WHERE ' + ' AND '.join(where)
        sql += ' ORDER BY d.dataset,d.id,p.number'
        groups = {}
        hit_pages = 0
        with self.connect() as c:
            for row in c.execute(sql, params):
                hit_pages += 1
                if row['id'] not in groups:
                    groups[row['id']] = {k:row[k] for k in ('id','dataset','page_count','low_text_pages','bytes','date_count','email_headers','date_status','primary_date','date_type')}
                    groups[row['id']].update(first_page=row['number'], snippet=snippet(row['text'], person_forms+words), matching_pages=[])
                groups[row['id']]['matching_pages'].append(row['number'])
        documents = list(groups.values())
        page_size = 15
        return {'query':q, 'total_documents':len(documents), 'total_matching_pages':hit_pages,
            'page':page, 'page_size':page_size, 'results':documents[(page-1)*page_size:page*page_size]}

    def document(self, document_id, page=1):
        with self.connect() as c:
            row = c.execute('SELECT * FROM documents WHERE id=?', (document_id,)).fetchone()
            if not row: raise LookupError('Document not found.')
            page = integer(page, 1, row['page_count'], 'PDF page')
            document = {k:row[k] for k in row.keys() if k != 'pdf_path'}
            text = c.execute('SELECT number,text,low_text,date_candidates FROM pages WHERE document_id=? AND number=?', (document_id,page)).fetchone()
            document['page'] = dict(text)
            document['page']['date_candidates'] = json.loads(text['date_candidates'])
            document['page']['name_mentions']=[{'id':r['person_id'],'label':r['label'],'occurrences':r['occurrences'],'hits':json.loads(r['hits_json'])} for r in c.execute('''SELECT m.person_id,n.label,m.occurrences,m.hits_json FROM name_mentions m JOIN people n ON n.id=m.person_id JOIN pages p ON p.id=m.page_id WHERE p.document_id=? AND p.number=? ORDER BY n.label''',(document_id,page))]
            review = c.execute('SELECT review_json FROM document_dates WHERE document_id=?',(document_id,)).fetchone()
            document['date_review'] = json.loads(review['review_json']) if review else {'status':'unreviewed','primary_date':None,'date_type':None,'notes':'This document has not yet had a primary-date review.'}
            return document

    def pdf(self, document_id):
        with self.connect() as c:
            row = c.execute('SELECT pdf_path FROM documents WHERE id=?', (document_id,)).fetchone()
            if not row: raise LookupError('Document not found.')
            return Path(row['pdf_path'])


def byte_range(header, size):
    if not header: return 0, size - 1, False
    match = re.fullmatch(r'bytes=(\d*)-(\d*)', header)
    if not match or not any(match.groups()): raise ValueError('Unsupported byte range.')
    left, right = match.groups()
    if not left:
        suffix = int(right)
        if suffix <= 0: raise ValueError('Invalid byte range.')
        return max(0,size-suffix), size-1, True
    start, end = int(left), min(int(right),size-1) if right else size-1
    if start >= size or end < start: raise ValueError('Invalid byte range.')
    return start, end, True


class Handler(BaseHTTPRequestHandler):
    catalog = Catalog()

    def send_headers(self, code, mime, length=None, extra=None):
        self.send_response(code)
        self.send_header('Content-Type', mime)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; object-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'")
        if length is not None: self.send_header('Content-Length',str(length))
        for key,value in (extra or {}).items(): self.send_header(key,str(value))
        self.end_headers()

    def json(self, code, value):
        data = json.dumps(value,ensure_ascii=False).encode('utf-8')
        self.send_headers(code,'application/json; charset=utf-8',len(data))
        self.wfile.write(data)

    def do_GET(self):
        if self.headers.get('Host','').split(':')[0] not in ('127.0.0.1','localhost'):
            self.json(403,{'error':'This viewer accepts local requests only.'})
            return
        url = urlsplit(self.path)
        query = {k:v[0] for k,v in parse_qs(url.query).items()}
        try:
            if url.path in ASSETS:
                filename,mime = ASSETS[url.path]
                data = (STATIC / filename).read_bytes()
                self.send_headers(200,mime,len(data))
                self.wfile.write(data)
            elif url.path == '/api/overview': self.json(200,self.catalog.overview())
            elif url.path == '/api/people': self.json(200,self.catalog.people())
            elif url.path == '/api/emails':self.json(200,self.catalog.emails(query.get('filter','all'),query.get('document',''),query.get('page',1)))
            elif url.path == '/api/coverage':self.json(200,self.catalog.coverage())
            elif url.path == '/api/words':self.json(200,self.catalog.words(**{k:query.get(k,'') for k in ('date_from','date_to','dataset','person','exclude')}))
            elif url.path == '/api/timeframes':self.json(200,self.catalog.timeframes(**{k:query.get(k,'') for k in ('date_from','date_to','dataset','person')}))
            elif url.path == '/api/search':
                self.json(200,self.catalog.search(query.get('q',''),query.get('dataset',''),query.get('quality','all'),query.get('page',1),query.get('date_from',''),query.get('date_to',''),query.get('date_status','all'),query.get('person','')))
            elif re.fullmatch(r'/api/documents/EFTA\d{8}', url.path):
                self.json(200,self.catalog.document(url.path.rsplit('/',1)[-1],query.get('page',1)))
            elif re.fullmatch(r'/pdf/EFTA\d{8}', url.path):
                path = self.catalog.pdf(url.path.rsplit('/',1)[-1])
                size = path.stat().st_size
                try: start,end,partial = byte_range(self.headers.get('Range'),size)
                except ValueError:
                    self.send_headers(416,'application/pdf',0,{'Content-Range':f'bytes */{size}'})
                    return
                extra = {'Accept-Ranges':'bytes','Content-Disposition':f'inline; filename="{path.name}"'}
                if partial: extra['Content-Range'] = f'bytes {start}-{end}/{size}'
                self.send_headers(206 if partial else 200,'application/pdf',end-start+1,extra)
                with path.open('rb') as stream:
                    stream.seek(start)
                    remaining = end-start+1
                    while remaining:
                        data = stream.read(min(65536,remaining))
                        if not data: break
                        self.wfile.write(data)
                        remaining -= len(data)
            else: self.json(404,{'error':'Not found.'})
        except ValueError as exc: self.json(400,{'error':str(exc)})
        except LookupError as exc: self.json(404,{'error':str(exc)})
        except (BrokenPipeError,ConnectionResetError): pass
        except Exception:
            self.json(500,{'error':'The local cache could not be read. See the server terminal.'})
            raise

    def log_message(self, format, *args):
        # Search strings can contain names; omit request URLs from routine logs.
        if len(args)>1: print(f'HTTP {args[1]}',flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8765)
    args = parser.parse_args()
    try: count = build_index()
    except (ValueError,FileNotFoundError) as exc: raise SystemExit(str(exc)) from None
    server = ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    print(f'Indexed {count} pilot documents. Local: http://127.0.0.1:{args.port}',flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()


if __name__ == '__main__': main()
