#!/usr/bin/env python3
"""Prospective merged single-source 19D/16D/17D scope and complete GPU quote."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from prepare_cara_source_coverage_reduced19_r2 import a1_variant
from wcomr.cara_fast_spec_r1 import digest,profile_from


QUALITY_CONTRACT='plans/cara_policy_generator_20261020/CAL66_DESIGN_AND_DECISION_CONTRACT_R1_20261025.md'


def selected_candidates(bundle,profile):
    selected=[]
    for budget in (19,16,17):
        pool=bundle['pools'][str(budget)]
        if digest({k:v for k,v in pool.items() if k!='pool_sha256'})!=pool['pool_sha256']:
            raise ValueError('New development candidate pool identity differs')
        if budget==19:
            candidates=pool['candidates']
        else:
            candidates=[c for c in pool['candidates'] if any(o['tilt'] in (2.,4.) and o['rank']==1 for o in c['origins'])]
        for c in candidates:
            corrected=a1_variant(profile,c['policy'])
            selected.append(dict(D=budget,candidate_id=c['candidate_id'],dense_steps=c['dense_steps'],
                origins=c['origins'],C_policy_sha256=c['policy']['fingerprint'],
                A1_policy_sha256=corrected['fingerprint'],
                A1_updates=[i for i,a in enumerate(corrected['actions'],1) if a=='A'],
                C_actions=''.join(c['policy']['actions']),A1_actions=''.join(corrected['actions'])))
    if ([sum(r['D']==k for r in selected) for k in (19,16,17)]!=[7,2,2]
            or len({r['candidate_id'] for r in selected})!=11):
        raise ValueError('Seven main19 and lambda2/4 first-choice layouts at16D and17D required')
    return selected


def build(card,bundle,history,robustness,settlement):
    if (digest({k:v for k,v in bundle.items() if k!='bundle_sha256'})!=bundle['bundle_sha256']
            or robustness['new_pools_bundle_sha256']!=bundle['bundle_sha256']):
        raise ValueError('Bound source pool and complete development audit required')
    refs=[r for r in robustness['reference_ranks'] if r['tilt'] in (2.,4.)]
    if len(refs)!=4 or any(r['rank_same_D']!=(1. if r['role']=='F19_C' else 2.) for r in refs):
        raise ValueError('Registered strong-reference development screen did not pass')
    candidates=selected_candidates(bundle,profile_from(card['profile']))
    rates=history['measured_max_rates_seconds'];path=max(rates['K19'],rates['F19_A1'])
    positions=dict(same_batch_references=12,main19_C_and_A1_FIT=28,fast16_17_C_and_A1_FIT=16,
        selected_main_and_fast_C_and_A1_CHECK=8,LPIPS_search19_FIT_upper=24,
        LPIPS_search19_CHECK=2,selected_fast_lightC_A1=4,warm_and_controls=12)
    # Pay the full measured19D rate even for16/17D and light-C; no presumed speed savings.
    costs=dict(same_batch_references=4*(rates['Native']+rates['K19']+rates['F19_A1']),
        warm_and_controls=history['components_seconds']['warm_and_controls']+2*path,
        main19_C_and_A1_FIT=28*path,fast16_17_C_and_A1_FIT=16*path,
        selected_main_and_fast_C_and_A1_CHECK=8*path,
        LPIPS_search19_FIT_upper=24*path,LPIPS_search19_CHECK=2*path,
        selected_fast_lightC_A1=4*path,internal_CPU_held_allocation=23*rates['score'],
        model_load_broker_admission=900.,stop_release_reserve=600.)
    costs['variation_margin']=.15*math.fsum(costs.values())
    forecast=math.fsum(costs.values())/3600
    available=settlement['result']['snapshot']['ledger']['available_gpu_hours']
    same_scope_split_extra=(costs['same_batch_references']+history['components_seconds']['warm_and_controls']+1500)*1.15/3600
    return dict(schema='CARA_PHASE_SINGLE_SOURCE_MERGED_DEVELOPMENT_PROPOSAL_R3',
        status='PREPARATION_ONLY_NEW_DEV_BASED_DESIGN_NO_GPU_AUTHORITY',
        method='SINGLE_SOURCE_PHASE_WEIGHTED_COVERAGE_WITH_COMPLETE_ENDPOINT_SELECTION',
        new_design_after_original42_DEV_audit=True,old_C1_pools_and_P1_results_unchanged=True,
        candidates=candidates,main19_unique_candidates=7,fast16_unique_candidates=2,fast17_unique_candidates=2,
        source_pool_bundle_sha256=bundle['bundle_sha256'],all_evaluated_candidates_have_C_and_A1_FIT=True,
        CPU_only_full_pools=[16,17,19,22],GPU_evaluated_budgets=[19,16,17],GPU_K22_paths=0,
        readout_selection=dict(main19='COMPLETE_TWO_FIT_C_LPIPS_MIN_THEN_FINGERPRINT',
            fast='COMPLETE_TWO_FIT_A1_LOWEST_LPIPS_AMONG_SPEED_GE_1_9_ELSE_LOWEST_LPIPS_ALL',
            fast_timing_ratio='INPUT_EQUAL_NATIVE_T_DD_MEAN_DIVIDED_BY_CANDIDATE_T_DD_MEAN',
            fast_no_speed_eligible='RECORD_STANDARD_SPEED_NOT_MET_NO_1_9_CLAIM',
            C_A1_CHECK_same_selected_layout=True,light_C_A1_parent='SAME_SELECTED_FAST_LAYOUT',
            light_C_A1_reselection=False,CHECK_reselection=False),
        light_C=dict(paths=4,readout='LATEST_TRUE_D_RESIDUAL_HOLD_FOR_C_ONLY',
            A_rule_unchanged=True,both_CFG_true_D_preserved=True,conditional_only_D=False,
            presumed_GPU_saving_in_quote=0,production_source_and_CPU_binding_accepted=False),
        same_batch_references=['NATIVE35','UNIFORM19_C','F19_A1'],FIT=card['FIT'],CHECK=card['CHECK'],CHECK_exposed=True,
        positions=positions,semantic_positions=sum(positions.values()),physical_paths_upper=sum(positions.values()),
        physical_model_pairs_upper=36*sum(positions.values()),
        controls=dict(warm=2,allD_vs_Native=4,Native_instrument_OFF=2,
            speed_backend_OFF_vs_original_fast_A1=2,light_C_instrument_OFF_vs_ON=2,
            independent_search_Uniform_RGB_bridges=2,total_identity_relations=12),
        internal_FIT_cohorts=dict(main19_C=7,fast16_17_A1=4,search19_upper=12,total_upper=23),
        internal_metric_pairs_upper=46,
        reporting=dict(all_candidate_FIT_C_A1_positions=44,formal_nonNative_positions=32,
            overlap_selected_candidate_FIT_positions=8,distinct_report_positions=68,
            sealed_logical_positions_reused_upper=26,postrelease_new_pairs_upper=42,
            all_search_queries_and_failure_denominators_reported=True),
        calibration_accounts=dict(main19_primary='C_ONLY_CANDIDATE_GENERATION_AND_INTERNAL_SCORES_PLUS_COMMON_COST',
            all_A1_characterization='GENERATION_AND_POSTRELEASE_METRICS_SEPARATELY_REPORTED_NOT_C_SEARCH_CREDIT',
            fast_primary='A1_FIT_SELECTION_COST_WITH_C_CHARACTERIZATION_REPORTED_SEPARATELY',
            main19_C_A1_full_characterization_cost_reported=True,
            shared_common_events=['MODEL_LOAD_SHARED_SETUP','WARM_NATIVE','WARM_UNIFORM19',
                'TWO_FIT_NATIVE','TWO_FIT_ALLD_BRIDGES','TWO_FIT_NATIVE_OFF'],
            not_primary_C_calibration=['A1_CHARACTERIZATION','LIGHT_C_CONTROLS','F19_UNIFORM_BENCHMARKS',
                'ALL_CHECK_PATHS','POSTRELEASE_QUALITY','RELEASE'],
            whole_guardian_billed_once=True,local_labels_collected=0,old_P1_labels_charged_again=False),
        search=dict(D=19,max_queries=12,cache='INDEPENDENT',initial_Uniform_independently_paid=True,
            cap='MAIN19_C_ACTUAL_CALIBRATION_COST_WITH_SAME_COMMON_SHARE',
            same_common_allocation='HALF_MAIN_HALF_FAST_BOTH_REPORT_STANDALONE_FULL_COMMON_COST',
            unspent_cap_not_charged_as_actual=True),
        continuation=dict(main19_C_LPIPS_to_F19_A1_max=1.15,main19_C_T_DD_to_F19_A1_max=1.05,
            main19_C_strictly_better_LPIPS_than_search=True,search_to_main_actual_cost_interval=[.9,1.],
            fast_Native_T_DD_to_candidate_min=1.9,fast_LPIPS_to_Native_max=.30,
            summary_unit='FOUR_OLD_CAL_INPUT_EQUAL_WITH_SEPARATE_FIT_AND_EXPOSED_CHECK',
            old_P1_1_10_decision_unchanged=True,new_video_evaluated=False,new_DEV_automatic=False),
        quality_gates=dict(source_contract=QUALITY_CONTRACT,
            max_mean_degradation=dict(MUSIQ_original_points=1.,subject_consistency=.01,motion_smoothness=.01),
            references=['SAME_BATCH_NATIVE35','SAME_BATCH_F19_A1'],
            tested_final_fast_variants=['FAST_C','FAST_A1','FAST_LIGHT_C_A1'],
            Shared25_selection_gates_not_rewritten=True,missing_is_not_pass=True,
            independent_quality_videos=20,independent_quality_scalar_values=60,
            quality_metric_production_CPU_binding_accepted=False),
        components_seconds=costs,forecast_GPUh=forecast,proposed_hard_GPUh=9.25,
        same_scope_two_separate_cards_extra_GPUh=same_scope_split_extra,
        quote_reuses_original_measured_history=True,no_new_live_admission=True,
        resources=dict(output_GiB=80,journal_MiB=48,GPU_GiB=40,internal_CPU_GiB=8,
            initial_host_GiB=50,per_internal_CPU_fresh_host_GiB=12,swap=False,
            temperature_stop_C=90,stop_release_seconds=600,only_two_card_original_A6000=True,
            postrelease_metric_CPU_timeout_seconds=7200,independent_quality_CPU_timeout_seconds_draft=21600,
            all_postrelease_GPU_hidden=True),
        budget=dict(last_available_snapshot_GPUh=available,Shared25_planning_hold_GPUh=10.,
            merged_plus_Shared25_planning_upper_GPUh=19.25,remaining_snapshot_headroom_GPUh=available-19.25,
            snapshot_is_not_live=True,Shared25_complete_quote_still_required=True,
            no_cap_increase_implicitly_authorized=True,old16_5_liability_preserved=True,ledger_reserved_GPUh=0),
        executable=False,whole_production_CPU_accepted=False,
        existing_pure_C_19_22_broker_not_valid_for_fast_A1_queries=True,
        independent_paper_evidence=False,protected_inputs_accessed=False,GPU_authorized=False,
        GPU_submissions=0,ledger_written=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True);args=parser.parse_args()
    refs=dict(card='plans/cara_next_stage_20261103/source_coverage/c1/C1_MANIFEST_R1.json',
        bundle='plans/cara_next_stage_20261103/source_coverage/c1/PHASE_SINGLE7_CANDIDATE_POOLS_R3.json',
        history='plans/cara_next_stage_20261103/source_coverage/c1/C1_WHOLE_QUOTE_R1.json',
        robustness='reports/cara_phase_coverage_robustness_zero_GPU_r1_20261103.json',
        settlement='reports/cara_v1_P1_successor_final_settlement_r1_20261103.json')
    raw={k:(ROOT/p).read_bytes() for k,p in refs.items()}
    result=build(**{k:json.loads(v) for k,v in raw.items()})
    result['input_sha256']={refs[k]:hashlib.sha256(v).hexdigest() for k,v in raw.items()}
    result['quality_contract_sha256']=hashlib.sha256((ROOT/QUALITY_CONTRACT).read_bytes()).hexdigest()
    result['source_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [Path(__file__),ROOT/'scripts/prepare_cara_source_coverage_reduced19_r2.py']}
    result['proposal_sha256']=digest(result)
    with Path(args.output).open('x') as out:out.write(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('semantic_positions','forecast_GPUh','proposed_hard_GPUh','budget')},indent=2))


if __name__=='__main__':main()
