"""Independent full-price acceptance from original bytes, finance and monitoring."""
import hashlib
import json
import math
from .policy_price_refresh_contract_r1 import COUNTS,matrix
from .policy_asset_price_review_r1 import exclusive_gate

IMAGE='sha256:1e81ac62ee68ca1a6ef655515096a1d84579b01aa4986810c9b18d4f6c4c552d'
RUN='wc-policy-price-refresh-cal4-full1624-ada-r1'


def require(value,message):
    if not value:raise ValueError(message)


def record(v,key):
    r=v['files'][key]
    require(r.get('exists') is True,'Missing original file: '+key)
    raw=r['raw_utf8'].encode()
    require(len(raw)==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256'],'Changed captured bytes: '+key)
    return json.loads(raw)


def monitor(v,L,runner,wall_seconds):
    meta=record(v,'monitor_final');raw=v['monitor_raw_utf8']
    require(hashlib.sha256(raw.encode()).hexdigest()==meta['monitor_sha256'],'Monitoring journal SHA differs')
    rows=[json.loads(s) for s in raw.splitlines()]
    require(meta['accepted'] and len(rows)==meta['observations'] and rows,'Incomplete exclusive monitoring')
    grant=record(v,'grant');ready=record(v,'ready')
    require(grant['runner']==ready['identity']==meta['runner']==runner,'Original context identity differs')
    require(grant['gpu_uuid']==L['gpu_uuid'] and grant['source_revision']==L['source_revision'],'Context grant identity differs')
    active=False;last=0.
    for row in rows:
        s=row['snapshot'];elapsed=row['monotonic_elapsed']
        require(math.isfinite(elapsed) and elapsed>=last,'Reversed or invalid monitor journal')
        # A delayed/failed sample cannot silently certify continuous monitoring.
        require(elapsed-last<=45,'Exclusive monitoring gap exceeds preregistered 45-second ceiling')
        require(not active or row['context_granted'],'Context grant regressed')
        active=active or row['context_granted'];last=elapsed
        phase='active' if active or s['compute_apps'] else 'idle'
        verdict=exclusive_gate(s,gpu_uuid=L['gpu_uuid'],phase=phase,runner=runner,now=s['observed_unix'])
        require(verdict['observation_passed'],'Exclusive journal contains foreign/unknown context or wrong mode')
    require(active,'No actual runner context verified')
    require(0<=wall_seconds-last<=45,'Unmonitored terminal interval exceeds 45 seconds')
    final=meta['final_snapshot']
    require(exclusive_gate(final,gpu_uuid=L['gpu_uuid'],phase='idle',now=final['observed_unix'])['observation_passed'],
            'Original CUDA context was not released under exclusive mode')
    return dict(accepted=True,samples=len(rows),max_sampling_gap_seconds=max(
        rows[i]['monotonic_elapsed']-(rows[i-1]['monotonic_elapsed'] if i else 0) for i in range(len(rows))))


def accept(v,old_capture,old_accepted):
    L=v['launch'];c=record(v,'config');reg=record(v,'registration');auth=record(v,'authorization')
    quote=record(v,'quote')
    require(L['run_id']==RUN and L['scope_counts']==COUNTS,'Wrong full price identity or denominator')
    require(reg['source_revision']==L['source_revision'] and reg['stage']==L['stage'],'Wrong frozen execution source')
    require(v['files']['registration']['sha256']==L['registration_sha256'],'Registration SHA differs')
    require(v['payload_actual_sha256']==reg['payload_sha256'] and v['runtime_actual_sha256']==reg['runtime_source_sha256'],
            'Frozen stage or pinned runtime changed')
    require(v['files']['config']['sha256']==L['config_sha256'] and c['scope_counts']==COUNTS and c['matrix']==matrix(),
            'Price config changed')
    for key,name in [('config','price-refresh-config.json'),('quote','price-whole-quote.json')]:
        require(v['files'][key]['sha256']==reg['payload_sha256'][name],'Captured registered bytes differ: '+name)
    require(quote['scope_counts']==COUNTS and quote['matrix']==matrix()
            and c['forecast_complete_GPUh']==quote['forecast_complete_GPUh']==L['forecast_GPUh']
            and c['billed_limit_GPUh']==quote['billed_limit_GPUh']==L['billed_limit_GPUh']
            and 0<L['forecast_GPUh']<=L['billed_limit_GPUh']<12,'Whole-card quote differs')
    require(v['files']['authorization']['sha256']==L['authorization_sha256'],'Authorization bytes differ')
    for k in ('run_id','launch_id','source_revision','gpu_uuid','registration_sha256','config_sha256','scope_counts','billed_limit_GPUh'):
        require(auth[k]==L[k],'Authority/launch differs: '+k)
    cpu=record(v,'CPU_acceptance')
    require(cpu['production_CPU_accepted'] and cpu['full_GPU_lifecycle_CPU_accepted']
            and cpu['source_revision']==L['source_revision'] and cpu['registration_sha256']==L['registration_sha256']
            and v['files']['CPU_acceptance']['sha256']==auth['independent_CPU_acceptance_sha256'],
            'Complete bound new CPU acceptance required')
    require(not any(v['original_live_handles'].values()) and v['own_UUID_lock_free'] is True,'Original handle or UUID lock remains live')
    con=v['container'];state=con['state']
    require(not state['Running'] and state['ExitCode']==0 and not state['OOMKilled'] and con['image']==IMAGE
            and con['readonly_root'] and con['pid_mode']=='host' and con['manifest_sha256']==L['registration_sha256'],
            'Original manifest-bound container did not exit cleanly')
    requests=con['device_requests']
    require(len(requests)==1 and requests[0]['DeviceIDs']==[L['gpu_uuid']],'Container exposes a different device')
    guard=record(v,'guardian');sup=record(v,'supervisor');postexit=record(v,'post_exit')
    require(guard['container_exit_code']==0 and guard['status']=='PRICE_HOST_GUARDIAN_TERMINAL'
            and not guard.get('error_type') and guard['gpu_uuid']==L['gpu_uuid'],'Host guardian failed')
    require(all(guard['identity'][k]==L['guardian_identity'][k] for k in ('pid','start_ticks'))
            and guard['source_revision']==L['source_revision'],'Original guardian identity differs')
    admitted=guard['mode_admission']['verified_snapshot']
    require(exclusive_gate(admitted,gpu_uuid=L['gpu_uuid'],phase='idle',now=admitted['observed_unix'])['observation_passed'],
            'Actual idle hardware exclusivity was not verified')
    require(sup['child_exit_code']==0 and sup['post_exit_code']==0 and sup['exclusive_monitor_accepted']
            and not sup.get('error_type') and not sup.get('release_error'),'Original supervisor failed')
    require(all(sup[k]==L[k] for k in ('source_revision','run_id','launch_id','gpu_uuid','scope_counts')),
            'Original supervisor launch identity differs')
    require(postexit['exit_code']==0 and postexit['CPU_only_after_UUID_release'],'Independent post failed')
    bill=record(v,'billing');pool=v['pool'];job=pool['jobs'][RUN]
    for k in ('run_id','launch_id','source_revision','gpu_uuid','scope_counts','billed_limit_GPUh'):
        require(bill[k]==L[k],'Original bill identity differs: '+k)
    actual=bill['actual_GPUh']
    require(math.isfinite(actual) and 0<actual==bill['wall_seconds']/3600<=L['billed_limit_GPUh']<12,'Invalid whole-card actual cost')
    exclusive=monitor(v,L,sup['child_identity'],bill['wall_seconds'])
    require(job['status']=='SETTLED' and job['launch_id']==L['launch_id'] and job['actual_GPUh']==actual
            and job['billing_sha256']==v['files']['billing']['sha256'],'Original price bill not settled')
    from .gpu_budget_pool_v2 import BudgetPool
    require(pool['cap_gpu_hours']==226 and all(pool[k]==value for k,value in BudgetPool.accounting(pool).items()),
            'Authoritative cumulative finance inconsistent')
    runner=record(v,'runner');post=record(v,'post');bundle=record(v,'bundle')
    require(runner['source_revision']==L['source_revision'] and runner['config_sha256']==L['config_sha256']
            and runner['registration_sha256']==L['registration_sha256'] and runner['model_loads']==1
            and runner['scope_counts']==COUNTS and runner['pid']==sup['child_identity']['pid'],'Original runner differs')
    require(post['runner_sha256']==v['files']['runner']['sha256'] and postexit['final_result_sha256']==v['files']['post']['sha256'],
            'Independent post is not bound to final runner bytes')
    require(post['registered_paths']==10 and len(post['rows'])==10 and not post['error_rows']
            and post['raw_parity_accepted'] and post['clean_action_prices_accepted']
            and post['generator_input_bundle_sha256']==v['files']['bundle']['sha256'],'Post missing complete accepted scope')
    require(len(runner['runs'])==10 and len(v['artifact_checks'])==10,'All ten full raw paths required')
    for row,p,audited,raw in zip(runner['runs'],matrix(),post['rows'],v['artifact_checks']):
        require(all(row[k]==p[k] for k in p) and row['status']=='COMPLETE','Missing/changed original path')
        require(row['solver_steps']==row['guided_pairs']==36 and row['actions']==['DD']*36,'Original dense parent differs')
        require(row['request_memory_lifecycle']['owners_alive_after']==0,'Request owner not released')
        require(audited['id']==raw['id']==row['id'] and audited['accepted'] and audited['all36_and_final_equal']
                and audited['all93_RGB_equal'] and raw['all93_old_Native_equal'],'Raw reference parity failed')
        require(raw['guided_sha256']==row['guided_artifact']['sha256']
                and raw['final_latent_sha256']==row['final_latent_artifact']['sha256']
                and raw['RGB_frame_count']==93,'Raw artifact bytes changed after post')
    require(old_accepted['full_protocol_accepted'] and old_accepted['formal_source_time_cells']==1624,'Accepted old labels required')
    expected_old={'runner.json':old_capture['runner_sha256'],
        'post-results.json':old_capture['files']['post']['sha256'],
        'generator-input-bundle.json':old_capture['files']['bundle']['sha256']}
    require(c['accepted_original_files']==v['original_files_actual_sha256']==expected_old,'Old accepted reference changed')
    from .policy_price_refresh_audit_r1 import make_repriced_bundle
    recomputed=make_repriced_bundle(runner['runs'],old_capture['runner']['runs'],old_capture['files']['bundle']['data'],
        original_bundle_sha256=expected_old['generator-input-bundle.json'],prices_sha256=v['files']['runner']['sha256'],
        profile_identity=L['registration_sha256'],exclusive_accepted=True,parity_accepted=True)
    require(bundle==recomputed,'Replacement bundle differs from independent full-domain recomputation')
    restoration=guard['mode_restoration']
    require(restoration['restored'] or restoration['status']=='RESTORE_DEFERRED_NO_FOREIGN_PROCESS_TOUCHED',
            'Unknown post-run mode-restoration outcome')
    return dict(status='FULL_PRICE_ORIGINALS_EXCLUSIVITY_AND_FINANCE_ACCEPTED',full_protocol_accepted=True,
        clean_action_prices_accepted=True,generator_input_ready=True,source_revision=L['source_revision'],
        launch_id=L['launch_id'],scope_counts=COUNTS,actual_GPUh=actual,exclusive_monitoring=exclusive,
        original_label_bundle_sha256=expected_old['generator-input-bundle.json'],
        replacement_bundle_sha256=v['files']['bundle']['sha256'],
        mode_restoration_pending=not restoration['restored'],
        GPU_submissions=0,ledger_written=False,endpoint_quality_or_deployment_speed_result=False)
