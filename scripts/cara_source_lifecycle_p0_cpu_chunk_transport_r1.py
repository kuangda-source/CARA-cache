"""Resume small verified CPU source blocks over the original two-card route.

The complete131KiB stream currently times out while short SSH commands work.
Only transfer bytes are retried. The remote prepare has a once intent; after an
unknown prepare, use the ordinary original CPU capture instead of rerunning it.
"""
import argparse
import ast
import base64
import gzip
import hashlib
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import time

from cara_two_card_transport_r1 import password
from cara_source_lifecycle_p0_entry_linux_cpu_r1 import STAGE,OVERLAY,REMOTE
from cara_s_initialization_selector_cpu_r1 import BASE_CAPTURE,BASE_ACCEPTED,LIMITS

ROOT=Path(__file__).resolve().parents[1]
REMOTE_ROOT='/data20t/gaokuangda/worldcache_workspace'
BLOCK_BYTES=8192


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source-revision',required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--resume-final',action='store_true')
    args=parser.parse_args()
    assert not args.output.exists()
    base_bytes=(ROOT/BASE_CAPTURE).read_bytes()
    base=json.loads(base_bytes)['result']
    accepted=json.loads((ROOT/BASE_ACCEPTED).read_text())
    assert accepted['capture_sha256']==hashlib.sha256(base_bytes).hexdigest()
    assert accepted['total_controls_passed']==113
    files={n:subprocess.check_output(['git','show',args.source_revision+':'+n],cwd=ROOT) for n in OVERLAY}
    assert all((ROOT/n).read_bytes()==b for n,b in files.items())
    hashes={**base['registration']['payload_sha256'],
            **{n:hashlib.sha256(b).hexdigest() for n,b in files.items()}}
    entry_accepted=json.loads((ROOT/'reports/cara_read_write_entry_Linux_CPU_accepted_r1_20261101.json').read_text())
    entry_raw=(ROOT/entry_accepted['capture_ref']).read_bytes()
    assert hashlib.sha256(entry_raw).hexdigest()==entry_accepted['capture_sha256']
    entry=json.loads(entry_raw)['result']
    assert entry['container_state']['ExitCode']==0 and entry['container_state']['Pid']==0
    inherited=entry['registration']['payload_sha256']
    assert entry['registration']['runtime_source_sha256']==base['registration']['runtime_source_sha256']
    changed={n:h for n,h in hashes.items() if inherited.get(n)!=h}
    uploads={n:files[n] for n in changed}
    payload=dict(action='prepare',host='two_card',stage_name=STAGE,
        base_stage=entry['launch']['stage'],base_registration_sha256=entry['registration_sha256'],
        parent_git_revision=args.source_revision,expected_host_config=LIMITS,
        minimum_available_memory_GiB=8,hash_patch=changed,hash_remove=sorted(set(inherited)-set(hashes)),
        full_mapping_sha256=hashlib.sha256(json.dumps(hashes,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
        files={n:base64.b64encode(b).decode() for n,b in uploads.items()})
    wrapper="""import hashlib,io,json,pathlib,sys
p=json.load(sys.stdin);f=pathlib.Path(p['base_stage'])/'registration.json'
assert hashlib.sha256(f.read_bytes()).hexdigest()==p['base_registration_sha256']
mapping=json.loads(f.read_text())['payload_sha256'].copy()
for name in p.pop('hash_remove'):mapping.pop(name)
mapping.update(p.pop('hash_patch'));p['hashes']=mapping
assert hashlib.sha256(json.dumps(mapping,sort_keys=True,separators=(',',':')).encode()).hexdigest()==p.pop('full_mapping_sha256')
sys.stdin=io.StringIO(json.dumps(p))
"""+'\nexec('+repr(REMOTE)+')\n'
    raw=gzip.compress(json.dumps(dict(code=wrapper,payload=payload)).encode(),mtime=0)
    digest=hashlib.sha256(raw).hexdigest()
    blocks=[raw[i:i+BLOCK_BYTES] for i in range(0,len(raw),BLOCK_BYTES)]
    directory=REMOTE_ROOT+'/.sync/cara-P0-point20-CPU-transfer-'+digest[:16]+'-'+str(BLOCK_BYTES)
    config=ROOT/'.sync/cara-fast-mainline-tailscale-20261030/ssh_config.p0_qos_none.private'
    assert config.stat().st_mode&0o077==0
    secret=password()
    started=time.time()
    print(json.dumps(dict(status='CPU_DELTA_SOURCE_TRANSFER',total_blocks=len(blocks),
        compressed_bytes=len(raw),uploaded_source_files=len(uploads),full_registered_source_files=len(hashes))),flush=True)
    journal=args.output.with_name(args.output.stem+'_blocks.jsonl')
    # The same block journal may be resumed; only immutable identical bytes may
    # be recovered. This is a transfer journal, never an execution receipt.
    def call(code):
        ast.parse(code)
        command="sudo -S -p '' -u gaokuangda -g docker python3 -c "+shlex.quote(code)
        child=subprocess.Popen(['ssh','-C','-F',str(config),'-o','BatchMode=yes','-o','ConnectTimeout=25',
            '-o','ServerAliveInterval=10','-o','ServerAliveCountMax=2','two_card_lan',command],
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
        try:
            out,err=child.communicate((secret+'\n').encode(),timeout=60)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid,signal.SIGKILL)
            out,err=child.communicate()
        return dict(exit_code=child.returncode,result=json.loads(out) if child.returncode==0 else None,
                    stderr=err.decode(errors='replace').replace(secret,'[REDACTED]'))

    for i,block in ([] if args.resume_final else enumerate(blocks)):
        code="""import base64,hashlib,json,pathlib
d=pathlib.Path(DIRECTORY);d.mkdir(mode=0o700,exist_ok=True);assert d.is_dir() and not d.is_symlink()
raw=base64.b64decode(BODY);assert hashlib.sha256(raw).hexdigest()==EXPECTED
p=d/NAME
if p.exists():assert p.read_bytes()==raw
else:
 with p.open('xb') as f:f.write(raw)
print(json.dumps(dict(block=NAME,sha256=hashlib.sha256(p.read_bytes()).hexdigest())))
"""
        code=('DIRECTORY='+repr(directory)+'\nBODY='+repr(base64.b64encode(block).decode())+
              '\nEXPECTED='+repr(hashlib.sha256(block).hexdigest())+'\nNAME='+repr(f'{i:04}.block')+'\n'+code)
        for attempt in range(3):
            observed=call(code)
            with journal.open('a') as stream:
                stream.write(json.dumps(dict(block=i,attempt=attempt,bytes=len(block),observed_unix=time.time(),**observed))+'\n')
            if observed['exit_code']==0:
                break
            if attempt<2:
                time.sleep(1)
        if observed['exit_code']!=0:
            print(json.dumps(dict(status='CPU_TRANSFER_BLOCK_UNKNOWN_RESUME_BYTES_ONLY',block=i,total=len(blocks))),flush=True)
            return
        if i%8==0 or i==len(blocks)-1:
            print(json.dumps(dict(status='CPU_SOURCE_BLOCKS_VERIFIED',complete=i+1,total=len(blocks))),flush=True)

    code=r"""import contextlib,fcntl,gzip,hashlib,io,json,pathlib,sys,time
d=pathlib.Path(DIRECTORY)
with (d/'prepare.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 result_file=d/'prepare-result.json'
 if result_file.exists():
  result=json.loads(result_file.read_text())
 else:
  assert not (d/'prepare-intent.json').exists(),'Original CPU preparation unknown: capture only'
  raw=b''.join((d/(f'{i:04}.block')).read_bytes() for i in range(COUNT))
  assert hashlib.sha256(raw).hexdigest()==EXPECTED
  packet=json.loads(gzip.decompress(raw));p=packet['payload']
  stage=pathlib.Path(ROOT)/'.sync'/p['stage_name']
  assert not stage.exists(),'Original CPU stage exists: capture only'
  (d/'prepare-intent.json').write_text(json.dumps(dict(source_sha256=EXPECTED,started_unix=time.time())))
  output=io.StringIO();sys.stdin=io.StringIO(json.dumps(p))
  with contextlib.redirect_stdout(output):exec(packet['code'])
  result=json.loads(output.getvalue())
  result_file.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result))
"""
    code=('DIRECTORY='+repr(directory)+'\nCOUNT='+repr(len(blocks))+'\nEXPECTED='+repr(digest)+
          '\nROOT='+repr(REMOTE_ROOT)+'\n'+code)
    observed=call(code)
    report=dict(action='prepare',host='two_card',stage_name=STAGE,source_revision=args.source_revision,
        started_unix=started,observed_unix=time.time(),expected_host_config=LIMITS,work_seconds=600,exit_seconds=60,
        remote_code_sha256=hashlib.sha256(REMOTE.encode()).hexdigest(),
        transport_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        source_packet_sha256=digest,source_packet_bytes=len(raw),source_blocks=len(blocks),
        transfer_directory=directory,unknown_requires_original_capture=True,
        GPU_submissions=0,ledger_written=False,**observed)
    with args.output.open('x') as stream:
        json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps(dict(exit_code=observed['exit_code'],status=(observed['result'] or {}).get('status'))),flush=True)


if __name__=='__main__':
    main()
