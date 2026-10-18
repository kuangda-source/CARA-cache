#!/usr/bin/env python3
"""Freeze read-only entry dependencies; never changes an accepted config/stage."""
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    entrypoints = ['scripts/wc_scout_gpu_lifecycle_cpu_r1.py', 'scripts/check_wc_scout_gpu_lifecycle_r1.py',
        'scripts/launch_wc_scout_gpu_r1.py', 'scripts/supervise_wc_scout_gpu_r1.py', 'scripts/watch_wc_scout_post_cpu_r1.py',
        'scripts/postprocess_wc_scout_gpu_r1.py', 'scripts/capture_wc_scout_gpu_r1.py', 'scripts/analyze_wc_scout_gpu_r1.py',
        'scripts/capture_wc_scout_gpu_lifecycle_cpu_r1.py']
    for kind in ('CAL12', 'BANK24'):
        prefix = 'reports/wc_scout_'+kind+'_real_entry_CPU_R1_'
        refs = dict(launch=prefix+'launch_20261018.json', capture=prefix+'collection_20261018.json.gz',
                    accepted=prefix+'independent_acceptance_20261018.json')
        cap = json.loads(gzip.decompress((ROOT/refs['capture']).read_bytes())); reg = cap['registration']
        meta = dict(status='SCOUT_DISTINCT_LIFECYCLE_OVER_UNCHANGED_ACCEPTED_REAL_ENTRY', kind=kind,
            entry_stage=reg['stage'], entry_source_revision=reg['source_revision'],
            entry_registration_sha256=cap['registration_sha256'],
            config_ref='configs/wc_scout_'+kind.lower()+'_production_entry_r1_20261018.json',
            evidence={k: dict(ref=v, sha256=hashlib.sha256((ROOT/v).read_bytes()).hexdigest()) for k, v in refs.items()},
            lifecycle_entrypoints=entrypoints, reuse_numerical_CPU=True, reuse_real_entry_CPU=True,
            execution_stage_written=False, algorithm_or_request_changed=False,
            lifecycle_planning_cost_increment_GPUh=0, GPU_submissions=0,
            CPU_post_outside_GPU_bill=True, original_request_observer_allowance_kept=True)
        path = ROOT/('manifests/scout_'+kind.lower()+'_lifecycle_dependency_r1_20261018.json')
        with path.open('x') as f: json.dump(meta, f, indent=2); f.write('\n')
        print(json.dumps(dict(kind=kind, dependency=str(path.relative_to(ROOT)), entry_source=reg['source_revision'])))


if __name__ == '__main__': main()
