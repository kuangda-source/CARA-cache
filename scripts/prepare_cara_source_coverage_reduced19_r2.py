#!/usr/bin/env python3
"""Quote a conditional 19D C1 proposal; no transport, launch or ledger writes."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from wcomr.cara_fast_spec_r1 import digest, policy_from_mask, profile_from


def a1_variant(profile, policy):
    """Portable predeclared age-one rule in the original F19 early A window."""
    dense = [i for i,a in enumerate(policy['actions'],1) if a=='D']
    corrections = [t for t in range(9,20) if policy['actions'][t-1]=='C' and t-1 in dense]
    return policy_from_mask(profile,dense,corrections)


def build(card, history, audit, last_settlement):
    profile = profile_from(card['profile'])
    main = copy.deepcopy(card['views']['main8-K19'])
    if audit['original_query_count']!=42 or audit['GPU_submissions']!=0:
        raise ValueError('Complete original42 zero-GPU audit required')
    rates = history['measured_max_rates_seconds']
    positions = dict(same_batch_references=12, main8_complete_FIT=16,
        selected_main_CHECK=2, search_complete_FIT_upper=24, selected_search_CHECK=2,
        selected_main_plus_A1=4, warm_and_identity_controls=10)
    costs = dict(same_batch_references=4*(rates['Native']+rates['K19']+rates['F19_A1']),
        warm_and_controls=history['components_seconds']['warm_and_controls'],
        main8_complete_FIT=16*rates['K19'], selected_main_CHECK=2*rates['K19'],
        fair_search_FIT_upper=24*rates['K19'], selected_search_CHECK=2*rates['K19'],
        selected_main_plus_A1=4*rates['F19_A1'], internal_CPU_held_allocation=20*rates['score'],
        model_load_broker_admission=900., stop_release_reserve=600.)
    costs['variation_margin']=.15*math.fsum(costs.values())
    available=last_settlement['result']['snapshot']['ledger']['available_gpu_hours']
    result=dict(schema='CARA_C1_REDUCED19_CONDITIONAL_PROPOSAL_R2',
        status='DESIGN_ONLY_ORIGINAL_C1_DEFERRED_NO_DOUBLE_SOURCE_INCREMENT_GATE_PASS',
        scope_parent_sha256=card['scope_sha256'], D_budgets=[19],
        scientific_question='PHASE_WEIGHTED_SOURCE_COVERAGE_CANDIDATE_EFFICIENCY_WITH_ENDPOINT_SELECTION',
        double_source_advantage_claimed=False, old_P1_engineering_screen_rewritten=False,
        main8=main, phase3=copy.deepcopy(card['views']['phase3-K19']),
        neutral3=copy.deepcopy(card['views']['neutral3-K19']),
        phase_neutral_analysis='FIT_SUBSETS_ONLY_NO_EXTRA_CHECK_NO_MECHANISM_SIGNIFICANCE_CLAIM',
        single8_new_video_paths=0, K22_new_video_paths=0, source_labels_collected=0,
        FIT=card['FIT'], CHECK=card['CHECK'], CHECK_exposed=True,
        same_batch_reference_roles=['NATIVE35','UNIFORM19_C','F19_A1'],
        positions=positions, semantic_positions=sum(positions.values()), physical_paths_upper=sum(positions.values()),
        physical_model_pairs_upper=36*sum(positions.values()), internal_FIT_cohorts_upper=20,
        internal_metric_pairs_upper=40, non_Native_quality_positions=20,
        sealed_FIT_positions_reused_upper=6, postrelease_new_metric_pairs_upper=14,
        identity_relations=10, old_metric_pairs_recomputed=0,
        winner_A1_rule=dict(eligible_updates=list(range(9,20)), source_age_updates=1, alpha=1.,
            original_F19_reproduced_exactly=a1_variant(profile,card['roles']['F19_C']['policy'])==card['roles']['F19_A1']['policy'],
            per_candidate={c['candidate_id']:a1_variant(profile,c['policy']) for c in main['candidates']},
            selected_by='ORIGINAL_PURE_C_COMPLETE_FIT_WINNER_ONLY', CHECK_reselection=False,
            primary_gate_rescue=False),
        search=dict(max_queries=12, cache='ISOLATED', initial_Uniform_paid_independently=True,
            cost_cap='MAIN8_ACTUAL_CALIBRATION_WITH_THE_SAME_FULL_SINGLE_BUDGET_COMMON_COST',
            report_actual_and_cap_separately=True),
        continuation_conditions=dict(preregister_before_any_new_C1_video=True,
            main_C_to_F19_A1_input_equal_four_old_CAL_LPIPS_max=1.15,
            main_C_to_F19_A1_input_equal_four_old_CAL_T_DD_max=1.05,
            main_C_LPIPS_strictly_better_than_LPIPS_search=True,
            search_actual_to_main_actual_calibration_cost_min=.9,
            search_actual_to_main_actual_calibration_cost_max=1.,
            cost_unmatched_means_no_automatic_DEV=True,
            both_FIT_and_exposed_CHECK_reported=True, statistical_significance_claimed=False,
            original_double_source_rank_advantage_gate_passed=False),
        cost_accounting=dict(standalone19='ALL_COMMON_REFERENCE_AND_CONTROL_COST_ONCE_PLUS_DIRECT19',
            joint19_22='NOT_EXECUTED_IF_LATER_RUN_SHOW_COMMON_ONCE_AND_EXPLICIT_HALF_SPLIT',
            new_label_cost_GPUh=0., old_P1_label_cost_charged_again=False,
            algorithm_accounts_are_not_additional_guardian_bills=True),
        components_seconds=costs, forecast_GPUh=math.fsum(costs.values())/3600,
        proposed_hard_GPUh=7., quote_basis='ORIGINAL_ACCEPTED_A6000_MAX_OPERATION_COSTS_NOT_A_LIVE_QUOTE',
        resources_draft=copy.deepcopy(dict(output_GiB=80, journal_MiB=48, GPU_memory_GiB=40,
            internal_CPU_memory_GiB=8, swap=False, initial_host_GiB=50,
            internal_CPU_fresh_host_GiB=12, temperature_stop_C=90, stop_release_seconds=600)),
        budget_priority=dict(Shared25_final_planning_hold_GPUh=10., F19_1_9x_planning_upper_GPUh=3.,
            C1_conditional_upper_GPUh=7., total_planning_upper_GPUh=20.,
            historical_available_GPUh=available, historical_shortfall_GPUh=max(0.,20.-available),
            historical_snapshot_not_live=True, real_reservations_created=0, old16_5_liability_unchanged=True),
        executable=False, reduced70_production_CPU_accepted=False,
        original166_CPU_acceptance_does_not_accept_reduced70=True,
        GPU_authorized=False, central_ledger_permission=False, GPU_submissions=0, ledger_written=False,
        protected_inputs_accessed=False)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    refs=dict(card='plans/cara_next_stage_20261103/source_coverage/c1/C1_MANIFEST_R1.json',
        history='plans/cara_next_stage_20261103/source_coverage/c1/C1_WHOLE_QUOTE_R1.json',
        audit='reports/cara_source_coverage_C1_zero_GPU_audit_r1_20261103.json',
        last_settlement='reports/cara_v1_P1_successor_final_settlement_r1_20261103.json')
    raw={k:(ROOT/p).read_bytes() for k,p in refs.items()}
    result=build(**{k:json.loads(v) for k,v in raw.items()})
    result['input_sha256']={refs[k]:hashlib.sha256(v).hexdigest() for k,v in raw.items()}
    result['source_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result['proposal_sha256']=digest(result)
    with Path(args.output).open('x') as out:
        out.write(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('status','semantic_positions','forecast_GPUh','proposed_hard_GPUh')},indent=2))


if __name__=='__main__':
    main()
