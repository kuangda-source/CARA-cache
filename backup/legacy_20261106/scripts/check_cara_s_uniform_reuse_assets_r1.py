"""Bounded two-card read-only hashes of the original sixteen video/argument pairs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from cara_two_card_transport_r1 import password

REMOTE=r'''
import hashlib,json,os,pathlib,resource,signal,sys,time
signal.alarm(120)
os.sched_setaffinity(0,{26})
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,256*1024**2))
p=json.load(sys.stdin)
roots=('/data20t/gaokuangda/worldcache_workspace/outputs/cara-fast-cal-a32-r2-20261028/',
       '/data20t/gaokuangda/worldcache_workspace/outputs/cara-fast-f19-b36-r1-20261029/')
resolved_roots={r:str(pathlib.Path(r).resolve()) for r in roots}
assert len(p['files'])==32 and len({r['path'] for r in p['files']})==32
start=time.time();rows=[]
for row in p['files']:
 path=pathlib.Path(row['path'])
 original_root=next(r for r in roots if str(path).startswith(r))
 assert '..' not in path.parts and path.resolve().is_relative_to(pathlib.Path(resolved_roots[original_root]))
 assert path.suffix in ('.mp4','.json')
 before=path.stat();assert before.st_size<=16*1024**2
 h=hashlib.sha256()
 with path.open('rb') as f:
  while True:
   b=f.read(1024**2)
   if not b:break
   h.update(b)
 after=path.stat()
 assert (before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns)
 actual=h.hexdigest()
 assert actual==row['sha256'] and (row.get('bytes') is None or after.st_size==row['bytes'])
 rows.append(dict(path=str(path),resolved_path=str(path.resolve()),bytes=after.st_size,sha256=actual,stable_during_read=True))
print(json.dumps(dict(status='ORIGINAL32_VIDEO_ARGUMENT_FILES_HASH_MATCH',host='two_card',
 started_unix=start,ended_unix=time.time(),files=rows,read_bytes=sum(r['bytes'] for r in rows),resolved_roots=resolved_roots,
 CPU_affinity=sorted(os.sched_getaffinity(0)),memory_limit_bytes=256*1024**2,
 GPU_submissions=0,ledger_written=False,active_GPU_outputs_read=False)))
'''


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--plan',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    assert not args.output.exists()
    raw=args.plan.read_bytes();plan=json.loads(raw)
    assert plan['counts']['reused_metric_positions']==12 and plan['counts']['original_reference_sources']==4
    sources=[r['source'] for r in plan['formal_matrix'] if r['mode']=='REUSE_COMPLETE_SCORE']
    sources.extend(r['source'] for r in plan['reference_sources'])
    files=[]
    for source in sources:
        files.append({k:source[k] for k in ('path','sha256','bytes')})
        files.append(dict(path=str(Path(source['path']).with_suffix('.json')),sha256=source['argument_file_sha256']))
    assert len(files)==len({r['path'] for r in files})==32
    binding=dict(status='ORIGINAL_REUSE_HASH_CHECK_INTENT',started_unix=time.time(),
        plan_ref=str(args.plan),plan_sha256=hashlib.sha256(raw).hexdigest(),expected_files=files,
        remote_code_sha256=hashlib.sha256(REMOTE.encode()).hexdigest(),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        GPU_submissions=0,ledger_written=False)
    with args.output.with_name(args.output.stem+'_binding.json').open('x') as f:
        json.dump(binding,f,indent=2);f.write('\n')
    secret=password()
    command="sudo -S -p '' -u gaokuangda -g docker /home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -c "+shlex.quote(REMOTE)
    child=subprocess.Popen(['ssh','-F',str(ROOT/'.sync/cara-fast-mainline-tailscale-20261030/ssh_config.budget_direct.private'),
        '-o','BatchMode=yes','-o','ConnectTimeout=25','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=3',
        'two_card_lan',command],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    try:
        out,err=child.communicate((secret+'\n'+json.dumps(dict(files=files))).encode(),timeout=150)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid,signal.SIGKILL);out,err=child.communicate()
    result=json.loads(out) if child.returncode==0 else None
    if result is not None:
        assert len(result['files'])==32 and result['CPU_affinity']==[26]
        assert [(r['path'],r['sha256']) for r in result['files']]==[(r['path'],r['sha256']) for r in files]
    report=dict(binding,observed_unix=time.time(),exit_code=child.returncode,result=result,
        status='ORIGINAL_REUSE_ASSETS_HASH_VERIFIED' if result else 'REUSE_ASSETS_NOT_VERIFIED',
        stderr=err.decode(errors='replace').replace(secret,'[REDACTED]'),
        live_admission_or_future_availability_proven=False,whole_GPU_card_accepted=False)
    with args.output.open('x') as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps(dict(status=report['status'],exit_code=child.returncode,
                         read_bytes=result['read_bytes'] if result else None)))


if __name__=='__main__':main()
