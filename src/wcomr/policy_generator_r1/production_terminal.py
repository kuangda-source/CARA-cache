"""Recompute complete PG decisions from original requests, scores and clean inputs."""
import copy
import hashlib
import json
from .production_contract import COUNTS,matrix
from .production_evidence import validate_score,native_clock
from .continuation_preparation import generator_input,require
from .production_batch import run
from ..policy_price_terminal_r1 import record,monitor,IMAGE


def replay(batch,consumer,clock,fit,select):
    """Recompute graph, both search batches, dedup and final SELECT from raw rows."""
    original={r['id']:r for r in batch['rows']};events=[];checkpoints=[]
    require(len(original)==len(batch['rows'])==64,'All64 registered rows retained')
    def endpoint(slot,policy=None,reference=None):
        row=original[slot['id']];events.append(row['id'])
        require(all(row[k]==v for k,v in slot.items() if k!='status'),'Original request differs from recomputed proposal/order')
        return {k:copy.deepcopy(v) for k,v in row.items() if k not in slot or k=='status'}
    recomputed=run(fit_members=fit,select_members=select,native=endpoint,evaluate=endpoint,
        build_consumer=lambda c:consumer,accept_native_clock=lambda r:clock,calibration_cap_GPUh=10.5,
        elapsed_GPUh=lambda:0.,save=lambda s:checkpoints.append(copy.deepcopy(s)),exposure_recheck=lambda:batch['SELECT_exposure_recheck'])
    for key in ('status','rows','candidates','selection_frozen','selected','query_attempts','TEST_used','native_clock','consumer_provenance','budget_seconds','finalists','simple_controls','selection','selected_policy'):
        require(recomputed.get(key)==batch.get(key),'Original decision differs from independent replay: '+key)
    return dict(recomputed=True,executed_slots=events,query_attempts=recomputed['query_attempts'],selected=recomputed['selected'])


def scientific(v):
    runner=record(v,'runner');batch=runner['batch'];consumer=record(v,'consumer');clock=record(v,'native_clock')
    old_raw=v['files']['old_bundle']['raw_utf8'].encode();new_raw=v['files']['new_bundle']['raw_utf8'].encode()
    old_accept=record(v,'old_acceptance');price_accept=record(v,'price_acceptance')
    expected=generator_input(new_raw,price_accept,old_raw,old_accept,clock)
    require(consumer==expected,'Consumer changed old labels/new prices/Native B')
    fit=consumer['CAL_FIT_members'];select=v['select_members'];refs={};requests=v['requests'];scores=v['scores']
    require(len(batch['rows'])==64 and batch['scope_counts']==COUNTS and runner['model_loads']==1,'Whole scope/single load missing')
    rows={r['id']:r for r in batch['rows']}
    require(set(rows)=={r['id'] for r in matrix()},'Missing/duplicate registered row')
    executed=[r for r in batch['rows'] if r['status']!='UNUSED_REGISTERED_UPPER_BOUND']
    require(set(requests)=={r['id'] for r in executed},'Original request set differs from full denominator')
    n_scores=0
    for planned in matrix():
        row=rows[planned['id']]
        require(all(row[k]==val for k,val in planned.items()),'Registered slot mutated')
        if row['status']=='UNUSED_REGISTERED_UPPER_BOUND':continue
        require(row['status'] in ('COMPLETE','TEXT_REJECTED','VIDEO_REJECTED'),'Unfinished/failed path cannot accept')
        req=record({'files':requests},row['id'])
        require(requests[row['id']]['sha256']==row['request_artifact']['sha256'],'Request original SHA changed')
        require(all(row[k]==val for k,val in req['slot'].items() if k!='status'),'Request identity changed')
        require(all(row[k]==val for k,val in req['result'].items()),'Runner row differs from original full request')
        if row['status']!='COMPLETE':continue
        checks=v['artifact_checks'][row['id']]
        require(checks['video_artifact']==row['video_artifact'] and checks['final_latent_artifact']==row['final_latent_artifact'] and checks['frames']==93,'Missing/changed full raw endpoint')
        require(row['solver_steps']==row['guided_pairs']==36,'Non-full path')
        if row['kind']=='NATIVE':
            require(req['policy'] is None,'Native was policy-modified')
            if row['split']!='WARM':refs[row['member']]=row
        else:
            from .production_sampling import validate_policy
            from .interval_grammar import Profile
            p=dict(consumer['profile']);p['protected_dense']=tuple(p['protected_dense']);p['alpha_candidates']=tuple(p['alpha_candidates'])
            policy=validate_policy(Profile(**p),req['policy'])
            require(policy['fingerprint']==row['fingerprint'],'Policy binding changed')
            history=row['semantic_history']
            require(len(history)==36 and [r['step'] for r in history]==list(range(1,37)),'Missing deployment history')
            for i,h in enumerate(history):
                require(h['planned']==policy['actions'][i] and h['actual'] in ('D',h['planned']),'Deployed action changed')
                if h['actual']!=h['planned']:require(h['fallback_reason'] in ('INSUFFICIENT_TRUE_D_ANCHORS','NONFINITE_READOUT_RESTORED_THEN_FULL_D'),'Unregistered policy mutation')
            require(row['teacher_calls']==0 and row['online_fitting'] is False,'Extra label collection/fitting on endpoints')
            if row['split']!='WARM':
                score=record({'files':scores},row['id']);n_scores+=1
                require(scores[row['id']]['sha256']==row['score_artifact']['sha256'],'Score original changed')
                require(row['LPIPS']==validate_score(score,refs[row['member']]['video_artifact'],row['video_artifact'],runner['metric_identity']),'Changed endpoint ranking loss')
    require(len(scores)==n_scores<=40,'Extra/missing scored endpoint')
    L=v['launch'];prefix=v['native_monitor_prefix_raw_utf8']
    require(v['monitor_raw_utf8'].startswith(prefix),'Native prefix not part of final exclusive journal')
    recomputed_clock=native_clock([rows['native_fit_'+str(i)] for i in range(4)],fit_members=fit,
        profile_identity=json.loads(new_raw)['profile_identity'],monitor_raw=prefix,runner=clock['runner'],gpu_uuid=L['gpu_uuid'],now=clock['observed_unix'],source_revision=L['source_revision'],launch_id=L['launch_id'])
    require(recomputed_clock==clock,'Native clock independent recomputation differs')
    replayed=replay(batch,consumer,clock,fit,select)
    actual_events=[r['id'] for r in sorted(executed,key=lambda r:r['started_unix'])]
    require(actual_events==replayed['executed_slots'],'Actual execution order differs from frozen search')
    require(all(a['ended_unix']<=b['started_unix'] for a,b in zip(sorted(executed,key=lambda r:r['started_unix']),sorted(executed,key=lambda r:r['started_unix'])[1:])),'Overlapping full requests')
    return dict(complete_registered_slots=64,executed_paths=len(executed),scored_pairs=n_scores,query_attempts=batch['query_attempts'],decision_recomputed=True,
        selected_policy=batch.get('selected_policy'),clean_Native_clock_accepted=True,teacher_conditioned_labels_preserved=True)


def accept(v):
    from .production_stage import RUN,CONFIG
    L=v['launch'];reg=record(v,'registration');auth=record(v,'authorization');cpu=record(v,'CPU_acceptance');c=record(v,'config');quote=record(v,'quote')
    require(L['run_id']==RUN and L['scope_counts']==COUNTS,'Wrong PG launch')
    require(v['files']['registration']['sha256']==L['registration_sha256'] and reg['source_revision']==L['source_revision'] and reg['stage']==L['stage'],'Stage/source identity differs')
    require(v['payload_actual_sha256']==reg['payload_sha256'] and v['runtime_actual_sha256']==reg['runtime_source_sha256'],'Frozen payload/runtime changed')
    for key,name in [('config',CONFIG),('quote','pg-whole-quote.json'),('old_bundle','pg-old-labels.json'),('new_bundle','pg-clean-prices.json'),('old_acceptance','pg-old-acceptance.json'),('price_acceptance','pg-price-acceptance.json')]:
        require(v['files'][key]['sha256']==reg['payload_sha256'][name],'Registered asset bytes differ: '+key)
    require(c['scope_counts']==quote['scope_counts']==COUNTS and c['matrix']==quote['matrix']==matrix(),'Full64 quote/config differ')
    require(c['billed_limit_GPUh']==quote['billed_limit_GPUh']==L['billed_limit_GPUh'] and 0<L['forecast_GPUh']==quote['forecast_complete_GPUh']<=L['billed_limit_GPUh']<12,'Whole card quote exceeded')
    require(v['files']['authorization']['sha256']==L['authorization_sha256'],'Authorization bytes changed')
    for k in ('run_id','launch_id','source_revision','gpu_uuid','registration_sha256','config_sha256','scope_counts','billed_limit_GPUh'):require(auth[k]==L[k],'Launch authority differs: '+k)
    require(cpu['full_GPU_lifecycle_CPU_accepted'] and cpu['production_CPU_accepted'] and v['files']['CPU_acceptance']['sha256']==auth['independent_CPU_acceptance_sha256'],'Bound complete CPU acceptance missing')
    require(not any(v['original_live_handles'].values()) and v['own_UUID_lock_free'] is True,'Original handle/lock still live')
    con=v['container'];s=con['state']
    require(not s['Running'] and s['ExitCode']==0 and not s['OOMKilled'] and con['image']==IMAGE and con['readonly_root'] and con['pid_mode']=='host' and con['manifest_sha256']==L['registration_sha256'],'Original container did not exit cleanly')
    require(len(con['device_requests'])==1 and con['device_requests'][0]['DeviceIDs']==[L['gpu_uuid']],'Wrong GPU exposure')
    guard=record(v,'guardian');sup=record(v,'supervisor');postexit=record(v,'post_exit');post=record(v,'post');bill=record(v,'billing')
    require(guard['status']=='PG_P1_HOST_GUARDIAN_TERMINAL' and guard['container_exit_code']==0 and not guard.get('error_type'),'Host guardian failure')
    require(all(guard['identity'][k]==L['guardian_identity'][k] for k in ('pid','start_ticks')) and guard['gpu_uuid']==L['gpu_uuid'] and guard['source_revision']==L['source_revision'],'Guardian identity changed')
    require(sup['child_exit_code']==sup['post_exit_code']==0 and sup['exclusive_monitor_accepted'] and not sup.get('error_type') and not sup.get('release_error'),'Supervisor failure')
    require(all(sup[k]==L[k] for k in ('source_revision','run_id','launch_id','gpu_uuid','scope_counts')),'Supervisor identity changed')
    for k in ('run_id','launch_id','source_revision','gpu_uuid','scope_counts','billed_limit_GPUh'):require(bill[k]==L[k],'Bill identity changed')
    actual=bill['actual_GPUh'];require(0<actual==bill['wall_seconds']/3600<=L['billed_limit_GPUh'],'Invalid actual whole-card bill')
    exclusive=monitor(v,L,sup['child_identity'],bill['wall_seconds'])
    pool=v['pool'];job=pool['jobs'][RUN]
    from ..gpu_budget_pool_v2 import BudgetPool
    require(job['status']=='SETTLED' and job['actual_GPUh']==actual and job['launch_id']==L['launch_id'] and job['billing_sha256']==v['files']['billing']['sha256'],'Actual bill not authoritatively settled')
    require(pool['cap_gpu_hours']==226 and all(pool[k]==x for k,x in BudgetPool.accounting(pool).items()),'Cumulative ledger mismatch')
    runner=record(v,'runner')
    require(runner['source_revision']==L['source_revision'] and runner['registration_sha256']==L['registration_sha256'] and runner['config_sha256']==L['config_sha256'] and runner['pid']==sup['child_identity']['pid'],'Runner identity changed')
    require(postexit['exit_code']==0 and postexit['CPU_only_after_UUID_release'] and postexit['final_result_sha256']==v['files']['post']['sha256'] and post['runner_sha256']==v['files']['runner']['sha256'],'Independent post binding failed')
    science=scientific(v);require(post['scientific']==science,'Post and original independent replay differ')
    restore=guard['mode_restoration'];require(restore['restored'] or restore['status']=='RESTORE_DEFERRED_NO_FOREIGN_PROCESS_TOUCHED','Unknown safe mode restoration')
    return dict(status='PG_P1_COMPLETE_ORIGINALS_FINANCE_AND_SELECTION_ACCEPTED',full_protocol_accepted=True,
        source_revision=L['source_revision'],launch_id=L['launch_id'],actual_GPUh=actual,scope_counts=COUNTS,
        exclusive_monitoring=exclusive,scientific= science,PG_P2_input_ready=science['selected_policy'] is not None,
        mode_restoration_pending=not restore['restored'],heldout_quality_or_speed_claim=False,GPU_submissions=0,ledger_written=False)
