"""One collection of an existing CPU handle; no launch, retry or model call."""
import argparse
import gzip
import json
from pathlib import Path
import shlex
import subprocess
import time

REMOTE_PY='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--launch-ref',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    if a.output.exists():raise ValueError('Fresh collection receipt required')
    launch=json.loads(a.launch_ref.read_text())['launch']
    code='launch='+repr(launch)+'\n'+"""import pathlib,json,hashlib,time
stage=pathlib.Path(launch['stage']).resolve();reg=stage/'registration.json'
assert hashlib.sha256(reg.read_bytes()).hexdigest()==launch['registration_sha256']
r=json.loads(reg.read_text());assert r['source_revision']==launch['source_revision']
assert all(hashlib.sha256((stage/n).read_bytes()).hexdigest()==h for n,h in r['payload_sha256'].items())
proc=pathlib.Path('/proc')/str(launch['pid']);state=None;command=None
if proc.exists():
 try:state=(proc/'stat').read_text().split(') ',1)[1].split()[0];command=(proc/'cmdline').read_bytes().replace(b'\\0',b' ').decode()
 except FileNotFoundError:pass
result=json.loads((stage/'CPU-bundle-result.json').read_text()) if (stage/'CPU-bundle-result.json').exists() else None
print(json.dumps({'observed_unix':time.time(),'source_revision':r['source_revision'],'payload_files_verified':len(r['payload_sha256']),'pid':launch['pid'],'process_state':state,'process_command':command,'result':result,'bundle_log':(stage/'CPU-bundle.log').read_text()[-5000:] if (stage/'CPU-bundle.log').exists() else '', 'child_log_tails':{n:(stage/n).read_text()[-5000:] for n in ('P80.log','W3_11.log') if (stage/n).exists()}}))
"""
    remote=REMOTE_PY+' -c '+shlex.quote(code)
    p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen',remote],text=True,capture_output=True,timeout=120)
    result={'transport_exit_code':p.returncode,'launch_ref':str(a.launch_ref),'stderr':p.stderr,'collected_unix':time.time()}
    try:result['capture']=json.loads(p.stdout)
    except json.JSONDecodeError:result['stdout']=p.stdout
    with a.output.open('xb') as f:f.write(gzip.compress(json.dumps(result,allow_nan=False).encode(),mtime=0))
    c=result.get('capture',{});data=c.get('result') or {}
    print(json.dumps({'receipt':str(a.output),'transport_exit_code':p.returncode,'pid':c.get('pid'),'process_state':c.get('process_state'),'status':data.get('status'),'jobs':[(x['name'],x['exit_code'],x.get('result',{}).get('error')) for x in data.get('jobs',[])]}))
    if p.returncode:raise SystemExit(p.returncode)


if __name__=='__main__':main()
