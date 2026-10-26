"""CPU-only full-card binding on either host. No GPU dispatch or authority writes."""
import argparse,base64,hashlib,json,re,subprocess
from pathlib import Path
import wc_dual_host_cara_dev128_cpu_r1 as old
from cara_two_card_transport_r1 import ssh,four_ssh
ROOT=old.ROOT
PREPARE=old.PREPARE
# Use the accepted base-container builder with new frozen full-lifecycle entry.
PREPARE=PREPARE.replace("cmd[at:at]=['--tmpfs','/fixture:rw,size=256m,mode=1777']", "cmd[at:at]=['--tmpfs','/fixture:rw,size=256m,mode=1777','--tmpfs','/fault:rw,size=64m,mode=1777']")
PREPARE=PREPARE.replace("scripts/check_cara_dev128_cpu_r1.py","scripts/check_cara_dev128_full_cpu_r1.py").replace("DEV128-CPU.json","DEV128-lifecycle-CPU.json")
needle="reg=dict(namespace='CARA_SHARED25_DEV128_CPU_R1'"
insert="""prior=pathlib.Path(p['prior_launch']['stage']);prior_reg=read(prior/'registration.json')
assert sha(prior/'registration.json')==p['prior_launch']['registration_sha256']
proof=prior/'DEV128-CPU.json';assert sha(proof)==p['prior_acceptance']['proof_sha256']
for metadata in ('CPU-reuse-binding.json','CPU-reuse-entry.json','CPU-reuse-combination.json'):
 assert sha(prior/metadata)==prior_reg['payload_sha256'][metadata]
 shutil.copyfile(prior/metadata,stage/metadata);names.add(metadata)
con=json.loads(subprocess.check_output(['docker','inspect',p['prior_launch']['container']]))[0]
assert not con['State']['Running'] and con['State']['ExitCode']==0 and not con['HostConfig']['DeviceRequests']
for name,src in [('prior-production-proof.json',proof),('prior-runner.py.txt',prior/'scripts/run_cara_dev128_r1.py')]:
 shutil.copyfile(src,stage/name);names.add(name)
binding=dict(launch=p['prior_launch'],acceptance=p['prior_acceptance'],proof_sha256=sha(proof),payload_sha256=prior_reg['payload_sha256'],prior_GPU_hidden=True,prior_exited_zero=True)
(stage/'prior-production-binding.json').write_text(json.dumps(binding,indent=2)+'\\n');names.add('prior-production-binding.json')
"""
PREPARE=PREPARE.replace(needle,insert+needle)
CAPTURE=old.CAPTURE.replace('DEV128-CPU.json','DEV128-lifecycle-CPU.json')
def main():
 p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','capture']);p.add_argument('--host',required=True,choices=['four_card','two_card']);p.add_argument('--stage-name');p.add_argument('--launch-ref',type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args();assert not a.output.exists()
 def remote(code,data):
  if a.host=='two_card':return ssh(code,data,docker_group=True,timeout=600)
  from wc_four_card_policy_assets_r1 import bridge,read,RUNTIME_REF
  return four_ssh(bridge(code,read(ROOT/RUNTIME_REF)),data,timeout=600)
 if a.command=='capture':
  L=json.loads(a.launch_ref.read_text());assert L['host']==a.host;v=remote(CAPTURE,L)
 else:
  assert re.fullmatch(r'cara-dev128-fullCPU-(?:ada|a6000)-r[0-9]+-20261026',a.stage_name)
  rev=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();files={};hashes={}
  from wcomr.policy_generator_r1.dev128_card import MANIFEST
  inputs=json.loads((ROOT/MANIFEST).read_text())['input_bindings']
  # Reuse the accepted full-CPU closure; GPU dispatch/provision controllers are
  # separate control-plane code and must never pull private bootstrap scripts.
  previous=json.loads((ROOT/'reports/cara_DEV128_full_two_card_CPU_complete_r2_20261026.json').read_text())['registration']['payload_sha256']
  names={n for n in previous if (ROOT/n).is_file() and n.startswith(('src/','scripts/','tests/','manifests/','configs/','reports/','plans/','vendor/'))}
  names.update(inputs)
  for n in sorted(names):
   raw=(ROOT/n).read_bytes()
   if n in inputs:assert hashlib.sha256(raw).hexdigest()==inputs[n]
   elif n.startswith('vendor/'):assert hashlib.sha256(raw).hexdigest()==previous[n],'Accepted pinned vendor changed'
   else:assert subprocess.check_output(['git','show',rev+':'+n],cwd=ROOT)==raw,'Commit source first '+n
   files[n]=base64.b64encode(raw).decode();hashes[n]=hashlib.sha256(raw).hexdigest()
  ref='reports/cara_DEV128_'+a.host+'_CPU_'
  L=json.loads((ROOT/(ref+'launch_r4_20261026.json')).read_text());accept=json.loads((ROOT/(ref+'accepted_r4_20261026.json')).read_text())
  assert hashlib.sha256((ROOT/accept['capture_ref']).read_bytes()).hexdigest()==accept['capture_sha256']
  v=remote(PREPARE,dict(root=old.REMOTE,host=a.host,stage_name=a.stage_name,revision=rev,files=files,hashes=hashes,base_registration_sha256='48193714a15f219b33fd62a6f929ee8e7a5c17b1b6c3dfd9c7615318318c7561',prior_launch=L,prior_acceptance=accept))
 with a.output.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
 print(json.dumps(dict(status=v['status'],host=a.host,stage=v.get('stage'),proof=bool(v.get('proof')))))
if __name__=='__main__':main()
