"""Scalar-recent own-trajectory replay of frozen official CAL8 schedules."""
import argparse
import hashlib
import json
import os
import signal
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
state={'stage':'W1_FIXED_REPLAY','status':'INITIALIZING','pid':os.getpid(),'started_unix':time.time(),'cases':[],
       'gates':{'official_reference_pass':False,'candidate_parity_pass':False}}
def interrupted(signum,frame):
    raise SystemExit('Received supervisor/timeout signal '+str(signum))
signal.signal(signal.SIGTERM,interrupted)
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
    protocol_path=project/'manifests/w1_fixed_replay_protocol.json'
    config=json.loads(protocol_path.read_text())
    reference_path=project/config['reference_receipt']
    assert sha(reference_path)==config['reference_receipt_sha256'],'Reference receipt changed'
    reference=json.loads(reference_path.read_text())
    screen_path=project/'reports/w1d_cal8_r1_summary.json'
    assert sha(screen_path)==config['reference_screen_sha256']
    from wcomr.w1d_summary import summarize as summarize_cal
    assert summarize_cal(reference)==json.loads(screen_path.read_text())
    assert config['candidate']=='scalar' and json.loads(screen_path.read_text())['candidate_signals']==['scalar']
    assert config['calibration_defaults']==reference['protocol']['calibration_defaults']
    state['source_sha256']={str(path.relative_to(project)):sha(path) for path in
        [protocol_path,project/'scripts/run_w1_replay.py',project/'scripts/supervise_f1.py']+[project/('src/wcomr/'+name+'.py') for name in
        ['fixed_replay','integration','shadow_forward','calibration','shadow_metrics','stage_witness','decoder_policy','guardrail_observation','measurement','protocol','replay_results','video_difference','w1d','w1d_summary']]}
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
    assert [s.name for s in samples]==[c['name'] for c in config['samples']]==reference['protocol']['samples']
    for entry,case in zip(config['samples'],reference['cases']):
        assert entry['schedule']==case['off']['trace']
    actual_setup=json.loads(setup.model_dump_json())
    assert {k:v for k,v in actual_setup.items() if k!='output_dir'}=={k:v for k,v in reference['setup'].items() if k!='output_dir'},'Reference setup differs'
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
    from wcomr.fixed_replay import FixedReplay,build_replay_forward
    from wcomr.shadow_forward import ShadowProbe
    from wcomr.replay_results import strict_parity,candidate_parity,validate_schedule_receipt
    from wcomr.video_difference import compare_videos
    model=inference.pipe.model
    layout_path=Path.cwd()/'cosmos_predict2/_src/predict2/networks/minimal_v4_dit.py'
    assert sha(layout_path)==reference['protocol']['layout_source_sha256'],'Layout source drift'
    checkpoint=project/'hfhub/models--nvidia--Cosmos-Predict2.5-2B/snapshots/6787e176dce74a101d922174a95dba29fa5f0c55/tokenizer.pth'
    h=hashlib.sha256()
    with checkpoint.open('rb') as file:
        for chunk in iter(lambda:file.read(8*1024*1024),b''):h.update(chunk)
    assert h.hexdigest()==reference['protocol']['decoder_checkpoint_sha256']==checkpoint.resolve().name
    state.update(decoder_checkpoint_sha256=h.hexdigest(),flags=backend_flags(),
                 tensor_layout={'residual':'B,T,H,W,D','velocity':'B,C,T,H,W',
                                'patch_spatial':net.patch_spatial,'patch_temporal':net.patch_temporal},
                 limitation='Own-current-state candidate on frozen official schedule. Hashing/shadow timing and RGB differences are not clean speed/quality or independent confirmation.')
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
    def finite_output_hook(module,args,output):
        def check(value):
            if isinstance(value,torch.Tensor):
                assert bool(torch.isfinite(value).all()),'Nonfinite replay model output'
            elif isinstance(value,(list,tuple)):
                for item in value:check(item)
            else:raise TypeError('Unsupported replay output type')
        check(output);traces.append(digest(output))
    handle=net.register_forward_hook(finite_output_hook)
    original=net.forward
    cache_fields=['cnt','worldcache_step_skipped_count','accumulated_rel_l1_distance','residual_cache',
                  'probe_residual_cache','residual_window','probe_residual_window','previous_internal_states',
                  'previous_input','previous_output','resume_flag']
    def generate(sample,label,mode,entry,holder,key,shadow_calls=None):
        counts.reset();traces.clear();guards.reset();stages.events=[];decode_calls.clear()
        replay=FixedReplay(entry['schedule'],mode,config['calibration_defaults'])
        identity=sample.name+'/'+label;replay.begin_request(identity)
        probe=ShadowProbe(shadow_calls) if shadow_calls else None
        if probe:probe.begin_request(identity)
        net.forward=types.MethodType(build_replay_forward(wc.worldcache_mini_train_dit_forward,replay,probe),net)
        state.update(status='GENERATING',current_sample=sample.name,current_mode=label);save()
        flags_before=backend_flags();torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats();started=time.perf_counter()
        destination=root/sample.name/label;destination.mkdir(parents=True,exist_ok=False)
        try:
            paths=inference.generate([sample],output_dir=destination)
        except BaseException:
            holder[key]={'status':'FAILED_DURING_GENERATION','partial_trace':list(counts.trace),
                         'partial_replay_records':list(replay.records),'forward_output_sha256':list(traces)}
            save();raise
        finally:net.forward=original
        torch.cuda.synchronize();outcome=guards.classify(paths)
        observed=None
        if outcome!='TEXT_REJECTED':
            scheduler=model.sample_scheduler
            observed={'scheduler_class':type(scheduler).__name__,'requested_steps':sample.num_steps,
                      'actual_schedule_steps':len(scheduler.timesteps),'timesteps':scheduler.timesteps.detach().cpu().tolist(),
                      'use_kerras_sigma':model.config.use_kerras_sigma_at_inference,'worldcache_horizon':net.worldcache_num_steps}
        calibration_end=digest([[cal.receipt(),[(anchor.step,anchor.probe,anchor.residual) for anchor in cal.anchors]] for cal in replay.calibrators]) if replay.calibrators else None
        result={'mode':label,'outcome':outcome,'guardrail_events':list(guards.events),
                'seconds_with_hashing_and_diagnostics':time.perf_counter()-started,
                'forward_output_sha256':list(traces),'block_counts':counts.result(),'trace':list(counts.trace),
                'cache_end_sha256':digest([getattr(net,k) for k in cache_fields]),'sampling':observed,
                'pipeline_events':list(stages.events),'decoder_calls':list(decode_calls),
                'flags_before':flags_before,'flags_after':backend_flags(),'video_sha256':None,'video_path':None,
                'decoded_rgb':[],'shadow_records':list(probe.records) if probe else [],
                'peak_memory':{'allocated_bytes':torch.cuda.max_memory_allocated(),'reserved_bytes':torch.cuda.max_memory_reserved(),
                               'scope':'Reset just before generation; includes existing live/reserved allocator state'},
                'calibration_end_sha256':calibration_end,
                'replay':{'request':identity,'mode':mode,'calibration_params':replay.params,'records':list(replay.records)} if outcome!='TEXT_REJECTED' else None}
        holder[key]=result;save()  # Persist before validation or full decode.
        if outcome!='TEXT_REJECTED':
            validate_schedule(observed,counts.result(),sampling,'worldcache');assert len(traces)==72
            assert [e['stage'] for e in stages.events][:3]==['sample_return','decode_input','decode_output']
            result['replay']=replay.finish()
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
        result['schedule_check']=validate_schedule_receipt(result,entry)
        replay.calibrators=None
        save();return result
    try:
        for index,sample in enumerate(samples):
            entry=config['samples'][index]
            case={'name':sample.name,'index':index,'sample':json.loads(sample.model_dump_json()),'status':'SCALAR_OFF_PENDING'}
            state['cases'].append(case);save()
            if index==0:
                gate=generate(sample,'official_replay','official',entry,state,'official_gate')
                state['official_reference_checks']=strict_parity(reference['cases'][0]['off'],gate)
                state['gates']['official_reference_pass']=True;save()
            off=generate(sample,'scalar_off','scalar',entry,case,'scalar_off')
            if index==0:
                case['status']='SCALAR_PARITY_PENDING';save()
                on=generate(sample,'scalar_on','scalar',entry,case,'scalar_on',entry['first_gate_shadow_calls'])
                state['candidate_parity_checks']=candidate_parity(off,on,entry)
                state['gates']['candidate_parity_pass']=True;save()
            assert all(state['gates'].values())
            ref=reference['cases'][index]['off']
            if off['outcome']=='ACCEPTED' and ref['outcome']=='ACCEPTED':
                assert sha(ref['video_path'])==ref['video_sha256'],'Reference video drift'
                comparison_started=time.perf_counter()
                case['video_difference']=compare_videos(ref['video_path'],off['video_path'])
                case['video_comparison_cpu_seconds']=time.perf_counter()-comparison_started
            else:case['video_difference']={'status':'NOT_ACCEPTED_PAIR','reference_outcome':ref['outcome'],'candidate_outcome':off['outcome']}
            case['status']='REPLAY_COMPLETED';save()
        assert len(state['cases'])==8 and all(c['status']=='REPLAY_COMPLETED' for c in state['cases'])
        state['status']='W1_REPLAY_ATTEMPTED_ALL_TECH_PASS'
    finally:
        net.forward=original;handle.remove();stages.close();guards.close();counts.close()
    cleanup_environment()
except BaseException as exc:
    state.update(status='TECH_BLOCKED',error_type=type(exc).__name__,error=str(exc));traceback.print_exc();raise
finally:
    state['ended_unix']=time.time();state['process_wall_seconds']=state['ended_unix']-state['started_unix'];save()
