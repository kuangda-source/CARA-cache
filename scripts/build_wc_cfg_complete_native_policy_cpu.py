#!/usr/bin/env python3
"""Freeze the complete H-T62 scope and unchanged previous CPU controls."""
import hashlib
import json
from pathlib import Path
import time


def main():
    sha=lambda name:hashlib.sha256(Path(name).read_bytes()).hexdigest()
    previous=Path('manifests/wc_cfg_native_policy_tail_boundary_cpu_r2_preregistration_20261009.json')
    old=json.loads(previous.read_text())
    assert {n:sha(n) for n in old['payload_sha256']}==old['payload_sha256']
    payload=dict(old['payload_sha256'])
    extra=[str(previous),
        'plans/WORLD_CACHE_COMPLETE_NATIVE_POLICY_INTERFACE_CPU_20261009.md',
        'src/wcomr/cfg_paired_probe_native_policy.py',
        'tests/check_cfg_complete_native_policy_cpu.py',
        'scripts/build_wc_cfg_complete_native_policy_cpu.py',
        'scripts/check_wc_cfg_complete_native_policy_cpu.py',
        'scripts/deploy_wc_cfg_complete_native_policy_cpu.py',
        'scripts/supervise_wc_cfg_complete_native_policy_cpu.py',
        'scripts/capture_wc_cfg_complete_native_policy_cpu.py',
        'reports/wc_cfg_native_policy_tail_boundary_cpu_r2_terminal_20261009_capture_and_independent_audit.json']
    assert set(extra).isdisjoint(payload)
    payload.update({n:sha(n) for n in extra})
    prior=json.loads(Path(old['prior_complete_CPU_audit_ref']).read_text())
    boundary_ref=extra[-1];boundary=json.loads(Path(boundary_ref).read_text())
    assert prior['exit_code']==boundary['exit_code']==0
    assert boundary['complete_comparisons']==16 and boundary['complete_paths']==32
    result={
        'identity':'H_T62_R1_COMPLETE_NATIVE_POLICY_INTERFACE_CPU',
        'registered_unix':time.time(),
        'plan_ref':'plans/WORLD_CACHE_COMPLETE_NATIVE_POLICY_INTERFACE_CPU_20261009.md',
        'CPU_scope':{
            'flow_configurations':['OFF','ON'],
            'threshold_profiles':{'NATIVE_THRESHOLD':.08,'HIGH_THRESHOLD':1e6},
            'observer_configurations':['OFF','ON'],'strict_repetitions':2,
            'complete_comparisons':16,'complete_paths':32,
            'solver_updates':1152,'net_calls':2304,'direct_guided_tensor_comparisons':576,
            'complete_tail_failure_controls':4,'complete_rows':20,
            'failure_names':['selector_tail35','invalid_action_tail35'],
            'failure_completed_steps':34,'paid_decisions_per_successful_paired_path':28,
            'tail_paid_counters':[68,69],'cycle_horizon':70,
            'old_base_mixed_production_and_source_contracts_unchanged':True,
            'prior_complete_112_and_boundary_16_CPU_rows_retained_and_reused_by_SHA':True,
            'GPU_submissions':0},
        'payload_sha256':dict(sorted(payload.items())),
        'runtime_source_sha256':old['runtime_source_sha256'],
        'prior_complete_CPU_audit_ref':old['prior_complete_CPU_audit_ref'],
        'prior_complete_CPU_audit_sha256':sha(old['prior_complete_CPU_audit_ref']),
        'prior_boundary_CPU_audit_ref':boundary_ref,
        'prior_boundary_CPU_audit_sha256':sha(boundary_ref),
        'new_GPU_card_selected':False,'GPU_submissions':0,'budget_written':False,
        'real_model_or_endpoint_or_latency_claim':False}
    target=Path('manifests/wc_cfg_complete_native_policy_cpu_r1_preregistration_20261009.json')
    assert not target.exists()
    target.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'payload_files':len(payload),'scope':result['CPU_scope'],'manifest':str(target)}))


if __name__=='__main__':main()
