#!/usr/bin/env python3
"""Exercise registered independent reader on one exited real arm, read-only.

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
         "if any((out/'ORIGINAL_COLD').rglob('*.pt')):"),
        (" for arm,process in zip(c['arms'],s['arms']):\n",
         " for arm,process in zip(c['arms'],s['arms']):\n  if arm['id']!='ORIGINAL_COLD':continue\n"),
        (" assert actual_files=={str(v.resolve()) for v in out.rglob('*.pt')}\n assert whole_paths==raw_audit['complete_numeric_paths']",
         " assert actual_files=={str(v.resolve()) for v in (out/'ORIGINAL_COLD').rglob('*.pt')}\n assert whole_paths==1")]
    changed=audit
    for before,after in changes:
        assert changed.count(before)==1;changed=changed.replace(before,after,1)
    inverse=changed
    for before,after in reversed(changes):
        assert inverse.count(after)==1;inverse=inverse.replace(after,before,1)
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
first=s['arms'][0];assert first['id']=='ORIGINAL_COLD' and first['exit_code']==0
assert not pathlib.Path('/proc/'+str(first['pid'])).exists()
assert s['pid']==L['GPU_supervisor_pid'] and s['source_revision']==L['source_revision']
assert sha(stage/'e1-diag8-r2-config.json')==s['config_sha256']==L['selected_config_sha256']
receipt=json.loads((out/'ORIGINAL_COLD/receipt.json').read_text())
assert sha(out/'ORIGINAL_COLD/receipt.json')==first['receipt_sha256']
assert receipt['status']=='E1_ARM_COMPLETE_REQUIRES_INDEPENDENT_CPU_AUDIT' and receipt['source_revision']==L['source_revision']
before=sha(project/'reports/budget.json');start=time.perf_counter()
'''
    suffix=r'''
assert independent['actual_vector_files']==1 and independent['actual_tensors_reloaded']==37
assert independent['actual_complete_policy_decisions_replayed']==36
assert independent['whole_arm_accepted_numeric_paths']==1
assert len(independent['per_path'])==1 and independent['per_path'][0]['arm']=='ORIGINAL_COLD'
assert independent['direct_full36_and_final_comparisons']==[]
assert sha(out/'ORIGINAL_COLD/receipt.json')==first['receipt_sha256']
assert before==sha(project/'reports/budget.json')
print(json.dumps({'status':'E1_INDEPENDENT_AUDIT_REAL_EXITED_COLD_CONTROL_CPU_PASS_NOT_FULL8',
 'pid':os.getpid(),'source_revision':L['source_revision'],'helper_sha256':P['helper_sha256'],
 'read_only_control_sha256':P['read_only_control_sha256'],'CPU_wall_seconds':time.perf_counter()-start,
 'independent':independent,'original_planned_paths':8,'full_terminal_audit_not_yet_executed':True,
 'budget_before_and_after_sha256':before,'CUDA_initialized':torch.cuda.is_initialized(),
 'GPU_submissions':0,'ledger_written':False,'observed_unix':time.time()}))
'''
    code=prefix+changed+suffix;ast.parse(code)
    target=root/'reports/wc_e1_independent_cold_audit_cpu_r2_20261011.json';assert not target.exists()
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen',
        '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -'],
        input=code,text=True,capture_output=True)
    raw_path=root/'.sync/wc-e1-independent-cold-audit-cpu-r2-transport.json';assert not raw_path.exists()
    raw_path.write_text(json.dumps({'returncode':call.returncode,'stdout':call.stdout,'stderr':call.stderr},indent=2)+'\n')
    if call.returncode:raise RuntimeError(call.stderr[-3500:])
    result=json.loads(call.stdout)
    assert not result['CUDA_initialized'] and result['GPU_submissions']==0 and not result['ledger_written']
    assert result['helper_sha256']==reg['helper_sha256'] and result['read_only_control_sha256']==packet['read_only_control_sha256']
    result.update(extracted_helper_readonly_scope_sites=3,inverse_scope_change_bytes_equal=True,
        control_script_sha256=packet['read_only_control_sha256'],remote_input_code_sha256=hashlib.sha256(code.encode()).hexdigest())
    target.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
