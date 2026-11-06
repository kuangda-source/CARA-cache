"""Local persistence/recovery acceptance; no GPU or model entry exists here."""
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
from wcomr.cara_budget_search_r1 import SearchConfig
from wcomr.cara_budget_search_journal_r1 import run_search
from wcomr.cara_fast_binding_r2 import load_card
from wcomr.cara_fast_spec_r1 import digest, profile_from


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check(artifacts):
    original_ref = 'reports/cara_fast_BudCache_search_component_CPU_r1_20261030.json'
    original = json.loads((ROOT/original_ref).read_bytes())
    for name, expected in original['source_sha256'].items():
        if sha(ROOT/name) != expected:
            raise ValueError('Original accepted controller component changed: '+name)
    suite = unittest.defaultTestLoader.discover(str(ROOT/'tests'), pattern='test_cara_budget_search_journal_r1.py')
    tested = unittest.TextTestRunner(verbosity=2).run(suite)
    if not tested.wasSuccessful() or tested.testsRun != 14 or tested.skipped:
        raise ValueError('Complete query journal controls required')
    artifacts.mkdir(mode=0o700)
    card = load_card(ROOT, 'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json')
    context = dict(CPU_fixture_only=True, original_component_receipt_sha256=sha(ROOT/original_ref),
        objective='constant synthetic loss1; no RGB/model')
    arguments = dict(schedule=card['schedule'], profile=profile_from(card['profile']),
        config=SearchConfig(42, 4), fit_members=card['FIT'], context_sha256=digest(context))
    calls = []

    def evaluate(request):
        calls.append(request['query_id'])
        return dict(request_sha256=request['request_sha256'], rows=[
            dict(member=m, status='COMPLETE', RGB_MSE=1.0) for m in request['FIT_members']])

    first = run_search(artifacts/'queries', **arguments, evaluate=evaluate, create=True, allow_new_queries=True)
    before = {p.name:sha(p) for p in (artifacts/'queries').iterdir()}
    recovered = run_search(artifacts/'queries', **arguments, evaluate=evaluate)
    after = {p.name:sha(p) for p in (artifacts/'queries').iterdir()}
    if (calls != [1,2,3,4] or before != after or first['queries'] != recovered['queries']
            or recovered['termination'] != 'QUERY_CAP_REACHED'
            or recovered['journal']['new_callback_calls'] != 0
            or recovered['journal']['reused_callback_returns'] != 4):
        raise ValueError('Original return recovery or exact-once callback control differs')
    sources = ['src/wcomr/cara_budget_search_journal_r1.py', 'tests/test_cara_budget_search_journal_r1.py',
        'scripts/check_cara_budget_query_journal_r1.py']
    return dict(schema='CARA_BUDGET_QUERY_JOURNAL_LOCAL_CPU_R1',
        status='LOCAL_QUERY_PERSISTENCE_AND_REPLAY_CPU_ACCEPTED_PRODUCTION_PENDING',
        observed_unix=time.time(), python_version=platform.python_version(), tests_run=tested.testsRun,
        tests_passed=tested.testsRun, source_sha256={name:sha(ROOT/name) for name in sources},
        original_component_ref=original_ref, original_component_sha256=sha(ROOT/original_ref),
        original_component_sources_unchanged=True, retained_CPU_artifact_directory=str(artifacts),
        journal_files_sha256=after, journal_file_count=len(after),
        synthetic_new_callback_calls=len(calls), recovered_new_callback_calls=0,
        recovered_original_returns=4, recovered_controller_query_trace_exact=True,
        unknown_after_actual_child_exit17_refused=True, disk_full_no_retry_verified=True,
        missing_or_torn_or_changed_records_refused=True, original_binding_and_lock_required=True,
        query_cap_not_reset_on_recovery=True, original_return_records_unchanged=True,
        callback_errors_not_physical_terminal_evidence=True,
        original_unknown_process_reader_accepted=False, dedicated_production_storage_accepted=False,
        production_evaluator_accepted=False, dual_host_production_CPU_accepted=False,
        whole_GPU_quote_frozen=False, GPU_dispatch_ready=False,
        actual_model_calls=0, actual_generated_videos=0, actual_GPU_submissions=0, new_reserved_GPUh=0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--artifacts', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.artifacts.exists():
        raise ValueError('Fresh receipt and CPU artifact directory required')
    result = check(args.artifacts.resolve())
    with args.output.open('x') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({k:result[k] for k in ('status','tests_passed','synthetic_new_callback_calls',
        'recovered_new_callback_calls','actual_GPU_submissions')}))


if __name__ == '__main__':
    main()
