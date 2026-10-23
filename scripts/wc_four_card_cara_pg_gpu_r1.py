#!/usr/bin/env python3
"""Once-only complete PG-P1 continuation after original price acceptance."""
import argparse,base64,hashlib,json,subprocess,sys,time,uuid
from pathlib import Path
from wc_four_card_policy_assets_r1 import ssh,write,read,sha,REPO,RUNTIME_REF
from wc_four_card_price_refresh_gpu_r1 import saved_secret,RUNTIME_WRAPPER,LAUNCH_SUFFIX as PRICE_LAUNCH,CAPTURE_GPU as PRICE_CAPTURE
from audit_cara_pg_p1_combination_cpu_r1 import accept as accept_cpu
sys.path.insert(0,str(REPO/'src'))
from wcomr.policy_generator_r1.production_stage import RUN,CONFIG,CPU_PROOF
from wcomr.policy_generator_r1.production_contract import COUNTS,VERSION,matrix,complete_quote
from wcomr.policy_generator_r1.production_terminal import accept as accept_terminal
OLD='reports/wc_policy_assets_full1624_fourcard_GPU_terminal_20261023_0826.json'
OLDACC='reports/wc_policy_assets_full1624_fourcard_GPU_accepted_20261023_0826.json'
QUOTE='manifests/cara_PG_P1_full64_whole_quote_r1_20261023.json'


def published():
 from wcomr.immutable_stage_payload_r1 import local_python_closure
 revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
 names=local_python_closure(REPO,['scripts/wc_four_card_cara_pg_gpu_r1.py','scripts/audit_cara_pg_p1_combination_cpu_r1.py',
  'scripts/audit_cara_pg_p1_production_cpu_r1.py','scripts/wc_four_card_policy_assets_r1.py',
  'scripts/wc_four_card_price_refresh_gpu_r1.py','scripts/wc_four_card_price_refresh_r1.py',
  'scripts/audit_wc_policy_price_refresh_cpu_r1.py','scripts/four_card_policy_assets_port_r1.py'])
 for n,h in names.items():
  if hashlib.sha256(subprocess.check_output(['git','show',revision+':'+n],cwd=REPO)).hexdigest()!=h:raise ValueError('Commit controller closure before dispatch')
 if subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=REPO,text=True).split()[0]!=revision:raise ValueError('Controller revision not published')
 return revision,names


def prepare(a):
 cap=read(a.cpu_capture);cpu=accept_cpu(cap);cpu.update(capture_ref=str(a.cpu_capture),capture_sha256=sha(a.cpu_capture))
 if read(a.cpu_acceptance)!=cpu:raise ValueError('Independent CPU acceptance does not reproduce')
 for n,h in cpu['execution_source_sha256'].items():
  # A base file can be a separately registered generated port. Check overlay
  # files that actually exist locally, while remote validates the whole base.
  if (REPO/n).exists() and sha(REPO/n)!=h and n.startswith('src/wcomr/policy_generator_r1/'):
   raise ValueError('CPU-accepted PG source changed: '+n)
 from wcomr.policy_price_terminal_r1 import accept as price_accept,record
 pricecap=read(a.price_capture);pacc=price_accept(pricecap,read(REPO/OLD),read(REPO/OLDACC))
 pacc.update(capture_ref=str(a.price_capture),capture_sha256=sha(a.price_capture))
 if read(a.price_acceptance)!=pacc:raise ValueError('Original complete clean price acceptance does not reproduce')
 exposure=read(a.exposure)
 if exposure['scoped_no_execution_evidence'] is not True or time.time()-exposure['observed_unix']>1800:raise ValueError('Fresh complete scoped local/remote SELECT audit required')
 quote=read(REPO/QUOTE);q=complete_quote(read(REPO/quote['planning_source_ref']))
 if any(quote[k]!=v for k,v in q.items()) or sha(REPO/quote['planning_source_ref'])!=quote['planning_source_sha256']:raise ValueError('Whole64 quote changed')
 old=read(REPO/OLD)['files']['bundle'];oldraw=old.get('raw_utf8') or json.dumps(old['data'],ensure_ascii=False,indent=2)+'\n'
 if hashlib.sha256(oldraw.encode()).hexdigest()!=old['sha256']:raise ValueError('Old label raw SHA differs')
 config=dict(version=VERSION,run_id=RUN,scope_counts=COUNTS,matrix=matrix(),forecast_complete_GPUh=quote['forecast_complete_GPUh'],billed_limit_GPUh=quote['billed_limit_GPUh'])
 rawfiles={'pg-old-labels.json':oldraw.encode(),'pg-clean-prices.json':pricecap['files']['bundle']['raw_utf8'].encode(),
  'pg-old-acceptance.json':(REPO/OLDACC).read_bytes(),'pg-price-acceptance.json':a.price_acceptance.read_bytes(),
  'pg-whole-quote.json':(REPO/QUOTE).read_bytes(),'pg-config.json':(json.dumps(config,indent=2)+'\n').encode(),
  'pg-exposure-baseline.json':a.exposure.read_bytes(),'pg-independent-CPU-acceptance.json':a.cpu_acceptance.read_bytes()}
 data=dict(CPU_launch=cap['launch'],CPU_proof_sha256=cap['proof']['sha256'],stage_name=a.stage_name,root='/data20t/gaokuangda/worldcache_workspace',
  files={n:base64.b64encode(raw).decode() for n,raw in rawfiles.items()},hashes={n:hashlib.sha256(raw).hexdigest() for n,raw in rawfiles.items()})
 value=ssh(PREPARE,data);write(a.output,value);return value

PREPARE=r'''
import pathlib,json,hashlib,sys,base64,shutil,time
p=json.load(sys.stdin);root=pathlib.Path(p['root']);base=pathlib.Path(p['CPU_launch']['stage']);stage=root/'.sync'/p['stage_name']
assert stage.parent==root/'.sync' and stage.name.startswith('cara-pg-p1-full64-') and not stage.exists()
sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
assert sha(base/'registration.json')==p['CPU_launch']['registration_sha256'] and sha(base/'PG-combination-CPU.json')==p['CPU_proof_sha256']
reg=json.loads((base/'registration.json').read_text())
for n,h in reg['payload_sha256'].items():assert sha(base/n)==h
stage.mkdir(mode=0o700)
for n in reg['payload_sha256']:
 t=stage/n;t.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(base/n,t)
shutil.copyfile(base/'PG-combination-CPU.json',stage/'PG-combination-CPU.json')
for n,s in p['files'].items():
 raw=base64.b64decode(s);assert hashlib.sha256(raw).hexdigest()==p['hashes'][n];(stage/n).write_bytes(raw)
names=set(reg['payload_sha256'])|set(p['files'])|{'PG-combination-CPU.json'}
reg.update(namespace='CARA_PG_P1_COMPLETE64_R1',stage=str(stage),payload_sha256={n:sha(stage/n) for n in sorted(names)})
(stage/'registration.json').write_text(json.dumps(reg,indent=2)+chr(10))
sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
from wcomr.policy_generator_r1.production_stage import validate
validate(root,stage)
v=dict(status='PG_P1_IMMUTABLE_STAGE_READY_NO_GPU',project=str(root),stage=str(stage),source_revision=reg['source_revision'],registration_sha256=sha(stage/'registration.json'),CPU_proof_sha256=p['CPU_proof_sha256'],GPU_submissions=0,ledger_written=False,observed_unix=time.time())
(stage/'pg-stage-reference.json').write_text(json.dumps(v,indent=2)+chr(10));print(json.dumps(v))
'''

PREFLIGHT=r'''
import pathlib,json,sys,subprocess,time,shutil,hashlib
p=json.load(sys.stdin);L=p['stage_ref'];root=pathlib.Path(L['project']);stage=pathlib.Path(L['stage'])
sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
from wcomr.policy_generator_r1.production_stage import validate,read,sha,RUN,COUNTS,CONFIG,CPU_PROOF
from wcomr.policy_generator_r1.production_exclusive import observe
from wcomr.gpu_budget_pool_v2 import BudgetPool
assert sha(stage/'registration.json')==L['registration_sha256']
c,reg,*_=validate(root,stage)
cpu=read(stage/'pg-independent-CPU-acceptance.json');assert cpu['production_CPU_accepted'] and cpu['full_GPU_lifecycle_CPU_accepted']
assert cpu['proof_sha256']==sha(stage/CPU_PROOF)==L['CPU_proof_sha256']
for n,h in cpu['execution_source_sha256'].items():assert reg['payload_sha256'][n]==h
pool=BudgetPool(root).read();assert pool['cap_gpu_hours']==226 and pool['origin_used_gpu_hours']==79.99637737158223
active=[k for k,j in pool['jobs'].items() if j['status']=='RESERVED_OR_RUNNING' and j.get('confirmed_GPU_submission') is not False]
snap=observe(p['gpu_uuid']);g=subprocess.check_output(['/usr/bin/nvidia-smi','-i',p['gpu_uuid'],'--query-gpu=uuid,name,compute_cap,memory.used','--format=csv,noheader,nounits'],text=True).strip().split(',')
assert g[0].strip()==p['gpu_uuid'] and 'RTX 6000 Ada' in g[1] and g[2].strip()=='8.9'
free=shutil.disk_usage(root).free;mem=int(next(x.split()[1] for x in pathlib.Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))*1024
reasons=[]
if active:reasons.append('OWN_CONFIRMED_GPU_JOB_ACTIVE')
if snap['compute_apps'] or int(g[3])>1024:reasons.append('GPU_BUSY')
if snap['mps_processes']!=[]:reasons.append('MPS_PRESENT_OR_UNKNOWN')
if snap['compute_mode'] not in ('Default','Exclusive_Process'):reasons.append('UNSUPPORTED_PRIOR_MODE')
if pool['available_gpu_hours']<c['billed_limit_GPUh']:reasons.append('INSUFFICIENT_WHOLE_BUDGET')
if free<30*2**30:reasons.append('DISK_BELOW_WHOLE_QUOTE')
if mem<24*2**30:reasons.append('MEMORY_BELOW_WHOLE_QUOTE')
value=dict(status='PG_P1_ADMISSION_OBSERVATION_PASS' if not reasons else 'PG_P1_RESOURCE_WAIT_NO_DISPATCH',admissible=not reasons,reasons=reasons,snapshot=snap,observed_unix=time.time(),disk_free_bytes=free,MemAvailable_bytes=mem,pool={k:pool[k] for k in ('used_gpu_hours','reserved_gpu_hours','available_gpu_hours','cap_gpu_hours')},GPU_submissions=0,ledger_written=False)
'''


def preflight(a):
 v=ssh(PREFLIGHT+'\nprint(json.dumps(value))',dict(stage_ref=read(a.stage_ref),gpu_uuid=a.gpu_uuid));write(a.output,v);return v


def launch(a):
 L=read(a.stage_ref);revision,closure=published();data=dict(stage_ref=L,gpu_uuid=a.gpu_uuid)
 observed=ssh(PREFLIGHT+'\nprint(json.dumps(value))',data)
 if not observed.get('admissible'):write(a.output,observed);return observed
 # Retrieve only already bound stage metadata, before durable intent.
 metadata=ssh(PREFLIGHT+"\nprint(json.dumps(dict(config=c,cpu_sha=sha(stage/'pg-independent-CPU-acceptance.json'),config_sha=sha(stage/CONFIG))))",data)
 c=metadata['config'];auth=dict(kind='AUTONOMOUS_COMPLETE_PG_P1_UNDER12',run_id=RUN,launch_id=str(uuid.uuid4()),source_revision=L['source_revision'],
  entry_stage=L['stage'],registration_sha256=L['registration_sha256'],config_sha256=metadata['config_sha'],production_CPU_sha256=L['CPU_proof_sha256'],
  independent_CPU_acceptance_sha256=metadata['cpu_sha'],gpu_uuid=a.gpu_uuid,scope_counts=COUNTS,forecast_GPUh=c['forecast_complete_GPUh'],
  billed_limit_GPUh=c['billed_limit_GPUh'],cumulative_cap_GPUh=226,direct_user_authorization=True,controller_source_revision=revision,controller_payload_sha256=closure)
 data.update(auth=auth,control_runtime=read(REPO/RUNTIME_REF),sudo_password=saved_secret())
 try:v=ssh(LAUNCH_PREFIX+PREFLIGHT.replace('p=json.load(sys.stdin);','')+LAUNCH_SUFFIX,data)
 except Exception as error:v=dict(status='PG_P1_DISPATCH_UNKNOWN_RECOVER_ONLY',stage_reference=L,intended_launch_id=auth['launch_id'],error_type=type(error).__name__,GPU_replay_allowed=False)
 finally:data.pop('sudo_password',None)
 write(a.output,v);return v

LAUNCH_PREFIX=r'''
import json,pathlib,sys,fcntl
p=json.load(sys.stdin);stage=pathlib.Path(p['stage_ref']['stage'])
lock=(stage/'pg-dispatch.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
for name in ('pg-GPU-launch.json','pg-GPU-intent.json'):
 if (stage/name).exists():
  print(json.dumps(dict(status='EXISTING_PG_P1_HANDLE_RECOVER_ONLY',original=json.loads((stage/name).read_text()))));raise SystemExit(0)
'''
# The audited host launch body is shared, using this new stage/contract only.
LAUNCH_SUFFIX=PRICE_LAUNCH.replace('price-','pg-').replace('PRICE_','PG_P1_').replace('wc_policy_price_host_guardian_r1.py','wc_cara_pg_p1_host_guardian_r1.py')
a=LAUNCH_SUFFIX.index("raw=base64.b64decode(p['accepted_base64'])");b=LAUNCH_SUFFIX.index("with (stage/'pg-GPU-authorization.json')",a)
LAUNCH_SUFFIX=LAUNCH_SUFFIX[:a]+"assert sha(stage/'pg-independent-CPU-acceptance.json')==auth['independent_CPU_acceptance_sha256']\n"+LAUNCH_SUFFIX[b:]


def recover(a):
 L=read(a.stage_ref)
 v=ssh("import json,pathlib,sys\nL=json.load(sys.stdin);s=pathlib.Path(L['stage']);v={n:json.loads((s/n).read_text()) for n in ('pg-GPU-intent.json','pg-GPU-launch.json','pg-host-guardian.json','pg-admission-failure.json') if (s/n).exists()};print(json.dumps(dict(status='PG_P1_ORIGINAL_HANDLE_RECOVERY_NO_DISPATCH',stage_reference=L,original_files=v,GPU_submissions=0)))",L)
 write(a.output,v);return v

# Preserve the proven handle/container/UUID observer; replace price-specific post.
CAPTURE=PRICE_CAPTURE[:PRICE_CAPTURE.index('if terminal:')]
CAPTURE=CAPTURE.replace('wcomr.policy_price_refresh_production_r1','wcomr.policy_generator_r1.production_stage').replace('RUN,ORIGINAL_RUN,read,sha','RUN,read,sha').replace('price-','pg-').replace('PRICE_','PG_P1_').replace('wcomr.policy_price_exclusive_r1','wcomr.policy_generator_r1.production_exclusive')
CAPTURE+=r'''
if terminal and not any(v['original_live_handles'].values()):
 from wcomr.policy_generator_r1.production_capture import collect
 try:v.update(collect(root,stage,L))
 except Exception as e:v['terminal_collection_error']=dict(error_type=type(e).__name__,error=str(e))
 reg=read(stage/'registration.json');v['payload_actual_sha256']={n:sha(stage/n) for n in reg['payload_sha256']};v['runtime_actual_sha256']={n:sha(root/'runtime'/n) for n in reg['runtime_source_sha256']}
print(json.dumps(v,allow_nan=False))
'''

def capture(a):
 v=ssh(CAPTURE,dict(launch=read(a.launch_ref),terminal=a.mode=='terminal'));write(a.output,v);return v

def main():
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
 t=sub.add_parser('prepare')
 for n in ('cpu-capture','cpu-acceptance','price-capture','price-acceptance','exposure'):t.add_argument('--'+n,type=Path,required=True)
 t.add_argument('--stage-name',required=True)
 for name in ('preflight','launch-gpu','recover'):
  t=sub.add_parser(name);t.add_argument('--stage-ref',type=Path,required=True)
  if name!='recover':t.add_argument('--gpu-uuid',required=True)
 t=sub.add_parser('capture');t.add_argument('--launch-ref',type=Path,required=True);t.add_argument('--mode',choices=['admission','halfway','terminal'],required=True)
 t=sub.add_parser('accept-gpu');t.add_argument('--capture',type=Path,required=True)
 for t in sub.choices.values():t.add_argument('--output',type=Path,required=True)
 a=p.parse_args()
 if a.command=='accept-gpu':v=accept_terminal(read(a.capture));v.update(capture_ref=str(a.capture),capture_sha256=sha(a.capture));write(a.output,v)
 else:v={'prepare':prepare,'preflight':preflight,'launch-gpu':launch,'recover':recover,'capture':capture}[a.command](a)
 print(json.dumps({k:v.get(k) for k in ('status','admissible','stage','launch_id','full_protocol_accepted')}))
if __name__=='__main__':main()
