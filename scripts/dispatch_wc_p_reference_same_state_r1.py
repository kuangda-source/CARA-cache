"""No SSH or selected stage until exact ready full-card above8 approval exists."""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def main():
    root=Path(__file__).resolve().parents[1]
    authority_ref='manifests/wc_p_reference_same_state_direct_authorization_20261011.json';authority=root/authority_ref
    if not authority.exists():
        print(json.dumps({'status':'WAIT_EXACT_P_REFERENCE_COMPLETE_ABOVE8_APPROVAL_NO_DISPATCH',
            'GPU_submissions':0,'SSH_called':False,'ledger_written':False,'new_selected_directory':False}));return 2
    sys.path.insert(0,str(root/'src'))
    from wcomr.p_reference_same_state_production_r1 import UUID,binding,sha
    from wcomr.p_reference_same_state_execution_r1 import exact_authorization
    reg=json.loads((root/'manifests/wc_p_reference_same_state_execution_cpu_r1_preregistration_20261011.json').read_text())
    c=json.loads((root/reg['config_ref']).read_text());p=json.loads((root/reg['protocol_ref']).read_text())
    approved=json.loads(authority.read_text());exact_authorization(c,approved)
    proof=json.loads((root/'reports/wc_p_reference_same_state_execution_cpu_r1_terminal_20261011_capture.json').read_text())
    assert proof['exit_code']==0 and proof['original_complete_post_selection_sources_and_actual_readers_independently_verified']
    assert proof['actual_reader']['tensors']==1160
    item=proof['originals']['execution-CPU-receipt.json'];raw=gzip.decompress((root/item['local_path']).read_bytes())
    assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256'];r=json.loads(raw)
    assert r['exit_code']==0 and r['method_binding_sha256']==binding(c) and r['protocol_sha256']==reg['protocol_sha256']
    assert r['method_payload_after_sha256']==c['payload_sha256'] and r['execution_payload_after_sha256']==p['execution_payload_sha256']
    c.update(GPU_execution_selected=True,gpu_uuid=UUID,production_CPU_receipt_sha256=p['original_production_CPU_receipt_sha256'],
        single_job_exception_authority={'ref':authority_ref,'sha256':sha(authority)})
    assert binding(c)==approved['config_binding_sha256']
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    assert authority.read_bytes()==subprocess.check_output(['git','show',revision+':'+authority_ref],cwd=root)
    target=root/'reports/wc_p_reference_same_state_selected_pipeline_r1_launch_20261011.json';assert not target.exists()
    packet={'stage':'.sync/wc-p-reference-same-state-selected-r1-20261011','original':'.sync/wc-p-reference-same-state-execution-cpu-r1-20261011',
        'method_payload':c['payload_sha256'],'execution_payload':p['execution_payload_sha256'],
        'execution_CPU_receipt_sha256':item['sha256'],'production_CPU_receipt_sha256':p['original_production_CPU_receipt_sha256'],
        'protocol_sha256':reg['protocol_sha256'],'selected_config':c,'source_revision':revision,
        'authority_ref':authority_ref,'authority_bytes':authority.read_text()}
    code='P='+repr(packet)+'\n'+r'''import hashlib,json,os,pathlib,shutil,subprocess,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');old=root/P['original'];stage=root/P['stage']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((old/'execution-CPU-receipt.json').read_text());assert r['exit_code']==0 and sha(old/'execution-CPU-receipt.json')==P['execution_CPU_receipt_sha256']
assert not pathlib.Path('/proc/'+str(r['pid'])).exists()
assert r['method_payload_after_sha256']==P['method_payload'] and r['execution_payload_after_sha256']==P['execution_payload']
assert sha(old/'production-CPU-receipt.json')==P['production_CPU_receipt_sha256']
budget=json.loads((root/'reports/budget.json').read_text())
if any('inflight' in n for n in budget):
 print(json.dumps({'status':'WAIT_ORIGINAL_INFLIGHT_NO_SELECTED_STAGE_CREATED','GPU_submissions':0,'ledger_written':False}));raise SystemExit(0)
assert P['selected_config']['forecast_complete_GPUh']<=budget['cap_gpu_hours']-budget['used_gpu_hours']
assert not stage.exists() and not (root/'outputs'/P['selected_config']['run_id']).exists();stage.mkdir()
for n,h in {**P['method_payload'],**P['execution_payload']}.items():
 assert sha(old/n)==h
 target=stage/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(old/n,target)
assert sha(old/'p-reference-execution-protocol.json')==P['protocol_sha256']
for name in ('p-reference-execution-protocol.json','production-CPU-receipt.json','execution-CPU-receipt.json','registration.json'):
 shutil.copyfile(old/name,stage/name)
(stage/'p-reference-same-state-config.json').write_text(json.dumps(P['selected_config'],indent=2)+'\n')
path=stage/P['authority_ref'];path.parent.mkdir(parents=True,exist_ok=True);path.write_text(P['authority_bytes'])
python='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
command=[python,str(stage/'scripts/select_and_launch_wc_p_reference_same_state_r1.py'),
 '--project',str(root),'--stage',str(stage),'--source-revision',P['source_revision']]
with (stage/'selected-driver.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
  env=dict(os.environ,CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1'))
result={'status':'P_REFERENCE_SELECTED_CPU_PIPELINE_STARTED_GPU_NOT_YET_SUBMITTED','stage':str(stage),
 'selected_driver_pid':child.pid,'source_revision':P['source_revision'],'config_sha256':sha(stage/'p-reference-same-state-config.json'),
 'protocol_sha256':sha(stage/'p-reference-execution-protocol.json'),'observed_unix':time.time(),
 'GPU_submissions_at_return':0,'ledger_written_by_deployment':False}
(stage/'selected-pipeline-launch.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],input=code,text=True,capture_output=True)
    if call.returncode:raise RuntimeError(call.stderr[-2500:])
    result=json.loads(call.stdout)
    if result['status']=='WAIT_ORIGINAL_INFLIGHT_NO_SELECTED_STAGE_CREATED':print(json.dumps(result));return 2
    target.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));return 0


if __name__=='__main__':raise SystemExit(main())
