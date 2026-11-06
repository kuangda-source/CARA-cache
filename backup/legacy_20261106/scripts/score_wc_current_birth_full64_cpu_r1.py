#!/usr/bin/env python3
"""Score every compatible slot after whole64 GPU and original raw CPU exit."""
import argparse
import gzip
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import time


def main():
    p=argparse.ArgumentParser()
    for n in ('project','stage'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
        TORCH_HOME='/home/gaokuangda/.cache/torch',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
    sys.path.insert(0,str(a.stage/'src'))
    from wcomr.lpips_resource_identity import audit,sha
    from wcomr.current_birth_real_production_r1 import COUNTS,RUN,CONFIG
    from wcomr.current_birth_full64_scores_r1 import pairing_slots,actual_costs,summarize
    from wcomr.rv0_video_reader import decoded_video
    reg=json.loads((a.stage/'score-preregistration.json').read_text());launch=reg['original_launch']
    if (reg['scope_counts']!=COUNTS or reg['maximum_pairs']!=64 or reg['frames_per_pair']!=93
        or launch['run_id']!=RUN or launch['planned_scope']!=COUNTS
        or {n:sha(a.stage/n) for n in reg['payload_sha256']}!=reg['payload_sha256']):
        raise ValueError('Frozen complete64 scoring scope and original payload required')
    gpu_stage=Path(launch['stage']);post=Path(launch['post_CPU_stage']);out=a.project/'outputs'/RUN
    source=out/'diagnostic/receipt.json';result_path=post/'result.json'
    supervisor=json.loads((out/'supervisor.json').read_text());cpu=json.loads((post/'receipt.json').read_text())
    raw=json.loads(result_path.read_text());runner=json.loads(source.read_text())
    pids=[launch['supervisor_pid'],supervisor['child_pid'],launch['post_CPU_pid'],cpu['child_pid']]
    c=json.loads((gpu_stage/CONFIG).read_text())
    if (any(Path('/proc/'+str(pid)).exists() for pid in pids)
        or supervisor['pid']!=launch['supervisor_pid'] or cpu['pid']!=launch['post_CPU_pid']
        or supervisor['exit_code']!=0 or cpu['exit_code']!=0 or cpu['child_exit_code']!=0
        or raw['status']!='CURRENT_BIRTH_FULL64_RAW_CPU_PASS_NOT_FIDELITY_SCORE' or raw['exit_code']!=0
        or sha(result_path)!=cpu['result_sha256'] or raw['runner_sha256']!=sha(source)
        or raw['source_revision']!=runner['source_revision'] or raw['source_revision']!=launch['source_revision']
        or raw['CUDA_initialized'] or raw['GPU_submissions'] or raw['budget_written']
        or runner['config']!=c or c['preregistration']['scope_counts']!=COUNTS
        or sha(gpu_stage/CONFIG)!=launch['config_sha256']
        or {n:sha(gpu_stage/n) for n in c['payload_sha256']}!=c['payload_sha256']
        or not raw['no_P_RA_and_OFF_exact_and_full_GEMM_reference_verified']
        or (raw['actual_all_guided_tensors_reloaded'],raw['actual_all_final_latents_reloaded'],
            raw['accepted_new_videos'],raw['Native_videos_rechecked'])!=(2304,64,64,4)):
        raise ValueError('Original whole64 GPU/raw CPU source and terminal evidence required')
    slots=pairing_slots(raw['pairing']);planned=[s for s in slots if s['compatible']]
    files={art['path']:art for s in slots for art in (s['video_artifact'],s['Native_artifact'])}
    def verify_files():
        for name,v in files.items():
            path=Path(name).resolve()
            if (not path.is_relative_to((a.project/'outputs').resolve())
                or path.stat().st_size!=v['bytes'] or sha(path)!=v['sha256']):
                raise ValueError('Original complete64 or reused Native video bytes changed')
    verify_files();costs=actual_costs(runner)
    resource=a.project/'.sync/wc-rv0-lpips-resource-v2'
    metric_sha=reg['payload_sha256']['src/wcomr/rv0_lpips.py']
    if any(reg['payload_sha256'][n]!=c['payload_sha256'][n]
        for n in ('src/wcomr/rv0_lpips.py','src/wcomr/rv0_video_reader.py')):
        raise ValueError('Use the original frozen all93 metric and reader')
    identity=audit(resource,metric_sha);sys.path.insert(0,str(resource/'site'))
    legacy_proof=json.loads((a.stage/reg['legacy_score_proof_ref']).read_text())
    if not legacy_proof['independent_checks']['success']:
        raise ValueError('Original complete32 score proof required for legacy comparisons')
    legacy_file=legacy_proof['files']['result']['local_path']
    legacy_raw=gzip.decompress((a.stage/legacy_file).read_bytes())
    import hashlib
    if hashlib.sha256(legacy_raw).hexdigest()!=legacy_proof['files']['result']['sha256']:
        raise ValueError('Original legacy score bytes changed')
    legacy=json.loads(legacy_raw)
    if legacy['actual_resource_identity']!=identity:
        raise ValueError('Legacy and current score require the same actual offline metric resources')
    import torch
    if torch.cuda.is_initialized():raise ValueError('Full64 CPU score unexpectedly initialized CUDA')
    def forbidden(*args,**kwargs):raise RuntimeError('Full64 CPU score forbids CUDA/downloads')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden;torch.set_num_threads(2)
    import lpips
    from wcomr.rv0_lpips import PROTOCOL,score_pair
    if (PROTOCOL!=identity['protocol'] or importlib.metadata.version('lpips')!='0.1.4'
        or Path(lpips.__file__).resolve()!=(resource/'site/lpips/__init__.py').resolve()):
        raise ValueError('Original actual CPU metric origin/version/protocol differs')
    target=a.stage/'result.json';assert not target.exists()
    record={'status':'CURRENT_BIRTH_FULL64_ALL93_CPU_SCORING_STARTED','pairs':[],
        'original_launch':launch,'original_PIDs_absent':pids,'original_scope':COUNTS,
        'original_runner_receipt_sha256':sha(source),'original_raw_audit_sha256':sha(result_path),
        'complete_pairing':raw['pairing'],'complete_actual_costs':costs,
        'maximum_pairs':64,'available_planned_pairs':len(planned),
        'incompatible_slots_retained':[s for s in slots if not s['compatible']],
        'actual_resource_identity':identity,'payload_sha256':reg['payload_sha256'],
        'legacy_score_proof_sha256':sha(a.stage/reg['legacy_score_proof_ref']),
        'legacy_score_native_sha256':legacy_proof['files']['result']['sha256'],
        'metric_protocol':{k:v for k,v in PROTOCOL.items() if k not in ('benefit','policy')},
        'budget_before_sha256':sha(a.project/'reports/budget.json'),'GPU_submissions':0,'ledger_written':False,
        'new_generation':False,'clean_speed_claim':False,'physics_or_semantics_or_independent_confirmation_claim':False}
    def save():
        tmp=target.with_suffix('.tmp');tmp.write_text(json.dumps(record,indent=2,allow_nan=False)+'\n');tmp.replace(target)
    started=time.perf_counter();save()
    try:
        model=lpips.LPIPS(net='alex',version='0.1',spatial=False,verbose=False).cpu().eval()
        for parameter in model.parameters():parameter.requires_grad_(False)
        for slot in planned:
            tick=time.perf_counter();ref=slot['Native_artifact'];candidate=slot['video_artifact']
            with decoded_video(ref['path']) as left,decoded_video(candidate['path']) as right:
                score=score_pair(left,right,model,reference_sha256=ref['sha256'],candidate_sha256=candidate['sha256'])
            record['pairs'].append({'strategy':slot['strategy'],'sample_name':slot['sample_name'],'method':slot['method'],
                'reference':ref,'candidate':candidate,'score':score,'CPU_wall_seconds':time.perf_counter()-tick});save()
            print(json.dumps({'strategy':slot['strategy'],'sample_name':slot['sample_name'],'method':slot['method'],
                'completed_pairs':len(record['pairs']),'available_planned_pairs':len(planned)}),flush=True)
        record['summary']=summarize(record['pairs'],raw['pairing'],costs,legacy)
        verify_files()
        if (sha(source)!=record['original_runner_receipt_sha256'] or sha(result_path)!=record['original_raw_audit_sha256']
            or audit(resource,metric_sha)!=identity or sha(a.project/'reports/budget.json')!=record['budget_before_sha256']):
            raise ValueError('Original source, metric resources or budget changed during CPU scoring')
        record['status']='CURRENT_BIRTH_FULL64_COMPLETE_AVAILABLE_ALL93_FIDELITY_NOT_CLEAN_SPEED'
    except BaseException as error:
        record.update(status='CURRENT_BIRTH_FULL64_SCORE_FAILED_COMPLETE_SCOPE_RETAINED',error_type=type(error).__name__,error=str(error));raise
    finally:
        record.update(CPU_wall_seconds=time.perf_counter()-started,CUDA_initialized=torch.cuda.is_initialized(),
            budget_after_sha256=sha(a.project/'reports/budget.json'),
            metric_packages={n:importlib.metadata.version(n) for n in ('torch','numpy','lpips')});save()
    print(json.dumps({'status':record['status'],'scored_pairs':len(record['pairs']),'registered_paths':64}))


if __name__=='__main__':main()
