"""One resident model, frozen original8 two-arm three-repeat cost experiment.

CPU validate-only is allowed now. Real generation requires the separate next
window decision and an updated approved ledger; this script cannot expand it.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import time
import traceback

p=argparse.ArgumentParser()
p.add_argument('--project',type=Path,required=True)
p.add_argument('--gpu-uuid',default='')
p.add_argument('--receipt',type=Path,required=True)
p.add_argument('--validate-only',action='store_true')
a=p.parse_args();project=a.project.resolve();root=a.receipt.parent
sys.path.insert(0,str(project/'src'))
from wcomr.clean_timing import validate_protocol,validate_attempt,synchronized_timer,summarize,validate_warmup_artifact,FORBIDDEN
from wcomr.development_vqa_run import sha256,load_bound
if a.receipt.exists():raise SystemExit('Existing run identity must not be overwritten')
state={'stage':'W1_CLEAN_TIMING','pid':os.getpid(),'status':'INITIALIZING','started_unix':time.time(),'rows':[],'gpu_uuid':a.gpu_uuid}
def save():
    root.mkdir(parents=True,exist_ok=True);tmp=a.receipt.with_suffix('.tmp')
    tmp.write_text(json.dumps(state,indent=2,allow_nan=False)+'\n');tmp.replace(a.receipt)
def interrupted(signum,frame):raise SystemExit('Signal '+str(signum))
signal.signal(signal.SIGTERM,interrupted)
save()
try:
    path=project/'manifests/w1_clean_timing_protocol.json';config=json.loads(path.read_text())
    frozen=load_bound(project/config['frozen_replay_protocol'],config['frozen_replay_sha256'])
    validate_protocol(config,frozen)
    reference=load_bound(project/frozen['reference_receipt'],frozen['reference_receipt_sha256'])
    prior=load_bound(project/config['prior_candidate_receipt'],config['prior_candidate_sha256'])
    assert prior['status']=='W1_REPLAY_ATTEMPTED_ALL_TECH_PASS' and all(prior['gates'].values())
    assert frozen['calibration_defaults']==reference['protocol']['calibration_defaults']==prior['protocol']['calibration_defaults']
    assert [c['name'] for c in reference['cases']]==[c['name'] for c in prior['cases']]==config['samples']
    assert [x['schedule'] for x in frozen['samples']]==[x['off']['trace'] for x in reference['cases']]
    input_path=project/'configs/cal_w1d8.jsonl';assert sha256(input_path)==frozen['input_sha256']
    assert sha256(project/'manifests/cal_v1.json')==frozen['cal_manifest_sha256']
    inputs=[json.loads(x) for x in input_path.read_text().splitlines()];assert [x['name'] for x in inputs]==config['samples']
    upstream=json.loads((project/'manifests/upstream.json').read_text());completion=json.loads((project/'manifests/runtime_completion.json').read_text())
    for file,digest in completion['files'].items():assert sha256(Path.cwd()/file)==digest,file
    sampling=json.loads((project/'manifests/f1_runtime_protocol.json').read_text())
    assert sha256(Path.cwd()/'cosmos_predict2/_src/predict2/models/fm_solvers_unipc.py')==sampling['scheduler_source_sha256']
    assert sha256(Path.cwd()/'cosmos_predict2/_src/predict2/networks/minimal_v4_dit.py')==reference['protocol']['layout_source_sha256']
    files=['scripts/run_w1_clean_timing.py','scripts/supervise_f1.py','manifests/w1_clean_timing_protocol.json','configs/f1_setup.json',
           'src/wcomr/clean_timing.py','src/wcomr/fixed_replay.py','src/wcomr/integration.py','src/wcomr/calibration.py',
           'src/wcomr/measurement.py','src/wcomr/guardrail_observation.py','src/wcomr/decoder_policy.py','src/wcomr/stage_witness.py',
           'src/wcomr/runtime_config.py','src/wcomr/protocol.py','src/wcomr/development_vqa_run.py','src/wcomr/replay_results.py']
    state.update(protocol=config,source_sha256={f:sha256(project/f) for f in files},sampling_protocol=sampling,input_sha256=sha256(input_path))
    if a.validate_only:
        state.update(status='CPU_PROTOCOL_SOURCE50_ATTEMPTS_VERIFIED_NO_TORCH_IMPORT_NO_GENERATION',cuda_initialized=False)
        print(state['status'])
    else:
        budget=json.loads((project/'reports/budget.json').read_text())
        if budget['cap_gpu_hours']<config['minimum_project_cap_gpu_hours']:
            raise RuntimeError('Next GPU budget decision pending; unchanged first-batch ledger refused')
        if (budget['cap_gpu_hours']-budget['used_gpu_hours'])*3600<config['max_gpu_seconds']:
            raise RuntimeError('Insufficient ledger balance for complete proposed timing window')
        if not a.gpu_uuid:raise RuntimeError('Explicit admitted GPU UUID required')
        os.environ.update(CUDA_VISIBLE_DEVICES=a.gpu_uuid,HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_CACHE=str(project/'hfhub'))
        import torch
        import types
        from contextlib import contextmanager
        from cosmos_oss.init import init_environment,init_output_dir,cleanup_environment
        from cosmos_predict2.config import SetupArguments,InferenceArguments
        from cosmos_predict2.inference import Inference
        import cosmos_predict2.inference as inference_module
        from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
        from wcomr.runtime_config import install_core_inference_registration
        from wcomr.measurement import BlockCounts
        from wcomr.protocol import validate_schedule
        from wcomr.fixed_replay import FixedReplay,build_replay_forward
        from wcomr.replay_results import summarize as summarize_prior
        from wcomr.decoder_policy import backend_flags,decode_policy
        from wcomr.guardrail_observation import GuardrailObservation
        from wcomr.stage_witness import StageWitness
        assert summarize_prior(prior,reference=reference)['status']=='FROZEN_REPLAY_TECH_PASS_QUALITY_UNASSESSED'
        assert sha256(wc.__file__)==upstream['cache_module_sha256']
        checkpoint=project/'hfhub/models--nvidia--Cosmos-Predict2.5-2B/snapshots/6787e176dce74a101d922174a95dba29fa5f0c55/tokenizer.pth'
        assert sha256(checkpoint)==reference['protocol']['decoder_checkpoint_sha256']
        params=json.loads((project/'configs/f1_setup.json').read_text());assert not params['disable_guardrails'] and not params['use_torch_compile']
        params.update(output_dir=str(root),worldcache_enabled=True,keep_going=True)
        init_environment();init_output_dir(root,profile=False);setup=SetupArguments(**params)
        install_core_inference_registration(setup.model,setup.experiment)
        actual=json.loads(setup.model_dump_json());assert {k:v for k,v in actual.items() if k!='output_dir'}=={k:v for k,v in reference['setup'].items() if k!='output_dir'}
        state['setup']=actual;save();started=time.perf_counter();inference=Inference(setup);state['model_load_seconds']=time.perf_counter()-started
        net=inference.pipe.model.net;net.eval();model=inference.pipe.model
        samples={s.name:s for s in InferenceArguments.from_files([input_path])}
        counts=BlockCounts(net.blocks,cache_model=net);guards=GuardrailObservation(inference_module.guardrail_presets)
        # Wrapper carries only the existing decode flags policy. No StageWitness
        # record/witness, tokenizer hash, RNG snapshots or tensor copy is called.
        wrappers=StageWitness();decode_flags=[]
        @contextmanager
        def context():
            with decode_policy(True) as flags:
                decode_flags.append(flags);yield
        wrappers.wrap(model,'decode',call_context=context)
        original=net.forward;entries={x['name']:x for x in frozen['samples']}
        def audit_video(path):
            import av
            import numpy as np
            frames=0;shape=None;times=[];finite=True;rgb_hashes=[]
            with av.open(str(path)) as video:
                assert float(video.streams.video[0].average_rate)==16
                for frame in video.decode(video=0):
                    rgb=frame.to_ndarray(format='rgb24');assert list(rgb.shape)==[432,768,3]
                    rgb_hashes.append(hashlib.sha256(rgb.tobytes()).hexdigest());shape=list(rgb.shape);frames+=1;times.append(float(frame.time));finite=finite and bool(np.isfinite(rgb).all())
            return {'path':str(path),'sha256':sha256(path),'frames':frames,'shape':shape,'finite':finite,
                    'decoded_rgb_sha256':rgb_hashes,'timestamps_strictly_increasing':all(y>x for x,y in zip(times,times[1:])),'fps':16}
        try:
            for attempt in config['attempts']:
                entry=entries[attempt['name']];sample=samples[attempt['name']]
                counts.reset();guards.reset();decode_flags.clear()
                replay=FixedReplay(entry['schedule'],attempt['arm'],config['calibration_defaults']);replay.begin_request(attempt['id'])
                net.forward=types.MethodType(build_replay_forward(wc.worldcache_mini_train_dit_forward,replay),net)
                row={'attempt':attempt,'status':'GENERATING','disabled_observers':FORBIDDEN,'flags_before':backend_flags()}
                state['rows'].append(row);state['status']='GENERATING';state['current_attempt']=attempt['id'];save()
                destination=root/'videos'/attempt['id'];destination.mkdir(parents=True,exist_ok=False)
                torch.cuda.reset_peak_memory_stats()
                try:
                    with synchronized_timer(torch.cuda.synchronize,row):
                        paths=inference.generate([sample],output_dir=destination)
                except BaseException:
                    row.update(status='FAILED_DURING_GENERATION',trace=counts.trace,partial_replay_records=replay.records);save();raise
                finally:net.forward=original
                row.update(status='MEASURED_AUDIT_PENDING',flags_after=backend_flags(),decode_flags=list(decode_flags),
                           guardrail_events=list(guards.events),outcome=guards.classify(paths),trace=list(counts.trace),
                           block_counts=counts.result(),peak_memory={'allocated_bytes':torch.cuda.max_memory_allocated(),'reserved_bytes':torch.cuda.max_memory_reserved()})
                save();audit_started=time.perf_counter()
                row['replay']=None if row['outcome']=='TEXT_REJECTED' else replay.finish()
                if row['outcome']!='TEXT_REJECTED':
                    scheduler=model.sample_scheduler
                    observed={'scheduler_class':type(scheduler).__name__,'requested_steps':sample.num_steps,'actual_schedule_steps':len(scheduler.timesteps),
                        'timesteps':scheduler.timesteps.detach().cpu().tolist(),'use_kerras_sigma':model.config.use_kerras_sigma_at_inference,'worldcache_horizon':net.worldcache_num_steps}
                    validate_schedule(observed,counts.result(),sampling,'worldcache');row['sampling']=observed
                row['artifact']=audit_video(paths[0]) if row['outcome']=='ACCEPTED' else None
                row['audit_seconds_outside_generation_timer']=time.perf_counter()-audit_started;row['status']='AUDITED'
                validate_attempt(row,attempt,entry['schedule'])
                if not attempt['timed']:
                    target=reference['cases'][0]['off'] if attempt['arm']=='official' else prior['cases'][0]['scalar_off']
                    validate_warmup_artifact(row,target);row['prior_decoded_rgb_gate_passed']=True
                replay.calibrators=None;save()
            state['status']='W1_CLEAN_TIMING_ALL50_AUDITED';state['summary']=summarize(state,frozen,reference,prior);save()
        finally:
            net.forward=original;wrappers.close();guards.close();counts.close()
        cleanup_environment()
except BaseException as exc:
    state.update(status='TECH_BLOCKED',error_type=type(exc).__name__,error=str(exc));traceback.print_exc();raise
finally:
    state['ended_unix']=time.time();state['process_wall_seconds']=state['ended_unix']-state['started_unix'];save()
