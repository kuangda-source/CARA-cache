"""Bind captured E1 actual input metadata to the accepted Native references.

Read-only metadata stage. No artifact rehash, metric, reuse selection or GPU.
"""
import gzip
import hashlib
import json
from pathlib import Path
import sys


def main():
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root/'src'))
    from wcomr.full64_partial_recovery_cpu import verifier, numerical_pairing
    refs = []
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    def load_capture(path, key):
        capture = json.loads((root/path).read_text()); item=capture['files'][key]
        name=item.get('local_path', item.get('local_ref')); data=(root/name).read_bytes()
        raw=gzip.decompress(data)
        compressed_sha=item.get('compressed_sha256',item.get('gzip_sha256'))
        assert compressed_sha is not None and sha(root/name)==compressed_sha and len(raw)==item['bytes']
        assert hashlib.sha256(raw).hexdigest()==item['sha256']
        refs.extend([path, name]);return capture,json.loads(raw)
    e1_ref='reports/wc_e1_diag8_gpu_r2_terminal_20261011_capture.json'
    e1,config=load_capture(e1_ref,'selected-config')
    independent=e1['independent_actual_tensor_and_policy_audit']
    assert e1['original_source_terminal_scope_and_cost_independently_verified'] and e1['complete_numeric_paths']==8
    assert (independent['actual_tensors_reloaded'],independent['actual_complete_policy_decisions_replayed'])==(296,288)
    assert len(independent['direct_full36_and_final_comparisons'])==6
    assert all(v['all_equal'] and len(v['equal'])==37 for v in independent['direct_full36_and_final_comparisons'])
    old_capture,old=load_capture('reports/wc_full64_partial_recovery_cpu_r1_terminal_20261011_capture.json','result.json')
    assert old['validated_paths']==14 and old['numerical_paired_scores']==8 and old['invalid_paths']==0
    _,runner=load_capture('reports/wc_current_birth_full64_r1_terminal_20261010_capture_and_independent_audit.json','runner')
    old_config=runner['config']
    reg_ref='manifests/wc_full64_partial_recovery_cpu_r1_20261011.json'
    reg=json.loads((root/reg_ref).read_text());refs.append(reg_ref)
    assert config['parent_config_sha256']==reg['original_config_sha256']
    old_sources={n:h for n,h in old_config['payload_sha256'].items() if n.startswith('src/wcomr/')}
    assert len(old_sources)==225 and all(sha(root/n)==h==config['parent_import_source_sha256'][n] for n,h in old_sources.items())
    check,proof=verifier(root,old_config['payload_sha256'])
    native={v['sample_name']:v for v in runner['matched_Native_metadata']}
    source_proof=old['numerical_zero_mask_source_proof']
    assert source_proof['zero_mask_gt_has_no_model_effect']
    rows=[]
    for arm in e1['arms']:
        _,receipt=load_capture(e1_ref,arm['id']+'-receipt')
        assert arm['exit_code']==0 and receipt['source_revision']==e1['source_revision']
        for request in receipt['batch']['requests']:
            for i,row in enumerate(request['paths']):
                strategy=config['working_epoch_strategy'];check(row,strategy)
                slot=dict(row=row,request_record=request,method_index=i)
                pair=numerical_pairing(slot,native[request['sample_name']],source_proof)
                rows.append(dict(arm=arm['id'],strategy=strategy,sample_name=request['sample_name'],
                    method=row['collect'],actual_complete_row_semantics_pass=True,pairing=pair,
                    vector_artifact=row['vector_artifact'],video_artifact=row['video_artifact'],
                    reuse_selected=False,artifact_rehash_and_complete_E3_manifest_pending=True))
    assert len(rows)==8
    candidates=[r for r in rows if r['arm']=='CPU_PREFIX' and r['sample_name']=='human_199' and r['pairing']['compatible']]
    result=dict(status='E3_E1_ACTUAL_NATIVE_METADATA_COMPATIBILITY_READONLY_NOT_REUSE_SELECTION',
        complete_E1_rows=8,compatible_rows=sum(r['pairing']['compatible'] for r in rows),
        original_source_files_unchanged=225,original_row_semantic_verifier_derivation=proof,
        existing_E0_zero_mask_source_proof_reused=True,rows=rows,
        additional_distinct_Human_candidates=len(candidates),candidate_keys=[{k:r[k] for k in ('strategy','sample_name','method')} for r in candidates],
        old_Human_missing_prepare_not_synthesized=True,old_full64_failure_unchanged=True,
        no_video_or_tensor_rehash_in_this_stage=True,no_new_metric_or_independent_confirmation=True,
        E3_GPU_execution_selected=False,GPU_submissions=0,ledger_written=False,Torch_imported='torch' in sys.modules,
        source_sha256={n:sha(root/n) for n in sorted(set(refs+['scripts/audit_wc_e3_e1_reference_compatibility_cpu_r1.py']))})
    assert not result['Torch_imported']
    target=root/'reports/wc_e3_e1_actual_native_metadata_cpu_r1_20261011.json';assert not target.exists()
    target.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('status','complete_E1_rows','compatible_rows','additional_distinct_Human_candidates','GPU_submissions')}))


if __name__=='__main__':main()
