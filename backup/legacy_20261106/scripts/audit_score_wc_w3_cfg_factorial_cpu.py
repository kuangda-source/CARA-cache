#!/usr/bin/env python3
"""Current four-cell controls and seven full videos; fixed reference contrasts."""
import argparse
import fcntl
import gzip
import importlib.metadata
import json
import math
import os
from pathlib import Path
import subprocess
import sys

def prepare_metric(project,stage):
    old=json.loads((stage/'onset-config.json').read_text());site=project/old['lpips_resource_stage']/'site';sys.path.insert(0,str(site))
    from wcomr.rv0_paired_cfg_production import sha
    from wcomr.rv0_placement_v2_execution import validate_preparation
    resource=validate_preparation(stage,json.loads((stage/'placement-config.json').read_text()))['lpips_resource']
    import torch
    assert not torch.cuda.is_initialized()
    def forbidden(*a,**k):raise RuntimeError('CPU scoring forbids CUDA/downloads')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden;torch.set_num_threads(2)
    import lpips
    package=Path(lpips.__file__).parent
    assert importlib.metadata.version('lpips')=='0.1.4' and package.resolve()==(site/'lpips').resolve()
    assert sha(package/'weights/v0.1/alex.pth')==resource['LPIPS_linear_weight_sha256']
    assert sha('/home/gaokuangda/.cache/torch/hub/checkpoints/alexnet-owt-7be5be79.pth')==resource['AlexNet_sha256']
    assert all(sha(package/n)==h for n,h in resource['installed_source_sha256'].items())
    from wcomr.rv0_lpips import PROTOCOL
    assert PROTOCOL==resource['protocol']
    metric=lpips.LPIPS(net='alex',version='0.1',spatial=False,verbose=False).cpu().eval()
    for parameter in metric.parameters():parameter.requires_grad_(False)
    return metric,PROTOCOL

def main():
    p=argparse.ArgumentParser()
    for name in ('project','stage'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--output',type=Path);p.add_argument('--prepare-only',action='store_true');a=p.parse_args()
    os.environ.update(CUDA_VISIBLE_DEVICES='',TORCH_HOME='/home/gaokuangda/.cache/torch',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    sys.path.insert(0,str(a.stage/'src'))
    from wcomr.rv0_cfg_factorial_production import validate,read_prior,sha
    c,_=validate(a.project,a.stage)
    metric,protocol=prepare_metric(a.project,a.stage)
    import torch
    if a.prepare_only:
        assert not torch.cuda.is_initialized()
        print(json.dumps({'status':'CFG_FACTORIAL_FROZEN_FULL93_METRIC_CPU_PREPARATION_PASS_NOT_SCORE',
            'CUDA_initialized':False,'GPU_submissions':0,'metric_protocol':protocol,'scored_videos':0}));return
    assert a.output and not a.output.exists()
    run=a.project/'outputs'/c['execution_run_id'];sup=json.loads((run/'supervisor.json').read_text())
    r=json.loads((run/'diagnostic/receipt.json').read_text());budget=json.loads((a.project/'reports/budget.json').read_text())
    assert sup['exit_code']==0 and r['status']=='CFG_FACTORIAL_GPU_CORE_COMPLETE_FIXED_REFERENCE_AUDIT_SCORE_PENDING'
    assert sup['source_revision']==r['source_revision'] and budget==sup['budget_after']
    assert math.isclose(budget['used_gpu_hours'],sup['budget_before']['used_gpu_hours']+sup['wall_seconds']/3600,abs_tol=1e-12)
    assert all(not Path('/proc/'+str(pid)).exists() for pid in [sup['pid'],sup['child_pid']])
    assert not sup['release']['pids'] and sup['release']['memory_used_mib']<=1024
    with (a.project/'.sync/f1.lock').open('a+') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True)
    assert not any(x.split(',')[0].strip()==sup['gpu_uuid'] for x in apps.splitlines())
    from wcomr.rv0_cfg_factorial_evaluation import verify_factorial_row
    from wcomr.rv0_video_reader import decoded_video,probe_video
    from wcomr.rv0_lpips import score_pair
    assert len(r['cases'])==1 and r['cases'][0]['seed']==2
    row=r['cases'][0]['WC']['requests'][0]
    verdict=verify_factorial_row(row,26)
    decoded={d['label']:d['artifact'] for d in row['decoded_children']}
    native=c['preregistration']['existing_Native'];files=[row['artifact']]+list(decoded.values())+[native]
    result={'status':'CFG_FACTORIAL_CPU_AUDIT_AND_SCORE_STARTED','runner_sha256':sha(run/'diagnostic/receipt.json'),
        'config_sha256':sha(a.stage/'factorial-config.json'),'budget':budget,'planned_scope':c['preregistration']['scope_counts'],
        'verdict':verdict,'fixed_reference_estimand':'CURRENT_CARD_SHARED_STATE_FIXED_REGISTERED_NATIVE_REFERENCE','historical_full_state_acceptance':False,'videos':[],'losses':{},'signed_pairs':[],
        'metric_protocol':{k:v for k,v in protocol.items() if k not in {'benefit','policy'}},
        'GPU_submissions':0,'CUDA_initialized':False,'independent_CONF':False,'clean_speed_measurement':False,
        'formal_single_action_RV_labels':False,'physics_or_semantic_acceptance':False}
    def save():
        tmp=a.output.with_suffix('.tmp');tmp.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');tmp.replace(a.output)
    save()
    assert len(files)==7 and len({item['path'] for item in files})==7
    for item in files:
        path=Path(item['path']);assert path.stat().st_size==item['bytes'] and sha(path)==item['sha256']
        if item is not native:assert (run/'diagnostic').resolve() in path.resolve().parents
        meta=probe_video(path)
        with decoded_video(path) as frames:assert sum(1 for _ in frames)==93
        result['videos'].append({**item,'probe':meta,'full93_decode':True});save()
    from wcomr.rv0_cfg_factorial_scores import CELLS, factorial_summary
    for label in CELLS:
        item=decoded[label+'_first']
        with decoded_video(native['path']) as left,decoded_video(item['path']) as right:
            result['losses'][label]=score_pair(left,right,metric,reference_sha256=native['sha256'],candidate_sha256=item['sha256'])
        save()
    controls={x['label']:x for x in row['children']}
    costs={label:[controls[label+'_'+n]['record']['control_wall_seconds'] for n in ('first','second')] for label in CELLS}
    counts={}
    for label in CELLS:
        deep=controls[label+'_first']['deep'];prefix=row['deep'][:44]
        counts[label]={'prefix_CFG':[sum(x>0 for x in prefix[slot::2]) for slot in (0,1)],
            'current_CFG':[int(x>0) for x in deep[:2]],
            'future_CFG':[sum(x>0 for x in deep[2:][slot::2]) for slot in (0,1)],
            'whole_CFG':[sum(x>0 for x in (prefix+deep)[slot::2]) for slot in (0,1)]}
    result['factorial_summary']=factorial_summary(result['losses'],counts,costs)
    result['signed_pairs']=result['factorial_summary']['contrasts']
    assert not torch.cuda.is_initialized()
    result['status']='CFG_FACTORIAL_COMPLETE_FULL93_AUDIT_FOUR_LOSSES_FOUR_PAIRS_ONE_INTERACTION_NOT_CONF';save()

if __name__=='__main__':main()
