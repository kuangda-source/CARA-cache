"""Bind complete CPU acceptance, immutable original requests and whole24 cost."""
import gzip
import hashlib
import json
from pathlib import Path


def main():
    root=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    proof_ref='reports/wc_e5_complete_sampling_cpu_r6_terminal_20261011_capture.json'
    proof=json.loads((root/proof_ref).read_text())
    assert proof['status']=='E5_COMPLETE_SAMPLER_R6_INDEPENDENT_FULL_WRITTEN_EQUIVALENCE_PASS_NOT_GPU'
    assert proof['actual_loaded_tensors']==888 and proof['actual_direct_equalities']==444
    reg_ref='manifests/wc_e5_complete_sampling_cpu_r6_20261011.json'
    cpu=json.loads((root/reg_ref).read_text());copies=dict(cpu['inherited_payload_sha256'],**cpu['new_payload_sha256'])
    original=json.loads(gzip.decompress((root/proof['original_files']['receipt.json']['local_ref']).read_bytes()))
    assert copies==original['payload_after_sha256'] and len(copies)==434
    old=json.loads((root/'configs/wc_e4c_source_age_production_r1_20261011.json').read_text())
    parent_ref='configs/wc_current_birth_full64_selected_r1_20261010.json'
    parent=json.loads((root/parent_ref).read_text())
    cost_ref='manifests/wc_e5_native_wrapped_head_complete24_cost_proposal_r1_20261011.json'
    cost=json.loads((root/cost_ref).read_text())
    # No Torch/runtime import on the client is needed to read literal arms.
    modes=('OFF','W1_ONE_PHASE','BETA1_ONE_PHASE')
    methods=tuple(v+'_'+a for a in modes for v in ('LEGACY','FAST'))
    av='av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632'
    arms=[{'id':tag+'_R'+str(rep),'sample_name':name,'repetition':rep,
        'methods':list(methods if rep==1 else methods[::-1])}
        for rep in (1,2) for tag,name in (('AV',av),('HUMAN','human_199'))]
    names=['src/wcomr/e5_head_complete24_sampling_r1.py','src/wcomr/e5_head_complete24_production_r1.py',
        'scripts/run_wc_e5_head_complete24_r1.py','scripts/check_wc_e5_head_complete24_production_cpu_r1.py',
        'scripts/supervise_wc_e5_head_complete24_r1.py','scripts/prepare_wc_e5_head_complete24_production_r1.py',
        'scripts/deploy_wc_e5_head_complete24_production_cpu_r1.py',
        'scripts/audit_wc_e5_head_complete24_terminal_cpu_r1.py',
        'scripts/supervise_wc_e5_head_complete24_terminal_cpu_r1.py',
        'tests/check_e5_complete24_supervisor_cpu_r1.py',cost_ref,proof_ref,
        'research/347_WC_E5_COMPLETE24_ACTUAL_ENTRY_AND_COST_PREREGISTRATION_20261011.md']
    names += [row['local_ref'] for row in proof['original_files'].values()]
    payload=dict(copies);new=[]
    for n in dict.fromkeys(names):
        h=sha(root/n)
        if n in payload:assert payload[n]==h,n
        else:payload[n]=h;new.append(n)
    requests=[r for r in parent['preregistration']['requests'] if r['name'] in (av,'human_199')]
    requests.sort(key=lambda r:0 if r['name']==av else 1)
    cache=root/'.sync/e5-head-complete24-production-r1-generated';assert not cache.exists();cache.mkdir()
    request_file=cache/'e5-head-requests.jsonl'
    request_file.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in requests))
    payload['e5-head-requests.jsonl']=sha(request_file)
    c={k:old[k] for k in ('parent_stage','parent_config_sha256','parent_import_source_sha256',
        'authorization_ref','authorization_sha256','automatic_single_job_GPUh','cumulative_cap_GPUh',
        'working_epoch_strategy','checkpoint_reserves','model_mode_contract_ref','model_mode_contract_sha256',
        'required_stage_assets','native_meta_CPU_receipt_ref','native_meta_CPU_receipt_raw_sha256')}
    c.update(card=cost['card'],run_id=cost['run_id'],arms=arms,requests=requests,
        scope_counts={'complete_paths':24,'independent_model_loads':4,'solver_updates':864,
            'CFG_calls':1728,'teacher_calls':0,'checkpoint_roundtrips':96,
            'written_tensor_files':24,'written_tensors':888,'old_new_tensor_equalities':444},
        cost_ref=cost_ref,cost_sha256=sha(root/cost_ref),forecast_complete_GPUh=cost['forecast_complete_GPUh'],
        sampling_CPU_capture_ref=proof_ref,sampling_CPU_capture_sha256=sha(root/proof_ref),
        sampling_CPU_stage='.sync/wc-e5-complete-sampling-cpu-r6-20261011',
        continue_after_failure='STOP_RETAIN_COMPLETE_SCOPE',empty_cache_or_gate_bypass=False,
        training=False,human_review=False,clean_latency_or_quality_frontier_claim=False,
        payload_sha256=payload,GPU_execution_selected=False,gpu_uuid=None,production_CPU_receipt_sha256=None)
    target=root/'configs/wc_e5_head_complete24_production_r1_20261011.json';assert not target.exists()
    target.write_text(json.dumps(c,indent=2)+'\n')
    reg={'identity':'E5_COMPLETE24_ACTUAL_ENTRY_CPU_PREREGISTRATION_NOT_GPU',
        'config_ref':str(target.relative_to(root)),'config_sha256':sha(target),
        'original_stage':'.sync/wc-e5-complete-sampling-cpu-r6-20261011',
        'copies_readonly_sha256':copies,'original_receipt_sha256':proof['original_files']['receipt.json']['sha256'],
        'new_local_files':new,'generated_requests_cache':str(request_file.relative_to(root)),
        'forecast_complete_GPUh':c['forecast_complete_GPUh'],'GPU_submissions':0,'ledger_written':False,
        'full_sampler_CPU_and_native_meta_not_rerun':True}
    target=root/'manifests/wc_e5_head_complete24_production_cpu_r1_preregistration_20261011.json'
    assert not target.exists();target.write_text(json.dumps(reg,indent=2)+'\n')
    print(json.dumps({'status':reg['identity'],'payload_files':len(payload),'forecast_GPUh':c['forecast_complete_GPUh']}))


if __name__=='__main__':main()
