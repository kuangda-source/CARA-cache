#!/usr/bin/env python3
"""Original eight W1 CAL rows, up to fourteen complete93 Native-relative losses."""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import time


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['project','stage','receipt','terminal-audit','output']:
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise ValueError('Preserve original scoring; no overwrite')
    os.environ.update(CUDA_VISIBLE_DEVICES='',TORCH_HOME='/home/gaokuangda/.cache/torch',
                      OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
    sys.path.insert(0,str(args.stage/'src'))
    from wcomr.w1_native_reference_execution import sha,validate_stage
    from wcomr.w1_native_reference_evaluation import reference_plan,summarize_scores
    from wcomr.rv0_video_reader import decoded_video
    config=json.loads((args.stage/'native-prod-config.json').read_text())
    terminal=json.loads(args.terminal_audit.read_text())
    if (terminal['status']!='FIVE_REFERENCE_TERMINAL_AVAILABLE_FULL93_AUDIT_PASS_NOT_QUALITY'
            or terminal['run_id']!=config['run_id'] or terminal['runner_receipt_sha256']!=sha(args.receipt)
            or terminal['config_sha256']!=sha(args.stage/'native-prod-config.json')
            or not terminal['original_pids_absent'] or not terminal['global_lock_free']
            or terminal['budget']!=json.loads((args.project/'reports/budget.json').read_text())):
        raise ValueError('Original full terminal/source/cost/release audit required')
    validate_stage(args.project,args.stage,args.project/'runtime',config,selected=True)
    receipt=json.loads(args.receipt.read_text());draft=json.loads((args.stage/'w1-reference-draft.json').read_text())
    plan=reference_plan(receipt,draft,args.project/'outputs'/config['run_id']/'diagnostic/artifacts')
    if plan!=terminal['reference_plan']:raise ValueError('Audited accepted/rejected/partial reference plan changed')
    resource=json.loads((args.stage/config['lpips_resource_audit']['path']).read_text())
    def verify_files():
        for pair in plan['pairs']:
            for item in [pair['reference'],pair['candidate']]:
                if sha(item['path'])!=item['sha256']:raise ValueError('Frozen paired video changed')
    verify_files()
    site=args.project/config['lpips_resource_stage']/'site';sys.path.insert(0,str(site))
    import torch
    if torch.cuda.is_initialized():raise ValueError('CPU scoring created CUDA context')
    def forbidden(*a,**k):raise RuntimeError('No CUDA/download in full-video CPU scoring')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden;torch.set_num_threads(2)
    import lpips
    package=Path(lpips.__file__).parent
    if (importlib.metadata.version('lpips')!='0.1.4' or package.resolve()!=(site/'lpips').resolve()
            or sha(package/'weights/v0.1/alex.pth')!=resource['LPIPS_linear_weight_sha256']
            or sha('/home/gaokuangda/.cache/torch/hub/checkpoints/alexnet-owt-7be5be79.pth')!=resource['AlexNet_sha256']):
        raise ValueError('Frozen isolated metric package/backbone differs')
    for name,digest in resource['installed_source_sha256'].items():
        if sha(package/name)!=digest:raise ValueError('Frozen isolated metric code changed')
    from wcomr.rv0_lpips import PROTOCOL,score_pair
    if PROTOCOL!=resource['protocol']:raise ValueError('Frozen full-frame metric protocol differs')
    result={'status':'CPU_SCORING_STARTED','original_denominator':[8,7,1],'planned_references':5,
        'maximum_matched_scenes':7,'available_loss_pairs':len(plan['pairs']),'pairs':[],'reference_plan':plan,
        'metric_protocol':{k:v for k,v in PROTOCOL.items() if k not in ['benefit','policy','formal_RV_training_labels','physics_or_quality_noninferiority']},
        'policy':'W1_DEV_CAL_WC_MINUS_W1_NEGATIVES_RETAINED_MISSING_NOT_ZERO',
        'runner_receipt_sha256':sha(args.receipt),'terminal_audit_sha256':sha(args.terminal_audit),
        'GPU_submissions':0,'formal_RV_training_labels':False,'clean_speed_claim':False}
    def save():
        path=args.output.with_suffix('.tmp');path.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');path.replace(args.output)
    started=time.perf_counter();save()
    try:
        model=lpips.LPIPS(net='alex',version='0.1',spatial=False,verbose=False).cpu().eval()
        for parameter in model.parameters():parameter.requires_grad_(False)
        for pair in plan['pairs']:
            a,b=pair['reference'],pair['candidate']
            with decoded_video(a['path']) as left,decoded_video(b['path']) as right:
                score=score_pair(left,right,model,reference_sha256=a['sha256'],candidate_sha256=b['sha256'])
            result['pairs'].append({**pair,'score':score});save()
        result['summary']=summarize_scores(result['pairs'],plan);verify_files()
        if torch.cuda.is_initialized():raise ValueError('CPU scoring created CUDA context')
        result['status']='W1_AVAILABLE_FULL93_NATIVE_FIDELITY_SCORES_COMPLETE_NOT_INDEPENDENT_CONFIRMATION'
    except BaseException as error:
        result.update(status='TECH_BLOCKED_CPU_SCORING_ORIGINAL_DENOMINATOR_PRESERVED',error_type=type(error).__name__,error=str(error));raise
    finally:
        result['CPU_wall_seconds']=time.perf_counter()-started;result['CUDA_initialized']=torch.cuda.is_initialized()
        result['metric_packages']={n:importlib.metadata.version(n) for n in ['torch','numpy','lpips']}
        result['analysis_code_sha256']=sha(Path(__file__));result['reader_code_sha256']=sha(args.stage/'src/wcomr/rv0_video_reader.py');save()
    print(json.dumps({'status':result['status'],'loss_pairs':len(result['pairs']),
                      'matched_scenes':result['summary']['matched_accepted_scene_count']}))


if __name__=='__main__':main()
