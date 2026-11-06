#!/usr/bin/env python3
"""Materialize review proposals and evidence reuse; never dispatch experiments."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from wcomr.interval_policy_v6_r1 import initial_development_candidates

DEST=ROOT/'plans/cara_v6_20261020'
SOURCE=Path('/Users/kuangda_gao/Documents/cara_v5_revision_plan_20261019')


def digest(p):
    b=p.read_bytes();return dict(sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))


def write(name,obj):
    p=DEST/name;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')


def prepare():
    DEST.mkdir(parents=True,exist_ok=True)
    archive=ROOT/'plans/reviews/cara_v5_20261019';archive.mkdir(parents=True,exist_ok=True)
    source_directory=SOURCE if SOURCE.is_dir() else archive
    provenance={}
    for p in sorted(source_directory.iterdir()):
        if not p.is_file():continue
        q=archive/p.name
        if q.exists() and q.read_bytes()!=p.read_bytes():
            raise ValueError('Do not overwrite a different review source')
        if p.resolve()!=q.resolve():shutil.copyfile(p,q)
        provenance[p.name]=dict(source=str(p),archived=str(q.relative_to(ROOT)),**digest(q))
    package_manifest=json.loads((archive/'PACKAGE_MANIFEST.json').read_text())
    for entry in package_manifest['files']:
        if digest(archive/entry['name'])!={k:entry[k] for k in ('sha256','bytes')}:
            raise ValueError('Review source does not match the supplied manifest')
    cfg=json.loads((ROOT/'configs/wc_scout_cal12_production_entry_r1_20261018.json').read_text())
    requests=cfg['requests'];scenes=[x['name'] for x in requests]
    plans=initial_development_candidates()
    # Reuse accepted endpoints; full alpha1 late readouts are new identities.
    existing={'K25_FRONT_FULL':'S25-A3','K25_FRONT_LATE':'G01_LATE_A','K26_MOVE22_C':'VARIATION26_C'}
    purpose={
        'K25_MOVE22_DROP21_FULL':'REV-R1',
        'K26_FRONT_FULL':'REV-R1','K26_MOVE22_FULL':'REV-R1',
        'SINGLE22':'REV-R2-A','SINGLE23':'REV-R2-A'}
    new_methods=list(purpose)
    rows=[]
    for repeat in (1,2):
        for m in new_methods if repeat==1 else new_methods[::-1]:
            rows.append(dict(id=f'warm_{repeat}_{m}',section='WARMUP',scene=scenes[0],
                method=m,repeat=repeat,trace_all36=True,observer=repeat==2))
        rows.append(dict(id=f'bridge_{repeat}_SINGLE21',section='COMPATIBILITY_WARMUP',scene=scenes[0],
            method='SINGLE21_COMPATIBILITY_ONLY',repeat=repeat,trace_all36=True,observer=repeat==2))
    for i,s in enumerate(scenes):
        for m in new_methods if i%2==0 else new_methods[::-1]:
            rows.append(dict(id=f'formal_{i}_{m}',section='FORMAL',scene=s,method=m,
                trace_all36=False,observer=False,task=purpose[m]))
    # Deliberately construct the old single21 bridge, not A3.
    from wcomr.interval_policy_v6_r1 import compile_interval_plan
    bridge=compile_interval_plan(drop_dense=(21,),coverage='explicit_ablation',explicit_A=(21,)).manifest()
    formal=sum(x['section']=='FORMAL' for x in rows);warm=len(rows)-formal
    assert (formal,warm,len(rows))==(20,12,32)
    quote_source=ROOT/'reports/wc_scout_CAL12_whole_quote_R1_20261018.json'
    old_quote=json.loads(quote_source.read_text());terms=old_quote['terms_seconds']
    alpha_copies=2.0 # Explicit new allowance per planned A, not a measured action price.
    manifests={k:v.manifest() for k,v in plans.items()}
    manifests['SINGLE21_COMPATIBILITY_ONLY']=bridge
    planned_A=sum(manifests[r['method']]['counts']['A'] for r in rows)
    quote_terms=dict(load=terms['load'],
        whole_requests=len(rows)*old_quote['source_whole_request_max_seconds'],
        projected_unattributed=len(rows)*terms['projected_unattributed']/old_quote['scope_counts']['total_paths'],
        full_warm_trace=warm*60.,setup=300.,
        additional_A_planning_allowance=planned_A*alpha_copies,
        observer_copy_hash_allowance=len(rows)*60.)
    forecast=sum(quote_terms.values())*1.2/3600
    quote=dict(status='ENGINEERING_COMPLETE32_FORECAST_NOT_PRODUCTION_ADMISSION_QUOTE',
        source_ref=str(quote_source.relative_to(ROOT)),source_binding=digest(quote_source),
        terms_seconds=quote_terms,planned_A_executions=planned_A,
        additional_A_allowance_seconds_per_execution=alpha_copies,
        action_unit_prices_measured=False,margin=1.2,
        forecast_complete_GPUh=forecast,proposed_billed_limit_GPUh=6.25,
        exact_runtime_upper_bound_guarantee=False,actual_production_CPU_accepted=False,
        forecast_requires_revalidation_after_actual_entry_and_instrumentation_freeze=True)
    write('FIRST_DEV_UNION32_DRAFT.json',dict(
        card='WC-CARA-V6-DEV-R1-R2A-UNION32-DRAFT-20261020',
        status='COMPLETE_SCOPE_DRAFT_LOCAL_STRUCTURAL_PASS_NOT_GPU_READY',
        requests=requests,method_plans={m:manifests[m] for m in new_methods+['SINGLE21_COMPATIBILITY_ONLY']},
        positions=rows,scope_counts=dict(formal_paths=formal,full_warm_and_bridge_paths=warm,
            total_paths=len(rows),ordinary_pairs=len(rows)*36,ordinary_CFG_calls=len(rows)*72,
            loads=1,new_Native_formal=0,online_teacher_pairs=0),
        formal_by_task={'REV-R1':12,'REV-R2-A':8},
        compatibility_bridge='Old S25-A1 endpoint; not two new scientific observations',
        source_request_config='configs/wc_scout_cal12_production_entry_r1_20261018.json',
        source_request_binding=digest(ROOT/'configs/wc_scout_cal12_production_entry_r1_20261018.json'),
        production_adapter_implemented=False,actual_production_CPU_accepted=False,
        GPU_dispatch_ready=False,GPU_execution_selected=False,new_GPU_submissions=0,
        downstream_of='Original BANK24 full acceptance or explicit separate direction decision; never amend BANK24',
        parameters=dict(beta=1,shared_alpha=1,true_D_only_anchor=True,P=False,F_B=False,
            original_head_paid_even_alpha1=True,post_RF_shared_CFG_fusion=True),
        quality_results=None,speed_results=None,quote=quote))
    quality=json.loads((ROOT/'reports/wc_CAL12_independent_A_factorial_and_shared_plan_analysis_20261019.json').read_text())
    pool=[]
    for r in quality['per_scene_methods']:
        pool.append({k:r[k] for k in ('scene','method','source_batch','original_row_id','LPIPS','D_steps','A_steps',
            'video_sha256','reference_video_sha256','final_latent_sha256')})
    write('DEVELOPMENT_UNION_V6.json',dict(status='FINITE_INITIAL_DESIGN_AND_EXACT_ACCEPTED_ENDPOINT_REUSE',
        CAL=scenes,candidates={k:manifests[k] for k in plans},accepted_equivalent_candidates=existing,
        equal_alpha1_front_A_is_new_not_legacy_phase_front_A=True,
        count_families={'K25':list(plans)[:3],'K26':list(plans)[3:6]},
        count_family_is_measured_time_budget=False,time_budgets_B1_B2_seconds=None,
        new_first_round_R1_formal=12,new_R2A_formal=8,first_complete_physical_card='FIRST_DEV_UNION32_DRAFT.json',
        development_revisions=dict(initial_round=1,maximum_reasoned_scientific_revisions=1,
            revision_requires_failure_analysis_and_new_manifest=True),
        R2_neighbor_new_formal_upper=8,R3_logical_grid_upper=48,
        R3_union_new_formal_count=None,R3_union_complete_GPUh=None,
        R3_dedup_rule='Union by complete physical identity. Selected R1 and R2-N endpoints may recur in R3; unselected search and R2-A cost remain in research ledger.',
        accepted_endpoint_pool=pool,quality_pool_ref='reports/wc_CAL12_independent_A_factorial_and_shared_plan_analysis_20261019.json',
        quality_reuse_requires_compatibility_bridge=True,clean_timing_reusable=False,
        first32_completes_budget_calibration=False,
        reused_candidate_comparable_time_measurements='Required in R3 before selection; physical paths must be included in the new union and complete quote',
        dedup_identity_fields=['model_checkpoint_SHA','input_prompt_and_condition_SHA','seed_and_noise_SHA',
            'solver_grid_SHA','precision_backend_runtime','D_mask','A_mask','alpha_rule','readout_coordinate',
            'warp_head_RF_order','source_anchor_semantics','fallback_rule','execution_source_SHA',
            'measurement_protocol'],
        new_video_results=None))
    exposures={}
    def add_request(r,ref):
        if not isinstance(r,dict) or not r.get('name') or not r.get('prompt'):return
        name=r['name'].split('_SCOUT_DEV_seed')[0]
        h=hashlib.sha256(' '.join(r['prompt'].split()).encode()).hexdigest()
        e=exposures.setdefault((name,h),dict(canonical_name=name,prompt_text_sha256=h,refs=[]))
        if ref not in e['refs']:e['refs'].append(ref)
    for p in sorted((ROOT/'configs').glob('*.json')):
        try:d=json.loads(p.read_text())
        except (ValueError,OSError):continue
        if not isinstance(d,dict):continue
        for r in d.get('requests',[]):add_request(r,str(p.relative_to(ROOT)))
        for v in d.get('input_files',{}).values() if isinstance(d.get('input_files'),dict) else []:
            q=ROOT/v.get('ref','')
            if q.is_file() and q.suffix=='.json':add_request(json.loads(q.read_text()),str(q.relative_to(ROOT)))
    write('TEST_V6_RESERVATION_PROTOCOL.json',dict(status='RESERVED_DESIGN_NOT_FROZEN_TEST_IDENTITIES',
        current_task_mode='text2world',source_mode_is_video_conditioned=False,
        model='Cosmos-Predict2.5-2B',solver_num_steps_argument=35,actual_guided_updates=36,
        dimensions=dict(frames=93,resolution='432,768',guidance_argument=7),
        primary_R4A=dict(prompts=12,seeds_per_prompt=2,roles=7,formal_paths=168,
            roles_order=['NATIVE35','FRONT_C','FRONT_A','TUNED_WC','TUNED_RA','FROZEN_NEIGHBOR','FROZEN_INTERVAL'],
            identities=None,seeds_proposed=[17,43],seeds_frozen=False),
        conditional_R4B=dict(subset_prompts=6,seeds_per_prompt=2,non_Native_roles=6,
            maximum_additional_formal_paths=72,
            subset_selection='Take first six of a strata-balanced hash order frozen before R4A generation/results',
            subset_identities=None,enabled=False),
        maximum_joint_formal=240,complete_GPUh_quote=None,complete_billed_limit_GPUh=None,
        launch_permission='Only after full identity/CPU/quote and specific approval if >=12 GPUh; no threshold-evading split',
        freeze_requires=['Final method and direct neighbor frozen','B1/B2 measured-time definitions frozen',
            'Baseline finite tuning frozen','All 12 input IDs and seed/noise hashes frozen',
            'B2 subset fixed before B1 outcomes','Common primary cohort rule and failures frozen',
            'Full warm/load/scoring/guard/diagnostic budget and physical scope frozen',
            'Registered-output identity audit beyond this local declaration inventory'],
        local_declared_exposure_inventory=list(exposures.values()),
        exposure_inventory_basis='All currently declared config requests/input_files including planned DEV; conservative exclusion, not global proof of no exposure',
        exclude_all_N07=True,exclude_all_CAL_and_EXPL_DEV=True,exclude_BANK24_DEV6=True,
        aggregation='93 frames -> video; two seeds -> prompt; prompts equal weight; paired prompt bootstrap4096',
        failure_policy='Retain text/video rejection, technical failure, missing Native and N/A. No replacement, zero-fill or seed cherry-picking.',
        primary_common_cohort_rule='For a declared contrast include complete dual-seed prompts common to all roles in that contrast; report full12 and retained denominator; do not choose comparison membership after outcomes',
        narrower_pairwise_secondary_only=True,quality_results=None,speed_results=None,new_GPU_submissions=0))
    variant_map=dict(schema_version=1,status='METHOD_IDENTITIES_SEPARATED_NO_RESULT_RENAMING',
        variants=[
            dict(id='legacy.efficient',internal='A_NO_P',display='CARA-Cache Legacy-Efficient',
                evidence=['N07','N08','N09','N10'],transfer_results_to_final_interval=False),
            dict(id='legacy.h1',internal='TABLE_PHASE_H1',display='CARA-Cache Legacy-H1',
                evidence=['N07','N08','N09','N10'],transfer_results_to_final_interval=False),
            dict(id='dev.interval25.a3',internal='S25-A3',display='Interval Correction (25D, A21-23, CAL)',
                evidence=['Window24','CAL12-four-grid'],independent_TEST_complete=False),
            dict(id='dev.shared26.c',internal='VARIATION26_C',display='Shared Refresh Plan (26D, C, CAL)',
                evidence=['CAL12'],independent_TEST_complete=False),
            dict(id='final.interval.B1',internal=None,display='CARA-Cache Interval (B1, candidate)',
                frozen=False,quality_results=None,speed_results=None),
            dict(id='final.interval.B2',internal=None,display='CARA-Cache Interval (B2, candidate)',
                frozen=False,quality_results=None,speed_results=None)],
        final_method_is_offline_shared_interval_plan=True,old_H1_online_independence_not_inferred=True,
        source_package_is_proposal_not_execution_authority=True)
    write('paper_variant_map.json',variant_map)
    # JSON is valid YAML 1.2; use identical bytes for simple cross-chat parsing.
    shutil.copyfile(DEST/'paper_variant_map.json',DEST/'paper_variant_map.yaml')
    tasks=[
        ('REV-R0',1,'PARTIAL_LOCAL_STRUCTURAL_AND_DOCUMENTS_READY','Freeze reproducible method/data/variant/reuse protocol',0,['BANK24 schedule preserved'],['production entry/runtime/source validation','final B1/B2 and TEST IDs']),
        ('REV-R1',1,'INITIAL_FINITE_CANDIDATES_DEFINED_NOT_VIDEO_EXECUTED','Finite shared interval-policy development',12,['REV-R0'],['32-path draft production adapter/CPU','measured time budgets and selection guards']),
        ('REV-R2-A',3,'EXACT8_NEW_FORMAL_DEFINED_NOT_EXECUTED','Single22/Single23 at same25D and alpha1',8,['REV-R0'],['32-path draft production adapter/CPU','8 new formal endpoints']),
        ('REV-R2-N',3,'RFC_PRIMARY_SOURCE_IDENTIFIED_ADAPTATION_NOT_FROZEN','One direct correction neighbor under common mask and coverage',8,['REV-R0'],['faithful source/code audit','adaptation note/formula parity/whole quote/real CPU']),
        ('REV-R3',4,'FINITE_FRONTIER_UNION_PENDING_IDENTITY_AND_COST','Two measured budgets x4CAL x6 roles, deduped union',48,['REV-R1','REV-R2-N'],['exact new union count/whole quote','fair finite WC/RA tuning','final freeze']),
        ('REV-R4-A',2,'CONDITIONAL_PLANNED_NOT_FROZEN_OR_APPROVED_CARD','12 new prompts x2 seeds x7 roles',168,['REV-R1','REV-R2-A','REV-R2-N','REV-R3'],['12 unseen identities','specific complete quote/CPU/approval if >=12','168 formal plus warm/load/score']),
        ('REV-R4-B',4,'CONDITIONAL_DISABLED_PRESELECT_SUBSET_BEFORE_R4A','6 prespecified prompts x2 seeds x6 roles',72,['REV-R4-A design freeze'],['subset before R4A outcomes','B2 variant frozen','complete cost and phase decision']),
        ('REV-R5-W',5,'CONDITIONAL_OTHER_WINDOWS_NOT_RUNTIME_VALIDATED','Two extra legal windows x4CAL x C/continuousA',16,['REV-R1','REV-R2-A'],['actual protection/source-age legality','own quote/production CPU','16 endpoints if enabled']),
        ('REV-R5-M',5,'SECOND_BACKBONE_OR_SETTING_NOT_SELECTED','6 prompts x2 seeds x4 roles transfer',48,['REV-R4-A'],['mature CFG backbone/setting and calibration','asset/runtime and complete quote/CPU']),
        ('REV-R6',6,'FINAL_VARIANT_TIMING_AND_QUALITY_PENDING','New final method repeats and automatic quality',30,['REV-R4-A'],['2 inputs x5 roles x3 balanced rounds plus10warm','exclusive GPU and paid full pipeline','reuse new TEST videos for five-model scores']),
        ('REV-R7',7,'CLAIM_AND_EVIDENCE_WRITING_PROTOCOL_READY','Align method, data table, main results and claims',0,['REV-R0','REV-R4-A','REV-R6'],['fill only accepted final-method results','choose narrative from actual direct-neighbor/plan findings'])]
    registry=[]
    count_basis={
        'REV-R0':'CPU_AND_DOCUMENTATION_NO_NEW_GENERATION',
        'REV-R1':'EXACT_NEW_FORMAL_INITIAL12',
        'REV-R2-A':'EXACT_NEW_FORMAL8',
        'REV-R2-N':'NEW_FORMAL_UPPER8_BEFORE_ADAPTATION',
        'REV-R3':'LOGICAL_GRID_UPPER48_NEEDS_PHYSICAL_AND_TIME_DEDUP',
        'REV-R4-A':'DESIGN_NEW_FORMAL168_UNFROZEN',
        'REV-R4-B':'CONDITIONAL_MAXIMUM_NEW_FORMAL72',
        'REV-R5-W':'CONDITIONAL_MAXIMUM_NEW_FORMAL16',
        'REV-R5-M':'CONDITIONAL_INITIAL_NEW_FORMAL48',
        'REV-R6':'NEW_TIMING_FORMAL30_PLUS_PROPOSED10_WARM',
        'REV-R7':'WRITING_NO_NEW_GENERATION'}
    contribution_map={'REV-R0':['C1','C2','C3'],'REV-R1':['C1','C2'],
        'REV-R2-A':['C1'],'REV-R2-N':['C1'],'REV-R3':['C2','C3'],
        'REV-R4-A':['C1','C2','C3'],'REV-R4-B':['C2','C3'],
        'REV-R5-W':['C1'],'REV-R5-M':['C1','C2','C3'],
        'REV-R6':['C3'],'REV-R7':['C1','C2','C3']}
    for id,priority,status,title,count,deps,gaps in tasks:
        registry.append(dict(id=id,priority=priority,status=status,title=title,
            formal_count_or_upper=count,count_basis=count_basis[id],
            formal_count_is_complete_physical_GPU_scope=False,
            contribution_ids=contribution_map[id],
            dependencies=deps,remaining_gaps=gaps,quality_results=None,speed_results=None,
            production_CPU_accepted=False,GPU_dispatch_ready=False,new_GPU_submissions=0))
    write('TASK_REGISTRY_V6.json',dict(schema_version=1,updated_local_date='2026-10-20',
        tasks=registry,original_BANK24_scope_and_automation_unchanged=True,
        first_dev_scope='FIRST_DEV_UNION32_DRAFT.json',
        ordering=['BANK24 original complete acceptance','R0 and initial R1/R2 preparation on CPU',
            'First exact development union after own production CPU','R2-N direct neighbor and finite R3 union',
            'Freeze final method/budgets/baselines and unseen TEST','R4-A and conditional preselected R4-B',
            'R5 supporting scope and final R6 timing/quality','R7 paper evidence closure'],
        authority=dict(cumulative_cap_GPUh=226,origin_GPUh=79.99637737158223,
            standalone_card_strict_under12_autonomous=True,
            standalone_card_at_least12_or_insufficient_balance_needs_specific_approval=True,
            no_split_to_avoid_threshold=True,long_task='one technical midpoint and one ETA collection',
            F_B='CLOSED',P_ACR='DEFERRED',training=False,human_review=False,paid_VLM=False,OMR=False),
        source_package_not_blanket_approval=True,all_formal_counts_exclude_warm_load_post_score=True,
        quoted_first_dev_forecast_GPUh=forecast,proposed_first_dev_cap_GPUh=6.25,
        final_test_total_quote_and_permission_pending=True))
    shutil.copyfile(DEST/'TASK_REGISTRY_V6.json',DEST/'TASK_REGISTRY_V6.yaml')
    sources=[ROOT/'reports/wc_CAL12_independent_A_factorial_and_shared_plan_analysis_20261019.json',
        ROOT/'reports/wc_scout_CAL12_full12_terminal_independent_acceptance_20261019.json',
        ROOT/'reports/wc_drop1_window24_full24_terminal_independent_acceptance_20261019.json',
        ROOT/'reports/wc_cara_v6_interval_compiler_local_CPU_controls_20261020.json']
    auto=Path('/Users/kuangda_gao/.codex/automations/worldcache-bank24/automation.toml')
    reconcile=dict(status='REVIEW_PACKAGE_INTEGRATED_PLAN_AND_LOCAL_STRUCTURAL_CONTROLS_ONLY',
        package_manifest_ref=str((archive/'PACKAGE_MANIFEST.json').relative_to(ROOT)),
        archived_package_files=provenance,source_package_unchanged=True,
        all_five_supplied_manifest_hashes_verified=True,
        discussion_ref='chatgpt-conversation://6abf4581-4ec8-83e8-8990-3efe11053cf4',
        latest_discussion_read=True,discussion_is_context_not_execution_authority=True,
        source_bindings={str(p.relative_to(ROOT)):digest(p) for p in sources},
        BANK24_automation_binding=dict(path=str(auto),**digest(auto)),
        BANK24_automation_modified=False,SSH_calls=0,new_server_CPU_jobs=0,new_GPU_submissions=0,
        actual_production_CPU_accepted=False,new_scientific_results=None,
        first_dev_engineering_forecast_GPUh=forecast,first_dev_proposed_cap_GPUh=6.25,
        current_finance_basis=dict(observed_local='2026-10-19T23:28:49.481+08:00',
            actual_GPUh=116.825023108771,cap_GPUh=226,active_reservation_GPUh=0,
            available_GPUh=109.174976891229,current_turn_live_verified=False),
        conflict_resolutions=[
            'At most one scientifically justified revision after the initial finite round, taking the stricter handoff/registry rule',
            'Priority2 unseen main test executes only after development/neighbor/final freeze dependencies, not before them',
            '25D/26D are count families; actual B1/B2 are measured-time budgets not yet frozen',
            'Review formal counts exclude complete warm/load/scoring/guard costs; no blanket GPU approval',
            'Moving D22 cuts correction interval at22; never combine old A21-23 bitmap with new retainedD22'])
    out=ROOT/'reports/wc_cara_v6_revision_package_and_current_evidence_reconciliation_20261020.json'
    out.write_text(json.dumps(reconcile,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(status=reconcile['status'],first_dev_total_paths=len(rows),
        first_dev_new_formal=formal,first_dev_forecast_GPUh=forecast,declared_exposure_records=len(exposures),
        tasks=len(registry),new_GPU_submissions=0),ensure_ascii=False))


if __name__=='__main__':prepare()
