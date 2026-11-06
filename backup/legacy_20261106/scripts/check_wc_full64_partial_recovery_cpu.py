#!/usr/bin/env python3
"""Metadata controls on captured real failed64 receipt, without Torch/CUDA."""
import copy
import gzip
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from wcomr.full64_partial_recovery_cpu import verifier, slots, numerical_pairing


def main():
    r = json.loads(gzip.decompress((ROOT/'reports/wc_current_birth_full64_r1_terminal_20261010_runner_native.gz').read_bytes()))
    verify, proof = verifier(ROOT, r['config']['payload_sha256'])
    rows = slots(r); complete = [s for s in rows if s['written_complete']]
    refs = {v['sample_name']: v for v in r['matched_Native_metadata']}
    for s in complete:
        verify(s['row'], s['strategy'])
    source = {'zero_mask_gt_has_no_model_effect': True}
    verdicts = [numerical_pairing(s, refs[s['sample_name']], source) for s in complete]
    assert len(rows) == 64 and len(complete) == 14
    assert sum(v['compatible'] for v in verdicts) == 8
    assert all(not v['compatible'] and not v['prepared_evidence_available'] for v in verdicts[8:])
    assert all(not v['strict_original_verdict']['compatible'] for v in verdicts)
    base = next(s for s in complete if s['method'] == 'CPD')
    bad_cases = []
    def reject(name, change):
        bad = copy.deepcopy(base['row']); change(bad)
        try:
            verify(bad, base['strategy'])
        except (ValueError, KeyError):
            bad_cases.append(name)
        else:
            raise AssertionError('Invalid original path accepted: '+name)
    reject('missing_guided_update', lambda row: row['guided_sha256'].pop())
    reject('failed_path_as_complete', lambda row: row.update(status='CALIBRATION_PARENT_FAILED_COMPLETE_SCOPE_RETAINED'))
    reject('missing_checkpoint', lambda row: row['P0_roundtrips'].pop())
    reject('teacher_updates', lambda row: row['collection_complete']['deployment'].update(teacher_calls=1))
    reject('fake_zero_P_floor', lambda row: next(h for h in row['collection_complete']['deployment']['history'] if h['action']=='PP')['source_policy'].update(creation_floor_proxy_after=0))
    reject('different_source_rule', lambda row: row['collection_complete']['deployment'].update(working_epoch_strategy='OTHER'))
    pairing_rejections = []
    for name, edit in [
        ('nonzero_mask', lambda s: s['row']['actual_condition_masks'][0].update(nonzero_elements=1)),
        ('changed_active_condition', lambda s: s['row']['condition_fields_before'][0].update(crossattn_emb='0'*64)),
        ('missing_prepare', lambda s: s['request_record'].pop('prepared_input_calls')),
        ('changed_numerical_solver', lambda s: s['row']['actual_raw_solver_configuration'].update(class_identity='OTHER_SOLVER'))]:
        bad = copy.deepcopy(base); edit(bad)
        assert not numerical_pairing(bad, refs[bad['sample_name']], source)['compatible']
        pairing_rejections.append(name)
    out = {'status':'PARTIAL_RECOVERY_REAL_METADATA_AND_PAIRING_CPU_CONTROLS_PASS_NOT_FILE_OR_METRIC_ACCEPTANCE',
        'original_planned_slots':64, 'original_saved_complete_rows':14,
        'all14_original_row_semantics_pass':True, 'strict_original_native_pairs':0,
        'numerical_pairing_fixture_eligible':8, 'Human_missing_prepare_retained':6,
        'invalid_path_refusals':bad_cases, 'invalid_pairing_refusals':pairing_rejections,
        'original_verifier_derivation':proof, 'Torch_imported': 'torch' in sys.modules,
        'source_proof_fixture_not_real_runtime_verification':True, 'GPU_submissions':0}
    assert not out['Torch_imported']
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    main()
