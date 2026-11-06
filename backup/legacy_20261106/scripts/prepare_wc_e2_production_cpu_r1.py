#!/usr/bin/env python3
"""Build the unchanged complete76 production CPU card; no GPU selection."""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root=Path(__file__).resolve().parents[1]
    config=root/'configs/wc_e2_production_r1_20261011.json'
    registration=root/'manifests/wc_e2_production_cpu_r1_preregistration_20261011.json'
    assert not config.exists() and not registration.exists()
    proof_ref='reports/wc_e2_confirmation_timing_cpu_r3_terminal_20261011_capture.json'
    proof=json.loads((root/proof_ref).read_text())
    assert proof['exit_code']==0 and proof['original_source_and_raw_identity_verified'] and proof['GPU_submissions']==0
    assert proof['independent_tensor_reload']=={'guided_tensors':3168,'final_latents':152,
        'old_A_direct_parity_paths':8,'CUDA_initialized':False}
    for name,v in proof['files'].items():
        p=root/v['local_path'];packed=p.read_bytes();raw=gzip.decompress(packed)
        assert len(raw)==v['bytes'] and hashlib.sha256(raw).hexdigest()==v['sha256']
        assert hashlib.sha256(packed).hexdigest()==v['packed_sha256']
    old_reg=json.loads(gzip.decompress((root/proof['files']['registration.json']['local_path']).read_bytes()))
    base_ref='reports/wc_ra_plus_a_production_cpu_r1_terminal_20261010_ra-plus-a-config.json.native.gz'
    base=json.loads(gzip.decompress((root/base_ref).read_bytes()))
    runtime=dict(base['runtime_source_sha256'])
    for n,h in old_reg['runtime_source_sha256'].items():
        assert n not in runtime or runtime[n]==h
        runtime[n]=h
    inputs_ref='manifests/wc_e2_confirmation_full72_inputs_r1_20261011.json'
    inputs=json.loads((root/inputs_ref).read_text())
    timing_names=list(dict.fromkeys(r['CAL_name'] for r in inputs['timing_slots']))
    assert timing_names==['av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632','av_51b45829-502e-4143-9c32-c026bd6ab191']
    rows=inputs['requests']+[next(r for r in base['preregistration']['requests'] if r['name']==n) for n in timing_names]
    assert len(rows)==10 and len({r['name'] for r in rows})==10
    cache=root/'.sync/wc-e2-production-inputs-r1';cache.mkdir(exist_ok=False)
    requests='e2-requests.jsonl'
    (cache/requests).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
    forecast_ref='reports/wc_e2_full76_whole_cost_r1_20261011.json'
    forecast=json.loads((root/forecast_ref).read_text())
    assert forecast['complete_actual_GPU_paths']==76 and forecast['forecast_complete_GPUh']>8
    new_files=['src/wcomr/e2_confirmation_production_r1.py','scripts/run_wc_e2_confirmation_r1.py',
        'src/wcomr/cfg_guided_w1_deployment_production.py',
        'scripts/prepare_wc_e2_production_cpu_r1.py','scripts/deploy_wc_e2_production_cpu_r1.py',
        'scripts/supervise_wc_e2_production_cpu_r1.py',proof_ref,forecast_ref,
        'manifests/wc_current_window_execution_authorization_20261011_8gpuh.json',
        'research/294_WC_E2_COMPLETE_CPU_ACCEPTANCE_AND_PRODUCTION_CPU_SCOPE_20261011.md']
    new_files.extend(v['local_path'] for v in proof['files'].values())
    payload=dict(old_reg['payload_sha256'])
    assert sha(root/'src/wcomr/cfg_guided_w1_deployment_production.py')==base['payload_sha256']['src/wcomr/cfg_guided_w1_deployment_production.py']
    for n in new_files:
        assert n not in payload
        payload[n]=sha(root/n)
    payload[requests]=sha(cache/requests)
    c={'card':'WC-E2-PHASE-A-CONF40-TIMING32-PARITY4-R1-20261011-A',
       'run_id':'wc-e2-phase-a-conf40-timing32-parity4-r1',
       'scope_counts':{'scientific_paths':72,'confirmation_paths':40,'timing_paths':32,'parity_paths':4,
           'complete_actual_GPU_paths':76,'solver_updates':2736,'CFG_calls':5472},
       'historical_wc_settings':base['historical_wc_settings'],
       'sampling_protocol':base['sampling_protocol'],'expected_real_shape':base['expected_real_shape'],
       'RA_calibration_fingerprint':'9ab1d77c303560823ed2f32f43b2982318cdd9835828a46da4835a1b95ea7d7a',
       'RA_threshold':0.070744235098772,'branch_order':['conditional','negative_prompt'],'guided_weights':[8,-7],
       'A_phase_boundary':25,'A_phase_strength':[1.,.5], 'original_A_extra_heads_elided':False,
       'teacher_calls':0,'training':False,'boundary_or_alpha_sweep':False,
       'clean_latency_claim':False,'confirmation_accepted':False,
       'inputs_ref':inputs_ref,'inputs_sha256':sha(root/inputs_ref),
       'forecast_ref':forecast_ref,'forecast_sha256':sha(root/forecast_ref),
       'forecast_complete_GPUh':forecast['forecast_complete_GPUh'],
       'base_dependency_stage':'.sync/wc-ra-plus-a-production-cpu-r1-20261010',
       'base_dependency_config_sha256':'a7c3fb6c69a072cf49c60e0148be05b22650621cd7c2d639fe0643592e64f126',
       'sampler_CPU_capture_ref':proof_ref,'payload_sha256':payload,'runtime_source_sha256':runtime,
       'automatic_single_job_GPUh':8,'cumulative_cap_GPUh':77.89524658965853,
       'GPU_execution_selected':False,'gpu_uuid':None,'single_job_exception_authority':None,
       'production_cpu_stage':'.sync/wc-e2-production-cpu-r1-20261011','production_cpu_receipt_sha256':None}
    config.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    reg={'identity':'E2_COMPLETE76_ACTUAL_PRODUCTION_CPU_PREREGISTRATION_NOT_GPU',
         'base_revision_before_registration':revision,'config_ref':str(config.relative_to(root)),
         'config_sha256':sha(config),'CPU_scope':'TEN_ACTUAL_REQUESTS_SOURCE_ASSETS_PRIOR_GUARDRAILS_AND_THIRTEEN_CONTRACT_REFUSALS',
         'copy_original_E2_CPU_stage':'.sync/wc-e2-confirmation-timing-cpu-r3-20261011',
         'copy_original_E2_CPU_source':proof['source_revision'],
         'copies_readonly_sha256':old_reg['payload_sha256'],'new_local_files':new_files,
         'generated_requests_file':requests,'generated_requests_cache':str(cache.relative_to(root)),
         'payload_sha256':payload,'complete_actual_GPU_paths':76,
         'forecast_complete_GPUh':c['forecast_complete_GPUh'],'GPU_execution_selected':False,
         'GPU_submissions':0,'ledger_written':False,'no_human_review':True}
    registration.write_text(json.dumps(reg,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':reg['identity'],'payload_files':len(payload),'requests':len(rows),
        'forecast_GPUh':c['forecast_complete_GPUh'],'config_sha256':sha(config),'GPU_submissions':0}))


if __name__=='__main__':main()
