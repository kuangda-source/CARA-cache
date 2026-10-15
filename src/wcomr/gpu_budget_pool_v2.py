"""Per-device leases and additive, job-scoped accounting.

The legacy W3 writer and its CPU reader retain exclusive ownership of the old
ledger until their terminal receipts exist. The v2 ledger is authoritative for
new jobs; a legacy job is imported with its entire approved limit reserved.
"""
import copy
from contextlib import contextmanager
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import time

SCHEMA = 'WC_GPU_BUDGET_POOL_V2'


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.' + str(os.getpid()) + '.tmp')
    with temporary.open('w') as handle:
        json.dump(value, handle, indent=2, allow_nan=False)
        handle.write('\n'); handle.flush(); os.fsync(handle.fileno())
    os.replace(temporary, path)
    descriptor = os.open(str(path.parent), os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def process_identity(pid):
    try:
        p = Path('/proc') / str(pid)
        fields = (p / 'stat').read_text().split(') ', 1)[1].split()
        return dict(pid=pid, state=fields[0], start_ticks=int(fields[19]),
                    command=(p / 'cmdline').read_bytes().replace(bytes([0]), b' ').decode())
    except FileNotFoundError:
        return dict(pid=pid, state=None, start_ticks=None, command=None)


def same_live_process(identity):
    actual = process_identity(identity['pid'])
    return (actual['state'] not in (None, 'Z', 'X')
            and actual['start_ticks'] == identity['start_ticks'])


class DeviceLease:
    def __init__(self, project, gpu_uuid):
        if not isinstance(gpu_uuid, str) or not re.fullmatch(r'GPU-[A-Za-z0-9-]+', gpu_uuid):
            raise ValueError('An actual immutable GPU UUID is required')
        self.path = Path(project) / '.sync/gpu-locks' / (gpu_uuid + '.lock')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = None

    def acquire(self):
        if self.handle is not None:
            raise ValueError('Device lease already held')
        handle = self.path.open('a+')
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BaseException:
            handle.close(); raise
        self.handle = handle
        return self

    def close(self):
        if self.handle is not None:
            fcntl.flock(self.handle, fcntl.LOCK_UN)
            self.handle.close(); self.handle = None

    def __enter__(self):
        return self.acquire()

    def __exit__(self, *unused):
        self.close()


class BudgetPool:
    def __init__(self, project):
        self.project = Path(project).resolve()
        self.path = self.project / 'reports/gpu-budget-v2.json'
        self.lock_path = self.project / '.sync/gpu-budget-v2.lock'

    @contextmanager
    def transaction(self):
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        with self.lock_path.open('a+') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            value = json.loads(self.path.read_text()) if self.path.exists() else None
            yield value

    @staticmethod
    def accounting(value):
        if (value['schema'] != SCHEMA or not finite(value['cap_gpu_hours'])
                or not finite(value['origin_used_gpu_hours']) or value['origin_used_gpu_hours'] < 0
                or value['cap_gpu_hours'] <= 0):
            raise ValueError('Invalid pool origin or cap')
        used = value['origin_used_gpu_hours']; reserved = 0.
        devices = []
        for job in value['jobs'].values():
            if job['status'] == 'RESERVED_OR_RUNNING':
                if not finite(job['billed_limit_GPUh']) or job['billed_limit_GPUh'] <= 0:
                    raise ValueError('Invalid whole-job reservation')
                reserved += job['billed_limit_GPUh']; devices.append(job['gpu_uuid'])
            elif job['status'] == 'SETTLED':
                actual = job['actual_GPUh']
                if not finite(actual) or actual < 0:
                    raise ValueError('Invalid actual settlement')
                used += actual
            else:
                raise ValueError('Unknown job accounting state')
        if len(set(devices)) != len(devices):
            raise ValueError('Multiple live reservations on one GPU')
        return dict(used_gpu_hours=used, reserved_gpu_hours=reserved,
                    available_gpu_hours=value['cap_gpu_hours'] - used - reserved,
                    gpu_jobs_launched=value['origin_gpu_jobs_launched'] + len(value['jobs']))

    def commit(self, value, event):
        value.update(self.accounting(value))
        value['events'].append(dict(sequence=len(value['events']) + 1, unix=time.time(), **event))
        atomic_json(self.path, value)

    def initialize(self, *, cap, origin_used, origin_jobs, authorization, legacy_job):
        if (not finite(cap) or not finite(origin_used) or not 0 <= origin_used < cap
                or type(origin_jobs) is not int or origin_jobs < 0
                or authorization.get('direct_user_authorization') is not True
                or authorization.get('cumulative_cap_GPUh') != cap
                or authorization.get('autonomy_exclusive_upper_GPUh') != 12
                or not authorization.get('user_reply_quote')):
            raise ValueError('Direct dual-card authority and unchanged finite origin required')
        job = copy.deepcopy(legacy_job)
        if (job['kind'] != 'LEGACY_W3' or job['status'] != 'RESERVED_OR_RUNNING'
                or job['billed_limit_GPUh'] != 12 or not job['source_revision']
                or not job['launch_id'] or not job['gpu_uuid'].startswith('GPU-')):
            raise ValueError('Exact approved legacy W3 reservation required')
        with self.transaction() as existing:
            if existing is not None:
                if (existing['cap_gpu_hours'] != cap or existing['origin_used_gpu_hours'] != origin_used
                        or existing['origin_gpu_jobs_launched'] != origin_jobs
                        or existing['legacy_job_id'] != job['job_id']
                        or any(existing['jobs'][job['job_id']].get(k) != job.get(k)
                               for k in ('gpu_uuid', 'source_revision', 'launch_id', 'supervisor_pid',
                                         'supervisor_start_ticks', 'billed_limit_GPUh', 'stage'))):
                    raise ValueError('Pool already has a different origin; never reset usage')
                return existing
            value = dict(schema=SCHEMA, cap_gpu_hours=cap, origin_used_gpu_hours=origin_used,
                         origin_gpu_jobs_launched=origin_jobs, legacy_job_id=job['job_id'],
                         authorization=authorization, jobs={job['job_id']: job}, events=[])
            if self.accounting(value)['available_gpu_hours'] < 0:
                raise ValueError('Legacy reservation exceeds original balance')
            self.commit(value, dict(type='IMPORT_LEGACY_W3_LIMIT_NO_OLD_LEDGER_WRITE'))
            return value

    def reserve(self, job, gpu):
        job = copy.deepcopy(job)
        forecast, limit = job['forecast_GPUh'], job['billed_limit_GPUh']
        if (not finite(forecast) or not finite(limit) or not 0 < forecast <= limit < 12
                or not job.get('source_revision') or not job.get('config_sha256')
                or not job.get('launch_id') or not job.get('job_id')
                or gpu['uuid'] != job['gpu_uuid'] or 'A6000' not in gpu['name']
                or gpu['compute_cap'] != '8.6' or not finite(gpu['memory_used_mib'])
                or not 0 <= gpu['memory_used_mib'] <= 1024 or gpu['pids']):
            raise ValueError('Fresh idle UUID and a complete strictly-under12 job are required')
        with self.transaction() as value:
            if value is None or value.get('budget_overrun_recorded'):
                raise ValueError('Pool unavailable or an overrun needs reconciliation')
            if job['job_id'] in value['jobs']:
                raise ValueError('Original job exists; do not reserve or launch it again')
            balance = self.accounting(value)
            if limit > balance['available_gpu_hours'] + 1e-10:
                raise ValueError('Whole-job budget would overbook the cumulative cap')
            if any(j['status'] == 'RESERVED_OR_RUNNING' and j['gpu_uuid'] == job['gpu_uuid']
                   for j in value['jobs'].values()):
                raise ValueError('Device already reserved by an original job')
            job.update(status='RESERVED_OR_RUNNING', kind='V2', reserved_unix=time.time())
            value['jobs'][job['job_id']] = job
            self.commit(value, dict(type='RESERVE_WHOLE_JOB', job_id=job['job_id']))
            return copy.deepcopy(value)

    def settle(self, job_id, actual, billing_sha256):
        if not finite(actual) or actual < 0 or not re.fullmatch('[0-9a-f]{64}', billing_sha256):
            raise ValueError('Actual finite cost and immutable billing receipt required')
        with self.transaction() as value:
            if value is None or job_id not in value['jobs']:
                raise ValueError('Unknown original job')
            job = value['jobs'][job_id]
            if job['status'] == 'SETTLED':
                if job['actual_GPUh'] != actual or job['billing_sha256'] != billing_sha256:
                    raise ValueError('Conflicting settlement; preserve the original receipt')
                return copy.deepcopy(value)
            job.update(status='SETTLED', actual_GPUh=actual, billing_sha256=billing_sha256,
                       settled_unix=time.time())
            if actual > job['billed_limit_GPUh']:
                value['budget_overrun_recorded'] = True
            self.commit(value, dict(type='SETTLE_ACTUAL_ADDITIVELY', job_id=job_id))
            return copy.deepcopy(value)

    def read(self):
        with self.transaction() as value:
            if value is None:
                raise ValueError('Pool not initialized')
            if any(value[k] != v for k, v in self.accounting(value).items()):
                raise ValueError('Stored pool totals disagree with job records')
            return copy.deepcopy(value)

    def mirror_after_legacy_post(self, *, post_exit, expected_legacy_pid):
        """Never write the old ledger while the original W3 CPU reader runs."""
        post_exit = Path(post_exit)
        if not post_exit.exists():
            return 'DEFERRED_UNTIL_ORIGINAL_CPU_POST_TERMINAL'
        post = json.loads(post_exit.read_text())
        if (post.get('status') != 'W3_LABEL64_FULL_POST_CPU_TERMINAL'
                or type(post.get('exit_code')) is not int):
            raise ValueError('Original CPU post has no terminal receipt')
        lock_path = self.project / '.sync/f1.lock'
        with lock_path.open('a+') as old_lock:
            try:
                fcntl.flock(old_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return 'DEFERRED_OLD_PROJECT_LOCK_STILL_OWNED'
            with self.transaction() as value:
                legacy = value['jobs'][value['legacy_job_id']]
                if legacy['supervisor_pid'] != expected_legacy_pid or legacy['status'] != 'SETTLED':
                    raise ValueError('Original W3 cost must be settled first')
                # New jobs use only the pool. The permanent inflight protocol
                # marker makes old unconverted admission functions refuse.
                old_path = self.project / 'reports/budget.json'
                old = json.loads(old_path.read_text())
                if old['cap_gpu_hours'] != value['cap_gpu_hours']:
                    raise ValueError('Original cumulative cap changed')
                old.update(used_gpu_hours=value['used_gpu_hours'],
                           gpu_jobs_launched=value['gpu_jobs_launched'],
                           status='GPU_BUDGET_V2_AUTHORITATIVE_COMPATIBILITY_MIRROR',
                           wc_gpu_v2_inflight_protocol=dict(authoritative='reports/gpu-budget-v2.json',
                               reason='USE_UUID_LEASES_AND_JOB_SCOPED_RESERVATIONS'),
                           reserved_gpu_hours=value['reserved_gpu_hours'],
                           available_gpu_hours=value['available_gpu_hours'])
                old.pop('wc_w3_label64_inflight', None)
                atomic_json(old_path, old)
                return 'OLD_LEDGER_MIRRORED_AFTER_ORIGINAL_CPU_POST'
