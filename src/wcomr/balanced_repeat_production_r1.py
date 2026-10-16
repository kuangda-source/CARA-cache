"""Full40 production contract and out-of-clock artifacts; no point selection."""
import gzip
import json
from pathlib import Path

from .balanced_repeat_execution_r1 import COUNTS, bind
from .frozen_shared_production_r1 import fingerprint, number, sha

CONFIG = 'configs/wc_paper_N08_balanced_full40_production_r1_20261016.json'
RUN = 'wc-paper-n08-balanced-full40-r1'
CARD = 'WC-PAPER-N08-BALANCED-FULL40-R1'
CPU_RESULT = 'N08-production-CPU-result.json'
CPU_STATUS = 'N08_FULL40_ACTUAL_PRODUCTION_ENTRY_CPU_PASS_NOT_GPU'
STRATEGY = 'WORKING_P_AGE_NONZERO_REBASE'
TIMING = 'SYNCHRONIZED_TEXT_ENCODING_DENOISING_VAE_DECODING'


def validate_contract(config, protocol, shared_config, method_freeze):
    """The five role bindings must already exist in the common-method freeze."""
    if (config['card'] != CARD or config['run_id'] != RUN or config['scope_counts'] != COUNTS
            or config['main_timing'] != TIMING or config['strategy'] != STRATEGY
            or config['memory_policy'] != 'REQUEST_BOUNDARY_GC_ONLY'
            or config['reference_method'] != 'NATIVE35'
            or config['warm_trace_policy'] != 'ALL10_FULL36_GUIDED_TRACE'
            or config['clean_resource_requirement'] != 'NO_CONCURRENT_WORLD_CACHE_GPU_OR_CPU_METRICS'
            or config['autonomy_exclusive_upper_GPUh'] != 12
            or not config['guardrails_enabled'] or not config['resource_boundary_audit']
            or not config['same_round_native_reference']
            or any(config[k] for k in ('training', 'online_teachers', 'F_B_enabled', 'P_ACR',
                                      'T1', 'head_elision', 'deployment_profiling'))):
        raise ValueError('Original full40 timing scope and ordinary inference policies required')
    if (method_freeze['parameters_frozen_from'] != 'DEVELOPMENT_ONLY'
            or method_freeze['final_test_outputs_seen'] is not False
            or method_freeze['method_ids'] != shared_config['method_ids']
            or method_freeze['repeat_timing_bindings'] != config['bindings']):
        raise ValueError('Bind all five timing roles in the original development-only common-method freeze')
    bound = bind(protocol, config['bindings'], shared_config['method_ids'])
    if config['bound_timing_fingerprint'] != fingerprint(bound):
        raise ValueError('Original inputs, order, role bindings or complete matrix changed')
    cost, limit = config['forecast_complete_GPUh'], config['billed_limit_GPUh']
    if (not all(number(v) for v in (cost, limit)) or not 0 < cost <= limit
            or config['cumulative_cap_GPUh'] != shared_config['cumulative_cap_GPUh']
            or config['budget_origin_used_GPUh'] != shared_config['budget_origin_used_GPUh']
            # The original accounting origin stays fixed when the human
            # explicitly increases the cap. Actual launch still requires an
            # exact match to the authoritative ledger and bound authority.
            or not number(config['cumulative_cap_GPUh'])
            or config['cumulative_cap_GPUh'] < 104.97136333301378
            or config['budget_origin_used_GPUh'] != 79.99637737158223):
        raise ValueError('Complete full40 cost and unchanged cumulative budget window required')
    return bound


def read_reference(stage, binding):
    relative = Path(binding['ref'])
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('A stage-local immutable timing reference is required')
    path = Path(stage) / relative
    if sha(path) != binding['sha256']:
        raise ValueError('Frozen timing reference changed: ' + str(relative))
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def validate(project, stage):
    """Reuse accepted numeric/model assets, never N07 permission or GPU scope."""
    from .frozen_shared_production_r1 import CONFIG as SHARED_CONFIG, validate as shared_validate
    stage = Path(stage)
    config = json.loads((stage / CONFIG).read_text())
    references = config['references']
    if set(references) != {'shared_config', 'method_freeze', 'timing_protocol'}:
        raise ValueError('Exactly the registered shared config, freeze and timing protocol references required')
    shared_config = read_reference(stage, references['shared_config'])
    if references['shared_config']['ref'] != SHARED_CONFIG:
        raise ValueError('The original common frozen config cannot be replaced')
    freeze = read_reference(stage, references['method_freeze'])
    protocol = read_reference(stage, references['timing_protocol'])
    if references['method_freeze'] != shared_config['references']['method_freeze']:
        raise ValueError('N07 and N08 must use the identical method-freeze file and SHA')
    bound = validate_contract(config, protocol, shared_config, freeze)
    actual_shared, registration, old, inputs, tables, previous, shared_bound, source_reuse = shared_validate(project, stage)
    if actual_shared != shared_config or shared_bound['method_ids'] != bound['final_shared_method_ids']:
        raise ValueError('Numerically accepted shared executor binding differs')
    return config, registration, old, inputs, tables, previous, bound, source_reuse


def validate_launch_authority(config, bound, registration, proof, authority, *, revision,
                              gpu_uuid, config_sha256, proof_sha256, registration_sha256):
    if (registration['source_revision'] != revision or proof['source_revision'] != revision
            or authority['source_revision'] != revision or proof['status'] != CPU_STATUS or proof['exit_code'] != 0
            or proof['registration_sha256'] != registration_sha256
            or proof['config_sha256'] != config_sha256 or authority['config_sha256'] != config_sha256
            or authority['production_CPU_sha256'] != proof_sha256
            or proof['bound_timing_fingerprint'] != fingerprint(bound)
            or authority['bound_timing_fingerprint'] != fingerprint(bound)
            or authority.get('bound_input_fingerprint') != fingerprint(bound)
            or authority['scope_counts'] != COUNTS or proof['scope_counts'] != COUNTS
            or authority['whole_card_run'] != RUN or authority['gpu_uuid'] != gpu_uuid
            or authority['forecast_complete_GPUh'] != config['forecast_complete_GPUh']
            or authority['billed_limit_GPUh'] != config['billed_limit_GPUh']
            or authority['cumulative_cap_GPUh'] != config['cumulative_cap_GPUh']
            or authority['budget_origin_used_GPUh'] != config['budget_origin_used_GPUh']
            or not authority['direct_user_authorization'] or not authority['user_reply_quote']
            or not authority['launch_id']):
        raise ValueError('A separate whole40 source/CPU/price/UUID launch authority is required')
    allowed = ('STANDING_STRICT_UNDER12', 'SPECIFIC_WHOLE_CARD_APPROVAL') if config['billed_limit_GPUh'] < 12 else (
        'SPECIFIC_WHOLE_CARD_APPROVAL',)
    if authority['kind'] not in allowed:
        raise ValueError('At or above12GPUh requires the specific whole-card human reply')


def clean_registered_jobs(pool, own_run):
    """Only an execution-boundary observation; not a whole-run clean claim."""
    other = [name for name, job in pool['jobs'].items()
             if name != own_run and job['status'] != 'SETTLED']
    if other:
        raise ValueError('Another registered GPU job overlaps clean timing: ' + ','.join(sorted(other)))
    return dict(other_registered_GPU_jobs_active=[],
                observation_only_not_entire_interval_cleanliness=True)


def archive_output(result, planned, directory, output_root, *, expected_shape):
    """CPU tensor serialization and hashes happen after the measured request."""
    import torch
    from .mid_coverage import tree_digest
    directory, output_root = Path(directory).resolve(), Path(output_root).resolve()
    if not directory.is_relative_to(output_root):
        raise ValueError('Out-of-clock artifacts must remain in their original run directory')
    row = dict(result)
    guided, final = row.pop('guided', None), row.pop('final_latent', None)
    if row['status'] == 'TEXT_REJECTED':
        if guided is not None or final is not None:
            raise ValueError('Text rejection cannot create model artifacts')
        return row
    if row['status'] not in ('COMPLETE', 'VIDEO_REJECTED'):
        raise ValueError('Only completed original model paths can be archived')

    def tensor(value):
        return (isinstance(value, torch.Tensor) and value.device.type == 'cpu'
                and tuple(value.shape) == tuple(expected_shape) and bool(torch.isfinite(value).all()))
    if not tensor(final):
        raise ValueError('Actual finite CPU final latent with the declared shape required')
    warm = planned['section'] == 'WARMUP'
    if (warm and (not isinstance(guided, list) or len(guided) != 36 or not all(tensor(t) for t in guided))) or (
            not warm and guided is not None):
        raise ValueError('Exactly all36 warm outputs and zero formal guided copies required')
    directory.mkdir(parents=True, exist_ok=True)
    def store(filename, key, value):
        path = directory / filename
        with path.open('xb') as handle: torch.save({key: value}, handle)
        return dict(path=str(path), sha256=sha(path), bytes=path.stat().st_size)
    if warm:
        row.update(warm_guided_outputs=36, warm_guided_tree_sha256=tree_digest(guided),
                   warm_guided_artifact=store('warm-guided.pt', 'guided', guided))
    row.update(final_latent_sha256=tree_digest(final),
               final_artifact=store('final-latent.pt', 'final_latent', final))
    if row.get('video_path'):
        video = Path(row['video_path']).resolve()
        if not video.is_relative_to(directory):
            raise ValueError('Original video path belongs to another timing run')
        row['video_path'] = str(video)
    return row
