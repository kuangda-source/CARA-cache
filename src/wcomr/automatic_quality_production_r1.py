"""Complete N10 scoring entry contract, before any neural-framework import.

The supervisor, deployment, whole-card quote and independent terminal acceptor
remain separate duties. This module neither reserves a GPU nor grants authority.
"""
import gzip
import json
import math
from pathlib import Path
import re

from .automatic_quality_batch_r1 import JsonlSink, execute, initial_rows, read_journal, reconstruct
from .automatic_quality_models_r1 import ROLES, SELF_REF, WEIGHTS, sha
from .automatic_quality_r1 import DIMENSIONS

CONFIG = 'N10-production-config.json'
PURPOSE = 'N10_COMPLETE160_SIX_DIMENSION960_ORIGINAL_METRIC_SCORING'
FILES = ('accepted_inputs', 'model_CPU_acceptance', 'model_CPU_registration', 'model_resources')


def read(path):
    raw = Path(path).read_bytes()
    return json.loads(gzip.decompress(raw) if Path(path).suffix == '.gz' else raw)


def validate(config, registration, inputs, CPU, CPU_registration, resources):
    """Bind the complete accepted input cohort, five-role CPU proof and price."""
    bundle = inputs['input_bundle']
    initial_rows(bundle)
    if (config['purpose'] != PURPOSE or registration['purpose'] != PURPOSE
            or not isinstance(registration['source_revision'], str)
            or re.fullmatch('[0-9a-f]{40}', registration['source_revision']) is None
            or not isinstance(config['run_id'], str)
            or re.fullmatch('wc-paper-n10-[a-z0-9-]+', config['run_id']) is None
            or inputs['status'] != 'N10_ACCEPTED_COMMON_OUTPUT_INPUTS_BOUND_NOT_METRIC_RUNTIME'
            or config['input_bundle_fingerprint'] != bundle['fingerprint']
            or config['measurement_protocol_sha256'] != inputs['measurement_protocol_sha256']
            or config['measurement_protocol_sha256'] != bundle['evaluator_identity']['measurement_protocol_sha256']
            or config['scorer_fingerprint'] != bundle['scorer_fingerprint']
            or config['methods'] != bundle['methods'] or config['dimensions'] != list(DIMENSIONS)
            or config['scope_counts'] != dict(generation_positions=160, metric_positions=960,
                prompt_groups=8, seeds=[17, 43], methods=10, new_generation_paths=0)
            or config['bootstrap_repetitions'] != 4096
            or inputs['static_eligible_prompts'] != 0
            or any(case['static_eligible'] for case in bundle['cases'])):
        raise ValueError('Use all original accepted160/960 positions and their frozen measurement identity')
    pairs = config['comparisons']
    if (not isinstance(pairs, list) or not pairs or len({tuple(p) for p in pairs}) != len(pairs)
            or any(len(p) != 2 or p[0] == p[1] or any(m not in bundle['methods'] for m in p) for p in pairs)):
        raise ValueError('Explicit unique original-method comparison pairs required')
    if (CPU.get('status') != 'N10_ALL_FIVE_MODEL_CPU_INDEPENDENTLY_ACCEPTED_NOT_QUALITY'
            or CPU.get('CPU_accepted') is not True or CPU.get('accepted_models') != 5
            or CPU.get('registered_model_denominator') != 5
            or CPU['registration_sha256'] != config['references']['model_CPU_registration']['sha256']
            or CPU['source_revision'] != CPU_registration['source_revision']
            or CPU_registration['roles'] != list(ROLES)
            or CPU_registration['purpose'] != 'N10_FULL_FIVE_METRIC_MODEL_CPU_ONLY_NOT_SCORING'
            or [row['role'] for row in CPU['rows']] != list(ROLES)
            or any(row['status'] != 'CPU_ROLE_ACCEPTED'
                or row['proof'].get('constructor_source_sha256') != sha(Path(__file__).with_name('automatic_quality_models_r1.py'))
                for row in CPU['rows'])
            or CPU_registration['payload_sha256'].get(SELF_REF) != sha(Path(__file__).with_name('automatic_quality_models_r1.py'))
            or set(resources['resources']) != set(ROLES)
            or any((record['bytes'], record['sha256']) != WEIGHTS[role]
                for role, record in resources['resources'].items())):
        raise ValueError('Complete independent CPU proof of the same original five model constructors required')
    forecast, limit = config['forecast_GPUh'], config['billed_limit_GPUh']
    if (any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
                for v in (forecast, limit, config['cumulative_cap_GPUh'], config['budget_origin_used_GPUh']))
            or not 0 < forecast <= limit
            or config['budget_origin_used_GPUh'] < 0
            or config['cumulative_cap_GPUh'] <= config['budget_origin_used_GPUh']
            or config['whole_card_cost_includes_load_warm_scoring_and_release'] is not True
            or config['generation_latency_claim'] is not False
            or config['weighted_quality_total'] is not None):
        raise ValueError('Whole-card billed scoring price and original cumulative window required')
    return bundle


def load(stage):
    """Read only hash-bound staged inputs; large model weights are checked later."""
    stage = Path(stage).resolve()
    config = read(stage / CONFIG); registration = read(stage / 'registration.json')
    if registration['payload_sha256'].get(CONFIG) != sha(stage / CONFIG):
        raise ValueError('The complete scoring config is not registered in the original stage')
    for relative, digest in registration['payload_sha256'].items():
        path = stage / relative
        if (Path(relative).is_absolute() or '..' in Path(relative).parts or path.is_symlink()
                or not path.resolve().is_relative_to(stage) or sha(path) != digest):
            raise ValueError('Production payload changed before any model import')
    values = []
    for name in FILES:
        ref = config['references'][name]; path = stage / ref['ref']
        if (Path(ref['ref']).is_absolute() or '..' in Path(ref['ref']).parts
                or registration['payload_sha256'].get(ref['ref']) != ref['sha256']
                or sha(path) != ref['sha256']):
            raise ValueError('Original scoring reference is not bound to this source stage')
        values.append(read(path))
    bundle = validate(config, registration, *values)
    return config, registration, bundle, values[1], values[2], values[3]


def admitted_job(config, *, pool, source_revision, config_sha256, gpu_uuid, authority, parent):
    """Check the parent's already-reserved original task without writing a ledger."""
    job = pool['jobs'][config['run_id']]
    if (job['status'] != 'RESERVED_OR_RUNNING' or job['source_revision'] != source_revision
            or job['config_sha256'] != config_sha256
            or job['launch_id'] != authority['launch_id'] or job['gpu_uuid'] != gpu_uuid
            or authority['config_sha256'] != config_sha256 or authority['source_revision'] != source_revision
            or authority['gpu_uuid'] != gpu_uuid or job['forecast_GPUh'] != config['forecast_GPUh']
            or job['billed_limit_GPUh'] != config['billed_limit_GPUh']
            or pool['cap_gpu_hours'] != config['cumulative_cap_GPUh']
            or pool['origin_used_gpu_hours'] != config['budget_origin_used_GPUh']
            or job['supervisor_pid'] != parent['pid'] or job['supervisor_start_ticks'] != parent['start_ticks']
            or parent['state'] in (None, 'Z', 'X')
            or any(name != config['run_id'] and item['status'] == 'RESERVED_OR_RUNNING'
                for name, item in pool['jobs'].items())
            or (config['billed_limit_GPUh'] >= 12 and job['kind'] != 'V2_SPECIFIC_WHOLE_CARD_APPROVAL')):
        raise ValueError('Match the live original supervisor and its already-admitted whole-card reservation')
    return dict(run_id=config['run_id'], launch_id=job['launch_id'], gpu_uuid=gpu_uuid,
                reservation_limit_GPUh=job['billed_limit_GPUh'], ledger_written=False)


def score_complete(bundle, comparisons, factory, output, *, bootstrap_repetitions=4096):
    """Exclusive original journal plus independently rebuilt full-matrix result."""
    output = Path(output)
    sink = JsonlSink(output / 'original-metric-events.jsonl')
    try:
        result = execute(bundle, comparisons, factory, sink, bootstrap_repetitions=bootstrap_repetitions)
    finally:
        sink.close()
    original = read_journal(sink.path)
    rebuilt = reconstruct(bundle, original['events'])
    if rebuilt['final'] != result or original['incomplete_original_tail'] is not None:
        raise ValueError('Original complete scoring journal does not independently rebuild')
    result.update(original_journal_sha256=original['original_sha256'],
                  original_journal_bytes=original['original_bytes'])
    raw = json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2).encode()
    with (output / 'metric-results.json.gz').open('xb') as handle:
        handle.write(gzip.compress(raw))
        handle.flush()
        import os
        os.fsync(handle.fileno())
    return result
