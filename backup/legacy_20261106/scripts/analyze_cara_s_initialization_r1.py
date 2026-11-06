"""Read only accepted S artifacts, never the active budget-calibration output."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from wcomr.cara_s_initialization_audit_r1 import audit
from wcomr.cara_fast_spec_r1 import profile_from, uniform_mask


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Fresh diagnostic output required')
    refs = ['plans/cara_next_stage_20261028/sq/S_COMMON_RISK_PROPOSALS_R1_20261030.json',
            'reports/cara_sq_s_A6000_post_analysis_accepted_r1_20261030.json',
            'reports/cara_sq_s_A6000_complete_frozen_risk_result_r1_20261030.json',
            'plans/cara_next_stage_20261028/mainline/RUN_MANIFEST.json']
    raw = {p: (ROOT / p).read_bytes() for p in refs}
    digests = {p: hashlib.sha256(v).hexdigest() for p, v in raw.items()}
    proposal, accepted, result, manifest = (json.loads(raw[p]) for p in refs)
    assert proposal['independent_acceptance_sha256'] == digests[refs[1]]
    assert proposal['source_result_sha256'] == accepted['evidence']['result']['sha256'] == digests[refs[2]]
    assert accepted['original_GPU_release_accepted'] and accepted['original_financial_settlement_accepted']
    assert accepted['all_original_GPU_and_CPU_handles_exited'] and accepted['independent_recompute_exact']
    assert accepted['complete_same_state_rows'] == 108 and accepted['CPU_exit_code'] == 0
    assert not accepted['CPU_oom_killed']
    selected = result['risk_and_mask_proposals']
    assert selected['rule_sha256'] == accepted['rule_sha256'] == proposal['rule_sha256']
    baselines = {}
    for name, role in [('F19_C', 'F19_C'), ('Uniform19_C', 'UNIFORM19_C')]:
        policy = selected['policies'][name]
        assert policy == manifest['roles'][role]['policy']
        baselines[name] = [step for step, action in enumerate(policy['actions'], 1) if action == 'D']
    uniform, _ = uniform_mask(manifest['schedule'], profile_from(manifest['profile']), 19)
    assert uniform == baselines['Uniform19_C']
    risk = {name: {int(step): value for step, value in values.items()} for name, values in selected['risk'].items()}
    output = audit(manifest['profile'], baselines, risk, accepted['choices'], accepted['common_candidate_count'])
    sources = ['src/wcomr/cara_s_initialization_audit_r1.py', 'scripts/analyze_cara_s_initialization_r1.py',
               'src/wcomr/cara_fast_spec_r1.py', 'src/wcomr/policy_generator_r1/interval_grammar.py']
    output.update(observed_unix=time.time(), design_ref='plans/cara_next_stage_20261028/02_SQ_Method_and_Experiments.md A2.1',
                  evidence_sha256=digests, source_sha256={p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources},
                  original_S_launch_id=accepted['launch_id'], original_S_rule_sha256=accepted['rule_sha256'],
                  initialization_search_budget='One legal 19D remove/add per objective and initialization; no budget sweep',
                  method_scope='Fixed Shared25-C/F19-C parent risks on two old FIT inputs; no Uniform19 parent recollection',
                  active_budget_run_accessed=False, ledger_written=False, torch_imported='torch' in sys.modules)
    with args.output.open('x') as stream:
        json.dump(output, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(dict(status=output['status'], choices={k:v['choices'] for k,v in output['origins'].items()},
                          additional_histories=len(output['additional_selector_histories'])), ensure_ascii=False))


if __name__ == '__main__':
    main()
