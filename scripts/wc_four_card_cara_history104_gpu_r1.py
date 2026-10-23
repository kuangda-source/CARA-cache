#!/usr/bin/env python3
"""Once-only full104 exclusive launch, original-handle capture and independent audit."""
import argparse,base64,hashlib,json,subprocess,sys,time,uuid
from pathlib import Path
from wc_four_card_policy_assets_r1 import ssh,write,read,sha,REPO,RUNTIME_REF,base_ssh,bridge
from wc_four_card_price_refresh_gpu_r1 import saved_secret
import wc_four_card_cara_pg_gpu_r1 as base
from recover_cara_pg_p1_terminal_codec_r1 import COLLECT as READONLY_CODEC
from audit_cara_history104_cpu_r1 import accept as accept_cpu
sys.path.insert(0,str(REPO/'src'))
from wcomr.policy_generator_r1.historical_card import RUN,CONFIG,CPU_PROOF,MANIFEST,COUNTS,VERSION,check_card
from wcomr.policy_generator_r1.historical_terminal import accept as accept_terminal

def published():
 from wcomr.immutable_stage_payload_r1 import local_python_closure
 revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip();closure=local_python_closure(REPO,['scripts/wc_four_card_cara_history104_gpu_r1.py'])
 for n,h in closure.items():
  if hashlib.sha256(subprocess.check_output(['git','show',revision+':'+n],cwd=REPO)).hexdigest()!=h:raise ValueError('Commit exact controller closure')
 if subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=REPO,text=True).split()[0]!=revision:raise ValueError('Controller not published')
 return revision,closure

def prepare(a):
 cap=read(a.cpu_capture);cpu=accept_cpu(cap);cpu.update(capture_ref=str(a.cpu_capture),capture_sha256=sha(a.cpu_capture))
 if cpu!=read(a.cpu_acceptance):raise ValueError('Independent CPU acceptance does not reproduce')
 for n,h in cpu['execution_source_sha256'].items():
  if (REPO/n).exists() and n.startswith(('src/wcomr/policy_generator_r1/','scripts/run_cara_history','scripts/wc_cara_history','scripts/postprocess_cara_history')) and sha(REPO/n)!=h:raise ValueError('Accepted source changed '+n)
 card=check_card(read(REPO/MANIFEST));config=dict(version=VERSION,run_id=RUN,scope_counts=COUNTS,matrix=card['matrix'],forecast_complete_GPUh=card['quote']['forecast_GPUh'],billed_limit_GPUh=11.9)
 rawfiles={'pg-whole-quote.json':(json.dumps(card['quote'],indent=2)+'\n').encode(),'pg-config.json':(json.dumps(config,indent=2)+'\n').encode(),'pg-independent-CPU-acceptance.json':a.cpu_acceptance.read_bytes()}
 data=dict(CPU_launch=cap['launch'],CPU_proof_sha256=cap['proof']['sha256'],stage_name=a.stage_name,root='/data20t/gaokuangda/worldcache_workspace',files={n:base64.b64encode(raw).decode() for n,raw in rawfiles.items()},hashes={n:hashlib.sha256(raw).hexdigest() for n,raw in rawfiles.items()})
 v=ssh(PREPARE,data);write(a.output,v);return v

PREPARE=base.PREPARE.replace('PG-combination-CPU.json',CPU_PROOF).replace('cara-pg-p1-full64-','cara-history104-full-').replace('CARA_PG_P1_COMPLETE64_R1',VERSION).replace('policy_generator_r1.production_stage','policy_generator_r1.historical_card').replace('PG_P1','HISTORY104')
PREFLIGHT=base.PREFLIGHT.replace('policy_generator_r1.production_stage','policy_generator_r1.historical_card').replace('PG_P1','HISTORY104')
LAUNCH_PREFIX=base.LAUNCH_PREFIX.replace('PG_P1','HISTORY104')
LAUNCH_SUFFIX=base.LAUNCH_SUFFIX.replace('wc_cara_pg_p1_host_guardian_r1.py','wc_cara_history104_host_guardian_r1.py').replace('PG_P1','HISTORY104')

def preflight(a):
 v=ssh(PREFLIGHT+'\nprint(json.dumps(value))',dict(stage_ref=read(a.stage_ref),gpu_uuid=a.gpu_uuid));write(a.output,v);return v

def launch(a):
 L=read(a.stage_ref);revision,closure=published();data=dict(stage_ref=L,gpu_uuid=a.gpu_uuid)
 observed=ssh(PREFLIGHT+'\nprint(json.dumps(value))',data)
 if not observed.get('admissible'):write(a.output,observed);return observed
 metadata=ssh(PREFLIGHT+"\nprint(json.dumps(dict(config=c,cpu_sha=sha(stage/'pg-independent-CPU-acceptance.json'),config_sha=sha(stage/CONFIG))))",data);c=metadata['config']
 auth=dict(kind='DIRECT_USER_COMPLETE104_UNDER12',run_id=RUN,launch_id=str(uuid.uuid4()),source_revision=L['source_revision'],entry_stage=L['stage'],registration_sha256=L['registration_sha256'],config_sha256=metadata['config_sha'],production_CPU_sha256=L['CPU_proof_sha256'],independent_CPU_acceptance_sha256=metadata['cpu_sha'],gpu_uuid=a.gpu_uuid,scope_counts=COUNTS,forecast_GPUh=c['forecast_complete_GPUh'],billed_limit_GPUh=11.9,cumulative_cap_GPUh=226,deployment_limit_seconds=257.7712338712067,direct_user_authorization=True,controller_source_revision=revision,controller_payload_sha256=closure)
 data.update(auth=auth,control_runtime=read(REPO/RUNTIME_REF),sudo_password=saved_secret())
 try:v=ssh(LAUNCH_PREFIX+PREFLIGHT.replace('p=json.load(sys.stdin);','')+LAUNCH_SUFFIX,data)
 except Exception as e:v=dict(status='HISTORY104_DISPATCH_UNKNOWN_RECOVER_ONLY',stage_reference=L,intended_launch_id=auth['launch_id'],error_type=type(e).__name__,GPU_replay_allowed=False)
 finally:data.pop('sudo_password',None)
 write(a.output,v);return v

def recover(a):
 L=read(a.stage_ref)
 v=ssh("import json,pathlib,sys\nL=json.load(sys.stdin);s=pathlib.Path(L['stage']);v={n:json.loads((s/n).read_text()) for n in ('pg-GPU-intent.json','pg-GPU-launch.json','pg-host-guardian.json','pg-admission-failure.json') if (s/n).exists()};print(json.dumps(dict(status='HISTORY104_ORIGINAL_HANDLE_RECOVERY_NO_DISPATCH',stage_reference=L,original_files=v,GPU_submissions=0)))",L);write(a.output,v);return v

OLD=" from wcomr.policy_generator_r1.production_capture import collect\n try:v.update(collect(root,stage,L))\n except Exception as e:v['terminal_collection_error']=dict(error_type=type(e).__name__,error=str(e))\n"
assert base.CAPTURE.count(OLD)==1
CAPTURE=base.CAPTURE.replace(OLD,READONLY_CODEC.replace('policy_generator_r1.production_capture','policy_generator_r1.historical_capture').replace("'--memory','2g'","'--memory','4g'").replace("'--read-only','--network'","'--read-only','--tmpfs','/tmp:rw,size=256m','--network'").replace('timeout=140','timeout=360'))
CAPTURE=CAPTURE.replace('policy_generator_r1.production_stage','policy_generator_r1.historical_card').replace('PG_P1','HISTORY104')
CAPTURE=CAPTURE.replace('print(json.dumps(v,allow_nan=False))',"\nif (out/'score-progress.json').exists():\n s=read(out/'score-progress.json');v['post_score_health']={k:s.get(k) for k in ('status','completed_pairs','planned_pairs','started_unix','ended_unix')}\nprint(json.dumps(v,allow_nan=False))")

def capture(a):
 v=base_ssh(bridge(CAPTURE,read(REPO/RUNTIME_REF)),dict(launch=read(a.launch_ref),terminal=a.mode=='terminal'),timeout=420);write(a.output,v);return v

def main():
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
 t=sub.add_parser('prepare')
 for n in ('cpu-capture','cpu-acceptance'):t.add_argument('--'+n,type=Path,required=True)
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
 print(json.dumps({k:v.get(k) for k in ('status','stage','launch_id','admissible','reasons','health','original_live_handles','full_protocol_accepted','post_score_health','terminal_collection_error')}))
if __name__=='__main__':main()
