"""Bounded same-seed official-WC shadow off/on gate. Not a quality benchmark."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback
import types

p=argparse.ArgumentParser()
p.add_argument('--project',type=Path,required=True)
p.add_argument('--gpu-uuid',required=True)
p.add_argument('--receipt',type=Path,required=True)
p.add_argument('--same-state',action='store_true',help='Score official/shrink/scalar on the official trajectory')
a=p.parse_args();project=a.project.resolve();root=a.receipt.parent
os.environ.update(CUDA_VISIBLE_DEVICES=a.gpu_uuid,HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
sys.path.insert(0,str(project/'src'))
state={'stage':'W1_SAME_STATE_PARITY' if a.same_state else 'W1_SHADOW_PARITY','status':'INITIALIZING','pid':os.getpid(),'started_unix':time.time(),'runs':[]}
def save():
    root.mkdir(parents=True,exist_ok=True)
    temp=a.receipt.with_suffix('.tmp');temp.write_text(json.dumps(state,indent=2)+'\n');temp.replace(a.receipt)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
save()
try:
    import torch
    from cosmos_oss.init import init_environment,init_output_dir,cleanup_environment
    from cosmos_predict2.config import SetupArguments,InferenceArguments
    from cosmos_predict2.inference import Inference
    from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
    from wcomr.runtime_config import install_core_inference_registration
    from wcomr.shadow_forward import ShadowProbe,build_shadow_forward
    from wcomr.same_state import SameStateProbe,build_same_state_forward
    from wcomr.measurement import BlockCounts
    from wcomr.protocol import validate_schedule
    protocol_path=project/('manifests/w1_same_state_protocol.json' if a.same_state else 'manifests/w1_parity_protocol.json')
    config=json.loads(protocol_path.read_text())
    state['source_sha256']={str(path.relative_to(project)):sha(path) for path in
        [protocol_path,project/'scripts/check_w1_parity.py',project/'src/wcomr/same_state.py',
         project/'src/wcomr/calibration.py',project/'src/wcomr/shadow_metrics.py']}
    upstream=json.loads((project/'manifests/upstream.json').read_text())
    assert sha(wc.__file__)==upstream['cache_module_sha256'],'Cache source drift'
    completion=json.loads((project/'manifests/runtime_completion.json').read_text())
    for path,digest in completion['files'].items():assert sha(Path.cwd()/path)==digest,path
    sampling=json.loads((project/'manifests/f1_runtime_protocol.json').read_text())
    assert sha(Path.cwd()/'cosmos_predict2/_src/predict2/models/fm_solvers_unipc.py')==sampling['scheduler_source_sha256']
    init_environment();init_output_dir(root,profile=False)
    params=json.loads((project/'configs/f1_setup.json').read_text())
    assert not params['disable_guardrails'] and not params['use_torch_compile']
    params.update(output_dir=str(root),worldcache_enabled=True,keep_going=False)
    setup=SetupArguments(**params)
    install_core_inference_registration(setup.model,setup.experiment)
    sample=next(s for s in InferenceArguments.from_files([project/'configs/smoke.jsonl']) if s.name==config['sample'])
    state.update(protocol=config,setup=json.loads(setup.model_dump_json()),sample=json.loads(sample.model_dump_json()),
                 cache_source_sha256=sha(wc.__file__),sampling_protocol=sampling)
    save();inference=Inference(setup);net=inference.pipe.model.net;net.eval()
    original=net.forward
    probe=(SameStateProbe(config['shadow_calls'],config['calibration_defaults']) if a.same_state
           else ShadowProbe(config['shadow_calls']))
    counts=BlockCounts(net.blocks,cache_model=net)
    traces=[]
    cache_fields=['cnt','worldcache_step_skipped_count','accumulated_rel_l1_distance','residual_cache',
                  'probe_residual_cache','residual_window','probe_residual_window','previous_internal_states',
                  'previous_input','previous_output','resume_flag']
    def digest(value):
        h=hashlib.sha256()
        def visit(x):
            if isinstance(x,torch.Tensor):
                h.update(str((tuple(x.shape),str(x.dtype))).encode())
                h.update(x.detach().contiguous().reshape(-1).view(torch.uint8).cpu().numpy().tobytes())
            elif isinstance(x,(list,tuple)):
                h.update(str(type(x)).encode())
                for item in x:visit(item)
            else:h.update(repr(x).encode())
        visit(value);return h.hexdigest()
    def record(module,inputs,output):traces.append(digest(output))
    handle=net.register_forward_hook(record)
    try:
        for mode in ['off','on']:
            probe.begin_request(sample.name+'/'+mode)
            instrumented=(build_same_state_forward(wc.worldcache_mini_train_dit_forward,probe) if a.same_state
                          else build_shadow_forward(wc.worldcache_mini_train_dit_forward,'official',probe))
            net.forward=original if mode=='off' else types.MethodType(instrumented,net)
            counts.reset();traces.clear();state.update(status='GENERATING',current_mode=mode);save()
            destination=root/mode;destination.mkdir(exist_ok=False)
            torch.cuda.synchronize();started=time.perf_counter()
            paths=inference.generate([sample],output_dir=destination)
            torch.cuda.synchronize()
            assert len(paths)==1 and Path(paths[0]).is_file(),'Expected accepted output for parity'
            scheduler=inference.pipe.model.sample_scheduler
            observed={'scheduler_class':type(scheduler).__name__,'requested_steps':sample.num_steps,
                      'actual_schedule_steps':len(scheduler.timesteps),'timesteps':scheduler.timesteps.detach().cpu().tolist(),
                      'use_kerras_sigma':inference.pipe.model.config.use_kerras_sigma_at_inference,
                      'worldcache_horizon':net.worldcache_num_steps}
            run={'mode':mode,'seconds_with_diagnostic_hashing':time.perf_counter()-started,
                 'forward_output_sha256':list(traces),'block_counts':counts.result(),'trace':list(counts.trace),
                 'cache_end_sha256':digest([getattr(net,k) for k in cache_fields]),
                 'video_sha256':sha(paths[0]),'video_path':str(paths[0]),'sampling':observed,
                 'shadow_records':list(probe.records),'peak_allocated_since_upstream_reset':torch.cuda.max_memory_allocated(),
                 'peak_reserved_since_upstream_reset':torch.cuda.max_memory_reserved()}
            state['runs'].append(run);save()
            validate_schedule(observed,counts.result(),sampling,'worldcache')
            assert len(traces)==72,'Expected all net outputs captured'
        off,on=state['runs']
        checks={k:off[k]==on[k] for k in ['forward_output_sha256','block_counts','trace','cache_end_sha256','video_sha256']}
        checks['selected_calls_observed']=[r['call'] for r in on['shadow_records']]==config['shadow_calls']
        if a.same_state:
            checks['finite_metrics']=all(r['candidates'][candidate][kind]['status']=='OK'
                for r in on['shadow_records'] for candidate in ['official','scalar','shrink']
                for kind in ['prewarp_residual','postwarp_residual','velocity'])
            checks['past_anchors_only']=all(all(step<r['cache_counter'] for step in r['candidates'][candidate]['history']['anchor_steps'])
                for r in on['shadow_records'] for candidate in ['scalar','shrink'])
        else:
            checks['finite_metrics']=all(r['metrics'][kind]['status']=='OK' for r in on['shadow_records'] for kind in ['residual','velocity'])
        state['checks']=checks;save()
        assert all(checks.values()),'Shadow parity gate failed'
        state['status']='SAME_STATE_CANDIDATE_DIAGNOSTIC_PARITY_PASS_SINGLE_SAMPLE' if a.same_state else 'OFFICIAL_SHADOW_PARITY_PASS_SINGLE_SAMPLE'
        state['limitation']='One engineering sample on official trajectory; candidate scores are mechanism evidence only. Not candidate closed-loop efficacy, independent CAL, quality or deployment speed measurement.' if a.same_state else 'Official path only; not candidate efficacy, quality review, independent CAL, or deployment speed measurement.'
    finally:
        net.forward=original;handle.remove();counts.close()
    cleanup_environment()
except BaseException as exc:
    state.update(status='FAILED',error_type=type(exc).__name__,error=str(exc));traceback.print_exc();raise
finally:
    state['ended_unix']=time.time();state['process_wall_seconds']=state['ended_unix']-state['started_unix'];save()
