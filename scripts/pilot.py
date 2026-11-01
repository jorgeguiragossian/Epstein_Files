"""Bounded DOJ PDF pilot. No AI calls, OCR, mirrors, or automatic retries.

Run select first, then download with --age-confirmed, then analyze.
PDFs and page text are ignored by Git; published metrics contain no contact values.
"""
import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / 'data/pilot/2026-11-01'
MAX_FILE = 64 * 1024 * 1024
MAX_TOTAL = 512 * 1024 * 1024
DATE = re.compile(r'\b(?:\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[/.-]\d{1,2}[/.-](?:\d{4}|\d{2})|(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s+\d{1,2},?\s+\d{4}|\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s+\d{4})\b', re.I)
HEADER = re.compile(r'^\s*(From|To|Cc|Bcc|Sent|Date|Subject)\s*:\s*(.*)$', re.I)
ADDRESS = re.compile(r'[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}', re.I)


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def select(out, inventory):
    if (out / 'selection.json').exists():
        raise SystemExit('Selection already exists; reuse it or choose a new output directory.')
    with inventory.open(encoding='utf-8-sig', newline='') as stream:
        source = list(csv.DictReader(stream))
    selected = []
    for dataset in range(1, 13):
        rows = sorted((r for r in source if int(r['dataset']) == dataset), key=lambda r: r['file_id'])
        positions = list(range(len(rows))) if dataset in (6, 7) else [j * (len(rows) - 1) // 6 for j in range(7)]
        if len(set(positions)) != len(positions):
            raise SystemExit(f'Insufficient candidates in dataset {dataset}')
        for position in positions:
            selected.append(dict(rows[position], dataset=dataset, observed_pool_size=len(rows), zero_based_pool_position=position))
    if len(selected) != 100 or len({r['url'] for r in selected}) != 100:
        raise SystemExit('Expected 100 distinct source URLs')
    save(out / 'selection.json', {'created_at_utc': now(), 'inventory': str(inventory.relative_to(ROOT)),
        'inventory_sha256': digest(inventory), 'method': 'All visible files in datasets 6 and 7; seven evenly spaced positions in each other first-page pool. Non-random, first-page biased coverage pilot.', 'files': selected})
    print('Selected 100 documents across all 12 datasets.', flush=True)


def download(out, age_confirmed):
    if not age_confirmed:
        raise SystemExit('DOJ requires adult age verification; pass --age-confirmed only after confirmation.')
    selection = read(out / 'selection.json')['files']
    log = out / 'downloads.json'
    records = read(log)['files'] if log.exists() else []
    # A fresh clone contains the manifest but not the ignored PDF cache.
    # Redownload missing/changed cached files instead of trusting historical logs.
    complete = {r['url'] for r in records if r['status'] != 'downloaded' or
        ((out / r['local_path']).is_file() and digest(out / r['local_path']) == r['sha256'])}
    records = [r for r in records if r['url'] in complete]
    used = sum(p.stat().st_size for p in (out / 'cache').glob('*.pdf'))
    for item in selection:
        if item['url'] in complete:
            continue
        parsed = urllib.parse.urlsplit(item['url'])
        if parsed.scheme != 'https' or parsed.netloc != 'www.justice.gov' or not parsed.path.startswith('/epstein/files/'):
            raise SystemExit('Source URL outside the approved DOJ file path')
        result = dict(item, attempted_at_utc=now(), status='pending', http_status=None)
        path = out / 'cache' / f"ds{item['dataset']:02d}-{item['filename']}"
        part = path.with_suffix('.part')
        try:
            if used >= MAX_TOTAL:
                result['status'] = 'total_byte_limit'
            else:
                request = urllib.request.Request(item['url'], headers={'User-Agent': 'EpsteinFilesResearchPilot/0.1 (bounded 100-document sample)', 'Cookie': 'justiceGovAgeVerified=true'})
                with urllib.request.urlopen(request, timeout=60) as response:
                    result.update(http_status=response.status, final_url=response.url,
                        content_type=response.headers.get('Content-Type'), content_length=response.headers.get('Content-Length'))
                    final = urllib.parse.urlsplit(response.url)
                    if final.netloc != 'www.justice.gov' or not final.path.startswith('/epstein/files/'):
                        result['status'] = 'redirected_outside_file_path'
                    elif int(response.headers.get('Content-Length', 0)) > min(MAX_FILE, MAX_TOTAL - used):
                        result['status'] = 'byte_limit'
                    else:
                        path.parent.mkdir(parents=True, exist_ok=True)
                        size = 0
                        with part.open('wb') as stream:
                            for chunk in iter(lambda: response.read(1024 * 1024), b''):
                                size += len(chunk)
                                if size > min(MAX_FILE, MAX_TOTAL - used):
                                    raise ValueError('byte_limit')
                                stream.write(chunk)
                        with part.open('rb') as stream:
                            is_pdf = stream.read(1024).lstrip().startswith(b'%PDF-')
                        if not is_pdf:
                            result['status'] = 'non_pdf_response'
                        else:
                            part.replace(path)
                            used += size
                            result.update(status='downloaded', bytes=size, sha256=digest(path), local_path=path.relative_to(out).as_posix())
        except urllib.error.HTTPError as exc:
            result.update(status='http_error', http_status=exc.code)
        except Exception as exc:
            result.update(status='error', error_type=type(exc).__name__, error=str(exc)[:240])
        finally:
            if part.exists():
                part.unlink()
        records.append(result)
        save(log, {'updated_at_utc': now(), 'max_file_bytes': MAX_FILE, 'max_total_bytes': MAX_TOTAL, 'files': records})
        print(f"{len(records)}/100 ds{item['dataset']:02d} {item['file_id']}: {result['status']} {result.get('bytes', '')}", flush=True)
        time.sleep(0.4)


def extract_one(pdf, target):
    import pypdf
    reader = pypdf.PdfReader(pdf)
    if reader.is_encrypted and not reader.decrypt(''):
        raise ValueError('encrypted_password_required')
    pages, header_blocks, dates = [], [], []
    all_words = Counter()
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ''
        lines = text.splitlines()
        chars = sum(c.isalnum() for c in text)
        # The EFTA stamp alone is not substantive text.
        substantive = re.sub(r'\bEFTA\d+\b', '', text, flags=re.I)
        substantive_chars = sum(c.isalnum() for c in substantive)
        page_dates = []
        for line_number, line in enumerate(lines, start=1):
            for match in DATE.finditer(line):
                candidate = {'page': index, 'line': line_number, 'raw': match.group(0), 'role': 'unclassified_mention', 'validated': False}
                page_dates.append(candidate)
                dates.append(candidate)
        for line_index, line in enumerate(lines):
            match = HEADER.match(line)
            if not match or match.group(1).lower() != 'from':
                continue
            headers = []
            for offset, header_line in enumerate(lines[line_index:line_index + 20]):
                h = HEADER.match(header_line)
                if h:
                    if headers and h.group(1).lower() == 'from':
                        break
                    headers.append({'field': h.group(1).lower(), 'value': h.group(2), 'line': line_index + offset + 1})
            fields = {h['field'] for h in headers}
            if 'to' in fields and fields.intersection({'sent', 'date'}):
                header_blocks.append({'page': index, 'start_line': line_index + 1, 'headers': headers,
                    'email_addresses': sorted(set(ADDRESS.findall('\n'.join(h['value'] for h in headers)))),
                    'status': 'unverified_header_candidate_not_unique_message'})
        words = re.findall(r"[A-Za-z]{3,}(?:'[A-Za-z]+)?", substantive)
        all_words.update(w.lower() for w in words)
        # Image counts detect XObjects only, not every inline image or scanned page.
        resources = page.get('/Resources', {})
        resources = resources.get_object() if hasattr(resources, 'get_object') else resources
        objects = resources.get('/XObject', {})
        objects = objects.get_object() if hasattr(objects, 'get_object') else objects
        image_count = sum(1 for obj in objects.values() if obj.get_object().get('/Subtype') == '/Image')
        pages.append({'page': index, 'text': text, 'characters': len(text), 'alphanumeric_characters': chars,
            'substantive_alphanumeric_characters': substantive_chars, 'low_text_candidate': substantive_chars < 80,
            'image_xobjects': image_count, 'date_candidates': page_dates})
    metrics = {'status': 'extracted', 'pypdf_version': pypdf.__version__, 'page_count': len(pages),
        'pages_processed': len(pages), 'characters': sum(p['characters'] for p in pages),
        'low_text_pages': sum(p['low_text_candidate'] for p in pages),
        'zero_text_pages': sum(p['alphanumeric_characters'] == 0 for p in pages),
        'pages_with_image_xobjects': sum(p['image_xobjects'] > 0 for p in pages),
        'date_candidate_count': len(dates), 'date_candidates': dates,
        'email_header_candidate_count': len(header_blocks), 'candidate_document_type': 'email_headers_detected' if header_blocks else 'unclassified',
        'document_date': None, 'document_date_status': 'requires_context_review',
        'ocr_performed': False, 'ocr_review_needed': any(p['low_text_candidate'] for p in pages),
        'unique_words': len(all_words), 'word_tokens': sum(all_words.values()),
        'page_metrics': [{k:v for k,v in p.items() if k not in ('text', 'date_candidates')} for p in pages]}
    save(target, {'source_filename': pdf.name, 'source_sha256': digest(pdf), 'metrics': metrics, 'pages': pages, 'email_header_candidates': header_blocks,
        'word_counts': dict(all_words), 'review_status': 'unreviewed_do_not_publish_text_or_infer_relationships'})


def analyze(out):
    downloads = read(out / 'downloads.json')['files']
    results = []
    for item in downloads:
        result = {k:item.get(k) for k in ('dataset','file_id','url','sha256','bytes')}
        if item['status'] != 'downloaded':
            result.update(status='not_downloaded', download_status=item['status'])
        else:
            target = out / 'extractions' / (Path(item['local_path']).stem + '.json')
            try:
                if not target.exists() or read(target).get('source_sha256') != item['sha256']:
                    subprocess.run([sys.executable, str(Path(__file__).resolve()), '_extract', '--pdf', str(out / item['local_path']), '--target', str(target)],
                        check=True, capture_output=True, timeout=120)
                extraction = read(target)
                result.update(extraction['metrics'])
                result['extraction_path'] = target.relative_to(out).as_posix()
            except subprocess.TimeoutExpired:
                result.update(status='extraction_timeout', timeout_seconds=120)
            except Exception as exc:
                result.update(status='extraction_error', error_type=type(exc).__name__)
        results.append(result)
        save(out / 'metrics.json', {'updated_at_utc': now(), 'method': 'pypdf native text only; low-text threshold <80 substantive alphanumeric characters/page, excluding EFTA stamps. Dates and email blocks are unverified candidates, never established document dates or unique messages.', 'files': results})
        print(f"Analyzed {len(results)}/{len(downloads)} {item['file_id']}: {result['status']}", flush=True)
    fields = ['dataset','file_id','url','status','bytes','sha256','page_count','pages_processed','characters','low_text_pages','zero_text_pages','pages_with_image_xobjects','date_candidate_count','email_header_candidate_count','ocr_review_needed','candidate_document_type','word_tokens','unique_words']
    with (out / 'metrics.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(results)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['select','download','analyze','_extract'])
    parser.add_argument('--out', type=Path, default=DEFAULT)
    parser.add_argument('--inventory', type=Path, default=ROOT / 'data/inventory/2026-11-01/observed-files.csv')
    parser.add_argument('--age-confirmed', action='store_true')
    parser.add_argument('--pdf', type=Path)
    parser.add_argument('--target', type=Path)
    args = parser.parse_args()
    if args.action == 'select': select(args.out, args.inventory)
    elif args.action == 'download': download(args.out, args.age_confirmed)
    elif args.action == 'analyze': analyze(args.out)
    else: extract_one(args.pdf, args.target)
