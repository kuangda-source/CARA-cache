#!/usr/bin/env python3
"""One immutable CPU download stage and handle; no metric/GPU job or budget write."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
PYTHON='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
WORKER='scripts/fetch_wc_N10_viclip_resource_r1.py'
BOOTSTRAP=r'''
import hashlib,json,os,pathlib,subprocess,sys,time
payload=json.loads(sys.stdin.buffer.read());root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr').resolve()
stage=root/'.sync/wc-N10-viclip-resource-r1-20261016'
assert not stage.exists();stage.mkdir()
worker=stage/'fetch_wc_N10_viclip_resource_r1.py';raw=payload['worker_source'].encode()
assert hashlib.sha256(raw).hexdigest()==payload['worker_sha256'];worker.write_bytes(raw)
registration=dict(purpose='N10_PINNED_PUBLIC_RESOURCE_ONLY_NO_MODEL_OR_GPU',source_revision=payload['source_revision'],
 worker_sha256=payload['worker_sha256'],expected_weight=payload['expected_weight'],original_generation_stages_written=False)
with (stage/'registration.json').open('x') as handle:json.dump(registration,handle,indent=2)
command=[sys.executable,str(worker),'--stage',str(stage)]
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1')
with (stage/'resource-worker.log').open('xb') as log:
 child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
fields=(pathlib.Path('/proc')/str(child.pid)/'stat').read_text().split(') ',1)[1].split()
now=time.time();receipt=dict(status='N10_RESOURCE_CPU_DOWNLOAD_SINGLE_DISPATCHED',pid=child.pid,start_ticks=int(fields[19]),
 process_state=fields[0],command=command,stage=str(stage),source_revision=payload['source_revision'],
 worker_sha256=payload['worker_sha256'],registration_sha256=hashlib.sha256((stage/'registration.json').read_bytes()).hexdigest(),
 expected_weight=payload['expected_weight'],started_unix=now,first_collection_not_before_unix=now+1800,
 GPU_submissions=0,ledger_written=False,models_imported=False,weights_loaded=0)
with (stage/'resource-launch.json').open('x') as handle:json.dump(receipt,handle,indent=2)
print(json.dumps(receipt,allow_nan=False))
'''


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();assert not args.output.exists()
    sys.path.insert(0,str(ROOT/'scripts'))
    from fetch_wc_N10_viclip_resource_r1 import URL,SHA,SIZE,NAME
    identity=json.loads((ROOT/'reports/wc_paper_N10_official_tokenizer_and_ViCLIP_checkpoint_identity_20261016.json').read_text())
    original=identity['required_checkpoint']
    assert (NAME,SIZE,SHA)==(original['rfilename'],original['size'],original['lfs']['sha256'])
    assert URL==('https://huggingface.co/'+identity['model_repo']+'/resolve/'+identity['model_revision']+'/'+NAME)
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    source=(ROOT/WORKER).read_bytes()
    for name in (WORKER,str(Path(__file__).resolve().relative_to(ROOT))):
        assert subprocess.check_output(['git','show',revision+':'+name],cwd=ROOT)==(ROOT/name).read_bytes()
    payload=dict(source_revision=revision,worker_source=source.decode(),worker_sha256=hashlib.sha256(source).hexdigest(),
                 expected_weight=dict(url=URL,sha256=SHA,bytes=SIZE,name=NAME))
    try:
        call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes',
            'gkd_minchen',PYTHON+' -c '+shlex.quote(BOOTSTRAP)],input=json.dumps(payload).encode(),
            capture_output=True,timeout=90)
    except (subprocess.TimeoutExpired,OSError) as error:
        args.output.write_text(json.dumps(dict(status='N10_RESOURCE_DISPATCH_TRANSPORT_UNKNOWN_DO_NOT_RETRY',
            stage='.sync/wc-N10-viclip-resource-r1-20261016',source_revision=revision,error_type=type(error).__name__,
            error=str(error),original_launch_ref='resource-launch.json',GPU_submissions=0,ledger_written=False),indent=2)+'\n')
        raise
    value=dict(transport_exit_code=call.returncode,stderr=call.stderr.decode())
    try:value['launch']=json.loads(call.stdout)
    except json.JSONDecodeError:value['stdout']=call.stdout.decode()
    args.output.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    print(json.dumps(value,allow_nan=False));raise SystemExit(call.returncode)


if __name__=='__main__':main()
