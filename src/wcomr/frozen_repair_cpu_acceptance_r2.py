"""Independently bind the full180 repair CPU process, source and actual entry."""
from .frozen_shared_acceptance_r1 import digest, original_alive
from .frozen_repair180_r2 import PRODUCTION_CPU_STATUS, fingerprint, validate_contract
from .frozen_shared_execution_r1 import point
from .frozen_repair_entry_r2 import ENTRIES, WORKER

CPU_BUNDLE_STATUS = 'N07_REFUSAL_REPAIR180_COMPLETE_PRODUCTION_CPU_PASS_NOT_GPU'
CPU_ACCEPTED_STATUS = 'N07_REFUSAL_REPAIR180_REAL_PRODUCTION_CPU_ACCEPTED_NOT_GPU'
PATTERNS = ('test_frozen_shared_production_r1.py', 'test_frozen_shared_batch_r1.py',
    'test_frozen_shared_post_r1.py', 'test_frozen_shared_acceptance_r1.py',
    'test_frozen_shared_dispatch_r1.py', 'test_frozen_guardrail_boundary_r2.py',
    'test_frozen_repair180_r2.py', 'test_frozen_repair_cpu_acceptance_r2.py')
BUNDLE_WORKER = 'scripts/run_wc_paper_N07_repair_production_cpu_bundle_r2.py'


def validate_bundle(bundle, source_revision, *, payload=None):
    commands = bundle['commands']; stage, project, python = (bundle[k] for k in ('stage','project','python_executable'))
    expected = [[python, '-m', 'unittest', 'discover', '-s', stage + '/tests', '-p', name, '-v'] for name in PATTERNS]
    expected.append([python, stage + '/' + WORKER, '--project', project, '--stage', stage, '--cpu-check'])
    if (bundle['status'] != CPU_BUNDLE_STATUS or bundle['exit_code'] != 0
            or [r['command'] for r in commands] != expected or any(r['exit_code'] != 0 for r in commands)
            or bundle['source_revision'] != source_revision
            or any(bundle[k] for k in ('GPU_submissions','model_weights_loaded','ledger_written',
                'shared_runtime_written','original_base_stage_written'))):
        raise ValueError('All eight same-source controls and the actual complete180 repair CPU entry must pass')
    if payload is not None:
        expected_sources = {n:payload.get(n) for n in [BUNDLE_WORKER] + ['tests/'+p for p in PATTERNS]}
        if (not all(digest(h) for h in expected_sources.values())
                or bundle['control_source_sha256'] != expected_sources):
            raise ValueError('The complete same-stage CPU commands need original source SHA bindings')


def validate_proof(proof, config, bound, registration, *, registration_sha256, config_sha256):
    plan = validate_contract(config, bound); payload = registration['payload_sha256']
    if (proof['status'] != PRODUCTION_CPU_STATUS or proof['exit_code'] != 0
            or proof['source_revision'] != registration['source_revision']
            or proof['registration_sha256'] != registration_sha256 or proof['config_sha256'] != config_sha256
            or proof['bound_input_fingerprint'] != fingerprint(bound) or proof['scope_counts'] != config['scope_counts']
            or proof['matrix'] != plan or proof['actual_sample_argument_variants'] != 160
            or proof['runner_source_sha256'] != payload.get(WORKER) or not digest(proof['runner_source_sha256'])
            or any(proof[k] for k in ('CUDA_initialized','GPU_submissions','model_weights_loaded','ledger_written'))):
        raise ValueError('The original whole180 typed requests and repair CPU proof must match')
    guarded = [m for m in bound['method_ids'] if point(m)['family'] in ('NATIVE','FIXED26')]
    expected = {(c['id'],c['seed'],m) for c in bound['cases'][:2] for m in guarded}
    checks = proof['guardrail_checks']
    if (len(checks) != len(expected) or {(r['case_id'],r['seed'],r['method']) for r in checks} != expected
            or not all(r['unguarded_execution_refused'] is True for r in checks)
            or proof['native_forward_identity']['qualified_name'] !=
                'cosmos_predict2._src.predict2.networks.minimal_v1_lvg_dit.MinimalV1LVGDiT.forward'
            or not digest(proof['native_forward_identity']['sha256'])):
        raise ValueError('Both selected seeds and every Native/fixed-mask missing-guard refusal required')
    reuse = proof['unchanged_numeric_CPU_reuse']
    repair = reuse['request_boundary_repair']
    if (reuse['status'] != 'ACCEPTED_FULL952_NUMERICAL_DEPENDENCIES_REUSED'
            or reuse['checked_source_files'] != len(reuse['source_sha256']) or reuse['checked_source_files'] != 99
            or any(payload.get(n) != h or not digest(h) for n,h in reuse['source_sha256'].items())
            or repair['status'] != 'ACCEPTED_FULL520_REQUEST_BOUNDARY_CPU_REUSED_NOT_PRODUCTION'
            or repair['successful_CPU_paths'] != 520 or repair['expected_original_failure_reproductions'] != 4
            or repair['new_full520_paths_run'] != 0
            or repair['original_CPU_sha256'] != config['references']['refusal_boundary_CPU']['sha256']
            or any(payload.get(n) != h or not digest(h) for n,h in repair['source_sha256'].items())):
        raise ValueError('Unchanged numerical99 and the complete520 request-boundary proof required')
    entries = reuse['metadata_entry_derivations']
    if set(entries) != set(ENTRIES): raise ValueError('Bind every worker, supervisor, watcher and post entry')
    for kind, (name, expected_sha) in ENTRIES.items():
        d = entries[kind]
        if (d['original_entry'] != name or d['original_sha256'] != expected_sha or payload.get(name) != expected_sha
                or not d['inverse_bytes_and_AST_equal'] or d['original_stage_or_script_written']
                or not d['only_declared_metadata_imports_paths_and_CPU_guard_coverage_changed']):
            raise ValueError('Exact reversible lifecycle entry binding required')


def accept(value):
    launch, registration = value['launch'], value['registration']
    if (value['status'] != 'N07_REPAIR_PRODUCTION_CPU_ORIGINAL_ONCE_CAPTURE'
            or value['observed_unix'] < launch['first_collection_not_before_unix']
            or value['registration_sha256'] != launch['registration_sha256']
            or registration['source_revision'] != launch['source_revision']
            or set(value['payload_verified']) != set(registration['payload_sha256'])
            or not value['payload_verified'] or not all(v is True for v in value['payload_verified'].values())
            or value['GPU_submissions'] or value['ledger_written']):
        raise ValueError('Use the original repair CPU handle, complete source and post-ETA capture')
    if original_alive(launch['identity'], value['process']):
        return dict(status='N07_REPAIR_ORIGINAL_CPU_STILL_RUNNING_REESTIMATE_ONCE',CPU_accepted=False,GPU_submissions=0)
    f = value['files']
    if f['bundle']['exists'] and f['bundle']['data'].get('exit_code') not in (None,0):
        return dict(status='N07_REPAIR_ORIGINAL_CPU_FAILED_RETAINED',CPU_accepted=False,
            original_bundle=f['bundle']['data'],no_GPU_launch_authorized=True,GPU_submissions=0)
    if not all(f[k]['exists'] for k in ('bundle','proof','config','bound_inputs')):
        return dict(status='N07_REPAIR_ORIGINAL_CPU_MISSING_RESULTS',CPU_accepted=False,
            no_GPU_launch_authorized=True,GPU_submissions=0)
    bundle, proof, config, bound = (f[k]['data'] for k in ('bundle','proof','config','bound_inputs'))
    validate_bundle(bundle, launch['source_revision'],payload=registration['payload_sha256'])
    validate_proof(proof,config,bound,registration,registration_sha256=value['registration_sha256'],
        config_sha256=f['config']['sha256'])
    if (f['bound_inputs']['sha256'] != config['references']['bound_inputs']['sha256']
            or bundle['stage'] != launch['stage'] or bundle['project'] != launch['project']):
        raise ValueError('The original CPU process must bind the complete original conditioning and stage')
    return dict(status=CPU_ACCEPTED_STATUS,CPU_accepted=True,source_revision=launch['source_revision'],
        original_CPU_identity=launch['identity'],registration_sha256=value['registration_sha256'],
        config_sha256=f['config']['sha256'],production_CPU_sha256=f['proof']['sha256'],
        production_CPU_bundle_sha256=f['bundle']['sha256'],scope_counts=config['scope_counts'],
        bound_input_fingerprint=fingerprint(bound),CPU_commands=len(PATTERNS)+1,
        actual_sample_argument_variants=160,guardrail_refusal_checks=len(proof['guardrail_checks']),
        whole_GPU_card_selected=False,real_video_or_speed_result=False,GPU_submissions=0,ledger_written=False)
