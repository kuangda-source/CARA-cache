"""Select only the accepted complete E4c stage; actual admission stays locked."""
import json
from pathlib import Path
import subprocess


def main():
    root = Path(__file__).resolve().parents[1]
    source = json.loads((root/'reports/wc_e4c_source_age_production_cpu_r1_launch_20261011.json').read_text())
    proof = json.loads((root/'reports/wc_e4c_source_age_production_cpu_r1_terminal_20261011_capture.json').read_text())
    assert proof['exit_code'] == 0 and proof['original_source_actual_entry_contract_and_wrapper_independently_verified']
    target = root/'reports/wc_e4c_source_age_gpu_r1_launch_20261011.json'; assert not target.exists()
    packet = {'source': source, 'production_receipt_sha256': proof['files']['production-CPU-receipt.json']['sha256'],
        'dispatch_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()}
    code = 'P='+repr(packet)+'\n'+r'''import fcntl,hashlib,json,os,pathlib,shutil,subprocess,sys,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');old=pathlib.Path(P['source']['stage'])
sys.path.insert(0,str(old/'src'))
from wcomr.e4c_source_age_production_r1 import CONFIG,RUN,UUID,sha,write,binding,validate,validate_selected,admit
c,*_=validate(root,old);r=json.loads((old/'production-CPU-receipt.json').read_text())
assert r['exit_code']==r['child_exit_code']==0 and r['source_revision']==P['source']['source_revision']
assert sha(old/'production-CPU-receipt.json')==P['production_receipt_sha256']
assert not any(pathlib.Path('/proc/'+str(pid)).exists() for pid in (r['pid'],r['child_pid']))
assert r['config_binding_sha256']==binding(c) and r['payload_after_sha256']==c['payload_sha256']
sys.path.insert(0,str(old/'scripts'));from supervise_wc_e4c_source_age_r1 import observe
ledger=json.loads((root/'reports/budget.json').read_text());gpu=observe(UUID);admit(c,ledger,gpu,r)
lock=(root/'.sync/f1.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
fcntl.flock(lock,fcntl.LOCK_UN);lock.close()
s=root/'.sync/wc-e4c-source-age-selected-r1-20261011'
assert not s.exists() and not (root/'outputs'/RUN).exists();s.mkdir()
for n in list(c['payload_sha256'])+['production-CPU-receipt.json','production-CPU.log','registration.json']:
 target=s/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(old/n,target)
original_binding=binding(c)
c.update(GPU_execution_selected=True,gpu_uuid=UUID,production_CPU_receipt_sha256=sha(old/'production-CPU-receipt.json'))
assert binding(c)==original_binding;write(s/CONFIG,c);validate(root,s);validate_selected(c,s)
selection={'source_revision':r['source_revision'],'dispatch_revision':P['dispatch_revision'],
 'selected_config_sha256':sha(s/CONFIG),'production_CPU_receipt_sha256':sha(s/'production-CPU-receipt.json'),
 'original_CPU_stage':str(old),'config_binding_sha256':original_binding}
write(s/'selection.json',selection)
command=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python',
 str(s/'scripts/supervise_wc_e4c_source_age_r1.py'),'--project',str(root),'--stage',str(s),'--source-revision',r['source_revision']]
with (s/'GPU-supervisor.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
  env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
value={'status':'E4C_COMPLETE_SOURCE_AGE_DISPATCHED_LOCKED_ADMISSION_STILL_IN_SUPERVISOR',
 'source_revision':r['source_revision'],'dispatch_revision':P['dispatch_revision'],'stage':str(s),
 'GPU_supervisor_pid':child.pid,'forecast_complete_GPUh':c['forecast_complete_GPUh'],
 'scope_counts':c['scope_counts'],'selected_config_sha256':sha(s/CONFIG),
 'preselection_live_resource':gpu,'preselection_used_GPUh':ledger['used_gpu_hours'],
 'GPU_submissions_at_dispatch_return_not_claimed':True,'observed_unix':time.time()}
write(s/'GPU-launch.json',value);print(json.dumps(value))
'''
    call = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', 'gkd_minchen',
        '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -'],
        input=code, text=True, capture_output=True)
    if call.returncode: raise RuntimeError(call.stderr[-3000:])
    value = json.loads(call.stdout); target.write_text(json.dumps(value, indent=2)+'\n'); print(json.dumps(value))


if __name__ == '__main__': main()
