#!/usr/bin/env python3
"""Run only local CPU phase controls; no SSH, CUDA, weights or budget writes."""
import argparse, gzip, json, os, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault('OMP_NUM_THREADS', '2')
os.environ.setdefault('OPENBLAS_NUM_THREADS', '2')
sys.path.insert(0, str(ROOT/'src'))
from wcomr.w3_grouped_action_eval_r1 import accept_dataset, sha
from wcomr.w3_phase_vs_state_cpu_r1 import evaluate_phase_controls

def main():
    p = argparse.ArgumentParser(); p.add_argument('--output', type=Path, required=True); a = p.parse_args()
    assert not a.output.exists()
    previous_ref = 'reports/wc_w3_grouped_T0_T1_T2_primary_and_raw_sensitivity_accepted_r2_20261016.json'
    previous = json.loads((ROOT/previous_ref).read_text())
    start = time.perf_counter()
    for k in ('original', 'repair'):
        assert sha(ROOT/previous[k+'_capture_ref']) == previous[k+'_capture_sha256']
    original = json.loads(gzip.decompress((ROOT/previous['original_capture_ref']).read_bytes()))
    repair = json.loads(gzip.decompress((ROOT/previous['repair_capture_ref']).read_bytes()))
    data, acceptance = accept_dataset(ROOT, original, repair)
    result = dict(status='W3_PHASE_VS_STATE_CPU_COMPLETE_NOT_VIDEO_VALIDATION',
        prior_ref=previous_ref, prior_sha256=sha(ROOT/previous_ref),
        protocol_ref='plans/WC_W3_T1_PHASE_VS_STATE_AND_NEGATIVE_RISK_CPU_NEXT_20261016.md',
        protocol_sha256=sha(ROOT/'plans/WC_W3_T1_PHASE_VS_STATE_AND_NEGATIVE_RISK_CPU_NEXT_20261016.md'),
        acceptance=acceptance, cohorts=[evaluate_phase_controls(data, c) for c in previous['cohorts']],
        GPU_submissions=0, SSH_queries=0, ledger_written=False,
        CPU_wall_seconds=time.perf_counter()-start,
        code_sha256={p: sha(ROOT/p) for p in ('src/wcomr/w3_phase_vs_state_cpu_r1.py',
            'scripts/evaluate_wc_w3_phase_vs_state_cpu_r1.py')})
    a.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: result[k] for k in ('status', 'CPU_wall_seconds', 'GPU_submissions')}))
    for c in result['cohorts']:
        print(c['cohort'])
        for s in c['models']:
            print(s['model'], s['prompt_equal_mean_regret'], s['regret_change_percent_vs_T0_CAD'], s['actions_disagree_with_T1'])

if __name__ == '__main__': main()
