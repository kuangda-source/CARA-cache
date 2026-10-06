"""Full-pipeline own-state observation; the historical OFF identity is mandatory."""
from contextlib import contextmanager
import hashlib
from pathlib import Path
import time
import types

import torch
from .decoder_policy import backend_flags, decode_policy, tokenizer_identity, compare_decoder_identity
from .fixed_replay import FixedReplay, build_replay_forward
from .guardrail_observation import GuardrailObservation
from .measurement import BlockCounts
from .own_state_shadow import OwnStateProbe, build_own_state_forward
from .protocol import validate_schedule
from .replay_results import strict_parity, validate_schedule_receipt
from .stage_witness import StageWitness

CACHE_FIELDS = ['cnt','worldcache_step_skipped_count','accumulated_rel_l1_distance',
    'residual_cache','probe_residual_cache','residual_window','probe_residual_window',
    'previous_internal_states','previous_input','previous_output','resume_flag']


def digest(value):
    # Byte-compatible with the original W1 replay, including tuple/list tags.
    h = hashlib.sha256()
    def visit(x):
        if isinstance(x, torch.Tensor):
            h.update(str((tuple(x.shape), str(x.dtype))).encode())
            h.update(x.detach().contiguous().reshape(-1).view(torch.uint8).cpu().numpy().tobytes())
        elif isinstance(x, (list, tuple)):
            h.update(str(type(x)).encode())
            for item in x: visit(item)
        else: h.update(repr(x).encode())
    visit(value)
    return h.hexdigest()


def decoded_rgb(path):
    import av
    records = []
    with av.open(str(path)) as container:
        for frame in container.decode(video=0):
            rgb = frame.to_ndarray(format='rgb24')
            records.append({'sha256': hashlib.sha256(rgb.tobytes()).hexdigest(),
                'shape': list(rgb.shape), 'pts': frame.pts, 'time_base': str(frame.time_base)})
    if len(records) != 93 or any(r['shape'] != [432,768,3] for r in records):
        raise ValueError('Complete original 93-frame decode required')
    return records


def historical_bridge(old, observed, entry, calls):
    checks = strict_parity(old, observed)
    checks['calibration_end'] = old['calibration_end_sha256'] == observed['calibration_end_sha256']
    checks['replay'] = all(old['replay'][k] == observed['replay'][k]
        for k in ['mode','calibration_params','records'])
    checks['observations'] = [r['call'] for r in observed['shadow_records']] == calls
    validate_schedule_receipt(old, entry); validate_schedule_receipt(observed, entry)
    if not all(checks.values()):
        raise ValueError('Historical W1 OFF identity bridge failed: '+str(checks))
    return checks


def run_request(inference, sample, entry, *, params, calls, original, sampling,
                inference_module, destination, holder, save, synchronize,
                reader=decoded_rgb, peak=None, diagnostic=True):
    """diagnostic=False is only used to construct an OFF reference in CPU fixtures."""
    net = inference.pipe.model.net; model = inference.pipe.model
    if (net.training or any(m.training for m in net.modules()) or destination.exists()
            or len(entry['schedule']) != 72):
        raise ValueError('Fresh destination, eval and full frozen mask required')
    prior_own = 'forward' in vars(net); prior_value = vars(net).get('forward')
    replay = FixedReplay(entry['schedule'], 'scalar', params)
    identity = sample.name+'/own_state_shadow'; replay.begin_request(identity)
    probe = OwnStateProbe(calls, replay) if diagnostic else None
    if probe: probe.begin_request(identity)
    counts = BlockCounts(net.blocks, cache_model=net); stages = StageWitness()
    guards = None; handle = None; outputs = []; decode_calls = []
    result = {'status':'GENERATING','shadow_records':[], 'forward_output_sha256':[]}
    holder['observed'] = result; save()
    try:
        guards = GuardrailObservation(inference_module.guardrail_presets)
        def input_record(stage):
            return lambda args,kwargs: stages.record(stage,args[0] if args else next(iter(kwargs.values())))
        stages.wrap(model,'generate_samples_from_batch',after=lambda r:stages.record('sample_return',r))
        def before_decode(args,kwargs):
            input_record('decode_input')(args,kwargs)
            decode_calls.append({'before':tokenizer_identity(model.tokenizer),'flags_before':backend_flags()})
        def after_decode(value):
            stages.record('decode_output',value)
            call=decode_calls[-1];call['after']=tokenizer_identity(model.tokenizer);call['flags_after']=backend_flags()
            call['unchanged']=compare_decoder_identity(call['before'],call['after'])
            if (not all(call['unchanged'].values()) or call['flags_before']!=call['flags_after']
                    or call['flags_inside']!=dict(call['flags_before'],cudnn_benchmark=False,cudnn_deterministic=True)):
                raise ValueError('Original decoder identity/policy differs')
        @contextmanager
        def decode_context():
            with decode_policy(True) as active:
                decode_calls[-1]['flags_inside']=active
                yield
        stages.wrap(model,'decode',before=before_decode,after=after_decode,call_context=decode_context)
        stages.wrap(inference_module.guardrail_presets,'run_video_guardrail',before=input_record('guardrail_input'),
            after=lambda r:stages.record('guardrail_output',r))
        stages.wrap(inference_module,'save_img_or_video',before=input_record('save_input'))
        def finite_hook(module,args,value):
            def check(v):
                if isinstance(v,torch.Tensor):
                    if not bool(torch.isfinite(v).all()):raise ValueError('Nonfinite deployed output')
                elif isinstance(v,(list,tuple)):
                    for item in v:check(item)
                else:raise TypeError('Unsupported deployed output')
            check(value);outputs.append(digest(value))
        handle=net.register_forward_hook(finite_hook)
        forward=build_own_state_forward(original,replay,probe) if diagnostic else build_replay_forward(original,replay)
        net.forward=types.MethodType(forward,net)
        destination.mkdir(parents=True,exist_ok=False)
        flags=backend_flags();synchronize();started=time.perf_counter()
        if peak:peak('reset')
        paths=inference.generate([sample],output_dir=destination)
        synchronize();outcome=guards.classify(paths)
        observed=None
        if outcome!='TEXT_REJECTED':
            scheduler=model.sample_scheduler
            observed={'scheduler_class':type(scheduler).__name__,'requested_steps':sample.num_steps,
                'actual_schedule_steps':len(scheduler.timesteps),'timesteps':scheduler.timesteps.detach().cpu().tolist(),
                'use_kerras_sigma':model.config.use_kerras_sigma_at_inference,'worldcache_horizon':net.worldcache_num_steps}
        result.update(mode='own_state_shadow',outcome=outcome,guardrail_events=list(guards.events),
            seconds_with_hashing_and_diagnostics=time.perf_counter()-started,
            forward_output_sha256=list(outputs),block_counts=counts.result(),trace=list(counts.trace),
            cache_end_sha256=digest([getattr(net,k) for k in CACHE_FIELDS]),sampling=observed,
            pipeline_events=list(stages.events),decoder_calls=decode_calls,
            flags_before=flags,flags_after=backend_flags(),video_sha256=None,video_path=None,decoded_rgb=[],
            shadow_records=list(probe.records) if probe else [],
            calibration_end_sha256=digest([[c.receipt(),[(a.step,a.probe,a.residual) for a in c.anchors]]
                for c in replay.calibrators]) if replay.calibrators else None,
            replay=None,peak_memory=peak('read') if peak else None)
        save()  # Partial observations remain durable if any following gate fails.
        if outcome!='TEXT_REJECTED':
            validate_schedule(observed,counts.result(),sampling,'worldcache')
            result['replay']=replay.finish()
            if probe:result['shadow_records']=probe.finish()
            if len(outputs)!=72:raise ValueError('Missing deployed outputs')
        elif outputs or stages.events:raise ValueError('Text rejection executed pipeline')
        if outcome=='ACCEPTED':
            if len(paths)!=1 or not Path(paths[0]).is_file():raise ValueError('Accepted artifact missing')
            result.update(video_path=str(paths[0]),video_sha256=hashlib.sha256(Path(paths[0]).read_bytes()).hexdigest())
            result['decoded_rgb']=reader(paths[0])
            if len(result['decoded_rgb'])!=93 or any(r['shape']!=[432,768,3] for r in result['decoded_rgb']):
                raise ValueError('Full decoded RGB coverage differs')
        elif paths:raise ValueError('Rejected video unexpectedly saved')
        result['schedule_check']=validate_schedule_receipt(result,entry)
        result['status']='GENERATED_REQUIRES_HISTORICAL_BRIDGE';save()
        return result
    except BaseException as error:
        result.update(status='FAILED_RETAINED_NOT_A_SCIENTIFIC_ROW',error_type=type(error).__name__,error=str(error),
            partial_trace=list(counts.trace),forward_output_sha256=list(outputs),
            partial_replay_records=list(replay.records),shadow_records=list(probe.records) if probe else [])
        save();raise
    finally:
        if prior_own:net.forward=prior_value
        elif 'forward' in vars(net):delattr(net,'forward')
        if handle:handle.remove()
        stages.close()
        if guards:guards.close()
        counts.close();replay.calibrators=None


def run_batch(inference,samples,old,config,*,state,save,output,inference_module,original,synchronize,peak=None,reader=decoded_rgb):
    if [s.name for s in samples]!=config['sample_names']:raise ValueError('Three original requests required')
    state.update(planned_scenes=3,planned_observations=12,cases=[])
    for index,sample in zip(config['sample_indices'],samples):
        ref=old['cases'][index];entry=old['protocol']['samples'][index]
        case={'name':sample.name,'original_CAL_index':index,'status':'PENDING','bridge_pass':False}
        state['cases'].append(case);save()
        observed=run_request(inference,sample,entry,params=old['protocol']['calibration_defaults'],
            calls=config['fixed_CFG_calls'],original=original,sampling=old['sampling_protocol'],
            inference_module=inference_module,destination=output/sample.name,holder=case,save=save,
            synchronize=synchronize,peak=peak,reader=reader)
        case['bridge_checks']=historical_bridge(ref['scalar_off'],observed,entry,config['fixed_CFG_calls'])
        case.update(bridge_pass=True,status='HISTORICAL_OFF_BRIDGE_AND_OBSERVATIONS_PASS');save()
    if len(state['cases'])!=3:raise ValueError('Reduced diagnostic batch')
    state['status']='OWN_STATE_THREE_SCENE_TECH_PASS_REQUIRES_TERMINAL_AUDIT';save()
