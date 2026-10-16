"""Original full40 production CPU evidence; not GPU or speed acceptance."""
from .balanced_repeat_execution_r1 import COUNTS
from .balanced_repeat_production_r1 import CPU_STATUS, validate_contract
from .frozen_shared_acceptance_r1 import digest, original_alive
from .frozen_shared_production_r1 import fingerprint

PATTERNS = ('test_balanced_repeat_timing_r1.py', 'test_balanced_repeat_execution_r1.py',
            'test_balanced_repeat_production_r1.py', 'test_balanced_repeat_post_r1.py',
            'test_balanced_repeat_supervision_r1.py', 'test_balanced_repeat_dispatch_r1.py',
            'test_balanced_repeat_acceptance_r1.py', 'test_balanced_repeat_capture_r1.py')
BUNDLE_STATUS = 'N08_FULL40_ACTUAL_PRODUCTION_CPU_COMPLETE_PASS_NOT_GPU'
ACCEPTED_STATUS = 'N08_FULL40_REAL_PRODUCTION_CPU_INDEPENDENTLY_ACCEPTED_NOT_GPU'


def validate_bundle(bundle, revision):
    commands = bundle['commands']
    if (bundle['status'] != BUNDLE_STATUS or bundle['exit_code'] != 0
            or bundle['source_revision'] != revision or len(commands) != len(PATTERNS) + 1
            or any(r['exit_code'] != 0 for r in commands)
            or any(commands[i]['command'][-2:] != [name, '-v'] for i, name in enumerate(PATTERNS))
            or not commands[-1]['command'][1].endswith('/scripts/run_wc_paper_N08_balanced_full40_r1.py')
            or commands[-1]['command'][-1] != '--cpu-check'
            or any(bundle[k] for k in ('GPU_submissions', 'model_weights_loaded', 'ledger_written',
                                      'shared_runtime_written', 'original_base_stage_written'))):
        raise ValueError('All eight declared controls and the actual full40 no-weights entry must pass')


def validate_proof(proof, config, bound, registration, *, registration_sha256, config_sha256):
    if (proof['status'] != CPU_STATUS or proof['exit_code'] != 0
            or proof['source_revision'] != registration['source_revision']
            or proof['registration_sha256'] != registration_sha256
            or proof['config_sha256'] != config_sha256
            or proof['bound_timing_fingerprint'] != fingerprint(bound)
            or proof['scope_counts'] != COUNTS or proof['matrix'] != bound['execution_plan']
            or proof['actual_sample_argument_variants'] != 10
            or proof['runner_source_sha256'] != registration['payload_sha256'][
                'scripts/run_wc_paper_N08_balanced_full40_r1.py']
            or any(proof[k] for k in ('CUDA_initialized', 'GPU_submissions', 'model_weights_loaded', 'ledger_written'))):
        raise ValueError('All original ten typed arguments and the exact no-weights full40 proof required')
    expected = {(r['name'], 0, 'NATIVE35') for r in bound['requests']}
    checks = proof['guardrail_checks']
    if (len(checks) != 2 or {(r['scene'], r['seed'], r['method']) for r in checks} != expected
            or any(r['unguarded_execution_refused'] is not True for r in checks)
            or proof['native_forward_identity']['qualified_name'] !=
                'cosmos_predict2._src.predict2.networks.minimal_v1_lvg_dit.MinimalV1LVGDiT.forward'
            or not digest(proof['native_forward_identity']['sha256'])):
        raise ValueError('Both original actual Native guard refusals and native source identity required')
    reused = proof['unchanged_numeric_CPU_reuse']
    if (reused['status'] != 'ACCEPTED_FULL952_NUMERICAL_DEPENDENCIES_REUSED'
            or reused['checked_source_files'] != 99 or len(reused['source_sha256']) != 99
            or any(registration['payload_sha256'].get(n) != h for n, h in reused['source_sha256'].items())):
        raise ValueError('Reuse exactly the original accepted99 numerical dependencies')


def accept(value):
    launch, registration = value['launch'], value['registration']
    if (value['status'] != 'N08_PRODUCTION_CPU_ORIGINAL_ONCE_CAPTURE'
            or value['observed_unix'] < launch['first_collection_not_before_unix']
            or value['registration_sha256'] != launch['registration_sha256']
            or registration['source_revision'] != launch['source_revision']
            or set(value['payload_verified']) != set(registration['payload_sha256'])
            or not value['payload_verified'] or not all(v is True for v in value['payload_verified'].values())
            or value['GPU_submissions'] or value['ledger_written']):
        raise ValueError('Original source, full payload and post-ETA CPU observation required')
    if original_alive(launch['identity'], value['process']):
        return dict(status='N08_ORIGINAL_PRODUCTION_CPU_STILL_RUNNING_REESTIMATE_ONCE',
                    CPU_accepted=False, original_process=value['process'], GPU_submissions=0)
    files = value['files']
    if files['bundle']['exists'] and (files['bundle']['data']['status'] != BUNDLE_STATUS
                                     or files['bundle']['data']['exit_code'] != 0):
        return dict(status='N08_ORIGINAL_PRODUCTION_CPU_FAILED_RESULT_RETAINED', CPU_accepted=False,
                    original_bundle=files['bundle']['data'], no_GPU_launch_authorized=True, GPU_submissions=0)
    names = ('bundle', 'proof', 'config', 'timing_protocol', 'shared_config', 'method_freeze')
    if not all(files[k]['exists'] for k in names):
        return dict(status='N08_ORIGINAL_PRODUCTION_CPU_TERMINAL_MISSING_RESULTS', CPU_accepted=False,
                    no_GPU_launch_authorized=True, GPU_submissions=0)
    bundle, proof, config, protocol, shared, freeze = [files[k]['data'] for k in names]
    validate_bundle(bundle, launch['source_revision'])
    bound = validate_contract(config, protocol, shared, freeze)
    if config['references']['method_freeze'] != shared['references']['method_freeze']:
        raise ValueError('Common evaluation and timing must use the same original freeze reference')
    for name in ('timing_protocol', 'shared_config', 'method_freeze'):
        if files[name]['sha256'] != config['references'][name]['sha256']:
            raise ValueError('Frozen timing reference identity differs: ' + name)
    validate_proof(proof, config, bound, registration, registration_sha256=value['registration_sha256'],
                   config_sha256=files['config']['sha256'])
    return dict(status=ACCEPTED_STATUS, CPU_accepted=True, source_revision=launch['source_revision'],
        registration_sha256=value['registration_sha256'], config_sha256=files['config']['sha256'],
        production_CPU_sha256=files['proof']['sha256'], production_CPU_bundle_sha256=files['bundle']['sha256'],
        bound_timing_fingerprint=fingerprint(bound), scope_counts=COUNTS.copy(), CPU_commands=len(PATTERNS) + 1,
        actual_sample_argument_variants=10, payload_files=len(value['payload_verified']),
        original_CPU_identity=launch['identity'], wall_seconds=bundle['wall_seconds'],
        whole_GPU_card_selected=False, real_video_or_speed_result=False, GPU_submissions=0, ledger_written=False)
