"""One separately approved B36; every later call recovers the original handles."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from cara_two_card_transport_r1 import ssh,four_ssh,password

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from wcomr.cara_fast_b36_dispatch_r2 import ASSETS,STAGE_NAME,validate_grant
from wcomr.cara_fast_b36_execution_r1 import RUN,PROFILE,read,require

PROJECT='/data20t/gaokuangda/worldcache_workspace'
STAGE=PROJECT+'/.sync/'+STAGE_NAME
PROOF='reports/cara_fast_B36_dispatch_CPU_acceptance_r2_20261029.json'
CORE='reports/cara_fast_B36_CPU_acceptance_r1_20261029.json'

REMOTE=r'''
import hashlib,json,os,sys
from pathlib import Path
p=json.load(sys.stdin);project=Path('/data20t/gaokuangda/worldcache_workspace');stage=Path(p['stage'])
if p['action']=='prepare':
 base=Path(p['base_stage'])
 for name,expected in p['operator_sources'].items():
  raw=__import__('base64').b64decode(p['files'][name]);assert hashlib.sha256(raw).hexdigest()==expected
 # The new operator is sent explicitly before the new immutable stage exists.
 # Execute it in a private CPU import directory, never replacing the A stage.
 import tempfile
 with tempfile.TemporaryDirectory(prefix='B36-prepare-') as td:
  directory=Path(td)
  for name,expected in p['operator_sources'].items():
   target=directory/name;target.parent.mkdir(parents=True,exist_ok=True)
   target.write_bytes(__import__('base64').b64decode(p['files'][name]))
  sys.path[:0]=[str(directory/'src'),str(base/'src'),str(base/'scripts')]
  import wcomr
  wcomr.__path__.append(str(base/'src/wcomr'))
  from wcomr.cara_fast_b36_dispatch_r2 import prepare_stage
  result=prepare_stage(project,stage,p)
else:
 for name,expected in p['operator_sources'].items():assert hashlib.sha256((stage/name).read_bytes()).hexdigest()==expected
 sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
 from wcomr.cara_fast_b36_dispatch_r2 import provision,admit,bind,launch,status
 if p['action']=='provision':result=provision(project,stage,p.pop('sudo_password'))
 elif p['action']=='admit':result=admit(project,stage)
 elif p['action']=='bind':result=bind(project,stage,p['envelope'])
 elif p['action']=='launch':result=launch(project,stage,p.pop('sudo_password'),p['central_state'])
 elif p['action']=='status':result=status(project,stage)
 else:raise ValueError('Unknown explicit B action')
print(json.dumps(result,allow_nan=False))
'''

CENTRAL=r'''
import hashlib,json,sys,time
from pathlib import Path
p=json.load(sys.stdin);root=Path('/data20t/gaokuangda/worldcache_workspace');base=Path(p['CPU_stage'])
for name,expected in p['sources'].items():assert hashlib.sha256((base/name).read_bytes()).hexdigest()==expected
sys.path[:0]=[str(base/'src'),str(base/'scripts')]
from wcomr.cara_fast_b36_execution_r1 import Pool,RUN,PROFILE,SPEC,load_handoff,read
from wcomr.cara_fast_binding_r2 import load_card
from wcomr.gpu_budget_pool_v2 import atomic_json
pool=Pool(root);before=pool.read();job=p['job'];receipt=root/'reports'/(RUN+'.central-reservation.json')
if p.get('action')=='read':
 print(json.dumps(dict(central_ledger_host='four_card',job=before['jobs'].get(RUN),budget_overrun_recorded=bool(before.get('budget_overrun_recorded')),observed_unix=time.time(),cap=before['cap_gpu_hours'])));sys.exit()
if RUN in before['jobs']:
 assert before['jobs'][RUN]['launch_id']==job['launch_id'] and before['jobs'][RUN]['status']=='RESERVED_OR_RUNNING','Recover original B job'
 assert receipt.exists(),'Recover original reservation receipt; do not reserve again'
 result=read(receipt);assert result['job']==before['jobs'][RUN]
else:
 assert not receipt.exists(),'Original receipt exists; recover its job'
 card=load_card(base,SPEC);bound=load_handoff(base,card,read(base/PROFILE))
 after=pool.reserve(job,p['gpu'],bound)
 result=dict(central_ledger_host='four_card',new_reservation=True,job=after['jobs'][RUN],central_before=before,central_after=after,observed_unix=time.time())
 atomic_json(receipt,result)
print(json.dumps(result))
'''


def payload_for_authority(authority,proof,core,revision):
    profile=read(ROOT/PROFILE)
    validate_grant(authority,profile)
    terminal=read(ROOT/'reports/cara_fast_A6000_terminal_20261029_0050.json')
    original=json.loads(terminal['files']['registration']['raw_utf8'])
    original_launch=json.loads(terminal['files']['launch']['raw_utf8'])
    names=set(proof['critical_source_sha256'])|set(core['critical_source_sha256'])|{ASSETS,
        'scripts/cara_fast_b36_dispatch_r2.py','configs/f1_setup.json',
        'configs/wc_ra_comparison_production_r2_20261010.json','manifests/wc_h0_eval_mode_contract_20261003.json',
        'reports/cara_fast_four_card_host_profile_readonly_r2_20261028.json'}
    names.update(descriptor['path'] for descriptor in profile['A32_handoff_files'].values())
    hashes=dict(original['payload_sha256']);files={}
    for name in sorted(names):
        body=(ROOT/name).read_bytes()
        require(subprocess.check_output(['git','show',revision+':'+name],cwd=ROOT)==body,'Unpublished B overlay: '+name)
        hashes[name]=hashlib.sha256(body).hexdigest();files[name]=base64.b64encode(body).decode()
    require(all(hashes.get(name)==expected for name,expected in proof['critical_source_sha256'].items()),'B CPU/source proof changed')
    require(all(hashes.get(name)==expected for name,expected in core['critical_source_sha256'].items()),'Core CPU/source changed')
    authority=dict(authority,source_revision=revision)
    operators=[name for name in proof['critical_source_sha256'] if name.startswith('src/wcomr/cara_fast_b36_')]
    operators+=['src/wcomr/__init__.py']
    for name in operators:
        if name not in files:files[name]=base64.b64encode((ROOT/name).read_bytes()).decode()
        hashes[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    return dict(action='prepare',stage=STAGE,files=files,hashes=hashes,CPU_proof=proof,core_CPU_proof=core,
        authority=authority,base_stage=original_launch['stage'],base_registration_sha256=original_launch['registration_sha256'],
        base_source_revision=original_launch['source_revision'],runtime_source_sha256=original['runtime_source_sha256'],
        source_revision=revision,operator_sources={name:hashes[name] for name in operators})


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['prepare','provision','admit','reserve','launch','status'])
    parser.add_argument('--authorization',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    assert not args.output.exists()
    proof=read(ROOT/PROOF)
    operators={name:expected for name,expected in proof['critical_source_sha256'].items()
               if name.startswith('src/wcomr/cara_fast_b36_')}
    payload=dict(action=args.action,stage=STAGE,operator_sources=operators)
    if args.action=='prepare':
        assert args.authorization is not None,'Supply the receipt of explicit human B approval'
        authority=read(args.authorization)
        validate_grant(authority,read(ROOT/PROFILE))
        current=four_ssh(CENTRAL,dict(action='read',CPU_stage=proof['receipts']['four_card']['launch']['stage'],job={},
            sources={name:value for name,value in proof['critical_source_sha256'].items() if name.startswith('src/')}),timeout=60)
        require(current['job'] is None,'Original B central job exists; recover it before any preparation')
        revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        payload=payload_for_authority(authority,proof,read(ROOT/CORE),revision)
    if args.action in ('provision','launch'):payload['sudo_password']=password()
    if args.action=='reserve':
        admission=ssh(REMOTE,dict(payload,action='admit'),docker_group=True,timeout=1800)
        auth=admission['authorization']
        job={key:auth[key] for key in ('run_id','phase','physical_paths','host','gpu_uuid','launch_id','source_revision',
            'scope_sha256','registration_sha256','A_launch_id','frozen_file_sha256')}
        job.update(job_id=RUN,stage=STAGE,billed_limit_GPUh=5.5,forecast_GPUh=read(ROOT/PROFILE)['hosts']['two_card']['stage_B_forecast_GPUh'],
            authorization_sha256=admission['authorization_sha256'])
        central=dict(CPU_stage=proof['receipts']['four_card']['launch']['stage'],
            sources={name:value for name,value in proof['critical_source_sha256'].items() if name.startswith('src/')},job=job,gpu=admission['gpu'])
        envelope=four_ssh(CENTRAL,central,timeout=60)
        with args.output.with_suffix('.central.json').open('x') as handle:json.dump(envelope,handle,indent=2);handle.write('\n')
        result=ssh(REMOTE,dict(payload,action='bind',envelope=envelope),docker_group=True,timeout=90)
        result['central_envelope']=envelope
    else:
        if args.action=='launch':
            payload['central_state']=four_ssh(CENTRAL,dict(action='read',CPU_stage=proof['receipts']['four_card']['launch']['stage'],job={},
                sources={name:value for name,value in proof['critical_source_sha256'].items() if name.startswith('src/')}),timeout=60)
        result=ssh(REMOTE,payload,docker_group=True,timeout=1800 if args.action=='admit' else 300 if args.action=='provision' else 90)
    with args.output.open('x') as handle:json.dump(result,handle,indent=2,allow_nan=False);handle.write('\n')
    print(json.dumps({key:result.get(key) for key in ('status','launch_id','stage','guardian_identity','progress','GPU_submissions')}))


if __name__=='__main__':
    main()
