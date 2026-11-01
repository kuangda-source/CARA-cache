"""Prospective V1 parent/source coverage from the grid and legal actions only."""
from itertools import combinations

from .cara_fast_spec_r1 import digest, policy_from_mask, uniform_mask


def calibration_design(schedule, profile, fit_members):
    if schedule['actual_updates'] != 36 or profile.horizon != 36 or len(set(fit_members)) != 2:
        raise ValueError('Original36 grid and two fixed FIT members required')
    n = profile.horizon
    parents = []
    index_grid = dict(schedule, sigmas=list(range(n, -1, -1)))
    for budget in (19,22):
        for rule,grid in (('SIGMA_FARTHEST',schedule),('UPDATE_FARTHEST',index_grid)):
            dense,_ = uniform_mask(grid,profile,budget)
            policy = policy_from_mask(profile,dense)
            parents.append(dict(id='K'+str(budget)+'_'+rule, D=budget, rule=rule,
                dense_steps=dense, policy=policy, states=[]))
    assert len({p['policy']['fingerprint'] for p in parents}) == 4
    candidates = {};groups = {}
    sigmas = schedule['sigmas']
    for parent in parents:
        past = [];states = []
        for t in range(1,n+1):
            if t in parent['dense_steps']:
                past.append(t)
            else:
                a,b = past[-2:]
                state = dict(t=t,a=a,b=b,sigma=sigmas[t-1],
                    features=[sigmas[t-1],abs(sigmas[t-1]-sigmas[b-1]),abs(sigmas[b-1]-sigmas[a-1])])
                states.append(state)
                groups.setdefault((t,b),[]).append((parent['id'],state))
        candidates[parent['id']] = states
    chosen = {p['id']:{} for p in parents}
    # Reserve up to half the slots for exact stage/age matches with different
    # previous-source gaps. This selection sees no measured error or video.
    for key,values in sorted(groups.items()):
        for (left,a),(right,b) in combinations(values,2):
            if a['a'] == b['a'] or len(chosen[left]) >= 4 or len(chosen[right]) >= 4:
                continue
            chosen[left][a['t']] = a;chosen[right][b['t']] = b
    for parent in parents:
        selected = chosen[parent['id']]
        while len(selected) < min(8,len(candidates[parent['id']])):
            remaining = [r for r in candidates[parent['id']] if r['t'] not in selected]
            def distance(row):
                if not selected:
                    return 0.
                return min(sum((x-y)**2 for x,y in zip(row['features'],other['features']))
                           for other in selected.values())
            row = min(remaining,key=lambda r:(-distance(r),r['t']))
            selected[row['t']] = row
        parent['states'] = [selected[t] for t in sorted(selected)]
    selected_groups = {}
    for parent in parents:
        for row in parent['states']:
            selected_groups.setdefault((row['t'],row['b']),set()).add(row['a'])
    contrasts = [dict(t=t,b=b,previous_a=sorted(values)) for (t,b),values in sorted(selected_groups.items()) if len(values)>1]
    result = dict(schema='CARA_SOURCE_LIFECYCLE_CALIBRATION_DESIGN_R1',
        parents=parents, FIT=list(fit_members), CHECK=[], seed=0, parent_paths=8,
        targets_per_parent_max=8, same_state_shadow_D_labels=64,
        parent_solver_pairs=8*36, additional_Dense_pairs=64, total_model_pairs=352,
        held_out_group='entire_parent_mask_across_both_FIT', random_adjacent_split=False,
        exact_stage_age_gap_contrasts=contrasts, selection_inputs='sigma_grid_and_legal_actions_only',
        F19_initialization=False, measured_errors_used=False, GPU_authorized=False)
    result['scope_sha256'] = digest(result)
    return result
