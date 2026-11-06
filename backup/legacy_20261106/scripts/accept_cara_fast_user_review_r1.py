"""Recover one original packet mapping and record the user's complete diagnostic."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from wcomr.cara_fast_b36_figures_r1 import verify_analysis
from wcomr.cara_fast_review_r1 import plan_review
from wcomr.cara_fast_review_analysis_r1 import summarize_response


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser()
    for name in ('analysis','coordinator','response','output'):p.add_argument('--'+name,type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():raise ValueError('Fresh review acceptance receipt required')
    if args.coordinator.stat().st_mode & 0o077:raise ValueError('Private coordinator must remain0600')
    analysis,analysis_sha=verify_analysis(args.analysis)
    coordinator=json.loads(args.coordinator.read_bytes())
    descriptor=analysis['input_file_sha256']['manifest'];manifest_path=ROOT/descriptor['path']
    if sha(manifest_path)!=descriptor['sha256']:raise ValueError('Original score manifest changed')
    plan=plan_review(analysis,json.loads(manifest_path.read_bytes()),bytes.fromhex(coordinator['nonce']))
    expected=dict(schema='CARA_REVIEW_COORDINATOR_PRIVATE_R1',nonce=coordinator['nonce'],
        analysis_sha256=analysis_sha,manifest_sha256=descriptor['sha256'],**plan)
    if coordinator!=expected:raise ValueError('Original case mapping differs; do not reassign labels')
    response=json.loads(args.response.read_bytes());result=summarize_response(plan,response)
    result.update(observed_unix=time.time(),response_created_at=response['created_at'],
        raw_response_sha256=sha(args.response),raw_response_retained_privately=True,
        original_analysis_sha256=analysis_sha,original_manifest_sha256=descriptor['sha256'],
        coordinator_sha256=sha(args.coordinator),reviewer_alias_retained_privately=True,
        source_sha256={n:sha(ROOT/n) for n in ('scripts/accept_cara_fast_user_review_r1.py',
            'src/wcomr/cara_fast_review_analysis_r1.py')})
    with args.output.open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({k:result[k] for k in ('status','positions','reviewer_count',
        'self_control_all_axes_no_difference','full_pair_playback_recorded','GPU_submissions')}))


if __name__=='__main__':main()
