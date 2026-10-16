"""Independent acceptance of the complete, original N09 no-weights CPU job."""
from .frozen_shared_acceptance_r1 import digest, original_alive
from .frozen_shared_production_r1 import fingerprint, number
from .runtime_profile40_production_r1 import CPU_STATUS, COUNTS, PROFILE_SOURCES, validate_contract

PATTERNS = ('test_runtime_profile40_execution_r1.py', 'test_runtime_profile40_production_r1.py',
    'test_runtime_profile40_post_r1.py', 'test_runtime_profile40_cost_r1.py',
    'test_runtime_profile40_supervision_r1.py', 'test_runtime_profile40_post_watcher_r1.py',
    'test_runtime_profile40_cpu_acceptance_r1.py')
WORKER = 'scripts/run_wc_paper_N09_runtime_profile40_r1.py'
BUNDLE_WORKER = 'scripts/run_wc_paper_N09_production_cpu_bundle_r1.py'
BUNDLE_STATUS = 'N09_FULL40_ACTUAL_PRODUCTION_CPU_COMPLETE_PASS_NOT_GPU'
ACCEPTED_STATUS = 'N09_FULL40_REAL_PRODUCTION_CPU_INDEPENDENTLY_ACCEPTED_NOT_GPU'


def validate_bundle(bundle, revision, *, registration_sha256, config_sha256, proof_sha256, payload_sha256):
    stage, project, python = (bundle[k] for k in ('stage', 'project', 'python_executable'))
    expected = [[python, '-m', 'unittest', 'discover', '-s', stage + '/tests', '-p', pattern, '-v']
                for pattern in PATTERNS]
    expected.append([python, stage + '/' + WORKER, '--project', project, '--stage', stage, '--cpu-check'])
    commands = bundle['commands']
    controls = {'tests/' + name: payload_sha256.get('tests/' + name) for name in PATTERNS}
    if (bundle['status'] != BUNDLE_STATUS or bundle['exit_code'] != 0
            or bundle['source_revision'] != revision or bundle['registration_sha256'] != registration_sha256
            or bundle['config_sha256'] != config_sha256 or bundle['production_CPU_sha256'] != proof_sha256
            or len(commands) != len(expected) or [c['command'] for c in commands] != expected
            or any(c['exit_code'] != 0 for c in commands)
            or bundle['control_source_sha256'] != controls or not all(digest(h) for h in controls.values())
            or bundle['bundle_source_sha256'] != payload_sha256.get(BUNDLE_WORKER)
            or not digest(bundle['bundle_source_sha256'])
            or not number(bundle['wall_seconds']) or bundle['wall_seconds'] < 0
            or any(bundle[k] for k in ('GPU_submissions', 'model_weights_loaded', 'ledger_written',
                                      'shared_runtime_written', 'original_base_stage_written'))):
        raise ValueError('All seven same-source control groups and actual full40 CPU entry must pass')


def validate_proof(proof, config, bound, registration, *, registration_sha256, config_sha256):
    if (proof['status'] != CPU_STATUS or proof['exit_code'] != 0
            or proof['source_revision'] != registration['source_revision']
            or proof['registration_sha256'] != registration_sha256 or proof['config_sha256'] != config_sha256
            or proof['bound_profile_fingerprint'] != fingerprint(bound) or proof['scope_counts'] != COUNTS
            or proof['matrix'] != bound['execution_plan'] or proof['actual_sample_argument_variants'] != 10
            or proof['runner_source_sha256'] != registration['payload_sha256'].get(WORKER)
            or not digest(proof['runner_source_sha256'])
            or any(proof[k] for k in ('CUDA_initialized', 'GPU_submissions', 'model_weights_loaded', 'ledger_written'))
            or proof['guardrail_checks'] != [dict(scene=r['name'], unguarded_execution_refused=True) for r in bound['requests']]
            or proof['native_forward_identity']['qualified_name'] !=
                'cosmos_predict2._src.predict2.networks.minimal_v1_lvg_dit.MinimalV1LVGDiT.forward'
            or not digest(proof['native_forward_identity']['sha256'])):
        raise ValueError('Original full40 matrix, ten typed arguments, native source and guard controls required')
    reused = proof['unchanged_profile_and_numeric_CPU_reuse']
    numeric = reused['shared_numeric_reuse']
    if (reused['original_full102_CPU_paths'] != 102 or reused['new_full102_paths_run'] != 0
            or set(reused['source_sha256']) != set(PROFILE_SOURCES)
            or numeric['status'] != 'ACCEPTED_FULL952_NUMERICAL_DEPENDENCIES_REUSED'
            or numeric['checked_source_files'] != 99 or len(numeric['source_sha256']) != 99
            or any(not digest(h) or registration['payload_sha256'].get(n) != h
                   for group in (reused['source_sha256'], numeric['source_sha256']) for n, h in group.items())):
        raise ValueError('Reuse the original unchanged four observer sources and all99 numerical dependencies')


def accept(value):
    if value.get('status') != 'N09_PRODUCTION_CPU_ORIGINAL_ONCE_CAPTURE':
        raise ValueError('A transport failure is not an original CPU terminal observation')
    launch, registration = value['launch'], value['registration']
    payload = registration['payload_sha256']
    if (value['status'] != 'N09_PRODUCTION_CPU_ORIGINAL_ONCE_CAPTURE'
            or value['observed_unix'] < launch['first_collection_not_before_unix']
            or value['registration_sha256'] != launch['registration_sha256']
            or registration['source_revision'] != launch['source_revision']
            or not payload or value['payload_actual_sha256'] != payload
            or set(value['payload_verified']) != set(payload)
            or not all(v is True for v in value['payload_verified'].values())
            or value['GPU_submissions'] or value['ledger_written']):
        raise ValueError('Original complete payload SHA and a post-ETA CPU snapshot required')
    if original_alive(launch['identity'], value['process']):
        return dict(status='N09_ORIGINAL_PRODUCTION_CPU_STILL_RUNNING_REESTIMATE_ONCE',
                    CPU_accepted=False, original_process=value['process'], GPU_submissions=0)
    files = value['files']
    if (files['bundle']['exists'] and files['bundle']['data'].get('exit_code') not in (None, 0)):
        return dict(status='N09_ORIGINAL_PRODUCTION_CPU_FAILED_RESULT_RETAINED', CPU_accepted=False,
                    original_bundle=files['bundle']['data'], no_GPU_launch_authorized=True, GPU_submissions=0)
    names = ('bundle', 'proof', 'CPU_exit', 'config', 'runtime_scope', 'timing_protocol', 'method_freeze', 'shared_config')
    if not all(files[k]['exists'] for k in names):
        return dict(status='N09_ORIGINAL_PRODUCTION_CPU_TERMINAL_MISSING_RESULTS', CPU_accepted=False,
                    no_GPU_launch_authorized=True, GPU_submissions=0)
    config, scope, protocol, freeze, shared = (files[k]['data'] for k in names[3:])
    bound = validate_contract(config, scope, protocol, freeze, shared)
    for name in ('runtime_scope', 'timing_protocol', 'method_freeze', 'shared_config'):
        if files[name]['sha256'] != config['references'][name]['sha256']:
            raise ValueError('Original N09 CPU configuration reference differs: ' + name)
    if config['references']['method_freeze'] != shared['references']['method_freeze']:
        raise ValueError('Keep the original shared five-role freeze')
    bundle, proof, exit = (files[k]['data'] for k in names[:3])
    validate_bundle(bundle, launch['source_revision'], registration_sha256=value['registration_sha256'],
        config_sha256=files['config']['sha256'], proof_sha256=files['proof']['sha256'], payload_sha256=payload)
    validate_proof(proof, config, bound, registration, registration_sha256=value['registration_sha256'],
                   config_sha256=files['config']['sha256'])
    if any(proof['unchanged_profile_and_numeric_CPU_reuse']['source_sha256'][n]
           != scope['source_bindings'][n]['sha256'] for n in PROFILE_SOURCES):
        raise ValueError('The original accepted102 observer source must also match the frozen scope')
    if (bundle['stage'] != launch['stage'] or bundle['project'] != launch['project']
            or exit['exit_code'] != 0 or exit['source_revision'] != launch['source_revision']
            or exit['registration_sha256'] != value['registration_sha256']
            or any(exit['original_CPU_identity'].get(k) != launch['identity'].get(k)
                   for k in ('pid', 'start_ticks'))
            or exit['production_CPU_sha256'] != files['proof']['sha256']
            or exit['bundle_result_sha256'] != files['bundle']['sha256']):
        raise ValueError('The same original CPU process must finish with its bound bundle and proof')
    return dict(status=ACCEPTED_STATUS, CPU_accepted=True, source_revision=launch['source_revision'],
        registration_sha256=value['registration_sha256'], config_sha256=files['config']['sha256'],
        production_CPU_sha256=files['proof']['sha256'], production_CPU_bundle_sha256=files['bundle']['sha256'],
        original_CPU_identity=launch['identity'], bound_profile_fingerprint=fingerprint(bound),
        scope_counts=COUNTS.copy(), CPU_commands=len(PATTERNS) + 1, actual_sample_argument_variants=10,
        payload_files=len(payload), wall_seconds=bundle['wall_seconds'], whole_GPU_card_selected=False,
        real_video_or_speed_result=False, GPU_submissions=0, ledger_written=False)
