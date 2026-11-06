"""Accept only the local bounded-search component with synthetic RGB objectives."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from wcomr.cara_budget_search_r1 import SearchConfig, search
from wcomr.cara_fast_binding_r2 import load_card
from wcomr.cara_fast_spec_r1 import digest, profile_from


def check():
    suite = unittest.defaultTestLoader.discover(str(ROOT/'tests'), pattern='test_cara_budget_search_r1.py')
    tested = unittest.TextTestRunner(verbosity=2).run(suite)
    if not tested.wasSuccessful() or tested.testsRun != 11 or tested.skipped:
        raise ValueError('Complete local component controls required')
    sources = ['src/wcomr/cara_budget_search_r1.py', 'tests/test_cara_budget_search_r1.py',
        'scripts/check_cara_budget_search_component_r1.py', 'src/wcomr/cara_fast_binding_r2.py',
        'src/wcomr/cara_fast_spec_r1.py', 'src/wcomr/policy_generator_r1/interval_grammar.py',
        'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json',
        'plans/cara_next_stage_20261028/mainline/r2/BUDCACHE_ADAPTATION_R1.json']
    source_sha = {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sources}
    card = load_card(ROOT, 'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json')
    profile = profile_from(card['profile'])
    context = dict(CPU_SYNTHETIC_ONLY=True, parent_scope_sha256=card['scope_sha256'],
        source_sha256=source_sha, objective='constant synthetic value1 per FIT; no RGB/model')
    requests = []

    def evaluate(request):
        claimed = request['request_sha256']
        if digest({k:v for k,v in request.items() if k != 'request_sha256'}) != claimed:
            raise ValueError('Query identity differs')
        if (request['policy']['counts'] != dict(D=19, A=0, C=17)
                or request['FIT_members'] != card['FIT'] or request['generation_seed'] != 0):
            raise ValueError('Synthetic query changed registered scope')
        requests.append(claimed)
        return dict(request_sha256=claimed, rows=[dict(member=m, status='COMPLETE', RGB_MSE=1.0)
            for m in request['FIT_members']])

    result = search(card['schedule'], profile, SearchConfig(seed=42, max_evaluations=301),
        fit_members=card['FIT'], context_sha256=digest(context), evaluate=evaluate)
    if (result['termination'] != 'CONFIGURED_SEARCH_FINISHED' or len(requests) != 301
            or result['requested_endpoint_paths'] != 602
            or result['best_complete_candidate']['policy_fingerprint'] != card['roles']['UNIFORM19_C']['policy']['fingerprint']):
        raise ValueError('Complete synthetic controller or original Uniform19 initialization differs')
    trace = result.pop('queries')
    result.update(query_trace_sha256=digest(trace),
        initial_dense=trace[0]['dense'], query_identity_sequence_sha256=digest(requests))
    return dict(schema='CARA_BUDCACHE_STYLE_LOCAL_COMPONENT_CPU_R1',
        status='BOUNDED_SEARCH_COMPONENT_CPU_ACCEPTED_PRODUCTION_EVALUATOR_PENDING',
        observed_unix=time.time(), python_version=platform.python_version(),
        CPU_fixture_only=True, source_sha256=source_sha, context=context,
        tests_run=tested.testsRun, tests_passed=tested.testsRun,
        controlled_failure_cases=8, original_Uniform19_policy_exact=True,
        search_can_leave_initial_single_swap_neighborhood=True,
        original_grid_profile_and_FIT_bound=True, synthetic_controller=result,
        actual_model_calls=0, actual_generated_videos=0, actual_GPU_submissions=0,
        new_reserved_GPUh=0, production_evaluator_accepted=False,
        durable_original_query_recovery_accepted=False, dual_host_production_CPU_accepted=False,
        actual_GPU_query_cap_frozen=False, whole_GPU_quote_frozen=False,
        whole_GPU_card_accepted=False, GPU_dispatch_ready=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Fresh receipt required')
    result = check()
    with args.output.open('x') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({k:result[k] for k in ('status', 'tests_passed', 'actual_model_calls', 'actual_GPU_submissions')}))


if __name__ == '__main__':
    main()
