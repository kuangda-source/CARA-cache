"""Select qualified reuse in all64 and preregister all54 bounded execution paths."""
import hashlib
import json
from pathlib import Path


def main():
    root=Path(__file__).resolve().parents[1]
    refs=['configs/wc_current_birth_full64_selected_r1_20261010.json',
          'reports/wc_e3_complete64_candidate_rehash_cpu_r1_20261011.json',
          'reports/wc_e3_e1_actual_native_metadata_cpu_r1_20261011.json',
          'reports/wc_e1_diag8_gpu_r2_terminal_20261011_capture.json',
          'reports/wc_e3_prepare_persistence_cpu_r2_terminal_20261011_capture.json']
    old,rehash,metadata,e1,persist=[json.loads((root/n).read_text()) for n in refs]
    assert rehash['complete_scientific_positions']==64 and rehash['artifact_qualified_candidates']==10
    assert all(v['matches_registered'] for v in rehash['actual_remote_rehash']['files'])
    assert metadata['compatible_rows']==8 and e1['complete_numeric_paths']==8
    assert persist['receipt']['exit_code']==0 and persist['source_and_original_terminal_receipts_independently_verified']
    methods=old['preregistration']['methods'];strategies=old['preregistration']['strategies']
    names=[r['name'] for r in old['preregistration']['requests']]
    expected=[(s,n,m) for s in strategies for n in names for m in methods]
    assert len(expected)==len(set(expected))==64
    slots=[]
    for index,(key,row) in enumerate(zip(expected,rehash['all64_slots'])):
        assert key==tuple(row[k] for k in ('strategy','sample_name','method'))
        selected=row['candidate_artifacts_rehashed_and_reference_qualified']
        entry={'slot':index,'strategy':key[0],'sample_name':key[1],'method':key[2],
               'disposition':'REUSE_QUALIFIED_DEV_OUTPUT' if selected else 'GENERATE_COMPLETE_PATH',
               'original_position_classification':row['classification']}
        if selected:entry['reuse_binding']=row['candidate_binding']
        slots.append(entry)
    fresh={(r['strategy'],r['sample_name'],r['method']):r for r in slots if r['disposition']=='GENERATE_COMPLETE_PATH'}
    assert len(fresh)==54
    blocks=[]
    for i,name in enumerate(names):
        for j,strategy in enumerate(strategies if i%2==0 else list(reversed(strategies))):
            offset=(2*i+strategies.index(strategy))%len(methods)
            rotated=methods[offset:]+methods[:offset]
            missing=[m for m in rotated if (strategy,name,m) in fresh]
            for start in range(0,len(missing),3):
                chosen=missing[start:start+3]
                blocks.append({'id':'E3_BLOCK_'+str(len(blocks)+1).zfill(2),'strategy':strategy,
                    'paths':[{'sample_name':name,'method':m,'slot':fresh[(strategy,name,m)]['slot']} for m in chosen]})
    execution=[(b['strategy'],p['sample_name'],p['method']) for b in blocks for p in b['paths']]
    assert len(blocks)==20 and len(execution)==len(set(execution))==54 and set(execution)==set(fresh)
    result={'identity':'E3_COMPLETE64_REUSE10_FRESH54_BLOCK_SCOPE_PREREGISTRATION_NOT_GPU',
        'card':'WC-E3-CURRENT-BIRTH-COMPLETE64-REUSE10-FRESH54-R1-20261011-A',
        'run_id':'wc-e3-current-birth-complete64-reuse10-fresh54-r1',
        'strategies':strategies,'sample_names':names,'methods':methods,'requests':old['preregistration']['requests'],
        'scientific_positions':64,'reused_DEV_positions':10,'generated_complete_positions':54,
        'fresh_model_processes':20,'maximum_paths_per_model_process':3,'all64_slots':slots,'blocks':blocks,
        'complete_solver_updates_to_generate':1944,'normal_CFG_calls_to_generate':3888,
        'original_failed64_scope_and_fees_preserved':True,'one_complete_GPU_card_not20_independent_cards':True,
        'reuse_is_not_independent_confirmation':True,'forecast_all_loads_CPU_copies_failures_cleanup_pending':True,
        'production_CPU_and_execution_wiring_pending':True,'GPU_execution_selected':False,'GPU_submissions':0,'ledger_written':False,
        'source_sha256':{n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in refs+[
            'scripts/prepare_wc_e3_complete64_slots_cpu_r1.py',
            'research/317_WC_E3_COMPLETE64_REUSE10_FRESH54_BLOCK_CPU_PREREGISTRATION_20261011.md']}}
    target=root/'manifests/wc_e3_complete64_reuse10_fresh54_blocks_r1_20261011.json';assert not target.exists()
    target.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('identity','scientific_positions','reused_DEV_positions','generated_complete_positions','fresh_model_processes','GPU_submissions')}))


if __name__=='__main__':main()
