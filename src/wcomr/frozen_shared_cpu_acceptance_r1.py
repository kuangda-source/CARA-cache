"""Offline original CPU acceptance, distinct from any video or GPU result."""
from .frozen_shared_acceptance_r1 import original_alive
from .frozen_shared_production_r1 import PRODUCTION_CPU_STATUS, fingerprint, validate_contract
from .frozen_shared_execution_r1 import point

CPU_BUNDLE_STATUS = 'N07_SHARED180_ACTUAL_PRODUCTION_CPU_COMPLETE_PASS_NOT_GPU'
CPU_ACCEPTED_STATUS = 'N07_SHARED180_REAL_PRODUCTION_CPU_INDEPENDENTLY_ACCEPTED_NOT_GPU'


def validate_bundle(bundle, source_revision):
    patterns = ('test_frozen_shared_production_r1.py', 'test_frozen_shared_batch_r1.py',
                'test_frozen_shared_post_r1.py', 'test_frozen_shared_acceptance_r1.py',
                'test_frozen_shared_dispatch_r1.py')
    commands = bundle['commands']
    if (bundle['status'] != CPU_BUNDLE_STATUS or bundle['exit_code'] != 0
            or len(commands) != 6 or any(r['exit_code'] != 0 for r in commands)
            or any(commands[i]['command'][-2:] != [name, '-v'] for i, name in enumerate(patterns))
            or not commands[-1]['command'][1].endswith('/scripts/run_wc_paper_N07_frozen_shared180_r1.py')
            or commands[-1]['command'][-1] != '--cpu-check'
            or bundle['source_revision'] != source_revision
            or any(bundle[k] for k in ('GPU_submissions', 'model_weights_loaded', 'ledger_written',
                                      'shared_runtime_written', 'original_base_stage_written'))):
        raise ValueError('All five declared controls and actual production entry must pass unchanged')


def accept(value):
    launch = value['launch']; registration = value['registration']
    if (value['status'] != 'N07_PRODUCTION_CPU_ORIGINAL_ONCE_CAPTURE'
            or value['observed_unix'] < launch['first_collection_not_before_unix']
            or value['registration_sha256'] != launch['registration_sha256']
            or registration['source_revision'] != launch['source_revision']
            or set(value['payload_verified']) != set(registration['payload_sha256'])
            or not value['payload_verified'] or not all(v is True for v in value['payload_verified'].values())
            or value['GPU_submissions'] or value['ledger_written']):
        raise ValueError('Original no-GPU CPU source, registration and not-before identity required')
    if original_alive(launch['identity'], value['process']):
        return dict(status='N07_ORIGINAL_PRODUCTION_CPU_STILL_RUNNING_REESTIMATE_ONCE',
            original_process=value['process'], GPU_submissions=0, CPU_accepted=False)
    files = value['files']
    if files['bundle']['exists']:
        bundle = files['bundle']['data']
        if bundle['status'] != CPU_BUNDLE_STATUS or bundle['exit_code'] != 0:
            return dict(status='N07_ORIGINAL_PRODUCTION_CPU_FAILED_RESULT_RETAINED',
                CPU_accepted=False, original_bundle=bundle, no_GPU_launch_authorized=True, GPU_submissions=0)
    if not all(files[k]['exists'] for k in ('bundle', 'proof', 'config', 'bound_inputs')):
        return dict(status='N07_ORIGINAL_PRODUCTION_CPU_TERMINAL_MISSING_RESULTS',
            CPU_accepted=False, original_process=value['process'], no_GPU_launch_authorized=True, GPU_submissions=0)
    bundle, proof, config, bound = [files[k]['data'] for k in ('bundle', 'proof', 'config', 'bound_inputs')]
    plan = validate_contract(config, bound)
    validate_bundle(bundle, launch['source_revision'])
    if (proof['status'] != PRODUCTION_CPU_STATUS or proof['exit_code'] != 0
            or proof['source_revision'] != launch['source_revision']
            or proof['registration_sha256'] != value['registration_sha256']
            or proof['config_sha256'] != files['config']['sha256']
            or files['bound_inputs']['sha256'] != config['references']['bound_inputs']['sha256']
            or proof['bound_input_fingerprint'] != fingerprint(bound)
            or proof['scope_counts'] != config['scope_counts'] or proof['matrix'] != plan
            or proof['actual_sample_argument_variants'] != 160
            or proof['runner_source_sha256'] != registration['payload_sha256'][
                'scripts/run_wc_paper_N07_frozen_shared180_r1.py']
            or any(proof[k] for k in ('CUDA_initialized', 'GPU_submissions', 'model_weights_loaded', 'ledger_written'))):
        raise ValueError('Whole180 source/input/type/production proof differs')
    native = [m for m in bound['method_ids'] if point(m)['family'] == 'NATIVE']
    expected = {(c['id'], c['seed'], m) for c in bound['cases'][:2] for m in native}
    actual = {(r['case_id'], r['seed'], r['method']) for r in proof['guardrail_checks']}
    if (len(proof['guardrail_checks']) != len(expected) or actual != expected
            or any(r['unguarded_execution_refused'] is not True for r in proof['guardrail_checks'])
            or proof['native_forward_identity']['qualified_name'] !=
                'cosmos_predict2._src.predict2.networks.minimal_v1_lvg_dit.MinimalV1LVGDiT.forward'):
        raise ValueError('Actual original Native class and every typed Native/seed guard refusal required')
    reused = proof['unchanged_numeric_CPU_reuse']
    if (reused['status'] != 'ACCEPTED_FULL952_NUMERICAL_DEPENDENCIES_REUSED'
            or reused['checked_source_files'] != 99 or reused['checked_source_files'] != len(reused['source_sha256'])
            or any(registration['payload_sha256'].get(n) != h for n, h in reused['source_sha256'].items())):
        raise ValueError('Accepted whole952 numerical dependencies must match the actual stage')
    return dict(status=CPU_ACCEPTED_STATUS, CPU_accepted=True, source_revision=launch['source_revision'],
        registration_sha256=value['registration_sha256'], config_sha256=files['config']['sha256'],
        production_CPU_sha256=files['proof']['sha256'], production_CPU_bundle_sha256=files['bundle']['sha256'],
        bound_input_fingerprint=fingerprint(bound), scope_counts=config['scope_counts'],
        payload_files=len(value['payload_verified']), CPU_commands=6, actual_sample_argument_variants=160,
        original_CPU_identity=launch['identity'], wall_seconds=bundle['wall_seconds'],
        native_forward_identity=proof['native_forward_identity'],
        whole_GPU_card_selected=False, real_video_or_speed_result=False, GPU_submissions=0, ledger_written=False)
