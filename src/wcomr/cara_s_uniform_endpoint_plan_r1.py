"""Complete prospective Uniform19 endpoint scope; no execution authority."""
import copy
import math

from .cara_fast_spec_r1 import digest,profile_from,policy_from_mask

NEW_ROLES = ('SU19_BR_DIAG_C','SU19_CFG_C')
REUSED_ROLES = ('F19_C','UNIFORM19_C','F19_A1')
FORMAL_ROLES = REUSED_ROLES + NEW_ROLES


def require(condition,message):
    if not condition:
        raise ValueError(message)


def build(card,diagnostic,scores,analysis,numeric):
    members=card['FIT']+card['CHECK']
    require(len(members)==len(set(members))==4 and len(card['FIT'])==len(card['CHECK'])==2,
            'Exactly the original four CAL inputs required')
    require(analysis['status']=='COMPLETE_ACCEPTED_B36_ANALYSIS' and not analysis['CPU_fixture_only']
        and analysis['formal_logical_positions']==32 and len(scores['rows'])==32
        and scores['scope_sha256']==analysis['scope_sha256']==card['scope_sha256']
        and scores['protocol_sha256']==analysis['protocol_sha256']==card['fidelity_protocol_sha256'],
        'Original complete B36 and unchanged Fidelity protocol required')
    require(numeric['status']=='UNIFORM_INITIALIZATION_TINY_PAIRED_NUMERIC_CPU_ACCEPTED_NOT_ENDPOINT'
        and numeric['production_paths']==36 and numeric['old_fixed_paths']==12
        and numeric['failure_controls']==18 and numeric['checked_flows']==[False,True]
        and numeric['all36_old_new_guided_and_final_output_exact'] is True
        and numeric['ON_OFF_AUDIT_exact'] is True and numeric['checked_members']==card['FIT']
        and numeric['checked_roles']==['Uniform19_C','Uniform19_BR_DIAG_C','Uniform19_CFG_C'],
        'Affected complete numerical CPU evidence required')
    require(diagnostic['original_F19_reproduced_exact'] and not diagnostic['endpoint_results_used']
        and not diagnostic['uniform_parent_risks_collected'],'Original accepted FIT-only initialization diagnostic required')
    origin=diagnostic['origins']['Uniform19_C']
    choices=origin['choices']
    require(choices['BR']['policy_fingerprint']==choices['DIAG']['policy_fingerprint']
        !=choices['CFG']['policy_fingerprint'],'Exactly two distinct Uniform proposals required')
    require(origin['initial_policy_fingerprint']==card['roles']['UNIFORM19_C']['policy']['fingerprint'],
        'Unchanged generic Uniform19 initialization required')
    profile=profile_from(card['profile'])
    policies={}
    for role,objective in zip(NEW_ROLES,('DIAG','CFG')):
        policy=policy_from_mask(profile,choices[objective]['dense'])
        require(policy['fingerprint']==choices[objective]['policy_fingerprint']
            and policy['actions'].count('D')==19 and policy['actions'][23]=='D',
            'Exact accepted 19D proposal and D24 protection required')
        policies[role]=policy
    index={(r['member'],r['role']):r for r in scores['rows']}
    require(len(index)==32,'Duplicate original score position')
    formal,references=[],[]
    expected_model=expected_precision=None
    for member in members:
        native=index[(member,'NATIVE35')]
        require(native['candidate']==native['reference'] and native['status']=='COMPLETE'
            and native['frames']==93 and native['PTS_equal'],'Complete original Native reference required')
        references.append(dict(member=member,source=copy.deepcopy(native['candidate']),
            score_id=native['id'],score_row_sha256=digest(native),decoded_RGB_sha256=native['decoded_RGB_sha256'][0]))
        for role in REUSED_ROLES:
            row=index[(member,role)]
            source=row['candidate']
            require(row['status']=='COMPLETE' and row['frames']==93 and row['PTS_equal']
                and row['reference']==native['candidate'] and source['host']=='two_card'
                and source['gpu_uuid']==analysis['gpu_uuid'] and source['seed']==0
                and source['comparison_input_sha256']==native['candidate']['comparison_input_sha256']
                and source['execution_request_sha256']==native['candidate']['execution_request_sha256'],
                'Exact original reference, input, seed and request required')
            expected_model=expected_model or source['model_sha256']
            expected_precision=expected_precision or source['precision']
            require(source['model_sha256']==native['candidate']['model_sha256']==expected_model
                and source['precision']==native['candidate']['precision']==expected_precision,
                'Original model and precision must be shared')
            formal.append(dict(member=member,role=role,mode='REUSE_COMPLETE_SCORE',
                score_id=row['id'],score_row_sha256=digest(row),source=copy.deepcopy(source),
                reference=copy.deepcopy(row['reference']),decoded_RGB_sha256=copy.deepcopy(row['decoded_RGB_sha256']),
                counts_as_new_sample=False,counts_as_current_batch_timing=False))
        formal.extend(dict(member=member,role=role,mode='GENERATE_AND_SCORE',
            reference_score_id=native['id'],reference=copy.deepcopy(native['candidate'])) for role in NEW_ROLES)
    physical=[]
    def add(section,member,role,*,clean=False):
        physical.append(dict(id=f'SU19_END_{len(physical)+1:03d}',section=section,
            member=member,role=role,seed=0,timing_enabled=True,audit_enabled=False,
            eligible_clean_time=clean))
    for role in ('NATIVE35','F19_A1')+NEW_ROLES:
        add('WARM',card['FIT'][0],role)
    add('ALLD_EQUIVALENCE',card['FIT'][0],'ALLD')
    # Counterbalance deterministic request order across all four CAL inputs.
    timing_roles=('NATIVE35','F19_A1')+NEW_ROLES
    for i,member in enumerate(members):
        for role in timing_roles[i:]+timing_roles[:i]:
            add('FORMAL' if role in NEW_ROLES else 'REPLAY_CONTROL',member,role,clean=True)
    for i,member in enumerate(card['CHECK']):
        for role in NEW_ROLES[::1 if i==0 else -1]:
            add('REPEAT',member,role,clean=True)
    control_pairs=[dict(kind='FRESH_VS_ORIGINAL_DECODED_RGB',member=member,role=role,
        original_score_id=index[(member,role)]['id'],
        original_decoded_RGB_sha256=index[(member,role)]['decoded_RGB_sha256'][0])
        for member in members for role in ('NATIVE35','F19_A1')]
    control_pairs.append(dict(kind='FRESH_NATIVE_VS_ALLD_DECODED_RGB',member=card['FIT'][0],
        role='ALLD',reference_role='NATIVE35',reference_section='WARM'))
    result=dict(schema='CARA_SU19_COMPLETE_ENDPOINT_PROPOSAL_R1',
        status='PROSPECTIVE_COMPLETE_SCOPE_NOT_GPU_READY',host='two_card',gpu_uuid=analysis['gpu_uuid'],
        parent_B36_scope_sha256=card['scope_sha256'],profile=copy.deepcopy(card['profile']),
        schedule=copy.deepcopy(card['schedule']),inputs=copy.deepcopy(card['inputs']),
        FIT=card['FIT'][:],CHECK=card['CHECK'][:],new_policies=policies,
        shared_execution_settings=copy.deepcopy(card['roles']['ALLD']['settings']),
        model_sha256=expected_model,precision_sha256=expected_precision,
        fidelity_protocol_ref=card['fidelity_protocol_ref'],fidelity_protocol_sha256=card['fidelity_protocol_sha256'],
        role_aliases={'SU19_BR_C':'SU19_BR_DIAG_C','SU19_DIAG_C':'SU19_BR_DIAG_C'},
        scientific_roles=list(FORMAL_ROLES),formal_matrix=formal,reference_sources=references,
        physical_matrix=physical,identity_controls=control_pairs,
        counts=dict(logical_quality_positions=20,reused_metric_positions=12,new_scoring_pairs=8,
            original_reference_sources=4,new_GPU_paths=25,warm_paths=4,allD_control_paths=1,
            formal_candidate_paths=8,fresh_native_and_A1_controls=8,timing_repeat_paths=4,
            clean_timing_samples=20,postrelease_decoded_identity_controls=9),
        recipe=dict(initialization='Registered protected-point noise-coordinate Uniform19',
            budget_D=19,updates=36,candidate_count=170,exchange_count=1,
            objectives=['BR','DIAG','CFG'],risk_parents=['Shared25_C','F19_C'],
            risk_inputs=card['FIT'][:],propagation_weight=1,
            positive_gain_only=True,tie_rule='remove-D then add-D numeric order',
            no_positive_gain_fallback='Uniform19_C',recipe_for_this_card_only=True,
            changes_original_S_freeze=False,uniform_parent_risks_collected=False),
        timing=dict(primary_batch_roles=list(timing_roles),clocks=['T_DD','T_request'],
            averaging='Average formal and registered repeats per member, then equal weight all four members',
            group_speedup='Ratio of equal-prompt Native and method time means from this allocation only',
            historical_F19_and_Uniform_times='Separate historical context; never pooled as fresh measurements',
            warm_and_allD_control_excluded=True),
        acceptance=dict(complete25_and_original_release_before_CPU=True,all9_identity_controls_required=True,
            identity_failure='Retain failed complete/partial receipts and cost; no scientific acceptance or automatic replay',
            new_scoring='Once only all eight new candidate-versus-original-Native pairs, all93 frames',
            reused_scoring='Twelve original accepted rows referenced unchanged; never recomputed or independent samples',
            new_metric_veto_thresholds=None,all_failure_denominators_retained=True,
            no_recipe_selection_from_CHECK=True,no_final_or_reserve_inputs=True,
            no_endpoint_initialization_robustness_claim=True),
        readiness=dict(affected_numeric_component=True,whole25_CPU_accepted=False,
            whole_runner_source_frozen=False,actual_reuse_assets_rehashed=False,
            private_storage_bound=False,fresh_admission_passed=False,central_transaction_authorized=False),
        GPU_authorized=False,GPU_dispatch_ready=False,GPU_submissions=0,ledger_written=False)
    validate(result)
    result['scope_sha256']=digest(result)
    return result


def validate(plan):
    members=plan['FIT']+plan['CHECK']
    formal=plan['formal_matrix'];physical=plan['physical_matrix']
    require(len(formal)==20 and {(r['member'],r['role']) for r in formal}==
        {(m,r) for m in members for r in FORMAL_ROLES},'Complete20 scientific matrix required')
    require(sum(r['mode']=='REUSE_COMPLETE_SCORE' for r in formal)==12 and
        sum(r['mode']=='GENERATE_AND_SCORE' for r in formal)==8,'Exact12 reused plus8 new required')
    require(all(r['mode']==('REUSE_COMPLETE_SCORE' if r['role'] in REUSED_ROLES else 'GENERATE_AND_SCORE')
        for r in formal),'Reuse cannot replace a new method endpoint')
    expected={'WARM':4,'ALLD_EQUIVALENCE':1,'FORMAL':8,'REPLAY_CONTROL':8,'REPEAT':4}
    require(len(physical)==25 and len({r['id'] for r in physical})==25
        and {k:sum(r['section']==k for r in physical) for k in expected}==expected,'Complete25 physical scope required')
    for section,roles,inputs in [('FORMAL',NEW_ROLES,members),('REPLAY_CONTROL',('NATIVE35','F19_A1'),members),
                                ('REPEAT',NEW_ROLES,plan['CHECK']),
                                ('WARM',('NATIVE35','F19_A1')+NEW_ROLES,[plan['FIT'][0]]),
                                ('ALLD_EQUIVALENCE',('ALLD',),[plan['FIT'][0]])]:
        require({(r['member'],r['role']) for r in physical if r['section']==section}==
            {(m,r) for m in inputs for r in roles},'Physical role/member coverage differs')
    require(len(plan['identity_controls'])==9 and all(r['seed']==0 and not r['audit_enabled'] for r in physical)
        and sum(r['eligible_clean_time'] for r in physical)==20,'Identity controls or clean timing differs')
    require({(r['member'],r['role']) for r in plan['identity_controls']}==
        {(m,r) for m in members for r in ('NATIVE35','F19_A1')}|{(plan['FIT'][0],'ALLD')}
        and all(r['eligible_clean_time']==(r['section'] in ('FORMAL','REPLAY_CONTROL','REPEAT')) for r in physical),
        'Complete replay controls and warm exclusion required')
    require(not plan['GPU_authorized'] and not plan['GPU_dispatch_ready'] and not plan['ledger_written']
        and plan['GPU_submissions']==0,'Preparation grants no GPU execution')


def quote(plan,analysis):
    validate(plan)
    slowest=max(t['T_request'] for r in analysis['per_member'] if r['role']=='NATIVE35' for t in r['timing_samples'])
    require(math.isfinite(slowest) and slowest>0,'Historical full Native request price required')
    components=dict(generation_all25_at_slowest_Native=25*slowest,
        artifact_copy_save_hash_allowance=25*60,producer_complete_readback_allowance=1800,
        admission_and_model_load_allowance=1800,stop_and_release_allowance=600)
    forecast=math.fsum(components.values())/3600
    hard=math.ceil(forecast*1.10*4)/4
    return dict(status='COMPLETE_ENGINEERING_QUOTE_DRAFT_NOT_DISPATCH_ACCEPTED',
        scope_sha256=plan['scope_sha256'],host='two_card',physical_paths=25,
        components_seconds=components,slowest_original_Native_request_seconds=slowest,
        forecast_GPUh=forecast,proposed_hard_GPUh=hard,hard_limit_rule='10% above forecast, round up to quarter GPUh',
        margin_seconds=(hard-forecast)*3600,requires_separate_over4_GPUh_approval=hard>4,
        postrelease_CPU_scoring_not_GPU_billed=True,all_native_proxy_is_proven_bound=False,
        source_of_allowances='Same explicit whole-card allowances as accepted successor14 engineering quote; artifact allowance scales to25 paths',
        actual_new_policy_GPU_timing_measured=False,whole_quote_accepted=False,
        current_ledger_or_resource_facts_checked=False,GPU_dispatch_ready=False,GPU_submissions=0,ledger_written=False)
