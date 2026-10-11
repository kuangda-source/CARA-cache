"""Independently read original two-entry CPU lifecycle and frozen459 bytes."""
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess


REMOTE = r'''import base64,gzip,hashlib,json,pathlib,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr')
s=root/'.sync/wc-p-reference-same-state-production-cpu-r2-20261011'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
launch=json.loads((s/'launch.json').read_text());r=json.loads((s/'production-CPU-receipt.json').read_text())
assert launch==P['launch'] and launch['source_revision']==r['source_revision'] and launch['supervisor_pid']==r['pid']
ids=[r['pid']]+[c['pid'] for c in r.get('actual_entry_children',[])]
if any(pathlib.Path('/proc/'+str(p)).exists() for p in ids):
 print(json.dumps({'status':'WAIT_ORIGINAL_P_REFERENCE_TWO_FLOW_PRODUCTION_CPU','pids':ids,'observed_unix':time.time()}));raise SystemExit(0)
assert sha(s/'registration.json')==P['registration_sha256'] and sha(s/'p-reference-same-state-config.json')==P['config_sha256']
c=json.loads((s/'p-reference-same-state-config.json').read_text())
dynamic={'GPU_execution_selected','gpu_uuid','production_CPU_receipt_sha256','single_job_exception_authority'}
binding=hashlib.sha256(json.dumps({k:v for k,v in c.items() if k not in dynamic},sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
assert r['status']=='P_REFERENCE_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU' and r['exit_code']==0 and r['child_exit_codes']==[0,0]
assert r['config_binding_sha256']==binding and r['GPU_submissions']==0 and not r['CUDA_initialized'] and not r['ledger_written']
assert not c['GPU_execution_selected'] and c['single_job_exception_authority'] is None
assert len(c['payload_sha256'])==459 and {n:sha(s/n) for n in c['payload_sha256']}==c['payload_sha256']==r['payload_after_sha256']
assert r['budget_before_sha256']==r['budget_after_sha256']
assert len(r['actual_entry_results'])==2 and [v['flow'] for v in r['actual_entry_results']]==[False,True]
assert len(r['required_GPU_startup_asset_refusals'])==4
assert len(r['admission_refusals'])==9 and r['admission_refusals'][-1]=='above8_missing_exact_whole_card_approval'
assert r['synthetic_admission_is_not_live_GPU_admission'] and r['synthetic_above8_gate_is_not_direct_human_authorization']
assert r['original_two_flow_full_sampler_CPU_proof_reused'] and r['original_native_meta_CPU_proof_reused']
mode=r['native_mode_meta_CPU_result'];assert mode['parameter_count']==2059174912 and not mode['cuda_initialized']
assert mode['mode']['after']['training_modules']==0 and mode['contract_sha256']==c['model_mode_contract_sha256']
for arm,v in zip(['FLOW_OFF','FLOW_ON'],r['actual_entry_results']):
 assert v['arm']==arm and v['config_binding_sha256']==binding and v['scope_counts']==c['scope_counts']
 assert v['per_flow_scope_counts']['total_pair_computations']==344 and not v['CUDA_initialized'] and v['GPU_submissions']==0
 assert len(v['contract_mutation_refusals'])==10 and v['guardrail_less_entry_refused']
 assert v['payload_sha256']==c['payload_sha256']
 proof=v['production_entry_inverse_proof'];assert proof['accepted_E4c_actual_entry_inverse_bytes_equal'] and proof['full_native_heads_and_copy_gates_preserved']
 lines=[]
 for line in (s/('production-CPU-'+arm+'.log')).read_text().splitlines():
  try:x=json.loads(line)
  except ValueError:continue
  if isinstance(x,dict) and x.get('status')=='P_REFERENCE_ACTUAL_PRODUCTION_ENTRY_CPU_PASS_NOT_GPU':lines.append(x)
 assert lines==[v]
accepted=json.loads((s/c['sampling_CPU_capture_ref']).read_text())
assert accepted['actual_reloaded_files']==88 and accepted['actual_reloaded_tensors']==1160 and accepted['actual_direct_tensor_comparisons']==420
assert accepted['candidate_restore_operations']==240 and accepted['D_source_control_equalities']==96
assert not (root/'outputs'/c['run_id']).exists()
originals={}
for name in ['launch.json','registration.json','p-reference-same-state-config.json','production-CPU-receipt.json','driver.log','production-CPU-FLOW_OFF.log','production-CPU-FLOW_ON.log']:
 raw=(s/name).read_bytes();originals[name]={'remote_path':str(s/name),'bytes':len(raw),'sha256':sha(s/name),'gzip_base64':base64.b64encode(gzip.compress(raw,mtime=0)).decode()}
print(json.dumps({'status':'P_REFERENCE_TWO_FLOW_ACTUAL_PRODUCTION_CPU_INDEPENDENTLY_ACCEPTED_NOT_GPU','original_PIDs_absent':ids,
 'source_revision':r['source_revision'],'config_binding_sha256':binding,'CPU_wall_seconds':r['CPU_wall_seconds'],
 'complete_frozen_files_unchanged':459,'actual_flow_entry_results':r['actual_entry_results'],'original_sampler_CPU_proof_reused':True,
 'contract_refusals':20,'guardrail_less_refusals':2,'asset_refusals':4,'admission_refusals':9,
 'original_2B_native_meta_proof_reused':True,'exact_above8_human_approval_received':False,'GPU_submissions':0,'ledger_written':False,
 'original_GPU_queue_not_altered':True,'live_budget_observation':json.loads((root/'reports/budget.json').read_text()),
 'observed_unix':time.time(),'originals':originals}))
'''


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); root = Path(__file__).resolve().parents[1]
    target = args.output if args.output.is_absolute() else root/args.output
    assert not target.exists()
    launch = json.loads((root/'reports/wc_p_reference_same_state_production_cpu_r2_launch_20261011.json').read_text())
    reg_ref = root/'manifests/wc_p_reference_same_state_production_cpu_r2_preregistration_20261011.json'
    reg = json.loads(reg_ref.read_text())
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    packet = {'launch': launch, 'registration_sha256': sha(reg_ref), 'config_sha256': sha(root/reg['config_ref'])}
    call = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', 'gkd_minchen', 'python3 -'],
        input='P='+repr(packet)+'\n'+REMOTE, text=True, capture_output=True)
    if call.returncode: raise RuntimeError(call.stderr[-3000:])
    value = json.loads(call.stdout)
    if value['status'].startswith('WAIT_'): print(json.dumps(value)); return 2
    folder = target.with_suffix(''); assert not folder.exists(); folder.mkdir()
    for name, item in value['originals'].items():
        data = base64.b64decode(item.pop('gzip_base64')); raw = gzip.decompress(data)
        assert len(raw) == item['bytes'] and hashlib.sha256(raw).hexdigest() == item['sha256']
        dest = folder/(name+'.gz'); dest.write_bytes(data)
        item['local_path'] = str(dest.relative_to(root))
        item['gzip_sha256'] = sha(dest)
    target.write_text(json.dumps(value, indent=2)+'\n')
    print(json.dumps({k: value[k] for k in ['status', 'original_PIDs_absent', 'source_revision',
        'CPU_wall_seconds', 'complete_frozen_files_unchanged', 'contract_refusals', 'admission_refusals', 'GPU_submissions']}))
    return 0


if __name__ == '__main__': raise SystemExit(main())
