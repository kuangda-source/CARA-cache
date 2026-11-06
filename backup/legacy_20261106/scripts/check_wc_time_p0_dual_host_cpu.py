"""Bounded GPU-hidden CPU checks in fresh stages; no GPU/ledger mutation APIs."""
import base64,concurrent.futures,hashlib,io,json,tarfile,time
from pathlib import Path
from cara_two_card_transport_r1 import ssh,four_ssh
ROOT=Path(__file__).resolve().parents[1]
REMOTE=r'''
import json,sys,base64,tarfile,io,hashlib,subprocess,time,os
from pathlib import Path
p=json.load(sys.stdin);root=Path('/data20t/gaokuangda/worldcache_workspace');s=root/'.sync'/('cara-wc-time-P0-'+p['host']+'-20261027')
if s.exists():
 old=json.loads((s/'terminal.json').read_text());assert old['payload_sha256']==p['files'];print(json.dumps(old));raise SystemExit(0)
base=root/'.sync'/('cara-dev128-fullCPU-ada-r3-20261026' if p['host']=='four_card' else 'cara-dev128-fullCPU-a6000-r3-20261026')
assert (base/'CPU-command.json').exists()
s.mkdir(mode=0o700)
raw=base64.b64decode(p['archive']);assert hashlib.sha256(raw).hexdigest()==p['archive_sha256']
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as t:
 for m in t.getmembers():
  assert m.isfile() and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts
  dest=s/m.name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(t.extractfile(m).read())
assert all(hashlib.sha256((s/n).read_bytes()).hexdigest()==h for n,h in p['files'].items())
c=json.loads((base/'CPU-command.json').read_text());c=[x.replace(str(base),str(s)).replace(base.name,s.name) for x in c]
c[c.index('--name')+1]=s.name+'-cpu'
i=c.index('--entrypoint')+2
# The immutable image follows --entrypoint Python; replace only the old worker arguments.
c=c[:i+1]+[str(s/'tests/check_wc_time_protocol_p0.py'),str(root/'runtime'),str(s/'result.json')]
assert '--gpus' not in c and 'CUDA_VISIBLE_DEVICES=' in c and 'NVIDIA_VISIBLE_DEVICES=void' in c
(s/'command.json').write_text(json.dumps(c,indent=2))
start=time.time()
with (s/'CPU.log').open('x') as log:
 child=subprocess.Popen(c,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 (s/'launch.json').write_text(json.dumps(dict(pid=child.pid,started_unix=start,command_sha256=hashlib.sha256((s/'command.json').read_bytes()).hexdigest())))
 try:rc=child.wait(timeout=180)
 except subprocess.TimeoutExpired:
  subprocess.run(['docker','stop','--time','5',s.name+'-cpu'],capture_output=True);rc=124
inspection=json.loads(subprocess.check_output(['docker','inspect',s.name+'-cpu']))[0]
v=dict(host=p['host'],stage=str(s),exit_code=rc,wall_seconds=time.time()-start,
 payload_sha256=p['files'],GPU_submissions=0,ledger_written=False,
 container_running=inspection['State']['Running'],device_requests=inspection['HostConfig']['DeviceRequests'],
 result=json.loads((s/'result.json').read_text()) if (s/'result.json').exists() else None,
 log_tail=(s/'CPU.log').read_text()[-2500:])
(s/'terminal.json').write_text(json.dumps(v,indent=2));print(json.dumps(v))
'''
def main():
 names=list((ROOT/'src/wcomr').rglob('*.py'))+[ROOT/'tests'/n for n in ['check_full_sampling.py','check_fair_sampling_cpu.py','check_wc_time_protocol_p0.py']]
 files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in names}
 b=io.BytesIO()
 with tarfile.open(fileobj=b,mode='w:gz') as t:
  for p in names:t.add(p,arcname=str(p.relative_to(ROOT)))
 raw=b.getvalue();data=dict(archive=base64.b64encode(raw).decode(),archive_sha256=hashlib.sha256(raw).hexdigest(),files=files)
 results={}
 def call(host):
  payload=dict(data,host=host)
  return four_ssh(REMOTE,payload,timeout=240) if host=='four_card' else ssh(REMOTE,payload,docker_group=True,timeout=240)
 with concurrent.futures.ThreadPoolExecutor(2) as pool:
  jobs={h:pool.submit(call,h) for h in ('four_card','two_card')}
  for h,f in jobs.items():
   try:results[h]=f.result()
   except Exception as e:results[h]=dict(error=str(e))
 p=ROOT/'reports/cara_wc_time_P0_dual_host_CPU_20261027.json';p.write_text(json.dumps(results,indent=2)+'\n')
 for h,r in results.items():print(h,{k:v for k,v in r.items() if k not in ('payload_sha256','result')})
if __name__=='__main__':main()
