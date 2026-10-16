"""Read-only full12 action-price audit; retain every failed or missing position.

The price observer already audits each complete source/phase scene. This layer
adds full parent/raw/RGB controls and keeps observed modes and rounds separate.
"""
import copy
from collections import Counter
from pathlib import Path
from statistics import mean,median

import torch

from .action_price12_execution_r1 import full_rows
from .action_price16_audit_r1 import audit_scene
from .action_price16_cost_r1 import COUNTS
from .frozen_shared_post_r1 import artifact_path,failure,inspect_video,stable_history
from .frozen_shared_production_r1 import number
from .mid_coverage import tree_digest

GPU_TERMINAL_STATUS='N09_ACTION12_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT'
COMPLETE_STATUS='N09_ACTION12_ALL12_RAW_RGB_AND_CURRENT_PRICES_AUDITED_NOT_CLEAN_LATENCY'


def metadata_audit(row,planned):
    if (any(row.get(k)!=v for k,v in planned.items())
            or row['observation_mode']!=planned['mode'] or row['complete_parent_identity']!=planned
            or row['new_prices_used_in_parent']
            or row['timing_claim']!='N09_SAME_STATE_INCREMENTAL_ACTION_DIAGNOSTIC_NOT_CLEAN_VIDEO'):
        raise ValueError('Original complete parent identity, diagnostic mode and offline-only policy required')
    restored=row['pre_request_state_identity'];memory=row['request_memory_lifecycle']
    if (restored['original_state_sha256']!=restored['restored_state_sha256']
            or restored['shared_eval_verified'] is not True or len(restored['original_state_sha256'])!=64
            or memory['components_alive_after']!=0 or memory['within_request_algorithm_or_guardrails_changed']
            or type(memory['observed_components']) is not int or memory['observed_components']<0
            or any(not number(memory[k]['seconds']) or memory[k]['seconds']<0 for k in ('before','after'))):
        raise ValueError('Exact restored state/eval, original request lifetime and all owners released required')
    if row['status']=='TEXT_REJECTED':
        if (row['solver_steps']!=0 or row['guided_pairs']!=0 or row['actual_pair_computations']!=0
                or row['diagnostic_points'] or row.get('actions') or row.get('A_history') or row.get('source_history')
                or any(row.get(k) for k in ('final_artifact','guided_artifact','video_path',
                    'final_latent_sha256','guided_tree_sha256','guided_outputs'))):
            raise ValueError('Text rejection cannot contain generated parent or trial artifacts')
        return
    if row['status'] not in ('COMPLETE','VIDEO_REJECTED'):
        raise ValueError('Original terminal generation outcome required')
    points=0 if planned['mode']=='BASELINE' else 4
    if (row['solver_steps']!=36 or row['guided_pairs']!=36 or row['guided_outputs']!=36
            or len(row['scheduler_timesteps'])!=36 or len(row['actions'])!=36
            or row['actual_pair_computations']!=(36 if not points else 100)
            or len(row['diagnostic_points'])!=points
            or len(row['source_history'])!=36):
        raise ValueError('All36 parent updates and the complete original trial denominator required')
    # Baseline execute() includes an aggregate; direct diagnostic execute()
    # records the original per-step counters instead. Derive from all36,
    # never interpret a missing aggregate as zero without its full history.
    teachers=[item['teacher_calls'] for item in row['source_history']]
    if (any(type(n) is not int or n<0 for n in teachers) or sum(teachers)!=0
            or ('online_teacher_calls' in row and row['online_teacher_calls']!=sum(teachers))):
        raise ValueError('Complete ordinary parent teacher counters must prove zero online teachers')
    for index,item in enumerate(row['source_history'],1):
        if (item['step']!=index or item['action']!=row['actions'][index-1]
                or item['teacher_calls'] or item['P_updates_true_D_or_zero_risk_RA_anchor']
                or (item['action']!='DD' and item['true_D_before']!=item['true_D_after'])):
            raise ValueError('Ordinary source history changed or an offline teacher reached the parent')
        if item['action']=='PP' and (item['source_policy']['creation_floor_proxy_after']<=0
                or any(s['kind']!='P' or s['RA_zero_risk_reset_allowed'] for s in item['working_sources'])):
            raise ValueError('Partial sources retain their nonzero birth error and cannot become true D')


def audit_parent(row,planned,loader,*,expected_shape):
    metadata_audit(row,planned)
    if row['status']=='TEXT_REJECTED':return
    final=loader(row['final_artifact']);guided=loader(row['guided_artifact'])
    if (set(final)!={'final_latent'} or set(guided)!={'guided'} or len(guided['guided'])!=36
            or tree_digest(final['final_latent'])!=row['final_latent_sha256']
            or tree_digest(guided['guided'])!=row['guided_tree_sha256']):
        raise ValueError('Original final tensor and all36 original guided tensor identities required')
    for tensor in [final['final_latent'],*guided['guided']]:
        if (not isinstance(tensor,torch.Tensor) or tensor.device.type!='cpu'
                or tensor.dtype!=torch.float32 or tuple(tensor.shape)!=tuple(expected_shape)
                or not bool(torch.isfinite(tensor).all())):
            raise ValueError('Original finite CPU FP32 parent geometry required')


def original_raw(binding,*,expected_shape):
    asset=binding['final_artifact'];path=artifact_path(Path(asset['path']).parent,asset)
    payload=torch.load(path,map_location='cpu',weights_only=True)
    if (set(payload)!={'final_latent'} or not isinstance(payload['final_latent'],torch.Tensor)
            or payload['final_latent'].dtype!=torch.float32
            or tuple(payload['final_latent'].shape)!=tuple(expected_shape)
            or not bool(torch.isfinite(payload['final_latent']).all())
            or tree_digest(payload['final_latent'])!=binding['final_latent_sha256']):
        raise ValueError('Original independent P_OFF endpoint tensor differs')
    return dict(final_artifact=copy.deepcopy(asset),final_latent_sha256=binding['final_latent_sha256'],
        actions=copy.deepcopy(binding['actions']))


def original_video(binding):
    asset=binding['video_artifact'];path=artifact_path(Path(asset['path']).parent,asset)
    value=inspect_video(path.parent,dict(video_path=str(path)))
    if (binding['decoded_video']['frames']!=93
            or value['decoded_video']['RGB_sha256']!=binding['decoded_video']['RGB_sha256']):
        raise ValueError('Original independent P_OFF93-frame RGB identity differs')
    return value


def audit_rows(runs,scope,baseline,loader,video_inspector,old_raw_inspector,old_video_inspector,
               *,expected_shape,save=lambda result:None):
    rows=copy.deepcopy(full_rows(runs,scope));names=[r['name'] for r in scope['requests']]
    if (len(rows)!=12 or len(names)!=4 or len(set(names))!=4
            or scope['scope_counts']!=COUNTS or set(baseline['bindings'])!=set(names)):
        raise ValueError('All12 original parents and all four independent old bindings required')
    result=dict(rows=rows,audit_failures=[],old_parent_controls=[],mode_controls=[],
        price_scenes=[],unavailable_price_scenes=[])
    old={}
    for scene in names:
        binding=baseline['bindings'][scene]
        control=dict(scene=scene,raw_model_audit='UNAVAILABLE_RETAINED',endpoint_audit='UNAVAILABLE_RETAINED')
        old[scene]=control;result['old_parent_controls'].append(control)
        for kind,key,observe in (
                ('OLD_PARENT_RAW','raw_model_audit',lambda:old_raw_inspector(binding)),
                ('OLD_PARENT_RGB','endpoint_audit',lambda:old_video_inspector(binding))):
            try:
                control.update(observe());control[key]='PASS'
            except Exception as error:
                control[key]='AUDIT_FAILURE_RETAINED';result['audit_failures'].append(failure(kind,{'id':scene},error))
        save(result)
    seen_paths=set()
    for row,planned in zip(rows,scope['complete_parent_matrix']):
        if row['status'] in ('TECH_FAILED','NOT_REACHED'):
            save(result);continue
        try:
            if row['status'] in ('COMPLETE','VIDEO_REJECTED'):
                if planned['mode']!='BASELINE':
                    actual={p['point']['chosen']['step']:p['point'] for p in row['diagnostic_points']}
                    expected={p['chosen']['step']:p for p in scope['states'] if p['scene']==row['scene']}
                    if len(actual)!=4 or actual!=expected:
                        raise ValueError('Every original natural source/phase/age point must match the registered scope')
                assets=[row['final_artifact'],row['guided_artifact']]+[
                    p['artifact'] for p in row['diagnostic_points']]
                paths=[str(Path(a['path']).resolve()) for a in assets]
                if len(paths)!=len(set(paths)) or seen_paths.intersection(paths):
                    raise ValueError('All original parent and point files need unique identities')
                seen_paths.update(paths)
            audit_parent(row,planned,loader,expected_shape=expected_shape)
            row['raw_model_audit']='NOT_APPLICABLE_TEXT_REJECTION_RETAINED' if row['status']=='TEXT_REJECTED' else 'PASS'
        except Exception as error:
            row['raw_model_audit']='AUDIT_FAILURE_RETAINED'
            result['audit_failures'].append(failure('PARENT_RAW_OR_METADATA',row,error))
        if row['status']!='COMPLETE':row['endpoint_audit']='NOT_APPLICABLE_'+row['status']+'_RETAINED'
        else:
            try:
                row.update(video_inspector(row));row['endpoint_audit']='PASS'
            except Exception as error:
                row['endpoint_audit']='AUDIT_FAILURE_RETAINED'
                result['audit_failures'].append(failure('PARENT_VIDEO_CONTAINER_OR_RGB',row,error))
        save(result)
    indexed={(r['scene'],r['mode']):r for r in rows}
    for scene in names:
        group=[indexed[(scene,m)] for m in ('BASELINE','AUDIT','LEAN')];base=group[0];legacy=old[scene]
        control=dict(scene=scene,parent_ids=[r['id'] for r in group],
            raw_control='UNAVAILABLE_RETAINED',RGB_control='UNAVAILABLE_RETAINED')
        result['mode_controls'].append(control)
        if all(r.get('raw_model_audit')=='PASS' for r in group) and legacy['raw_model_audit']=='PASS':
            try:
                if any(r['final_latent_sha256']!=legacy['final_latent_sha256']
                       or r['actions']!=legacy['actions'] for r in group):
                    raise ValueError('New complete parents differ from the old independent P_OFF endpoint/actions')
                for other in group[1:]:
                    for key in ('final_latent_sha256','guided_tree_sha256','actions','A_history',
                                'scheduler_timesteps','pre_request_state_identity'):
                        if other[key]!=base[key]:raise ValueError('Full36 parent modes differ: '+key)
                    if stable_history(other['source_history'])!=stable_history(base['source_history']):
                        raise ValueError('Ordinary parent source histories differ between diagnostic modes')
                control['raw_control']='PASS'
            except Exception as error:
                control['raw_control']='PARITY_FAILURE_RETAINED'
                result['audit_failures'].append(failure('FULL36_PARENT_MODE_AND_OLD_RAW_CONTROL',base,error))
        if all(r.get('endpoint_audit')=='PASS' for r in group) and legacy['endpoint_audit']=='PASS':
            try:
                rgb=legacy['decoded_video']['RGB_sha256']
                if any(r['decoded_video']['RGB_sha256']!=rgb for r in group):
                    raise ValueError('New93-frame RGB outputs differ from the independent original parent')
                if any(r['video_artifact']['decoded_rgb_sha256']!=base['video_artifact']['decoded_rgb_sha256'] for r in group[1:]):
                    raise ValueError('Per-frame mode RGB controls differ')
                control['RGB_control']='PASS'
            except Exception as error:
                control['RGB_control']='PARITY_FAILURE_RETAINED'
                result['audit_failures'].append(failure('PARENT_93FRAME_RGB_CONTROL',base,error))
        if control['raw_control']=='PASS':
            try:
                checked=audit_scene({m:indexed[(scene,m)]['diagnostic_points'] for m in ('AUDIT','LEAN')},
                    loader,expected_shape=expected_shape)
                checked.update(parent_scene=scene,parent_raw_control='PASS',parent_RGB_control=control['RGB_control'],
                    video_gap_does_not_become_a_raw_teacher_failure=control['RGB_control']!='PASS')
                result['price_scenes'].append(checked)
            except Exception as error:
                result['audit_failures'].append(failure('COMPLETE_SCENE_ACTION_PRICES',base,error))
                result['unavailable_price_scenes'].append(dict(scene=scene,reason='ORIGINAL_PRICE_RAW_AUDIT_FAILURE_RETAINED'))
        else:result['unavailable_price_scenes'].append(dict(scene=scene,reason='PARENT_RAW_OR_OLD_CONTROL_UNAVAILABLE_RETAINED'))
        save(result)
    return result


def price_statistics(price_scenes):
    groups={}
    for scene in price_scenes:
        for observation in scene['observations']:
            for action,values in observation['formal_seconds'].items():
                if len(values['all_three'])!=3:raise ValueError('All three formal intervals must be retained')
                key=(observation['mode'],observation['source'],observation['phase'],action)
                groups.setdefault(key,[]).append(dict(scene=observation['scene'],step=observation['step'],
                    all_three=values['all_three'],scene_mean=mean(values['all_three'])))
    return [dict(mode=key[0],source=key[1],phase=key[2],action=key[3],
        scenes=values,observed_scenes=len(values),required_scenes=4,
        scene_equal_mean_seconds=mean(v['scene_mean'] for v in values),
        median_scene_mean_seconds=median(v['scene_mean'] for v in values),
        formal_intervals=3*len(values),warmup_intervals_included=False,
        audit_lean_modes_combined=False,complete_scene_support=len(values)==4)
        for key,values in sorted(groups.items())]


def summarize(result,scope,*,observed_paths,child_exit_code):
    rows=result['rows'];prices=result['price_scenes'];controls=result['mode_controls']
    if (len(rows)!=12 or len(controls)!=4 or len(result['old_parent_controls'])!=4
            or scope['scope_counts']!=COUNTS or type(observed_paths) is not int or not 0<=observed_paths<=12):
        raise ValueError('Full12 and all four control denominators must survive')
    complete=(observed_paths==12 and child_exit_code==0 and not result['audit_failures']
        and all(r['status']=='COMPLETE' and r.get('raw_model_audit')=='PASS' and r.get('endpoint_audit')=='PASS' for r in rows)
        and all(c['raw_control']==c['RGB_control']=='PASS' for c in controls)
        and len(prices)==4 and sum(r['actual_pair_computations'] for r in rows)==944)
    status=(COMPLETE_STATUS if complete else
        'N09_ACTION12_AUDIT_FAILURE_FULL_SCOPE_RETAINED' if result['audit_failures'] else
        'N09_ACTION12_TECHNICAL_INCOMPLETE_FULL_SCOPE_RETAINED' if observed_paths!=12 or child_exit_code!=0 else
        'N09_ACTION12_REJECTIONS_OR_MISSING_CONTROLS_RETAINED')
    return dict(status=status,registered_total_parent_positions=12,original_runner_paths=observed_paths,
        original_parent_outcomes=dict(Counter(r['status'] for r in rows)),
        raw_model_pass_paths=sum(r.get('raw_model_audit')=='PASS' for r in rows),
        verified_parent_tensor_files=2*sum(r.get('raw_model_audit')=='PASS' for r in rows),
        verified_parent_tensors=37*sum(r.get('raw_model_audit')=='PASS' for r in rows),
        accepted_93frame_videos=sum(r.get('endpoint_audit')=='PASS' for r in rows),
        accepted_old_raw_controls=sum(c['raw_model_audit']=='PASS' for c in result['old_parent_controls']),
        accepted_old93_RGB_controls=sum(c['endpoint_audit']=='PASS' for c in result['old_parent_controls']),
        accepted_full36_mode_controls=sum(c['raw_control']=='PASS' for c in controls),
        accepted_mode93_RGB_controls=sum(c['RGB_control']=='PASS' for c in controls),
        verified_price_scenes=len(prices),required_price_scenes=4,
        verified_price_point_files=sum(c['raw_files'] for c in prices),
        verified_price_point_tensors=sum(c['raw_tensors'] for c in prices),
        verified_trial_intervals=sum(c['retained_trial_intervals'] for c in prices),
        verified_formal_intervals=sum(c['formal_trial_intervals'] for c in prices),
        known_pair_computations=sum(r['actual_pair_computations'] for r in rows
            if type(r.get('actual_pair_computations')) is int and r['actual_pair_computations']>=0),
        unavailable_pair_counter_positions=[r['id'] for r in rows if r['status']!='NOT_REACHED'
            and (type(r.get('actual_pair_computations')) is not int or r['actual_pair_computations']<0)],
        whole_registered_pairs=944,all_requested_measurements_valid=complete,
        separate_price_statistics=price_statistics(prices),
        primitive_selector_is_not_full_H1_controller_cost=True,
        price_is_post_paid_probe_incremental_not_clean_video_latency=True,
        minimal_calibration_collection_cost_measured=False,new_parameters_deployed=False,
        new_video_quality_or_clean_acceleration_claim=False,GPU_submissions=0,ledger_written=False)
