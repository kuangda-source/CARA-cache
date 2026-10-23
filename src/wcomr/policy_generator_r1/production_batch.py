"""One complete adaptive PG-P1 card; evaluators execute complete requests.

Every callback is synchronous and must return original accepted full-request
metadata. The engine never launches GPU work, accepts partial prices or retries
failed videos. Production transport binds the callbacks to the registered stage.
"""
import math
import statistics
from .interval_grammar import Profile
from .proposal_tables import Costs, QuadraticStats, make_proxy_graph
from .budgeted_planner import solve, two_topologies
from .search_protocol import front_dense_control, initial_batch, joint_neighbors, choose_observed
from .production_contract import COUNTS, matrix
from .continuation_preparation import TIME_BOUNDARY


def proposal_context(data):
    p=dict(data['profile']);p['protected_dense']=tuple(p['protected_dense']);p['alpha_candidates']=tuple(p['alpha_candidates']);profile=Profile(**p)
    c=dict(data['costs']);c['dense_seconds']=tuple(c['dense_seconds']);c['C_seconds']=tuple(c['C_seconds']);c['A_seconds_by_alpha']={float(k):tuple(v) for k,v in c['A_seconds_by_alpha'].items()};costs=Costs(**c)
    stats={(r['member'],r['source'],r['update']):QuadraticStats(r['e2'],r['ed'],r['d2'],r['fusion_contract']) for r in data['statistics']}
    if len(stats)!=len(data['statistics']):raise ValueError('Duplicate statistics')
    graph=make_proxy_graph(profile,statistics=stats,fit_members=tuple(data['CAL_FIT_members']),costs=costs,
        weights=tuple(data['weights']),label_basis=data['label_basis'],statistic_profile_identity=data['statistic_profile_identity'])
    if graph['missing_cells']:raise ValueError('Incomplete legal source/time graph')
    result=solve(profile,graph['graph'],budget_seconds=data['budget_seconds'],shared_seconds=costs.shared_seconds,
        quantum_seconds=data['quantum_seconds'],paths_per_state=data['paths_per_state'],maximum_final_paths=data['maximum_final_paths'])
    controls={mode:front_dense_control(profile,costs,budget_seconds=data['budget_seconds'],mode=mode,quantum_seconds=data['quantum_seconds']) for mode in ('C','A')}
    return profile,costs,graph['graph'],initial_batch(controls,two_topologies(result))


def run(*,fit_members,select_members,native,evaluate,build_consumer,accept_native_clock,
        calibration_cap_GPUh,elapsed_GPUh,save,exposure_recheck):
    """Execute native -> first4 -> one refinement4 -> frozen SELECT, exactly once.

    native(slot), evaluate(slot,policy,reference), accept_native_clock(rows),
    build_consumer(accepted_clock), exposure_recheck() are mandatory adapters.
    CPU tests use explicitly synthetic callbacks, never real scientific results.
    """
    if len(fit_members)!=4 or len(select_members)!=2 or len(set(fit_members+select_members))!=6:
        raise ValueError('Four FIT and two disjoint SELECT members required')
    if not 0<calibration_cap_GPUh<12:raise ValueError('Whole registered PG-P1 cap required')
    state=dict(status='PG_P1_NATIVE_CLOCK',scope_counts=COUNTS,rows=[dict(r,status='NOT_REACHED') for r in matrix()],
        candidates=[],selection_frozen=None,selected=None,query_attempts=0,TEST_used=False)
    rows={r['id']:r for r in state['rows']};references={};records=[];plans={};role_ids={}
    def checkpoint():save(state)
    def call(identifier,plan=None):
        row=rows[identifier]
        if row['status']!='NOT_REACHED':raise ValueError('No repeat or replacement request allowed')
        if elapsed_GPUh()>=calibration_cap_GPUh:raise RuntimeError('Whole card cap reached; preserve remaining slots')
        members=select_members if row['split']=='CAL_SELECT' else fit_members
        row.update(member=members[row['member_index']],seed=0,status='RUNNING')
        if plan:row['fingerprint']=plan['fingerprint']
        checkpoint()
        try:
            value=native(dict(row)) if plan is None else evaluate(dict(row),plan,references[row['member']])
            if value.get('status') not in ('COMPLETE','TEXT_REJECTED','VIDEO_REJECTED'):raise ValueError('Missing original complete/refused request')
            if value['status']=='COMPLETE':
                if value.get('timing_boundary')!=TIME_BOUNDARY or not 0<value.get('full_request_seconds',0)<float('inf'):
                    raise ValueError('Actual finite full-request clock required')
                if value.get('solver_steps')!=36 or value.get('guided_pairs')!=36:raise ValueError('Full36 endpoints required')
                if plan and row['split']!='WARM':
                    loss=value.get('LPIPS')
                    if type(loss) not in (float,int) or not math.isfinite(loss) or loss<0:raise ValueError('Full paired LPIPS required')
            forbidden=set(row)&set(value)-{'status'}
            if forbidden:raise ValueError('Evaluator attempted to rewrite registered position')
            row.update(value);checkpoint()
        except BaseException as error:
            row.update(status='TECH_FAILED',error_type=type(error).__name__,error=str(error));checkpoint();raise
        if plan and row['split']!='WARM':
            records.append(dict(fingerprint=plan['fingerprint'],prompt=row['member'],seed=0,split=row['split'],
                status=row['status'],LPIPS=row.get('LPIPS'),measured_seconds=row.get('full_request_seconds'),
                timing_protocol=TIME_BOUNDARY,profile_identity=profile.identity,
                endpoint_basis="NATURAL_FULL_TRAJECTORY_ALL_REGISTERED_FRAMES_LPIPS"))
        return row
    def ranking(split,ids,ceiling):
        return choose_observed([r for r in records if r['split']==split and r['fingerprint'] in ids],
            members=tuple((m,0) for m in (fit_members if split=='CAL_FIT' else select_members)),
            candidate_fingerprints=ids,budget_seconds=data['budget_seconds'],timing_protocol=TIME_BOUNDARY,
            profile_identity=profile.identity,split=split,loss_ceiling=ceiling)
    def query(proposal,roles):
        policy=proposal['policy'];fp=policy['fingerprint']
        if fp in plans:raise ValueError('Physical duplicate must alias; no free query replacement')
        q=state['query_attempts']
        if q>=8:raise ValueError('Q<=8 exhausted')
        plans[fp]=policy;state['query_attempts']+=1
        for role in roles:role_ids[role]=fp
        state['candidates'].append(dict(query_slot=q,roles=roles,proposal=proposal));checkpoint()
        for i in (1,2):call(f'q{q}_warm_{i}',policy)
        for i in range(4):call(f'q{q}_fit_{i}',policy)
    checkpoint()
    try:
        for i in (1,2):call('native_warm_'+str(i))
        for i in range(4):references[fit_members[i]]=call('native_fit_'+str(i))
        clock=accept_native_clock([references[m] for m in fit_members]);data=build_consumer(clock)
        if data.get('Q')!=8 or data['CAL_FIT_members']!=fit_members:raise ValueError('Frozen consumer quota or members differ')
        profile,costs,graph,batch=proposal_context(data)
        state.update(status='PG_P1_FIT_FIRST4',native_clock=clock,consumer_provenance=data['provenance'],budget_seconds=data['budget_seconds'])
        for item in batch['batch']:query(item['proposal'],item['roles'])
        ids=list(plans)
        if not ids:state['status']='BUDGET_NOT_VERIFIED';return state
        first=ranking('CAL_FIT',ids,1e100)
        incumbents=[plans[r['fingerprint']] for r in first['order'][:2]]
        state['status']='PG_P1_FIT_REFINEMENT4';checkpoint()
        if incumbents:
            neighbors=joint_neighbors(profile,graph,costs,incumbents,budget_seconds=data['budget_seconds'],
                quantum_seconds=data['quantum_seconds'],seen=plans,maximum=4,variants_per_boundary=4)
            for i,proposal in enumerate(neighbors):query(proposal,['REFINEMENT_'+str(i)])
        ranked=ranking('CAL_FIT',list(plans),1e100)
        finalists=[r['fingerprint'] for r in ranked['order'][:2]]
        controls=[role_ids.get('SIMPLE_C'),role_ids.get('SIMPLE_A')]
        if not finalists or any(c is None for c in controls):
            state['status']='BUDGET_NOT_VERIFIED';return state
        frozen=list(dict.fromkeys(finalists+controls))
        state.update(status='PG_P1_SEARCH_CLOSED_SELECT_FROZEN',selection_frozen=frozen,finalists=finalists,simple_controls=controls);checkpoint()
        exposure=exposure_recheck()
        if exposure.get('passed') is not True:raise ValueError('Fresh CAL_SELECT exposure metadata audit required')
        state['SELECT_exposure_recheck']=exposure;checkpoint()
        for i in range(2):references[select_members[i]]=call('native_select_'+str(i))
        for q,fp in enumerate(frozen):
            for i in range(2):call(f'select_{q}_{i}',plans[fp])
        simple=[r for r in records if r['split']=='CAL_SELECT' and r['fingerprint'] in set(controls)]
        if len(simple)!=2*len(set(controls)) or any(r['status']!='COMPLETE' for r in simple):
            state['status']='SELECT_CONTROLS_INCOMPLETE_NO_SELECTION';return state
        ceiling={m:min(r['LPIPS'] for r in simple if r['prompt']==m)+.01 for m in select_members}
        selection=ranking('CAL_SELECT',frozen,ceiling)
        state.update(status='PG_P1_CAL_SELECTION_COMPLETE' if selection['selected'] else 'BUDGET_NOT_VERIFIED',
            selection=selection,selected=selection['selected'],selected_policy=plans[selection['selected']['fingerprint']] if selection['selected'] else None)
        return state
    except BaseException as error:
        state.update(status='PG_P1_TECHNICAL_STOP_FULL_SCOPE_RETAINED',error_type=type(error).__name__,error=str(error));raise
    finally:
        if state['status'] in ('PG_P1_CAL_SELECTION_COMPLETE','BUDGET_NOT_VERIFIED','SELECT_CONTROLS_INCOMPLETE_NO_SELECTION'):
            for row in state['rows']:
                if row['status']=='NOT_REACHED':row['status']='UNUSED_REGISTERED_UPPER_BOUND'
        state['actual_billed_GPUh_observed']=elapsed_GPUh();checkpoint()
