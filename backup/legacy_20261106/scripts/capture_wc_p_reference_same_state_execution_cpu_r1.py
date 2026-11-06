"""Original execution CPU handles plus independent full88 saved-vector reads."""
import argparse
import ast
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess


REMOTE = r'''import base64,gzip,hashlib,json,pathlib,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');s=root/'.sync/wc-p-reference-same-state-execution-cpu-r1-20261011'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
launch=json.loads((s/'launch.json').read_text());r=json.loads((s/'execution-CPU-receipt.json').read_text())
assert launch==P['launch'] and launch['pid']==r['pid'] and launch['source_revision']==r['source_revision']
if pathlib.Path('/proc/'+str(r['pid'])).exists():
 print(json.dumps({'status':'WAIT_ORIGINAL_COMPLETE_P_REFERENCE_EXECUTION_CPU','pid':r['pid'],'observed_unix':time.time()}));raise SystemExit(0)
assert sha(s/'registration.json')==P['registration_sha256'] and sha(s/'p-reference-same-state-config.json')==P['config_sha256']
assert sha(s/'p-reference-execution-protocol.json')==P['protocol_sha256']
c=json.loads((s/'p-reference-same-state-config.json').read_text());p=json.loads((s/'p-reference-execution-protocol.json').read_text())
assert {n:sha(s/n) for n in c['payload_sha256']}==c['payload_sha256']==r['method_payload_after_sha256']
assert {n:sha(s/n) for n in p['execution_payload_sha256']}==p['execution_payload_sha256']==r['execution_payload_after_sha256']
assert len(c['payload_sha256'])==459 and len(p['execution_payload_sha256'])==23
assert r['status']=='P_REFERENCE_COMPLETE_EXECUTION_CPU_PASS_NOT_GPU' and r['exit_code']==0
assert r['GPU_submissions']==0 and not r['ledger_written'] and not r['CUDA_initialized']
assert not c['GPU_execution_selected'] and c['single_job_exception_authority'] is None
assert r['budget_before_sha256']==r['budget_after_sha256']
raw=r['actual_reader'];assert (raw['files'],raw['tensors'],raw['direct_comparisons'],raw['points'],raw['D_source_equalities'])==(88,1160,420,48,96)
assert len(raw['partial_point_refusals'])==9 and raw['actual_old_GPU_video_frames_decoded']==372
terminal=r['terminal_and_exact_authority_controls']
assert (terminal['complete_parent_slots'],terminal['complete_event_slots'],terminal['complete_suffix_slots'],terminal['complete_point_slots'])==(8,8,32,48)
assert len(terminal['inventory_refusals'])==7 and len(terminal['authority_refusals'])==6
assert terminal['original_live_handle_refusals']==3 and len(terminal['isolated_launch_cases'])==2
assert len(r['whole_two_flow_supervisor_lifecycle_controls'])==4
assert all(v['one_temporary_ledger_job_charged'] and v['whole_paths_retained']==8 for v in r['whole_two_flow_supervisor_lifecycle_controls'])
assert raw['reader_proof']['original_five_readout_reader_inverse_bytes_and_AST_equal']
# Independently re-read the complete original88 and all five errors using the
# previous manual capture's source, not the new post/reader implementation.
independent={'P':P['original_CPU_packet'],'__name__':'independent_old_full_scope_capture'}
exec(compile(P['independent_reader_prefix'],'<original-manual-full88-reader>','exec'),independent)
assert (len(independent['files']),independent['tensors'],independent['direct'],len(independent['all_points']),independent['restores'],independent['D_controls'])==(88,1160,420,48,240,96)
assert all(v['frames']==93 and sha(pathlib.Path(v['path']))==v['sha256'] for v in raw['actual_old_GPU_videos'])
assert not (root/'outputs'/c['run_id']).exists() and sha(s/'execution-CPU-receipt.json')==P['receipt_sha256']
originals={}
for name in ['launch.json','registration.json','p-reference-same-state-config.json','p-reference-execution-protocol.json','production-CPU-receipt.json','execution-CPU-receipt.json','driver.log']:
 data=(s/name).read_bytes();originals[name]={'remote_path':str(s/name),'bytes':len(data),'sha256':sha(s/name),'gzip_base64':base64.b64encode(gzip.compress(data,mtime=0)).decode()}
print(json.dumps({'status':'P_REFERENCE_COMPLETE_POST_SELECTION_CPU_INDEPENDENTLY_ACCEPTED_NOT_GPU','exit_code':0,
 'original_complete_post_selection_sources_and_actual_readers_independently_verified':True,
 'original_PID_absent':r['pid'],'source_revision':r['source_revision'],'CPU_wall_seconds':r['CPU_wall_seconds'],
 'method_files_unchanged':459,'execution_files_unchanged':23,'protocol_sha256':P['protocol_sha256'],
 'method_binding_sha256':r['method_binding_sha256'],'actual_reader':raw,
 'independent_manual_full_scope_reads':{'files':88,'tensors':1160,'direct_comparisons':420,'points':48,'complete_restores':240,'D_source_equalities':96},
 'terminal_and_exact_authority_controls':terminal,'whole_two_flow_supervisor_lifecycle_controls':r['whole_two_flow_supervisor_lifecycle_controls'],
 'all_independent_CPU_error_records_not_scientific_result':independent['all_points'],
 'CUDA_initialized':False,'GPU_submissions':0,'ledger_written':False,
 'GPU_inflight_ledger_observation':json.loads((root/'reports/budget.json').read_text()),'observed_unix':time.time(),'originals':originals}))
'''


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); root = Path(__file__).resolve().parents[1]
    target = args.output if args.output.is_absolute() else root/args.output; assert not target.exists()
    launch = json.loads((root/'reports/wc_p_reference_same_state_execution_cpu_r1_launch_20261011.json').read_text())
    reg_ref = root/'manifests/wc_p_reference_same_state_execution_cpu_r1_preregistration_20261011.json'
    reg = json.loads(reg_ref.read_text()); sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    # Parse a literal data constant; importing the old capture is unnecessary.
    file = root/'scripts/capture_wc_p_reference_same_state_cpu_r3.py'; tree = ast.parse(file.read_text())
    assign = next(n for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'REMOTE' for t in n.targets))
    prefix = ast.literal_eval(assign.value).split('originals={}\n', 1)[0]
    assert 'print(json.dumps(' not in prefix.split('raise SystemExit(0)', 1)[1]
    oldlaunch = json.loads((root/'reports/wc_p_reference_same_state_cpu_r3_launch_20261011.json').read_text())
    oldreg = root/'manifests/wc_p_reference_same_state_cpu_r3_20261011.json'
    packet = {'launch': launch, 'registration_sha256': sha(reg_ref), 'config_sha256': sha(root/reg['config_ref']),
        'protocol_sha256': sha(root/reg['protocol_ref']),
        'original_CPU_packet': {'launch': oldlaunch, 'registration_sha256': sha(oldreg)},
        'independent_reader_prefix': prefix}
    # Read the original execution receipt SHA once, then bind the heavy audit
    # to it. Never treat a failed observation as a terminal original process.
    observe = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', 'gkd_minchen',
        'python3 -'], input='import hashlib,pathlib\np=pathlib.Path('+repr(launch['stage']+'/execution-CPU-receipt.json')+')\nprint(hashlib.sha256(p.read_bytes()).hexdigest())\n',
        text=True, capture_output=True)
    if observe.returncode: raise RuntimeError(observe.stderr[-2000:])
    packet['receipt_sha256'] = observe.stdout.strip()
    call = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', 'gkd_minchen',
        '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -'],
        input='P='+repr(packet)+'\n'+REMOTE, text=True, capture_output=True)
    if call.returncode: raise RuntimeError(call.stderr[-3000:])
    value = json.loads(call.stdout)
    if value['status'].startswith('WAIT_'): print(json.dumps(value)); return 2
    folder = target.with_suffix(''); assert not folder.exists(); folder.mkdir()
    for name, item in value['originals'].items():
        data = base64.b64decode(item.pop('gzip_base64')); raw = gzip.decompress(data)
        assert len(raw) == item['bytes'] and hashlib.sha256(raw).hexdigest() == item['sha256']
        destination = folder/(name+'.gz'); destination.write_bytes(data)
        item['local_path'] = str(destination.relative_to(root)); item['gzip_sha256'] = sha(destination)
    target.write_text(json.dumps(value, indent=2)+'\n')
    print(json.dumps({k: value[k] for k in ['status', 'source_revision', 'original_PID_absent', 'CPU_wall_seconds',
        'method_files_unchanged', 'execution_files_unchanged', 'independent_manual_full_scope_reads', 'GPU_submissions']}))
    return 0


if __name__ == '__main__': raise SystemExit(main())
