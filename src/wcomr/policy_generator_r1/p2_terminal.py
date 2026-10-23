"""P2 original lifecycle/finance gate, composed with raw science audit later.

No budget default: the final bound authorization is supplied after P1/dedup.
This module never reserves, launches, settles or changes hardware state.
"""
import math
from ..policy_price_terminal_r1 import record,monitor,IMAGE,require
from ..policy_asset_price_review_r1 import exclusive_gate
from ..gpu_budget_pool_v2 import BudgetPool


def accept_lifecycle(v):
    L=v['launch'];reg=record(v,'registration');auth=record(v,'authorization');c=record(v,'config');q=record(v,'quote')
    require(L['run_id'].startswith('cara-pg-p2-'),'Wrong P2 run')
    require(v['files']['registration']['sha256']==L['registration_sha256'] and reg['source_revision']==L['source_revision'] and reg['stage']==L['stage'],'Original stage/source changed')
    require(v['payload_actual_sha256']==reg['payload_sha256'] and v['runtime_actual_sha256']==reg['runtime_source_sha256'],'Frozen closure changed')
    require(v['files']['config']['sha256']==L['config_sha256']==reg['payload_sha256']['pg-p2-config.json'] and v['files']['quote']['sha256']==reg['payload_sha256']['pg-p2-whole-quote.json'],'Original config/quote bytes differ')
    require(c['scope_counts']==q['scope_counts']==L['scope_counts'] and c['manifest_sha256']==q['manifest_sha256'],'Bound whole scope differs')
    require(c['final_P1_and_dedup_bound'] is True and q['final_budget_determined'] is True,'P1/dedup/budget remains pending')
    require(v['files']['authorization']['sha256']==L['authorization_sha256'],'Authority changed')
    for k in ('run_id','launch_id','source_revision','gpu_uuid','registration_sha256','config_sha256','scope_counts','billed_limit_GPUh'):require(auth[k]==L[k],'Authority identity changed: '+k)
    require(c['billed_limit_GPUh']==q['billed_limit_GPUh']==L['billed_limit_GPUh'] and math.isfinite(L['billed_limit_GPUh']) and 0<L['forecast_GPUh']==q['forecast_complete_GPUh']<=L['billed_limit_GPUh'],'Final whole quote differs')
    require(auth['specific_whole_card_approved'] is True,'No whole-card authorization')
    cpu=record(v,'CPU_acceptance')
    require(cpu['production_CPU_accepted'] and cpu['full_GPU_lifecycle_CPU_accepted'] and v['files']['CPU_acceptance']['sha256']==auth['independent_CPU_acceptance_sha256'],'Bound CPU acceptance required')
    require(not any(v['original_live_handles'].values()) and v['own_UUID_lock_free'] is True,'Original handles/lock remain live')
    con=v['container'];s=con['state']
    require(not s['Running'] and s['ExitCode']==0 and not s['OOMKilled'] and con['image']==IMAGE and con['readonly_root'] and con['pid_mode']=='host' and con['manifest_sha256']==L['registration_sha256'],'Original container failed')
    require(len(con['device_requests'])==1 and con['device_requests'][0]['DeviceIDs']==[L['gpu_uuid']],'Wrong exposed UUID')
    guard=record(v,'guardian');sup=record(v,'supervisor');bill=record(v,'billing')
    require(guard['status']=='PG_P2_HOST_GUARDIAN_TERMINAL' and guard['container_exit_code']==0 and not guard.get('error_type'),'Host guardian failed')
    require(all(guard['identity'][k]==L['guardian_identity'][k] for k in ('pid','start_ticks')) and guard['gpu_uuid']==L['gpu_uuid'] and guard['source_revision']==L['source_revision'],'Original guardian changed')
    snap=guard['mode_admission']['verified_snapshot'];require(exclusive_gate(snap,gpu_uuid=L['gpu_uuid'],phase='idle',now=snap['observed_unix'])['observation_passed'],'Idle hardware admission failed')
    require(sup['child_exit_code']==sup['post_exit_code']==0 and sup['exclusive_monitor_accepted'] and not sup.get('error_type') and not sup.get('release_error'),'Supervisor failed')
    for k in ('run_id','launch_id','source_revision','gpu_uuid','scope_counts'):
        require(sup[k]==bill[k]==L[k],'Supervisor/bill identity differs')
    require(bill['billed_limit_GPUh']==L['billed_limit_GPUh'],'Bill limit changed')
    actual=bill['actual_GPUh'];require(math.isfinite(actual) and 0<actual==bill['wall_seconds']/3600<=L['billed_limit_GPUh'],'Invalid actual cost')
    exclusive=monitor(v,L,sup['child_identity'],bill['wall_seconds'])
    pool=v['pool'];job=pool['jobs'][L['run_id']]
    require(job['status']=='SETTLED' and job['actual_GPUh']==actual and job['launch_id']==L['launch_id'] and job['billing_sha256']==v['files']['billing']['sha256'],'Actual bill not authoritatively settled')
    require(pool['cap_gpu_hours']==226 and all(pool[k]==x for k,x in BudgetPool.accounting(pool).items()),'Cumulative ledger mismatch')
    runner=record(v,'runner');post=record(v,'post');postexit=record(v,'post_exit')
    require(runner['pid']==sup['child_identity']['pid'] and all(runner[k]==L[k] for k in ('source_revision','registration_sha256','config_sha256')),'Original runner differs')
    require(postexit['exit_code']==0 and postexit['CPU_only_after_UUID_release'] and postexit['final_result_sha256']==v['files']['post']['sha256'] and post['runner_sha256']==v['files']['runner']['sha256'],'Original independent post binding differs')
    restore=guard['mode_restoration'];require(restore['restored'] or restore['status']=='RESTORE_DEFERRED_NO_FOREIGN_PROCESS_TOUCHED','Unknown mode restoration')
    return dict(lifecycle_and_finance_accepted=True,actual_GPUh=actual,exclusive_monitoring=exclusive,
        manifest_sha256=c['manifest_sha256'],scientific_acceptance_required=True,GPU_dispatch_ready=False)
