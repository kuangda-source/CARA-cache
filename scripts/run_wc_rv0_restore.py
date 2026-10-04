#!/usr/bin/env python3
"""Independent two-parent/four-suffix restoration diagnostic; no C/D labels."""
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
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda:f.read(1<<20),b''):h.update(part)
    return h.hexdigest()


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def validate(project,stage,runtime,output):
    c=json.loads((stage/'mid-config.json').read_text())
    gate=load(stage/'src/wcomr/rv0_restore_scope.py','restore_scope_gate')
    gate.validate_scope(c);gate.cost_gate(c)
    if output.parent.name!=c['run_id']:raise ValueError('Restore output identity differs')
    for name,digest in c['payload_sha256'].items():
        if sha(stage/name)!=digest:raise ValueError('Restore payload changed: '+name)
    for name,digest in c['upstream_source_sha256'].items():
        if sha(runtime/name)!=digest:raise ValueError('Official source changed: '+name)
    for name,digest in [('configs/cal_w1d8.jsonl',c['cal_config_sha256']),('configs/f1_setup.json',c['f1_setup_sha256'])]:
        if sha(project/name)!=digest:raise ValueError('CAL or model setup changed: '+name)
    proposal=json.loads((stage/c['cost_admission']['cost_report_ref']).read_text())
    if (proposal['cost']['conditional_estimated_seconds']!=c['cost_admission']['conditional_estimated_seconds']
            or proposal['cost']['proposed_cap_seconds']!=c['timeout_seconds']
            or proposal['cost']['complete_cost_bound_validated'] is not False):
        raise ValueError('Conditional proposal cost binding differs')
    binding=c['cpu_control_binding'];prior=project/binding['server_stage']/'receipt.json'
    if sha(prior)!=binding['receipt_sha256']:raise ValueError('Actual CPU original receipt changed')
    r=json.loads(prior.read_text())
    if (r['status']!='RV0_FROZEN_RESTORE_CPU_CONTROLS_PASS_NOT_REAL_GPU' or r['exit_code']!=0
            or r['controls']['cuda_initialized'] is not False
            or r['original_GPU_budget_unchanged_during_CPU'] is not True
            or r['GPU_submissions']!=0 or r['RV_labels']!=0
            or r['payload_sha256']!=binding['payload_sha256']):
        raise ValueError('Actual CPU restoration source binding incomplete')
    for name,digest in binding['payload_sha256'].items():
        if sha(stage/name)!=digest:raise ValueError('Current production differs from CPU control: '+name)
    for sample,item in c['historical_WC_artifacts'].items():
        path=Path(item['path'])
        if (path.stat().st_size!=item['bytes'] or sha(path)!=item['sha256']
                or item['sha256']!=c['expected_parent_video_sha256'][sample]):
            raise ValueError('Historical complete official WC video bridge changed')
    if set(c['historical_WC_artifacts'])!=set(c['sample_names']):
        raise ValueError('Both historical official videos required')
    mode=json.loads((stage/'manifests/wc_h0_eval_mode_contract_20261003.json').read_text())
    mode_gate=load(stage/'src/wcomr/h0_eval_scope.py','restore_mode_sources')
    mode_gate.validate_mode_sources(runtime,mode,c)
    base=load(stage/'scripts/run_wc_s0_profile.py','historical_assets_only')
    base.validate(project,stage,runtime)  # Identity/asset validation, never the old GPU job.
    return c,mode,base


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['project','stage','runtime','output']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--gpu-uuid');p.add_argument('--validate-only',action='store_true')
    p.add_argument('--cpu-import-check',action='store_true')
    a=p.parse_args();c,mode,base=validate(a.project,a.stage,a.runtime,a.output)
    if a.validate_only:
        print(json.dumps({'status':'RESTORE_SOURCE_ASSET_COST_CPU_BINDING_PASS_NO_TORCH',
                          'config_sha256':sha(a.stage/'mid-config.json')}));return
    if a.cpu_import_check:
        sys.argv=[str(a.stage/'scripts/run_wc_s0_profile.py'),'--project',str(a.project),
                  '--stage',str(a.stage),'--runtime',str(a.runtime),'--output',str(a.output),'--cpu-import-check']
        base.main()
        import torch
        from cosmos_predict2._src.predict2 import conditioner
        from wcomr import rv0_restore,rv0_fork
        classes={name:bool(getattr(conditioner,name).__dataclass_params__.frozen)
                 for name in ['BaseCondition','Text2WorldCondition','GR00TV1Img2VidCondition']}
        if not all(classes.values()) or torch.cuda.is_initialized():raise ValueError('Actual frozen condition/CPU guard differs')
        for module in [rv0_restore,rv0_fork]:
            if not Path(module.__file__).resolve().is_relative_to((a.stage/'src').resolve()):
                raise ValueError('Current restoration import source differs')
        print(json.dumps({'status':'RESTORE_ACTUAL_IMPORT_FROZEN_CLASSES_PASS_NO_CUDA',
                          'classes':classes,'cuda_initialized':False}));return
    if (not c['gpu_execution_selected'] or not a.gpu_uuid
            or os.environ.get('CUDA_VISIBLE_DEVICES')!=a.gpu_uuid
            or a.gpu_uuid!=c['gpu_uuid'] or Path.cwd().resolve()!=a.runtime.resolve()):
        raise ValueError('Selected independently supervised restore GPU required')
    sys.path[:0]=[str(a.stage/'src'),str(a.runtime),str(a.runtime/'packages/cosmos-oss'),str(a.runtime/'packages/cosmos-cuda')]
    a.output.mkdir(parents=True,exist_ok=False)
    os.environ.update(HF_HUB_CACHE=str(a.project/'hfhub'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    state={'run_card':c['card'],'status':'INITIALIZING','pid':os.getpid(),'started_unix':time.time(),
           'scope':c,'gpu_uuid':a.gpu_uuid,'requests':[],'RV_labels':0,'action_interventions':0,
           'planned_parent_phases':2,'planned_suffix_controls':4,'planned_parent_outputs':2,
           'complete_RV0_acceptance':False,'clean_speed_measurement':False,'complete_video':False}
    def save():
        path=a.output/'receipt.tmp';path.write_text(json.dumps(state,indent=2)+'\n');path.replace(a.output/'receipt.json')
    save();cleanup=None
    try:
        import torch
        from cosmos_oss.init import init_environment,init_output_dir,cleanup_environment
        init_environment();init_output_dir(a.output,profile=False);cleanup=cleanup_environment
        from cosmos_predict2.config import SetupArguments,InferenceArguments
        from cosmos_predict2.inference import Inference
        from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
        from wcomr.runtime_config import install_core_inference_registration
        from wcomr.h0_mode import establish_shared_eval,verify_shared_eval
        from wcomr.mid_coverage import tree_digest
        from wcomr.rv0_restore import run_restore_controls,cuda_memory_observation
        if torch.__version__!='2.7.1+cu128' or torch.cuda.get_device_capability()!=(8,6):
            raise ValueError('Actual Torch/sm86 differs')
        params=json.loads((a.project/'configs/f1_setup.json').read_text())
        if params['disable_guardrails'] or params['use_torch_compile']:raise ValueError('Frozen guardrails/eager required')
        params.update(keep_going=True,worldcache_enabled=True,output_dir=str(a.output))
        setup=SetupArguments(**params)
        state['registration']=install_core_inference_registration(setup.model,setup.experiment)
        available=InferenceArguments.from_files([a.project/'configs/cal_w1d8.jsonl'])
        samples=[available[i] for i in c['sample_indices']]
        if [s.name for s in samples]!=c['sample_names'] or any(s.num_steps!=35 or s.seed!=0 for s in samples):
            raise ValueError('Frozen two CAL identities differ')
        start=time.perf_counter();inference=Inference(setup);torch.cuda.synchronize()
        state['load_seconds']=time.perf_counter()-start;state['memory_after_load']=cuda_memory_observation()
        model,net=inference.pipe.model,inference.pipe.model.net
        state['mode_setup']=establish_shared_eval(net,mode['module_types']);verify_shared_eval(net,state['mode_setup'])
        if len(net.blocks)!=28 or model.config.use_torch_compile:raise ValueError('Model structure differs')
        for block in net.blocks:
            attn=block.self_attn
            if (attn.backend,attn.n_heads,attn.head_dim,type(attn.attn_op).__name__)!=('minimal_a2a',16,128,'MinimalA2AAttnOp'):
                raise ValueError('Original dense attention binding differs')
        settings={k:getattr(net,k) for k in ['worldcache_num_steps','worldcache_rel_l1_thresh','worldcache_ret_ratio',
            'probe_depth','worldcache_motion_sensitivity','worldcache_flow_enabled','worldcache_flow_scale',
            'worldcache_saliency_enabled','worldcache_saliency_weight','worldcache_osi_enabled','worldcache_dynamic_decay']}
        if settings['worldcache_num_steps']!=params['worldcache_num_steps'] or settings['probe_depth']!=params['worldcache_probe_depth']:
            raise ValueError('WC constructor differs')
        state['wc_settings']=settings
        contexts=[(c['run_id']+':'+s.name,'Cosmos-Predict2.5-2B:'+c['f1_setup_sha256'],tree_digest(s.model_dump(mode='json'))) for s in samples]
        state['reference_contexts']=[list(v) for v in contexts];save()
        run_restore_controls(inference,samples,wc,settings,state=state,save=save,output=a.output,
            contexts=contexts,mode_setup=state['mode_setup'],
            sampler_source=a.runtime/'cosmos_predict2/_src/predict2/models/text2world_model_rectified_flow.py',config=c)
        state['complete_video']=True;state['memory_after_all_controls']=cuda_memory_observation()
    except BaseException as error:
        state.update(status='TECH_BLOCKED_RESTORE_TWO_PARENT_FOUR_SUFFIX_DENOMINATOR_PRESERVED',
                     error_type=type(error).__name__,error=str(error));traceback.print_exc();raise
    finally:
        if cleanup is not None:
            try:cleanup()
            except Exception as error:state['cleanup_error']=str(error)
        state['ended_unix']=time.time();state['process_wall_seconds']=state['ended_unix']-state['started_unix'];save()


if __name__=='__main__':main()
