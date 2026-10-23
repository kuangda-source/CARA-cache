"""Five original quality models for P2; no model/GPU construction at import.

The caller owns accepted model CPU evidence and the final whole-card admission.
Each physical video is scored once per dimension; role aliases remain explicit.
"""
import copy
import time
from pathlib import Path

from .continuation_preparation import require
from .p2_combination import DIMENSIONS, digest, validate_manifest, audit_quality
from .production_evidence import verify_artifact
from ..automatic_quality_r1 import sampling_spec, text_sha
from ..automatic_quality_batch_r1 import validate_result, JsonlSink
from ..automatic_quality_models_r1 import OriginalMetricFactory, WEIGHTS, ROLES
from ..automatic_quality_terminal_r1 import decoder_evidence


def evaluator_identity(registration, acceptance, resources, registration_sha256):
    require(acceptance['CPU_accepted'] is True and acceptance['accepted_models'] == 5,
            'Complete independent five-model CPU acceptance required')
    require(acceptance['registration_sha256'] == registration_sha256,
            'Original registration file SHA required')
    require(set(resources) == set(ROLES), 'All five original checkpoints required')
    for role, (size, sha) in WEIGHTS.items():
        require((resources[role]['bytes'], resources[role]['sha256']) == (size, sha),
                'No checkpoint substitution')
    return dict(vbench_commit=registration['official_VBench_commit'],
                model_CPU_registration_sha256=acceptance['registration_sha256'],
                constructor_sources=registration['payload_sha256'],
                metric_stage=registration['stage'],
                weights={r: dict(bytes=resources[r]['bytes'], sha256=resources[r]['sha256']) for r in ROLES},
                dimensions=list(DIMENSIONS), precision='FP32',
                dynamic_degree_descriptive=True, weighted_total=None)


def build_plan(manifest, state, members, identity, output_root):
    slots=validate_manifest(manifest)
    require(state['manifest_sha256']==manifest['sha256'] and
            state['status']=='COMPLETE_ORIGINALS_REQUIRE_INDEPENDENT_AUDIT',
            'Complete original generation state required before scoring')
    require(len(state['rows'])==len(slots), 'Full original generation denominator required')
    rows=[]
    for slot, original in zip(slots,state['rows']):
        require(original['slot']==slot and original['status']=='COMPLETE', 'Changed/failed original slot')
        if slot['block']!='new_dev':continue
        member=members[slot['member']]
        require(text_sha(member['prompt'])==member['prompt_sha256'], 'Original prompt changed')
        result=original['result'];video=result['video_artifact']
        verify_artifact(video,output_root)
        request=verify_artifact(result['request_artifact'],output_root)
        import json
        saved=json.loads(request.read_text())
        require(saved['slot']==slot and saved['result']=={k:v for k,v in result.items() if k!='request_artifact'},
                'Original request does not bind the video')
        for dimension in DIMENSIONS:
            rows.append(dict(case_id=slot['member']+':seed'+str(slot['seed']),method=slot['id'],
                physical_path_id=slot['id'],roles=list(slot['roles']),seed=slot['seed'],
                prompt_id=member['prompt_id'],prompt=member['prompt'],prompt_sha256=member['prompt_sha256'],
                dimension=dimension,input_status='READY_TO_SCORE',video_path=video['path'],
                video_sha256=video['sha256'],request_sha256=result['request_artifact']['sha256'],
                scorer_fingerprint=digest(identity),expected_sampling=sampling_spec(dimension)))
    require(len(rows)==5*manifest['block_counts']['new_dev'], 'All five dimensions on every physical new DEV')
    plan=dict(manifest_sha256=manifest['sha256'],evaluator_identity=identity,rows=rows,
              physical_quality_positions=len(rows),role_quality_positions=sum(len(r['roles']) for r in rows))
    plan['sha256']=digest(plan)
    return plan


def execute(plan, factory, journal_path, *, clock=time.monotonic):
    require(plan['sha256']==digest({k:v for k,v in plan.items() if k!='sha256'}),'Quality plan changed')
    rows=[dict(planned=copy.deepcopy(p),status='NOT_REACHED',result=None) for p in plan['rows']]
    sink=JsonlSink(journal_path);state=dict(plan_sha256=plan['sha256'],rows=rows,status='RUNNING',model_lifecycle=[])
    try:
        sink(dict(kind='SCOPE',state=copy.deepcopy(state)))
        for dimension in DIMENSIONS:
            life=dict(dimension=dimension,status='ENTERING',started=clock());state['model_lifecycle'].append(life)
            sink(dict(kind='MODEL_ENTER',lifecycle=copy.deepcopy(life)))
            try:
                with factory(dimension) as scorer:
                    require(scorer.dimension==dimension and scorer.scorer_fingerprint==digest(plan['evaluator_identity']),
                            'Wrong original model scorer')
                    for index,row in enumerate(rows):
                        p=row['planned']
                        if p['dimension']!=dimension:continue
                        row['status']='RUNNING';sink(dict(kind='ROW_START',index=index))
                        raw=scorer.score(copy.deepcopy(p))
                        # Keep raw failure evidence before validation can reject it.
                        row['result']=copy.deepcopy(raw);sink(dict(kind='RAW_RESULT',index=index,result=raw))
                        validate_result(p,raw);validate_sources_and_decoder(plan['evaluator_identity'],raw);row['status']='SCORED'
                        sink(dict(kind='ROW_ACCEPTED',index=index))
                life.update(status='RELEASED',ended=clock())
                sink(dict(kind='MODEL_RELEASE',lifecycle=copy.deepcopy(life)))
            except BaseException as error:
                life.update(status='FAILED',error_type=type(error).__name__,error=str(error),ended=clock())
                raise
        audit_quality(plan['rows'],[r['result'] for r in rows])
        state['status']='COMPLETE_REQUIRE_INDEPENDENT_AUDIT'
        return state
    except BaseException:
        state['status']='FAILED_ALL_ORIGINAL_POSITIONS_RETAINED'
        raise
    finally:
        try:sink(dict(kind='TERMINAL',state=state))
        finally:sink.close()


def original_factory(*, stage, resources, acceptance, registration, identity, torch, device):
    """Real shared constructor; never a test/fallback scorer."""
    return OriginalMetricFactory(stage=stage,resources=resources,CPU_acceptance=acceptance,
        CPU_registration=registration,scorer_fingerprint=digest(identity),torch=torch,device=device)


def audit(plan, state):
    require(plan['sha256']==digest({k:v for k,v in plan.items() if k!='sha256'}),'Changed plan')
    require(state['status']=='COMPLETE_REQUIRE_INDEPENDENT_AUDIT' and state['plan_sha256']==plan['sha256'],
            'Incomplete quality terminal')
    require(len(state['rows'])==len(plan['rows']),'Missing score positions')
    for p,r in zip(plan['rows'],state['rows']):
        require(r['planned']==p and r['status']=='SCORED','Role/prompt/video position changed')
        validate_sources_and_decoder(plan['evaluator_identity'],r['result'])
    require([r['dimension'] for r in state['model_lifecycle']]==list(DIMENSIONS) and
            all(r['status']=='RELEASED' for r in state['model_lifecycle']),'Every original model must release')
    return audit_quality(plan['rows'],[r['result'] for r in state['rows']])


def validate_sources_and_decoder(identity, result):
    expected={str(Path(identity['metric_stage'])/n):h for n,h in identity['constructor_sources'].items()}
    require(result['metric_source_sha256'] and all(expected.get(p)==h for p,h in result['metric_source_sha256'].items()),
            'Actual metric/helper source differs from accepted payload')
    decoder_evidence(result)
