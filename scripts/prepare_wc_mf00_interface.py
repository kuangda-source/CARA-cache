#!/usr/bin/env python3
"""Freeze the entire MF-00 interface card against current spending/4h policy."""
import ast
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import time


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    prior_ref='manifests/wc_mf00_interface_sampling_cpu_r1_preregistration_20261010.json'
    prior=json.loads(Path(prior_ref).read_text())
    prefix='reports/wc_mf00_interface_sampling_cpu_r1_terminal_20261010_'
    audit_ref=prefix+'capture.json';receipt_ref=prefix+'receipt.json.native.gz'
    audit=json.loads(Path(audit_ref).read_text());receipt=json.loads(gzip.decompress(Path(receipt_ref).read_bytes()))
    assert audit['exit_code']==receipt['exit_code']==0
    assert audit['actual_Toy_guided_tensors_reloaded']==288 and audit['complete_executed_paths_including_last_writer_failures']==16
    assert {n:sha(n) for n in prior['payload_sha256']}==prior['payload_sha256']
    common=json.loads(gzip.decompress(Path('reports/wc_other_scene_cfg_confirmation_r1_terminal_20261009_config_native.gz').read_bytes()))
    human=json.loads(gzip.decompress(Path('reports/wc_cfg_mechanism_confirmation_r1_terminal_20261009_config_native.gz').read_bytes()))
    requests=[common['preregistration']['confirmation_request'],human['preregistration']['confirmation_request']]
    names=['reports/wc_cfg_guided_teacher_r1_terminal_20261009_runner_native.gz',
        'reports/wc_cfg_mechanism_confirmation_r1_terminal_20261009_runner_native.gz',
        'reports/wc_other_scene_cfg_confirmation_r1_terminal_20261009_runner_native.gz',
        'reports/wc_real_paired_interface_r1_terminal_20261009_runner_native.gz']
    sources=[]
    for name in names:
        v=json.loads(gzip.decompress(Path(name).read_bytes()))
        sources.append({'source':name,'compressed_sha256':sha(name),'source_revision':v['source_revision'],
            'complete_original_OFF_path_seconds':v['teacher']['parents'][0]['wall_seconds'],'load_seconds':v['load_seconds']})
    path=max(x['complete_original_OFF_path_seconds'] for x in sources)
    load=max(x['load_seconds'] for x in sources)
    total=(load+4*(path+180+120)+120)*1.2
    forecast={'all_complete_prior_sources':sources,'max_full_original_instrumented_path_seconds':path,
        'max_load_seconds':load,'complete_paths':4,'new_checkpoint_allowance_per_path_seconds':180,
        'guided_output_write_and_sha_allowance_per_path_seconds':120,'explicit_observer_allowance_seconds':0,
        'cleanup_allowance_seconds':120,'whole_scope_margin_factor':1.2,
        'forecast_complete_seconds':total,'forecast_complete_GPUh':total/3600,
        'CPU_only_scoring_not_GPU_charged':True,'estimate_not_execution_deadline_or_promised_speed':True}
    assert forecast['forecast_complete_GPUh']<=4
    budget_raw=Path('reports/budget.json').read_bytes();budget=json.loads(budget_raw)
    assert budget['automatic_single_job_gpu_hours']==4 and budget['cap_gpu_hours']==77.89524658965853
    assert not any('inflight' in k for k in budget)
    assert budget['used_gpu_hours']+forecast['forecast_complete_GPUh']<=budget['cap_gpu_hours']
    spec=importlib.util.spec_from_file_location('mf00_contract','src/wcomr/cfg_mf00_interface_production.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    reg={'card':module.CARD,'run_id':module.RUN,'registered_unix':time.time(),
        'hypothesis':'The necessary OFF-only original/paired interface preserves all full36 outputs, actions, states and complete videos on two exposed identities.',
        'scope_counts':module.COUNTS,'requests':requests,'orders':['ORIGINAL','PAIRED'],'observers':['OFF'],
        'repetitions':['first'],'state_steps':[13,21,33,35,36],
        'selector':'PER_SLOT_PAID_PROBE_NATIVE_CACHE_NO_POLICY_CHANGE',
        'measurement_space':'POST_DENOISE_BEFORE_SOLVER','timesteps':common['sampling_protocol']['timesteps'],
        'identity_selection':'Already exposed seed3 identities; implementation control, not independent CONF.',
        'new_policy_or_clean_latency_claim':False,'forecast':forecast,
        'independent_scope_reason':'Current integrated method plan prioritizes necessary interface control before RA/A/B/C; original sixteen-path card retained, no observer/repeat claims.',
        'does_not_accept_old_full16_card':True,
        'batch_CPU_registration_ref':prior_ref,'batch_CPU_registration_sha256':sha(prior_ref),
        'batch_CPU_complete_audit_ref':audit_ref,'batch_CPU_complete_audit_sha256':sha(audit_ref),
        'execution_policy_ref':'manifests/wc_execution_autonomy_authorization_20261010_4gpuh.json',
        'budget_window_authorization_ref':'manifests/budget_authorization_20261009_wc_new_window_48gpuh.json'}
    reg_ref='manifests/wc_mf00_interface_r1_preregistration_20261010.json'
    target=Path(reg_ref);assert not target.exists();target.write_text(json.dumps(reg,indent=2)+'\n')
    profile=Path('.sync/real-paired-interface-inputs-r1/profile-config.json').read_bytes()
    old=json.loads(Path('configs/wc_real_paired_interface_production_r1_20261009.json').read_text())
    assert hashlib.sha256(profile).hexdigest()==old['payload_sha256']['profile-config.json']
    generated={'profile-config.json':profile,'native-policy-requests.jsonl':(''.join(json.dumps(r)+'\n' for r in requests)).encode(),
        'budget-at-preparation.json':budget_raw}
    files=set(prior['payload_sha256'])|{prior_ref,audit_ref,receipt_ref,reg_ref,
        'src/wcomr/cfg_mf00_interface_production.py','src/wcomr/runtime_config.py',
        'manifests/wc_h0_eval_mode_contract_20261003.json','scripts/run_wc_s0_profile.py'}
    files.update(str(p) for p in Path('scripts').glob('*wc_mf00_interface*.py'))
    files.update(names)
    payload={n:sha(n) for n in sorted(files)}
    payload.update({n:hashlib.sha256(v).hexdigest() for n,v in generated.items()})
    for name in files:
        if name.endswith('.py'):ast.parse(Path(name).read_bytes());compile(Path(name).read_bytes(),name,'exec')
    runtime={**old['runtime_source_sha256'],**prior['runtime_source_sha256']}
    config={'identity':'MF00_INTERFACE_PREPARATION_NOT_SELECTED','execution_run_id':module.RUN,
        'preregistration':reg,'preregistration_ref':reg_ref,'preregistration_sha256':sha(reg_ref),
        'payload_sha256':payload,'project_input_sha256':old['project_input_sha256'],'runtime_source_sha256':runtime,
        'historical_wc_settings':old['historical_wc_settings'],'sampling_protocol':old['sampling_protocol'],
        'expected_real_components':1216,'expected_real_shape':[1,16,24,54,96],
        'logical_copy_cap_bytes':6*(1<<30),'workspace_reserve_bytes':4*(1<<30),'paired_prefix_reserve_bytes':4*(1<<30),
        'cumulative_cap_GPUh':budget['cap_gpu_hours'],'automatic_single_job_GPUh':4,
        'GPU_execution_selected':False,'gpu_uuid':None,'single_job_exception_authority':None,
        'production_cpu_receipt_sha256':None,
        'production_cpu_stage':'.sync/wc-mf00-interface-production-cpu-r1-20261010',
        'batch_cpu_registration_ref':prior_ref,'batch_cpu_receipt_ref':receipt_ref,'batch_cpu_audit_ref':audit_ref,
        'legacy_profile_validator_role':'READ_ONLY_SOURCE_CHECKPOINT_GUARDRAIL_ASSET_CHECK_NO_OLD_EXECUTION_CAP'}
    inputs=Path('.sync/mf00-interface-inputs-r1');inputs.mkdir(exist_ok=False)
    for name,raw in generated.items():(inputs/name).write_bytes(raw)
    p=inputs/reg_ref;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(target.read_bytes())
    module.validate_contract(config,inputs)
    dest=Path('configs/wc_mf00_interface_production_r1_20261010.json');assert not dest.exists()
    dest.write_text(json.dumps(config,indent=2)+'\n')
    print(json.dumps({'status':'MF00_INTERFACE_LOCAL_PREPARATION_NOT_PRODUCTION_CPU','payload_files':len(payload),
        'scope':module.COUNTS,'forecast_complete_GPUh':forecast['forecast_complete_GPUh'],
        'GPU_submissions':0,'GPU_selected':False}))


if __name__=='__main__':main()
