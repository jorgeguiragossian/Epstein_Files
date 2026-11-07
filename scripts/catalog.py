"""Resumable, listing-only DOJ catalog. Never downloads document bodies.

Seed from the saved inventory, crawl a bounded batch, then export open manifests.
Each successful listing and failed attempt is retained; incomplete is never empty.
"""
import argparse
import csv
import hashlib
import json
import re
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://www.justice.gov'
MAX_HTML = 4 * 1024 * 1024


def now():
    return datetime.now(timezone.utc).isoformat()


def listing_url(dataset, page=0):
    if dataset not in range(1, 13) or page < 0:
        raise ValueError('Invalid dataset or page')
    return f'{BASE}/epstein/doj-disclosures/data-set-{dataset}-files' + (f'?page={page}' if page else '')


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.hrefs.extend(value for key, value in attrs if key == 'href' and value)


def parse_listing(html, dataset, page=0):
    parser = Links()
    parser.feed(html)
    files, pages = set(), {page}
    expected = urllib.parse.urlsplit(listing_url(dataset)).path
    for href in parser.hrefs:
        url = urllib.parse.urlsplit(urllib.parse.urljoin(listing_url(dataset, page), href))
        if url.scheme != 'https' or url.netloc != 'www.justice.gov':
            continue
        if url.path.startswith('/epstein/files/') and not url.query:
            files.add(urllib.parse.urlunsplit((url.scheme, url.netloc, url.path, '', '')))
        if url.path == expected:
            query = urllib.parse.parse_qs(url.query)
            value = query.get('page', ['0'])[0]
            if value.isdigit() and int(value) < 1000000:
                pages.add(int(value))
    if not files:
        raise ValueError('No DOJ file links: access response or changed markup; not an empty dataset')
    return sorted(files), max(pages) + 1


def connect(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.executescript('''
        CREATE TABLE IF NOT EXISTS observations(
          dataset INTEGER, page INTEGER, observed_at TEXT, source_url TEXT,
          html_sha256 TEXT, snapshot TEXT, advertised_pages INTEGER, file_count INTEGER,
          PRIMARY KEY(dataset,page,html_sha256,observed_at));
        CREATE TABLE IF NOT EXISTS files(
          dataset INTEGER, url TEXT, filename TEXT, file_id TEXT, first_seen TEXT, last_seen TEXT,
          PRIMARY KEY(dataset,url));
        CREATE TABLE IF NOT EXISTS appearances(
          dataset INTEGER, url TEXT, page INTEGER, html_sha256 TEXT, observed_at TEXT,
          PRIMARY KEY(dataset,url,page,html_sha256,observed_at));
        CREATE TABLE IF NOT EXISTS attempts(
          dataset INTEGER, page INTEGER, attempted_at TEXT, status TEXT, http_status INTEGER,
          final_url TEXT, error TEXT, UNIQUE(dataset,page,attempted_at));
    ''')
    return db


def record(db, dataset, page, html, timestamp, snapshot):
    files, pages = parse_listing(html.decode('utf-8-sig'), dataset, page)
    digest = hashlib.sha256(html).hexdigest()
    for other in db.execute('SELECT DISTINCT page FROM observations WHERE dataset=? AND page<>?', (dataset, page)):
        other_files = {r[0] for r in db.execute('SELECT DISTINCT url FROM appearances WHERE dataset=? AND page=?', (dataset, other[0]))}
        if set(files) == other_files:
            raise ValueError('Identical file set on different listing pages; pagination requires review')
    with db:
        db.execute('INSERT OR IGNORE INTO observations VALUES(?,?,?,?,?,?,?,?)',
                   (dataset, page, timestamp, listing_url(dataset, page), digest, snapshot, pages, len(files)))
        for url in files:
            filename = urllib.parse.unquote(urllib.parse.urlsplit(url).path.rsplit('/', 1)[-1])
            db.execute('''INSERT INTO files VALUES(?,?,?,?,?,?) ON CONFLICT(dataset,url)
                          DO UPDATE SET first_seen=min(first_seen,excluded.first_seen),
                          last_seen=max(last_seen,excluded.last_seen)''',
                       (dataset, url, filename, Path(filename).stem, timestamp, timestamp))
            db.execute('INSERT OR IGNORE INTO appearances VALUES(?,?,?,?,?)',
                       (dataset, url, page, digest, timestamp))


def seed(db, folder):
    inventory = json.loads((folder / 'inventory.json').read_text(encoding='utf-8-sig'))
    for observation in inventory['observations']:
        match = re.fullmatch(r'https://www.justice.gov/epstein/doj-disclosures/data-set-(\d+)-files(?:\?page=(\d+))?', observation['url'])
        if not match:
            raise ValueError('Unexpected seed listing URL')
        dataset, page = int(match[1]), int(match[2] or 0)
        path = (folder / observation['snapshot']).resolve()
        if path.parent != folder.resolve():
            raise ValueError('Snapshot outside seed folder')
        html = path.read_bytes()
        if hashlib.sha256(html).hexdigest() != observation['html_sha256']:
            raise ValueError('Seed HTML hash mismatch')
        record(db, dataset, page, html, observation['retrieved_at_utc'], str(path.relative_to(ROOT)).replace('\\', '/'))
    for failure in inventory.get('failures', []):
        match = re.fullmatch(r'https://www.justice.gov/epstein/doj-disclosures/data-set-(\d+)-files\?page=(\d+)', failure['url'])
        if match:
            code = 403 if '403' in failure['error'] else None
            with db:
                db.execute('INSERT OR IGNORE INTO attempts VALUES(?,?,?,?,?,?,?)',
                           (int(match[1]), int(match[2]), failure['retrieved_at_utc'],
                            'historical_access_blocked' if code else 'historical_error', code, None, failure['error']))


def restore(db, folder):
    """Reconstruct the working database from committed manifests after a clone."""
    manifest = json.loads((folder / 'catalog.json').read_text(encoding='utf-8'))
    if manifest['schema_version'] != 1:
        raise ValueError('Unsupported catalog schema')
    with db:
        for row in manifest['observations']:
            db.execute('INSERT OR IGNORE INTO observations VALUES(?,?,?,?,?,?,?,?)',
                       tuple(row[k] for k in ('dataset', 'page', 'observed_at', 'source_url', 'html_sha256', 'snapshot', 'advertised_pages', 'file_count')))
        for row in manifest['attempts']:
            db.execute('INSERT OR IGNORE INTO attempts VALUES(?,?,?,?,?,?,?)',
                       tuple(row[k] for k in ('dataset', 'page', 'attempted_at', 'status', 'http_status', 'final_url', 'error')))
        with (folder / 'files.csv').open(encoding='utf-8', newline='') as stream:
            for row in csv.DictReader(stream):
                db.execute('''INSERT INTO files VALUES(?,?,?,?,?,?) ON CONFLICT(dataset,url)
                              DO UPDATE SET first_seen=min(first_seen,excluded.first_seen),
                              last_seen=max(last_seen,excluded.last_seen)''',
                           (int(row['dataset']), row['url'], row['filename'], row['file_id'], row['first_seen'], row['last_seen']))
        with (folder / 'provenance.csv').open(encoding='utf-8', newline='') as stream:
            for row in csv.DictReader(stream):
                db.execute('INSERT OR IGNORE INTO appearances VALUES(?,?,?,?,?)',
                           (int(row['dataset']), row['url'], int(row['listing_page']), row['html_sha256'], row['observed_at']))


def import_browser(db, dataset, page, snapshot):
    listing_url(dataset, page)
    if not snapshot.name.endswith('.dom.html'):
        raise ValueError('Expected a .dom.html link snapshot')
    metadata = json.loads(snapshot.with_suffix('.json').read_text(encoding='utf-8'))
    if metadata['url'] != listing_url(dataset, page):
        raise ValueError('Browser snapshot URL does not match requested listing')
    body = snapshot.read_bytes()
    if hashlib.sha256(body).hexdigest() != metadata['sha256']:
        raise ValueError('Browser snapshot hash mismatch')
    record(db, dataset, page, body, metadata['captured_at_utc'],
           str(snapshot.resolve().relative_to(ROOT)).replace('\\', '/'))


def crawl(db, max_pages, delay, refresh_first=False, cache=None):
    # Round-robin by page index, so large datasets do not starve smaller ones.
    queue = [(n, 0) for n in range(1, 13)] if refresh_first else []
    if not refresh_first:
        for dataset in range(1, 13):
            seen = {r[0] for r in db.execute('SELECT DISTINCT page FROM observations WHERE dataset=?', (dataset,))}
            advertised = db.execute('SELECT max(advertised_pages) FROM observations WHERE dataset=?', (dataset,)).fetchone()[0] or 1
            queue.extend((dataset, page) for page in range(advertised) if page not in seen)
        queue.sort(key=lambda pair: (pair[1], pair[0]))
    fetched = 0
    for dataset, page in queue[:max_pages]:
        if fetched:
            time.sleep(delay)
        url, timestamp = listing_url(dataset, page), now()
        status, code, final_url, error = 'error', None, None, None
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'EpsteinFilesResearchCatalog/1.0 (listing-only public research)'})
            with urllib.request.urlopen(request, timeout=25) as response:
                code, final_url = response.status, response.geturl()
                if final_url != url:
                    raise ValueError('Redirected listing; record for access review')
                body = response.read(MAX_HTML + 1)
                if len(body) > MAX_HTML:
                    raise ValueError('Listing exceeds HTML size limit')
                files, _ = parse_listing(body.decode('utf-8-sig'), dataset, page)
                digest = hashlib.sha256(body).hexdigest()
                snapshot = cache / (digest + '.html')
                snapshot.parent.mkdir(parents=True, exist_ok=True)
                snapshot.write_bytes(body)
                record(db, dataset, page, body, timestamp, str(snapshot.relative_to(ROOT)).replace('\\', '/'))
                status = 'observed'
                print(f'Dataset {dataset} page {page}: {len(files)} file links', flush=True)
        except urllib.error.HTTPError as exc:
            code, error = exc.code, str(exc)
            status = 'access_blocked' if code in (401, 403, 429) else 'http_error'
        except (OSError, ValueError, UnicodeError) as exc:
            error = str(exc)
        with db:
            db.execute('INSERT INTO attempts VALUES(?,?,?,?,?,?,?)', (dataset, page, timestamp, status, code, final_url, error))
        fetched += 1
        if status != 'observed':
            print(f'Dataset {dataset} page {page}: {status} ({code}); stopping batch, no automatic retry.', flush=True)
            break
    return fetched


def export(db, folder, pilot):
    folder.mkdir(parents=True, exist_ok=True)
    observations = [dict(r) for r in db.execute('SELECT * FROM observations ORDER BY dataset,page,observed_at')]
    for row in observations:
        row['representation'] = 'browser_link_dom' if row['snapshot'].endswith('.dom.html') else 'http_html'
    attempts = [dict(r) for r in db.execute('SELECT * FROM attempts ORDER BY attempted_at')]
    downloads = {r['url']: r for r in json.loads((pilot / 'downloads.json').read_text(encoding='utf-8'))['files']}
    metrics = {r['file_id']: r for r in json.loads((pilot / 'metrics.json').read_text(encoding='utf-8'))['files']}
    fields = ['dataset', 'file_id', 'filename', 'url', 'first_seen', 'last_seen', 'listing_pages_observed',
              'download_status', 'bytes', 'source_sha256', 'pdf_pages', 'extraction_status']
    with (folder / 'files.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for record_row in db.execute('SELECT * FROM files ORDER BY dataset,url'):
            row = dict(record_row)
            row['listing_pages_observed'] = ';'.join(str(r[0]) for r in db.execute('SELECT DISTINCT page FROM appearances WHERE dataset=? AND url=? ORDER BY page', (row['dataset'], row['url'])))
            download = downloads.get(row['url'])
            metric = metrics.get(row['file_id']) if download else None
            row.update(download_status='pilot_download_record' if download and download['status'] == 'downloaded' else 'not_downloaded',
                       bytes=metric.get('bytes') if metric else None,
                       source_sha256=metric.get('sha256') if metric else None,
                       pdf_pages=metric.get('page_count') if metric else None,
                       extraction_status='pilot_extraction_record' if metric else 'not_processed')
            writer.writerow(row)
    datasets = []
    for dataset in range(1, 13):
        subset = [r for r in observations if r['dataset'] == dataset]
        pages = {r['page'] for r in subset}
        advertised = max((r['advertised_pages'] for r in subset), default=None)
        count = db.execute('SELECT count(*) FROM files WHERE dataset=?', (dataset,)).fetchone()[0]
        complete = advertised is not None and pages == set(range(advertised))
        datasets.append(dict(dataset=dataset, listing_url=listing_url(dataset), observed_listing_pages=len(pages),
                             advertised_listing_pages=advertised, observed_file_urls=count,
                             listing_coverage='all_advertised_pages_observed' if complete else 'partial',
                             current_total_files=None,
                             last_observed_at=max((r['observed_at'] for r in subset), default=None)))
    manifest = dict(schema_version=1, exported_at_utc=now(), scope='Twelve numbered DOJ datasets; observed URL pairs, not unique documents',
                    method='Historical and current listing observations retained separately. No file URLs inferred from EFTA numeric ranges. No document GET or HEAD requests.',
                    observed_file_urls=sum(r['observed_file_urls'] for r in datasets), current_total_files=None,
                    datasets=datasets, observations=observations, attempts=attempts)
    (folder / 'catalog.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    # Separate provenance rows keep the main catalog compact while retaining every discovery.
    with (folder / 'provenance.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['dataset', 'url', 'listing_page', 'html_sha256', 'observed_at'])
        writer.writerows(tuple(r) for r in db.execute('SELECT * FROM appearances ORDER BY dataset,url,page,observed_at'))
    print(f"Exported {manifest['observed_file_urls']} observed dataset/file URL pairs; full current total unknown.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['seed', 'restore', 'crawl', 'import-browser', 'export'])
    parser.add_argument('--database', type=Path, default=ROOT / 'data/catalog/catalog.sqlite')
    parser.add_argument('--seed', type=Path, default=ROOT / 'data/inventory/2026-11-01')
    parser.add_argument('--out', type=Path, default=ROOT / 'data/catalog/2026-11-07')
    parser.add_argument('--max-pages', type=int, default=12)
    parser.add_argument('--delay', type=float, default=1)
    parser.add_argument('--refresh-first', action='store_true')
    parser.add_argument('--dataset', type=int)
    parser.add_argument('--page', type=int, default=0)
    parser.add_argument('--snapshot', type=Path)
    args = parser.parse_args()
    if not 1 <= args.max_pages <= 100 or args.delay < 0.5:
        parser.error('Use 1–100 requests per batch and at least 0.5 seconds between requests')
    with connect(args.database) as db:
        if args.command == 'seed':
            seed(db, args.seed)
        elif args.command == 'restore':
            restore(db, args.out)
        elif args.command == 'import-browser':
            if args.dataset is None or args.snapshot is None or not args.snapshot.name.endswith('.dom.html'):
                parser.error('Browser import requires --dataset, --page and a .dom.html link snapshot')
            import_browser(db, args.dataset, args.page, args.snapshot)
        elif args.command == 'crawl':
            crawl(db, args.max_pages, args.delay, args.refresh_first, ROOT / 'data/catalog/cache')
        export(db, args.out, ROOT / 'data/pilot/2026-11-01')


if __name__ == '__main__':
    main()
