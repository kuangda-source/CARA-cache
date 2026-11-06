"""Observe original GPU/CPU handles; keep a recoverable terminal reader receipt."""
import argparse
import hashlib
import json
from pathlib import Path

from cara_two_card_transport_r1 import four_ssh,ssh

ROOT=Path(__file__).resolve().parents[1]
REMOTE=r'''
import hashlib,json,os,resource,signal,sys
from pathlib import Path
d=json.load(sys.stdin);project=Path('/data20t/gaokuangda/worldcache_workspace');stage=Path(d['stage'])
signal.alarm(900)
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
for name,expected in d['capture_source_sha256'].items():
 assert hashlib.sha256((stage/name).read_bytes()).hexdigest()==expected,'Capture source differs'
sys.path.insert(0,str(stage/'src'))
from wcomr.cara_fast_b36_capture_r1 import capture_terminal,capture_scores
result=(capture_terminal(project,stage,d['launch_sha256']) if d['kind']=='GPU-terminal'
        else capture_scores(project,stage,Path(d['manifest_path']),d['manifest_sha256']))
print(json.dumps(result,allow_nan=False))
'''


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--launch',type=Path,required=True)
    parser.add_argument('--score-manifest',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    assert not args.output.exists()
    launch=json.loads(args.launch.read_text())
    assert launch['host'] in ('four_card','two_card')
    names=['src/wcomr/cara_fast_b36_capture_r1.py','src/wcomr/cara_fast_b36_terminal_r1.py',
           'src/wcomr/cara_fast_b36_post_r1.py','scripts/capture_cara_fast_b36_terminal_r1.py']
    data=dict(stage=launch['stage'],kind='CPU-score' if args.score_manifest else 'GPU-terminal',
              launch_sha256=hashlib.sha256(args.launch.read_bytes()).hexdigest(),
              capture_source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in names})
    if args.score_manifest:
        data.update(manifest_path=json.loads(args.score_manifest.read_text())['manifest_path'],
                    manifest_sha256=hashlib.sha256(args.score_manifest.read_bytes()).hexdigest())
    result=(four_ssh(REMOTE,data,timeout=930) if launch['host']=='four_card'
            else ssh(REMOTE,data,docker_group=True,timeout=930))
    with args.output.open('x') as handle:
        json.dump(result,handle,indent=2,allow_nan=False)
        handle.write('\n')
    print(json.dumps({key:result.get(key) for key in ('status','launch_id','original_live_handles',
                                                    'artifact_bytes_read','scientific_rows_returned')}))


if __name__=='__main__':
    main()
