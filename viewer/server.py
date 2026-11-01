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
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / 'data/pilot/2026-11-01'
STATIC = Path(__file__).resolve().parent / 'static'
DB = ROOT / 'data/viewer/pilot.sqlite'
ASSETS = {'/': ('index.html', 'text/html; charset=utf-8'),
           '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
           '/style.css': ('style.css', 'text/css; charset=utf-8')}


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def build_index(pilot=PILOT, database=DB):
    downloads = {r['url']: r for r in load(pilot / 'downloads.json')['files']}
    metrics = load(pilot / 'metrics.json')['files']
    selected = load(pilot / 'selection.json')['files']
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
        prepared.append((metric, item, extracted, pdf))
    if not prepared:
        raise ValueError('No extracted pilot documents available.')
    database.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(database)) as connection:
        connection.executescript('''
            DROP TABLE IF EXISTS search;
            DROP TABLE IF EXISTS pages;
            DROP TABLE IF EXISTS documents;
            CREATE TABLE documents (id TEXT PRIMARY KEY, dataset INTEGER, page_count INTEGER,
                low_text_pages INTEGER, bytes INTEGER, date_count INTEGER, email_headers INTEGER,
                url TEXT, sha256 TEXT, pdf_path TEXT);
            CREATE TABLE pages (id INTEGER PRIMARY KEY, document_id TEXT, number INTEGER,
                text TEXT, low_text INTEGER, date_candidates TEXT, UNIQUE(document_id, number));
            CREATE VIRTUAL TABLE search USING fts5(text, tokenize='unicode61');
        ''')
        for metric, item, extracted, pdf in prepared:
            connection.execute('INSERT INTO documents VALUES (?,?,?,?,?,?,?,?,?,?)',
                (metric['file_id'], metric['dataset'], metric['page_count'], metric['low_text_pages'],
                 item['bytes'], metric['date_candidate_count'], metric['email_header_candidate_count'],
                 metric['url'], item['sha256'], str(pdf.resolve())))
            for page in extracted['pages']:
                cursor = connection.execute('INSERT INTO pages(document_id,number,text,low_text,date_candidates) VALUES (?,?,?,?,?)',
                    (metric['file_id'], page['page'], page['text'], int(page['low_text_candidate']), json.dumps(page['date_candidates'])))
                connection.execute('INSERT INTO search(rowid,text) VALUES (?,?)', (cursor.lastrowid, page['text']))
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
    matches = [re.search(r'\b' + re.escape(word) + r'\b', text, re.I) for word in words]
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
                'datasets': [dict(r) for r in c.execute('SELECT dataset,COUNT(*) AS documents,SUM(page_count) AS pages FROM documents GROUP BY dataset ORDER BY dataset')]}

    def search(self, q='', dataset='', quality='all', page=1):
        q = q.strip()
        if len(q) > 200:
            raise ValueError('Keep search text to 200 characters or fewer.')
        page = integer(page, 1, 10000, 'Result page')
        where, params = [], []
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
            p.number,p.text,p.low_text FROM pages p JOIN documents d ON d.id=p.document_id'''
        if where: sql += ' WHERE ' + ' AND '.join(where)
        sql += ' ORDER BY d.dataset,d.id,p.number'
        groups = {}
        hit_pages = 0
        with self.connect() as c:
            for row in c.execute(sql, params):
                hit_pages += 1
                if row['id'] not in groups:
                    groups[row['id']] = {k:row[k] for k in ('id','dataset','page_count','low_text_pages','bytes','date_count','email_headers')}
                    groups[row['id']].update(first_page=row['number'], snippet=snippet(row['text'], words), matching_pages=[])
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
            elif url.path == '/api/search':
                self.json(200,self.catalog.search(query.get('q',''),query.get('dataset',''),query.get('quality','all'),query.get('page',1)))
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
