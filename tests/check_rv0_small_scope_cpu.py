"""Independent scope/cost/remaining-budget rejection contracts, no Torch."""
import copy
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from wcomr.rv0_small_scope import proposal, validate_scope, budget_gate


def run():
    scope = proposal(); validate_scope(scope)
    invalid = []
    for key, value in [('parent_phases', 8), ('complete_suffix_controls', 4), ('new_encoded_outputs', 6),
                       ('target_calls', [45, 45]), ('selected_CFG_slots', [0, 0]), ('snapshot_step', 21),
                       ('budget_matched', True), ('full_RV0_acceptance', True), ('RV_labels', 2),
                       ('current_WC_historical_encoded_bridge_required', False), ('timeout_seconds', 1080),
                       ('GPU_execution_selected', True), ('new_sparse_W1_Head_LoRA_training_human_review', True)]:
        bad = copy.deepcopy(scope); bad[key] = value; invalid.append(bad)
    bad = copy.deepcopy(scope); bad['extra'] = 'scope drift'; invalid.append(bad)
    for bad in invalid:
        try:
            validate_scope(bad)
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid new small diagnostic scope accepted')
    budget = {'cap_gpu_hours': 13, 'used_gpu_hours': 11.022315686839217,
              'budget_authorization_ref': scope['budget_authorization_ref']}
    admitted = budget_gate(budget, scope)
    bad_budgets = [dict(budget, used_gpu_hours=12), dict(budget, cap_gpu_hours=12),
                   dict(budget, used_gpu_hours=float('nan')), dict(budget, used_gpu_hours=True),
                   dict(budget, wc_other_inflight={}), dict(budget, budget_authorization_ref='other')]
    for bad in bad_budgets:
        try:
            budget_gate(bad, scope)
        except ValueError:
            pass
        else:
            raise AssertionError('Bad budget/cumulative authorization accepted')
    return {'status': 'SMALL_CD_SCOPE_CPU_PASS_NOT_SELECTION', 'invalid_scopes_refused': len(invalid),
            'invalid_budget_cases_refused': len(bad_budgets), 'budget_gate': admitted, 'GPU_submissions': 0}


if __name__ == '__main__':
    print(json.dumps(run()))
