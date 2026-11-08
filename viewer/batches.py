"""Load explicitly registered expansion batches without altering the original pilot."""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def script(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_expansions():
    try:
        from .email_parser import parse_document
    except ImportError:
        from email_parser import parse_document
    registry = read(ROOT / 'data/pilot/viewer-batches.json')
    prepared, records = [], []
    for batch in registry['batches']:
        folder = (ROOT / batch['path']).resolve()
        if not folder.is_relative_to(ROOT / 'data/pilot'):
            raise ValueError('Expansion folder outside pilot workspace')
        for filename, expected in batch['evidence_sha256'].items():
            if hashlib.sha256((folder / filename).read_bytes()).hexdigest() != expected:
                raise ValueError('Expansion evidence changed: ' + filename)
        metrics = read(folder / 'metrics.json')['files']
        downloads = {r['url']: r for r in read(folder / 'downloads.json')['files']}
        selected = read(folder / 'selection.json')['files']
        if {r['url'] for r in metrics} != {r['url'] for r in selected} or len(metrics) != batch['documents']:
            raise ValueError('Incomplete expansion selection')
        current = []
        for metric in metrics:
            item = downloads[metric['url']]
            pdf = folder / item['local_path']
            extracted = read(folder / metric['extraction_path'])
            if (metric['status'] != 'extracted' or item['status'] != 'downloaded'
                    or hashlib.sha256(pdf.read_bytes()).hexdigest() != metric['sha256']
                    or item['sha256'] != metric['sha256'] or extracted['source_sha256'] != metric['sha256']
                    or len(extracted['pages']) != metric['page_count']):
                raise ValueError('Expansion source/extraction validation failed')
            current.append((metric, item, extracted, pdf))
        mode = batch.get('review_mode','derived_header_layers_v1')
        if mode == 'native_correspondence_v1':
            if 'correspondence-reviews.json' not in batch['evidence_sha256']:
                raise ValueError('Native correspondence review requires pinned evidence')
            reviewed, _ = script('check-wave-correspondence').build_catalog(folder)
        elif mode == 'native_layout_review_v1':
            if 'table-date-role-reviews.json' not in batch['evidence_sha256']:
                raise ValueError('Native layout review requires pinned evidence')
            script('check-table-date-review').validate(folder)
            rows = read(folder/'table-date-role-reviews.json')['reviews']
            by_id = {r['file_id']:r for r in rows}
            for metric,item,extracted,pdf in current:
                metric['source_quality_review'] = by_id[metric['file_id']]
            reviewed = dict(records=[])
        elif mode == 'derived_header_layers_v1':
            script('prepare-header-layers').main(folder)
            reviewed, _ = script('prepare-wave-boundaries').build_catalog(folder)
        else:
            raise ValueError('Unsupported expansion review mode')
        checked = {}
        for record in reviewed['records']:
            checked.setdefault(record['file_id'], []).append(record)
        for metric, item, extracted, pdf in current:
            key = metric['file_id']
            candidates = checked[key] if key in checked else parse_document(extracted, key, metric['dataset'], metric['sha256'])
            for candidate in candidates:
                if candidate.get('derived_text_layer'):
                    candidate['native_header_evidence'] = [dict(page=h['page'], line=h['line'],
                        text=extracted['pages'][h['page'] - 1]['text'].splitlines()[h['line'] - 1]) for h in candidate['header_evidence']]
            records.extend(candidates)
        prepared.extend(current)
    return prepared, records


def load_expansion_dates():
    rows = []
    for batch in read(ROOT / 'data/pilot/viewer-batches.json')['batches']:
        expected = batch['evidence_sha256'].get('date-reviews.json')
        if expected is None:
            continue
        folder = (ROOT / batch['path']).resolve()
        if not folder.is_relative_to(ROOT / 'data/pilot'):
            raise ValueError('Expansion folder outside pilot workspace')
        path = folder / 'date-reviews.json'
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Expansion date evidence changed')
        rows.extend(read(path)['reviews'])
    return rows


def merge_catalog(base, extra, document_count):
    try:
        from .email_parser import group_records
    except ImportError:
        from email_parser import group_records
    records = base['records'] + extra
    if len({r['id'] for r in records}) != len(records):
        raise ValueError('Duplicate email candidate ID across batches')
    groups = group_records(records)
    summary = dict(base['summary'])
    summary.update(documents_scanned=document_count, candidate_occurrences=len(records),
                   documents_with_candidates=len({r['file_id'] for r in records}), visible_groups=len(groups),
                   repeat_groups=sum(g['occurrences'] > 1 for g in groups),
                   exact_visible_copy_groups=sum(g['kind'] == 'exact_visible_copies' for g in groups),
                   possible_repeat_groups=sum(g['kind'] == 'possible_repeat_incomplete' for g in groups),
                   flag_counts={flag: sum(flag in r['flags'] for r in records) for flag in sorted({f for r in records for f in r['flags']})})
    reviewed = [r for r in records if r.get('source_review')]
    summary['source_review'] = dict(summary['source_review'], reviewed_candidates=len(reviewed),
        documents_with_reviewed_candidates=len({r['file_id'] for r in reviewed}),
        supported_segments=sum(r['source_review']['boundary_status'] == 'supported_segment' for r in reviewed),
        boundary_attention=sum(r['source_review']['boundary_status'] != 'supported_segment' for r in reviewed))
    partitions = [r['body_partition'] for r in records if r.get('body_partition')]
    summary['body_partitions'] = dict(summary['body_partitions'], annotated_candidates=len(partitions),
        quoted_spans=sum(s['kind'] in ('inline_quote', 'forwarded_quote', 'inline_quote_header_only') for p in partitions for s in p['spans']))
    return dict(summary=summary, records=records, groups=groups)
