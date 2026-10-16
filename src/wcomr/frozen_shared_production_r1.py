"""Parameterized final-test production contract; no scope selection or launch.

The actual final configuration is intentionally absent before N05 acceptance.
Unchanged physical dependencies reuse the accepted N05 validator; the final
selection, sixteen requests, whole cost and authority are independently bound.
"""
import ast
import gzip
import hashlib
import json
import math
from pathlib import Path
import time

from .frozen_shared_inputs_r1 import bind_selected

CONFIG = 'configs/wc_paper_N07_frozen_shared_production_r1_20261016.json'
RUN = 'wc-paper-n07-frozen-shared180-r1'
CARD = 'WC-PAPER-N07-FROZEN-SHARED180-R1'
STRATEGY = 'WORKING_P_AGE_NONZERO_REBASE'
PRODUCTION_CPU_STATUS = 'N07_FROZEN_SHARED_ACTUAL_PRODUCTION_ENTRY_CPU_PASS_NOT_GPU'
SHARED_CPU_STATUS = 'FROZEN_SHARED_REGISTRY952_SEED_CONTEXT_AND_LEGACY_PARITY_INDEPENDENTLY_ACCEPTED_NOT_PRODUCTION'
TIMING = 'SYNCHRONIZED_TEXT_ENCODING_DENOISING_VAE_DECODING'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def write(path, value):
    from .gpu_budget_pool_v2 import atomic_json
    atomic_json(path, value)


def validate_contract(config, bound):
    from .frozen_shared_execution_r1 import matrix, point
    if (config['card'] != CARD or config['run_id'] != RUN
            or config['strategy'] != STRATEGY or config['main_timing'] != TIMING
            or config['memory_policy'] != 'REQUEST_BOUNDARY_GC_ONLY'
            or config['autonomy_exclusive_upper_GPUh'] != 12
            or config['reference_method'] != 'NATIVE35'
            or config['method_ids'] != bound['method_ids']
            or config['bound_input_fingerprint'] != fingerprint(bound)
            or config['scope_counts'] != bound['planned_scope_counts']
            or config['warm_trace_policy'] != 'ALL20_FULL_TRACE_BOTH_REPEATS'
            or not config['guardrails_enabled'] or not config['neighbor_gap_retained']
            or any(config[k] for k in ('training', 'online_teachers', 'F_B_enabled', 'P_ACR',
                                      'T1', 'head_elision', 'deployment_profiling'))):
        raise ValueError('Whole frozen shared scope, source or ordinary inference policy changed')
    cost, limit = config['forecast_complete_GPUh'], config['billed_limit_GPUh']
    cap, origin = config['cumulative_cap_GPUh'], config['budget_origin_used_GPUh']
    if (not all(number(v) for v in (cost, limit, cap, origin))
            or not 0 < cost <= limit or not 0 <= origin < cap):
        raise ValueError('Explicit complete cost and original budget window required')
    plan = matrix(bound['cases'], bound['method_ids'])
    counts = bound['planned_scope_counts']
    if (bound['execution_plan'] != plan or len(bound['argument_variants']) != 160
            or len(plan) != 180 or counts['scientific_paths'] != 160
            or counts['full_warmup_paths'] != 20 or counts['total_paths'] != 180
            or counts['ordinary_pairs'] != sum(point(p['method'])['actual_updates'] for p in plan)
            or counts['ordinary_CFG_calls'] != 2 * counts['ordinary_pairs']
            or counts['loads'] != 1 or counts['teacher_pairs'] != 0
            or not {'FRONT_DENSE_C', 'FRONT_DENSE_A'}.issubset(bound['method_ids'])):
        raise ValueError('Keep every formal/warmup position and selected strong simple comparators')
    return plan


def prepare_samples(bound, inference_arguments):
    samples = {}
    for row in bound['argument_variants']:
        sample = inference_arguments(**row['arguments'])
        actual = sample.model_dump(mode='json')
        if any(actual[k] != v for k, v in row['arguments'].items()):
            raise ValueError('Actual typed inference arguments changed original conditioning or seed')
        key = (row['case_id'], row['method'])
        if key in samples:
            raise ValueError('Duplicate actual request/method arguments')
        samples[key] = sample
    if len(samples) != 160:
        raise ValueError('All final typed request variants required')
    return samples


def sampling_source_closure(root):
    """Follow local Python imports from the accepted numerical executor.

    Newly added unrelated quality/input helpers need not invalidate the full952
    proof. Runtime-derived WC/RF bodies are checked separately by their SHA.
    """
    root = Path(root)
    pending = ['wcomr.frozen_shared_execution_r1']
    visited = {}
    while pending:
        module = pending.pop()
        relative = 'src/' + module.replace('.', '/') + '.py'
        if relative in visited:
            continue
        path = root / relative
        if not path.is_file():
            raise ValueError('Numerical execution dependency absent: ' + relative)
        visited[relative] = sha(path)
        package = module.rsplit('.', 1)[0]
        for node in ast.walk(ast.parse(path.read_text())):
            targets = []
            if isinstance(node, ast.ImportFrom):
                if node.level:
                    parts = package.split('.')
                    prefix = '.'.join(parts[:len(parts) - node.level + 1])
                    if node.module:
                        targets = [prefix + '.' + node.module]
                    else:
                        targets = [prefix + '.' + alias.name for alias in node.names]
                elif node.module and node.module.startswith('wcomr.'):
                    targets = [node.module]
            elif isinstance(node, ast.Import):
                targets = [a.name for a in node.names if a.name.startswith('wcomr.')]
            for target in targets:
                if target.startswith('wcomr.'):
                    pending.append(target)
    return visited


def verify_sampling_sources(root, numeric, accepted):
    if (accepted['status'] != SHARED_CPU_STATUS or accepted['actual_CPU_paths'] != 952
            or numeric['actual_CPU_paths'] != 952 or numeric['ordinary_pairs'] != 32816
            or numeric['CFG_calls'] != 65632 or numeric['CUDA_initialized']
            or accepted['source_revision'] != numeric['source_revision']):
        raise ValueError('Accepted original complete952 execution proof required')
    actual = sampling_source_closure(root)
    for name, digest in actual.items():
        if numeric['source_sha256'].get(name) != digest:
            raise ValueError('An actual numerical execution dependency changed: ' + name)
    return dict(status='ACCEPTED_FULL952_NUMERICAL_DEPENDENCIES_REUSED',
                checked_source_files=len(actual), source_sha256=actual,
                unrelated_new_helpers_do_not_change_numeric_proof=True)


def validate_launch_authority(config, bound, registration, proof, authority, *, revision,
                              gpu_uuid, config_sha256, proof_sha256, registration_sha256):
    validate_contract(config, bound)
    if (registration['source_revision'] != revision or proof['source_revision'] != revision
            or authority['source_revision'] != revision
            or proof['status'] != PRODUCTION_CPU_STATUS or proof['exit_code'] != 0
            or proof['registration_sha256'] != registration_sha256
            or proof['config_sha256'] != config_sha256 or authority['config_sha256'] != config_sha256
            or authority['production_CPU_sha256'] != proof_sha256
            or authority['bound_input_fingerprint'] != fingerprint(bound)
            or authority['scope_counts'] != config['scope_counts']
            or authority['whole_card_run'] != RUN or authority['gpu_uuid'] != gpu_uuid
            or authority['forecast_complete_GPUh'] != config['forecast_complete_GPUh']
            or authority['billed_limit_GPUh'] != config['billed_limit_GPUh']
            or authority['cumulative_cap_GPUh'] != config['cumulative_cap_GPUh']
            or authority['budget_origin_used_GPUh'] != config['budget_origin_used_GPUh']
            or not authority['direct_user_authorization'] or not authority['user_reply_quote']
            or not authority['launch_id']):
        raise ValueError('Bind complete scope/source/CPU/price to one authorized launch')
    if config['billed_limit_GPUh'] < 12:
        allowed = authority['kind'] in ('STANDING_STRICT_UNDER12', 'SPECIFIC_WHOLE_CARD_APPROVAL')
    else:
        allowed = authority['kind'] == 'SPECIFIC_WHOLE_CARD_APPROVAL'
    if not allowed:
        raise ValueError('At or above12GPUh requires the specific complete-card human reply')


def validate(project, stage):
    """Read immutable scope/selection/physical evidence, never dispatch work."""
    from .frozen_input_selection_r1 import select
    from .paper_baseline_production_r1 import validate as unchanged_physical_inputs
    project, stage = Path(project), Path(stage)
    config = json.loads((stage / CONFIG).read_text())
    references = {}
    for key, binding in config['references'].items():
        relative = Path(binding['ref'])
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Immutable stage-local evidence reference required')
        path = stage / relative
        if sha(path) != binding['sha256']:
            raise ValueError('Changed frozen N07 reference: ' + key)
        data = gzip.decompress(path.read_bytes()) if path.suffix == '.gz' else path.read_bytes()
        references[key] = json.loads(data)
    development = references['development']
    if (development['N05'] != references['N05_acceptance']
            or development['N06'] != references['N06_acceptance']):
        raise ValueError('Use original complete development acceptance receipts')
    selected = select(references['dataset_catalog']['records'],
        references['local_input_inventory']['excluded_group_members'], references['input_protocol'],
        development=development, method_freeze=references['method_freeze'],
        remote_audit=references['remote_identity_audit'])
    if selected != references['selection']:
        raise ValueError('Original deterministic input selection differs')
    raw_inputs = {}
    for source in selected['selected_sources']:
        binding = config['input_files'][source['name']]
        relative = Path(binding['ref'])
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Original input bytes need a stage-local reference')
        path = stage / relative
        if sha(path) != binding['sha256']:
            raise ValueError('Original selected input file changed')
        raw_inputs[source['name']] = path.read_bytes()
    bound = bind_selected(selected, raw_inputs)
    if bound != references['bound_inputs']:
        raise ValueError('Full final input/argument binding changed')
    validate_contract(config, bound)
    shared = verify_sampling_sources(stage, references['shared_CPU_raw'], references['shared_CPU_acceptance'])
    if sha(stage / config['references']['shared_CPU_capture']['ref']) != references['shared_CPU_acceptance']['capture_sha256']:
        raise ValueError('Original complete952 capture identity differs')
    # This only reuses unchanged model/calibration/runtime assets and old420
    # controls, not the old GPU card's permission or four-CAL scientific scope.
    _prior_config, registration, old, inputs, tables, previous = unchanged_physical_inputs(project, stage)
    for name, digest in references['shared_CPU_raw']['runtime_source_sha256'].items():
        if sha(project / 'runtime' / name) != digest:
            raise ValueError('Runtime differs from accepted numerical executor: ' + name)
    return config, registration, old, inputs, tables, previous, bound, shared


def audit_row(row, planned, bound):
    from .frozen_shared_execution_r1 import point
    from .simple26d_r1 import plans
    if any(row.get(k) != v for k, v in planned.items()):
        raise ValueError('Final input/method/order identity changed')
    case = next(c for c in bound['cases'] if c['id'] == planned['case_id'])
    if row['status'] == 'TEXT_REJECTED':
        if row.get('solver_steps') != 0 or row.get('guided_pairs') != 0 or row.get('final_artifact'):
            raise ValueError('Text rejection cannot contain a generated model path')
        return
    if row['status'] not in ('COMPLETE', 'VIDEO_REJECTED'):
        raise ValueError('Keep only explicit original generation outcomes in the running batch')
    selected = point(planned['method'])
    n, warm = selected['actual_updates'], planned['section'] == 'WARMUP'
    if (row['frozen_execution_point'] != selected
            or row['solver_steps'] != n or row['guided_pairs'] != n
            or len(row['scheduler_timesteps']) != n
            or row['in_timing_guided_copies'] != (n if warm else 0)
            or row['in_timing_hashes'] or row['research_checkpoints']
            or row['audit'] != warm or not row['write_deferred_after_main_timer']
            or not number(row['core_seconds']) or row['core_seconds'] <= 0
            or row['frozen_request_cleanup']['components_alive_after'] != 0):
        raise ValueError('Final actual counts, deferred observations or request lifetime differ')
    identity = row['frozen_input_identity']
    # The final N07 contract binds only17/43. The same per-path metadata audit
    # is also reused by separately scoped N08, whose original input seed is0.
    context_token = ('fixed-seed0-request' if case['seed'] == 0 else
                     'frozen-input-seed' + str(case['seed']))
    if (identity['name'] != case['id'] or identity['actual_sample_seed'] != case['seed']
            or identity['requested_steps'] != selected['requested_steps']
            or not identity['installed_contexts']
            or any(c[2] != context_token for c in identity['installed_contexts'])):
        raise ValueError('Actual cache/input seed identity differs from the frozen case')
    if warm and row.get('warm_guided_outputs') != n:
        raise ValueError('All actual warm guided outputs required, including reduced-step Native')
    if selected['family'] == 'NATIVE':
        # The accepted executor observes the first/last block endpoints. The
        # pinned native class and production28-block check are separate from
        # this two-counter receipt; do not invent 28 per-layer measurements.
        if (row['actions'] is not None
                or set(row['native_block_CFG_counts']) != {'first_block_CFG', 'last_block_CFG'}
                or set(row['native_block_CFG_counts'].values()) != {2 * n}
                or not row['native_count_adaptation']['inverse_bytes_and_AST_equal']):
            raise ValueError('Native first/last dense endpoints must match both actual CFG branches')
    else:
        if len(row['actions']) != 36 or any(a not in ('CC', 'CD', 'DC', 'DD', 'PP') for a in row['actions']):
            raise ValueError('All original branch action positions required')
        if selected['family'] == 'WC' and row['installed_thresholds'][0]['net_WC_threshold'] != selected['threshold']:
            raise ValueError('Installed WorldCache workpoint changed')
        if selected['family'] == 'RA' and row['installed_thresholds'][0]['controller_RA_threshold'] != selected['threshold']:
            raise ValueError('Installed RA workpoint changed')
        if selected['family'] == 'FIXED26':
            if row['semantic_plan'] != list(plans()[planned['method']]) or row['actions'].count('DD') != 26:
                raise ValueError('Strong simple comparator mask or dense quota changed')
            if [h['A_readout']['readout_action'] for h in row['source_history']] != row['semantic_plan']:
                raise ValueError('Actual fixed-mask readout differs from the frozen semantic actions')
    if planned['method'] == 'TABLE_PHASE_H1' or selected['family'] == 'FIXED26':
        history = row['source_history']
        if len(history) != 36 or [h['action'] for h in history] != row['actions']:
            raise ValueError('Full H1 source history required')
        for item in history:
            if item['teacher_calls'] or item['P_updates_true_D_or_zero_risk_RA_anchor']:
                raise ValueError('No online teacher or false true-D source is permitted')
            if item['action'] != 'DD' and item['true_D_before'] != item['true_D_after']:
                raise ValueError('Approximate action cannot update actual dense history')
            if item['action'] == 'PP' and (item['source_policy']['creation_floor_proxy_after'] <= 0
                    or any(s['kind'] != 'P' or s['RA_zero_risk_reset_allowed'] for s in item['working_sources'])):
                raise ValueError('Existing P0 must keep its approximate source and nonzero birth error')


def run_registered_batch(config, bound, samples, run_one, *, save=lambda state: None):
    """The callback owns actual inference/artifacts; this loop owns every slot."""
    plan = validate_contract(config, bound)
    expected = {(r['case_id'], r['method']) for r in plan}
    if set(samples) != expected:
        raise ValueError('All160 frozen typed request variants required')
    state = dict(status='N07_SHARED180_RUNNING', scope_counts=config['scope_counts'], runs=[])
    save(state)
    for planned in plan:
        row = {**planned, 'status': 'RUNNING', 'started_unix': time.time()}
        state['runs'].append(row)
        save(state)
        try:
            value = run_one(planned, samples[(planned['case_id'], planned['method'])])
            row.update(value, ended_unix=time.time())
            audit_row(row, planned, bound)
            save(state)
        except BaseException as error:
            row.update(original_returned_status=row['status'], status='TECH_FAILED',
                       error_type=type(error).__name__, error=str(error), ended_unix=time.time())
            state.update(status='N07_SHARED180_TECHNICAL_FAILURE_FULL_SCOPE_RETAINED',
                         error_type=type(error).__name__, error=str(error))
            save(state)
            raise
    state['status'] = 'N07_SHARED180_GPU_COMPLETE_CPU_AUDIT_PENDING'
    save(state)
    return state


def full_rows(runs, plan):
    """Retain all warm/formal positions after any original terminal failure."""
    if (len({r['id'] for r in runs}) != len(runs)
            or [r['id'] for r in runs] != [r['id'] for r in plan[:len(runs)]]
            or len(runs) > len(plan)):
        raise ValueError('Original ordered execution prefix required')
    for row, planned in zip(runs, plan):
        if any(row.get(k) != v for k, v in planned.items()):
            raise ValueError('Foreign final input or method in the original prefix')
    indexed = {r['id']: r for r in runs}
    values = []
    for planned in plan:
        row = dict(indexed.get(planned['id'], {**planned, 'status': 'NOT_REACHED'}))
        if row['status'] == 'RUNNING':
            row.update(original_runner_status='RUNNING', status='TECH_FAILED')
        values.append(row)
    return values
