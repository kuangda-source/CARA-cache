"""Whole24 real-production CPU proof acceptance, separate from numerical88."""
import math
from .drop1_window24_production_r1 import (
    CONFIG, CPU_RESULT, PRODUCTION_CPU_STATUS, COUNTS, matrix, validate_contract,
)
from .frozen_shared_acceptance_r1 import original_alive

PATTERNS = ('test_drop1_window24_production_r1.py', 'test_drop1_window_original_controls_r1.py',
            'test_drop1_window24_execution_envelope_r1.py', 'test_gpu_budget_pool_v2.py')
BUNDLE = 'window24-CPU-bundle-result.json'
BUNDLE_STATUS = 'WINDOW24_COMPLETE_PRODUCTION_CPU_BUNDLE_PASS_NOT_GPU'
ACCEPTED_STATUS = 'WINDOW24_REAL_PRODUCTION_CPU_INDEPENDENTLY_ACCEPTED_NOT_GPU'
WORKER = 'scripts/run_wc_drop1_window24_r1.py'


def validate_proof(proof, config, *, source_revision, registration_sha256, config_sha256):
    validate_contract(config)
    if (proof.get('status') != PRODUCTION_CPU_STATUS or proof.get('exit_code') != 0
            or proof.get('source_revision') != source_revision
            or proof.get('registration_sha256') != registration_sha256
            or proof.get('config_sha256') != config_sha256
            or proof.get('numerical_CPU_capture_sha256') != config['references']['numeric_capture']['sha256']
            or proof.get('scope_counts') != COUNTS
            or proof.get('matrix') != matrix([r['name'] for r in config['requests']])
            or set(proof.get('mutations_refused', [])) != {'scope_counts', 'methods', 'A_method', 'P_enabled',
                'online_teachers', 'training', 'autonomy_exclusive_upper_GPUh', 'cumulative_cap_GPUh',
                'billed_limit_GPUh', 'timing_claim', 'plans'}
            or not proof.get('input_evidence')
            or any(proof.get(k) is not False if k == 'CUDA_initialized' else proof.get(k) != 0
                   for k in ('CUDA_initialized', 'GPU_submissions'))
            or proof.get('ledger_written') is not False):
        raise ValueError('Complete real24 entry, raw88 binding, inputs and all CPU refusal checks required')


def validate_bundle(bundle, proof, config, registration, *, registration_sha256, config_sha256, proof_sha256):
    expected = [[bundle['python_executable'], '-m', 'unittest', 'discover', '-s',
                 bundle['stage'] + '/tests', '-p', name, '-v'] for name in PATTERNS]
    expected.append([bundle['python_executable'], bundle['stage'] + '/' + WORKER,
                     '--project', bundle['project'], '--stage', bundle['stage'], '--cpu-check'])
    if (bundle.get('status') != BUNDLE_STATUS or bundle.get('exit_code') != 0
            or bundle.get('source_revision') != registration['source_revision']
            or bundle.get('registration_sha256') != registration_sha256
            or bundle.get('config_sha256') != config_sha256
            or bundle.get('production_CPU_sha256') != proof_sha256
            or bundle.get('bundle_worker_source_sha256') != registration['payload_sha256'].get('scripts/run_wc_drop1_window24_cpu_bundle_r1.py')
            or not isinstance(bundle.get('wall_seconds'), (int, float))
            or not math.isfinite(bundle['wall_seconds']) or bundle['wall_seconds'] <= 0
            or [x['command'] for x in bundle['commands']] != expected
            or any(x['exit_code'] != 0 for x in bundle['commands'])
            or bundle.get('control_source_sha256') != {'tests/' + n: registration['payload_sha256']['tests/' + n] for n in PATTERNS}
            or any(bundle.get(k) != 0 for k in ('GPU_submissions', 'model_weights_loaded'))
            or any(bundle.get(k) is not False for k in ('ledger_written', 'original_stage_written'))):
        raise ValueError('All four declared control groups and the actual full24 CPU entry required')
    validate_proof(proof, config, source_revision=registration['source_revision'],
        registration_sha256=registration_sha256, config_sha256=config_sha256)


def accept(value):
    launch, reg = value['launch'], value['registration']
    if (value.get('status') != 'WINDOW24_PRODUCTION_CPU_ORIGINAL_ONCE_CAPTURE'
            or value['observed_unix'] < launch['final_not_before_unix']
            or value['registration_sha256'] != launch['registration_sha256']
            or reg['source_revision'] != launch['source_revision']
            or value['payload_actual_sha256'] != reg['payload_sha256']
            or value['runtime_actual_sha256'] != reg['runtime_source_sha256']
            or not reg['payload_sha256'] or not reg['runtime_source_sha256']
            or value['GPU_submissions'] or value['ledger_written']):
        raise ValueError('Original post-ETA CPU capture and the complete immutable source/runtime required')
    if original_alive(launch['identity'], value['process']):
        return dict(status='WINDOW24_CPU_STILL_RUNNING_REESTIMATE_ONCE', CPU_accepted=False, GPU_submissions=0)
    if not all(value['files'][k].get('data') for k in ('bundle', 'proof', 'config')):
        return dict(status='WINDOW24_CPU_TERMINAL_MISSING_RESULTS_RETAINED', CPU_accepted=False, GPU_submissions=0)
    bundle, proof, config = (value['files'][k]['data'] for k in ('bundle', 'proof', 'config'))
    if bundle.get('exit_code') != 0:
        return dict(status='WINDOW24_CPU_ORIGINAL_FAILURE_RETAINED', CPU_accepted=False, GPU_submissions=0)
    if (value['files']['config']['sha256'] != reg['payload_sha256'].get(CONFIG)
            or bundle.get('stage') != launch['stage'] or bundle.get('project') != launch['project']
            or reg.get('stage') != launch['stage']):
        raise ValueError('CPU config, original stage and project must match the registered handle')
    validate_bundle(bundle, proof, config, reg, registration_sha256=value['registration_sha256'],
        config_sha256=value['files']['config']['sha256'], proof_sha256=value['files']['proof']['sha256'])
    return dict(status=ACCEPTED_STATUS, CPU_accepted=True, source_revision=reg['source_revision'],
        registration_sha256=value['registration_sha256'], config_sha256=value['files']['config']['sha256'],
        production_CPU_sha256=value['files']['proof']['sha256'], bundle_sha256=value['files']['bundle']['sha256'],
        original_CPU_identity=launch['identity'], scope_counts=COUNTS, CPU_commands=5,
        numerical88_reused_unchanged=True, actual_GPU_or_video_result=False,
        CPU_wall_seconds=bundle['wall_seconds'], GPU_submissions=0, ledger_written=False)
