"""Audit the entire 18-parent/72-position W3 collection, never fit a policy.

Readers must bind immutable file hashes and paths outside this pure auditor.
All planned positions survive rejection or technical stopping. Raw labels are
recomputed from every available original tensor; videos are parent controls.
"""
import torch

from .mid_coverage import tree_digest
from .p_acr_profile528_contract_r1 import H1_FP
from .w3_label64_post_r1 import audit_features,audit_label,full_matrix
from .w3_label64_h1_owner_r1 import STEPS

PROVENANCE=('REAL_SAME_STATE_POST_RF','SYNTHETIC_CPU_INTERFACE')
TERMINAL={'COMPLETE','VIDEO_REJECTED','TEXT_REJECTED','TECHNICAL_FAILURE','NOT_RUN'}


def check_row(row,planned):
    if any(row.get(k)!=planned[k] for k in ('id','scene','section','kind')):
        raise ValueError('Original18 parent identities/order must be preserved')
    if row.get('status') not in TERMINAL:
        raise ValueError('Original parent lacks terminal or explicit missing status')
    if row['status'] in ('COMPLETE','VIDEO_REJECTED'):
        if (row.get('solver_steps')!=36 or row.get('guided_pairs')!=36
                or row.get('method_fingerprint')!=H1_FP or len(row.get('actions',()))!=36
                or len(row.get('source_history',()))!=36 or len(row.get('A_history',()))!=36
                or len(row.get('guided_sha256',()))!=36 or not row.get('parent_vectors')):
            raise ValueError('Every completed ordinary36 parent vector/history required')
    elif row['status']=='TEXT_REJECTED' and (row.get('solver_steps',0)
            or row.get('guided_pairs',0) or row.get('parent_vectors')):
        raise ValueError('Text rejection cannot carry generated parent vectors')
    if row['kind']=='BASELINE' and row.get('diagnostic_points'):
        raise ValueError('Ordinary baseline cannot contain shadow teacher labels')


def parent_vectors(raw,row,shape):
    if set(raw)!={'guided','final_latent'} or len(raw['guided'])!=36:
        raise ValueError('All37 ordinary parent tensors required')
    values=list(raw['guided'])+[raw['final_latent']]
    if any(not isinstance(t,torch.Tensor) or list(t.shape)!=list(shape)
            or t.dtype!=torch.float32 or t.device.type!='cpu' or not bool(torch.isfinite(t).all()) for t in values):
        raise ValueError('Finite CPU FP32 actual parent geometry required')
    if ([tree_digest(t) for t in raw['guided']]!=row['guided_sha256']
            or tree_digest(raw['final_latent'])!=row['final_latent_sha256']):
        raise ValueError('Raw parent vectors differ from recorded actual outputs')


def partial_point_vectors(raw,shape):
    """Read a saved partial-run point without promoting it to a usable label."""
    if set(raw)!={'C','A','D','actual_latent','timestep'}:
        raise ValueError('All8 saved partial point tensors required')
    for kind in ('C','A','D'):
        if not isinstance(raw[kind],tuple) or len(raw[kind])!=2:
            raise ValueError('Both saved partial branch outputs required')
        for t in raw[kind]:
            if (not isinstance(t,torch.Tensor) or list(t.shape)!=list(shape) or t.dtype!=torch.float32
                    or t.device.type!='cpu' or not bool(torch.isfinite(t).all())):
                raise ValueError('Saved partial point geometry changed')
    if (list(raw['actual_latent'].shape)!=list(shape) or not bool(torch.isfinite(raw['actual_latent']).all())
            or raw['timestep'].numel()!=1 or not bool(torch.isfinite(raw['timestep']).all())):
        raise ValueError('Saved partial latent/time coordinates changed')


def audit_all(rows,requests,*,clock,expected_shape,load_raw,read_video,provenance):
    if provenance not in PROVENANCE:raise ValueError('Explicit actual or synthetic provenance required')
    plan=full_matrix(requests)
    if len(rows)!=18:raise ValueError('All18 parents remain even when rejected or stopped')
    output={'parents':[],'labels':[],'planned_parent_denominator':18,
        'planned_formal_label_denominator':64,'planned_warmup_label_denominator':8,
        'planned_pairs_maximum':864,'planned_raw_files_maximum':90,'planned_raw_tensors_maximum':1242,
        'provenance':provenance,'real_teacher_claim':provenance=='REAL_SAME_STATE_POST_RF',
        'method_endpoint_or_latency_claim':False,'GPU_submissions':0}
    controls={};rgb_controls={};raw_ids=set();raw_owners={};tensor_count=actual_pairs=accepted_videos=0
    failures=[];recorded_counts=[]
    for row,planned in zip(rows,plan):
        key=(planned['section'],planned['scene']);base_key=key+('BASELINE',)
        parent={k:planned[k] for k in ('id','scene','section','kind')}
        parent.update(original_status=row.get('status'),audit_status='PENDING')
        count=row.get('actual_pair_computations',0 if row.get('status') in ('NOT_RUN','TEXT_REJECTED') else None)
        recorded_counts.append(count if type(count) is int and 0<=count<=60 else None)
        try:
            check_row(row,planned)
            complete=row['status'] in ('COMPLETE','VIDEO_REJECTED')
            raw=None
            if row.get('parent_vectors'):
                asset=row['parent_vectors'];raw=load_raw(asset)
                identity=asset['path']
                if identity in raw_ids:raise ValueError('A raw file cannot substitute another parent/point')
                raw_ids.add(identity);raw_owners[identity]=planned['id'];parent_vectors(raw,row,expected_shape);tensor_count+=37
            if complete and raw is None:raise ValueError('Missing complete original parent vectors')
            if complete:
                count=row.get('actual_pair_computations')
                points=row.get('diagnostic_points',[])
                expected=36+sum(r['extra_pairs'] for r in points)
                if (type(count) is not int or count!=expected or not 36<=count<=60
                        or row['kind']=='BASELINE' and count!=36):
                    raise ValueError('Actual ordinary/diagnostic charge count differs')
                actual_pairs+=count
                if row['kind']=='BASELINE':controls[base_key]=(raw,row)
                else:
                    baseline=controls.get(base_key)
                    if baseline is None:raise ValueError('Resident ordinary control missing; never substitute')
                    old,oldrow=baseline
                    if (any(not torch.equal(a,b) for a,b in zip(raw['guided'],old['guided']))
                            or not torch.equal(raw['final_latent'],old['final_latent'])
                            or row['actions']!=oldrow['actions'] or row['A_history']!=oldrow['A_history']):
                        raise ValueError('Shadow diagnostics changed the complete ordinary H1 parent')
                    parent['all36_guided_actions_Ahistory_final_equal']=True
            if row['kind']=='DIAGNOSTIC':
                records=row.get('diagnostic_points',[])
                if len({r['step'] for r in records})!=len(records) or any(r['step'] not in STEPS for r in records):
                    raise ValueError('Duplicate/unregistered label cannot replace planned positions')
                if complete and [r['step'] for r in records]!=list(STEPS):
                    raise ValueError('All8 labels including UNKNOWN required on completed diagnostic parent')
                features=audit_features(row['feature_rows'],clock=clock) if complete else None
                indexed={r['step']:r for r in records}
                for step in STEPS:
                    label={'parent_id':planned['id'],'scene':planned['scene'],'section':planned['section'],
                        'step':step,'denominator_kept':True,'labels_available':False}
                    record=indexed.get(step)
                    payload=None
                    if record is not None and record.get('artifact'):
                        asset=record['artifact'];payload=load_raw(asset);identity=asset['path']
                        if identity in raw_ids:raise ValueError('A raw file cannot substitute another parent/point')
                        raw_ids.add(identity);raw_owners[identity]=planned['id']
                        if tree_digest(payload)!=asset['tensor_sha256']:raise ValueError('Saved raw point fingerprint changed')
                        partial_point_vectors(payload,expected_shape);tensor_count+=8
                    if record is None or features is None:
                        label.update(status='MISSING_OR_TECHNICAL_PARENT_RETAINED',original_parent_status=row['status'],
                            partial_record_preserved=record is not None,available_raw8_read=payload is not None,
                            admitted_to_training=False)
                    else:
                        if record['status'].startswith('COMPLETE') and any(
                                t.get('exact_original_70_call_cycle_clear')!=(step==35) for t in record['trials']):
                            raise ValueError('Exact native35 cycle receipt differs')
                        label.update(audit_label(payload,record,features,row['source_history'],
                            expected_shape=expected_shape,provenance=provenance))
                    output['labels'].append(label)
                # A point can be saved before a later ordinary-call failure
                # prevents the label record from committing. Audit that file
                # too, but never fabricate the missing state/teacher label.
                inventory=row.get('raw_point_artifacts',[])
                if len({r['step'] for r in inventory})!=len(inventory):
                    raise ValueError('Duplicate saved point inventory step')
                orphans=[]
                for item in inventory:
                    if item['step'] not in STEPS:raise ValueError('Unregistered saved point inventory')
                    asset=item['artifact'];identity=asset['path']
                    if identity in raw_ids:
                        if raw_owners[identity]!=planned['id']:raise ValueError('Point inventory refers to another parent raw file')
                        recorded=indexed.get(item['step'],{}).get('artifact')
                        if recorded!=asset:raise ValueError('Recorded point and saved inventory differ')
                        continue
                    if complete:raise ValueError('Completed parent has an unrecorded saved point')
                    raw=load_raw(asset)
                    if tree_digest(raw)!=asset['tensor_sha256']:raise ValueError('Orphan saved point fingerprint changed')
                    partial_point_vectors(raw,expected_shape);raw_ids.add(identity);raw_owners[identity]=planned['id'];tensor_count+=8
                    orphans.append({'step':item['step'],'all8_saved_tensors_read':True,'admitted_to_training':False})
                parent['unrecorded_saved_points_retained']=orphans
            if row['status']=='COMPLETE':
                video=read_video(row)
                if video.get('frames')!=93 or not video.get('RGB_sha256'):
                    raise ValueError('Every accepted video must fully decode93 frames')
                parent.update(video=video,video_is_original_H1_control=True);accepted_videos+=1
                if row['kind']=='BASELINE':rgb_controls[base_key]=video['RGB_sha256']
                else:
                    control=rgb_controls.get(base_key)
                    if control is None or control!=video['RGB_sha256']:
                        raise ValueError('Missing/rejected RGB control or parent video mismatch')
                    parent['all93_RGB_equal_to_resident_baseline']=True
            parent['audit_status']='AUDITED' if complete else 'ORIGINAL_REJECTION_OR_MISSING_RETAINED'
        except (ValueError,KeyError,TypeError,AssertionError,OSError,RuntimeError,EOFError) as error:
            parent.update(audit_status='AUDIT_FAILURE',error_type=type(error).__name__,error=str(error));failures.append(parent['id'])
            if planned['kind']=='DIAGNOSTIC':
                present={r['step'] for r in output['labels'] if r['parent_id']==planned['id']}
                for step in STEPS:
                    if step not in present:output['labels'].append({'parent_id':planned['id'],'scene':planned['scene'],
                        'section':planned['section'],'step':step,'status':'AUDIT_FAILURE_RETAINED','denominator_kept':True,'labels_available':False})
        output['parents'].append(parent)
    if len(output['parents'])!=18 or len(output['labels'])!=72:
        raise ValueError('Full18/72 audit denominator was lost')
    labels=sum(r['labels_available'] for r in output['labels'])
    output.update(status='W3_FULL18_LABEL72_RAW_PARENT_CPU_AUDITED' if not failures and actual_pairs==864 and labels==72
        else 'W3_FULL_SCOPE_PARTIAL_REJECTIONS_OR_AUDIT_FAILURES_RETAINED',audit_failed_parent_ids=failures,
        actual_pairs=sum(recorded_counts) if all(v is not None for v in recorded_counts) else None,
        actual_pair_count_unknown_parent_ids=[p['id'] for p,v in zip(plan,recorded_counts) if v is None],
        verified_complete_parent_pairs=actual_pairs,actual_available_labels=labels,raw_files=len(raw_ids),raw_tensors=tensor_count,
        accepted_videos=accepted_videos,scored_control_frames=accepted_videos*93,
        full90_1242_raw_scope_audited=len(raw_ids)==90 and tensor_count==1242,
        real_teacher_claim=provenance=='REAL_SAME_STATE_POST_RF' and labels>0)
    return output
