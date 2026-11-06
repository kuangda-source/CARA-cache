"""Bounded P2 timing/history engines. Callbacks own resident-model execution.

No GPU dispatch, P1 selection, extra queries, or new-input quality selection.
Every physical slot is durable before execution and cannot be retried in place.
"""
import statistics
from .continuation_preparation import (TIME_BOUNDARY, require, history_matrix,
    native_candidate_counts, select_native_by_time)


def timing_matrix(methods, members, block):
    require(len(members)==len(set(members))==4 and len(methods)==len(set(methods)), 'Unique four CAL and methods required')
    methods=sorted(methods);rows=[]
    for method in methods:
        for i in (1,2):rows.append(dict(id=f'{block}_{method}_warm{i}',split='WARM',method=method,member=members[0],seed=0,repeat=i))
    for r in range(3):
        rotated=members[r:]+members[:r]
        for j,member in enumerate(rotated):
            k=(r+j)%len(methods)
            for method in methods[k:]+methods[:k]:
                rows.append(dict(id=f'{block}_{method}_{member}_r{r+1}',split='CAL_FIT',method=method,member=member,seed=0,repeat=r+1))
    return rows


def run_timing(*,members,schedule_rows,profile_identity,execute_request,accept_exclusive_prefix,save):
    state=dict(status='P2_TIME_REFERENCE',rows=[],screen=None,choice=None,quality_values_used=False)
    def block(methods,name):
        rows=[dict(r,status='NOT_REACHED') for r in timing_matrix(methods,members,name)]
        state['rows'].extend(rows);save(state)
        for row in rows:
            row['status']='RUNNING';save(state)
            try:
                result=execute_request(dict(row))
                require(not (set(result)&{'LPIPS','quality','scores'}),'Timing module must not consume quality')
                require(not (set(result)&(set(row)-{'status'})), 'Request cannot rewrite slot identity')
                row.update(result);save(state)
                require(row['status']=='COMPLETE' and row['timing_boundary']==TIME_BOUNDARY and 0<row['full_request_seconds']<float('inf'), 'No missing or rejected timing slot may disappear')
            except BaseException as e:
                row.update(status='TECH_FAILED',error_type=type(e).__name__,error=str(e));save(state);raise
        return rows
    try:
        reference=block(['CARA','NATIVE35'],'reference')
        prefix=accept_exclusive_prefix(reference)
        require(prefix['accepted'] is True and len(prefix['sha256'])==64,'Independent clean clock prefix required')
        mean=lambda method:statistics.mean(statistics.mean(r['full_request_seconds'] for r in reference if r['method']==method and r['member']==m and r['split']=='CAL_FIT') for m in members)
        state['screen']=native_candidate_counts(schedule_rows,mean('CARA'),mean('NATIVE35'));state['reference_exclusive']=prefix
        state['status']='P2_TIME_CANDIDATES';save(state)
        counts=state['screen']['requested_steps'];result=block([f'NATIVE{n}' for n in counts],'candidate')
        prefix=accept_exclusive_prefix(state['rows']);require(prefix['accepted'] is True,'Complete time prefix not accepted')
        rows=[dict(requested_steps=int(r['method'][6:]),member=r['member'],repeat=r['repeat'],seconds=r['full_request_seconds'],
            profile_identity=profile_identity,accepted=True,exclusive_acceptance_sha256=prefix['sha256'],timing_boundary=TIME_BOUNDARY)
            for r in result if r['split']=='CAL_FIT']
        state['choice']=select_native_by_time(rows,candidates=counts,members=members,target_seconds=mean('CARA'),profile_identity=profile_identity)
        state.update(status='P2_TIME_CHOICE_FROZEN',exclusive=prefix)
        return state
    except BaseException:
        state['status']='P2_TIME_STOP_FULL_DENOMINATOR_RETAINED';raise
    finally:save(state)


def run_history(*,profile,roles,members,execute_request,save):
    matrix=history_matrix(profile,roles,members)
    state=dict(status='P2_HISTORY_RUNNING',matrix=matrix,rows=[])
    plans={p['fingerprint']:p for p in roles.values()}
    state['rows']=[dict(r,id=f'history_{i}',status='NOT_REACHED') for i,r in enumerate(matrix['rows'])];save(state)
    try:
        for row in state['rows']:
            row['status']='RUNNING';save(state)
            try:
                result=execute_request(dict(row),plans[row['policy_fingerprint']])
                require(not(set(result)&(set(row)-{'status'})),'History callback cannot rewrite slot identity')
                row.update(result);save(state)
                require(row['status']=='COMPLETE' and row['shadow_D_pairs']==row['diagnostic']['shadow_D_pairs']
                    and len(row['history_records'])==len(row['diagnostic']['points']), 'Incomplete original history path')
                require(row['clean_deployment_timing'] is False and row['full_request_seconds'] is None,'Shadow time cannot enter latency table')
            except BaseException as e:
                row.update(status='TECH_FAILED',error_type=type(e).__name__,error=str(e));save(state);raise
        state['status']='P2_HISTORY_COMPLETE_REQUIRES_ORIGINAL_ARTIFACT_AUDIT';return state
    except BaseException:
        state['status']='P2_HISTORY_STOP_FULL_DENOMINATOR_RETAINED';raise
    finally:save(state)
