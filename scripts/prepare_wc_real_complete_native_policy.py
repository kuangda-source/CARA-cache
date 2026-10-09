#!/usr/bin/env python3
"""Prepare the full16 real card only after complete new actual batch CPU proof."""
import ast
import base64
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import time


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    prior_ref='manifests/wc_cfg_complete_native_policy_sampling_cpu_r2_preregistration_20261009.json'
    prior=json.loads(Path(prior_ref).read_text())
    prefix='reports/wc_cfg_complete_native_policy_sampling_cpu_r2_terminal_20261009_'
    audit_ref=prefix+'capture_and_independent_audit.json';receipt_ref=prefix+'receipt.json.native.gz'
    audit=json.loads(Path(audit_ref).read_text());receipt=json.loads(gzip.decompress(Path(receipt_ref).read_bytes()))
    assert audit['exit_code']==receipt['exit_code']==0 and audit['complete_new_actual_batch_matrix_and_last_writer_failures_verified']
    assert audit['actual_Toy_guided_tensors_reloaded']==1152 and audit['complete_executed_paths_including_last_writer_failures']==64
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
        value=json.loads(gzip.decompress(Path(name).read_bytes()))
        sources.append({'source':name,'compressed_sha256':sha(name),'source_revision':value['source_revision'],
            'complete_original_OFF_path_seconds':value['teacher']['parents'][0]['wall_seconds'],'load_seconds':value['load_seconds']})
    path=max(x['complete_original_OFF_path_seconds'] for x in sources);load=max(x['load_seconds'] for x in sources)
    # Previously instrumented full paths include ordinary model/prepare/decode/
    # guardrail/write. Explicit conservative allowances cover the new five
    # checkpoints, output persistence, observations and cleanup, then 20% margin.
    total=(load+16*(path+180+120)+8*36*1.0+120)*1.2
    forecast={'all_complete_prior_sources':sources,'max_full_original_instrumented_path_seconds':path,
        'max_load_seconds':load,'complete_paths':16,'new_checkpoint_allowance_per_path_seconds':180,
        'guided_output_write_and_sha_allowance_per_path_seconds':120,
        'explicit_observer_allowance_seconds':8*36*1.0,'cleanup_allowance_seconds':120,
        'whole_scope_margin_factor':1.2,'forecast_complete_seconds':total,'forecast_complete_GPUh':total/3600,
        'CPU_only_scoring_not_GPU_charged':True,'estimate_not_execution_deadline_or_promised_speed':True}
    remote="import base64,pathlib;print(base64.b64encode(pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr/reports/budget.json').read_bytes()).decode())"
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -c '+repr(remote)],capture_output=True,text=True,timeout=45)
    if call.returncode:raise RuntimeError(call.stderr[-2000:])
    raw_budget=base64.b64decode(call.stdout.strip(),validate=True);budget=json.loads(raw_budget)
    assert raw_budget==Path('reports/budget.json').read_bytes() and budget['cap_gpu_hours']==50
    assert not any('inflight' in k for k in budget) and budget['used_gpu_hours']+forecast['forecast_complete_GPUh']<=50
    spec=importlib.util.spec_from_file_location('complete_native_contract','src/wcomr/cfg_complete_native_policy_production.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    reg={'card':module.CARD,'run_id':module.RUN,'registered_unix':time.time(),
        'hypothesis':'Full real native-policy interface preserves every guided output, actual adaptive action, complete state and video across execution order/observers/strict repeats.',
        'scope_counts':module.COUNTS,'requests':requests,'orders':['ORIGINAL','PAIRED'],'observers':['OFF','ON'],
        'repetitions':['first','second'],'state_steps':[13,21,33,35,36],
        'selector':'PER_SLOT_PAID_PROBE_NATIVE_CACHE_NO_POLICY_CHANGE',
        'measurement_space':'POST_DENOISE_BEFORE_SOLVER','timesteps':common['sampling_protocol']['timesteps'],
        'identity_selection':'Both already exposed seed3 identities; implementation comparison, not CONF.',
        'new_policy_or_clean_latency_claim':False,'forecast':forecast,
        'batch_CPU_registration_ref':prior_ref,'batch_CPU_registration_sha256':sha(prior_ref),
        'batch_CPU_complete_audit_ref':audit_ref,'batch_CPU_complete_audit_sha256':sha(audit_ref)}
    reg_ref='manifests/wc_real_complete_native_policy_r1_preregistration_20261009.json'
    target=Path(reg_ref);assert not target.exists();target.write_text(json.dumps(reg,indent=2)+'\n')
    profile=Path('.sync/real-paired-interface-inputs-r1/profile-config.json').read_bytes()
    old=json.loads(Path('configs/wc_real_paired_interface_production_r1_20261009.json').read_text())
    assert hashlib.sha256(profile).hexdigest()==old['payload_sha256']['profile-config.json']
    generated={'profile-config.json':profile,'native-policy-requests.jsonl':(''.join(json.dumps(r)+'\n' for r in requests)).encode(),
        'budget-at-preparation.json':raw_budget}
    files=set(prior['payload_sha256'])|{prior_ref,audit_ref,receipt_ref,reg_ref,
        'src/wcomr/cfg_complete_native_policy_production.py','src/wcomr/runtime_config.py',
        'manifests/wc_h0_eval_mode_contract_20261003.json','manifests/wc_execution_autonomy_authorization_20261007.json',
        'manifests/budget_authorization_20261008_wc_50gpuh.json','scripts/run_wc_s0_profile.py'}
    files.update(str(p) for p in Path('scripts').glob('*wc_real_complete_native_policy*.py'))
    files.update(names)
    payload={n:sha(n) for n in sorted(files)}
    payload.update({n:hashlib.sha256(v).hexdigest() for n,v in generated.items()})
    for name in files:
        if name.endswith('.py'):ast.parse(Path(name).read_bytes());compile(Path(name).read_bytes(),name,'exec')
    runtime={**old['runtime_source_sha256'],**prior['runtime_source_sha256']}
    assert all(runtime[n]==v for n,v in old['runtime_source_sha256'].items())
    config={'identity':'REAL_COMPLETE_NATIVE_POLICY_PREPARATION_NOT_SELECTED','execution_run_id':module.RUN,
        'preregistration':reg,'preregistration_ref':reg_ref,'preregistration_sha256':sha(reg_ref),
        'payload_sha256':payload,'project_input_sha256':old['project_input_sha256'],'runtime_source_sha256':runtime,
        'historical_wc_settings':old['historical_wc_settings'],'sampling_protocol':old['sampling_protocol'],
        'expected_real_components':1216,'expected_real_shape':[1,16,24,54,96],
        'logical_copy_cap_bytes':6*(1<<30),'workspace_reserve_bytes':4*(1<<30),'paired_prefix_reserve_bytes':4*(1<<30),
        'cumulative_cap_GPUh':50,'automatic_single_job_GPUh':2,'GPU_execution_selected':False,'gpu_uuid':None,
        'single_job_exception_authority':None,'production_cpu_receipt_sha256':None,
        'production_cpu_stage':'.sync/wc-real-complete-native-policy-production-cpu-r1-20261009',
        'batch_cpu_registration_ref':prior_ref,'batch_cpu_receipt_ref':receipt_ref,'batch_cpu_audit_ref':audit_ref,
        'legacy_profile_validator_role':'READ_ONLY_EXISTING_SOURCE_CHECKPOINT_GUARDRAIL_ASSET_CHECK_NO_OLD_EXECUTION_CAP'}
    inputs=Path('.sync/real-complete-native-policy-inputs-r1');inputs.mkdir(exist_ok=False)
    for name,raw in generated.items():(inputs/name).write_bytes(raw)
    p=inputs/reg_ref;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(target.read_bytes())
    module.validate_contract(config,inputs)
    dest=Path('configs/wc_real_complete_native_policy_production_r1_20261009.json');assert not dest.exists()
    dest.write_text(json.dumps(config,indent=2)+'\n')
    print(json.dumps({'status':'REAL_COMPLETE_NATIVE_POLICY_LOCAL_PREPARATION_NOT_PRODUCTION_CPU','payload_files':len(payload),
        'scope':module.COUNTS,'forecast_complete_GPUh':forecast['forecast_complete_GPUh'],'budget_GPUh':budget['used_gpu_hours'],
        'specific_over_2_GPUh_approval_required':True,'GPU_submissions':0,'GPU_selected':False}))


if __name__=='__main__':main()
