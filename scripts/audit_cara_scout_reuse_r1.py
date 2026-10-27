"""Audit saved, settled B1 evidence for the original E1 readouts. No dispatch.

This does not fit IG coefficients, reopen IG, or retrospectively complete the
E1 cost/tolerance contract. Missing or unsupported states fail closed.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess
import time

from analyze_cara_ig_b1_complete_r1 import analyze, integrate_saved

ROOT = Path(__file__).resolve().parents[1]
PLAN = 'plans/cara_predictor_refresh_scout_v2_20261026/'
LABELS = ('WC_C', 'A_PHASE', 'FULL', 'R4_GLOBAL', 'R4_LONG', 'DCTA')
BASELINES = ('WC_C', 'A_PHASE', 'FULL', 'DCTA')
INPUTS = dict(
    capture='reports/cara_IG_B1_R2_terminal_20261027.json',
    settlement='reports/cara_IG_B1_R2_central_settlement_20261027.json',
    prior='reports/cara_IG_B1_engineering_central_settlement_20261027.json',
    saved='reports/cara_IG_B1_saved_CPU_finished_20261027.json',
    metadata=PLAN+'E1_STATE_METADATA_V22.json',
    registry=PLAN+'SCOUT_REGISTRY_PATCH_V22.yaml',
    dual_cpu='reports/cara_IG_grouped_dual_host_CPU_acceptance_20261027.json')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def summarize(rows, prompts, metadata):
    expected = {(p, s['step']) for p in prompts for s in metadata}
    assert len(rows) == len(expected) == 12
    assert {(r['prompt'], r['step']) for r in rows} == expected
    for row in rows:
        assert row['P1_dense_head_RF_exact'] and row['P2_C_paid_parent_exact']
        for label in LABELS:
            v = row['original_readout_summary'][label]
            assert v['status'] == 'SUPPORTED' and math.isfinite(v['MSE']) and v['MSE'] >= 0
    reports = {}
    for group in ('all', 'short', 'long'):
        steps = {m['step'] for m in metadata if group == 'all' or m['stratum'] == group}
        selected = [r for r in rows if r['step'] in steps]
        by_prompt = {p: {l: statistics.mean(r['original_readout_summary'][l]['MSE']
            for r in selected if r['prompt'] == p) for l in LABELS} for p in prompts}
        q = {l: statistics.mean(by_prompt[p][l] for p in prompts) for l in LABELS}
        best = min(BASELINES, key=lambda l: (q[l], BASELINES.index(l)))
        candidates = {}
        for label in ('R4_GLOBAL', 'R4_LONG'):
            deltas = [r['original_readout_summary'][label]['MSE'] -
                      r['original_readout_summary'][best]['MSE'] for r in selected]
            candidates[label] = dict(q=q[label], gain_vs_best_fixed=1-q[label]/q[best] if q[best] else None,
                strictly_better_states=sum(d < 0 for d in deltas),
                worst_MSE_increase=max(deltas),
                per_prompt_delta={p: by_prompt[p][label]-by_prompt[p][best] for p in prompts},
                per_state_delta=[dict(prompt=r['prompt'], step=r['step'], delta=d)
                                 for r, d in zip(selected, deltas)])
        reports[group] = dict(states=len(selected), q=q, by_prompt=by_prompt,
                             best_fixed_baseline=best, candidates=candidates)
    short = [r for r in rows if r['step'] in (22, 23, 25)]
    # Summary equality is not a new tensor-equality claim; the source-bound CPU
    # tests and original parent controls carry that separate evidence.
    reports['short_A_fallback_summary_exact'] = all(
        r['original_readout_summary']['R4_LONG'] == r['original_readout_summary']['A_PHASE'] for r in short)
    return reports


def audit():
    values = {k: json.loads((ROOT / p).read_text()) for k, p in INPUTS.items() if k != 'registry'}
    cap, saved, metadata = (values[k] for k in ('capture', 'saved', 'metadata'))
    original = analyze(cap, values['settlement'], values['prior'])
    integrate_saved(original, cap, saved)  # original terminal, finance and saved-result binding
    result = cap['files']['B1-results.json']['value']
    assert result['calibration']['expected_prompts'] == metadata['prompt_ids']
    assert result['calibration']['expected_steps'] == metadata['provisional_steps']
    assert saved['result']['GPU_submissions'] == 0 and not saved['result']['real_model_rerun']
    revision = original['source_revision']
    scientific_files = ['src/wcomr/scout_readout_v22.py', 'src/wcomr/scout_parent_v22.py',
                        'src/wcomr/innovation_gain_grouped_r2.py', 'src/wcomr/innovation_gain_assets_r1.py']
    hashes = {}
    for name in scientific_files:
        blob = subprocess.check_output(['git', 'show', revision+':'+name], cwd=ROOT)
        hashes[name] = hashlib.sha256(blob).hexdigest()
        assert hashes[name] == sha(ROOT/name), 'Scientific source changed: '+name
    host_refs = values['dual_cpu']['host_refs']
    assert set(host_refs) == {'four_card', 'two_card'}
    for host, name in host_refs.items():
        c = json.loads((ROOT/name).read_text())
        assert c['all_payload_hashes_equal'] and c['runtime_hashes_equal']
        assert c['container_state']['ExitCode'] == 0 and not c['device_requests']
        assert c['launch']['source_revision'] == revision
        assert all(c['proof']['source_sha256'][n] == h for n, h in hashes.items())
    reports = summarize(saved['result']['rows'], metadata['prompt_ids'], metadata['rows_per_prompt'])
    # Necessary directional conditions only. An unfilled cost gate cannot turn
    # an error increase into a qualifying improvement; no thresholds are fitted.
    negative = all(reports[g]['candidates'][c]['gain_vs_best_fixed'] < 0
                   for g, c in [('all', 'R4_GLOBAL'), ('long', 'R4_LONG')])
    evidence = dict(INPUTS, **{host+'_cpu': p for host, p in host_refs.items()})
    return dict(status='E1_ORIGINAL_READOUT_RECEIPTS_REUSED_NO_NEW_COLLECTION',
        observed_unix=time.time(), source_revision=revision, original_launch_id=original['launch_id'],
        evidence={k:dict(path=p,sha256=sha(ROOT/p)) for k,p in evidence.items()},
        scientific_source_sha256=hashes, parent_policy_fingerprint=metadata['parent_policy_fingerprint'],
        state_steps=metadata['provisional_steps'], strata=reports,
        coverage=dict(prompts=2, states=12, readout_positions=72, original_OFF_ON_controls=2,
            dual_host_CPU_source_matches=True, real_model_host='two_card',
            current_remote_files_rehashed=False, saved_CPU_original_manifest_sha256=saved['result']['assets_manifest_sha256'],
            full_solver_RNG_checkpoint_available=False, new_state_replay_claim=False),
        recommendation='DO_NOT_DISPATCH_CURRENT_R4_E2' if negative else 'REVIEW_INCOMPLETE_E1_CONTRACT_NO_AUTO_PROMOTION',
        missing_acceptance=['original E1 numeric/cost/peak-memory gates were not fully frozen',
            'per-readout deployment cost and actual peak memory are not established by grouped collection bill',
            'new CPU decomposition needs retained branch tensors and fresh read-only hash verification'],
        full_E1_acceptance=False, retrospective_preregistration=False, j1=None,
        IG_reopened=False, fitting_performed=False, DEV128_used=False,
        new_GPU_submissions=0, new_GPUh=0, ledger_writes=0, server_actions=0)


def self_test():
    m=json.loads((ROOT/INPUTS['metadata']).read_text())
    rows=json.loads((ROOT/INPUTS['saved']).read_text())['result']['rows']
    summarize(rows,m['prompt_ids'],m['rows_per_prompt'])
    faults=[]
    def reject(name, bad):
        try: summarize(bad,m['prompt_ids'],m['rows_per_prompt'])
        except AssertionError: faults.append(name)
        else: raise AssertionError('Accepted '+name)
    reject('missing_state',rows[:-1])
    reject('duplicate_state',rows[:-1]+[rows[0]])
    for name,field,value in [('unsupported','status','UNSUPPORTED'),('nonfinite','MSE',float('nan'))]:
        bad=copy.deepcopy(rows);bad[0]['original_readout_summary']['DCTA'][field]=value;reject(name,bad)
    bad=copy.deepcopy(rows);bad[0]['P2_C_paid_parent_exact']=False;reject('conversion_control',bad)
    return dict(status='CPU_BOUNDARY_PASS',rejected=faults,positive_complete_denominator=True,GPU_submissions=0)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--self-test',action='store_true')
    args=p.parse_args()
    result=self_test() if args.self_test else audit()
    result['auditor_sha256']=sha(Path(__file__))
    with args.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(result['status'])
