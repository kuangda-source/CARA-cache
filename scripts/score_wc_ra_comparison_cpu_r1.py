#!/usr/bin/env python3
"""All available method/Native full93 losses after original GPU/raw-audit exit."""
import argparse
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
    from wcomr.cfg_ra_comparison_scores import summarize,NAMES,METHODS
    from wcomr.rv0_video_reader import decoded_video
    reg=json.loads((a.stage/'score-preregistration.json').read_text())
    if reg['sample_names']!=NAMES or reg['methods']!=METHODS or reg['maximum_pairs']!=6 or reg['frames_per_pair']!=93:
        raise ValueError('Complete two-scene three-method all93 scoring scope required')
    if {n:sha(a.stage/n) for n in reg['payload_sha256']}!=reg['payload_sha256']:
        raise ValueError('Actual scoring source payload changed')
    launch=reg['original_launch'];gpu_stage=Path(launch['stage']);post=Path(launch['post_CPU_stage'])
    out=a.project/'outputs'/launch['run_id'];source=out/'diagnostic/receipt.json'
    supervisor=json.loads((out/'supervisor.json').read_text());cpu=json.loads((post/'receipt.json').read_text())
    result_path=post/'result.json';raw=json.loads(result_path.read_text());runner=json.loads(source.read_text())
    pids=[launch['supervisor_pid'],supervisor['child_pid'],launch['post_CPU_pid'],cpu['child_pid']]
    if (any(Path('/proc/'+str(x)).exists() for x in pids) or supervisor['exit_code']!=0 or cpu['exit_code']!=0
            or cpu['child_exit_code']!=0 or supervisor['pid']!=launch['supervisor_pid'] or cpu['pid']!=launch['post_CPU_pid']
            or sha(result_path)!=cpu['result_sha256'] or sha(source)!=raw['runner_receipt_sha256']
            or sha(gpu_stage/'ra-comparison-config.json')!=launch['config_sha256'] or raw['config_sha256']!=launch['config_sha256']
            or raw['status']!='REAL_RA_COMPARISON_FULL_RAW_CPU_AUDIT_NOT_QUALITY_OR_CLEAN_LATENCY'
            or not raw['all_accepted_complete93_videos_and_raw_vector_artifacts_verified']
            or raw['source_revision']!=runner['source_revision'] or raw['source_revision']!=launch['source_revision']
            or raw['CUDA_initialized'] or raw['GPU_submissions']):
        raise ValueError('Complete original GPU and raw CPU terminal evidence required')
    c=json.loads((gpu_stage/'ra-comparison-config.json').read_text())
    if (runner['config']!=c or c['preregistration']['scope_counts']!=launch['planned_scope']
            or {n:sha(gpu_stage/n) for n in c['payload_sha256']}!=c['payload_sha256']):
        raise ValueError('Complete original method configuration/source changed')
    refs=runner['comparison']['references'];pairs=raw['matched_fidelity_pairs']
    expected=[(r['sample_name'],m) for r in refs if r['outcome']=='ACCEPTED' for m in METHODS]
    if [(q['sample_name'],q['method']) for q in pairs]!=expected:
        raise ValueError('Complete available Native-relative six-pair order differs')
    files={v['path']:v for v in raw['videos']}
    def verify_files():
        for n,v in files.items():
            path=Path(n).resolve()
            if (not path.is_relative_to((out/'diagnostic').resolve())
                    or path.stat().st_size!=v['bytes'] or sha(path)!=v['sha256']):
                raise ValueError('Original complete video artifact changed')
    verify_files()
    resource=a.project/'.sync/wc-rv0-lpips-resource-v2'
    metric_sha=reg['payload_sha256']['src/wcomr/rv0_lpips.py']
    if reg['payload_sha256']['src/wcomr/rv0_video_reader.py']!=c['payload_sha256']['src/wcomr/rv0_video_reader.py']:
        raise ValueError('Use the already bound original full-frame video reader')
    identity=audit(resource,metric_sha);sys.path.insert(0,str(resource/'site'))
    import torch
    if torch.cuda.is_initialized():raise ValueError('CPU metric unexpectedly initialized CUDA')
    def forbidden(*args,**kwargs):raise RuntimeError('Full93 CPU scoring forbids CUDA/downloads')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden;torch.set_num_threads(2)
    import lpips
    from wcomr.rv0_lpips import PROTOCOL,score_pair
    if (PROTOCOL!=identity['protocol'] or importlib.metadata.version('lpips')!='0.1.4'
            or Path(lpips.__file__).resolve()!=(resource/'site/lpips/__init__.py').resolve()):
        raise ValueError('Frozen actual offline CPU metric origin/protocol differs')
    target=a.stage/'result.json'
    if target.exists():raise ValueError('Preserve original scoring identity')
    record={'status':'RA_FULL_COMPARISON_ALL93_CPU_SCORING_STARTED','pairs':[],
        'original_launch':launch,'original_PIDs_absent':pids,'references':refs,
        'original_runner_receipt_sha256':sha(source),'original_raw_audit_sha256':sha(result_path),
        'original_scope':launch['planned_scope'],'maximum_pairs':6,'available_planned_pairs':len(pairs),
        'metric_protocol':{k:v for k,v in PROTOCOL.items() if k not in ('benefit','policy')},
        'actual_resource_identity':identity,'payload_sha256':reg['payload_sha256'],
        'budget_before_sha256':sha(a.project/'reports/budget.json'),'GPU_submissions':0,'ledger_written':False,
        'original_method_actions_and_costs':raw['actual_method_actions_and_costs'],
        'CUDA_initialized':False,'new_generation':False,'clean_speed_claim':False,
        'physics_or_semantics_or_independent_confirmation_claim':False}
    def save():
        temp=target.with_suffix('.tmp');temp.write_text(json.dumps(record,indent=2,allow_nan=False)+'\n');temp.replace(target)
    started=time.perf_counter();save()
    try:
        model=lpips.LPIPS(net='alex',version='0.1',spatial=False,verbose=False).cpu().eval()
        for parameter in model.parameters():parameter.requires_grad_(False)
        for q in pairs:
            tick=time.perf_counter()
            with decoded_video(q['reference']['path']) as left,decoded_video(q['candidate']['path']) as right:
                score=score_pair(left,right,model,reference_sha256=q['reference']['sha256'],candidate_sha256=q['candidate']['sha256'])
            record['pairs'].append({**q,'score':score,'CPU_wall_seconds':time.perf_counter()-tick});save()
            print(json.dumps({'sample_name':q['sample_name'],'method':q['method'],'mean_LPIPS':score['mean_LPIPS'],
                'completed_pairs':len(record['pairs']),'available_planned_pairs':len(pairs)}),flush=True)
        record['summary']=summarize(record['pairs'],refs,raw['actual_method_actions_and_costs'])
        verify_files()
        if sha(source)!=record['original_runner_receipt_sha256'] or sha(result_path)!=record['original_raw_audit_sha256']:
            raise ValueError('Original terminal source/evidence changed during CPU scoring')
        if audit(resource,metric_sha)!=identity:raise ValueError('Offline metric resource changed during scoring')
        record['status']='RA_FULL_COMPARISON_COMPLETE_AVAILABLE_ALL93_FIDELITY_AND_COST_NOT_CLEAN_SPEED'
    except BaseException as error:
        record.update(status='RA_SCORE_FAILED_COMPLETE_SCOPE_RETAINED',error_type=type(error).__name__,error=str(error));raise
    finally:
        record.update(CPU_wall_seconds=time.perf_counter()-started,CUDA_initialized=torch.cuda.is_initialized(),
            budget_after_sha256=sha(a.project/'reports/budget.json'),metric_packages={n:importlib.metadata.version(n) for n in ('torch','numpy','lpips')})
        save()
    print(json.dumps({'status':record['status'],'scored_pairs':len(record['pairs']),'summary':record['summary']['scene_equal_aggregates']}))


if __name__=='__main__':main()
