"""Bound CPU-only timing checks; no GPU, ledger, mounts provisioning or sudo mode changes."""
import argparse,base64,hashlib,json,subprocess,sys
from pathlib import Path
from cara_two_card_transport_r1 import ssh,four_ssh
ROOT=Path(__file__).resolve().parents[1]
REMOTE=r'''
import base64,hashlib,json,os,pathlib,shutil,subprocess,sys,time
p=json.load(sys.stdin);root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace');stage=root/'.sync'/p['stage_name']
sha=lambda path:hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
if p['action']=='capture':
 reg=json.loads((stage/'registration.json').read_text());L=json.loads((stage/'CPU-launch.json').read_text())
 assert L['registration_sha256']==sha(stage/'registration.json')
 con=json.loads(subprocess.check_output(['docker','inspect',L['container']]))[0]
 proof=stage/'CPU-proof.json'
 print(json.dumps(dict(status='PAPER_TIMING_CPU_CAPTURE',launch=L,registration=reg,registration_sha256=sha(stage/'registration.json'),payload_intact=all(sha(stage/n)==h for n,h in reg['payload_sha256'].items()),runtime_intact=all(sha(root/'runtime'/n)==h for n,h in reg['runtime_source_sha256'].items()),container_state=con['State'],host_config={k:con['HostConfig'][k] for k in ('NanoCpus','Memory','DeviceRequests','NetworkMode','ReadonlyRootfs')},CPU_proof=json.loads(proof.read_text()) if proof.exists() else None,CPU_proof_sha256=sha(proof) if proof.exists() else None,log_tail=(stage/'CPU.log').read_text(errors='replace')[-4500:],observed_unix=time.time(),GPU_submissions=0,ledger_written=False)))
else:
 assert not stage.exists(),'Existing CPU stage: capture, never overwrite/relaunch'
 base=pathlib.Path(p['base_stage']);assert sha(base/'registration.json')==p['base_registration_sha256']
 reg=json.loads((base/'registration.json').read_text())
 assert all(sha(root/'runtime'/n)==h for n,h in reg['runtime_source_sha256'].items())
 mem=int(next(l.split()[1] for l in pathlib.Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))*1024
 assert mem>=8*2**30 and shutil.disk_usage(root).free>=2*2**30
 old=json.loads((base/'CPU-command.json').read_text());assert '--gpus' not in old
 stage.mkdir(mode=0o700)
 for n,encoded in p['files'].items():
  path=pathlib.Path(n);assert not path.is_absolute() and '..' not in path.parts
  raw=base64.b64decode(encoded);assert hashlib.sha256(raw).hexdigest()==p['hashes'][n]
  target=stage/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
 newreg=dict(host=p['host'],stage=str(stage),payload_sha256=p['hashes'],runtime_source_sha256=reg['runtime_source_sha256'],parent_git_revision=p['parent_git_revision'],source_identity='EXACT_PAYLOAD_SHA_WORKTREE_CPU_ONLY',base_registration_sha256=p['base_registration_sha256'])
 (stage/'registration.json').write_text(json.dumps(newreg,indent=2)+'\n')
 for name in ('torchinductor','triton','extensions','cuda','xdg'):(stage/'CPU-caches'/name).mkdir(parents=True)
 cmd=[s.replace(str(base),str(stage)) for s in old]
 cmd[cmd.index('--name')+1]=stage.name+'-cpu';cmd[cmd.index('--cpus')+1]='1';cmd[cmd.index('--memory')+1]='4g'
 for i,s in enumerate(cmd):
  if s.startswith('wcomr.manifest='):cmd[i]='wcomr.manifest='+sha(stage/'registration.json')
  if s.startswith(('OMP_NUM_THREADS=','OPENBLAS_NUM_THREADS=')):cmd[i]=s.split('=')[0]+'=1'
 end=cmd.index('--entrypoint')+3
 cmd=cmd[:end]+[str(stage/'scripts/check_wc_time_lifecycle_cpu_r1.py'),'--runtime',str(root/'runtime'),'--stage',str(stage),'--host',p['host'],'--output',str(stage/'CPU-proof.json')]
 assert '--gpus' not in cmd and 'CUDA_VISIBLE_DEVICES=' in cmd and 'NVIDIA_VISIBLE_DEVICES=void' in cmd and cmd[cmd.index('--network')+1]=='none'
 (stage/'CPU-command.json').write_text(json.dumps(cmd))
 with (stage/'CPU.log').open('x') as out:child=subprocess.Popen(cmd,stdout=out,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
 v=dict(status='PAPER_TIMING_CPU_LAUNCHED_NOT_GPU',host=p['host'],stage=str(stage),container=stage.name+'-cpu',registration_sha256=sha(stage/'registration.json'),pid=child.pid,started_unix=time.time(),MemAvailable_before=mem,free_disk_before=shutil.disk_usage(root).free,GPU_submissions=0,ledger_written=False)
 (stage/'CPU-launch.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
'''
def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','capture']);p.add_argument('--host',choices=['four_card','two_card'],required=True);p.add_argument('--stage-name',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 import re
 assert re.fullmatch(r'cara-wc-lifecycle-CPU-(ada|a6000)-r[0-9]+-20261027',a.stage_name)
 assert not a.output.exists();payload=dict(action=a.action,host=a.host,stage_name=a.stage_name)
 if a.action=='prepare':
  capname={'four_card':'cara_DEV128_full_four_card_CPU_complete2_r3_20261026.json','two_card':'cara_DEV128_full_two_card_CPU_complete_r3_20261026.json'}[a.host]
  cap=json.loads((ROOT/'reports'/capname).read_text());L=cap['launch']
  paths=list((ROOT/'src').rglob('*.py'))+list((ROOT/'tests').glob('*.py'))+[ROOT/'scripts/check_wc_time_lifecycle_cpu_r1.py',ROOT/'manifests/cara_DEV128_scope_r1_20261026.json',ROOT/'configs/cara_DEV128_requests_r1_20261026.json']
  paths += [ROOT/'plans/cara_wc_time_protocol_p0_20261027/CONTROL_IDENTITY_MATRIX.yaml',ROOT/'plans/cara_wc_time_protocol_r1_20261027/RA_BINDING.json']
  files={str(q.relative_to(ROOT)):q.read_bytes() for q in paths}
  payload.update(base_stage=L['stage'],base_registration_sha256=L['registration_sha256'],parent_git_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),files={n:base64.b64encode(b).decode() for n,b in files.items()},hashes={n:hashlib.sha256(b).hexdigest() for n,b in files.items()})
 result=ssh(REMOTE,payload,docker_group=True,timeout=180) if a.host=='two_card' else four_ssh(REMOTE,payload,timeout=180)
 with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({k:result.get(k) for k in ('status','host','stage','container_state','CPU_proof_sha256','log_tail')}))
if __name__=='__main__':main()
