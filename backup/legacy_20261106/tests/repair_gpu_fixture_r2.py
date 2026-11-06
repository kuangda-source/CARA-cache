"""Full180 synthetic receipts; no real task, frame, quality or GPU observation."""
import copy
import hashlib
import importlib.util
from pathlib import Path
from types import SimpleNamespace

from wcomr import frozen_repair180_r2 as repair
from wcomr.gpu_budget_pool_v2 import BudgetPool,SCHEMA
from wcomr.frozen_shared_post_r1 import GPU_TERMINAL_STATUS


def load(name):
    p=Path(__file__).with_name(name+'.py');s=importlib.util.spec_from_file_location('synthetic_repair_'+name,p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def fixture():
    cpu=load('test_frozen_repair_cpu_acceptance_r2');config,bound,registration,proof=cpu.fixture()
    post=load('test_frozen_shared_post_r1');batch=load('test_frozen_shared_batch_r1')
    plan=repair.validate_contract(config,bound);root='/SYNTHETIC_PROJECT/outputs/'+repair.RUN;runs=[]
    for planned in plan:
        case=next(c for c in bound['cases'] if c['id']==planned['case_id'])
        sample=SimpleNamespace(values=dict(name=case['id'],seed=case['seed'],
            num_steps=batch.point(planned['method'])['requested_steps']))
        row={**planned,**batch.fake_result(planned,sample)}
        digest=hashlib.sha256((planned['case_id']+planned['method']).encode()).hexdigest()
        row.update(final_latent_sha256=digest,A_history=[],synthetic_RGB_digest=digest,
            video_path=root+'/'+row['id']+'/video.mp4',
            final_artifact=dict(path=root+'/'+row['id']+'/final.pt',sha256=digest,bytes=1))
        if row['section']=='WARMUP':
            row.update(warm_guided_artifact=dict(path=root+'/'+row['id']+'/guided.pt',sha256='1'*64,bytes=1),
                       warm_guided_tree_sha256='2'*64)
        runs.append(row)
    final=post.evaluate(bound,plan,runs)
    final['artifact_inventory']=[dict(path=a['path'],bytes=a['bytes'],sha256=a['sha256'])
        for row in final['rows'] for key in ('final_artifact','warm_guided_artifact','video_artifact')
        if (a:=row.get(key)) is not None]
    own=dict(pid=1101,start_ticks=11010);child=dict(pid=1103,start_ticks=11030);watch=dict(pid=1102,start_ticks=11020)
    authority=dict(source_revision=registration['source_revision'],config_sha256=proof['config_sha256'],
        production_CPU_sha256='5'*64,bound_input_fingerprint=repair.fingerprint(bound),scope_counts=config['scope_counts'],
        whole_card_run=repair.RUN,gpu_uuid='GPU-SYNTHETIC-REPAIR',forecast_complete_GPUh=config['forecast_complete_GPUh'],
        billed_limit_GPUh=config['billed_limit_GPUh'],cumulative_cap_GPUh=config['cumulative_cap_GPUh'],
        budget_origin_used_GPUh=config['budget_origin_used_GPUh'],kind='SPECIFIC_WHOLE_CARD_APPROVAL',
        direct_user_authorization=True,user_reply_quote='SYNTHETIC CONTROL ONLY, NO HUMAN GPU APPROVAL',launch_id='SYNTHETIC_NO_GPU')
    start=100.;delay=config['first_collection_delay_seconds']
    launch=dict(run_id=repair.RUN,source_revision=registration['source_revision'],launch_id=authority['launch_id'],
        gpu_uuid=authority['gpu_uuid'],scope_counts=config['scope_counts'],config_sha256=proof['config_sha256'],
        registration_sha256='a'*64,production_CPU_sha256='5'*64,authorization_sha256='8'*64,
        bound_input_fingerprint=repair.fingerprint(bound),supervisor_pid=own['pid'],supervisor_identity=own,
        post_watcher_pid=watch['pid'],post_watcher_identity=watch,started_unix=start,
        midpoint_check_not_before_unix=start+delay/2,next_check_not_before_unix=start+delay,
        stage='/SYNTHETIC_PROJECT/.sync/stage',project='/SYNTHETIC_PROJECT')
    supervisor=dict(status=GPU_TERMINAL_STATUS,pid=own['pid'],start_ticks=own['start_ticks'],
        child_identity=child,child_pid=child['pid'],child_exit_code=0,billing_sha256='9'*64,actual_GPUh=1.,runner_sha256='b'*64,
        **{k:launch[k] for k in ('source_revision','launch_id','run_id','gpu_uuid','scope_counts','config_sha256',
            'bound_input_fingerprint','registration_sha256')})
    bill=dict(status='N07_SHARED180_ACTUAL_GPU_BILL',original_output_root_available=True,actual_GPUh=1.,wall_seconds=3600.,
        billed_limit_GPUh=config['billed_limit_GPUh'],**{k:launch[k] for k in ('source_revision','launch_id','run_id','gpu_uuid','scope_counts','config_sha256')})
    job=dict(status='SETTLED',kind='V2_SPECIFIC_WHOLE_CARD_APPROVAL',authorization_sha256=launch['authorization_sha256'],
        actual_GPUh=1.,billing_sha256='9'*64,forecast_GPUh=config['forecast_complete_GPUh'],billed_limit_GPUh=config['billed_limit_GPUh'],
        **{k:launch[k] for k in ('source_revision','launch_id','gpu_uuid','config_sha256','scope_counts',
            'production_CPU_sha256','bound_input_fingerprint')})
    pool=dict(schema=SCHEMA,cap_gpu_hours=config['cumulative_cap_GPUh'],origin_used_gpu_hours=config['budget_origin_used_GPUh'],
        origin_gpu_jobs_launched=100,jobs={repair.RUN:job},events=[]);pool.update(BudgetPool.accounting(pool))
    final.update(source_revision=launch['source_revision'],config_sha256=launch['config_sha256'],
        bound_input_fingerprint=launch['bound_input_fingerprint'],scope_counts=config['scope_counts'],
        GPU_supervisor=copy.deepcopy(supervisor),CUDA_initialized=False)
    runner=dict(runs=runs,source_revision=launch['source_revision'],config_sha256=launch['config_sha256'],
        bound_input_fingerprint=launch['bound_input_fingerprint'],scope_counts=config['scope_counts'],
        cases=bound['cases'],methods=bound['method_ids'],matrix=plan,model_load_calls=1,model_loads_completed=1)
    value=dict(status='N07_SHARED180_ORIGINAL_ONCE_CAPTURE',mode='terminal',observed_unix=launch['next_check_not_before_unix']+100,
        launch=launch,registration=registration,registration_sha256=launch['registration_sha256'],
        payload_verified={n:True for n in registration['payload_sha256']},config=config,config_sha256=launch['config_sha256'],
        bound_inputs=bound,bound_inputs_sha256=config['references']['bound_inputs']['sha256'],
        production_CPU=proof,production_CPU_sha256=launch['production_CPU_sha256'],
        production_CPU_bundle=cpu.bundle_fixture(registration),authorization=authority,authorization_sha256='8'*64,
        supervisor=supervisor,runner=runner,runner_sha256='b'*64,
        original_processes={k:dict(pid=p['pid'],start_ticks=None,state=None) for k,p in
            (('supervisor_pid',own),('child_pid',child),('post_watcher_pid',watch))},
        billing=bill,billing_sha256='9'*64,pool=pool,own_UUID_lock_free=True,own_GPU=launch['gpu_uuid']+', NVIDIA RTX A6000, 24',
        compute_apps='',output_root=root,post_exit=dict(status='N07_SHARED180_POST_CPU_TERMINAL',exit_code=0,
            original_supervisor=own,source_revision=launch['source_revision'],config_sha256=launch['config_sha256'],final_result_sha256='c'*64),
        final=final,final_sha256='c'*64)
    return value,launch
