"""Freeze 25 observed URLs for a bounded second expansion; no network calls."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'data/pilot/2026-11-15-phase-02'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if (OUT/'selection.json').exists():
        raise ValueError('Selection exists; retain it instead of regenerating')
    spec=importlib.util.spec_from_file_location('planner',ROOT/'scripts/plan-expansion.py')
    planner=importlib.util.module_from_spec(spec);spec.loader.exec_module(planner)
    catalog=ROOT/'data/catalog/2026-11-07'
    registry=ROOT/'data/pilot/viewer-batches.json'
    selections=[ROOT/'data/pilot/2026-11-01/selection.json']+[
        ROOT/b['path']/'selection.json' for b in read(registry)['batches']]
    excluded={f['url'] for path in selections for f in read(path)['files']}
    if len(excluded)!=200:
        raise ValueError('Processed selection baseline changed; review scope')
    candidates,coverage=planner.choose(planner.read_csv(catalog/'files.csv'),excluded,per_dataset=5)
    selected=[f for f in candidates if f['dataset'] in (8,9,10,11,12)]
    if len(selected)!=25 or len({f['url'] for f in selected})!=25:
        raise ValueError('Expected 25 distinct new observed PDF URLs')
    provenance=planner.read_csv(catalog/'provenance.csv')
    for f in selected:
        evidence=[p for p in provenance if p['url']==f['url'] and int(p['dataset'])==f['dataset']
                  and int(p['listing_page'])==f['first_observed_listing_page']]
        if not evidence:raise ValueError('Missing observed listing provenance')
        f['listing_evidence']=max(evidence,key=lambda p:p['observed_at'])
    plan=dict(schema_version=1,planned_on='2026-11-15',status='planned_not_downloaded',
        source_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        source_catalog='data/catalog/2026-11-07/files.csv',source_catalog_sha256=sha(catalog/'files.csv'),
        source_provenance_sha256=sha(catalog/'provenance.csv'),
        excluded_processed_urls=len(excluded),exclusion_selection_sha256={
            p.relative_to(ROOT).as_posix():sha(p) for p in selections},
        registry_sha256=sha(registry),
        method='Five evenly spaced positions in each remaining observed PDF pool for datasets 8-12. '
               'Deterministic non-random coverage sample; not representative. No topic, date, size, '
               'email content or identity inferred from filenames. Listing observations are historical '
               'and must be checked during normal-browser acquisition.',
        limits=dict(max_file_bytes=64*1024**2,max_wave_bytes=128*1024**2,
                    max_expansion_bytes=512*1024**2,extraction_timeout_seconds_per_file=120,
                    active_evidence_cache_limit_bytes=2*1024**3,paid_ocr=False,live_ai=False),
        first_wave=dict(dataset=9,files=5,reason='Prior ten-file dataset9 sample had38native header candidates '
                       'across38pages; this is a workload signal only, not a content prediction.'),
        catalog_limits='24,447 observed dataset/file URL pairs; full current release total unknown. '
                       'Datasets9/10/11 observed pages0-60, next unobserved61. '
                       'No completeness claim or file URL inferred from numeric ranges.',
        coverage=[c for c in coverage if c['dataset'] in (8,9,10,11,12)],files=selected)
    OUT.mkdir(parents=True,exist_ok=True)
    target=OUT/'selection.json';target.write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
    first=dict(schema_version=1,status='planned_not_downloaded',parent_selection=target.relative_to(ROOT).as_posix(),
               parent_selection_sha256=sha(target),dataset=9,files=[f for f in selected if f['dataset']==9])
    (OUT/'first-wave.json').write_text(json.dumps(first,indent=2)+'\n',encoding='utf-8')
    print('Frozen25observedURLs, excluded200processed; first wave5dataset9PDFs. No downloads.')


if __name__=='__main__':main()
