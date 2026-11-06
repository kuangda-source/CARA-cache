#!/usr/bin/env python3
"""Freeze complete CAL exploration scope and nonbinding quote; no dispatch."""
import json,hashlib,sys,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from wcomr.policy_generator_r1.interval_grammar import Profile
from wcomr.policy_generator_r1.shared_exploration import roles,shared_dense

def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def build():
    score_ref='reports/wc_scout_saved_assets_actual_CPU_r1_20261018.json'
    score=read(score_ref)['result']['X_S_schedule_candidates']['gain_squared_weighted']['scene_equal_scores']
    source='reports/cara_PG_P1_original_terminal_codec_recovered_20261024_0035.json'
    consumer=json.loads(read(source)['files']['consumer']['raw_utf8'])
    p=consumer['profile'];p['protected_dense']=tuple(p['protected_dense']);p['alpha_candidates']=tuple(p['alpha_candidates']);profile=Profile(**p)
    arm=roles(profile,score);members=consumer['CAL_FIT_members'];order=list(arm);matrix=[]
    def add(section,role,member,repeat):
        matrix.append(dict(id=f'{section}_{role}_{members.index(member)}_{repeat}',section=section,role=role,member=member,seed=0,repeat=repeat,actual_updates=arm[role]['requested_steps']+1))
    warm=['NATIVE35','NATIVE26','NATIVE28','NATIVE30','S26_C','S26_A_PHASE','SHARED20_C','SHARED20_A_PHASE']
    timing=['NATIVE35','NATIVE26','NATIVE28','NATIVE30','S24_C','S24_A_PHASE','SHARED24_C','SHARED24_A_PHASE','S25_A_PHASE','SHARED25_A_PHASE']
    for role in warm:add('WARM',role,members[0],0)
    # Pair forward/reverse within each repeat-input block, no outcome-adaptive ordering.
    for i,member in enumerate(members):
        rotated=order[i:]+order[:i]
        for role in rotated:add('QUALITY',role,member,1)
        if i<2:
            for role in rotated[::-1]:
                if role in timing:add('TIMING_REPEAT',role,member,2)
    for role in ('NATIVE35','SHARED24_A_PHASE'):add('DIAGNOSTIC',role,members[0],0)
    assert len(matrix)==106
    timing_ref='reports/cara_cost112_complete_timing_thermal_analysis_20261025.json'
    observed=read(timing_ref);existing={r['role']:r['complete_request_mean_seconds'] for r in observed['descriptive_CAL_role_summary']}
    native=existing['PG_ALL_D'];seconds={}
    for role,spec in arm.items():
        # Full-D bound for all unmeasured roles, including fewer steps. No optimistic extrapolation.
        seconds[role]=existing.get(role,native)
    generation=sum(seconds[r['role']] for r in matrix)/3600
    components=dict(generation_GPUh=generation,model_load_GPUh=.15,artifact_save_release_GPUh=.35)
    forecast=sum(components.values())*1.15
    native_ref='reports/cara_PG_P2_native_history_CPU_accepted_r4_20261023.json'
    result=dict(status='SHARED_CAL106_FROZEN_PREPARATION_NO_GPU_AUTHORITY',profile=p,roles=arm,
        energy_scores=score,energy_source_ref=score_ref,energy_source_sha256=sha(score_ref),
        generation={str(n):shared_dense(score,n) for n in (20,24,25,26)},
        source_bindings={r:sha(r) for r in (score_ref,source,timing_ref,native_ref)},
        schedules=read(native_ref)['schedule_rows'],CAL_FIT_members=members,matrix=matrix,
        scope=dict(roles=19,CAL=4,seeds=[0],warm_paths=8,quality_paths=76,timing_repeat_paths=20,diagnostic_paths=2,total_paths=106,
            guided_pairs=sum(r['actual_updates'] for r in matrix),CFG_calls=2*sum(r['actual_updates'] for r in matrix),loads=1,
            LPIPS_pairs=72,LPIPS_frames=6696,independent_quality_videos=76,SELECT_paths=0,DEV_paths=0,TEST_paths=0),
        quote=dict(basis='Accepted112 role means; unmeasured roles conservatively use measured fullD mean',arm_seconds=seconds,
            components=components,uncertainty_margin=.15,forecast_GPUh=forecast,proposed_limit_GPUh=11.5,
            limit_approved=False,cumulative_cap_GPUh=226,ledger_snapshot=observed['ledger'],
            post_release_CPU=dict(GPU_held=False,LPIPS_pairs=72,independent_quality_videos=76,
                metrics=['MUSIQ','subject_consistency','motion_smoothness'],cpus=2,memory_GiB=8,wall_limit_hours=6,
                vCPU_hours_upper=12,quality_resource_CPU_acceptance_required=True)),
        contract=dict(exploration=True,scientific_results_require_complete_originals=True,
            timing_predictor_2s_gate_not_prerequisite=True,old_failed_gates_unchanged=True,
            final_absolute_seconds=257.7712338712067,final_relative_native=.8,
            final_budget_rule='min(257.7712338712067, 0.8 * fresh paired Native mean)',
            original_alpha='A target<25:1; target>=25:0.5',age_cap_is_hypothesis=True,
            no_D_added_for_age_cap=True,quality_repetition_scored_once_only_if_RGB_equal=True,
            repeat_prompt_selection='First two frozen CAL members; no time/quality selection',
            timing_repeat_roles=timing,warm_roles=warm,
            nonrepeated_roles_not_independently_latency_confirmed=True,
            no_TEST_or_DEV_selection=True,failures_refusals_retained_no_replacement=True,
            pure_timing_card_and_GRAPH102_deferred=True,hardware_exclusivity_storage_budget_checks_retained=True),
        GPU_dispatch_ready=False,GPU_submissions=0,ledger_written=False)
    assert forecast<11.5
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();v=build()
    with a.output.open('x') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(dict(scope=v['scope'],forecast=v['quote']['forecast_GPUh'],limit=v['quote']['proposed_limit_GPUh'])))
if __name__=='__main__':main()
