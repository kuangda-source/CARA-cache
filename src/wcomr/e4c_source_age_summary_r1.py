"""Retain all24 points and matched source pairs; no endpoint-quality inference."""
import math


def summarize(state, audited):
    reduced = {(p['event'], p['source'], p['age']): p for p in audited['actual_age_points_reduced']}
    points = []
    for request in state['requests']:
        for row in request['paths']:
            for event in row['origins']:
                for branch in event['branches']:
                    for p in branch['age_points']:
                        key = (event['event']['id'], branch['source'], p['age'])
                        q = reduced[key]
                        h = p['actual_source_and_decision_history']
                        d = h['source_policy']['decision']
                        times = (p['actual_C_full_pair_seconds'], p['research_teacher_full_pair_seconds'])
                        if any(not math.isfinite(v) or v < 0 for v in times):
                            raise ValueError('Finite nonnegative full-pair research timing required')
                        if (h['action'] != 'CC' or h['true_D_before'] != h['true_D_after']
                                or h['working_source_ages'] != [p['age']]*2
                                or not p['teacher_state_restored_before_actual_C']
                                or p['teacher_updates_final_deployment_anchors']):
                            raise ValueError('Actual same-state/source teacher invariant differs')
                        points.append({**q, 'sample': request['sample_name'],
                            'birth_step': event['event']['birth_step'], 'phase': event['event']['phase'],
                            'step': p['step'], 'sigma': p['sigma'], 'timestep': p['timestep'],
                            'effective_beta': p['effective_scalar_beta'], 'fitted_beta': p['fitted_beta_from_actual_D_statistics'],
                            'A_status': p['A_status'], 'shared_alpha': p['actual_shared_alpha'],
                            'true_D_steps_before': p['true_D_steps_before'],
                            'actual_C_full_pair_seconds': times[0], 'research_teacher_full_pair_seconds': times[1],
                            'cost_boundary': p['cost_boundary'],
                            'forced_decision_with_unforced_proxy_candidates': d,
                            'candidate_state_sha256': p['candidate_latent_sha256'],
                            'offline_C4_not_online_feasible_action': True})
    if len(points) != 24 or len(reduced) != 24:
        raise ValueError('All24 registered point values required')
    comparisons = []
    for event in dict.fromkeys(p['event'] for p in points):
        for age in (1, 2, 4):
            p, d = [next(v for v in points if (v['event'], v['source'], v['age']) == (event, source, age))
                    for source in ('P', 'D')]
            comparisons.append({'event': event, 'age': age, 'P_own_state_guided_MSE': p['guided_MSE'],
                'D_own_state_guided_MSE': d['guided_MSE'], 'difference_P_minus_D': p['guided_MSE']-d['guided_MSE'],
                'ratio_P_over_D': p['guided_MSE']/d['guided_MSE'] if d['guided_MSE'] else None,
                'subsequent_latents_are_each_arms_own_states_not_identical': True})
    return {'points': points, 'matched_birth_age_comparisons': comparisons,
        'registered_events': 4, 'registered_points': 24, 'matched_P_D_age_pairs': 12,
        'independent_scenes': 2, 'seeds': [0], 'events_are_not_independent_scene_samples': True,
        'no_arbitrary_MSE_quality_cutoff': True, 'local_error_is_not_video_quality_or_cache_lifetime_proof': True,
        'diagnostic_timings_are_not_clean_latency': True}
