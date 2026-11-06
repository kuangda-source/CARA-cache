#!/usr/bin/env python3
"""Read the complete real parameter / four Native capsule; never install it."""
import argparse
import hashlib
import os
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from wcomr.current_birth_real_inputs_r1 import load


def main():
    started = time.perf_counter()
    parser=argparse.ArgumentParser()
    parser.add_argument('--project',type=Path,required=True)
    args=parser.parse_args()
    os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    import torch
    def forbidden(*a,**kw):raise RuntimeError('Metadata CPU forbids CUDA and weight downloads')
    torch.cuda._lazy_init=forbidden
    torch.hub.download_url_to_file=forbidden
    assert not torch.cuda.is_initialized()
    reg_path = ROOT / 'manifests/wc_current_birth_real_inputs_cpu_r3_preregistration_20261010.json'
    reg = json.loads(reg_path.read_text())
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    budget = args.project / 'reports/budget.json'
    before = sha(budget)
    for name, value in reg['source_sha256'].items():
        if sha(ROOT / name) != value:
            raise ValueError('Registered complete real input source changed: ' + name)
    from wcomr import source_aware_current_birth_sampling_r2 as sampler
    required=('METHODS','STRATEGIES','valid_P_interval','verify_batch','DERIVATION_PROOFS','run_batch','audit_vectors')
    assert all(hasattr(sampler,n) for n in required)
    calibration, specs, references, parent, evidence = load(ROOT)
    assert tuple(specs) == tuple(reg['strategies'])
    assert all(tuple(value) == tuple(reg['methods']) for value in specs.values())
    assert [r['sample_name'] for r in references] == reg['sample_names']
    assert evidence['complete_cost_rows'] == 48 and evidence['timed_values'] == 144
    assert evidence['reference_project_input_sha256'] == parent['project_input_sha256']
    assert evidence['actual_threshold_reconstruction']['threshold'] == .070744235098772
    assert evidence['current_P_birth_rule'] == reg['current_P_birth_rule']
    assert not torch.cuda.is_initialized() and before == sha(budget)
    value = {'status': 'COMPLETE_REAL_INPUTS_AND_NATIVE_METADATA_CPU_BOUND_NOT_VIDEO_EXECUTION',
        'registration_ref': str(reg_path.relative_to(ROOT)), 'registration_sha256': sha(reg_path),
        'source_sha256': reg['source_sha256'], 'evidence': evidence,
        'scope_counts': reg['scope_counts'], 'complete_method_parameter_sets': 16,
        'complete_native_reference_metadata_slots': 4,
        'CPU_wall_seconds': time.perf_counter() - started,
        'Torch_imported': True, 'CUDA_initialized': False, 'GPU_submissions': 0,
        'model_or_controller_installed': False, 'budget_written': False,
        'budget_before_sha256': before, 'budget_after_sha256': sha(budget),
        'live_Native_file_hashes_verified': True, 'new_trajectory_compatibility_pending': True}
    for ref in references:
        artifact=ref['artifact'];path=Path(artifact['path']).resolve()
        if (not path.is_relative_to((args.project/'outputs').resolve())
                or path.stat().st_size!=artifact['bytes'] or sha(path)!=artifact['sha256']):
            raise ValueError('Actual matched Native video file changed')
    value['actual_Native_file_sizes_and_hashes_verified']=4
    value['fixture_API_required_exports_verified']=list(required)
    value['metadata_native_decode_provenance_already_independently_accepted']=True
    dest = ROOT / 'reports/wc_current_birth_real_inputs_cpu_r3_results_20261010.json'
    if dest.exists():
        raise ValueError('Preserve first metadata binding; register revisions separately')
    dest.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: value[k] for k in ('status', 'CPU_wall_seconds', 'GPU_submissions')}))


if __name__ == '__main__':
    main()
