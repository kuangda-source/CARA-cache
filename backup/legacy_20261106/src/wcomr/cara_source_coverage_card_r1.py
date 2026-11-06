"""C1 finite endpoint experiment and measured-history whole-scope quotation."""
import copy
import math

from .cara_fast_spec_r1 import digest, profile_from, policy_from_mask, uniform_mask
from .cara_source_lifecycle_p1_plan_r1 import BASELINES, SEARCH_CONFIG


def evaluation_view(pool, ids, name):
    candidates = []
    for key in ids:
        source = next(c for c in pool['candidates'] if c['candidate_id'] == key)
        row = {k:copy.deepcopy(source[k]) for k in ('candidate_id','dense_steps','policy','origins')}
        row['generator_candidate_id'] = row['candidate_id']
        row['candidate_id'] = row['policy']['fingerprint']
        candidates.append(row)
    payload = dict(schema='CARA_SOURCE_COVERAGE_EVALUATION_VIEW_R1', name=name,
        source_pool_sha256=pool['pool_sha256'], exact_D=pool['exact_D'],
        candidates=candidates, endpoint_evaluated=False, GPU_dispatch_ready=False)
    return dict(payload, pool_sha256=digest(payload))


def balanced_eight(pool):
    """Keep all neutral controls, then round-robin phase/rank before any scores."""
    selected = []
    for rank in (1, 2, 3):
        for tilt in pool['tilts']:
            matches = [c['candidate_id'] for c in pool['candidates']
                       if any(o['tilt'] == tilt and o['rank'] == rank for o in c['origins'])]
            for key in matches:
                if key not in selected:
                    selected.append(key)
    neutral = [c['candidate_id'] for c in pool['candidates']
               if any(o['tilt'] == 0 for o in c['origins'])]
    required = list(dict.fromkeys(selected[:4]+neutral))
    result = (required+[key for key in selected if key not in required])[:8]
    if len(result) != 8 or not set(neutral) <= set(result):
        raise ValueError('Eight distinct candidates including the three neutral controls required')
    return result


def build(parent, bundle):
    profile = profile_from(parent['profile'])
    views = {}
    for budget in (19, 22):
        two, single = (bundle['pools'][f'{m}_{budget}'] for m in ('two', 'single'))
        for pool in (two, single):
            if digest({k:v for k,v in pool.items() if k != 'pool_sha256'}) != pool['pool_sha256']:
                raise ValueError('Original CPU candidate pool changed')
        main_ids, single_ids = balanced_eight(two), balanced_eight(single)
        neutral = [c['candidate_id'] for c in two['candidates'] if any(o['tilt'] == 0 for o in c['origins'])]
        phase = [next(c['candidate_id'] for c in two['candidates']
            if any(o['tilt'] == tilt and o['rank'] == 1 for o in c['origins'])) for tilt in (0., -2., 4.)]
        if len(set(phase)) != 3 or not set(phase+neutral) <= set(main_ids):
            raise ValueError('Matched3 phase/neutral controls must be contained in the main8 cohort')
        for name, pool, ids in (('main8', two, main_ids), ('single8', single, single_ids),
                                ('neutral3', two, neutral), ('phase3', two, phase)):
            views[f'{name}-K{budget}'] = evaluation_view(pool, ids, f'{name}-K{budget}')
    roles = {name:copy.deepcopy(parent['roles'][name]) for name in BASELINES if name != 'UNIFORM22_C'}
    roles['UNIFORM22_C'] = dict(kind='policy', requested_steps=35,
        policy=policy_from_mask(profile, uniform_mask(parent['schedule'], profile, 22)[0]))
    controls = [dict(id='warm-Native', kind='native', member=parent['FIT'][0], timing='DIAGNOSTIC'),
        dict(id='warm-Uniform19', kind='policy', role='UNIFORM19_C', member=parent['FIT'][0], timing='DIAGNOSTIC')]
    for i, member in enumerate(parent['FIT']+parent['CHECK']):
        controls.append(dict(id=f'control-allD-{i}', kind='allD', member=member,
            timing='DIAGNOSTIC', compare_to='NATIVE35'))
    for i, member in enumerate(parent['FIT']):
        for role in ('NATIVE35', 'UNIFORM19_C'):
            controls.append(dict(id=f'control-OFF-{role}-{i}', kind=roles[role]['kind'], role=role,
                member=member, timing='OFF', compare_to=role))
    card = dict(schema='CARA_SOURCE_COVERAGE_C1_SCOPE_R1',
        state='CPU_PREPARATION_NO_GPU_AUTHORITY', parent_scope_sha256=parent['scope_sha256'],
        profile=copy.deepcopy(parent['profile']), schedule=copy.deepcopy(parent['schedule']),
        settings=copy.deepcopy(parent['roles']['ALLD']['settings']), inputs=copy.deepcopy(parent['inputs']),
        FIT=list(parent['FIT']), CHECK=list(parent['CHECK']), views=views, roles=roles,
        baseline_roles=list(BASELINES), D_budgets=[19,22], search_config=vars(SEARCH_CONFIG),
        controls=controls, scientific_positions=dict(fresh_baselines=24, candidate_FIT=64,
            selected_view_CHECK=16, search_FIT_max=48, selected_search_CHECK=4, controls=10),
        semantic_positions=166, physical_paths_upper=166, physical_model_pairs_upper=5976,
        candidate_FIT_cohorts=32, internal_FIT_queries_upper=56, internal_metric_pairs_upper=112,
        formal_quality_positions=60, final_quality_roles=15, postrelease_new_metric_pairs_upper=36,
        identity_controls=12, Uniform_search_baseline_RGB_bridges=4,
        search_cache='ISOLATED_FROM_CANDIDATE_AND_BASELINE_CACHES',
        search_cap='main8_direct_operations_plus_half_common_reference_and_control_cost',
        comparison='SAME_COST_CAP_AND_MAX12_QUERIES_REPORT_ACTUAL_SPEND',
        old_CHECK_exposed=True, original_frozen_results_unchanged=True,
        protected_final_reserve_accessed=False, GPU_authorized=False, ledger_permission=False,
        GPU_submissions=0, ledger_written=False)
    card['scope_sha256'] = digest(card)
    validate(card)
    return card


def validate(card):
    if (card['schema'] != 'CARA_SOURCE_COVERAGE_C1_SCOPE_R1'
            or digest({k:v for k,v in card.items() if k != 'scope_sha256'}) != card['scope_sha256']
            or card['semantic_positions'] != sum(card['scientific_positions'].values())
            or card['semantic_positions'] != 166 or card['physical_paths_upper'] != 166
            or card['physical_model_pairs_upper'] != 36*166
            or card['search_config'] != vars(SEARCH_CONFIG)
            or card['search_cache'] != 'ISOLATED_FROM_CANDIDATE_AND_BASELINE_CACHES'
            or card['protected_final_reserve_accessed'] is not False):
        raise ValueError('Complete immutable C1 scope and isolated fair-search cache required')
    profile = profile_from(card['profile'])
    for name, view in card['views'].items():
        if (digest({k:v for k,v in view.items() if k != 'pool_sha256'}) != view['pool_sha256']
                or len(view['candidates']) != (8 if name.startswith(('main8', 'single8')) else 3)):
            raise ValueError('Matched candidate quotas and immutable views required')
        for row in view['candidates']:
            policy = policy_from_mask(profile, row['dense_steps'])
            if policy != row['policy'] or row['candidate_id'] != policy['fingerprint']:
                raise ValueError('Actual production policy differs from its candidate identity')
    return profile


def quote(card, summary, original_analysis):
    """Use accepted A6000 operation costs, without reading a live ledger."""
    validate(card)
    ops = summary['operations']
    def maximum(prefix):
        values = [v['charged_seconds'] for k,v in ops.items() if k.startswith(prefix)]
        if not values:
            raise ValueError('Original measured timing cohort missing: '+prefix)
        return max(values)
    rates = dict(K19=maximum('fit-stage-K19'), K22=maximum('fit-stage-K22'),
        Native=maximum('baseline-NATIVE35'), F19_C=maximum('baseline-F19_C'),
        F19_A1=maximum('baseline-F19_A1'), BUDGET=maximum('baseline-BUDGET'),
        score=maximum('score-'))
    # Baseline masks and controls are charged separately from calibration.
    baselines = 4*sum(rates[k] for k in ('Native','K19','K22','F19_C','F19_A1','BUDGET'))
    controls = maximum('warm-Native')+maximum('warm-Uniform19')+4*rates['Native']+2*(rates['Native']+rates['K19'])
    components = dict(fresh_baselines=baselines, warm_and_controls=controls,
        candidate_FIT=32*(rates['K19']+rates['K22']),
        selected_view_CHECK=8*(rates['K19']+rates['K22']),
        fair_search_FIT_upper=24*(rates['K19']+rates['K22']),
        selected_search_CHECK=2*(rates['K19']+rates['K22']),
        internal_CPU_held_allocation=56*rates['score'],
        model_load_broker_admission=900., stop_release_reserve=600.)
    components['variation_margin'] = .15*sum(components.values())
    forecast = sum(components.values())/3600
    hard = math.ceil(forecast)
    return dict(schema='CARA_SOURCE_COVERAGE_C1_HISTORY_QUOTE_R1', scope_sha256=card['scope_sha256'],
        host='two_card', device='A6000 GPU-cebf7119-cf03-23b9-e192-cd196332b704',
        components_seconds=components, measured_max_rates_seconds=rates,
        forecast_GPUh=forecast, proposed_hard_GPUh=hard,
        output_volume_GiB=80, output_low_water_GiB=8, independent_journal_MiB=48,
        historical_original_GPUh=original_analysis['original_guardian_GPUh'],
        source_summary_content_sha256=digest(summary), historical_balance_not_live=True,
        search_query_bounds=dict(path_seconds=360.,FIT_score_seconds=180.,overhead_seconds=30.),
        postrelease_CPU=dict(max_new_pairs=36, cpus=2,memory_GiB=8,swap=False,wall_seconds=7200),
        GPU_authorized=False, ledger_permission=False, live_funds_verified=False,
        production_CPU_and_dispatch_binding_accepted=False, GPU_submissions=0, ledger_written=False)
