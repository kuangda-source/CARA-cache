"""Independent whole104 numerical, score, timing and financial acceptance."""
from .historical_card import COUNTS,check_card
from .historical_collection import audit_rows,FORMAL
from .historical_timing_analysis import analyze
from .production_evidence import validate_score
from .continuation_preparation import require
from ..policy_price_terminal_r1 import record,monitor,IMAGE


def scientific(v):
    card=record(v,'card');runner=record(v,'runner');batch=runner['batch']
    require(runner['model_loads']==1,'Single model load required')
    clocks=audit_rows(card,batch,v['requests'],v['artifact_checks'])
    controls=v['controls'];require(len(controls)==15 and v['all36_diagnostic_equal'],'Full numerical controls missing')
    expected=[]
    for s in card['matrix']:
        if s['role']=='PG_ALL_D':expected.append((next(x['id'] for x in card['matrix'] if x['role']=='NATIVE' and all(x[k]==s[k] for k in ('section','member','repeat'))),s['id']))
        if s['section']=='DIAGNOSTIC':expected.append((next(x['id'] for x in card['matrix'] if x['section']=='CALIBRATION' and x['role']==s['role'] and x['member']==s['member']),s['id']))
    require([(c['left'],c['right']) for c in controls]==expected,'Control pairing/denominator changed')
    for c in controls:
        left,right=c['left'],c['right'];a=v['artifact_checks'][left];b=v['artifact_checks'][right]
        require(a['latent_tensor']==b['latent_tensor'] and c['left_rgb']==c['right_rgb'] and c['left_rgb']['frames']==93 and c['latent_equal'] and c['RGB93_equal'],'Original numerical control mismatch')
    require(v['artifact_checks']['DIAGNOSTIC_NATIVE_0_1']['guided_tensors']==v['artifact_checks']['DIAGNOSTIC_PG_ALL_D_0_1']['guided_tensors'],'All36 guided identity differs')
    verified=record(v,'collection_verified');require(verified['controls']==controls and verified['all36_diagnostic_equal'] and verified['before_GPU_release'],'Pre-release numerical checks missing')
    progress=record(v,'score_progress');bill=record(v,'billing');release=progress['release']
    require(progress['status']=='CPU_SCORE_COMPLETE72' and progress['completed_pairs']==progress['planned_pairs']==72,'Incomplete scores')
    require(all(release[k] for k in ('GPU_released','ledger_settled','lock_free','CUDA_hidden')) and release['billing_sha256']==v['files']['billing']['sha256'] and release['observed_unix']>=bill['ended_unix'] and progress['started_unix']>=release['observed_unix'],'Scoring before GPU release')
    rows={r['slot']['id']:r['result'] for r in batch['rows']};expected=[s for s in card['matrix'] if s['section'] in FORMAL and s['role']!='NATIVE']
    require(set(v['scores'])==set(progress['scores'])=={s['id'] for s in expected},'Missing/extra paired scores')
    quality={}
    for slot in expected:
        ref=next(s for s in card['matrix'] if s['role']=='NATIVE' and all(s[k]==slot[k] for k in ('section','member','seed','repeat')))
        score=record({'files':v['scores']},slot['id']);entry=progress['scores'][slot['id']]
        require(entry['reference_id']==ref['id'] and entry['score_artifact']['sha256']==v['scores'][slot['id']]['sha256'],'Score source changed')
        metric=score['metric_identity'];require(metric['alexnet_sha256']=='7be5be791159472b1fbf3c69796f7cb30dca7ad8466c2df70058c37116cdee02' and metric['linear_sha256']=='df73285e35b22355a2df87cdb6b70b343713b667eddbda73e1977e0c860835c0' and metric['version']=='0.1.4','Metric identity changed')
        value=validate_score(score,rows[ref['id']]['video_artifact'],rows[slot['id']]['video_artifact'],metric);require(value==entry['LPIPS'],'Score scalar changed')
        quality.setdefault(slot['role'],[]).append(dict(member=slot['member'],repeat=slot['repeat'],LPIPS=value))
    return dict(complete_paths=104,scored_pairs=72,scored_frames=6696,all36_Native_PG_equal=True,controls=15,
                timing=analyze(card,clocks),quality=quality,independent_prompts=4,selection_performed=False,heldout_claim=False)


def accept(v):
    from .historical_card import RUN,CONFIG,MANIFEST
    L=v['launch'];reg=record(v,'registration');auth=record(v,'authorization');cpu=record(v,'CPU_acceptance');c=record(v,'config');quote=record(v,'quote')
    require(L['run_id']==RUN and L['scope_counts']==COUNTS,'Wrong PG launch')
    require(v['files']['registration']['sha256']==L['registration_sha256'] and reg['source_revision']==L['source_revision'] and reg['stage']==L['stage'],'Stage/source identity differs')
    require(v['payload_actual_sha256']==reg['payload_sha256'] and v['runtime_actual_sha256']==reg['runtime_source_sha256'],'Frozen payload/runtime changed')
    for key,name in [('config',CONFIG),('quote','pg-whole-quote.json'),('card',MANIFEST)]:
        require(v['files'][key]['sha256']==reg['payload_sha256'][name],'Registered asset bytes differ: '+key)
    card=record(v,'card');check_card(card)
    require(c['scope_counts']==COUNTS and c['matrix']==card['matrix'] and quote==card['quote'],'Full104 quote/config differ')
    require(c['billed_limit_GPUh']==quote['billed_limit_GPUh']==L['billed_limit_GPUh'] and 0<L['forecast_GPUh']==quote['forecast_GPUh']<=L['billed_limit_GPUh']<12,'Whole card quote exceeded')
    require(v['files']['authorization']['sha256']==L['authorization_sha256'],'Authorization bytes changed')
    for k in ('run_id','launch_id','source_revision','gpu_uuid','registration_sha256','config_sha256','scope_counts','billed_limit_GPUh'):require(auth[k]==L[k],'Launch authority differs: '+k)
    require(cpu['full_GPU_lifecycle_CPU_accepted'] and cpu['production_CPU_accepted'] and v['files']['CPU_acceptance']['sha256']==auth['independent_CPU_acceptance_sha256'],'Bound complete CPU acceptance missing')
    require(not any(v['original_live_handles'].values()) and v['own_UUID_lock_free'] is True,'Original handle/lock still live')
    con=v['container'];s=con['state']
    require(not s['Running'] and s['ExitCode']==0 and not s['OOMKilled'] and con['image']==IMAGE and con['readonly_root'] and con['pid_mode']=='host' and con['manifest_sha256']==L['registration_sha256'],'Original container did not exit cleanly')
    require(len(con['device_requests'])==1 and con['device_requests'][0]['DeviceIDs']==[L['gpu_uuid']],'Wrong GPU exposure')
    guard=record(v,'guardian');sup=record(v,'supervisor');postexit=record(v,'post_exit');post=record(v,'post');bill=record(v,'billing')
    from ..policy_asset_price_review_r1 import exclusive_gate
    admitted=guard['mode_admission']['verified_snapshot']
    require(exclusive_gate(admitted,gpu_uuid=L['gpu_uuid'],phase='idle',now=admitted['observed_unix'])['observation_passed'],'Idle hardware mode admission missing')
    require(guard['status']=='HISTORY104_HOST_GUARDIAN_TERMINAL' and guard['container_exit_code']==0 and not guard.get('error_type'),'Host guardian failure')
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
    return dict(status='HISTORY104_COMPLETE_ORIGINALS_FINANCE_AND_SELECTION_ACCEPTED',full_protocol_accepted=True,
        source_revision=L['source_revision'],launch_id=L['launch_id'],actual_GPUh=actual,scope_counts=COUNTS,
        exclusive_monitoring=exclusive,scientific= science,PG_P2_input_ready=False,timing_model_validated=science['timing']['timing_model_validated'],
        mode_restoration_pending=not restore['restored'],heldout_quality_or_speed_claim=False,GPU_submissions=0,ledger_written=False)
