#!/usr/bin/env python3
"""After release: source/cost/state/video audit and four full-frame CPU losses."""
import argparse
import fcntl
import hashlib
import importlib.metadata
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys


def main():
    p=argparse.ArgumentParser()
    for name in ('project','stage','output'):p.add_argument('--'+name,type=Path,required=True)
    args=p.parse_args();assert not args.output.exists()
    os.environ.update(CUDA_VISIBLE_DEVICES='',TORCH_HOME='/home/gaokuangda/.cache/torch',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
    sys.path.insert(0,str(args.stage/'src'));sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    spec=importlib.util.spec_from_file_location('d46_runner_validator',args.stage/'scripts/run_wc_w3_d46_fresh_seeds.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);config,base=m.validate(args.project,args.stage)
    run=args.project/'outputs'/config.get('execution_run_id',config['preregistration']['run_id']);sup=json.loads((run/'supervisor.json').read_text());r=json.loads((run/'diagnostic/receipt.json').read_text());budget=json.loads((args.project/'reports/budget.json').read_text())
    assert sup['exit_code']==0 and r['status']=='D46_TWO_SEEDS_GPU_CORE_COMPLETE_AUDIT_AND_SCORE_PENDING'
    assert budget==sup['budget_after'] and math.isclose(budget['used_gpu_hours'],sup['budget_before']['used_gpu_hours']+sup['wall_seconds']/3600,abs_tol=1e-12)
    assert all(not Path('/proc/'+str(pid)).exists() for pid in [sup['pid'],sup['child_pid']])
    assert not sup['release']['pids'] and sup['release']['memory_used_mib']<=1024
    with (args.project/'.sync/f1.lock').open('a+') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True)
    assert not any(x.split(',')[0].strip()==sup['gpu_uuid'] for x in apps.splitlines())
    from wcomr.rv0_d46_seed_evaluation import verify_seed_row
    from wcomr.rv0_video_reader import decoded_video,probe_video
    assert [c['seed'] for c in r['cases']]==[1,2]
    result={'status':'D46_CPU_AUDIT_AND_SCORE_STARTED','GPU_submissions':0,'CUDA_initialized':False,
        'runner_sha256':sha(run/'diagnostic/receipt.json'),'config_sha256':sha(args.stage/'seed-config.json'),
        'budget':budget,'planned_scope':config['preregistration']['scope_counts'],'cases':[],
        'independent_CONF':False,'clean_speed_measurement':False,'RV_labels':False,'physics_or_semantic_acceptance':False}
    def save():
        tmp=args.output.with_suffix('.tmp');tmp.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');tmp.replace(args.output)
    save();videos=[]
    for case in r['cases']:
        assert case['pre_Native_initial_fingerprint']==case['pre_WC_initial_fingerprint']
        native=case['native'];assert native['CFG_calls']==72 and native['solver_steps']==36 and native['block_counts']['full_calls']==72
        row=case['WC']['requests'][0];verdict=verify_seed_row(row,26);decoded={d['label']:d['artifact'] for d in row['decoded_children']}
        files=[row['artifact']]+list(decoded.values())+([native['artifact']] if native['outcome']=='ACCEPTED' else [])
        for item in files:
            path=Path(item['path']);assert path.resolve().is_relative_to((run/'diagnostic').resolve()) and path.stat().st_size==item['bytes'] and sha(path)==item['sha256']
            meta=probe_video(path)
            with decoded_video(path) as frames:assert sum(1 for _ in frames)==93
            videos.append({**item,'probe':meta,'full93_decode':True})
        result['cases'].append({'name':case['name'],'seed':case['seed'],'verdict':verdict,'Native_outcome':native['outcome'],
            'Native':native['artifact'],'BASE':decoded['BASE_first'],'REFRESH':decoded['REFRESH_first'],'losses':{},
            'control_costs':{label:[c['record']['control_wall_seconds'] for c in row['children'] if c['label'].startswith(label+'_')] for label in ('BASE','REFRESH')}})
    assert len({v['path'] for v in videos})==len(videos);result['videos']=videos;save()
    old=json.loads((base/'onset-config.json').read_text());site=args.project/old['lpips_resource_stage']/'site';sys.path.insert(0,str(site))
    from wcomr.rv0_placement_v2_execution import validate_preparation
    resource=validate_preparation(base,json.loads((base/'placement-config.json').read_text()))['lpips_resource']
    import torch
    assert not torch.cuda.is_initialized()
    def forbidden(*a,**k):raise RuntimeError('CPU scoring forbids CUDA/downloads')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden;torch.set_num_threads(2)
    import lpips
    package=Path(lpips.__file__).parent
    assert importlib.metadata.version('lpips')=='0.1.4' and package.resolve()==(site/'lpips').resolve()
    assert sha(package/'weights/v0.1/alex.pth')==resource['LPIPS_linear_weight_sha256'] and sha('/home/gaokuangda/.cache/torch/hub/checkpoints/alexnet-owt-7be5be79.pth')==resource['AlexNet_sha256']
    assert all(sha(package/n)==h for n,h in resource['installed_source_sha256'].items())
    from wcomr.rv0_lpips import score_pair,PROTOCOL
    assert PROTOCOL==resource['protocol'];result['metric_protocol']={k:v for k,v in PROTOCOL.items() if k not in {'benefit','policy'}}
    metric=lpips.LPIPS(net='alex',version='0.1',spatial=False,verbose=False).cpu().eval()
    for parameter in metric.parameters():parameter.requires_grad_(False)
    for case in result['cases']:
        if case['Native_outcome']!='ACCEPTED':
            case['score_status']='MISSING_NATIVE_REFERENCE_REJECTION_RETAINED';save();continue
        for label in ('BASE','REFRESH'):
            a,b=case['Native'],case[label]
            with decoded_video(a['path']) as left,decoded_video(b['path']) as right:
                case['losses'][label]=score_pair(left,right,metric,reference_sha256=a['sha256'],candidate_sha256=b['sha256'])
        a,b=case['losses']['BASE'],case['losses']['REFRESH'];assert a['pts']==b['pts']
        case['signed_quality']=a['mean_LPIPS']-b['mean_LPIPS']
        case['signed_diagnostic_seconds']=math.fsum(case['control_costs']['BASE'])/2-math.fsum(case['control_costs']['REFRESH'])/2
        case['improved_frames']=sum(x<y for x,y in zip(b['frame_distances'],a['frame_distances']));case['worse_frames']=sum(x>y for x,y in zip(b['frame_distances'],a['frame_distances']))
        case['score_status']='FULL93_NATIVE_RELATIVE_LOSSES_SIGNED_NEGATIVE_RETAINED';save()
    result['status']='D46_TWO_REGISTERED_SEEDS_FULL_CPU_AUDIT_AND_AVAILABLE_LOSSES_COMPLETE_NOT_CONF'
    assert not torch.cuda.is_initialized();save()


if __name__=='__main__':main()
