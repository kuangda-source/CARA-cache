"""Frozen Q1 prepare/recover/admit/capture/settle commands, one central envelope.

Only launch consumes a new human authorization. Every ambiguous operation is
recover-only; no command retries a GPU submission or falls back after dispatch.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import uuid

import cara_two_card_transport_r1 as transport

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from wcomr.sq_q1_spec_r1 import RUN,COUNTS,LIMITS,QUOTES,SCOPE,PROFILE,EXECUTION_CRITICAL
from wcomr.sq_q1_execution_r1 import require


def remote(host,code,data=None,timeout=180):
    return (transport.ssh(code,data,docker_group=True,timeout=timeout) if host=='two_card'
            else transport.four_ssh(code,data,timeout=timeout))


PREFIX="""
import json,os,sys,time,socket,subprocess
from pathlib import Path
p=json.load(sys.stdin);project=Path('/data20t/gaokuangda/worldcache_workspace')
host=p['host'];stage=project/'.sync'/('cara-sq-q1-saved-'+host.replace('_','-')+'-r2-20261029')
os.environ['CUDA_VISIBLE_DEVICES']=''
sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
"""

RECOVER="""
import json,sys,subprocess
from pathlib import Path
p=json.load(sys.stdin);project=Path('/data20t/gaokuangda/worldcache_workspace')
stage=project/'.sync'/('cara-sq-q1-saved-'+p['host'].replace('_','-')+'-r2-20261029')
value=dict(status='Q1_ORIGINAL_HANDLE_RECOVERY_ONLY',host=p['host'],stage=str(stage),
 stage_exists=stage.exists(),handles={},GPU_submissions=0,ledger_writes=0)
for version in ('r1-20261028','r2-20261029'):
 original=project/'.sync'/('cara-sq-q1-saved-'+p['host'].replace('_','-')+'-'+version)
 for name in ('GPU-intent.json','GPU-dispatch-consumed.json','GPU-launch.json','pg-host-guardian.json'):
  if (original/name).exists():value['handles'][version+'/'+name]=json.loads((original/name).read_text())
 q=subprocess.run(['docker','inspect','--type','container',original.name+'-gpu'],capture_output=True,text=True,timeout=20)
 if q.returncode==0:
  actual=json.loads(q.stdout)[0]
  value['handles'][version+'/container']=dict(id=actual['Id'],state=actual['State'])
 elif q.returncode!=1 or q.stderr.strip() not in ('Error: No such object: '+original.name+'-gpu','Error: No such container: '+original.name+'-gpu','Error response from daemon: No such container: '+original.name+'-gpu'):
  value['handles'][version+'/container_observation']=dict(status='UNKNOWN_RECOVER_ONLY')
pool=project/'reports/gpu-budget-v2.json'
value['central_job']=json.loads(pool.read_text())['jobs'].get(p['run']) if p['host']=='four_card' and pool.exists() else None
print(json.dumps(value))
"""


def recover_both():
    return {host:remote(host,RECOVER,dict(host=host,run=RUN)) for host in LIMITS}


def select_host(probes):
    for host in ('four_card','two_card'):
        if probes[host]['admissible']:return host
    raise ValueError('No fully admissible Q1 host; prepare or wait without reserving/dispatching')


def selected_authority(approval,probe):
    host=probe['host']
    require(probe['admissible'] and 0<=time.time()-probe['observed_unix']<=60
        and probe['storage_contract_sha256'] is not None
        and approval['direct_user_authorization'] is True and bool(approval['user_quote'])
        and approval['run_id']==RUN and approval['scope_counts']==COUNTS
        and approval['allowed_host_hard_limits_GPUh']==LIMITS
        and approval['host_policy']=='PREFER_ADMISSIBLE_FOUR_ELSE_TWO'
        and approval['source_revision']==probe['source_revision']
        and approval['scope_sha256']==probe['scope_sha256']
        and approval['CPU_proof_sha256']==probe['CPU_proof_sha256']
        and approval['quote_sha256'][host]==probe['quote_sha256']
        and approval['authorizes_retry'] is False and approval['authorizes_S_collection'] is False,
        'Direct source-bound authority for this complete Q1-only card is required')
    return dict(direct_user_authorization=True,user_quote=approval['user_quote'],run_id=RUN,host=host,
        scope_counts=COUNTS,whole_GPUh=LIMITS[host],gpu_uuid=probe['selected_gpu']['uuid'],
        launch_id=str(uuid.uuid4()),source_revision=probe['source_revision'],scope_sha256=probe['scope_sha256'],
        CPU_proof_sha256=probe['CPU_proof_sha256'],quote_sha256=probe['quote_sha256'],
        storage_contract_sha256=probe['storage_contract_sha256'],
        registration_sha256=probe['registration_sha256'],authorizes_retry=False,authorizes_S_collection=False)


def bound_controller(revision):
    # This unused prepared source predates the host allocation clock. It must
    # not launch while the source-bound correction and CPU proof are prepared.
    require(revision!='f3be7662175889c77e3719521fecb9c4d3be83af',
        'Original Q1 readiness withdrawn: host admission/container/release billing is incomplete; use the corrected complete CPU-accepted source')
    # Remote workers use the complete immutable stage registration. A later
    # unrelated shared-file edit must not rebind that frozen remote package.
    local_names=('scripts/cara_sq_q1_control_r1.py','src/wcomr/sq_q1_spec_r1.py',
        'src/wcomr/sq_q1_execution_r1.py','src/wcomr/wc73_execution_r1.py','src/wcomr/gpu_budget_pool_v2.py')
    for name in local_names:
        require(subprocess.check_output(['git','show',revision+':'+name],cwd=ROOT)==(ROOT/name).read_bytes(),
            'Use the exact prospectively CPU-accepted Q1 controller source: '+name)


def prepare(args):
    launch=json.loads(args.cpu_launch.read_text());raw=args.cpu_proof.read_text();proof=json.loads(raw)
    require(launch['source_revision']==proof['source_revision'],'Original CPU launch/proof source differs')
    code="""
import json,sys,hashlib
from pathlib import Path
p=json.load(sys.stdin);base=Path(p['base']);root=base.parents[1]
for name,digest in p['proof']['critical_source_sha256'].items():
 assert hashlib.sha256((base/name).read_bytes()).hexdigest()==digest,'Accepted CPU source differs'
sys.path[:0]=[str(base/'src'),str(base/'scripts')]
from wcomr.sq_q1_stage_r1 import install
print(json.dumps(install(root,p['host'],base,p['proof'],p['proof_raw'],p['base_registration_sha256'])))
"""
    return remote(args.host,code,dict(host=args.host,base=launch['stage'],proof=proof,proof_raw=raw,
        base_registration_sha256=launch['registration_sha256']))


def reuse_inputs(args):
    recovered=recover_both()
    require(not any(value['handles'] or value['central_job'] is not None for value in recovered.values()),
            'Recover every old/corrected Q1 intent before rebinding prepared inputs')
    expected=json.loads(args.inputs_ref.read_text())
    code=PREFIX+"\nfrom wcomr.sq_q1_stage_r1 import reuse_prepared_inputs\nprint(json.dumps(reuse_prepared_inputs(project,host,p['expected'])))"
    return remote(args.host,code,dict(host=args.host,expected=expected))


def preflight_both():
    code=PREFIX+"\nfrom wcomr.sq_q1_stage_r1 import preflight\nprint(json.dumps(preflight(project,host)))\n"
    return {host:remote(host,code,dict(host=host)) for host in LIMITS}


def launch(args):
    recovered=recover_both()
    if any(value['handles'] or value['central_job'] is not None for value in recovered.values()):
        return dict(status='Q1_EXISTING_INTENT_OR_ENVELOPE_RECOVER_ONLY',original=recovered,GPU_submissions=0)
    probes=preflight_both();host=select_host(probes);probe=probes[host]
    bound_controller(probe['source_revision'])
    authority=selected_authority(json.loads(args.authorization.read_text()),probe)
    # Check the shared balance before creating a host intent; reserve itself
    # repeats this atomically against the original four-card ledger.
    pool=remote('four_card',PREFIX+"\nfrom wcomr.sq_q1_execution_r1 import Pool\nprint(json.dumps(Pool(project).read()))",
                dict(host='four_card'))
    from wcomr.sq_q1_execution_r1 import Pool
    from wcomr.wc73_execution_r1 import admit_host
    require(Pool.accounting(pool)['available_gpu_hours']>=LIMITS[host],'Whole Q1 funds unavailable')
    admit_host(pool,host)
    intent=remote(host,PREFIX+"\nfrom wcomr.sq_q1_stage_r1 import prepare_intent\nprint(json.dumps(prepare_intent(project,host,p['authority'])))",
                  dict(host=host,authority=authority))
    code=PREFIX+"""
from wcomr.sq_q1_execution_r1 import Pool,read,require
from wcomr.sq_q1_spec_r1 import QUOTES,COUNTS,RUN
require(host=='four_card' and read(stage/'registration.json')['native_hostname']==socket.gethostname(),
 'Only the registered central four-card host may reserve Q1')
authority=p['authority'];quote=read(stage/QUOTES[authority['host']])
require(read(stage/'execution-CPU-proof.json')['source_revision']==authority['source_revision'],
 'Central execution source differs')
job=dict(job_id=RUN,run_id=RUN,scope_counts=COUNTS,host=authority['host'],gpu_uuid=authority['gpu_uuid'],
 forecast_GPUh=quote['forecast_complete_GPUh'],billed_limit_GPUh=authority['whole_GPUh'],
 **{key:authority[key] for key in ('launch_id','source_revision','scope_sha256','registration_sha256')},
 authorization_sha256=p['authorization_sha256'],stage=p['selected_stage'])
value=Pool(project).reserve(job,p['gpu'])
print(json.dumps(dict(central_ledger_host='four_card',new_reservation=True,job=value['jobs'][RUN])))
"""
    envelope=remote('four_card',code,dict(host='four_card',authority=authority,
        authorization_sha256=intent['authorization_sha256'],selected_stage=probe['stage'],gpu=probe['selected_gpu']))
    if host=='two_card':secret=transport.password()
    else:
        from wc_four_card_price_refresh_gpu_r1 import saved_secret
        secret=saved_secret()
    data=dict(host=host,envelope=envelope,intent_sha256=intent['intent_sha256'],sudo_password=secret)
    try:
        return remote(host,PREFIX+"\nfrom wcomr.sq_q1_stage_r1 import dispatch\nprint(json.dumps(dispatch(project,host,p['envelope'],p['intent_sha256'],p.pop('sudo_password'))))",data)
    except Exception as error:
        return dict(status='Q1_HANDOFF_UNKNOWN_RECOVER_ORIGINAL_ONLY',host=host,launch_id=authority['launch_id'],
            intent=intent,central_envelope=envelope,error_type=type(error).__name__,authorizes_retry=False)
    finally:data.pop('sudo_password',None);secret=None


def capture(args):
    launch=json.loads(args.launch.read_text());host=launch['host']
    code=PREFIX+"\nfrom wcomr.sq_q1_capture_r1 import capture\nprint(json.dumps(capture(project,stage,p['launch_sha256']),allow_nan=False))"
    return remote(host,code,dict(host=host,launch_sha256=hashlib.sha256(args.launch.read_bytes()).hexdigest()))


def settle(args):
    captured=json.loads(args.capture.read_text())
    code=PREFIX+"""
from wcomr.sq_q1_execution_r1 import Pool,read,require
from wcomr.sq_q1_spec_r1 import SCOPE
from wcomr.sq_q1_terminal_r1 import settle_original
from wcomr.gpu_budget_pool_v2 import sha
require(host=='four_card' and read(stage/'registration.json')['native_hostname']==socket.gethostname(),
 'Only the original four-card central host may settle')
require(sha(stage/'src/wcomr/sq_q1_terminal_r1.py')==p['capture']['terminal_validator_sha256'],
 'Use the original source-bound terminal validator')
print(json.dumps(settle_original(Pool(project),p['capture'],read(stage/SCOPE)),allow_nan=False))
"""
    return remote('four_card',code,dict(host='four_card',capture=captured))


def analyse(args):
    captured=json.loads(args.capture.read_text());settlement=json.loads(args.settlement.read_text())
    host=json.loads(captured['files']['launch']['raw_utf8'])['host']
    code=PREFIX+"""
from wcomr.sq_q1_execution_r1 import read
from wcomr.sq_q1_spec_r1 import SCOPE,RUN
from wcomr.sq_q1_terminal_r1 import audit_settlement,technical_terminal
from wcomr.gpu_budget_pool_v2 import atomic_json,process_identity
from wcomr.sq_q1_stage_r1 import exclusive_json
from postprocess_cara_sq_q1_r1 import container_arguments
audit_settlement(p['capture'],read(stage/SCOPE),p['settlement'])
technical_terminal(p['capture'],read(stage/SCOPE))
directory=project/'outputs'/RUN/'CPU-post'
if directory.exists():
 print(json.dumps(dict(status='Q1_ORIGINAL_CPU_POST_EXISTS_RECOVER_ONLY',directory=str(directory))))
 raise SystemExit(0)
directory.mkdir(mode=0o700)
atomic_json(directory/'capture.json',p['capture']);atomic_json(directory/'settlement.json',p['settlement'])
command=container_arguments(project,stage,directory)
exclusive_json(directory/'CPU-intent.json',dict(command=command,created_unix=time.time(),GPU_submissions=0))
with (directory/'CPU.log').open('x') as log:
 child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
result=dict(status='Q1_RELEASED_CPU_POST_STARTED',host=host,stage=str(stage),directory=str(directory),
 container=stage.name+'-post-cpu',identity=process_identity(child.pid),started_unix=time.time(),
 resource_limits=dict(CPUs=2,RAM_GiB=8,wall_seconds=300),GPU_submissions=0,ledger_writes=0)
atomic_json(directory/'CPU-launch.json',result);print(json.dumps(result))
"""
    return remote(host,code,dict(host=host,capture=captured,settlement=settlement))


def post_capture(args):
    launch=json.loads(args.launch.read_text());host=launch['host']
    code=PREFIX+"""
from wcomr.sq_q1_execution_r1 import read,require
from wcomr.gpu_budget_pool_v2 import sha,same_live_process
directory=Path(p['launch']['directory']);require(read(directory/'CPU-launch.json')==p['launch'],'Original CPU post handle differs')
q=subprocess.run(['docker','inspect',p['launch']['container']],capture_output=True,text=True,timeout=20)
con=json.loads(q.stdout)[0] if q.returncode==0 else None
result=dict(status='Q1_CPU_POST_CAPTURE',launch=p['launch'],
 original_handle_live=same_live_process(p['launch']['identity']),
 container_state=con['State'] if con else None,GPU_submissions=0,ledger_writes=0)
path=directory/'analysis.json'
if con and not con['State']['Running'] and path.exists():result.update(analysis=read(path),analysis_sha256=sha(path))
print(json.dumps(result))
"""
    return remote(host,code,dict(host=host,launch=launch))


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=('prepare','recover','preflight','launch','capture','settle',
        'assets','assets-status','provision','native-probe','analyse','post-capture','reuse-inputs'))
    p.add_argument('--host',choices=tuple(LIMITS));p.add_argument('--output',type=Path,required=True)
    for name in ('cpu-launch','cpu-proof','authorization','launch','capture','settlement','inputs-ref'):p.add_argument('--'+name,type=Path)
    args=p.parse_args();require(not args.output.exists(),'Preserve original Q1 controller output')
    if args.command=='provision':
        if args.host=='two_card':secret=transport.password()
        else:
            from wc_four_card_price_refresh_gpu_r1 import saved_secret
            secret=saved_secret()
        data=dict(host=args.host,sudo_password=secret)
        try:
            result=remote(args.host,PREFIX+"\nfrom wcomr.sq_q1_stage_r1 import provision_storage\nprint(json.dumps(provision_storage(project,host,p.pop('sudo_password'))))",data)
        finally:data.pop('sudo_password',None);secret=None
    elif args.command in ('assets','assets-status','native-probe'):
        action={'assets':'start_assets','assets-status':'assets_status','native-probe':'native_probe'}[args.command]
        code=PREFIX+'\nfrom wcomr.sq_q1_stage_r1 import '+action+'\nprint(json.dumps('+action+'(project,host)))'
        result=remote(args.host,code,dict(host=args.host))
    else:
        result=(recover_both() if args.command=='recover' else preflight_both() if args.command=='preflight'
                else globals()[args.command.replace('-','_')](args))
    with args.output.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(status=result.get('status'),output=str(args.output))))


if __name__=='__main__':main()
