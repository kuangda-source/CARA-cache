#!/usr/bin/env python3
"""Read the complete real parameter / four Native capsule; never install it."""
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from wcomr.current_birth_real_inputs_r1 import load


def main():
    started = time.perf_counter()
    reg_path = ROOT / 'manifests/wc_current_birth_real_inputs_cpu_r1_preregistration_20261010.json'
    reg = json.loads(reg_path.read_text())
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    budget = ROOT / 'reports/budget.json'
    before = sha(budget)
    for name, value in reg['source_sha256'].items():
        if sha(ROOT / name) != value:
            raise ValueError('Registered complete real input source changed: ' + name)
    calibration, specs, references, parent, evidence = load(ROOT)
    assert tuple(specs) == tuple(reg['strategies'])
    assert all(tuple(value) == tuple(reg['methods']) for value in specs.values())
    assert [r['sample_name'] for r in references] == reg['sample_names']
    assert evidence['complete_cost_rows'] == 48 and evidence['timed_values'] == 144
    assert evidence['reference_project_input_sha256'] == parent['project_input_sha256']
    assert evidence['actual_threshold_reconstruction']['threshold'] == .070744235098772
    assert evidence['current_P_birth_rule'] == reg['current_P_birth_rule']
    assert 'torch' not in sys.modules and before == sha(budget)
    value = {'status': 'COMPLETE_REAL_INPUTS_AND_NATIVE_METADATA_CPU_BOUND_NOT_VIDEO_EXECUTION',
        'registration_ref': str(reg_path.relative_to(ROOT)), 'registration_sha256': sha(reg_path),
        'source_sha256': reg['source_sha256'], 'evidence': evidence,
        'scope_counts': reg['scope_counts'], 'complete_method_parameter_sets': 16,
        'complete_native_reference_metadata_slots': 4,
        'CPU_wall_seconds': time.perf_counter() - started,
        'Torch_imported': False, 'GPU_submissions': 0,
        'model_or_controller_installed': False, 'budget_written': False,
        'budget_before_sha256': before, 'budget_after_sha256': sha(budget),
        'live_Native_file_hashes_and_new_trajectory_compatibility_pending': True}
    dest = ROOT / 'reports/wc_current_birth_real_inputs_cpu_r1_results_20261010.json'
    if dest.exists():
        raise ValueError('Preserve first metadata binding; register revisions separately')
    dest.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: value[k] for k in ('status', 'CPU_wall_seconds', 'GPU_submissions')}))


if __name__ == '__main__':
    main()
