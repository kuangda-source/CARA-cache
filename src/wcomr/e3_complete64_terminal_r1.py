"""Complete E3 inventory and fidelity reporting, including failed/unstarted slots.

No model import at module import time. Reused timings keep their original batch;
they are never presented as clean or same-card speed measurements.
"""
import copy
import math
from pathlib import Path
from statistics import mean

from .e3_complete64_block_scope_r1 import validate_scope, STRATEGIES, NAMES, METHODS
from .full64_partial_recovery_cpu import numerical_pairing, sha_file


def receipt_slots(slots):
    # Original rows remain in SHA-bound GPU receipts. Avoid duplicating each
    # multi-megabyte request/history across incremental CPU writes.
    return [{k:v for k,v in s.items() if k not in ('row','request_record','method_index')} for s in slots]


def inventory(scope, supervisor, receipts, reused):
    validate_scope(scope)
    if (supervisor['run_id'] != scope['run_id'] or len(supervisor['blocks']) != 20
            or [b['id'] for b in supervisor['blocks']] != [b['id'] for b in scope['blocks']]
            or set(receipts)-{b['id'] for b in scope['blocks']}):
        raise ValueError('Exact terminal full20 supervisor and full64 scope required')
    reuse_keys = {s['slot'] for s in scope['all64_slots'] if s['disposition']=='REUSE_QUALIFIED_DEV_OUTPUT'}
    if set(reused) != reuse_keys:
        raise ValueError('All ten immutable reuse bindings required, no replacement')
    found = {}; block_for = {}
    for block, lifecycle in zip(scope['blocks'], supervisor['blocks']):
        if lifecycle['planned_paths'] != len(block['paths']):
            raise ValueError('Supervisor block size changed')
        for p in block['paths']: block_for[p['slot']] = lifecycle
        receipt = receipts.get(block['id'])
        if receipt is None: continue
        if (receipt['block'] != block or receipt['run_id'] != scope['run_id']
                or receipt['planned_paths'] != len(block['paths'])
                or receipt['source_revision'] != supervisor['source_revision']
                or receipt['config_sha256'] != supervisor['config_sha256']
                or receipt['pid'] != lifecycle.get('pid')):
            raise ValueError('Actual E3 block receipt/source/process differs')
        allowed = {(p['sample_name'],p['method']):p['slot'] for p in block['paths']}
        seen = set()
        for request in receipt.get('batch',{}).get('requests',[]):
            for i,row in enumerate(request.get('paths',[])):
                key=(request['sample_name'],row['collect'])
                if key not in allowed or key in seen:
                    raise ValueError('Unexpected/duplicate E3 output row')
                seen.add(key)
                # Completed prefix remains eligible after a later protected/unknown failure.
                found[allowed[key]] = dict(row=row,request_record=request,method_index=i,
                    source_receipt=receipt['source_receipt'],source_revision=receipt['source_revision'],
                    model_context=receipt['model_context'],artifact_root=receipt['artifact_root'],
                    source_kind='FRESH_E3_BLOCK',block_id=block['id'])
    result=[]
    for declared in scope['all64_slots']:
        item={k:copy.deepcopy(declared[k]) for k in ('slot','strategy','sample_name','method','disposition')}
        value=reused.get(declared['slot']) if declared['slot'] in reuse_keys else found.get(declared['slot'])
        if value is not None:
            item.update(value)
            if item['row']['collect'] != declared['method'] or item['request_record']['sample_name'] != declared['sample_name']:
                raise ValueError('Actual row does not match the registered slot')
            if declared['slot'] in reuse_keys:
                for kind in ('vector_artifact','video_artifact'):
                    if item['row'].get(kind) != declared['reuse_binding'][kind]:
                        raise ValueError('Immutable selected reuse artifact differs')
                item['source_kind']='QUALIFIED_REUSED_DEV'
            item['status']='COMPLETE_REQUIRES_RAW_AUDIT' if item['row'].get('status')=='COMPLETE_PARENT_PATH' else 'PARTIAL_OR_REJECTED_RETAINED'
        else:
            lifecycle=block_for[declared['slot']]
            item.update(status='UNSTARTED_RETAINED' if 'pid' not in lifecycle else 'ATTEMPTED_NO_ROW_RETAINED',
                source_kind='FRESH_E3_BLOCK',block_id=lifecycle['id'])
        item.update(scored=False,compatible=None,score=None,missing_filled_with_zero=False)
        result.append(item)
    return result


def artifact_file(art, root, suffix):
    path=Path(art['path']).resolve();root=Path(root).resolve()
    if (root not in path.parents or path.suffix!=suffix or not path.is_file()
            or path.stat().st_size!=art['bytes'] or sha_file(path)!=art['sha256']):
        raise ValueError('Missing, foreign, truncated or changed actual artifact')
    return path


def actual_vectors(item, loader, expected_shape, torch, tree_digest):
    row=item['row'];art=row['vector_artifact']
    path=artifact_file(art,item['artifact_root'],'.pt')
    values=loader(path,map_location='cpu',weights_only=True)
    if (set(values)!={'guided','final_latent'} or len(values['guided'])!=36
            or any(t.dtype!=torch.float32 or list(t.shape)!=expected_shape
                or t.device.type!='cpu' or not bool(torch.isfinite(t).all())
                for t in values['guided']+[values['final_latent']])
            or {k:tree_digest(v) for k,v in values.items()}!=art['tensor_sha256']
            or [tree_digest(t) for t in values['guided']]!=row['guided_sha256']
            or tree_digest(values['guided'])!=row['guided_list_sha256']
            or tree_digest(values['final_latent'])!=row['final_latent_sha256']):
        raise ValueError('Actual complete36/final tensor content differs')
    return {'file':art,'actual_tensors_reloaded':37,'final_and_all_guided_hashes_verified':True}


def replay_policy(row, strategy, calibration, specs):
    # Reconstruct recorded choices from actual priors/costs, without touching a generator.
    deployment=row['collection_complete'].get('deployment')
    if deployment is None:
        if row['collect']!='SOURCE_RA':raise ValueError('Only original RA has no current-birth deployment')
        return {'current_birth_decisions_replayed':0,'original_RA_row_verifier_required':True}
    import dataclasses
    import json
    from .source_aware_current_birth_control_r1 import CurrentBirthCPDController
    spec=specs[strategy][row['collect']]
    controller=CurrentBirthCPDController(calibration,spec['threshold'],spec['costs'],spec['partial_prior'],strategy=strategy)
    history=deployment['history']
    if len(history)!=36:raise ValueError('Complete source history required')
    for entry in history:
        actual=entry['source_policy'];saved=actual['decision']
        decision=controller._choice(saved['step'],tuple(tuple(v) for v in saved['packets']),
            saved['both_sources_ready'],saved['partial_ready'],protected=saved['reason']=='actual_protected_dense')
        expected=json.loads(json.dumps(dataclasses.asdict(dataclasses.replace(decision,owner=saved['owner']))))
        if expected!=saved or controller.query_basis(decision)!=actual['working_epoch_basis']:
            raise ValueError('Actual current-birth decision differs from independent replay')
        controller.commit(decision,actual_action=entry['action'][0],pair_completed=True)
        if entry['action']!=decision.action*2:
            raise ValueError('Recorded double-CFG action differs')
        for key,value in {'dense_anchor_after':controller.anchor,'working_kind_after':controller.working_kind,
            'working_created_step_after':controller.working_step,'creation_floor_proxy_after':controller.creation_floor,
            'accumulated_interval_proxy_after':controller.accumulated,'consecutive_P_after':controller.consecutive_P}.items():
            if actual[key]!=value:raise ValueError('Actual source-state update differs: '+key)
    return {'current_birth_decisions_replayed':36,'actual_priors_costs_and_source_state_replayed':True}


def bind_pair(item, reference, source_proof, model_context):
    pair=numerical_pairing(item,reference,source_proof)
    pair['checks']['same_model_context']=item['model_context']==model_context
    pair['compatible']=all(pair['checks'].values())
    pair['incompatible_fields']=[k for k,v in pair['checks'].items() if not v]
    return pair


def recorded_cost(item):
    row=item['row'];actions=row['actions'];complete=row['collection_complete']
    wall=row['instrumented_parent_pipeline_wall_seconds'];d=complete.get('deployment')
    a=d.get('A_readout') if d is not None else None;extra=a['extra_candidate_heads'] if a else 0
    if (len(actions)!=36 or any(x not in ('CC','PP','DD') for x in actions)
            or complete['complete_pairs']!=36 or type(wall) not in (int,float) or not math.isfinite(wall) or wall<0
            or type(extra) is not int or extra<0 or len(complete['actual_original_plus_candidate_heads'])!=72+extra
            or a and (a['teacher_calls'] or a['extra_candidate_deep_blocks'])):
        raise ValueError('Actual complete action/head/cost record differs')
    return {'actions':actions,'complete_branch_calls':2*actions.count('DD'),
        'partial_branch_calls':2*actions.count('PP'),'reuse_branch_calls':2*actions.count('CC'),
        'extra_candidate_heads':extra,'instrumented_pipeline_wall_seconds':wall,
        'source_kind':item['source_kind'],'source_revision':item['source_revision'],
        'source_receipt':item['source_receipt'],'block_id':item.get('block_id'),
        'clean_speed_claim':False,'cross_batch_or_load_order_isolation':False}


def summarize(slots):
    expected=[(s,n,m) for s in STRATEGIES for n in NAMES for m in METHODS]
    if len(slots)!=64 or [(x['strategy'],x['sample_name'],x['method']) for x in slots]!=expected:
        raise ValueError('Full64 reporting denominator required')
    scored={};rows=[]
    for item in slots:
        s=item.get('score')
        if s is not None:
            v=s['frame_distances']
            if (item['status']!='SCORED_FULL93' or not item['compatible'] or not item['scored']
                    or s['frames']!=93 or len(v)!=93 or len(s['pts'])!=93 or len({tuple(x) for x in s['pts']})!=93
                    or any(not math.isfinite(x) for x in v) or not math.isfinite(s['mean_LPIPS'])
                    or not math.isclose(mean(v),s['mean_LPIPS'],rel_tol=1e-12,abs_tol=1e-12)
                    or s['reference_sha256']!=item['reference']['sha256']
                    or s['candidate_sha256']!=item['candidate']['sha256']):
                raise ValueError('Every actual score needs full93 PTS/distances and original hashes')
            scored[(item['strategy'],item['sample_name'],item['method'])]=item
        elif item['scored']:raise ValueError('Missing score cannot be counted or zero-filled')
        rows.append({k:copy.deepcopy(item.get(k)) for k in ('slot','strategy','sample_name','method','status',
            'disposition','source_kind','compatible','pairing','scored','score','recorded_cost','error_type','error')})
    comparisons=[]
    within=[('DYNAMIC_NO_P','SOURCE_RA'),('CPD','DYNAMIC_NO_P'),('REF_CPD','CPD'),('A_CPD_OFF','CPD'),
        ('A_CPD_W1_ONE_PHASE','CPD'),('A_CPD_BETA1_ONE_PHASE','CPD'),('A_CPD_W1_ONE_PHASE','A_CPD_BETA1_ONE_PHASE'),
        ('DENSE_CONTROL','SOURCE_RA')]
    contrasts=[((s,a),(s,b)) for s in STRATEGIES for a,b in within]
    contrasts += [((STRATEGIES[1],m),(STRATEGIES[0],m)) for m in METHODS]
    for candidate,baseline in contrasts:
        matched=[];gaps=[]
        for name in NAMES:
            a=scored.get((candidate[0],name,candidate[1]));b=scored.get((baseline[0],name,baseline[1]))
            if a is None or b is None:
                gaps.append({'sample_name':name,'candidate_available':a is not None,'baseline_available':b is not None});continue
            if a['reference']!=b['reference'] or a['score']['pts']!=b['score']['pts']:
                raise ValueError('A contrast must use the same actual Native and timestamps')
            delta=[x-y for x,y in zip(b['score']['frame_distances'],a['score']['frame_distances'])]
            matched.append({'sample_name':name,'candidate_LPIPS':a['score']['mean_LPIPS'],
                'baseline_LPIPS':b['score']['mean_LPIPS'],'baseline_minus_candidate_LPIPS':mean(delta),
                'relative_LPIPS_improvement_percent':100*mean(delta)/b['score']['mean_LPIPS'] if b['score']['mean_LPIPS']>0 else None,
                'improved_frames':sum(x>0 for x in delta),'degraded_frames':sum(x<0 for x in delta),
                'tied_frames':sum(x==0 for x in delta),'contiguous31_frame_mean_differences':[mean(delta[i:i+31]) for i in (0,31,62)],
                'candidate_recorded_cost':a.get('recorded_cost'),'baseline_recorded_cost':b.get('recorded_cost'),
                'same_card_clean_timing_comparison':False})
        comparisons.append({'candidate':list(candidate),'baseline':list(baseline),'registered_scenes':4,
            'matched_scenes':len(matched),'gaps':gaps,'per_scene':matched,
            'scene_equal_mean_LPIPS_difference':mean(r['baseline_minus_candidate_LPIPS'] for r in matched) if matched else None,
            'improved_scenes':sum(r['baseline_minus_candidate_LPIPS']>0 for r in matched),
            'degraded_scenes':sum(r['baseline_minus_candidate_LPIPS']<0 for r in matched)})
    return {'registered_positions':64,'qualified_reuse_positions':10,'fresh_generation_positions':54,
        'scored_pairs':len(scored),'actual_frame_distances':93*len(scored),'per_slot':rows,
        'gaps_retained':64-len(scored),'contrasts':comparisons,'missing_scores_filled_with_zero':False,
        'clean_speed_claim':False,'frames_are_independent_samples':False,
        'fidelity_not_semantic_or_physics_quality':True,'development_not_independent_confirmation':True,
        'single_threshold_direction_rejection':False}
