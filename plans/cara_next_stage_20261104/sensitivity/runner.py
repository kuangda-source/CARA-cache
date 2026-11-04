"""Already-admitted loaded-model entry. No ledger, dispatch or monitoring service."""
import argparse
import copy
import gc
import json
import os
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(HERE),str(ROOT/'src'),str(ROOT/'scripts')]


def collect_loaded(inference,samples,card,common,output,storage,mode_types,*,cpu_validation=False):
    import torch
    from sampling import execute
    from wcomr.cara_f19_speed190_requests_r1 import Requests
    from wcomr.full_sampling import CompleteStateRoundtrip
    from wcomr.h0_mode import establish_shared_eval,verify_shared_eval
    from wcomr.gpu_budget_pool_v2 import atomic_json,sha
    from wcomr.cara_s_endpoint_runner_r1 import observed_precision
    model,net=inference.pipe.model,inference.pipe.model.net
    caller_owned='forward' in vars(net);caller_forward=net.forward
    precision=observed_precision(model)
    if not cpu_validation and (precision['model_precision']!='torch.bfloat16'
            or precision['use_wan_fp32_strategy'] is not True or precision['outer_autocast'] is not False):
        raise ValueError('CAL35 shared production precision required')
    mode=establish_shared_eval(net,mode_types)
    common['wc'].apply_worldcache(net,**{k.removeprefix('worldcache_'):v for k,v in card['settings'].items()})
    initial=CompleteStateRoundtrip(net,model.sample_scheduler,torch.zeros(1))
    clean=Requests(inference,samples,card,common,cpu_validation=cpu_validation)
    output=Path(output);target=output/'collection.json'
    if target.exists():
        raise ValueError('Existing original collection; recover it without replay')
    state=dict(status='RUNNING',run_id=card['run_id'],scope_sha256=card['scope_sha256'],
        rows=[dict(slot=copy.deepcopy(s),status='NOT_REACHED') for s in card['matrix']],
        CPU_fixture_only=cpu_validation)
    indexed={};reused_members=set()
    record_roots={member:output/'native_states'/member for member in samples}
    if 'reuse' in card:
        reuse=card['reuse'];original=json.loads(Path(reuse['collection']).read_text())
        if original['run_id']!=reuse['run_id'] or original['scope_sha256']!=reuse['scope_sha256']:
            raise ValueError('Original Native record scope differs')
        reused=[copy.deepcopy(r) for r in original['rows'] if r['slot']['id'] in reuse['record_ids']]
        if len(reused)!=len(reuse['record_ids']) or any(r['status']!='COMPLETE' or r['slot']['role']!='NATIVE_RECORD' for r in reused):
            raise ValueError('Complete original Native records required')
        state['reused_rows']=reused
        for row in reused:
            member=row['slot']['member'];reused_members.add(member)
            indexed[member,'NATIVE_RECORD',None]=Path(row['result']['latent_artifact']['path'])
            record_roots[member]=Path(reuse['output_root'])/'native_states'/member
    if 'carryover' in card:
        carried=copy.deepcopy(card['carryover']['rows'])
        for row in carried:
            for key in ('latent_artifact','video_artifact'):
                artifact=row['result'][key]
                if sha(artifact['path'])!=artifact['sha256']:
                    raise ValueError('Carried result bytes differ')
            slot=row['slot']
            indexed[slot['member'],slot['role'],slot['target_update']]=Path(row['result']['latent_artifact']['path'])
        state['carried_rows']=carried
    def save():atomic_json(target,state)
    save()
    try:
        for row in state['rows']:
            slot=row['slot'];storage.check();initial.restore();verify_shared_eval(net,mode)
            row['status']='RUNNING';save()
            member=slot['member'];states=record_roots[member]
            path=output/'requests'/slot['id'];role=slot['role']
            if role in card['roles']:
                result=clean(slot,path)
            else:
                result=execute(inference,samples[member],card=card,common=common,output=path,
                    record_root=states if role=='NATIVE_RECORD' else None,
                    checkpoint=states/f"state_before_{slot['target_update']:02d}.pt" if role in ('SINGLE_C','RESUME_D') else None,
                    target=slot['target_update'] if role in ('SINGLE_C','FULL_SINGLE_C') else None)
            if result['status']!='COMPLETE':
                raise ValueError('Rejected/incomplete request; retain denominator, no replacement')
            latent=result.pop('final_latent');result.pop('guided',None)
            tensor=output/(slot['id']+'.pt');torch.save(latent,tensor)
            result['latent_artifact']=dict(path=str(tensor),sha256=sha(tensor))
            video=Path(result['video_path'])
            result['video_artifact']=dict(path=str(video),sha256=sha(video),bytes=video.stat().st_size)
            indexed[(member,role,slot['target_update'])]=tensor
            if role in ('RESUME_D','NATIVE35') and (member,'NATIVE_RECORD',None) in indexed:
                ref=indexed[(member,'NATIVE_RECORD',None)]
                reference=torch.load(ref,map_location='cpu',weights_only=True)
                result['latent_bridge']=dict(kind='Native_allD_or_unchanged_suffix',
                    equal=torch.equal(latent,reference),max_abs_diff=float((latent.float()-reference.float()).abs().max()))
            if role=='FULL_SINGLE_C':
                ref=indexed[(member,'SINGLE_C',slot['target_update'])]
                reference=torch.load(ref,map_location='cpu',weights_only=True)
                result['latent_bridge']=dict(kind='full_single_C_vs_resumed_suffix',
                    equal=torch.equal(latent,reference),max_abs_diff=float((latent.float()-reference.float()).abs().max()))
            row.update(status='COMPLETE',result=result);save()
            if (card.get('pipeline') and role=='SINGLE_C' and slot['target_update']==card['sensitivity_steps'][-1]
                    and member not in reused_members):
                removed=0
                for t in card['sensitivity_steps']:
                    checkpoint=states/f'state_before_{t:02d}.pt'
                    removed+=checkpoint.stat().st_size;checkpoint.unlink()
                row['state_cleanup']=dict(count=len(card['sensitivity_steps']),bytes=removed,
                    retained='metrics, every-step latents, guided tensors, terminal latent and MP4')
                save()
            # Compiled sampler/unpickler cycles retain checkpoint tensors until cyclic GC.
            gc.collect()
            if card.get('host_memory_logging') and not cpu_validation:
                log_host_memory(output/'host_memory.jsonl',slot['id'])
        state['status']='COMPLETE_PENDING_RELEASE_SCORING';save()
        return state
    except BaseException as error:
        state.update(status='FAILED_NO_RETRY',error_type=type(error).__name__,error=str(error));save();raise
    finally:
        initial.restore();verify_shared_eval(net,mode)
        if caller_owned:net.forward=caller_forward
        else:vars(net).pop('forward',None)


def log_host_memory(path,request_id):
    rss=int(next(line.split()[1] for line in Path('/proc/self/status').read_text().splitlines()
        if line.startswith('VmRSS:')))*1024
    relative=next(line.split(':')[2] for line in Path('/proc/self/cgroup').read_text().splitlines()
        if 'memory' in line.split(':')[1].split(','))
    group=Path('/sys/fs/cgroup/memory')/relative.lstrip('/')
    row=dict(request_id=request_id,unix=time.time(),pid=os.getpid(),RSS_bytes=rss,
        cgroup_version=1,memory_current_source='memory.usage_in_bytes',
        memory_current_bytes=int((group/'memory.usage_in_bytes').read_text()))
    peak=group/'memory.max_usage_in_bytes'
    if peak.exists():row['memory_peak_bytes']=int(peak.read_text())
    with Path(path).open('a') as stream:stream.write(json.dumps(row)+'\n')


def main():
    parser=argparse.ArgumentParser()
    for name in ('project','stage'):parser.add_argument('--'+name,type=Path,required=True)
    for name in ('source-revision','gpu-uuid'):parser.add_argument('--'+name,required=True)
    parser.add_argument('--manifest',type=Path,default=HERE/'manifest.json')
    args=parser.parse_args()
    sys.path[:0]=[str(args.stage/'src'),str(args.stage/'scripts'),str(args.project/'runtime'),
        str(args.project/'runtime/packages/cosmos-oss'),str(args.project/'runtime/packages/cosmos-cuda')]
    from wcomr.gpu_budget_pool_v2 import sha
    from wcomr.history104_storage_r2 import storage_for
    from wcomr.wc73_exclusive_r1 import runner_context_gate
    from run_cara_budget_calibration_r1 import validate_runner_handoff
    read=lambda path:json.loads(Path(path).read_text())
    launch=read(args.stage/'GPU-launch.json');reg=read(args.stage/'registration.json')
    card=read(args.manifest)
    if (launch['run_id']!=card['run_id'] or launch['source_revision']!=args.source_revision
            or launch['gpu_uuid']!=args.gpu_uuid or launch['billed_limit_GPUh']!=card['quote']['hard_GPUh']
            or launch['scope_sha256']!=card['scope_sha256']):
        raise ValueError('Exact Phase2 admitted source/run/budget required')
    if any(sha(args.stage/name)!=digest for name,digest in reg['payload_sha256'].items()):
        raise ValueError('Admitted source differs')
    if any(sha(args.project/'runtime'/name)!=digest for name,digest in reg['runtime_source_sha256'].items()):
        raise ValueError('Admitted runtime source differs')
    envelope=read(args.stage/'central-reservation.json')
    if envelope['job']['job_id']!=card['run_id'] or envelope['job']['launch_id']!=launch['launch_id']:
        raise ValueError('Exact single central reservation required')
    command=[sys.executable,str(HERE/'runner.py'),'--project',str(args.project),'--stage',str(args.stage),
        '--manifest',str(args.manifest),'--source-revision',args.source_revision,'--gpu-uuid',args.gpu_uuid]
    validate_runner_handoff(args.stage,launch,sha(args.stage/'GPU-launch.json'),command)
    runner_context_gate(args.project,args.stage,args.gpu_uuid)
    import torch
    torch.set_num_threads(2)
    from cosmos_predict2.config import SetupArguments,InferenceArguments
    import cosmos_predict2.inference as im
    from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
    from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf
    from cosmos_oss.init import init_environment,init_output_dir,cleanup_environment
    from wcomr.runtime_config import install_core_inference_registration
    storage=storage_for(args.stage);storage.check()
    setup=SetupArguments(**{**read(args.stage/'configs/f1_setup.json'),
        'keep_going':True,'worldcache_enabled':True,'output_dir':str(storage.output)})
    if setup.disable_guardrails or setup.use_torch_compile or setup.offload_diffusion_model:
        raise ValueError('Original guarded, uncompiled resident-model setup required')
    samples={r['name']:InferenceArguments(**{k:v for k,v in r.items() if k!='partition'}) for r in card['inputs']}
    init_environment();init_output_dir(storage.output,profile=False)
    try:
        install_core_inference_registration(setup.model,setup.experiment)
        inference=im.Inference(setup)
        if torch.__version__!='2.7.1+cu128' or len(inference.pipe.model.net.blocks)!=28:
            raise ValueError('CAL35 production Torch and 28-block model required')
        common=dict(runtime=args.project/'runtime',wc=wc,rf=rf,inference_module=im,
            expected_shape=read(args.stage/'configs/wc_ra_comparison_production_r2_20261010.json')['expected_real_shape'])
        collect_loaded(inference,samples,card,common,storage.output,storage,
            read(args.stage/'manifests/wc_h0_eval_mode_contract_20261003.json')['module_types'])
    finally:
        cleanup_environment()


if __name__=='__main__':main()
