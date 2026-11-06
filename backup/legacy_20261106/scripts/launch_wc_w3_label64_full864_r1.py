"""Dispatch one newly approved whole card; default remains local plan only."""
import argparse
import hashlib
import inspect
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
REMOTE_PROJECT='/home/gaokuangda/data/gkd/worldcache_omr'
REMOTE_PY='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
CONFIG='manifests/wc_w3_label64_parent18_full864_scope_r1_20261015.json'


def command(stage,project,revision,uuid,authorization):
    return [REMOTE_PY,'-u',str(Path(stage)/'scripts/supervise_wc_w3_label64_full864_r1.py'),
        '--project',str(project),'--stage',str(stage),'--source-revision',revision,
        '--gpu-uuid',uuid,'--authorization',str(authorization)]


def preflight(scope,launch,permission,uuid,proof,*,scope_sha256):
    from wcomr.w3_label64_production_contract_r1 import require_new_permission
    require_new_permission(scope,permission,proof,source_revision=launch['source_revision'],scope_sha256=scope_sha256)
    if (not isinstance(permission.get('user_reply_quote'),str) or not permission['user_reply_quote'].strip()
            or not isinstance(permission.get('launch_id'),str) or not permission['launch_id']
            or not isinstance(uuid,str) or not uuid.startswith('GPU-')):
        raise ValueError('Concrete fresh whole W3 permission and UUID required before SSH')


def dispatch(project,launch,permission,uuid):
    """Exact function sent to the server; CPU fixtures use fake process handles."""
    import fcntl
    root=Path(project).resolve();stage=Path(launch['stage']).resolve()
    if not stage.is_relative_to(root/'.sync'):raise ValueError('Project-owned stage required')
    sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    def store(path,value):
        temporary=path.with_name(path.name+'.tmp')
        temporary.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');temporary.replace(path)
    reg=json.loads((stage/'registration.json').read_text())
    if reg['source_revision']!=launch['source_revision'] or sha(stage/'registration.json')!=launch['registration_sha256']:
        raise ValueError('Original production CPU stage identity changed')
    for name,digest in reg['payload_sha256'].items():
        path=(stage/name).resolve()
        if not path.is_relative_to(stage) or sha(path)!=digest:raise ValueError('Immutable W3 payload changed')
    sys.path.insert(0,str(stage/'src'))
    from wcomr.w3_label64_production_r1 import SCOPE as CONFIG,RUN
    from wcomr.w3_label64_admission_r1 import verify_permission
    c=json.loads((stage/CONFIG).read_text());proof=json.loads((stage/'production-CPU-result.json').read_text())
    verify_permission(c,permission,proof,reg,scope_sha256=sha(stage/CONFIG),proof_sha256=sha(stage/'production-CPU-result.json'))
    if proof['registration_sha256']!=sha(stage/'registration.json'):raise ValueError('Production CPU registration changed')
    receipt_path=stage/'GPU-launch.json'
    if receipt_path.exists():
        original=json.loads(receipt_path.read_text())
        if (original['launch_id']!=permission['launch_id'] or original['source_revision']!=reg['source_revision']
                or original['new_authorization_sha256']!=hashlib.sha256(json.dumps(permission,sort_keys=True,allow_nan=False).encode()).hexdigest()):
            raise ValueError('Conflicting original dispatch; never resubmit')
        return {'status':'ORIGINAL_W3_DISPATCH_RETURNED_NO_RESTART','original':original}
    claim=stage/'GPU-dispatch-claim'
    if claim.exists():raise ValueError('Unknown original dispatch; inspect claim, never resubmit')
    if (root/'outputs'/RUN).exists():raise ValueError('Original run directory already exists')
    claim.mkdir()  # Atomic exclusion remains after timeout, crash or partial dispatch.
    store(claim/'request.json',{'launch_id':permission['launch_id'],'requested_unix':time.time()})
    auth=stage/'new-W3-GPU-authorization.json'
    with auth.open('x') as handle:json.dump(permission,handle,sort_keys=True,allow_nan=False);handle.write('\n')
    supervisor=[sys.executable,'-u',str(stage/'scripts/supervise_wc_w3_label64_full864_r1.py'),
        '--project',str(root),'--stage',str(stage),'--source-revision',reg['source_revision'],
        '--gpu-uuid',uuid,'--authorization',str(auth)]
    with (stage/'GPU-supervisor.log').open('x') as log:
        child=subprocess.Popen(supervisor,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
            start_new_session=True,env={**os.environ,'CUDA_VISIBLE_DEVICES':'','PYTHONDONTWRITEBYTECODE':'1'})
    result={'status':'W3_ORIGINAL_SUPERVISOR_DISPATCHED_POST_PENDING','supervisor_pid':child.pid,
        'launch_id':permission['launch_id'],'source_revision':reg['source_revision'],'stage':str(stage),
        'command':supervisor,'started_unix':time.time(),'forecast_complete_GPUh':proof['forecast_complete_GPUh'],
        'new_authorization_sha256':hashlib.sha256(json.dumps(permission,sort_keys=True,allow_nan=False).encode()).hexdigest(),
        'production_CPU_sha256':sha(stage/'production-CPU-result.json')}
    store(receipt_path,result)  # Preserve the original handle before starting post.
    post_command=[sys.executable,str(stage/'scripts/watch_wc_w3_label64_post_cpu_r1.py'),
        '--project',str(root),'--stage',str(stage),'--supervisor-pid',str(child.pid)]
    try:
        with (stage/'post-watcher.log').open('x') as log:
            post=subprocess.Popen(post_command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
                start_new_session=True,env={**os.environ,'CUDA_VISIBLE_DEVICES':'','PYTHONDONTWRITEBYTECODE':'1'})
        result.update(status='W3_LABEL64_FULL864_DISPATCHED_ADMISSION_PENDING',post_watcher_pid=post.pid,post_command=post_command)
    except BaseException as error:
        result.update(status='W3_ORIGINAL_SUPERVISOR_DISPATCHED_POST_FAILED',
            post_error_type=type(error).__name__,post_error=str(error));store(receipt_path,result);raise
    store(receipt_path,result);return result


def remote_code(launch,permission,uuid,project=REMOTE_PROJECT):
    code=('import hashlib,json,os,subprocess,sys,time\nfrom pathlib import Path\n'+inspect.getsource(dispatch)
        +'\nprint(json.dumps(dispatch('+repr(project)+','+repr(launch)+','+repr(permission)+','+repr(uuid)+')))\n')
    compile(code,'W3-full864-dispatch','exec');return code


def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--launch',action='store_true');p.add_argument('--cpu-launch-ref',type=Path,required=True)
    p.add_argument('--authorization',type=Path);p.add_argument('--gpu-uuid');p.add_argument('--output',type=Path)
    p.add_argument('--production-proof-ref',type=Path)
    a=p.parse_args(argv);launch=json.loads(a.cpu_launch_ref.read_text())['launch']
    if not a.launch:
        print(json.dumps({'status':'W3_FULL864_LOCAL_PLAN_NOT_LAUNCHED','stage':launch['stage'],
            'source_revision':launch['source_revision'],'GPU_submissions':0,'SSH_calls':0}));return
    if a.authorization is None or a.gpu_uuid is None or a.output is None or a.production_proof_ref is None:
        raise ValueError('Concrete new whole-card permission, fresh UUID and receipt required before SSH')
    if a.output.exists():raise ValueError('Do not repeat a locally recorded dispatch')
    sys.path.insert(0,str(ROOT/'src'))
    permission=json.loads(a.authorization.read_text());c=json.loads((ROOT/CONFIG).read_text())
    proof=json.loads(a.production_proof_ref.read_text())['production_result']
    preflight(c,launch,permission,a.gpu_uuid,proof,scope_sha256=hashlib.sha256((ROOT/CONFIG).read_bytes()).hexdigest())
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes',
        'gkd_minchen',REMOTE_PY+' -c '+shlex.quote(remote_code(launch,permission,a.gpu_uuid))],text=True,capture_output=True,timeout=120)
    result={'transport_exit_code':call.returncode,'stderr':call.stderr,'authorization_sha256':hashlib.sha256(a.authorization.read_bytes()).hexdigest()}
    try:result['dispatch']=json.loads(call.stdout)
    except json.JSONDecodeError:result['stdout']=call.stdout
    with a.output.open('x') as out:json.dump(result,out,indent=2);out.write('\n')
    print(json.dumps(result))
    if call.returncode:raise SystemExit(call.returncode)


if __name__=='__main__':main()
