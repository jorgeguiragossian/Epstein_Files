"""Prepare a bounded PDF expansion from observed catalog URLs; no network calls."""
import argparse
import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def read_csv(path):
    with path.open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def choose(rows, excluded_urls, per_dataset=10):
    if not 1 <= per_dataset <= 10:
        raise ValueError('Use 1–10 PDFs per dataset')
    pools = {dataset: {} for dataset in range(1, 13)}
    for row in rows:
        url = urlsplit(row['url'])
        dataset = int(row['dataset'])
        if dataset not in pools or row['url'] in excluded_urls or row.get('download_status') != 'not_downloaded':
            continue
        if url.scheme != 'https' or url.netloc != 'www.justice.gov' or url.query or url.fragment:
            continue
        if not unquote(url.path).startswith(f'/epstein/files/DataSet {dataset}/') or not url.path.lower().endswith('.pdf'):
            continue
        if row['filename'] != unquote(url.path.rsplit('/', 1)[-1]):
            raise ValueError('Filename does not match observed URL')
        pages = [int(value) for value in row['listing_pages_observed'].split(';')]
        if min(pages) < 0:
            raise ValueError('Invalid listing page')
        pools[dataset][row['url']] = dict(row, dataset=dataset, first_observed_listing_page=min(pages))
    selected, coverage = [], []
    for dataset, unique in pools.items():
        pool = sorted(unique.values(), key=lambda row: (row['first_observed_listing_page'], row['url']))
        count = min(per_dataset, len(pool))
        positions = [j * (len(pool) - 1) // (count - 1) for j in range(count)] if count > 1 else ([0] if count else [])
        selected.extend(dict(pool[position], observed_pool_size=len(pool), zero_based_pool_position=position) for position in positions)
        coverage.append(dict(dataset=dataset, eligible_observed_pdfs=len(pool), selected=count,
                             reason='evenly_spaced_observed_pool_positions' if count else 'no_remaining_eligible_observed_pdfs'))
    return selected, coverage


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path, default=ROOT / 'data/catalog/2026-11-07')
    parser.add_argument('--out', type=Path, default=ROOT / 'data/pilot/2026-11-07-expansion')
    parser.add_argument('--wave-out', type=Path, default=ROOT / 'data/pilot/2026-11-07-wave-01')
    args = parser.parse_args()
    if any((folder / 'selection.json').exists() for folder in (args.out, args.wave_out)):
        raise SystemExit('Selection already exists; retain it or use new output directories')
    prior_path = ROOT / 'data/pilot/2026-11-01/selection.json'
    excluded = {row['url'] for row in json.loads(prior_path.read_text(encoding='utf-8'))['files']}
    selected, coverage = choose(read_csv(args.catalog / 'files.csv'), excluded)
    if len(selected) != 100 or len({r['url'] for r in selected}) != 100:
        raise ValueError('Expected 100 new PDF URLs for this milestone; review changed coverage')
    provenance = read_csv(args.catalog / 'provenance.csv')
    for row in selected:
        evidence = [p for p in provenance if p['url'] == row['url'] and int(p['dataset']) == row['dataset']
                    and int(p['listing_page']) == row['first_observed_listing_page']]
        if not evidence:
            raise ValueError('Selected URL has no matching listing provenance')
        row['listing_evidence'] = max(evidence, key=lambda r: r['observed_at'])
    plan = dict(schema_version=1, created_at_utc=datetime.now(timezone.utc).isoformat(),
                source_catalog_git_revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                status='planned_not_downloaded', source_catalog=str((args.catalog / 'files.csv').relative_to(ROOT)).replace('\\', '/'),
                source_catalog_sha256=sha(args.catalog / 'files.csv'), source_provenance_sha256=sha(args.catalog / 'provenance.csv'),
                excluded_pilot_selection_sha256=sha(prior_path),
                method='Ten evenly spaced positions in each remaining observed PDF pool; excludes prior pilot URLs and processed catalog records. Non-random coverage sample, not a representative collection sample. No dates or topics inferred from filenames.',
                limits=dict(max_file_bytes=64 * 1024 * 1024, max_total_bytes=512 * 1024 * 1024,
                            extraction_timeout_seconds_per_file=120, ocr=False, live_ai=False),
                coverage=coverage, files=selected)
    wave = dict(plan, parent_selection=str((args.out / 'selection.json').relative_to(ROOT)).replace('\\', '/'),
                method='First wave: the ten dataset 8 PDFs from the parent selection. Measure extraction and review needs before processing the rest.',
                files=[row for row in selected if row['dataset'] == 8])
    wave.pop('coverage')
    assert len(wave['files']) == 10
    for folder, value in ((args.out, plan), (args.wave_out, wave)):
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'selection.json').write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    print('Planned 100 new PDFs across ten datasets; first dataset 8 wave contains 10. No downloads performed.')


if __name__ == '__main__':
    main()
