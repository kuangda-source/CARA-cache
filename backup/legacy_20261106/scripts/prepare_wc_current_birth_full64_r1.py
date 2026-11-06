#!/usr/bin/env python3
"""Freeze the complete64 card only after the whole current-target CPU audit."""
import ast
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


def main():
    audit_ref='reports/wc_current_birth_sampling_cpu_r3_terminal_20261010_capture.json'
    if not Path(audit_ref).exists():
        print(json.dumps({'status':'WAIT_COMPLETE_CURRENT_TARGET256_CPU_NO_CARD_WRITTEN','GPU_submissions':0}));return 2
    sys.path.insert(0,'src')
    from wcomr import current_birth_real_production_r1 as production
    from wcomr.current_birth_real_inputs_r1 import PARENT_PROOF
    sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    audit=json.loads(Path(audit_ref).read_text())
    assert audit['exit_code']==0 and audit['independent_source_complete_results_and_actual_artifact_hashes_verified']
    assert audit['independent_tensor_reload']['actual_tensors']==4736
    assert audit['independent_tensor_reload']['independently_replayed_working_policy_decisions']==4032
    cpu_ref='manifests/wc_current_birth_sampling_cpu_r3_preregistration_20261010.json';cpu=json.loads(Path(cpu_ref).read_text())
    assert {n:sha(n) for n in cpu['payload_sha256']}==cpu['payload_sha256']
    parent_proof=json.loads(Path(PARENT_PROOF).read_text())
    parent=json.loads(gzip.decompress(Path(parent_proof['files']['config']['local_path']).read_bytes()))
    meta_ref='reports/wc_current_birth_real_inputs_cpu_r3_terminal_20261010_capture.json'
    meta_proof=json.loads(Path(meta_ref).read_text());assert meta_proof['CPU_result_accepted']
    meta_item=meta_proof['files']['reports/wc_current_birth_real_inputs_cpu_r3_results_20261010.json']
    meta=json.loads(gzip.decompress(Path(meta_item['local_path']).read_bytes()))
    cost_ref='reports/wc_current_birth_full64_whole_cost_20261010.json';cost=json.loads(Path(cost_ref).read_text())
    for name,value in cost['source_sha256'].items():assert sha(name)==value
    pairing_ref='reports/wc_native_compatibility_cpu_r1_results_20261010.json'
    pairing=json.loads(Path(pairing_ref).read_text());assert pairing['actual_accepted_video_metadata_pairs']==28
    for name,value in pairing['source_sha256'].items():assert sha(name)==value
    r={'card':production.CARD,'run_id':production.RUN,'registered_unix':time.time(),
        'scope_counts':production.COUNTS,'requests':parent['preregistration']['requests'],
        'strategies':list(production.STRATEGIES),'methods':list(production.METHODS),'repetitions':['first'],
        'branch_order':['conditional','negative_prompt'],'guided_weights':[8,-7],'state_steps':[12,30,35,36],
        'timesteps':parent['sampling_protocol']['timesteps'],'current_P_birth_rule':production.CURRENT_BIRTH_RULE,
        'fixed_P_steps':[],'P_mode':'ROTATION_050','P_layers':[4,10,16,22],'P_block_size':128,'P_ratio':.5,
        'shared_A_phase_boundary':25,'shared_A_strength':[1.,.5],'maximum_consecutive_P':2,
        'borrowed_D_drift_ratio':1.,'P_future_drift_empirically_calibrated':False,
        'RA_calibration_fingerprint':production.FINGERPRINT,'RA_threshold':production.THRESHOLD,
        'reference_policy':'REUSE_FOUR_ACCEPTED_NATIVE_ONLY_IF_EXACT_INPUT_SOLVER_AND_PROTECTED_PREFIX_MATCH',
        'teacher_calls':0,'training':False,'boundary_or_alpha_sweep':False,
        'clean_latency_claim':False,'independent_confirmation_claim':False,'forecast':cost,
        'plan_ref':'research/273_WC_CURRENT_BIRTH_CAPD_FULL64_METHOD_DEVELOPMENT_20261010.md',
        'hypothesis':'Phase guided A and current-birth partial refresh jointly improve closed-loop fidelity and cost under fixed real-input source control; two working-source epoch rules are compared without deleting controls.',
        'identity_selection':'Four exposed CAL seed0; development only; all64 slots and failures retained.'}
    r['plan_sha256']=sha(r['plan_ref'])
    reg_ref='manifests/wc_current_birth_full64_r1_preregistration_20261010.json'
    assert not Path(reg_ref).exists();Path(reg_ref).write_text(json.dumps(r,indent=2,allow_nan=False)+'\n')
    budget_raw=subprocess.check_output(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen',
        'cat /home/gaokuangda/data/gkd/worldcache_omr/reports/budget.json'],timeout=40)
    budget=json.loads(budget_raw);assert budget['cap_gpu_hours']==77.89524658965853 and budget['automatic_single_job_gpu_hours']==4
    generated={'profile-config.json':Path('.sync/ra-comparison-inputs-r2/profile-config.json').read_bytes(),
        production.REQUESTS:(''.join(json.dumps(row)+'\n' for row in r['requests'])).encode(),
        'budget-at-preparation.json':budget_raw}
    files=set(cpu['payload_sha256'])|set(parent['payload_sha256'])|set(meta['source_sha256'])
    files.difference_update({'profile-config.json','ra-plus-a-requests.jsonl','budget-at-preparation.json'})
    files.update([cpu_ref,audit_ref,reg_ref,meta_ref,meta_item['local_path'],cost_ref,pairing_ref,r['plan_ref'],
        'src/wcomr/current_birth_real_production_r1.py','src/wcomr/native_video_compatibility_r1.py',
        'scripts/run_wc_current_birth_full64_r1.py','scripts/prepare_wc_current_birth_full64_r1.py',
        'scripts/audit_wc_current_birth_full64_r1.py',
        'scripts/deploy_wc_current_birth_full64_production_cpu_r1.py',
        'scripts/capture_wc_current_birth_full64_production_cpu_r1.py',
        'scripts/supervise_wc_current_birth_full64_r1.py',
        'scripts/supervise_wc_current_birth_full64_post_cpu_r1.py',
        'scripts/select_wc_current_birth_full64_r1_package.py',
        'scripts/forecast_wc_current_birth_full64_r1.py','scripts/check_wc_native_compatibility_cpu_r1.py'])
    files.update(item['local_path'] for item in audit['files'].values())
    for name in files:
        if name.endswith('.py'):ast.parse(Path(name).read_bytes());compile(Path(name).read_bytes(),name,'exec')
    payload={n:sha(n) for n in sorted(files)};payload.update({n:hashlib.sha256(v).hexdigest() for n,v in generated.items()})
    keep=('historical_wc_settings','expected_real_components','expected_real_shape','logical_copy_cap_bytes',
        'workspace_reserve_bytes','paired_prefix_reserve_bytes','cumulative_cap_GPUh','automatic_single_job_GPUh',
        'project_input_sha256','sampling_protocol')
    config={k:parent[k] for k in keep}
    config.update(identity='CURRENT_BIRTH_COMPLETE64_PREPARATION_NOT_SELECTED',execution_run_id=production.RUN,
        preregistration=r,preregistration_ref=reg_ref,preregistration_sha256=sha(reg_ref),payload_sha256=payload,
        runtime_source_sha256={**parent['runtime_source_sha256'],**cpu['runtime_source_sha256']},
        input_binding_fingerprint=meta['evidence']['binding_fingerprint'],GPU_execution_selected=False,gpu_uuid=None,
        single_job_exception_authority=None,production_cpu_receipt_sha256=None,
        production_cpu_stage='.sync/wc-current-birth-full64-production-cpu-r1-20261010',
        batch_cpu_registration_ref=cpu_ref,batch_cpu_audit_ref=audit_ref)
    # Additional CPU-origin checks may name another immutable network class;
    # all common actual parent runtime files must remain byte-identical.
    assert all(parent['runtime_source_sha256'].get(n,h)==h for n,h in cpu['runtime_source_sha256'].items())
    directory=Path('.sync/current-birth-full64-inputs-r1');directory.mkdir(exist_ok=False)
    for name,raw in generated.items():(directory/name).write_bytes(raw)
    target=directory/reg_ref;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(Path(reg_ref).read_bytes())
    production.validate_contract(config,directory)
    dest=Path('configs/wc_current_birth_full64_production_r1_20261010.json');assert not dest.exists()
    dest.write_text(json.dumps(config,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':'FULL64_CARD_PREPARED_NOT_SELECTED_NOT_GPU','scope':production.COUNTS,
        'payload_files':len(payload),'forecast_complete_GPUh':cost['forecast_complete_GPUh'],
        'specific_full_card_confirmation_required':cost['forecast_complete_GPUh']>4,'GPU_submissions':0}));return 0


if __name__=='__main__':raise SystemExit(main())
