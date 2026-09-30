"""CAL-first8 OFF/ON same-state diagnostic; all work under one supervisor."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback

p=argparse.ArgumentParser()
p.add_argument('--project',type=Path,required=True)
p.add_argument('--gpu-uuid',required=True)
p.add_argument('--receipt',type=Path,required=True)
a=p.parse_args()
project=a.project.resolve();root=a.receipt.parent
os.environ.update(CUDA_VISIBLE_DEVICES=a.gpu_uuid,HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
sys.path.insert(0,str(project/'src'))
state={'stage':'W1D_CAL8','status':'INITIALIZING','pid':os.getpid(),'started_unix':time.time(),'cases':[]}
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
    from wcomr.measurement import BlockCounts
    from wcomr.protocol import validate_schedule
    protocol_path=project/'manifests/w1d_cal_protocol.json'
    config=json.loads(protocol_path.read_text())
    state['source_sha256']={str(path.relative_to(project)):sha(path) for path in
        [protocol_path,project/'scripts/run_w1d_cal.py']+[project/('src/wcomr/'+name+'.py') for name in ['w1d','same_state','calibration','shadow_metrics','stage_witness','decoder_policy','guardrail_observation','measurement']]}
    upstream=json.loads((project/'manifests/upstream.json').read_text())
    assert sha(wc.__file__)==upstream['cache_module_sha256'],'Cache source drift'
    completion=json.loads((project/'manifests/runtime_completion.json').read_text())
    for path,digest in completion['files'].items():assert sha(Path.cwd()/path)==digest,path
    sampling=json.loads((project/'manifests/f1_runtime_protocol.json').read_text())
    assert sha(Path.cwd()/'cosmos_predict2/_src/predict2/models/fm_solvers_unipc.py')==sampling['scheduler_source_sha256']
    init_environment();init_output_dir(root,profile=False)
    params=json.loads((project/'configs/f1_setup.json').read_text())
    assert not params['disable_guardrails'] and not params['use_torch_compile']
    params.update(output_dir=str(root),worldcache_enabled=True,keep_going=True)
    setup=SetupArguments(**params)
    install_core_inference_registration(setup.model,setup.experiment)
    input_path=project/'configs/cal_w1d8.jsonl'
    assert sha(input_path)==config['input_sha256']
    assert sha(project/'manifests/cal_v1.json')==config['cal_manifest_sha256']
    samples=InferenceArguments.from_files([input_path])
    assert [s.name for s in samples]==config['samples']
    state.update(protocol=config,setup=json.loads(setup.model_dump_json()),input_sha256=sha(input_path),
                 cache_source_sha256=sha(wc.__file__),sampling_protocol=sampling)
    save();inference=Inference(setup);net=inference.pipe.model.net;net.eval()
    import inspect
    import av
    import types
    from contextlib import contextmanager
    import cosmos_predict2.inference as inference_module
    from wcomr.stage_witness import StageWitness,witness
    from wcomr.decoder_policy import backend_flags,decode_policy,tokenizer_identity,compare_decoder_identity
    from wcomr.guardrail_observation import GuardrailObservation
    from wcomr.same_state import SameStateProbe,build_same_state_forward
    from wcomr.w1d import select_pairs,validate_pair
    model=inference.pipe.model
    layout_path=Path.cwd()/'cosmos_predict2/_src/predict2/networks/minimal_v4_dit.py'
    assert sha(layout_path)==config['layout_source_sha256'],'Layout source drift'
    checkpoint=project/'hfhub/models--nvidia--Cosmos-Predict2.5-2B/snapshots/6787e176dce74a101d922174a95dba29fa5f0c55/tokenizer.pth'
    h=hashlib.sha256()
    with checkpoint.open('rb') as file:
        for chunk in iter(lambda:file.read(8*1024*1024),b''):h.update(chunk)
    assert h.hexdigest()==config['decoder_checkpoint_sha256']==checkpoint.resolve().name
    state.update(decoder_checkpoint_sha256=h.hexdigest(),flags=backend_flags(),
                 tensor_layout={'residual':'B,T,H,W,D','velocity':'B,C,T,H,W',
                                'patch_spatial':net.patch_spatial,'patch_temporal':net.patch_temporal},
                 limitation='Reusable CAL sparse mechanism diagnostic. No candidate deployed, no quality/speed/independent confirmation claim.')
    counts=BlockCounts(net.blocks,cache_model=net)
    stages=StageWitness();guards=GuardrailObservation(inference_module.guardrail_presets)
    def input_record(stage):
        return lambda args,kwargs:stages.record(stage,args[0] if args else next(iter(kwargs.values())))
    stages.wrap(model,'generate_samples_from_batch',after=lambda r:stages.record('sample_return',r))
    decode_calls=[]
    def before_decode(args,kwargs):
        input_record('decode_input')(args,kwargs)
        decode_calls.append({'before':tokenizer_identity(model.tokenizer),'flags_before':backend_flags()})
    def after_decode(result):
        stages.record('decode_output',result)
        call=decode_calls[-1];call['after']=tokenizer_identity(model.tokenizer);call['flags_after']=backend_flags()
        call['unchanged']=compare_decoder_identity(call['before'],call['after'])
        assert all(call['unchanged'].values()) and call['flags_before']==call['flags_after']
        assert call['flags_inside']==dict(call['flags_before'],cudnn_benchmark=False,cudnn_deterministic=True)
    @contextmanager
    def decode_context():
        with decode_policy(True) as active:
            decode_calls[-1]['flags_inside']=active
            yield
    stages.wrap(model,'decode',before=before_decode,after=after_decode,call_context=decode_context)
    stages.wrap(inference_module.guardrail_presets,'run_video_guardrail',before=input_record('guardrail_input'),
                after=lambda r:stages.record('guardrail_output',r))
    stages.wrap(inference_module,'save_img_or_video',before=input_record('save_input'))
    traces=[]
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
    handle=net.register_forward_hook(lambda m,i,o:traces.append(digest(o)))
    original=net.forward
    cache_fields=['cnt','worldcache_step_skipped_count','accumulated_rel_l1_distance','residual_cache',
                  'probe_residual_cache','residual_window','probe_residual_window','previous_internal_states',
                  'previous_input','previous_output','resume_flag']
    def generate(sample,mode,probe):
        counts.reset();traces.clear();guards.reset();stages.events=[];decode_calls.clear()
        if mode=='on' and probe is not None:
            probe.begin_request(sample.name+'/on')
            net.forward=types.MethodType(build_same_state_forward(wc.worldcache_mini_train_dit_forward,probe),net)
        else:net.forward=original
        state.update(status='GENERATING',current_sample=sample.name,current_mode=mode);save()
        flags_before=backend_flags();torch.cuda.synchronize();started=time.perf_counter()
        destination=root/sample.name/mode;destination.mkdir(parents=True,exist_ok=False)
        paths=inference.generate([sample],output_dir=destination)
        torch.cuda.synchronize();outcome=guards.classify(paths)
        observed=None
        if outcome!='TEXT_REJECTED':
            scheduler=model.sample_scheduler
            observed={'scheduler_class':type(scheduler).__name__,'requested_steps':sample.num_steps,
                      'actual_schedule_steps':len(scheduler.timesteps),'timesteps':scheduler.timesteps.detach().cpu().tolist(),
                      'use_kerras_sigma':model.config.use_kerras_sigma_at_inference,'worldcache_horizon':net.worldcache_num_steps}
        result={'mode':mode,'outcome':outcome,'guardrail_events':list(guards.events),
                'seconds_with_hashing_and_diagnostics':time.perf_counter()-started,
                'forward_output_sha256':list(traces),'block_counts':counts.result(),'trace':list(counts.trace),
                'cache_end_sha256':digest([getattr(net,k) for k in cache_fields]),'sampling':observed,
                'pipeline_events':list(stages.events),'decoder_calls':list(decode_calls),
                'flags_before':flags_before,'flags_after':backend_flags(),'video_sha256':None,'video_path':None,
                'decoded_rgb':[],'shadow_records':list(probe.records) if probe else []}
        state['cases'][-1][mode]=result;save()  # Persist before validation or full decode.
        if outcome!='TEXT_REJECTED':
            validate_schedule(observed,counts.result(),sampling,'worldcache');assert len(traces)==72
            assert [e['stage'] for e in stages.events][:3]==['sample_return','decode_input','decode_output']
        else:assert not traces and not stages.events
        if outcome=='ACCEPTED':
            assert len(paths)==1 and Path(paths[0]).is_file()
            result.update(video_sha256=sha(paths[0]),video_path=str(paths[0]))
            with av.open(str(paths[0])) as container:
                for frame in container.decode(video=0):
                    rgb=frame.to_ndarray(format='rgb24')
                    result['decoded_rgb'].append({'sha256':hashlib.sha256(rgb.tobytes()).hexdigest(),
                         'shape':list(rgb.shape),'pts':frame.pts,'time_base':str(frame.time_base)})
            assert len(result['decoded_rgb'])==93 and all(f['shape']==[432,768,3] for f in result['decoded_rgb'])
        else:assert not paths  # Retained rejection; never save a rejected result.
        save();return result
    try:
        for index,sample in enumerate(samples):
            state['cases'].append({'name':sample.name,'index':index,'sample':json.loads(sample.model_dump_json()),'status':'OFF_PENDING'})
            off=generate(sample,'off',None)
            selection=select_pairs(off['trace'],config['max_pairs_per_sample'])
            state['cases'][-1].update(selection=selection,status='POINTS_FROZEN_BEFORE_SHADOW');save()
            probe=SameStateProbe(selection['calls'],config['calibration_defaults'],grouped=True) if selection['calls'] else None
            on=generate(sample,'on',probe)
            state['cases'][-1]['checks']=validate_pair(off,on,selection)
            state['cases'][-1]['status']='PAIR_PARITY_PASS'
            state['cases'][-1]['coverage']=selection['coverage'];save()
            net.forward=original
        assert len(state['cases'])==8 and all(c['status']=='PAIR_PARITY_PASS' for c in state['cases'])
        state['status']='W1D_CAL8_ATTEMPTED_ALL_PARITY_PASS'
    finally:
        net.forward=original;handle.remove();stages.close();guards.close();counts.close()
    cleanup_environment()
except BaseException as exc:
    state.update(status='TECH_BLOCKED',error_type=type(exc).__name__,error=str(exc));traceback.print_exc();raise
finally:
    state['ended_unix']=time.time();state['process_wall_seconds']=state['ended_unix']-state['started_unix'];save()
