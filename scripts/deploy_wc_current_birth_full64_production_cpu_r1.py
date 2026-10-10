#!/usr/bin/env python3
"""Transport a complete prepared64 production CPU card, with zero GPU work."""
import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile

DRIVER = r'''import hashlib,json,os,pathlib,subprocess,sys,time
stage=pathlib.Path(sys.argv[1]);root=stage.parent.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
c=json.loads((stage/'current-birth-full64-config.json').read_text())
assert not c['GPU_execution_selected'] and c['single_job_exception_authority'] is None
r={'status':'CURRENT_BIRTH_FULL64_PRODUCTION_CPU_RUNNING_NOT_GPU','pid':os.getpid(),
 'source_revision':sys.argv[2],'started_unix':time.time(),'GPU_submissions':0,
 'CUDA_initialized':False,'ledger_written':False,'GPU_lock_acquired':False,
 'budget_before_sha256':sha(root/'reports/budget.json'),'payload_sha256':c['payload_sha256']}
def save():
 p=stage/'receipt.json';t=p.with_suffix('.tmp');t.write_text(json.dumps(r,indent=2)+chr(10));t.replace(p)
assert not (stage/'receipt.json').exists();save();start=time.perf_counter()
try:
 assert {n:sha(stage/n) for n in c['payload_sha256']}==c['payload_sha256']
 env=dict(os.environ,CUDA_VISIBLE_DEVICES='',HF_HUB_CACHE=str(root/'hfhub'),HF_HUB_OFFLINE='1',
  TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
 cmd=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python',
  str(stage/'scripts/run_wc_current_birth_full64_r1.py'),'--project',str(root),'--stage',str(stage),'--cpu-check']
 with (stage/'test.log').open('x') as log:
  child=subprocess.Popen(cmd,cwd=root/'runtime',env=env,stdout=log,stderr=subprocess.STDOUT)
  r['child_pid']=child.pid;save();r['child_exit_code']=child.wait()
 assert r['child_exit_code']==0
 candidates=[]
 for line in (stage/'test.log').read_text().splitlines():
  if line.startswith('{'):
   try:v=json.loads(line)
   except ValueError:continue
   if v.get('status')=='CURRENT_BIRTH_FULL64_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU':candidates.append(v)
 assert len(candidates)==1;v=candidates[0]
 assert not v['CUDA_initialized'] and v['GPU_submissions']==0
 assert v['registered_scope']==c['preregistration']['scope_counts'] and v['payload_sha256']==c['payload_sha256']
 assert v['complete_method_parameter_sets']==16 and v['guardrail_less_entry_refused_both_strategies']
 (stage/'result.json').write_text(json.dumps(v,indent=2)+chr(10))
 r.update(status='CURRENT_BIRTH_FULL64_PRODUCTION_CPU_PASS_NOT_GPU',exit_code=0,
  result_sha256=sha(stage/'result.json'),config_binding_sha256=v['config_binding_sha256'],
  production_contract_mutation_refusals=v['production_contract_mutation_refusals'])
except BaseException as error:r.update(status='CURRENT_BIRTH_FULL64_PRODUCTION_CPU_FAILED_COMPLETE_SCOPE_RETAINED',
 exit_code=1,error_type=type(error).__name__,error=str(error))
finally:
 r.update(CPU_wall_seconds=time.perf_counter()-start,ended_unix=time.time(),
  budget_after_sha256=sha(root/'reports/budget.json'),payload_after_sha256={n:sha(stage/n) for n in c['payload_sha256']})
 if r['payload_after_sha256']!=c['payload_sha256']:r.update(status='FULL64_PRODUCTION_CPU_SOURCE_CHANGED',exit_code=1)
 if r['budget_after_sha256']!=r['budget_before_sha256']:r.update(status='FULL64_PRODUCTION_CPU_BUDGET_CHANGED',exit_code=1)
 save()
raise SystemExit(r['exit_code'])
'''


def main():
    config_ref=Path('configs/wc_current_birth_full64_production_r1_20261010.json')
    if not config_ref.exists():
        print(json.dumps({'status':'WAIT_FULL256_ACCEPTANCE_AND_COMPLETE64_CONFIG_NO_DEPLOYMENT','GPU_submissions':0}));return 2
    c=json.loads(config_ref.read_text());assert not c['GPU_execution_selected']
    compile(DRIVER,'full64_production_CPU_driver','exec')
    revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    assert config_ref.read_bytes()==subprocess.check_output(['git','show',revision+':'+str(config_ref)])
    launch=Path('reports/wc_current_birth_full64_production_cpu_r1_launch_20261010.json');assert not launch.exists()
    generated=Path('.sync/current-birth-full64-inputs-r1')
    files={}
    for name,expect in c['payload_sha256'].items():
        path=generated/name if name in ('profile-config.json','current-birth-full64-requests.jsonl','budget-at-preparation.json') else Path(name)
        raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==expect
        if path==Path(name):assert raw==subprocess.check_output(['git','show',revision+':'+name])
        files[name]=raw
    # Reuse immutable files, or recreate the exact captured gzip from its
    # original remote bytes. Full tensors/videos never enter this transport.
    roots=['.sync/wc-current-birth-sampling-cpu-r3-20261010',
        '.sync/wc-current-birth-real-inputs-cpu-r3-20261010']
    native={}
    for proofref in (c['batch_cpu_audit_ref'],
        'reports/wc_current_birth_real_inputs_cpu_r3_terminal_20261010_capture.json',
        'reports/wc_ra_plus_a_r1_terminal_20261010_capture_and_independent_audit.json'):
        proof=json.loads(Path(proofref).read_text())
        for item in proof['files'].values():
            if item.get('local_path') in files and item.get('path'):
                native[item['local_path']]={'path':item['path'],'sha256':c['payload_sha256'][item['local_path']]}
                roots.append(str(Path(item['path']).parent))
    packet={'sha256':c['payload_sha256'],'roots':list(dict.fromkeys(roots)),'native':native}
    inventory='P='+repr(packet)+'\n'+r'''
import gzip,hashlib,json,pathlib
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');out={}
for name,expect in P['sha256'].items():
 for source in P['roots']:
  p=root/source/name
  if p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==expect:
   out[name]={'path':str(p),'gzip':False};break
 if name not in out and name in P['native']:
  p=pathlib.Path(P['native'][name]['path'])
  if p.is_file():
   raw=gzip.compress(p.read_bytes(),compresslevel=1,mtime=0)
   if hashlib.sha256(raw).hexdigest()==expect:out[name]={'path':str(p),'gzip':True}
print(json.dumps(out))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],
        input=inventory,text=True,capture_output=True,timeout=55)
    if call.returncode:raise RuntimeError(call.stderr[-1500:])
    copied=json.loads(call.stdout)
    delta={n:b for n,b in files.items() if n not in copied}
    delta.update({'current-birth-full64-config.json':config_ref.read_bytes(),'driver.py':DRIVER.encode()})
    archive=io.BytesIO()
    with tarfile.open(fileobj=archive,mode='w:gz') as tar:
        for name,raw in delta.items():
            entry=tarfile.TarInfo(name);entry.size=len(raw);tar.addfile(entry,io.BytesIO(raw))
    raw=archive.getvalue();stem='wc-current-birth-full64-production-cpu-r1-20261010'
    local=Path('.sync')/(stem+'.tgz');assert not local.exists();local.write_bytes(raw)
    remote='/home/gaokuangda/data/gkd/worldcache_omr/.sync/'+stem+'.tgz'
    subprocess.run(['scp','-q','-o','BatchMode=yes','-o','ConnectTimeout=15',str(local),'gkd_minchen:'+remote],check=True,timeout=600)
    packet={'remote':remote,'archive_sha256':hashlib.sha256(raw).hexdigest(),'source_revision':revision,
        'driver_sha256':hashlib.sha256(DRIVER.encode()).hexdigest(),'stage_name':stem,'copied':copied,
        'payload_sha256':c['payload_sha256'],'config_sha256':hashlib.sha256(config_ref.read_bytes()).hexdigest()}
    code='P='+repr(packet)+'\n'+r'''
import gzip,hashlib,io,json,os,pathlib,subprocess,tarfile,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=root/'.sync'/P['stage_name'];assert not stage.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
raw=pathlib.Path(P['remote']).read_bytes();assert hashlib.sha256(raw).hexdigest()==P['archive_sha256']
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as tar:
 for item in tar.getmembers():
  p=pathlib.PurePosixPath(item.name);assert item.isfile() and not p.is_absolute() and '..' not in p.parts
 stage.mkdir()
 for name,source in P['copied'].items():
  data=pathlib.Path(source['path']).read_bytes()
  if source['gzip']:data=gzip.compress(data,compresslevel=1,mtime=0)
  assert hashlib.sha256(data).hexdigest()==P['payload_sha256'][name]
  p=stage/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 tar.extractall(stage)
assert {n:sha(stage/n) for n in P['payload_sha256']}==P['payload_sha256']
assert sha(stage/'driver.py')==P['driver_sha256'] and sha(stage/'current-birth-full64-config.json')==P['config_sha256']
with (stage/'driver.log').open('x') as log:
 child=subprocess.Popen(['python3',str(stage/'driver.py'),str(stage),P['source_revision']],
  stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
v={'stage':str(stage),'supervisor_pid':child.pid,'source_revision':P['source_revision'],
 'archive_sha256':P['archive_sha256'],'driver_sha256':P['driver_sha256'],'config_sha256':P['config_sha256'],
 'copied_or_exact_gzip_regenerated_files':len(P['copied']),'GPU_submissions':0,'ledger_written':False,'observed_unix':time.time()}
(stage/'launch.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],
        input=code,text=True,capture_output=True,timeout=55)
    if call.returncode:raise RuntimeError(call.stderr[-1500:])
    value=json.loads(call.stdout);launch.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value));return 0


if __name__=='__main__':raise SystemExit(main())
