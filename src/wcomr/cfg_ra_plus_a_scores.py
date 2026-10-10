"""Complete scene-level and all-frame fidelity/cost summaries for RA development."""
import math
from statistics import mean, median

NAMES = ['av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632', 'human_199', 'misc_13398218_3840_2160_60fps', 'av_51b45829-502e-4143-9c32-c026bd6ab191']
METHODS = ['WC', 'JOINT_NATIVE', 'RA', 'W1_GLOBAL_1', 'BETA1_GLOBAL_1', 'W1_ONE_PHASE', 'BETA1_ONE_PHASE']


def quantile(values, p):
    ordered=sorted(values);position=p*(len(ordered)-1)
    a,b=math.floor(position),math.ceil(position)
    return ordered[a]+(ordered[b]-ordered[a])*(position-a)


def summarize(pairs, references, costs):
    if [r['sample_name'] for r in references]!=NAMES:
        raise ValueError('All four original Native reference slots required')
    available=[r['sample_name'] for r in references if r['outcome']=='ACCEPTED']
    if any(r['outcome'] not in ('ACCEPTED','TEXT_REJECTED','VIDEO_REJECTED') for r in references):
        raise ValueError('Original reference outcomes must remain explicit')
    expected=[(n,m) for n in available for m in METHODS]
    if [(p['sample_name'],p['method']) for p in pairs]!=expected:
        raise ValueError('Complete available seven-method fidelity matrix required')
    if [(c['sample_name'],c['method']) for c in costs]!=[(n,m) for n in NAMES for m in METHODS+['NATIVE']]:
        raise ValueError('All32 actual method/reference cost slots required')
    for c in costs:
        wall=c['instrumented_pipeline_wall_seconds']
        if type(wall) not in (int,float) or not math.isfinite(wall) or wall<0:
            raise ValueError('Finite actual instrumented cost required')
        if type(c['complete_branch_calls']) is not int or not 0<=c['complete_branch_calls']<=72:
            raise ValueError('Actual complete-branch count differs')
    rows=[]
    for name in available:
        group=[p for p in pairs if p['sample_name']==name]
        base=group[0];ref=next(r for r in references if r['sample_name']==name)['artifact']
        for p in group:
            s=p['score'];values=s['frame_distances']
            if (p['reference']['sha256']!=ref['sha256'] or p['reference']!=base['reference']
                    or s['reference_sha256']!=p['reference']['sha256']
                    or s['candidate_sha256']!=p['candidate']['sha256']
                    or s['frames']!=93 or len(values)!=93 or len(s['pts'])!=93
                    or len({tuple(x) for x in s['pts']})!=93 or s['pts']!=base['score']['pts']
                    or any(type(v) not in (int,float) or not math.isfinite(v) for v in values)
                    or type(s['mean_LPIPS']) not in (int,float) or not math.isfinite(s['mean_LPIPS'])
                    or not math.isclose(sum(values)/93,s['mean_LPIPS'],rel_tol=1e-12,abs_tol=1e-12)):
                raise ValueError('Complete Native-relative all93 score source/PTS/mean differs')
        baseline_cost=next(c for c in costs if (c['sample_name'],c['method'])==(name,'WC'))
        for p in group:
            s=p['score'];bs=base['score'];delta=[a-b for a,b in zip(bs['frame_distances'],s['frame_distances'])]
            cost=next(c for c in costs if (c['sample_name'],c['method'])==(name,p['method']))
            difference=bs['mean_LPIPS']-s['mean_LPIPS']
            time_difference=baseline_cost['instrumented_pipeline_wall_seconds']-cost['instrumented_pipeline_wall_seconds']
            rows.append({'sample_name':name,'method':p['method'],'mean_LPIPS':s['mean_LPIPS'],
                'WC_minus_method_LPIPS':difference,
                'relative_fidelity_improvement_percent':100*difference/bs['mean_LPIPS'] if bs['mean_LPIPS']>0 else None,
                'improved_frames':sum(v>0 for v in delta),'degraded_frames':sum(v<0 for v in delta),
                'tied_frames':sum(v==0 for v in delta),'frame_count':93,
                'paired_difference_quantiles_type7':{str(q):quantile(delta,q) for q in (0,.1,.25,.5,.75,.9,1)},
                'contiguous_frame_bin_means':[{'frames_0_based':[a,b],
                    'mean_WC_minus_method':sum(delta[a:b+1])/31} for a,b in ((0,30),(31,61),(62,92))],
                'complete_branch_calls':cost['complete_branch_calls'],
                'instrumented_pipeline_wall_seconds':cost['instrumented_pipeline_wall_seconds'],
                'WC_minus_method_instrumented_wall_seconds':time_difference,
                'descriptive_same_run_fidelity_and_instrumented_time_both_improve':difference>0 and time_difference>0,
                'clean_speed_claim':False,'frames_are_independent_samples':False})
    aggregate=[]
    for method in METHODS:
        own=[r for r in rows if r['method']==method];values=[r['WC_minus_method_LPIPS'] for r in own]
        aggregate.append({'method':method,'matched_scenes':len(own),
            'scene_equal_mean_LPIPS':mean(r['mean_LPIPS'] for r in own) if own else None,
            'scene_equal_mean_WC_minus_method':mean(values) if values else None,
            'scene_median_WC_minus_method':median(values) if values else None,
            'improved_scenes':sum(v>0 for v in values),'degraded_scenes':sum(v<0 for v in values),
            'tied_scenes':sum(v==0 for v in values)})
    result = {'per_scene_method':rows,'scene_equal_aggregates':aggregate,
        'original_scenes':4,'original_method_paths':28,'original_reference_slots':4,
        'accepted_reference_scenes':len(available),'scored_pairs':len(pairs),
        'reference_gaps_or_rejections':[{'sample_name':r['sample_name'],'outcome':r['outcome']} for r in references if r['outcome']!='ACCEPTED'],
        'missing_scores_filled_with_zero':False,'fidelity_not_semantic_physics_quality':True,
        'not_matched_time_or_call_count':True,'clean_speed_claim':False,
        'development_exposure_not_independent_CONFIRMATION':True}

    contrasts = [('JOINT_NATIVE','WC'),('RA','WC')]
    contrasts += [(m,'RA') for m in METHODS[3:]]
    contrasts += [('W1_GLOBAL_1','BETA1_GLOBAL_1'),('W1_ONE_PHASE','BETA1_ONE_PHASE'),
                  ('W1_ONE_PHASE','W1_GLOBAL_1'),('BETA1_ONE_PHASE','BETA1_GLOBAL_1')]
    result['registered_contrasts'] = []
    for candidate, baseline in contrasts:
        comparison = []
        for name in available:
            own = next(p for p in pairs if (p['sample_name'],p['method']) == (name,candidate))
            base = next(p for p in pairs if (p['sample_name'],p['method']) == (name,baseline))
            delta = [b-a for b,a in zip(base['score']['frame_distances'],own['score']['frame_distances'])]
            own_cost = next(c for c in costs if (c['sample_name'],c['method']) == (name,candidate))
            base_cost = next(c for c in costs if (c['sample_name'],c['method']) == (name,baseline))
            comparison.append({'sample_name':name,
                'baseline_minus_candidate_LPIPS':base['score']['mean_LPIPS']-own['score']['mean_LPIPS'],
                'improved_frames':sum(d>0 for d in delta),'degraded_frames':sum(d<0 for d in delta),
                'tied_frames':sum(d==0 for d in delta),
                'baseline_minus_candidate_instrumented_seconds':base_cost['instrumented_pipeline_wall_seconds']-own_cost['instrumented_pipeline_wall_seconds'],
                'frames_are_independent_samples':False,'clean_speed_claim':False})
        result['registered_contrasts'].append({'candidate':candidate,'baseline':baseline,'per_scene':comparison,
            'scene_equal_mean_baseline_minus_candidate':mean(c['baseline_minus_candidate_LPIPS'] for c in comparison) if comparison else None,
            'matched_scenes':len(comparison),'development_not_confirmation':True})
    return result
