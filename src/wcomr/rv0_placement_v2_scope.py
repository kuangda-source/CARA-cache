"""Prospective R2 estimand; preserve R1's four pairs and complete denominator."""
from .rv0_placement_scope import LABELS, ENCODED, scope_from_parents
TAIL_CONTRACT = 'FIXED_EXECUTED_69_70_NATIVE_PROPOSALS_RECORDED_HARD_RESET_UNCHANGED'

CARD = 'WC-W3-PLACEMENT-TAIL-ALIGNED-R2-20261007-A'
RUN = 'wc-w3-placement-tail-aligned-r2'


def scope_from_candidates(candidates):
    scope = scope_from_parents(candidates)
    scope.update(card=CARD,run_id=RUN,
        protected_native_action_mismatch='RECORD_69_70_PROPOSAL_DIFFERENCE_KEEP_FROZEN_EXECUTED_MASK_NO_FALLBACK',
        tail_contract=TAIL_CONTRACT)
    return scope


def validate_scope(scope,candidates):
    if scope != scope_from_candidates(candidates):
        raise ValueError('R2 full placement scope or sole tail-contract change differs')
    return {'status':'R2_COMPLETE_FIXED_EXECUTED_TAIL_SCOPE_CPU_PASS_NOT_GPU',
            'parents':2,'suffixes':16,'new_outputs':10,'science_pairs':4}
