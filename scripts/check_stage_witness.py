"""One fresh-process official WC generation with read-only stage witnesses."""
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
p.add_argument('--deterministic-decode',action='store_true')
a=p.parse_args()
project=a.project.resolve();root=a.receipt.parent
os.environ.update(CUDA_VISIBLE_DEVICES=a.gpu_uuid,HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
sys.path.insert(0,str(project/'src'))
state={'stage':'POST_MODEL_STAGE_WITNESS','status':'INITIALIZING','pid':os.getpid(),'started_unix':time.time(),'runs':[]}
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
    protocol_path=project/('manifests/decoder_policy_protocol.json' if a.deterministic_decode else 'manifests/stage_witness_protocol.json')
    config=json.loads(protocol_path.read_text())
    state['source_sha256']={str(path.relative_to(project)):sha(path) for path in
        [protocol_path,project/'scripts/check_stage_witness.py',project/'src/wcomr/stage_witness.py',project/'src/wcomr/decoder_policy.py']}
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
    import inspect
    import av
    import cosmos_predict2.inference as inference_module
    from wcomr.stage_witness import StageWitness
    from wcomr.decoder_policy import backend_flags,decode_policy,tokenizer_identity,compare_decoder_identity
    from contextlib import contextmanager
    observer=StageWitness()
    model=inference.pipe.model
    def tensor_input(stage):
        def record(args,kwargs):
            bound = args[0] if args else next(iter(kwargs.values()))
            observer.record(stage,bound)
        return record
    # Resolve source identities BEFORE replacing imported module aliases.
    sources={}
    for target in [type(model),type(model.tokenizer),type(inference.pipe),inference_module,
                   inference_module.guardrail_presets,inspect.getmodule(inference_module.save_img_or_video)]:
        path=Path(inspect.getfile(target)).resolve()
        sources[str(path.relative_to(Path.cwd()))]=sha(path)
    flags={'cudnn_benchmark':torch.backends.cudnn.benchmark,
           'cudnn_deterministic':torch.backends.cudnn.deterministic,
           'cudnn_allow_tf32':torch.backends.cudnn.allow_tf32,
           'matmul_allow_tf32':torch.backends.cuda.matmul.allow_tf32,
           'deterministic_algorithms':torch.are_deterministic_algorithms_enabled()}
    state['runtime_identity']={'sources':sources,'torch':str(torch.__version__),
        'cuda':torch.version.cuda,'cudnn':torch.backends.cudnn.version(),'av':av.__version__,
        'flags':flags,'setup':{k:v for k,v in state['setup'].items() if k!='output_dir'},'sample':state['sample'],
        'asset_manifests':{str(p.relative_to(project)):sha(p) for p in [project/'manifests/upstream.json',project/'manifests/guardrail_integrity.json',project/'manifests/auxiliary_weights.json']}}
    observer.wrap(model,'generate_samples_from_batch',after=lambda r:observer.record('sample_return',r))
    decoder_calls=[]
    checkpoint=project/'hfhub/models--nvidia--Cosmos-Predict2.5-2B/snapshots/6787e176dce74a101d922174a95dba29fa5f0c55/tokenizer.pth'
    assert checkpoint.is_file(),'Pinned VAE checkpoint missing'
    # Stream the actual weights; record both requested revision and resolved blob.
    with checkpoint.open('rb') as file:
        h=hashlib.sha256()
        for chunk in iter(lambda:file.read(8*1024*1024),b''):h.update(chunk)
    actual_hash=h.hexdigest();blob=checkpoint.resolve().name
    assert len(blob)==64 and actual_hash==blob,'VAE checkpoint content differs from content-addressed blob'
    state['decoder_checkpoint']={'path':str(checkpoint),'resolved':str(checkpoint.resolve()),
                                 'bytes':checkpoint.stat().st_size,'sha256':actual_hash}
    state['decoder_policy']={'enabled':a.deterministic_decode,'scope':'original model.decode only',
                            'benchmark':False if a.deterministic_decode else flags['cudnn_benchmark'],
                            'deterministic':True if a.deterministic_decode else flags['cudnn_deterministic']}
    state['runtime_identity']['decoder_checkpoint']=state['decoder_checkpoint']
    state['runtime_identity']['decoder_policy']=state['decoder_policy']
    def before_decode(args,kwargs):
        tensor_input('decode_input')(args,kwargs)
        decoder_calls.append({'before':tokenizer_identity(model.tokenizer),'flags_before':backend_flags()})
    @contextmanager
    def local_decode_context():
        with decode_policy(a.deterministic_decode) as active:
            decoder_calls[-1]['flags_inside']=active
            yield
        decoder_calls[-1]['flags_after']=backend_flags()
    def after_decode(result):
        observer.record('decode_output',result)
        call=decoder_calls[-1];call['after']=tokenizer_identity(model.tokenizer)
        call['identity_unchanged']=compare_decoder_identity(call['before'],call['after'])
        assert all(call['identity_unchanged'].values()),'Decode mutated weights/normalization/settings'
        assert call['flags_before']==call['flags_after'],'Decode flags did not restore'
    observer.wrap(model,'decode',before=before_decode,after=after_decode,call_context=local_decode_context)
    observer.wrap(inference_module.guardrail_presets,'run_video_guardrail',
                  before=tensor_input('guardrail_input'),after=lambda r:observer.record('guardrail_output',r))
    encoding=[]
    encode_signature=inspect.signature(inference_module.save_img_or_video)
    def before_encode(args,kwargs):
        bound=encode_signature.bind(*args,**kwargs);bound.apply_defaults()
        observer.record('save_input',next(v for v in bound.arguments.values() if isinstance(v,torch.Tensor)))
        encoding.append({k:bound.arguments[k] for k in ['fps','quality','ffmpeg_params']})
    observer.wrap(inference_module,'save_img_or_video',before=before_encode)
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
    counts=BlockCounts(net.blocks,cache_model=net)
    try:
        state['status']='GENERATING';save()
        destination=root/'video';destination.mkdir(exist_ok=False)
        paths=inference.generate([sample],output_dir=destination)
        torch.cuda.synchronize()
        assert len(paths)==1 and Path(paths[0]).is_file(),'Expected accepted output'
        scheduler=model.sample_scheduler
        observed={'scheduler_class':type(scheduler).__name__,'requested_steps':sample.num_steps,
                  'actual_schedule_steps':len(scheduler.timesteps),'timesteps':scheduler.timesteps.detach().cpu().tolist(),
                  'use_kerras_sigma':model.config.use_kerras_sigma_at_inference,'worldcache_horizon':net.worldcache_num_steps}
        cache_fields=['cnt','worldcache_step_skipped_count','accumulated_rel_l1_distance','residual_cache',
                      'probe_residual_cache','residual_window','probe_residual_window','previous_internal_states',
                      'previous_input','previous_output','resume_flag']
        state.update(events=observer.events,forward_output_sha256=traces,block_counts=counts.result(),trace=counts.trace,
                     cache_end_sha256=digest([getattr(net,k) for k in cache_fields]),sampling=observed,
                     video_path=str(paths[0]),video_sha256=sha(paths[0]),encoding=encoding)
        validate_schedule(observed,counts.result(),sampling,'worldcache')
        assert len(traces)==72
        stages=[e['stage'] for e in observer.events]
        assert stages[0]=='sample_return' and stages[-3:]==['guardrail_input','guardrail_output','save_input']
        middle=stages[1:-3]
        assert middle and len(middle)%2==0 and middle==['decode_input','decode_output']*(len(middle)//2),'Unexpected decode topology'
        assert observer.events[-2]['value']['kind']!='None','Guardrail rejected'
        frames=[]
        with av.open(str(paths[0])) as container:
            stream=container.streams.video[0]
            state['codec']={'name':stream.codec_context.name,'width':stream.width,'height':stream.height,
                            'format':str(stream.codec_context.format),'rate':str(stream.average_rate),'metadata':container.metadata}
            for frame in container.decode(video=0):
                pixels=frame.to_ndarray(format='rgb24')
                frames.append({'sha256':hashlib.sha256(pixels.tobytes()).hexdigest(),
                               'shape':list(pixels.shape),'pts':frame.pts,'time_base':str(frame.time_base)})
        assert len(frames)==93 and all(f['shape']==[432,768,3] for f in frames),'Video shape mismatch'
        state.update(decoded_rgb=frames,status='STAGE_WITNESS_ACCEPTED_SINGLE_FRESH_PROCESS',
                     limitation='Read-only engineering witness, not a quality or speed result; no causal attribution yet.')
    finally:
        state['events']=observer.events;state['decoder_calls']=decoder_calls;observer.close();handle.remove();counts.close()
    cleanup_environment()
except BaseException as exc:
    state.update(status='TECH_BLOCKED',error_type=type(exc).__name__,error=str(exc));traceback.print_exc();raise
finally:
    state['ended_unix']=time.time();state['process_wall_seconds']=state['ended_unix']-state['started_unix'];save()
