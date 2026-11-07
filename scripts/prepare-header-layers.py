"""Rebuild opt-in source-reviewed label layers and local candidates, without publishing text."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from viewer.source_layers import header_label_layer, header_fragment_layer
from viewer.email_parser import parse_document, VERSION, DATE_VERSION


def main(folder):
    metrics = json.loads((folder / 'metrics.json').read_text(encoding='utf-8'))['files']
    reviews = json.loads((folder / 'header-label-reviews.json').read_text(encoding='utf-8'))['reviews']
    by_id = {r['file_id']: r for r in reviews}
    fragment_path = folder / 'header-fragment-reviews.json'
    fragments = json.loads(fragment_path.read_text(encoding='utf-8'))['reviews'] if fragment_path.exists() else []
    fragment_by_id = {r['file_id']: r for r in fragments}
    if len(fragment_by_id) != len(fragments) or set(fragment_by_id) & set(by_id):
        raise ValueError('Duplicate or conflicting header layers')
    if not set(fragment_by_id) <= {r['file_id'] for r in metrics}:
        raise ValueError('Unknown fragment review document')
    if len(by_id) != len(reviews) or not set(by_id) <= {r['file_id'] for r in metrics}:
        raise ValueError('Duplicate or unknown label review')
    counts = []
    for metric in metrics:
        key = metric['file_id']
        extracted = json.loads((folder / metric['extraction_path']).read_text(encoding='utf-8'))
        native = parse_document(extracted, key, metric['dataset'], metric['sha256'])
        records = native
        if key in by_id or key in fragment_by_id:
            derived = (header_label_layer(extracted, key, metric['sha256'], by_id[key]) if key in by_id else
                       header_fragment_layer(extracted, key, metric['sha256'], fragment_by_id[key]))
            records = parse_document(derived, key, metric['dataset'], metric['sha256'])
            for record in records:
                record['derived_text_layer'] = derived['derived_text_layer']
                if key in by_id:
                    record['flags'] = sorted(set(record['flags'] + ['source_assisted_header_labels', 'quoted_body_boundary_unresolved']))
                else:
                    record['unresolved_header_fragments'].extend(derived['derived_text_layer']['unresolved_fragments'])
                    record['flags'] = sorted(set(record['flags'] + ['source_assisted_header_fragment', 'header_fragments_unresolved']))
            out = folder / 'extractions/header-reviewed'
            out.mkdir(parents=True, exist_ok=True)
            (out / (key + '.json')).write_text(json.dumps(dict(derived_extraction=derived, candidates=records), indent=2) + '\n', encoding='utf-8')
        counts.append(dict(file_id=key, native_candidates=len(native), with_reviewed_layer_candidates=len(records),
                           reviewed_layer_applied=key in by_id or key in fragment_by_id))
    result = dict(parser_version=VERSION, date_parser_version=DATE_VERSION, documents=counts,
                  native_candidate_occurrences=sum(r['native_candidates'] for r in counts),
                  with_reviewed_layers_candidate_occurrences=sum(r['with_reviewed_layer_candidates'] for r in counts),
                  public_site_integration=False, unique_messages_verified=False, contact_rankings_ready=False,
                  interpretation='Richer viewer-parser counts, distinct from the simple pilot header heuristic. Source-assisted label/fragment layers are explicit opt-ins; native text and unresolved fragments are preserved.')
    (folder / 'header-parser-assessment.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(f"Native candidates: {result['native_candidate_occurrences']}; with reviewed header layers: {result['with_reviewed_layers_candidate_occurrences']}.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    main(parser.parse_args().out)
