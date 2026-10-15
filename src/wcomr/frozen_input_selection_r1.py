"""Deterministic final-input selection after development and identity-only audit.

Pure preparation kernel: this module does not read server data, choose methods,
write a frozen manifest, or authorize a GPU card.
"""
import copy
import hashlib

KNOWN_METHODS = {
    'NATIVE35', 'NATIVE26', 'NATIVE18',
    'WC_HALF', 'WC_DEFAULT', 'WC_DOUBLE',
    'RA_HALF', 'RA_DEFAULT', 'RA_DOUBLE', 'A_NO_P', 'TABLE_PHASE_H1',
    'FIXED_A', 'FIXED_PLAIN', 'UNIFORM_A', 'UNIFORM_C', 'FRONT_DENSE_A', 'FRONT_DENSE_C',
}


def select(records, local_excluded, protocol, *, development, method_freeze, remote_audit):
    n05, n06 = development['N05'], development['N06']
    if (n05['status'] not in ('N05_CORE66_INDEPENDENTLY_ACCEPTED',
            'N05_CORE66_ACCEPTED_WITH_REJECTIONS_RETAINED')
            or (n05['full_denominator'], n05['formal_denominator']) != (66, 44)
            or n06['status'] not in ('SIMPLE26D_FULL36_INDEPENDENT_TERMINAL_ACCEPTED',
                                    'SIMPLE26D_FULL36_TERMINAL_WITH_REJECTIONS_RETAINED')
            or (n06['full_denominator'], n06['formal_denominator']) != (36, 24)):
        raise ValueError('Independently accepted complete N05 and N06 required')
    methods = method_freeze['method_ids']
    if (len(methods) != 10 or len(set(methods)) != 10
            or not set(methods).issubset(KNOWN_METHODS)
            or not {'NATIVE35', 'A_NO_P', 'TABLE_PHASE_H1', 'FRONT_DENSE_C', 'FRONT_DENSE_A'}.issubset(methods)
            or not any(m.startswith('WC_') for m in methods)
            or not any(m.startswith('RA_') for m in methods)
            or method_freeze['parameters_frozen_from'] != 'DEVELOPMENT_ONLY'
            or method_freeze['final_test_outputs_seen'] is not False):
        raise ValueError('Complete development-only workpoints and strong simple comparators required')
    if (not remote_audit['no_endpoint_or_timing_values_extracted']
            or remote_audit['read_errors']
            or remote_audit['all_registered_GPU_jobs_terminal'] is not True
            or not development['latest_development_observed_unix'] <= method_freeze['freeze_unix']
                <= remote_audit['observed_unix']):
        raise ValueError('New identity-only audit after development/method freeze required')
    categories = protocol['categories_in_order']
    if (categories != ['av', 'human', 'misc', 'robot']
            or protocol['prompts_per_category'] != 2
            or protocol['seeds_in_order'] != [17, 43]):
        raise ValueError('Preserve the registered four-category/two-seed input scope')
    lookup = {r['name']: r for r in records}
    if len(lookup) != len(records):
        raise ValueError('Unique source identities required')
    groups = set()
    for record in records:
        group = tuple(sorted(record['group_members']))
        if not group or record['name'] not in group:
            raise ValueError('Every source must belong to its complete identity group')
        for member in group:
            if member not in lookup or tuple(sorted(lookup[member]['group_members'])) != group:
                raise ValueError('Nonreciprocal or incomplete source groups')
        groups.add(group)
    excluded = set(local_excluded) | set(remote_audit['identity_hits'])
    if not excluded.issubset(lookup):
        raise ValueError('Exclusions must refer to audited benchmark identities')
    for name in list(excluded):
        excluded.update(lookup[name]['group_members'])
    pools = {category: [] for category in categories}
    for group in groups:
        if excluded.intersection(group):
            continue
        representative = min(group)
        record = lookup[representative]
        category = record['category']
        if category not in pools:
            continue
        digest = hashlib.sha256((protocol['salt'] + '|' + representative).encode()).hexdigest()
        pools[category].append((digest, representative, record))
    selected = []
    for category in categories:
        pool = sorted(pools[category], key=lambda x: (x[0], x[1]))
        if len(pool) < 2:
            raise ValueError('Not enough complete unexposed groups; never replace with a seen group')
        for digest, representative, record in pool[:2]:
            selected.append(dict(copy.deepcopy(record), canonical_group_representative=representative,
                                 selection_rank_sha256=digest))
    cases = [dict(id=r['name'] + '_PAPER_COMMON_seed' + str(seed),
                  prompt_id=r['name'], seed=seed, category=r['category'])
             for r in selected for seed in protocol['seeds_in_order']]
    return dict(status='FINAL_INPUT_SELECTION_KERNEL_RESULT_REQUIRES_PHYSICAL_INPUT_BINDING',
        selected_sources=selected, cases=cases, prompt_groups=8, seed_cases=16,
        eligible_group_counts={category: len(pools[category]) for category in categories},
        excluded_group_members=sorted(excluded), method_ids=list(methods),
        no_endpoint_cost_or_rejection_screening=True, recording_or_semantic_independence_proven=False,
        final_physical_input_manifest_written=False, production_CPU_accepted=False,
        GPU_card_selected=False, GPU_submissions=0, SSH_queries=0, ledger_written=False)
