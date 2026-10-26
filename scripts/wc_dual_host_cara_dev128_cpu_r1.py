"""CPU-only isolated stages on both registered hosts. No GPU/volume/ledger API."""
import argparse,ast,base64,hashlib,json,re,subprocess,sys
from pathlib import Path
from cara_two_card_transport_r1 import ssh,four_ssh
ROOT=Path(__file__).resolve().parents[1];REMOTE='/data20t/gaokuangda/worldcache_workspace'
sys.path.insert(0,str(ROOT/'src'))
from wcomr.policy_generator_r1.dev128_card import MANIFEST,REQUESTS
PREPARE=r'''
import pathlib,sys,json,base64,hashlib,subprocess,time,os,shutil
p=json.load(sys.stdin);root=pathlib.Path(p['root']);base=root/'.sync/cara-shared66-full-ada-r2-20261025';stage=root/'.sync'/p['stage_name']
assert not stage.exists(),'Recover existing CPU handle; never overwrite'
read=lambda f:json.loads(pathlib.Path(f).read_text());sha=lambda f:hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest()
original=read(base/'registration.json');assert sha(base/'registration.json')==p['base_registration_sha256']
assert all(sha(base/n)==h for n,h in original['payload_sha256'].items())
assert all(sha(root/'runtime'/n)==h for n,h in original['runtime_source_sha256'].items())
mem=int(next(l.split()[1] for l in pathlib.Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))*1024
assert mem>=12*2**30 and shutil.disk_usage(root).free>=2*2**30,'CPU resources insufficient'
stage.mkdir(mode=0o700);names=set(original['payload_sha256'])-{'shared66-recovery-CPU.json','pg-independent-CPU-acceptance.json','history104-storage.json','pg-config.json','pg-whole-quote.json'}
for n in names:
 target=stage/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(base/n,target)
for n,raw in p['files'].items():
 data=base64.b64decode(raw);assert hashlib.sha256(data).hexdigest()==p['hashes'][n]
 target=stage/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data);names.add(n)
shutil.copyfile(base/'quality-binding.json',stage/'quality-binding.json');names.add('quality-binding.json')
sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
from wcomr.policy_generator_r1.dev128_card import COUNTS,MANIFEST,CONFIG
card=read(stage/MANIFEST)
c=dict(host=p['host'],compute_capability=[8,9] if p['host']=='four_card' else [8,6],scope_counts=COUNTS,matrix=card['matrix'],GPU_dispatch_authorized=False)
(stage/CONFIG).write_text(json.dumps(c,indent=2)+'\n');names.add(CONFIG)
reg=dict(namespace='CARA_SHARED25_DEV128_CPU_R1',stage=str(stage),source_revision=p['revision'],payload_sha256={n:sha(stage/n) for n in sorted(names)},runtime_source_sha256=original['runtime_source_sha256'],parent_registration_sha256=p['base_registration_sha256'],host=p['host'])
(stage/'registration.json').write_text(json.dumps(reg,indent=2)+'\n')
from wcomr.policy_generator_r1.dev128_card import validate
validate(root,stage)
bank=root/'.sync/wc-bank24-fourcard-full-execution-r3-20261022';sys.path.insert(0,str(bank))
from four_card_bank24_execution_tools_r1 import process_environment
from four_card_policy_assets_port_r1 import container_command
cmd=container_command(root,stage,'cpu-worker',sha(stage/'registration.json'),process_environment(root,stage/'CPU-caches'),os.getuid(),os.getgid())
cmd[cmd.index('--cpus')+1]='2';cmd[cmd.index('--memory')+1]='8g'
at=cmd.index('--entrypoint');cmd[at:at]=['--tmpfs','/fixture:rw,size=256m,mode=1777']
i=cmd.index(str(stage/'scripts/wc_policy_interval_assets_lifecycle_r1.py'))
cmd=cmd[:i]+[str(stage/'scripts/check_cara_dev128_cpu_r1.py'),'--project',str(root),'--stage',str(stage),'--output',str(stage/'DEV128-CPU.json')]
assert '--gpus' not in cmd
(stage/'CPU-command.json').write_text(json.dumps(cmd))
with (stage/'CPU.log').open('x') as log:child=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
stat=pathlib.Path('/proc/%d/stat'%child.pid).read_text().rsplit(')',1)[1].split()
v=dict(status='DEV128_PRODUCTION_CPU_LAUNCHED_NOT_GPU',host=p['host'],project=str(root),stage=str(stage),source_revision=p['revision'],registration_sha256=sha(stage/'registration.json'),container=stage.name+'-cpu',identity=dict(pid=child.pid,start_ticks=int(stat[19])),started_unix=time.time(),GPU_submissions=0,ledger_written=False,MemAvailable_before=mem)
(stage/'CPU-launch.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
'''
CAPTURE=r'''
import pathlib,sys,json,subprocess,time,hashlib
L=json.load(sys.stdin);s=pathlib.Path(L['stage']);read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
reg=read(s/'registration.json');assert sha(s/'registration.json')==L['registration_sha256']
r=subprocess.run(['docker','inspect',L['container']],capture_output=True,text=True,timeout=20);con=json.loads(r.stdout)[0] if r.returncode==0 else None
proof=s/'DEV128-CPU.json'
v=dict(status='DEV128_ORIGINAL_CPU_CAPTURE',observed_unix=time.time(),launch=L,registration=reg,registration_sha256=sha(s/'registration.json'),payload_actual_sha256={n:sha(s/n) for n in reg['payload_sha256']},runtime_actual_sha256={n:sha(pathlib.Path(L['project'])/'runtime'/n) for n in reg['runtime_source_sha256']},container=con,proof=read(proof) if proof.exists() else None,proof_sha256=sha(proof) if proof.exists() else None,log_tail=(s/'CPU.log').read_text(errors='replace')[-10000:],GPU_submissions=0)
print(json.dumps(v))
'''
def names():
 from wcomr.immutable_stage_payload_r1 import local_python_closure
 card=json.loads((ROOT/MANIFEST).read_text())
 ns=set(card['source_bindings'])|set(card['input_bindings'])|{MANIFEST,REQUESTS,'manifests/cara_DEV128_dual_host_whole_quote_r1_20261026.json'}
 ns.update(str(p.relative_to(ROOT)) for pattern in ['scripts/*dev128*.py','tests/*dev128*.py','src/wcomr/policy_generator_r1/dev128*.py'] for p in ROOT.glob(pattern))
 while True:
  old=set(ns);ns.update(local_python_closure(ROOT,[n for n in ns if n.endswith('.py')]))
  for n in list(ns):
   if not n.endswith('.py'):continue
   for node in ast.walk(ast.parse((ROOT/n).read_text())):
    if isinstance(node,ast.ImportFrom) and node.module and node.level==0:
     for folder in ('scripts','tests'):
      imported=Path(folder)/(node.module.replace('.', '/')+'.py')
      if (ROOT/imported).is_file():ns.add(str(imported))
    if isinstance(node,ast.Constant) and isinstance(node.value,str) and node.value.endswith('.py'):
     value=Path(node.value)
     if not value.is_absolute() and '..' not in value.parts:
      for candidate in (value,Path('scripts')/value,Path('tests')/value):
       if (ROOT/candidate).is_file():ns.add(str(candidate))
    if isinstance(node,ast.Constant) and isinstance(node.value,str) and re.fullmatch(r'[a-z_][a-z0-9_]*(?:\.py)?',node.value):
     sibling=Path(n).parent/(node.value if node.value.endswith('.py') else node.value+'.py')
     if (ROOT/sibling).is_file():ns.add(str(sibling))
  if old==ns:return ns

def main():
 p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','capture']);p.add_argument('--host',choices=['four_card','two_card'],required=True);p.add_argument('--stage-name');p.add_argument('--launch-ref',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
 def remote(code,data):
  if a.host=='two_card':return ssh(code,data,docker_group=True,timeout=600)
  from wc_four_card_policy_assets_r1 import bridge,read,RUNTIME_REF
  return four_ssh(bridge(code,read(ROOT/RUNTIME_REF)),data,timeout=600)
 if a.command=='capture':
  L=json.loads(a.launch_ref.read_text());assert L['host']==a.host;v=remote(CAPTURE,L)
 else:
  assert re.fullmatch(r'cara-dev128-CPU-(?:ada|a6000)-r[0-9]+-20261026',a.stage_name)
  rev=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();files={};hashes={}
  input_hashes=json.loads((ROOT/MANIFEST).read_text())['input_bindings']
  for n in sorted(names()):
   raw=(ROOT/n).read_bytes()
   if n in input_hashes:
    assert hashlib.sha256(raw).hexdigest()==input_hashes[n],'Frozen vendor input changed: '+n
   else:
    assert subprocess.check_output(['git','show',rev+':'+n],cwd=ROOT)==raw,'Commit exact source first: '+n
   files[n]=base64.b64encode(raw).decode();hashes[n]=hashlib.sha256(raw).hexdigest()
  v=remote(PREPARE,dict(root=REMOTE,host=a.host,stage_name=a.stage_name,revision=rev,files=files,hashes=hashes,base_registration_sha256='48193714a15f219b33fd62a6f929ee8e7a5c17b1b6c3dfd9c7615318318c7561'))
 with a.output.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
 print(json.dumps({k:v.get(k) for k in ('status','host','stage','proof_sha256')}))
if __name__=='__main__':main()
