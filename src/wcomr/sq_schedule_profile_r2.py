"""S-FAST19 uses the frozen production profile, not an old scout default.

D24 remains an explicit S design restriction because labels exclude step24.
It is not relabelled as a physical production requirement. Risk moments and
normalization are inherited unchanged; every objective uses the same grammar.
"""
from .policy_generator_r1.interval_grammar import Edge, Profile, compile_policy, digest
from .sq_risk_r1 import F19, TARGETS, aggregate, choose


def pure_C_policy(profile, dense):
    if not isinstance(profile, Profile) or sorted(set(dense)) != list(dense):
        raise ValueError('Frozen production profile and ordered unique D mask required')
    if len(dense) != 19 or 24 not in dense:
        raise ValueError('Common 19D budget and explicit S D24 design restriction required')
    edges = [Edge(start, end) for start, end in zip(dense, list(dense[1:])+[profile.horizon+1])]
    return compile_policy(profile, edges)


def candidate_set(profile, *, supports_history=None):
    base = pure_C_policy(profile, list(F19))
    protected = set(profile.protected_dense) | {24}
    rows = []
    for remove in sorted(set(F19)-protected):
        for add in sorted(set(TARGETS)-set(F19)):
            dense = sorted((set(F19)-{remove}) | {add})
            try:
                policy = pure_C_policy(profile, dense)
            except ValueError:
                continue
            past = []; histories = []
            for step, action in enumerate(policy['actions'], 1):
                if action == 'D':
                    past.append(step)
                else:
                    histories.append((step, past[-2], past[-1]))
            if supports_history is not None and not all(supports_history(*h) for h in histories):
                continue
            rows.append(dict(remove=remove, add=add, dense=dense, history=[list(h) for h in histories],
                             policy_fingerprint=policy['fingerprint']))
    return dict(base_policy_fingerprint=base['fingerprint'], candidates=rows,
                production_profile_fingerprint=profile.fingerprint,
                maximum_age=profile.max_source_age, production_protected=list(profile.protected_dense),
                S_extra_protected=[24], history_support_checked=supports_history is not None,
                real_parent_moments_complete=False, GPU_ready=False)


def plans_from_moments(rows, profile, *, baselines, execution_identity, propagation, supports_history):
    """Require the complete cohort and the same admissible baseline grammar."""
    if set(baselines) != {'F19_C', 'Uniform19_C', 'time_prior_C'} or baselines['F19_C'] != list(F19):
        raise ValueError('Explicit F19, Uniform19 and frozen time-prior masks required')
    policies = {name:pure_C_policy(profile, dense) for name,dense in baselines.items()}
    risk = aggregate(rows, prompts=('av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632','human_199'),
                     parent_weights={'Shared25-C':.5,'F19-C':.5}, propagation=propagation)
    common = candidate_set(profile, supports_history=supports_history)
    chosen = choose(risk, common['candidates'], execution_identity=execution_identity)
    for name, choice in chosen['choices'].items():
        policies['S_'+name+'19'] = pure_C_policy(profile, choice['dense'])
    aliases = {}
    for name, policy in policies.items():
        key = digest([execution_identity, policy['actions'], policy['shared_alpha']])
        aliases.setdefault(key, []).append(name)
    return dict(policies=policies, execution_equivalence=aliases, common_candidates=common,
                risk=risk, choices=chosen['choices'], scores=chosen['candidate_scores'],
                parent_local_risk_is_not_endpoint_marginal=True, GPU_ready=False)
