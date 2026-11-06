"""Complete four-swap diagnostic scope and cost, with no Torch or launcher.

The original parent mask is offline diagnostic information. A swap changes two
calls in one CFG branch; matching counts does not match runtime or define a
single-action training label. No GPU execution cap is selected here.
"""
import math
from .rv0_fixed_plan import FixedMaskPlan, cfg_full_counts, mask_sha256

SCENES = ['common_sense_6487f37f-ef57-49ca-afdc-d898922b5191', 'human_199']
PAIRS = [[(47,49),(48,50)],[(61,63),(46,48)]]
LABELS = ['OFF1','OFF2','BASE1','SWAP0_first','SWAP1_first','SWAP1_second','SWAP0_second','BASE2']
ENCODED = ['OFF1','BASE1','SWAP0_first','SWAP1_first']


def scope_from_parents(candidates):
    if len(candidates) != 4:
        raise ValueError('Four pre-registered same-CFG swaps required; do not silently drop coverage')
    rows=[]
    for index,scene in enumerate(SCENES):
        chosen=candidates[2*index:2*index+2]
        mask=tuple(chosen[0]['parent_mask']);base=FixedMaskPlan(mask);base.validate()
        for slot,row in enumerate(chosen):
            pair=(row['from_cache_call_n'],row['donor_full_call_m'])
            if (row['sample'] != scene or row['cfg_slot'] != slot or pair != PAIRS[index][slot]
                    or tuple(row['parent_mask']) != mask or row['selection_reads_video_score_or_local_error'] is not False
                    or row['parent_full_CFG_counts'] != list(cfg_full_counts(mask))):
                raise ValueError('Frozen parent/selection/source/CFG pair differs')
            FixedMaskPlan(mask,pair).validate()
        plans=[]
        for label in LABELS:
            pair=() if label.startswith(('OFF','BASE')) else PAIRS[index][int(label[4])]
            action=FixedMaskPlan(mask,pair).action_mask()
            plans.append({'label':label,'mode':'ORIGINAL_ADAPTIVE' if label.startswith('OFF') else 'OFFLINE_FIXED_MASK',
                'swap_calls':list(pair),'planned_full_counts_per_CFG':list(cfg_full_counts(action)),
                'planned_action_mask_sha256':mask_sha256(action) if not label.startswith('OFF') else None,
                'encode':label in ENCODED})
        rows.append({'scene':scene,'parent_action_mask':list(mask),'parent_mask_sha256':mask_sha256(mask),
            'parent_full_counts_per_CFG':list(cfg_full_counts(mask)),
            'swaps':[{'CFG_slot':slot,'calls':list(pair)} for slot,pair in enumerate(PAIRS[index])],
            'controls':plans,'new_outputs_including_parent':5})
    return {'card':'WC-W3-PLACEMENT-SWAP-R1-20261004-A','run_id':'wc-w3-placement-swap-r1',
        'scene_role':'TWO_EXPOSED_CAL_NOT_CONF','seed':0,'sample_indices':[1,2],
        'requested_steps':35,'parent_updates':36,'parent_CFG_calls':72,'snapshot_step':22,
        'suffix_updates':14,'suffix_CFG_calls':28,'maximum_age_solver_steps':33,
        'protected_calls':list(range(1,45))+list(range(69,73)),
        'own_branch_latent_solver_cache_condition_RNG_required':True,
        'protected_native_action_mismatch':'INFEASIBLE_STOP_PRESERVE_DENOMINATOR_NO_FALLBACK',
        'parent_action_mask_reproducibility_required':True,
        'parent_phases':2,'complete_suffix_controls':16,'new_encoded_outputs':10,
        'existing_matched_Native_references':2,'science_swap_pairs':4,
        'Native_relative_video_losses':6,'signed_swap_diagnostics':4,
        'loss':'ALL93_FULL432X768_PRETRAINED_LPIPS_ALEX_CPU_MATCHED_NATIVE',
        'baseline_decoded_to_parent_byte_SHA_bridge_required':True,
        'current_parent_to_historical_WC_context_settings_grid_SHA_required':True,
        'original_adaptive_OFF_full_continuation_and_encoded_bridge_required':True,
        'all_fixed_baseline_and_swap_repeats_full_trajectory_state_required':True,
        'per_CFG_quota_matched_required':True,'equal_seconds_established':False,
        'online_policy':False,'single_step_RV_training_labels':False,
        'failed_infeasible_negative_pairs_preserve_frozen_denominator':True,
        'new_sparse_W1_Head_LoRA_training_human_review':False,'scenes':rows,
        'GPU_execution_selected':False,'GPU_submitted':False,'GPU_reserved_seconds':0,
        'GPU_timeout_seconds':None,'GPU_uuid':None,'production_entry_ready':False}


def validate_scope(scope, candidates):
    if scope != scope_from_parents(candidates):
        raise ValueError('Full placement control/encoding/reference/coverage contract differs')
    if sum(len(row['controls']) for row in scope['scenes']) != 16:
        raise ValueError('All eight suffix controls per scene required')
    return {'status':'PLACEMENT_FULL_SCOPE_CPU_PASS_NOT_GPU_SELECTION','parents':2,'suffixes':16,
        'new_outputs':10,'science_pairs':4,'Native_relative_losses':6,'signed_diagnostics':4}


def cost_proposal(load, parent_each, suffix_proxy, native_full, remaining_seconds):
    values=(load,parent_each,suffix_proxy,native_full,remaining_seconds)
    if any(type(v) not in (int,float) or not math.isfinite(v) or v<=0 for v in values):
        raise ValueError('Finite positive measured/proxy cost inputs required')
    components={'loading':load,'two_diagnostic_parents':2*parent_each,
        'sixteen_unchanged_suffix_proxies':16*suffix_proxy,
        'eight_unique_child_decode_encode_unmeasured_allowance':240,
        'new_bookkeeping_unmeasured_allowance':75}
    nominal=sum(components.values())*1.2+30
    stress=dict(components);stress['sixteen_unchanged_suffix_proxies']=16*(native_full+25)
    stress_total=sum(stress.values())*1.2+30
    return {'components_seconds':components,'nominal_complete_seconds':nominal,
        'stress_proxy_complete_seconds':stress_total,'planning_factor':1.2,'shutdown_allowance_seconds':30,
        'current_remaining_seconds':remaining_seconds,'A_CD_full_cap_seconds':3900,
        'remaining_after_A_CD_full_cap':remaining_seconds-3900,
        'nominal_B_shortfall_after_A_full_cap':max(0,nominal+15-(remaining_seconds-3900)),
        'nominal_A_plus_B_with_two_admissions':2811.502186484635+nominal+30,
        'proxies_are_hard_bounds':False,'real_fixed_mask_swap_cost_measured':False,
        'proposed_B_timeout_seconds':None,'B_GPU_admitted':False,
        'both_batches_guaranteed':False,'conditional_reprice_from_actual_A_required':True,
        'current_B_parent_reference_bridge_required':True,
        'A_payoff_must_be_positive_for_B':False}
