#!/usr/bin/env python3
"""Read-only five-reference source/cost/release and available full-video audit."""
import argparse
import fcntl
import json
from pathlib import Path
import sys
import time


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['project','stage','output']:parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--expected-source',required=True)
    args=parser.parse_args()
    if args.output.exists():raise ValueError('Preserve original audit; no overwrite')
    sys.path.insert(0,str(args.stage/'src'))
    from wcomr.w1_native_reference_execution import sha,validate_stage,audit_settlement
    from wcomr.w1_native_reference_evaluation import reference_plan
    from wcomr.rv0_video_reader import probe_video,decoded_video
    config=json.loads((args.stage/'native-prod-config.json').read_text())
    root=args.project/'outputs'/config['run_id'];path=root/'diagnostic/receipt.json'
    supervisor=json.loads((root/'supervisor.json').read_text());receipt=json.loads(path.read_text())
    budget=json.loads((args.project/'reports/budget.json').read_text())
    pids=audit_settlement(supervisor,receipt,config,budget,args.expected_source)
    if (receipt['scope']!=config or receipt['toy_fixture'] or 'cleanup_error' in receipt
            or any(Path('/proc/'+str(pid)).exists() for pid in pids)):
        raise ValueError('Original source/scope/process/cleanup differs')
    with (args.project/'.sync/f1.lock').open('a+') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    stage_check=validate_stage(args.project,args.stage,args.project/'runtime',config,selected=True)
    draft=json.loads((args.stage/'w1-reference-draft.json').read_text())
    plan=reference_plan(receipt,draft,root/'diagnostic/artifacts')
    if plan['complete_five_attempted'] and (supervisor['exit_code']!=0 or receipt['status']!=
            'FIVE_REFERENCES_ATTEMPTED_REQUIRES_TERMINAL_AND_CPU_VIDEO_AUDIT'):
        raise ValueError('Complete-five completion differs from original termination')
    files={p['path']:p for pair in plan['pairs'] for p in [pair['reference'],pair['candidate']]}
    videos=[]
    for item in files.values():
        video=Path(item['path'])
        if sha(video)!=item['sha256'] or ('bytes' in item and video.stat().st_size!=item['bytes']):
            raise ValueError('Original available video changed')
        probe=probe_video(video)
        with decoded_video(video) as frames:decoded=sum(1 for _ in frames)
        if decoded!=93:raise ValueError('Complete93 decode required')
        videos.append({**item,'probe':probe,'full93_decode':True})
    monitors=[json.loads(line) for line in (root/'gpu-monitor.jsonl').read_text().splitlines()]
    release=supervisor['release']
    if (not monitors or any(r['uuid']!=config['gpu_uuid'] or not set(r['pids']).issubset(pids) for r in monitors)
            or release.get('uuid')!=config['gpu_uuid'] or set(release['pids']).intersection(pids)):
        raise ValueError('Original workload monitor/release evidence differs')
    # Other users may start after our child releases. Their current GPU use is unrelated to CPU scoring.
    result={'status':'FIVE_REFERENCE_TERMINAL_AVAILABLE_FULL93_AUDIT_PASS_NOT_QUALITY',
        'run_id':config['run_id'],'source_revision':args.expected_source,'observed_unix':time.time(),
        'runner_receipt_sha256':sha(path),'config_sha256':sha(args.stage/'native-prod-config.json'),
        'supervisor_sha256':sha(root/'supervisor.json'),'original_pids_absent':True,'original_pids':pids,
        'global_lock_free':True,'budget':budget,'gpu_wall_seconds':supervisor['wall_seconds'],
        'full_five_reference_card_completed':plan['complete_five_attempted'],'reference_plan':plan,
        'stage_check':stage_check,'videos':videos,'GPU_submissions':0,'quality_or_physics_acceptance':False,
        'monitor_rows':len(monitors),'monitor_peak_mib':max(r['memory_used_mib'] for r in monitors),
        'audit_code_sha256':sha(Path(__file__))}
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':result['status'],'complete_five_attempted':plan['complete_five_attempted'],
                      'matched_scenes':plan['matched_accepted_scene_count'],'videos':len(videos)}))


if __name__=='__main__':main()
