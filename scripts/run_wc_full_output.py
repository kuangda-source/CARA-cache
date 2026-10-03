#!/usr/bin/env python3
"""Bounded complete official/dense gate followed by two paired sparse-refresh videos."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import traceback


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['project','stage','runtime','output']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--gpu-uuid');p.add_argument('--validate-only',action='store_true')
    p.add_argument('--cpu-import-check',action='store_true')
    a=p.parse_args()
    spec=importlib.util.spec_from_file_location('historical_asset_gate',a.stage/'scripts/run_wc_s0_profile.py')
    base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
    # Reuse identity validation only, never execute the historical S0 job.
    old,sampling=base.validate(a.project,a.stage,a.runtime)
    c=json.loads((a.stage/'mid-config.json').read_text())
    if a.output.parent.name != c['run_id']:
        raise ValueError('Full-output identity differs from frozen run')
    gate_spec=importlib.util.spec_from_file_location('mid_gate',a.stage/'src/wcomr/full_output_scope.py')
    gate=importlib.util.module_from_spec(gate_spec);gate_spec.loader.exec_module(gate);gate.validate_scope(c)
    for rel,digest in c['upstream_source_sha256'].items():
        if sha(a.runtime/rel)!=digest:raise ValueError('Pinned pipeline/sampler source changed: '+rel)
    if sha(a.project/'configs/cal_w1d8.jsonl') != c['cal_config_sha256'] or sha(a.project/'configs/f1_setup.json') != c['f1_setup_sha256']:
        raise ValueError('Frozen two-scene inputs or model setup changed')
    if sha(a.runtime/'cosmos_predict2/_src/predict2/inference/video2world.py')!=c['request_lifecycle_source_sha256']:
        raise ValueError('Official request reset source changed')
    if sha(a.runtime/'cosmos_predict2/_src/predict2/models/fm_solvers_unipc.py')!=c['unipc_source_sha256']:
        raise ValueError('Pinned UniPC source changed')
    for name,digest in c['payload_sha256'].items():
        if sha(a.stage/name)!=digest:raise ValueError('New payload changed: '+name)
    build=a.project/'.sync/wc-s1-source-build-r1'
    lock=json.loads((build/'build-audit-r2.json').read_text())
    imported=json.loads((build/'import-r2/receipt.json').read_text())
    if imported['package_lock_sha256']!=sha(build/'build-audit-r2.json'):raise ValueError('Package import lock differs')
    for name,item in lock['package_files'].items():
        if sha(build/'build-r1/lib'/name)!=item['sha256']:raise ValueError('Built package changed')
    mode_contract=json.loads((a.stage/'manifests/wc_h0_eval_mode_contract_20261003.json').read_text())
    from_gate=importlib.util.spec_from_file_location("mode_source_gate",a.stage/"src/wcomr/h0_eval_scope.py")
    mode_gate=importlib.util.module_from_spec(from_gate);from_gate.loader.exec_module(mode_gate)
    mode_gate.validate_mode_sources(a.runtime,mode_contract,c)
    if a.validate_only:
        print(json.dumps({'status':'NEW_SCOPE_ASSETS_SOURCE_PACKAGE_PASS_NO_TORCH_OR_CUDA','config_sha256':sha(a.stage/'mid-config.json')}));return
    if a.cpu_import_check:
        sys.argv=[str(a.stage/'scripts/run_wc_s0_profile.py'),'--project',str(a.project),'--stage',str(a.stage),
                  '--runtime',str(a.runtime),'--output',str(a.output),'--cpu-import-check']
        base.main();return
    gate.cost_gate(c)  # Before Torch import, CUDA allocation, or output creation.
    if not a.gpu_uuid or os.environ.get('CUDA_VISIBLE_DEVICES')!=a.gpu_uuid or Path.cwd().resolve()!=a.runtime.resolve():
        raise ValueError('Explicit supervised GPU and runtime required')
    sys.path[:0]=[str(a.stage/'src'),str(a.project/'src'),str(a.runtime),str(a.runtime/'packages/cosmos-oss'),
                  str(a.runtime/'packages/cosmos-cuda'),str(build/'build-r1/lib')]
    a.output.mkdir(parents=True,exist_ok=False)
    os.environ.update(HF_HUB_CACHE=str(a.project/'hfhub'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    state={'run_card':'WC-FULL-OUTPUT-R1-20261003-A','status':'INITIALIZING','pid':os.getpid(),'started_unix':time.time(),'scope':c,'requests':[],
           'planned_total_phases':6,'planned_output_files':6,'quality_evaluation':False,'complete_video':False,'clean_performance_measurement':False}
    def save():
        tmp=a.output/'receipt.tmp';tmp.write_text(json.dumps(state,indent=2)+'\n');tmp.replace(a.output/'receipt.json')
    save()
    try:
        import torch
        from cosmos_oss.init import init_environment,init_output_dir,cleanup_environment
        init_environment();init_output_dir(a.output,profile=False)
        from cosmos_predict2.config import SetupArguments,InferenceArguments
        from cosmos_predict2.inference import Inference
        from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
        from wcomr.runtime_config import install_core_inference_registration
        from wcomr.mid_coverage import tree_digest
        from wcomr.full_output_scope import validate_scope
        from wcomr.full_output import run_full_output
        validate_scope(c)
        if torch.__version__!='2.7.1+cu128' or torch.cuda.get_device_capability()!=(8,6):raise ValueError('Actual Torch/sm86 differs')
        params=json.loads((a.project/'configs/f1_setup.json').read_text())
        if params['disable_guardrails'] or params['use_torch_compile']:raise ValueError('Frozen safety/eager required')
        params.update(keep_going=True,worldcache_enabled=True,output_dir=str(a.output))
        setup=SetupArguments(**params)
        state['registration']=install_core_inference_registration(setup.model,setup.experiment)
        available=InferenceArguments.from_files([a.project/'configs/cal_w1d8.jsonl'])
        samples=[available[i] for i in c['sample_indices']]
        if [sample.name for sample in samples]!=c['sample_names'] or any(sample.num_steps!=35 or sample.seed!=0 for sample in samples):
            raise ValueError('Frozen two CAL identities, steps or seeds differ')
        start=time.perf_counter();inference=Inference(setup);torch.cuda.synchronize()
        state['load_seconds']=time.perf_counter()-start
        model,net=inference.pipe.model,inference.pipe.model.net
        from wcomr.h0_mode import establish_shared_eval,verify_shared_eval
        state['mode_setup']=establish_shared_eval(net,mode_contract['module_types'])
        verify_shared_eval(net,state['mode_setup'])
        save()
        if len(net.blocks)!=28 or model.config.use_torch_compile:raise ValueError('Model structure differs')
        for block in net.blocks:
            attn=block.self_attn
            if (attn.backend,attn.n_heads,attn.head_dim,type(attn.attn_op).__name__)!=('minimal_a2a',16,128,'MinimalA2AAttnOp'):
                raise ValueError('Attention binding differs')
        wc_settings={k:getattr(net,k) for k in ['worldcache_num_steps','worldcache_rel_l1_thresh','worldcache_ret_ratio',
                    'probe_depth','worldcache_motion_sensitivity','worldcache_flow_enabled','worldcache_flow_scale',
                    'worldcache_saliency_enabled','worldcache_saliency_weight','worldcache_osi_enabled','worldcache_dynamic_decay']}
        state['wc_settings']=wc_settings
        if wc_settings['worldcache_num_steps']!=params['worldcache_num_steps'] or wc_settings['probe_depth']!=params['worldcache_probe_depth']:
            raise ValueError('WC constructor differs from frozen setup')
        contexts=[(c['run_id'] + ':' + sample.name, 'Cosmos-Predict2.5-2B:'+sha(a.project/'configs/f1_setup.json'),
                   tree_digest(sample.model_dump(mode='json'))) for sample in samples]
        state['reference_contexts']=[list(context) for context in contexts]
        run_full_output(inference,samples,wc,wc_settings,c,state=state,save=save,
                       output=a.output,contexts=contexts,mode_setup=state['mode_setup'],
                       inference_module=sys.modules['cosmos_predict2.inference'])
        state['status']='COMPLETE_SIX_OUTPUTS_DD_AND_TWO_WC_S_PAIRS_REQUIRES_AUDIT';state['complete_video']=True
        cleanup_environment()
    except BaseException as exc:
        state.update(status='TECH_BLOCKED',error_type=type(exc).__name__,error=str(exc));traceback.print_exc();raise
    finally:
        state['ended_unix']=time.time();state['process_wall_seconds']=state['ended_unix']-state['started_unix'];save()


if __name__=='__main__':main()
