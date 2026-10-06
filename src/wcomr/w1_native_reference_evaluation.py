"""All eight original rows, accepted/rejected/missing Native references and W1 signs."""
import math
from pathlib import Path
import statistics

from .w1_native_reference_scope import INDICES, NAMES
from .protocol import validate_schedule


def reference_plan(receipt, draft, artifact_root):
    cases = receipt['cases']
    if (receipt['run_card'] != 'WC-W1-NATIVE-REFERENCE-CAL8-R1-20261006-A'
            or receipt['planned_references'] != 5 or receipt['original_denominator'] != [8,7,1]
            or len(cases) > 5 or receipt['original_rejected_sample_replaced']
            or receipt['independent_confirmation'] or receipt['GPU_scoring']):
        raise ValueError('Original reference generation denominator differs')
    verified, files = {}, []
    for i, case in enumerate(cases):
        row = draft['rows'][INDICES[i]]
        if (case['sample_name'] != NAMES[i] or case['original_CAL_index'] != INDICES[i]
                or case['request'] != row['request']):
            raise ValueError('Generated reference identity/order differs')
        if case['status'] not in ['ACCEPTED_REQUIRES_CPU_FULL_DECODE','TEXT_REJECTED','VIDEO_REJECTED']:
            continue  # Failed or unstarted rows stay unknown, never score their partial files.
        if (case['status'] != ('ACCEPTED_REQUIRES_CPU_FULL_DECODE' if case['outcome']=='ACCEPTED' else case['outcome'])
                or case['outcome'] not in ['ACCEPTED','TEXT_REJECTED','VIDEO_REJECTED']
                or case['flags_before'] != receipt['backend_flags'] or case['flags_after'] != receipt['backend_flags']):
            raise ValueError('Completed Native outcome/backend evidence differs')
        if case['worldcache_enabled'] or case['official_forward_identity'] != (
                'cosmos_predict2._src.predict2.networks.minimal_v1_lvg_dit.MinimalV1LVGDiT.forward'):
            raise ValueError('Native reference executed cache/other forward')
        if case['outcome'] == 'TEXT_REJECTED':
            if case['CFG_calls'] or case['solver_steps'] or case['prepare_calls'] or case['pipeline_events'] or case['artifact'] is not None:
                raise ValueError('Text rejection generation differs')
        elif (case['CFG_calls'],case['solver_steps'],case['prepare_calls']) != (72,36,1) or (
                case['block_counts'] != {'denoiser_calls':72,'full_calls':72,'skipped_deep_calls':0}
                or len(case['trace']) != 72 or not all(e['deep_executed'] for e in case['trace'])):
            raise ValueError('Every Native reference requires complete dense execution')
        if case['outcome']!='TEXT_REJECTED':
            validate_schedule(case['sampling'],case['block_counts'],draft['sampling_protocol'],'native')
            events=case['pipeline_events']; labels=[e['stage'] for e in events]
            expected=['sample_return','decode_input','decode_output','guardrail_input','guardrail_output']
            if case['outcome']=='ACCEPTED':expected.append('save_input')
            if (labels!=expected or events[2]['value']['shape']!=[1,3,93,432,768]
                    or events[3]['value']['shape']!=[93,432,768,3]
                    or (case['outcome']=='ACCEPTED' and (events[4]['value']['shape']!=[93,432,768,3]
                        or events[5]['value']['shape']!=[3,93,432,768]))):
                raise ValueError('Native full-video pipeline geometry/order differs')
        if case['outcome'] == 'ACCEPTED':
            item = case['artifact']
            if Path(item['path']).resolve() != (Path(artifact_root)/row['scene']/(row['scene']+'.mp4')).resolve():
                raise ValueError('New Native artifact escapes its own scope')
            files.append({'scene':row['scene'],'role':'new_Native35',**item})
        elif case['artifact'] is not None:
            raise ValueError('Rejected Native output was substituted')
        verified[row['scene']] = case
    rows, pairs = [], []
    for row in draft['rows']:
        result = {'scene':row['scene'],'original_CAL_index':row['original_CAL_index'],
                  'original_W1_outcome':row['W1_scalar']['outcome'], 'status':'UNMATCHED_NATIVE_REFERENCE'}
        native = row['matched_Native']
        if row['original_CAL_index'] in INDICES:
            case = verified.get(row['scene'])
            if case is not None:
                result['new_Native_outcome'] = case['outcome']
                if case['outcome'] == 'ACCEPTED': native = case['artifact']
                else: result['status']='NEW_NATIVE_REJECTED_REFERENCE_MISSING'
        if row['W1_scalar']['outcome'] != 'ACCEPTED':
            result['status']='ORIGINAL_W1_REJECTED_NOT_REPLACED'; native=None
        elif native is not None:
            result.update(status='TWO_FULL93_LOSSES_PLANNED',Native=native)
            for method,key in [('official_WC','official_WC'),('W1_scalar','W1_scalar')]:
                pairs.append({'scene':row['scene'],'method':method,'reference':native,'candidate':row[key]})
        rows.append(result)
    complete = len(cases)==5 and all(c['status'] in [
        'ACCEPTED_REQUIRES_CPU_FULL_DECODE','TEXT_REJECTED','VIDEO_REJECTED'] for c in cases)
    return {'rows':rows,'pairs':pairs,'new_files':files,'complete_five_attempted':complete,
            'original_denominator':[8,7,1],'matched_accepted_scene_count':len(pairs)//2,
            'unmatched_or_rejected_filled_with_zero':False}


def summarize_scores(pairs, plan):
    expected = [(p['scene'],p['method']) for p in plan['pairs']]
    if [(p['scene'],p['method']) for p in pairs] != expected:
        raise ValueError('Full score list/order must preserve every planned available pair')
    rows=[]
    for row in plan['rows']:
        if row['status']!='TWO_FULL93_LOSSES_PLANNED':continue
        own=[p for p in pairs if p['scene']==row['scene']]
        a,b=[p['score'] for p in own]
        for actual,expected_pair in zip(own,[p for p in plan['pairs'] if p['scene']==row['scene']]):
            if (actual['score']['reference_sha256']!=expected_pair['reference']['sha256']
                    or actual['score']['candidate_sha256']!=expected_pair['candidate']['sha256']):
                raise ValueError('Measured loss reference/candidate identity differs')
        if (a['frames']!=93 or b['frames']!=93 or len(a['pts'])!=93 or len(b['pts'])!=93 or a['pts']!=b['pts']
                or a['reference_sha256']!=b['reference_sha256']
                or any(len(s['frame_distances'])!=93 or not all(math.isfinite(v) for v in s['frame_distances']) for s in [a,b])
                or any(not math.isfinite(s['mean_LPIPS']) or abs(sum(s['frame_distances'])/93-s['mean_LPIPS'])>1e-12 for s in [a,b])):
            raise ValueError('W1/WC complete93 source/mean/PTS differs')
        delta=a['mean_LPIPS']-b['mean_LPIPS']
        frame_delta=[x-y for x,y in zip(a['frame_distances'],b['frame_distances'])]
        rows.append({'scene':row['scene'],'WC_LPIPS':a['mean_LPIPS'],'W1_LPIPS':b['mean_LPIPS'],
                     'WC_minus_W1':delta,'relative_improvement_percent':100*delta/a['mean_LPIPS'] if a['mean_LPIPS']>0 else None,
                     'improved_frames':sum(v>0 for v in frame_delta),'tied_frames':sum(v==0 for v in frame_delta),
                     'degraded_frames':sum(v<0 for v in frame_delta),'frames_are_independent_samples':False})
    values=[r['WC_minus_W1'] for r in rows]
    return {'per_scene':rows,'scene_equal_mean_WC_minus_W1':statistics.mean(values) if values else None,
            'scene_median_WC_minus_W1':statistics.median(values) if values else None,
            'improved_scenes':sum(v>0 for v in values),'tied_scenes':sum(v==0 for v in values),
            'degraded_scenes':sum(v<0 for v in values),'matched_accepted_scene_count':len(rows),
            'original_scene_count':8,'original_W1_accepted':7,'original_W1_rejected':1,
            'reference_gaps_and_rejections':[r for r in plan['rows'] if r['status']!='TWO_FULL93_LOSSES_PLANNED'],
            'full_five_reference_card_completed':plan['complete_five_attempted'],
            'all_seven_must_improve':False,'development_only_not_independent_CONF':True,
            'LPIPS_fidelity_not_physics_or_semantic_quality':True,'clean_speed_claim':False}
