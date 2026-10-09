#!/usr/bin/env python3
"""Preregister the actual new complete batch without rerunning unchanged controls."""
import hashlib
import json
from pathlib import Path
import time


def main():
    sha=lambda name:hashlib.sha256(Path(name).read_bytes()).hexdigest()
    previous=Path('manifests/wc_cfg_complete_native_policy_cpu_r1_preregistration_20261009.json')
    old=json.loads(previous.read_text())
    assert {n:sha(n) for n in old['payload_sha256']}==old['payload_sha256']
    payload=dict(old['payload_sha256'])
    extra=[str(previous),
        'plans/WORLD_CACHE_REAL_COMPLETE_NATIVE_POLICY_INTERFACE_20261009.md',
        'src/wcomr/cfg_complete_native_policy_sampling.py',
        'src/wcomr/rv0_video_reader.py',
        'tests/check_cfg_complete_native_policy_sampling_cpu.py',
        'scripts/build_wc_cfg_complete_native_policy_sampling_cpu.py',
        'scripts/check_wc_cfg_complete_native_policy_sampling_cpu.py',
        'scripts/deploy_wc_cfg_complete_native_policy_sampling_cpu.py',
        'scripts/supervise_wc_cfg_complete_native_policy_sampling_cpu.py',
        'scripts/capture_wc_cfg_complete_native_policy_sampling_cpu.py',
        'reports/wc_cfg_complete_native_policy_cpu_r1_terminal_20261009_capture_and_independent_audit.json']
    assert set(extra).isdisjoint(payload)
    payload.update({n:sha(n) for n in extra})
    result={
        'identity':'H_T63_R1_COMPLETE_NATIVE_POLICY_ACTUAL_BATCH_CPU',
        'registered_unix':time.time(),
        'plan_ref':'plans/WORLD_CACHE_REAL_COMPLETE_NATIVE_POLICY_INTERFACE_20261009.md',
        'CPU_scope':{
            'flow_configurations':['OFF','ON'],
            'threshold':.06,'observer_configurations':['OFF','ON'],'strict_repetitions':2,
            'orders':['ORIGINAL','PAIRED'],'complete_requests_per_batch':2,
            'scenarios':['complete','last_vector_writer_failure'],
            'complete_rows':4,'successful_full_paths':32,
            'executed_full_paths_including_last_writer_failures':64,
            'solver_updates':2304,'net_calls':4608,
            'actual_guided_tensors_reloaded':1152,'actual_final_latents_reloaded':32,
            'last_path_writer_failures':2,'semantic_mutation_refusals':24,
            'actual_truncation_refusals':2,'GPU_submissions':0,
            'prior_complete_CPU_controls_retained_reused_by_SHA':True},
        'payload_sha256':dict(sorted(payload.items())),
        'runtime_source_sha256':old['runtime_source_sha256'],
        'prior_complete_CPU_audit_ref':old['prior_complete_CPU_audit_ref'],
        'prior_boundary_CPU_audit_ref':old['prior_boundary_CPU_audit_ref'],
        'prior_native_policy_CPU_audit_ref':extra[-1],
        'prior_audit_sha256':{n:sha(n) for n in [old['prior_complete_CPU_audit_ref'],old['prior_boundary_CPU_audit_ref'],extra[-1]]},
        'new_GPU_card_selected':False,'GPU_submissions':0,'budget_written':False,
        'real_model_or_endpoint_or_latency_claim':False}
    target=Path('manifests/wc_cfg_complete_native_policy_sampling_cpu_r1_preregistration_20261009.json')
    assert not target.exists();target.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'payload_files':len(payload),'scope':result['CPU_scope'],'manifest':str(target)}))


if __name__=='__main__':main()
