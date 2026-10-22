"""Human-authorized retirement of an unreachable host, preserving its history.

This is an administrative authority reassignment, not a claim that the retired
server was inspected or remotely fenced. Unconfirmed old whole-card liabilities
remain reserved in full. No historical job or event is edited.
"""
import copy
import hashlib
import json
import math

ORIGIN=79.99637737158223
CAP=226
QUOTE='不管两卡服务器了，直接在 4 卡上做起来吧'
OLD_UUIDS=['GPU-de9a5370-cd87-0f1c-a48e-288888777dd3','GPU-cebf7119-cf03-23b9-e192-cd196332b704']

def digest(value):return hashlib.sha256((json.dumps(value,indent=2)+'\n').encode()).hexdigest()

def build(snapshot,authorization,route,epoch,now,accounting):
    if not (authorization.get('user_reply_quote')==QUOTE
        and authorization.get('four_card_is_only_future_authorized_writer') is True
        and authorization.get('two_card_future_dispatch_authority_revoked') is True
        and authorization.get('two_card_remote_fence_observed') is False
        and authorization.get('reset_history') is False):
        raise ValueError('Exact direct human reassignment required; no remote fence may be invented')
    if not (route.get('original_owned_client_exited') is True and route.get('original_33620_has_no_listener') is True
        and route.get('two_card_remote_commands')==0 and route.get('two_card_remote_fence_observed') is False):
        raise ValueError('Actual own retired dispatch route exit required')
    if (snapshot.get('schema')!='WC_GPU_BUDGET_POOL_V2' or snapshot.get('cap_gpu_hours')!=CAP
        or snapshot.get('origin_used_gpu_hours')!=ORIGIN or not snapshot.get('jobs')
        or not all(j['status']=='SETTLED' for j in snapshot['jobs'].values())):
        raise ValueError('Complete settled historical pool with original cap/origin required')
    totals=accounting(snapshot)
    if any(snapshot[k]!=v for k,v in totals.items()) or snapshot.get('budget_overrun_recorded'):
        raise ValueError('Historical accounting mismatch or recorded overrun')
    if not isinstance(epoch,str) or not epoch.startswith('four-card-human-retirement-') or not math.isfinite(now):
        raise ValueError('Unique administrative writer epoch and actual timestamp required')
    value=copy.deepcopy(snapshot)
    holds=[('BANK24',4.5),('FULL1624',12.0)]
    for (name,limit),uuid in zip(holds,OLD_UUIDS):
        key='retired-two-card-'+name.lower()+'-uncertainty-hold-20261022'
        if key in value['jobs']:raise ValueError('Do not create the transition twice')
        value['jobs'][key]=dict(job_id=key,kind='UNCONFIRMED_RETIRED_HOST_WHOLE_CARD_LIABILITY_HOLD',
            status='RESERVED_OR_RUNNING',billed_limit_GPUh=limit,gpu_uuid=uuid,
            supervisor_pid=None,supervisor_start_ticks=None,source_revision='NO_NEW_OLD_HOST_RUN_ASSERTED',
            launch_id='NOT_A_CONFIRMED_GPU_SUBMISSION',stage='RETIRED_HOST_UNKNOWN_DO_NOT_CONTACT',
            actual_cost_unknown=True,confirmed_GPU_submission=False,reserved_unix=now,
            release_policy='ONLY_WITH_INDEPENDENT_TERMINAL_OR_EXPLICIT_BUDGET_RECONCILIATION')
    value.update(writer_epoch=epoch,unique_future_authorized_writer='four_card',
        retired_host_current_state='UNKNOWN',retired_host_remote_fence_observed=False,
        historical_snapshot_is_not_a_current_old_host_observation=True,
        confirmed_GPU_jobs_at_authority_transition=snapshot['gpu_jobs_launched'],
        unconfirmed_old_host_reservation_slots=2,old_host_uncertainty_reserved_GPUh=16.5,
        gpu_jobs_launched_includes_unconfirmed_reservation_slots=True)
    value.update(accounting(value))
    if value['available_gpu_hours']<8.75:raise ValueError('Full BANK24 plus old uncertainty liabilities do not fit')
    value['events'].append(dict(sequence=len(value['events'])+1,unix=now,
        type='DIRECT_HUMAN_RETIRE_OLD_AUTHORITY_KEEP_HISTORY_RESERVE_BOTH_UNCONFIRMED_WHOLE_CARDS',
        writer_epoch=epoch,old_host_uncertainty_hold_GPUh=16.5,new_GPU_submissions=0))
    return value

def validate(snapshot,current,accounting):
    if current['cap_gpu_hours']!=snapshot['cap_gpu_hours'] or current['origin_used_gpu_hours']!=snapshot['origin_used_gpu_hours']:
        raise ValueError('Budget origin/cap changed')
    if any(current['jobs'].get(k)!=v for k,v in snapshot['jobs'].items()):raise ValueError('Historical job changed')
    if current['events'][:len(snapshot['events'])]!=snapshot['events']:raise ValueError('Historical events changed')
    if any(current[k]!=v for k,v in accounting(current).items()):raise ValueError('Stored accounting mismatch')
    holds=[v for k,v in current['jobs'].items() if k not in snapshot['jobs']]
    if len(holds)!=2 or sum(h['billed_limit_GPUh'] for h in holds)!=16.5:
        raise ValueError('Both complete old liabilities must remain reserved')
    if any(h.get('actual_cost_unknown') is not True or 'actual_GPUh' in h or h.get('confirmed_GPU_submission') is not False for h in holds):
        raise ValueError('Unknown old costs may not be converted to zero or confirmed GPU runs')
    return dict(historical_jobs_preserved=len(snapshot['jobs']),historical_events_preserved=len(snapshot['events']),
        used_gpu_hours=current['used_gpu_hours'],old_uncertainty_reserved_gpu_hours=16.5,
        available_gpu_hours=current['available_gpu_hours'],new_GPU_submissions=0,old_current_GPU_state_observed=False)
