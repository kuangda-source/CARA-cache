"""Synthetic complete32/25 packets, actual files and a temporary ledger only."""
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


def packet(project,write_media,decode,*,alias=False,shape=(93,16,16,3)):
    project=Path(project);project.mkdir(parents=True,exist_ok=True)
    proposal=json.loads((ROOT/PROPOSAL).read_text())
    original=json.loads((ROOT/SCORES).read_text())
    base=load_card(ROOT,'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json')
    requests={r['name']:r for r in base['inputs']}
    precision=dict(CPU_synthetic_precision=True)
    proposal['precision_sha256']=digest(precision)
    known={}

    def media(path,member,role):
        path.parent.mkdir(parents=True,exist_ok=True);write_media(path,member+'|'+role)
        descriptor=dict(path=str(path),bytes=path.stat().st_size,sha256=sha(path))
        args={k:v for k,v in requests[member].items() if k!='partition'}
        args.update(seed=0,num_steps=35)
        path.with_suffix('.json').write_text(json.dumps(args,indent=2)+'\n')
        return descriptor,args

    for row in original['rows']:
        if row['role'] not in ('NATIVE35','F19_C','UNIFORM19_C','F19_A1'):continue
        member,role=row['member'],row['role']
        video,args=media(project/'CPU-historical'/member/(role+'.mp4'),member,role)
        descriptor=copy.deepcopy(row['candidate'])
        descriptor.update(video,precision=digest(precision),execution_request_sha256=digest(args),
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
    stage=project/'.sync/cara-S-endpoint-GPU-CPU';stage.mkdir(parents=True)
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
    output=project/'outputs'/launch['run_id']/'B';rows=[]
    for slot in card['physical_matrix']:
        role=slot['role'];tag_role='NATIVE35' if role=='ALLD' else role
        video,args=media(output/slot['id']/(slot['member']+'.mp4'),slot['member'],tag_role)
        tensor=output/(slot['id']+'.pt');tensor.write_bytes(b'CPU-METADATA-FIXTURE-NOT-TORCH')
        result=dict(status='COMPLETE',slot_id=slot['id'],role=role,concrete_role=role,scope_sha256=card['scope_sha256'],
            CPU_fixture=True,solver_steps=36,guided_pairs=36,audit_enabled=False,in_timing_guided_copies=0,
            in_timing_hashes=0,research_checkpoints=0,T_DD=.5,T_request=1.,endpoint_video_artifact=video,video_path=video['path'])
        if 'policy' in card['roles'][role]:
            result['semantic_history']=[dict(actual=a,fallback_reason=None) for a in card['roles'][role]['policy']['actions']]
        rows.append(dict(slot=slot,status='COMPLETE',result=result,
            tensor_artifact=dict(path=str(tensor),bytes=tensor.stat().st_size,sha256=sha(tensor))))
    collection=dict(phase='B',status='TERMINAL',scope_sha256=card['scope_sha256'],rows=rows)
    put(capture,'collection',collection);put(capture,'runner_terminal',dict(scope_sha256=card['scope_sha256'],collection_sha256=digest(collection)))
    pool=BudgetPool(project/'CPU-ledger');pool.path.parent.mkdir(parents=True)
    before=dict(schema=SCHEMA,cap_gpu_hours=226.,origin_used_gpu_hours=50.,origin_gpu_jobs_launched=10,
        jobs={'old-unknown-16.5':dict(status='RESERVED_OR_RUNNING',gpu_uuid='GPU-OLD',billed_limit_GPUh=16.5),job['job_id']:job},events=[])
    before.update(pool.accounting(before));pool.path.write_text(json.dumps(before))
    after=pool.settle(job['job_id'],.05,capture['files']['billing']['sha256'])
    settlement=dict(central_ledger_host='four_card',launch_id=launch['launch_id'],billing_sha256=capture['files']['billing']['sha256'],
        central_before=before,central_after=after)
    return dict(capture=capture,expected_launch_sha256=expected,settlement=settlement,
                proposal=proposal,card=card,bound=bound,cpu_validation=True,cpu_shape=shape)
