"""P2 registered-card composition primitives, independent of budget/dispatch.

The final manifest must be constructed after accepted P1 and policy dedup.
CPU checks use an explicitly synthetic maximum-scope manifest. No fixture is
eligible for real admission (p2_combination_stage.validate remains closed).
"""
import copy
import hashlib
import json
import math
from pathlib import Path
from .continuation_preparation import require,TIME_BOUNDARY
from .production_evidence import artifact,verify_artifact,score_videos,validate_score
from ..gpu_budget_pool_v2 import atomic_json
from ..automatic_quality_batch_r1 import validate_result

DIMENSIONS=('subject_consistency','motion_smoothness','overall_consistency','dynamic_degree','MUSIQ_LONGER512')
BLOCK_MAX={'timing':84,'history':6,'simple_cal':64,'fixed_cal':24,'new_dev':320,'new_warm':20}

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def validate_manifest(m):
    require(m['sha256']==digest({k:v for k,v in m.items() if k!='sha256'}),'Frozen P2 manifest changed')
    rows=m['rows'];ids=[r['id'] for r in rows]
    require(len(set(ids))==len(ids)>0 and len(rows)<=518,'Original whole-card physical denominator')
    require(set(m['block_counts'])==set(BLOCK_MAX),'All P2 blocks must remain explicit')
    for block,upper in BLOCK_MAX.items():
        require(sum(r['block']==block for r in rows)==m['block_counts'][block] and 0<m['block_counts'][block]<=upper,'Missing full P2 block')
    seen={}
    for r in rows:
        require(Path(r['id']).name==r['id'] and r['id'] not in ('.','..'),'Unsafe slot')
        require(r['roles'] and len(set(r['roles']))==len(r['roles']) and type(r['seed']) is int,'Role aliases and seed required')
        require(type(r['expected_updates']) is int and 19<=r['expected_updates']<=36,'Pinned actual solver count required')
        require(r['quality_dimensions']==(list(DIMENSIONS) if r['block']=='new_dev' else []),'Quality denominator changed')
        ref=r['reference_id']
        if r['lpips']:
            require(ref in seen and all(seen[ref][k]==r[k] for k in ('member','seed')),'Original preceding paired reference required')
        require(not(r['block'] in ('timing','history','new_warm') and r['lpips']),'Diagnostic/time/warm score leakage')
        require(r['block']=='history' or not r.get('shadow_D_pairs',0),'Shadow cost outside history')
        seen[r['id']]=r
    require(sum(bool(r['lpips']) for r in rows)<=346,'LPIPS scope exceeded')
    require(sum(r.get('shadow_D_pairs',0) for r in rows)<=36,'Shadow scope exceeded')
    return rows

class Scores:
    """Score already serialized Requests output. Never owns a GPU or replay."""
    def __init__(self,root,metric,identity):self.root=Path(root);self.metric=metric;self.identity=identity
    def __call__(self,slot,result,reference):
        if not slot['lpips']:return {}
        require(result['status']==reference['status']=='COMPLETE','Complete paired outputs required')
        path=self.root/slot['id']/'score.json';require(not path.exists(),'Never replace original score')
        score=score_videos(reference['video_artifact'],result['video_artifact'],self.metric,root=self.root,metric_identity=self.identity)
        value=validate_score(score,reference['video_artifact'],result['video_artifact'],self.identity)
        atomic_json(path,score)
        return dict(LPIPS=value,score_artifact=artifact(path,self.root))

def run_registered(m,execute,score,save):
    """Durable complete denominator before execution; no implicit retry."""
    slots=validate_manifest(m);state=dict(manifest_sha256=m['sha256'],status='RUNNING',rows=[dict(slot=s,status='NOT_REACHED') for s in copy.deepcopy(slots)])
    save(copy.deepcopy(state));done={}
    try:
        for row in state['rows']:
            slot=copy.deepcopy(row['slot']);row['status']='RUNNING';save(copy.deepcopy(state))
            result=execute(copy.deepcopy(slot));row['result']=copy.deepcopy(result);save(copy.deepcopy(state))
            require(result['status']=='COMPLETE','Refused/failed original path retained')
            require(result['solver_steps']==result['guided_pairs']==slot['expected_updates'],'Full actual solver denominator')
            if slot['block']=='history':
                require(result['full_request_seconds'] is None and result['clean_deployment_timing'] is False and result['shadow_D_pairs']==slot['shadow_D_pairs'],'Shadow timing contamination')
            else:
                require(result['timing_boundary']==TIME_BOUNDARY and math.isfinite(result['full_request_seconds']) and result['full_request_seconds']>0,'Invalid complete request clock')
            scored=score(copy.deepcopy(slot),copy.deepcopy(result),copy.deepcopy(done.get(slot['reference_id'])))
            require(set(scored)<= {'LPIPS','score_artifact'} and bool(scored)==slot['lpips'],'Unexpected quality or missing score')
            row['score']=scored;row['status']='COMPLETE';done[slot['id']]=result;save(copy.deepcopy(state))
        state['status']='COMPLETE_ORIGINALS_REQUIRE_INDEPENDENT_AUDIT';return state
    except BaseException as e:
        row.update(status='TECH_FAILED',error_type=type(e).__name__,error=str(e));state['status']='FAILED_FULL_DENOMINATOR_RETAINED';raise
    finally:save(copy.deepcopy(state))

def audit_registered(m,state,request_records,score_records,metric_identity,artifact_check,history_audit=None):
    """Replay original request/scoring evidence, not trusted aggregate scalars."""
    slots=validate_manifest(m)
    require(state['manifest_sha256']==m['sha256'] and state['status']=='COMPLETE_ORIGINALS_REQUIRE_INDEPENDENT_AUDIT','Incomplete P2 original state')
    require(len(state['rows'])==len(slots) and set(request_records)=={s['id'] for s in slots},'Missing/extra original request')
    require(set(score_records)=={s['id'] for s in slots if s['lpips']},'Missing/extra original score')
    done={}
    for slot,row in zip(slots,state['rows']):
        require(row['slot']==slot and row['status']=='COMPLETE','Changed slot/alias or failure erased')
        req=request_records[slot['id']];result=row['result']
        require(req['slot']==slot and req['result']=={k:v for k,v in result.items() if k!='request_artifact'},'Original request bytes differ')
        for key in ('video_artifact','final_latent_artifact','request_artifact'):artifact_check(result[key])
        require(result['status']=='COMPLETE' and result['guided_pairs']==result['solver_steps']==slot['expected_updates'],'Partial path accepted')
        if slot['block']=='history':
            require(result['full_request_seconds'] is None and result['clean_deployment_timing'] is False and result['shadow_D_pairs']==slot['shadow_D_pairs'],'History entered clean timing')
            require(history_audit is not None,'Bound original branch and accepted P1 OFF auditor required')
            checked=history_audit(copy.deepcopy(slot),copy.deepcopy(result))
            require(checked['raw_branch_records_accepted'] is True and checked['P1_OFF_reference_parity'] is True,'Raw history/OFF audit missing')
        else:require(result['timing_boundary']==TIME_BOUNDARY and math.isfinite(result['full_request_seconds']) and result['full_request_seconds']>0,'Invalid clean clock')
        if slot['lpips']:
            score=score_records[slot['id']];value=validate_score(score,done[slot['reference_id']]['video_artifact'],result['video_artifact'],metric_identity)
            artifact_check(row['score']['score_artifact']);require(row['score']['LPIPS']==value,'Scalar differs from all93 original frames')
        else:require(not row['score'],'Unregistered quality consumed')
        done[slot['id']]=result
    return dict(physical_paths=len(slots),LPIPS_pairs=len(score_records),shadow_D_pairs=sum(s.get('shadow_D_pairs',0) for s in slots),roles_preserved=True)

def audit_quality(planned,results):
    require(len(planned)==len(results) and len({(r['case_id'],r['method'],r['dimension']) for r in planned})==len(planned),'Quality denominator changed')
    counts={}
    for p,r in zip(planned,results):
        require(p['dimension'] in DIMENSIONS,'Unregistered quality dimension')
        if p['input_status']=='NOT_APPLICABLE_PRE_REGISTERED':
            require(p.get('NA_reason') and r==dict(case_id=p['case_id'],method=p['method'],dimension=p['dimension'],status='NOT_APPLICABLE_PRE_REGISTERED',value=None,NA_reason=p['NA_reason']),'NA reason/value changed')
        else:
            require(p['input_status']=='READY_TO_SCORE','Missing video/resource cannot become NA')
            validate_result(p,r)
        counts[r['status']]=counts.get(r['status'],0)+1
    return dict(positions=len(planned),status_counts=counts,weighted_quality_total=None,frames_as_independent_samples=False)
