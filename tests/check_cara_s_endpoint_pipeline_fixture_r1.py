"""CPU pipeline packet setup; historical media comes from actual tiny routes."""
import copy
import json
from pathlib import Path

from wcomr import cara_s_endpoint_artifacts_r1 as artifacts
from wcomr import cara_s_endpoint_release_r1 as release
from wcomr.cara_fast_binding_r2 import load_card
from wcomr.cara_fast_scoring_manifest_r2 import comparison_input_digest
from wcomr.cara_fast_spec_r1 import digest
from wcomr.cara_s_uniform_endpoint_binding_r1 import map_physical_slots
from wcomr.cara_s_uniform_endpoint_execution_r1 import request_card
from wcomr.gpu_budget_pool_v2 import BudgetPool,SCHEMA,sha
from wcomr.policy_price_terminal_r1 import record
from test_cara_s_endpoint_release_r1 import endpoint_fixture
from test_cara_budget_lifecycle_r1 import put

ROOT=Path(__file__).resolve().parents[1]
PROPOSAL='plans/cara_next_stage_20261028/mainline/r2/S_UNIFORM_BUDGET_ENDPOINT32_PROPOSAL_R1_20261031.json'
SCORES='reports/cara_fast_B36_complete_scores_accepted_r1_20261029.json'


def historical_slot(base,member,role):
    section='A_ANCHOR' if role=='NATIVE35' and member in base['FIT'] else 'B_QUALITY'
    return next(s for s in base['physical_matrix'] if s['section']==section and s['member']==member and s['role']==role)


def packet(project,write_media,decode,*,alias=False,shape=(93,64,64,3),flow=True):
    project=Path(project);project.mkdir(parents=True,exist_ok=True)
    proposal=json.loads((ROOT/PROPOSAL).read_text())
    original=json.loads((ROOT/SCORES).read_text())
    base=load_card(ROOT,'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json')
    for item in base['inputs']:item['resolution']='16,16'
    base['roles']['ALLD']['settings']['worldcache_flow_enabled']=flow
    base['scope_sha256']=digest({k:v for k,v in base.items() if k!='scope_sha256'})
    proposal.update(inputs=copy.deepcopy(base['inputs']),parent_B36_scope_sha256=base['scope_sha256'],
                    shared_execution_settings=copy.deepcopy(base['roles']['ALLD']['settings']))
    original['scope_sha256']=base['scope_sha256']
    requests={r['name']:r for r in base['inputs']}
    precision=dict(CPU_synthetic_precision=True)
    proposal['precision_sha256']=digest(precision)
    known={}

    def media(path,member,role):
        path.parent.mkdir(parents=True,exist_ok=True);write_media(path,member+'|'+role)
        descriptor=dict(path=str(path),bytes=path.stat().st_size,sha256=sha(path))
        args=json.loads(path.with_suffix('.json').read_text())
        return descriptor,args

    for row in original['rows']:
        if row['role'] not in ('NATIVE35','F19_C','UNIFORM19_C','F19_A1'):continue
        member,role=row['member'],row['role']
        video,args=media(project/'CPU-historical'/role/member/(member+'.mp4'),member,role)
        descriptor=copy.deepcopy(row['candidate'])
        descriptor.update(video,scope_sha256=base['scope_sha256'],precision=digest(precision),execution_request_sha256=digest(args),
            registered_request_sha256=digest(args),comparison_input_sha256=comparison_input_digest(args),
            argument_file_sha256=sha(Path(video['path']).with_suffix('.json')))
        rgb=decode(video,shape=shape)['RGB_sha256']
        known[(member,role)]=(descriptor,rgb)
        row['candidate']=descriptor;row['CPU_synthetic_identity_fixture']=True
    for row in original['rows']:
        key=(row['member'],row['role'])
        if key not in known:continue
        native,native_rgb=known[(row['member'],'NATIVE35')]
        row.update(reference=copy.deepcopy(native),decoded_RGB_sha256=[known[key][1],native_rgb])
    old={r['id']:r for r in original['rows']}
    for reference in proposal['reference_sources']:
        row=old[reference['score_id']]
        reference.update(source=copy.deepcopy(row['candidate']),score_row_sha256=digest(row),decoded_RGB_sha256=row['decoded_RGB_sha256'][0])
    for item in proposal['formal_matrix']:
        item['reference']=copy.deepcopy(known[(item['member'],'NATIVE35')][0])
        if item['mode']=='REUSE_COMPLETE_SCORE':
            row=old[item['score_id']]
            item.update(source=copy.deepcopy(row['candidate']),score_row_sha256=digest(row),decoded_RGB_sha256=row['decoded_RGB_sha256'][:])
    for control in proposal['identity_controls']:
        if control['kind']=='FRESH_VS_ORIGINAL_DECODED_RGB':
            control['original_decoded_RGB_sha256']=known[(control['member'],control['role'])][1]
    proposal['CPU_fixture_only']=True
    proposal['scope_sha256']=digest({k:v for k,v in proposal.items() if k!='scope_sha256'})
    capture,_,job,_,old_bound=endpoint_fixture(alias)
    bound=map_physical_slots(proposal,old_bound['budget_policy'])
    bound.update(CPU_fixture_only=True,proposal_scope_sha256=proposal['scope_sha256'],
        original_freeze_sha256=old_bound['original_freeze_sha256'],original_calibration=old_bound['original_calibration'])
    bound['binding_sha256']=digest(bound)
    card=request_card(proposal,bound,base)
    stage=project/'.sync/cara-S-endpoint-CPU-fixture-chain';stage.mkdir(parents=True)
    for key in ('launch','authorization','billing','guardian','pending_release'):
        value=record(capture,key);value.update(stage=str(stage),scope_sha256=card['scope_sha256']);put(capture,key,value)
    put(capture,'endpoint_card',card);put(capture,'endpoint_binding',bound)
    put(capture,'endpoint_proposal',proposal);put(capture,'original_scores',original);put(capture,'precision',precision)
    reg=record(capture,'registration');reg['stage']=str(stage)
    reg['payload_sha256'].update({artifacts.SOURCE:sha(artifacts.__file__),
        artifacts.MANIFEST_SOURCE:sha(ROOT/artifacts.MANIFEST_SOURCE),
        release.CARD:capture['files']['endpoint_card']['sha256'],release.BINDING:capture['files']['endpoint_binding']['sha256'],
        artifacts.PROPOSAL:capture['files']['endpoint_proposal']['sha256'],
        artifacts.ORIGINAL_SCORES:capture['files']['original_scores']['sha256']})
    capture['payload_actual_sha256']=copy.deepcopy(reg['payload_sha256'])
    reg_sha=put(capture,'registration',reg)
    authority=record(capture,'authorization');authority['endpoint_binding_sha256']=bound['binding_sha256']
    auth_sha=put(capture,'authorization',authority)
    job.update(stage=str(stage),scope_sha256=card['scope_sha256'],registration_sha256=reg_sha,authorization_sha256=auth_sha)
    central_sha=put(capture,'central_reservation',dict(central_ledger_host='four_card',job=job))
    launch=record(capture,'launch');launch.update(registration_sha256=reg_sha,authorization_sha256=auth_sha,
        central_reservation_sha256=central_sha,endpoint_binding_sha256=bound['binding_sha256'],
        container=stage.name+'-gpu',model_sha256=proposal['model_sha256'])
    expected=put(capture,'launch',launch)
    capture['container'].update(name=launch['container'],manifest_sha256=reg_sha)
    guardian=record(capture,'guardian');guardian['container_terminal_witness']['container']=copy.deepcopy(capture['container'])
    guardian['billing_sha256']=capture['files']['billing']['sha256'];put(capture,'guardian',guardian)
    capture['files'].pop('collection');capture['files'].pop('runner_terminal')
    pool=BudgetPool(project/'CPU-ledger');pool.path.parent.mkdir(parents=True)
    before=dict(schema=SCHEMA,cap_gpu_hours=226.,origin_used_gpu_hours=50.,origin_gpu_jobs_launched=10,
        jobs={'old-unknown-16.5':dict(status='RESERVED_OR_RUNNING',gpu_uuid='GPU-OLD',billed_limit_GPUh=16.5),job['job_id']:job},events=[])
    before.update(pool.accounting(before));pool.path.write_text(json.dumps(before))
    return dict(capture=capture,expected_launch_sha256=expected,proposal=proposal,card=card,bound=bound,
                CPU_pool=pool,CPU_job=job,CPU_base=base,cpu_validation=True,cpu_shape=shape)
