"""Explicit source preparation/status and one future admitted launch; no scheduler."""
import argparse
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import uuid

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
REL=str(HERE.relative_to(ROOT))
BASE_REL='plans/cara_next_stage_20261104/sensitivity'
REPORT=ROOT/'reports/cara_sparse_refresh_probe_r1_20261105'
sys.path[:0]=[str(ROOT),str(ROOT/'src'),str(ROOT/'scripts')]
from wcomr.immutable_stage_payload_r1 import local_python_closure


def rpc(*args,**kwargs):
    # Host/CPU entry imports must not require the Mac-only SSH credentials path.
    from cara_f19_speed190_transport_r1 import rpc as transport
    return transport(*args,**kwargs)


def load_base(manifest):
    previous=sys.argv;sys.argv=[previous[0],'--manifest',str(manifest)]
    spec=importlib.util.spec_from_file_location('sparse_lifecycle_base',ROOT/BASE_REL/'ops.py')
    base=importlib.util.module_from_spec(spec)
    try:spec.loader.exec_module(base)
    finally:sys.argv=previous
    original_gpu=base.GPU
    base.HERE=HERE;base.REL=REL;base.GPU=base.CONFIG['gpu_uuid']
    matrix_requests=base.REQUESTS;base.REQUESTS=base.CONFIG['counts']['total_requests']
    for key in ('PREFIX','PRECHECK','INSTALL','CPU','CPU_STATUS','PROVISION','STORAGE_STATUS','ADMIT','CENTRAL','DISPATCH','STATUS','CAPTURE'):
        setattr(base,key,getattr(base,key).replace(BASE_REL,REL).replace(original_gpu,base.GPU)
            .replace(f'request_count={matrix_requests}',f'request_count={base.REQUESTS}'))
    # Deploy source now; the physical GPU and unique authority are bound only
    # after the future launch command's live precheck has passed.
    site=";create(stage/'GPU-authorization.json',p['authority'])"
    assert base.INSTALL.count(site)==1
    base.INSTALL=base.INSTALL.replace(site,'')
    base.CENTRAL=base.CENTRAL.replace('from wcomr.wc73_execution_r1 import Pool,admit_host',
        'from wcomr.wc73_execution_r1 import Pool,admit_host,hold')
    base.CENTRAL=base.CENTRAL.replace("   admit_host(value,'two_card')",'''   active=[j for j in value['jobs'].values() if j['status']=='RESERVED_OR_RUNNING' and not hold(j)]
   assert all(j.get('run_id')=='cara-generator-v1-confirm10-r1-20261105' and j.get('host')=='two_card' and j.get('gpu_uuid')!=auth['gpu_uuid'] for j in active),'Other allocation or selected GPU is already reserved' ''')
    base.PRECHECK=base.PRECHECK.replace("print(json.dumps(dict(","value=dict(").replace(
        "if l.startswith('MemAvailable:'))))))", "if l.startswith('MemAvailable:'))))")
    base.PRECHECK+='''
confirm=root/'.sync/cara-budget-calibration-GPU-generator-v1-confirm10-r1-20261105'
launch=read(confirm/'GPU-launch.json') if (confirm/'GPU-launch.json').exists() else None
qstate=subprocess.run(['docker','inspect','--format','{{json .State}}',confirm.name+'-gpu'],capture_output=True,text=True)
state=json.loads(qstate.stdout) if qstate.returncode==0 else None
value['confirm10']=dict(gpu_uuid=launch['gpu_uuid'] if launch else 'GPU-cebf7119-cf03-23b9-e192-cd196332b704',
 launch_id=launch['launch_id'] if launch else None,running=bool(state and state['Running']),
 claiming=bool((confirm/'GPU-intent.json').exists() and not (confirm/'billing.json').exists()))
if (stage/'registration.json').exists():value['registration']=read(stage/'registration.json')
print(json.dumps(value))
'''
    base.STATUS=base.STATUS.replace('print(json.dumps(v))','''
v['stage_prepared']=stage.exists()
v['production_CPU_passed']=(stage/'CPU-proof.json').exists() and read(stage/'CPU-proof.json')['passed']
v['storage_prepared']=(stage/'history104-storage.json').exists() or (stage/'storage-state.json').exists()
v['GPU_launch_exists']=(stage/'GPU-launch.json').exists()
s1=root/'outputs'/run/'s1.json'
if s1.exists():
 s=read(s1);v['S1']=dict(status=s['status'],gate_passed=s['gate']['gate_passed'])
 if 'progress' in v:v['progress'].update(S2_completed=v['progress']['completed'],S2_denominator=8,completed=v['progress']['completed']+1,denominator=9)
print(json.dumps(v))
''')
    return base


def bind_gpu(base,selected):
    previous=base.GPU;base.GPU=selected
    for key in ('PREFIX','ADMIT','DISPATCH','STATUS','CAPTURE'):
        setattr(base,key,getattr(base,key).replace(previous,selected))


def payload(base):
    data=base.payload()
    seeds=[BASE_REL+'/'+name for name in ('ops.py','runner.py','sampling.py','provision.py')]
    seeds+=['plans/cara_next_stage_20261105/g17_minitest/prepare.py']
    seeds+=['tests/'+name+'.py' for name in ('test_cara_read_write_provenance_r1','test_cara_read_write_transition_r1',
        'check_cara_pg_production_sampling_cpu_r1','check_partial_mlp_guided_sampling_cpu_r1','check_full_sampling',
        'check_rv0_video_actions_cpu','check_rv0_restore_cpu','check_rv0_actions_cpu')]
    files=local_python_closure(ROOT,seeds)
    for name in ('plans/cara_next_stage_20261028/mainline/RUN_MANIFEST.json',
            'plans/cara_next_stage_20261101/e1/ENDPOINT7_46_MANIFEST_R1.json'):
        files[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    for name,digest in files.items():
        raw=(ROOT/name).read_bytes()
        assert hashlib.sha256(subprocess.check_output(['git','show',data['revision']+':'+name],cwd=ROOT)).hexdigest()==digest,name
        data['files'][name]=base64.b64encode(raw).decode();data['hashes'][name]=digest
    return data


def selected_idle(precheck,preferred):
    # This is the live boundary: no authorization or ledger mutation precedes it.
    if precheck['MemAvailable_kib']*1024<50*2**30:
        raise ValueError('Host MemAvailable below unchanged50GiB admission gate')
    busy={line.split(',')[0].strip() for line in precheck['compute_apps'].splitlines() if line.strip()}
    confirm=precheck['confirm10'];excluded=confirm['gpu_uuid'] if confirm['running'] or confirm['claiming'] else None
    idle=[]
    for line in precheck['GPUs'].splitlines():
        gpu,name,util,used,total,mode,temp=(v.strip() for v in line.split(','))
        if gpu!=excluded and gpu not in busy and float(util)==0 and int(used)<=1024 and mode=='Default' and float(temp)<90:
            idle.append(gpu)
    if not idle:raise ValueError('No admissible idle GPU other than active confirm10')
    return preferred if preferred in idle else idle[0]


def launch(base,route,receipt,preferred):
    if receipt.exists():raise ValueError('Original launch receipt exists; use status/capture, never replay')
    card=base.CONFIG;q=card['quote']
    assert q['forecast_GPUh']<=1.05 and q['range_GPUh'][1]<=1.05 and q['hard_GPUh']==1.05
    live=rpc(base.PRECHECK,{},route=route)
    selected=selected_idle(live,preferred);bind_gpu(base,selected)
    assert live['stage_exists'] and live['registration']['scope_sha256']==card['scope_sha256']
    auth=dict(run_id=base.RUN,launch_id=uuid.uuid4().hex,host='two_card',gpu_uuid=selected,
        stage=live['registration']['stage'],source_revision=live['registration']['source_revision'],
        scope_sha256=card['scope_sha256'],billed_limit_GPUh=1.05,execution_authorized=True,
        direct_user_authorization=True,user_quote=card['authority']['user_quote'],
        reservation_event=card['reservation_event'],authorizes_replay=False,CPU_fixture_only=False,
        central_transaction_authorized=True,cumulative_budget_policy='RUNNING_TOTAL_NO_CUMULATIVE_CAP',authorization_date='2026-11-05')
    code=base.PREFIX+'''
assert not any((stage/n).exists() for n in ('GPU-intent.json','GPU-launch.json','GPU-dispatch.json')),'Recover original launch'
assert read(stage/'CPU-proof.json')['passed'] and read(stage/'storage-state.json')['status']=='TWO_CARD_PRIVATE16_STORAGE_PROVISIONED_NO_GPU'
auth=p['authority']
if (stage/'GPU-authorization.json').exists():
 original=read(stage/'GPU-authorization.json');assert original['gpu_uuid']==auth['gpu_uuid'] and original['source_revision']==auth['source_revision'];auth=original
else:create(stage/'GPU-authorization.json',auth)
print(json.dumps(auth))
'''
    authority=rpc(code,dict(authority=auth),route=route)
    assert authority.get('execution_authorized') is True,authority
    admission=rpc(base.ADMIT,{},route=route,timeout=300)
    assert admission.get('authorization',{}).get('launch_id')==authority['launch_id'],admission
    reserved=rpc(base.CENTRAL,dict(action='reserve',admission=admission),host='four_card',route=route)
    assert reserved.get('job',{}).get('launch_id')==authority['launch_id'],reserved
    result=dict(precheck={k:v for k,v in live.items() if k!='registration'},admission=admission,reservation=reserved)
    receipt.parent.mkdir(parents=True,exist_ok=True);receipt.write_text(json.dumps(result,indent=2)+'\n')
    snapshot=dict(reserved['central_after'],observed_unix=reserved['observed_unix'])
    dispatched=rpc(base.DISPATCH,dict(envelope=reserved,snapshot=snapshot),route=route)
    result['dispatch']=dispatched;receipt.write_text(json.dumps(result,indent=2)+'\n')
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('deploy','cpu','cpu-status','provision','storage-status','precheck','launch','status','capture','settle','launch-host','ledger-snapshot'))
    p.add_argument('--manifest',type=Path,default=HERE/'manifest.json');p.add_argument('--route',choices=('relay',),default='relay')
    p.add_argument('--receipt',type=Path);p.add_argument('--input',type=Path)
    p.add_argument('--gpu-uuid');p.add_argument('--project',type=Path);p.add_argument('--stage',type=Path)
    args=p.parse_args();base=load_base(args.manifest)
    if args.action=='launch-host':
        auth=json.loads((args.stage/'GPU-authorization.json').read_text());bind_gpu(base,auth['gpu_uuid'])
        base.launch_host(args.project,args.stage);return
    if args.action=='launch':
        result=launch(base,args.route,args.receipt or REPORT/'launch.json',args.gpu_uuid or base.GPU)
    elif args.action=='deploy':result=rpc(base.INSTALL,payload(base),route=args.route)
    elif args.action=='ledger-snapshot':
        code=base.PREFIX+'''
sys.path[:0]=['/tmp/cara-F19-CAL35-central-f17bfbf0d188491a8821bb65604cb679/src']
from wcomr.wc73_execution_r1 import Pool
pool=Pool(root);value=pool.read()
print(json.dumps(dict(ledger_sha256=sha(pool.path),used_GPUh=value['used_gpu_hours'],reserved_GPUh=value['reserved_gpu_hours'],
 events=len(value['events']),job=value['jobs'].get(run),ledger_writes=0)))
'''
        result=rpc(code,{},host='four_card',route=args.route)
    elif args.action=='settle':
        assert args.input is not None
        data=json.loads(args.input.read_text());data['action']='settle'
        result=rpc(base.CENTRAL,data,host='four_card',route=args.route)
    else:
        code=dict(cpu=base.CPU,**{'cpu-status':base.CPU_STATUS},provision=base.PROVISION,
            **{'storage-status':base.STORAGE_STATUS},precheck=base.PRECHECK,status=base.STATUS,capture=base.CAPTURE)[args.action]
        result=rpc(code,{},route=args.route)
    if args.receipt and args.action!='launch':
        assert not args.receipt.exists(),'Preserve existing observation'
        args.receipt.parent.mkdir(parents=True,exist_ok=True);args.receipt.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
