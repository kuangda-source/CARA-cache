"""Reject corrupted real receipt contracts; artifact IO verified separately."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path


def run(receipt):
    spec = importlib.util.spec_from_file_location('light_auditor', Path(__file__).parents[1] /
                                             'scripts/audit_wc_light_output_receipts.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    d = receipt['dense_control']
    checks = []
    original_phase = m.phase_audit
    # This stand-in isolates receipt validation, and provides no artifact proof.
    m.phase_audit = lambda p, path, **kw: {'sha256':p['artifacts'][0]['sha256']}
    positive = m.dense_control(receipt, Path('/CPU_CONTRACT_ONLY_NOT_REAL_FILES'))
    assert positive['state_components_per_checkpoint'] == [1216] * 5
    checks.append('actual_complete_DD_receipt_contract_only_no_artifact_IO')
    for kind in ('output_hash', 'mode_true_both_arms', 'missing_checkpoint_both_arms'):
        changed = deepcopy(receipt)
        rows = changed['dense_control']['observers']
        if kind == 'output_hash':
            rows[1]['output_hashes'][0] = '0' * 64
        elif kind == 'mode_true_both_arms':
            for row in rows:
                fields = row['field_signatures'][0]['components']
                fields['mode.'] = hashlib.sha256(repr(True).encode()).hexdigest()
                row['state_fingerprints'][0] = m.state_digest(fields)
        else:
            for row in rows:
                row['field_signatures'].pop()
                row['state_fingerprints'].pop()
        try:
            m.dense_control(changed, Path('/CPU_CONTRACT_ONLY_NOT_REAL_FILES'))
        except AssertionError:
            checks.append('reject_' + kind)
        else:
            raise AssertionError('Corrupted receipt accepted: ' + kind)
    m.phase_audit = original_phase
    for kind in ('CFG71', 'missing_fresh_prepare'):
        phase = deepcopy(d['phases'][0])
        phase['CFG_calls' if kind == 'CFG71' else 'prepare_calls'] = 71 if kind == 'CFG71' else 0
        try:
            m.phase_audit(phase, None, context=d['context'], sparse_allowed=False)
        except AssertionError:
            checks.append('reject_' + kind + '_before_file_IO')
        else:
            raise AssertionError('Corrupted phase accepted: ' + kind)
    candidate = d['phases'][1]
    m.provenance_audit(candidate, d['context'], sparse_allowed=False)
    checks.append('actual_dense_reference_event_and_recent_history_reconstruction')
    for kind in ('reference_kind', 'missing_reset', 'stale_true_dense_history'):
        phase = deepcopy(candidate)
        events = phase['refresh_provenance']['events']
        if kind == 'reference_kind':
            events[22]['references_read'][0]['kind'] = 'sparse'
        elif kind == 'missing_reset':
            events[69]['native_cycle_reset'] = False
        else:
            events[22]['true_dense_before'] = events[10]['true_dense_before']
        try:
            m.provenance_audit(phase, d['context'], sparse_allowed=False)
        except AssertionError:
            checks.append('reject_' + kind)
        else:
            raise AssertionError('Corrupted provenance accepted: ' + kind)
    incomplete = m.audit(receipt, Path('/CPU_CONTRACT_ONLY_NOT_REAL_FILES'))
    assert incomplete['status'] == 'INCOMPLETE_TEN_CARD_NOT_ACCEPTED'
    assert incomplete['planned_outputs'] == 10 and not incomplete['quality_acceptance']
    checks.append('running_original_retains_ten_output_denominator_and_no_acceptance')
    return {'status':'LIGHT_AUDIT_REAL_RECEIPT_CPU_CONTRACT_CONTROLS_PASS_NOT_ARTIFACT_OR_GPU',
        'checks':checks, 'CPU_only':True,
        'limits':'Only real receipt contract mutations and metadata reconstruction. Two actual files/decode must pass independently.'}


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--receipt', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    r = run(json.loads(args.receipt.read_text()))
    r.update(receipt_sha256=hashlib.sha256(args.receipt.read_bytes()).hexdigest(),
             test_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             audit_code_sha256=hashlib.sha256((Path(__file__).parents[1] /
                'scripts/audit_wc_light_output_receipts.py').read_bytes()).hexdigest())
    args.output.write_text(json.dumps(r, indent=2) + '\n')
    print(json.dumps({'status':r['status'], 'checks':len(r['checks'])}))
