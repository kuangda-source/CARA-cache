#!/usr/bin/env python3
"""Real lifecycle binding check, reusing unchanged actual request/guardrail CPU."""
import argparse
import os
from pathlib import Path
import sys


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for n in ('project', 'stage'): p.add_argument('--'+n, type=Path, required=True)
    a = p.parse_args(); os.environ['CUDA_VISIBLE_DEVICES'] = ''; sys.path.insert(0, str(a.stage/'src'))
    from wcomr.scout_gpu_lifecycle_r1 import bound_dependency, sha, dependency_ref, CPU_PROOF, counts
    from wcomr.scout_sampling_r1 import matrix
    from wcomr.gpu_budget_pool_v2 import atomic_json
    meta, c, reg, cap, accepted = bound_dependency(a.project, a.stage)
    from wcomr.scout_production_entry_r1 import validate
    # This traverses the real config, source, calibration, original guardrail
    # proof and complete request matrix. It never reruns a Toy or model path.
    actual, original, *_ = validate(a.project, Path(meta['entry_stage']))
    assert actual == c and original == cap['registration']
    assert cap['files']['proof']['data']['matrix'] == matrix(c['kind'], [r['name'] for r in c['requests']])
    import ast
    for name in meta['lifecycle_entrypoints']:
        ast.parse((a.stage/name).read_text(), filename=name)
    import torch
    assert not torch.cuda.is_initialized()
    assert not (a.stage/CPU_PROOF).exists()
    atomic_json(a.stage/CPU_PROOF, dict(status='SCOUT_LIFECYCLE_REAL_DEPENDENCY_AND_FULL_MATRIX_CHECK_PASS',
        kind=c['kind'], scope_counts=counts(c['kind']), source_revision=reg['source_revision'],
        registration_sha256=sha(a.stage/'registration.json'), dependency_sha256=sha(a.stage/dependency_ref(a.stage)),
        entry_source_revision=meta['entry_source_revision'], entry_registration_sha256=meta['entry_registration_sha256'],
        entry_CPU_sha256=accepted['production_entry_CPU_sha256'], entry_CPU_accepted=True,
        full_registered_request_matrix_checked=True, original_execution_stage_written=False,
        numerical_paths_reexecuted=0, real_entry_CPU_reexecuted=False, CUDA_initialized=False,
        GPU_submissions=0, ledger_written=False))


if __name__ == '__main__': main()
