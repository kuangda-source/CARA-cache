"""Offline original-request acceptance after its UUID was leased to R2.

The original capture and acceptor stay immutable. Only the device-idle
assumption is replaced by explicitly attributed, later approved ownership.
All original financial, tensor, video, denominator and statistical gates run.
"""
import ast
from functools import lru_cache
import gzip
import hashlib
import inspect
import json
from pathlib import Path
from textwrap import dedent

ORIGINAL_SHA = 'b93600daff82f236ec99a377f6eb762a0d4df297266785f1f486ae87a4f63997'
LATER_RUN = 'wc-paper-n07-refusal-repair180-r2'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    path = Path(path)
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def bound_later_admission(launch_ref, admission_ref, cpu_acceptance):
    """Recompute the saved admission, without inspecting the current R2 run."""
    from .frozen_repair_gpu_r2 import accept_admission
    launch = read_json(launch_ref)['dispatch']
    receipt = read_json(admission_ref)
    root = Path(__file__).resolve().parents[2]
    capture = Path(receipt['capture_ref'])
    if not capture.is_absolute():
        capture = root / capture
    if (receipt['launch_sha256'] != sha(launch_ref)
            or receipt['capture_sha256'] != sha(capture)):
        raise ValueError('The original later admission evidence changed')
    actual = accept_admission(read_json(capture), launch, cpu_acceptance)
    if (not actual.get('GPU_admitted')
            or any(receipt.get(k) != v for k, v in actual.items())):
        raise ValueError('Use the independently accepted later complete-card admission')
    return launch, receipt


def released_request_context(value, launch, newer_launch, newer_admission):
    from .frozen_shared_acceptance_r1 import original_alive
    supervisor = value['supervisor']
    identities = {
        'supervisor_pid': launch['supervisor_identity'],
        'post_watcher_pid': launch['post_watcher_identity'],
        'child_pid': supervisor['child_identity'],
    }
    if any(original_alive(identity, value['original_processes'].get(key))
           for key, identity in identities.items()):
        raise ValueError('The original request still owns a live handle')
    uuid = launch['gpu_uuid']
    if value['own_GPU'].split(',')[0].strip() != uuid:
        raise ValueError('The captured physical UUID differs')
    own_pids = {r['pid'] for r in identities.values()}
    current = []
    for line in value['compute_apps'].splitlines():
        if not line.strip():
            continue
        fields = line.split(',')
        if len(fields) != 2:
            raise ValueError('An exact UUID and PID observation is required')
        if fields[0].strip() == uuid:
            current.append(int(fields[1].strip()))
    if own_pids.intersection(current):
        raise ValueError('A captured compute process still belongs to the old request')
    old_job = value['pool']['jobs'][launch['run_id']]
    if (old_job['status'] != 'SETTLED'
            or old_job['launch_id'] != launch['launch_id']
            or old_job['billing_sha256'] != value['billing_sha256']
            or old_job['actual_GPUh'] != value['billing']['actual_GPUh']):
        raise ValueError('The original request must have its own settled bill')
    if value['own_UUID_lock_free'] and not current:
        return dict(status='ORIGINAL_REQUEST_RELEASED_DEVICE_CURRENTLY_IDLE',
                    physical_UUID_currently_idle=True, later_results_read=False)
    later = newer_launch
    admitted = newer_admission
    if (value['own_UUID_lock_free'] or later['run_id'] != LATER_RUN
            or later['run_id'] == launch['run_id']
            or later['gpu_uuid'] != uuid or later['launch_id'] == launch['launch_id']
            or later['started_unix'] <= old_job['settled_unix']
            or not admitted.get('GPU_admitted')
            or admitted['status'] != 'N07_REPAIR_ORIGINAL_GPU_ADMISSION_INDEPENDENTLY_ACCEPTED'
            or any(admitted[k] != later[k] for k in
                   ('source_revision', 'launch_id', 'gpu_uuid', 'config_sha256', 'scope_counts'))):
        raise ValueError('A distinct later approved admission must own the reused UUID')
    job = value['pool']['jobs'][LATER_RUN]
    if (job['status'] != 'RESERVED_OR_RUNNING'
            or job['kind'] != 'V2_SPECIFIC_WHOLE_CARD_APPROVAL'
            or any(job[k] != later[k] for k in
                   ('run_id', 'source_revision', 'launch_id', 'gpu_uuid', 'config_sha256',
                    'scope_counts', 'production_CPU_sha256', 'authorization_sha256',
                    'bound_input_fingerprint', 'billed_limit_GPUh'))
            or job['forecast_GPUh'] != later['forecast_complete_GPUh']
            or job['supervisor_pid'] != later['supervisor_identity']['pid']
            or job['supervisor_start_ticks'] != later['supervisor_identity']['start_ticks']
            or not current or set(current) != {admitted['runner_pid']}
            or admitted['runner_pid'] in own_pids):
        raise ValueError('Current reservation and compute PID are not attributed to the later card')
    return dict(status='ORIGINAL_REQUEST_RELEASED_UUID_REUSED_BY_LATER_APPROVED_CARD',
                physical_UUID_currently_idle=False, later_results_read=False,
                later_run_id=LATER_RUN, later_launch_id=later['launch_id'],
                later_registered_runner_pid=admitted['runner_pid'],
                evidence_scope='Saved accepted admission plus current ledger and compute PID; not new R2 health or science acceptance')


@lru_cache(maxsize=1)
def derived_acceptor():
    from . import frozen_shared_acceptance_r1 as original
    name = Path(original.__file__)
    if sha(name) != ORIGINAL_SHA:
        raise ValueError('The original complete180 acceptor changed')
    source = dedent(inspect.getsource(original.accept))
    before = """    if (not value['own_UUID_lock_free'] or value['own_GPU'].split(',')[0].strip() != launch['gpu_uuid']
            or any(line.split(',')[0].strip() == launch['gpu_uuid']
                   for line in value['compute_apps'].splitlines() if line.strip())):
        raise ValueError('Own UUID must be released; other GPUs are independent')"""
    after = """    if not _original_request_device_released(value, launch):
        raise ValueError('Original device ownership is not independently released or attributed')"""
    if source.count(before) != 1:
        raise ValueError('Exactly one original device-idle gate is required')
    changed = source.replace(before, after)
    restored = changed.replace(after, before)
    if restored != source or ast.dump(ast.parse(restored)) != ast.dump(ast.parse(source)):
        raise ValueError('An undeclared scientific or financial gate changed')
    return changed, vars(original), str(name), dict(
        original_acceptor_sha256=ORIGINAL_SHA, inverse_bytes_and_AST_equal=True,
        original_source_written=False, original_capture_fields_written=False,
        original_financial_tensor_video_statistics_gates_unchanged=True)


def accept(value, launch, newer_launch, newer_admission, *, bootstrap_repetitions=4096):
    context = released_request_context(value, launch, newer_launch, newer_admission)
    source, globals_, filename, proof = derived_acceptor()
    namespace = {**globals_, '_original_request_device_released': lambda value_, launch_:
                 bool(released_request_context(value_, launch_, newer_launch, newer_admission))}
    exec(compile(source, filename + '#explicit-prior-request-release', 'exec'), namespace)
    result = namespace['accept'](value, launch, bootstrap_repetitions=bootstrap_repetitions)
    if 'own_GPU_and_finance_released' in result:
        result['original_request_resources_and_finance_released'] = result.pop('own_GPU_and_finance_released')
    return dict(result, original_request_release_context=context,
                original_acceptor_derivation=proof)
