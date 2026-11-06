"""Offline initialization sensitivity on accepted S risks; no new S selection."""
import math

from .cara_fast_spec_r1 import policy_from_mask, profile_from

OBJECTIVES = ('BR', 'DIAG', 'CFG')
TARGETS = set(range(8, 36)) - {24}


def histories(policy):
    past, rows = [], []
    for step, action in enumerate(policy['actions'], 1):
        if action == 'D':
            past.append(step)
        else:
            if action != 'C' or len(past) < 2:
                raise ValueError('Pure C and two strictly past true anchors required')
            rows.append((step, past[-2], past[-1]))
    return rows


def candidates(profile, base):
    protected = set(profile.protected_dense) | {24}
    if len(base) != 19 or base != sorted(set(base)) or not protected <= set(base):
        raise ValueError('Fixed ordered 19D initialization with original protection required')
    baseline = policy_from_mask(profile, base)
    histories(baseline)
    rows = []
    for remove in sorted(set(base) - protected):
        for add in sorted(TARGETS - set(base)):
            dense = sorted((set(base) - {remove}) | {add})
            try:
                policy = policy_from_mask(profile, dense)
            except ValueError:
                continue
            rows.append(dict(remove=remove, add=add, dense=dense,
                             policy_fingerprint=policy['fingerprint'],
                             history=[list(row) for row in histories(policy)]))
    return baseline, rows


def rank(risk, rows, base):
    ranked = sorted((dict(row, score=risk[row['add']] - risk[row['remove']]) for row in rows),
                    key=lambda row: (-row['score'], row['remove'], row['add']))
    best = ranked[0] if ranked and ranked[0]['score'] > 0 else None
    return dict(dense=list(base) if best is None else best['dense'],
                remove=None if best is None else best['remove'],
                add=None if best is None else best['add'],
                score=0.0 if best is None else best['score']), ranked


def audit(profile_value, baselines, risk, original_choices, original_candidate_count):
    """Reproduce F19 first, then apply exactly one swap to the fixed Uniform19."""
    if set(baselines) != {'F19_C', 'Uniform19_C'} or set(risk) != set(OBJECTIVES):
        raise ValueError('Exactly the two planned initializations and three original objectives required')
    if any(set(values) != TARGETS or any(type(v) not in (float, int) or not math.isfinite(v) or v < 0
                                       for v in values.values()) for values in risk.values()):
        raise ValueError('All 27 finite original risks required; no fill or interpolation')
    profile = profile_from(profile_value)
    if profile.horizon != 36 or profile.max_source_age != 28:
        raise ValueError('Original 36-update production grammar required')
    origins = {}
    for name, base in baselines.items():
        policy, rows = candidates(profile, base)
        choices, scores = {}, {}
        for objective in OBJECTIVES:
            choices[objective], scores[objective] = rank(risk[objective], rows, base)
            choices[objective]['policy_fingerprint'] = policy_from_mask(
                profile, choices[objective]['dense'])['fingerprint']
        origins[name] = dict(initial_dense=base, initial_policy_fingerprint=policy['fingerprint'],
                             candidate_count=len(rows), candidates=rows, choices=choices, rankings=scores,
                             all_objectives_same_mask=len({tuple(c['dense']) for c in choices.values()}) == 1)
    original = origins['F19_C']
    if original['candidate_count'] != original_candidate_count:
        raise ValueError('Original accepted candidate denominator differs')
    for objective in OBJECTIVES:
        if original['choices'][objective] != original_choices[objective]:
            raise ValueError('Original accepted F19 decision was not reproduced exactly')
    old_histories = {tuple(h) for row in original['candidates'] for h in row['history']}
    for base in baselines.values():
        old_histories.update(histories(policy_from_mask(profile, base)))
    new_histories = {tuple(h) for row in origins['Uniform19_C']['candidates'] for h in row['history']}
    return dict(status='ACCEPTED_S_RISK_INITIALIZATION_SENSITIVITY_CPU_ONLY', origins=origins,
                original_F19_reproduced_exact=True,
                cross_initialization={j:dict(same_mask=original['choices'][j]['dense'] == origins['Uniform19_C']['choices'][j]['dense'],
                    dense_symmetric_difference=sorted(set(original['choices'][j]['dense']) ^ set(origins['Uniform19_C']['choices'][j]['dense'])))
                    for j in OBJECTIVES},
                additional_selector_histories=[list(h) for h in sorted(new_histories - old_histories)],
                uniform_parent_risks_collected=False, original_parent_risks_reused=True,
                new_selector_history_CPU_accepted=False, original_S_freeze_changed=False,
                endpoint_results_used=False, endpoint_gain_established=False,
                new_method_recipe_frozen=False, GPU_dispatch_ready=False, GPU_submissions=0)
