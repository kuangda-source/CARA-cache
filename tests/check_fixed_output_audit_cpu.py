"""Pure rejection controls on an actual fixed-card receipt; artifact IO separate."""
from copy import deepcopy
import importlib.util
from pathlib import Path


def run(receipt):
    spec = importlib.util.spec_from_file_location('fixed_auditor',
        Path(__file__).parents[1]/'scripts/audit_wc_fixed_output_receipts.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    checks = []
    m.binding(receipt)
    checks.append('actual_current_scope_mask_condition_contract_only')
    for case in ('denominator', 'wrong_condition', 'online_role', 'teacher_source',
                 'warm_skip', 'non_boolean', 'fixed_count'):
        changed = deepcopy(receipt)
        if case == 'denominator':
            changed['planned_output_files'] = 3
        elif case == 'wrong_condition':
            changed['fixed_mask']['condition_id'] = '0'*64
        elif case == 'online_role':
            changed['fixed_mask']['role'] = 'ONLINE_POLICY'
        elif case == 'teacher_source':
            changed['fixed_mask']['source_receipt_sha256'] = '0'*64
        elif case == 'warm_skip':
            changed['fixed_mask']['dense_calls'][0] = False
        elif case == 'non_boolean':
            changed['fixed_mask']['dense_calls'][0] = 1
        else:
            i = changed['fixed_mask']['dense_calls'].index(False)
            changed['fixed_mask']['dense_calls'][i] = True
        try:
            m.binding(changed)
        except AssertionError:
            checks.append('reject_'+case)
        else:
            raise AssertionError('Corrupted fixed receipt accepted: '+case)
    if receipt['status'] != 'FOUR_FIXED_DIAGNOSTIC_OUTPUTS_COMPLETE_REQUIRES_INDEPENDENT_AUDIT':
        r = m.audit(receipt, Path('/CPU_CONTRACT_ONLY_NO_ARTIFACT_IO'))
        assert r['status'] == 'INCOMPLETE_FIXED_FOUR_CARD_NOT_ACCEPTED' and r['planned_outputs'] == 4
        checks.append('incomplete_receipt_never_claims_four_output_acceptance')
    if receipt['dense_control']['status'] == 'FRESH_PREPARE_LIGHT_DD_NINE_AND_FINAL_PIPELINE_PASS':
        phase = receipt['dense_control']['phases'][1]
        context, mask = m.binding(receipt)
        m.fixed_provenance(phase, context, mask, sparse_allowed=False)
        checks.append('actual_fixed_D_history_mask_event_reconstruction')
        for case in ('online_policy', 'causal_labels', 'selected_skip', 'trace', 'missing_true_history'):
            changed = deepcopy(phase)
            report = changed['refresh_provenance']
            if case in ('online_policy','causal_labels'):
                report['online_policy' if case == 'online_policy' else 'causal_refresh_value_labels'] = True
            elif case == 'selected_skip':
                report['events'][0]['selected_fixed_skip'] = True
            elif case == 'trace':
                changed['trace'][0]['deep_executed'] = False
            else:
                report['events'][22]['true_dense_before'] = []
            try:
                m.fixed_provenance(changed, context, mask, sparse_allowed=False)
            except AssertionError:
                checks.append('reject_'+case)
            else:
                raise AssertionError('Corrupted fixed provenance accepted: '+case)
    return {'status':'FIXED_RECEIPT_CONTRACT_REJECTION_CONTROLS_PASS_NO_ARTIFACT_PROOF',
        'CPU_only':True, 'checks':checks, 'quality_acceptance':False,
        'limits':'Reads actual receipt contracts; no encoded artifact IO, GPU execution or quality evidence.'}
