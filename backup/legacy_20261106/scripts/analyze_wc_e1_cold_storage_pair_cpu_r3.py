#!/usr/bin/env python3
"""Exercise planned cold storage pair on two exited real arms, read-only.

This is an audit implementation control, not a reduction of the GPU card.
All eight paths still require the original complete terminal audit.
"""
import ast
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    root=Path(__file__).resolve().parents[1]
    ref='manifests/wc_e1_diag8_r2_independent_terminal_cpu_scope_20261011.json'
    reg=json.loads((root/ref).read_text());helper=(root/reg['helper_ref']).read_bytes()
    assert hashlib.sha256(helper).hexdigest()==reg['helper_sha256']
    tree=ast.parse(helper)
    function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    assignment=next(n for n in function.body if isinstance(n,ast.Assign) and any(
        isinstance(t,ast.Name) and t.id=='code' for t in n.targets))
    raw=ast.literal_eval(assignment.value.right)
    start=raw.index('independent={}\n')
    stop=raw.index("lock=(project/'.sync/f1.lock').open('a+')",start)
    audit=raw[start:stop]
    changes=[
        ("if raw_audit is not None and any(out.rglob('*.pt')):",
         "if any((out/'ORIGINAL_COLD').rglob('*.pt')) and any((out/'CPU_COLD').rglob('*.pt')):"),
        (" for arm,process in zip(c['arms'],s['arms']):\n",
         " for arm,process in zip(c['arms'],s['arms']):\n  if arm['id'] not in ('ORIGINAL_COLD','CPU_COLD'):continue\n"),
        (" assert actual_files=={str(v.resolve()) for v in out.rglob('*.pt')}\n assert whole_paths==raw_audit['complete_numeric_paths']",
         " assert actual_files=={str(v.resolve()) for arm_id in ('ORIGINAL_COLD','CPU_COLD') for v in (out/arm_id).rglob('*.pt')}\n assert whole_paths==2")]
    recorded_check="""   recorded=[v for v in raw_audit['successful_storage_or_cold_prefix_comparisons'] if v['arms']==[a,b]
    and v['sample_name']==key[1] and v['method']==key[2]]
   assert len(recorded)==1 and recorded[0]['equal']==equal and recorded[0]['all_equal']==all(equal)
"""
    changes.append((recorded_check,''))
    changed=audit
    for before,after in changes:
        assert changed.count(before)==1;changed=changed.replace(before,after,1)
    inverse=changed
    for before,after in reversed(changes):
        if after:
            assert inverse.count(after)==1;inverse=inverse.replace(after,before,1)
        else:
            anchor="   comparisons.append({'arms':[a,b],'sample_name':key[1],'method':key[2],'equal':equal,'all_equal':all(equal)})\n"
            assert inverse.count(anchor)==1;inverse=inverse.replace(anchor,before+anchor,1)
    assert inverse==audit
    launch=json.loads((root/'reports/wc_e1_diag8_gpu_r2_launch_20261011.json').read_text())
    packet={'launch':launch,'version':'r2','helper_sha256':reg['helper_sha256'],
            'read_only_control_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    prefix='P='+repr(packet)+'\n'+r'''import hashlib,json,pathlib,os,time
L=P['launch'];stage=pathlib.Path(L['stage']);project=stage.parents[1];out=project/'outputs/wc-e1-cold-prefix-storage-diag8-r2'
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(4<<20),b''):h.update(b)
 return h.hexdigest()
c=json.loads((stage/'e1-diag8-r2-config.json').read_text());s=json.loads((out/'supervisor.json').read_text())
first=s['arms'][0];second=s['arms'][1]
assert first['id']=='ORIGINAL_COLD' and second['id']=='CPU_COLD' and first['exit_code']==second['exit_code']==0
assert not any(pathlib.Path('/proc/'+str(row['pid'])).exists() for row in (first,second))
assert s['pid']==L['GPU_supervisor_pid'] and s['source_revision']==L['source_revision']
assert sha(stage/'e1-diag8-r2-config.json')==s['config_sha256']==L['selected_config_sha256']
receipt=json.loads((out/'ORIGINAL_COLD/receipt.json').read_text())
assert sha(out/'ORIGINAL_COLD/receipt.json')==first['receipt_sha256']
assert receipt['status']=='E1_ARM_COMPLETE_REQUIRES_INDEPENDENT_CPU_AUDIT' and receipt['source_revision']==L['source_revision']
CPU_receipt=json.loads((out/'CPU_COLD/receipt.json').read_text())
assert sha(out/'CPU_COLD/receipt.json')==second['receipt_sha256']
assert CPU_receipt['status']==receipt['status'] and CPU_receipt['source_revision']==L['source_revision']
assert receipt['arm']['storage']=='ORIGINAL_GPU_DEEPCOPY' and CPU_receipt['arm']['storage']=='CPU_OWNED_STORAGE_SERIAL_RESTORE_R1'
assert receipt['config_sha256']==CPU_receipt['config_sha256']==L['selected_config_sha256']
before=sha(project/'reports/budget.json');start=time.perf_counter()
'''
    suffix=r'''
assert independent['actual_vector_files']==2 and independent['actual_tensors_reloaded']==74
assert independent['actual_complete_policy_decisions_replayed']==72
assert independent['whole_arm_accepted_numeric_paths']==2
assert len(independent['per_path'])==2 and [v['arm'] for v in independent['per_path']]==['ORIGINAL_COLD','CPU_COLD']
assert len(independent['direct_full36_and_final_comparisons'])==1
comparison=independent['direct_full36_and_final_comparisons'][0]
assert comparison['arms']==['ORIGINAL_COLD','CPU_COLD'] and len(comparison['equal'])==37
assert sha(out/'CPU_COLD/receipt.json')==second['receipt_sha256']
assert sha(out/'ORIGINAL_COLD/receipt.json')==first['receipt_sha256']
assert before==sha(project/'reports/budget.json')
print(json.dumps({'status':'E1_REAL_EXITED_COLD_STORAGE_PAIR_CPU_AUDIT_PASS_NOT_FULL8',
 'pid':os.getpid(),'source_revision':L['source_revision'],'helper_sha256':P['helper_sha256'],
 'read_only_control_sha256':P['read_only_control_sha256'],'CPU_wall_seconds':time.perf_counter()-start,
 'independent':independent,'original_planned_paths':8,'full_terminal_audit_not_yet_executed':True,
 'original_cold_PIDs_absent':[first['pid'],second['pid']],
 'cold_storage_output_equivalence_observed':comparison['all_equal'],
 'budget_before_and_after_sha256':before,'CUDA_initialized':torch.cuda.is_initialized(),
 'GPU_submissions':0,'ledger_written':False,'observed_unix':time.time()}))
'''
    code=prefix+changed+suffix;ast.parse(code)
    target=root/'reports/wc_e1_cold_storage_pair_readonly_cpu_r3_20261011.json';assert not target.exists()
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen',
        '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -'],
        input=code,text=True,capture_output=True)
    raw_path=root/'.sync/wc-e1-cold-storage-pair-readonly-cpu-r3-transport.json';assert not raw_path.exists()
    raw_path.write_text(json.dumps({'returncode':call.returncode,'stdout':call.stdout,'stderr':call.stderr},indent=2)+'\n')
    if call.returncode:raise RuntimeError(call.stderr[-3500:])
    result=json.loads(call.stdout)
    assert not result['CUDA_initialized'] and result['GPU_submissions']==0 and not result['ledger_written']
    assert result['helper_sha256']==reg['helper_sha256'] and result['read_only_control_sha256']==packet['read_only_control_sha256']
    result.update(extracted_helper_readonly_scope_sites=4,inverse_scope_change_bytes_equal=True,
        control_script_sha256=packet['read_only_control_sha256'],remote_input_code_sha256=hashlib.sha256(code.encode()).hexdigest())
    target.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
