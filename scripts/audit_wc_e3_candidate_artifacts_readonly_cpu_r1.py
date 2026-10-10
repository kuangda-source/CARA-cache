"""Rehash ten evidence-qualified candidates, retaining the complete64 map."""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    root=Path(__file__).resolve().parents[1]
    refs=['reports/wc_e3_complete64_readonly_inventory_cpu_r1_20261011.json',
          'reports/wc_e3_e1_actual_native_metadata_cpu_r1_20261011.json',
          'reports/wc_e1_diag8_gpu_r2_terminal_20261011_capture.json',
          'reports/wc_full64_partial_recovery_cpu_r1_terminal_20261011_capture.json']
    inventory,metadata,e1,e0=[json.loads((root/n).read_text()) for n in refs]
    assert metadata['compatible_rows']==8 and metadata['additional_distinct_Human_candidates']==2
    assert e1['complete_numeric_paths']==8 and e1['original_source_terminal_scope_and_cost_independently_verified']
    item=e0['files']['result.json'];raw=gzip.decompress((root/item['local_ref']).read_bytes())
    assert hashlib.sha256(raw).hexdigest()==item['sha256'];old=json.loads(raw)
    refs.append(item['local_ref'])
    candidates=[]
    for row in inventory['all64_slots']:
        if row['classification']=='VALID_REFERENCE_COMPATIBLE_SCORED_REUSE_CANDIDATE_PENDING_E1':
            candidates.append({k:row[k] for k in ('strategy','sample_name','method','vector_artifact','video_artifact')})
            candidates[-1]['origin']='ORIGINAL_FAILED64_VALID_E0_PATH'
    for row in metadata['rows']:
        if row['arm']=='CPU_PREFIX' and row['sample_name']=='human_199' and row['pairing']['compatible']:
            candidates.append({k:row[k] for k in ('strategy','sample_name','method','vector_artifact','video_artifact')})
            candidates[-1]['origin']='E1_CPU_PREFIX_COMPLETE_ACTUAL_INPUT_MATCHED'
    keys=[(r['strategy'],r['sample_name'],r['method']) for r in candidates]
    assert len(keys)==len(set(keys))==10
    native=old['Native_files'];assert len(native)==4
    files=[]
    for r in candidates:
        for kind in ('vector_artifact','video_artifact'):files.append({'key':[*keys[candidates.index(r)],kind],**r[kind]})
    for r in native:files.append({'key':['NATIVE',r['sample_name']],**r['artifact']})
    packet={'files':files,'root':'/home/gaokuangda/data/gkd/worldcache_omr'}
    code='P='+repr(packet)+'\n'+r'''import hashlib,json,pathlib,time,os
root=pathlib.Path(P['root']);budget=root/'reports/budget.json'
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(4<<20),b''):h.update(block)
 return h.hexdigest()
before=sha(budget);started=time.perf_counter();rows=[]
for record in P['files']:
 path=pathlib.Path(record['path']).resolve()
 try:
  assert (root/'outputs').resolve() in path.parents and path.is_file()
  actual_bytes=path.stat().st_size;actual_sha=sha(path)
  ok=actual_bytes==record['bytes'] and actual_sha==record['sha256']
  rows.append({'key':record['key'],'path':str(path),'actual_bytes':actual_bytes,'actual_sha256':actual_sha,'matches_registered':ok})
 except (AssertionError,OSError) as error:rows.append({'key':record['key'],'path':str(path),'matches_registered':False,'error_type':type(error).__name__,'error':str(error)})
after=sha(budget)
print(json.dumps({'pid':os.getpid(),'observed_unix':time.time(),'CPU_wall_seconds':time.perf_counter()-started,
 'files':rows,'budget_before_sha256':before,'budget_after_sha256':after,'ledger_unchanged':before==after,
 'Torch_imported':False,'GPU_submissions':0,'ledger_written':False}))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],
                        input=code,text=True,capture_output=True)
    if call.returncode:raise RuntimeError(call.stderr[-2000:])
    remote=json.loads(call.stdout);assert remote['ledger_unchanged'] and len(remote['files'])==24
    bykey={tuple(v['key']):v for v in remote['files']};assert len(bykey)==24
    complete={k:r for k,r in zip(keys,candidates) if all(bykey[(*k,kind)]['matches_registered'] for kind in ('vector_artifact','video_artifact'))
              and bykey[('NATIVE',k[1])]['matches_registered']}
    slots=[]
    for original in inventory['all64_slots']:
        key=tuple(original[k] for k in ('strategy','sample_name','method'))
        row={k:original[k] for k in ('slot','strategy','sample_name','method','classification')}
        row.update(candidate_artifacts_rehashed_and_reference_qualified=key in complete,
                   E3_reuse_selected=False,new_complete_scope_generation_needed_if_selected=key not in complete)
        if key in complete:row['candidate_binding']=complete[key]
        slots.append(row)
    assert len(slots)==64 and sum(v['candidate_artifacts_rehashed_and_reference_qualified'] for v in slots)==len(complete)
    result=dict(status='E3_COMPLETE64_CANDIDATE_REHASH_READONLY_NOT_EXECUTION_OR_FINAL_REUSE_SELECTION',
                complete_scientific_positions=64,artifact_qualified_candidates=len(complete),
                proposed_fresh_positions_if_exact_candidates_selected=64-len(complete),all64_slots=slots,
                actual_remote_rehash=remote,original_missing_Human_prepare_not_synthesized=True,
                original_failed64_status_unchanged=True,E3_GPU_execution_selected=False,
                full_cost_forecast_and_production_block_CPU_still_required=True,GPU_submissions=0,ledger_written=False,
                source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in refs+['scripts/audit_wc_e3_candidate_artifacts_readonly_cpu_r1.py']})
    target=root/'reports/wc_e3_complete64_candidate_rehash_cpu_r1_20261011.json';assert not target.exists()
    target.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('status','complete_scientific_positions','artifact_qualified_candidates','proposed_fresh_positions_if_exact_candidates_selected','GPU_submissions')}))


if __name__=='__main__':main()
