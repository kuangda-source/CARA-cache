"""Resume only a hash-named CPU source transfer file; never prepare or run a job."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import time

REMOTE='''import fcntl,hashlib,json,os,sys
from pathlib import Path
p=json.loads(sys.argv[1]);target=Path(p['target'])
assert target.parent==Path('/data20t/gaokuangda/worldcache_workspace/.sync')
assert target.name.startswith('cara-budget-CPU-source-transfer-') and target.name.endswith('.json.gz')
assert not target.is_symlink()
if p['action']=='append':
 data=sys.stdin.buffer.read(p['length']);assert len(data)==p['length'] and hashlib.sha256(data).hexdigest()==p['chunk_sha256']
 mode='r+b' if target.exists() else 'x+b'
 with target.open(mode) as f:
  fcntl.flock(f,fcntl.LOCK_EX);old=f.read()
  assert len(old)==p['offset'] and hashlib.sha256(old).hexdigest()==p['prefix_sha256']
  assert f.write(data)==len(data);f.flush();os.fsync(f.fileno())
 os.chmod(target,0o600)
raw=target.read_bytes() if target.exists() else b''
print(json.dumps(dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())))
'''


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--host',choices=['four_card','two_card'],required=True)
    for key in ('metadata','ssh-config','output'):parser.add_argument('--'+key,type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise ValueError('Fresh transfer receipt required')
    if args.ssh_config.stat().st_mode&0o077:raise ValueError('Private SSH config required')
    meta=json.loads(args.metadata.read_text());local=Path(meta['path']);raw=local.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=meta['sha256'] or len(raw)!=meta['compressed_bytes']:
        raise ValueError('Original local source bytes differ')
    if meta['target']!='/data20t/gaokuangda/worldcache_workspace/.sync/'+local.name:
        raise ValueError('Original transfer filename required')
    report=dict(status='SOURCE_FILE_TRANSFER_STARTED_NOT_CPU',host=args.host,started_unix=time.time(),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        remote_code_sha256=hashlib.sha256(REMOTE.encode()).hexdigest(),metadata=meta,steps=[],CPU_jobs_started=0,GPU_submissions=0)
    # Exclusive intent is local only. The target remains a source blob, not a stage.
    with args.output.open('x') as f:json.dump(report,f,indent=2);f.write('\n')
    def save():
        temporary=args.output.with_suffix('.tmp');temporary.write_text(json.dumps(report,indent=2)+'\n');temporary.replace(args.output)
    def call(payload,data=b''):
        payload=dict(payload,target=meta['target'])
        remote='python3 -c '+shlex.quote(REMOTE)+' '+shlex.quote(json.dumps(payload))
        cmd=['ssh','-F',str(args.ssh_config),'-o','BatchMode=yes','-o','ConnectTimeout=35',
            '-o','ServerAliveInterval=5','-o','ServerAliveCountMax=2',
            'four_card' if args.host=='four_card' else 'two_card_lan',remote]
        child=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
        try:out,err=child.communicate(data,timeout=55)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGTERM);out,err=child.communicate()
        row=dict(action=payload['action'],observed_unix=time.time(),exit_code=child.returncode,stderr=err.decode(errors='replace'))
        if child.returncode==0:
            row['result']=json.loads(out);r=row['result']
            if not 0<=r['size']<=len(raw) or r['sha256']!=hashlib.sha256(raw[:r['size']]).hexdigest():
                report['steps'].append(row);report['status']='SOURCE_PREFIX_MISMATCH_NO_EXECUTION';save()
                raise ValueError('Original remote prefix differs; preserve it')
        report['steps'].append(row);save()
        if child.returncode:raise RuntimeError('Transfer connection unknown; recover file prefix before another append')
        return row['result']
    try:
        current=call(dict(action='probe'));report['initial_verified_bytes']=current['size'];save()
        while current['size']<len(raw):
            offset=current['size'];chunk=raw[offset:offset+32768]
            current=call(dict(action='append',offset=offset,length=len(chunk),prefix_sha256=current['sha256'],
                chunk_sha256=hashlib.sha256(chunk).hexdigest()),chunk)
            if current['size']!=offset+len(chunk):raise ValueError('Original append size differs')
            print(json.dumps(dict(verified_bytes=current['size'],total_bytes=len(raw))),flush=True)
        report.update(status='COMPLETE_SOURCE_FILE_SHA_VERIFIED_NOT_CPU',complete=True,ended_unix=time.time());save()
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as error:
        report.update(status=report['status'] if report['status']=='SOURCE_PREFIX_MISMATCH_NO_EXECUTION' else 'SOURCE_TRANSFER_INCOMPLETE_RECOVER_PREFIX',error_type=type(error).__name__,ended_unix=time.time());save()
        raise
    print(json.dumps(dict(status=report['status'],CPU_jobs_started=0,GPU_submissions=0)))


if __name__=='__main__':main()
