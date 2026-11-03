"""Frozen seven-role, four-old-CAL F19 speed screen and complete quote."""
import copy

from .cara_fast_spec_r1 import digest
from .cara_f19_speed190_identity_r1 import RUN,STAGE,MANIFEST,PARTIAL_UPDATES
ROLES=('NATIVE35','WC_T006','F19_A1','F19_A1_LIGHT_C','F17_A2_LIGHT_C',
       'F19_DELTA4_LIGHT_C','F16_C')


def build(base,layouts,analysis):
    policies={r['candidate']:r['variants'] for r in layouts['candidates']}
    roles={k:copy.deepcopy(base['roles'][k]) for k in ('NATIVE35','ALLD','F19_A1')}
    roles['WC_T006']=copy.deepcopy(base['roles']['WC_T006'])
    f19=base['roles']['F19_A1']['policy']
    for name,plan,partial in (
        ('F19_A1_LIGHT_C',f19,()),
        ('F17_A2_LIGHT_C',policies['F17_TAIL']['A2_EACH_INTERVAL']['policy'],()),
        ('F19_DELTA4_LIGHT_C',f19,PARTIAL_UPDATES)):
        roles[name]=dict(kind='speed_policy',requested_steps=35,policy=copy.deepcopy(plan),
            light_C=True,partial_updates=list(partial),
            light_C_semantics='CURRENT_EMBEDDING_PLUS_LATEST_TRUE_D_RESIDUAL_NO_PROBE_OSI_FLOW',
            delta_semantics='POST_RF_DIFFERENCE_FROM_MOST_RECENT_TRUE_DD_ONLY')
    roles['F16_C']=dict(kind='policy',requested_steps=35,
        policy=copy.deepcopy(policies['F16_TAIL']['C_ONLY']['policy']))
    roles['F19_OFF_CONTROL']=dict(kind='speed_policy',requested_steps=35,
        policy=copy.deepcopy(f19),light_C=False,partial_updates=[])
    roles['F19_PROFILE']=dict(kind='profile_policy',requested_steps=35,policy=copy.deepcopy(f19))
    members=base['FIT']+base['CHECK'];matrix=[]
    def add(section,member,role,audit=False,clean=False):
        matrix.append(dict(id=f'F19CAL35_{len(matrix)+1:03d}',section=section,member=member,
            role=role,seed=0,audit=audit,eligible_clean_time=clean))
    add('GLOBAL_WARM',members[0],'NATIVE35',True)
    add('GLOBAL_WARM',members[0],'F19_A1',True)
    add('EQUIVALENCE',members[0],'ALLD',True)
    add('EQUIVALENCE',members[0],'F19_OFF_CONTROL',True)
    add('DIAGNOSTIC',members[0],'F19_PROFILE')
    for i,member in enumerate(members):
        for role in ROLES[i:]+ROLES[:i]:add('FORMAL',member,role,clean=True)
    for role in ('F19_A1','NATIVE35'):add('TIMING_REPEAT',members[-1],role,clean=True)
    old={r['role']:r['time_mean']['T_request'] for r in analysis['prompt_equal_summaries']['ALL']}
    prices={r:old.get(r,old['F19_A1']) for r in roles}
    # Use the full old F19-A1 request price for all unmeasured reduced-compute
    # methods. No hypothesized probe/branch saving discounts the whole quote.
    prices['ALLD']=old['NATIVE35'];prices['F19_PROFILE']=old['F19_A1']*1.2
    generation=sum(prices[s['role']] for s in matrix)
    components=dict(all35_requests_seconds=generation,request_variation_10pct_seconds=generation*.10,
        model_load_and_cleanup_seconds=600.,audit_materialization_seconds=240.,stop_release_seconds=600.)
    card=dict(schema='CARA_F19_SPEED190_CAL35_R1',run_id=RUN,stage_name=STAGE,
        inputs=copy.deepcopy(base['inputs']),FIT=base['FIT'],CHECK=base['CHECK'],
        profile=copy.deepcopy(base['profile']),schedule=copy.deepcopy(base['schedule']),
        settings=copy.deepcopy(base['roles']['ALLD']['settings']),roles=roles,formal_roles=list(ROLES),matrix=matrix,
        counts=dict(physical_paths=35,formal_positions=28,global_warm=2,equivalence=2,
            diagnostic=1,timing_repeats=2,actual_updates=1260,new_LPIPS_pairs=24,quality_positions=84),
        quote=dict(components_seconds=components,forecast_GPUh=sum(components.values())/3600,
            hard_GPUh=3.,release_margin_seconds=600,price_basis='B36 prompt-equal full requests; no new-method speed discount',
            postrelease_CPU=dict(cpus=2,memory_GiB=8,wall_seconds=21600,max_vCPUh=12)),
        success=dict(group_speedup_T_DD_min=1.9,LPIPS_Alex_max=.27,
            absolute_T_DD_target_seconds=133.0,
            independent_quality_min_differences=dict(MUSIQ_LONGER512=-1.,subject_consistency=-.01,motion_smoothness=-.01),
            quality_references=['NATIVE35','F19_A1'],quality_gate='PROMPT_EQUAL_POINT_DIFFERENCES_ALL_THREE; bootstrap_CIs_descriptive_on_four_exposed_CAL',selection='Report every arm; passing CAL is not independent confirmation'),
        old_CHECK_exposed=True,independent_new_inputs=False,protected_inputs_accessed=False,
        warm_policy='One Native and one original F19 exercise existing dense/cache/A/flow kernels; no role-specific warm',
        authority=dict(direct_user_authorization=True,
            user_quote='把这个小 CAL 卡也跑一下，跑完验收后给我一个报告',
            single_card_hard_GPUh=3.,authorizes_replay=False,authorizes_total_cap_increase=False),
        preserve_independent_confirmation_planning_GPUh=10.,GPU_dispatch_ready=False)
    card['scope_sha256']=digest(card)
    validate(card)
    return card


def validate(card):
    if card['scope_sha256']!=digest({k:v for k,v in card.items() if k!='scope_sha256'}):raise ValueError('Changed CAL35 scope')
    rows=card['matrix']
    if len(rows)!=35 or len({r['id'] for r in rows})!=35 or set(card['formal_roles'])!=set(ROLES):raise ValueError('Complete35/seven-role scope required')
    formal=[r for r in rows if r['section']=='FORMAL']
    if {(r['member'],r['role']) for r in formal}!={(m,r) for m in card['FIT']+card['CHECK'] for r in ROLES}:raise ValueError('All four old CAL x seven roles required')
    if any(r['seed']!=0 or (r['audit'] and r['eligible_clean_time']) for r in rows):raise ValueError('Frozen seed/audit boundaries differ')
    if card['quote']['forecast_GPUh']>3 or card['quote']['hard_GPUh']!=3:raise ValueError('Complete CAL quote exceeds the authorized small card')
    return card
