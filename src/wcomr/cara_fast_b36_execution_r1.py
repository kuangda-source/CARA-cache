"""A separately authorized B36, bound to the immutable, settled A32 handoff."""
import copy
import time
from pathlib import Path

from .cara_fast_b36_r1 import bind_handoff, read_handoff
from .cara_fast_binding_r2 import load_card
from .cara_fast_execution_r2 import RUN as A_RUN, SPEC, QUOTE, RA, read, require
from .cara_fast_terminal_r2 import record
from .gpu_budget_pool_v2 import finite, sha
from .wc73_execution_r1 import Pool as CentralPool, admit_host

RUN = 'cara-fast-f19-b36-r1-20261029'
PROFILE = 'plans/cara_next_stage_20261028/mainline/r2/B36_EXECUTION_PROFILE_R1.json'
LIMITS = {'four_card': 5., 'two_card': 5.5}
EXECUTION_SOURCES = (
    'src/wcomr/cara_fast_b36_execution_r1.py',
    'scripts/cara_fast_b36_worker_r1.py',
    'scripts/cara_fast_b36_host_guardian_r1.py',
    'scripts/run_cara_fast_b36_r1.py','scripts/cara_fast_b36_dispatch_r2.py',
    'scripts/dispatch_cara_fast_b36_score_cpu_r2.py',
    'src/wcomr/cara_fast_b36_dispatch_r2.py',
    'plans/cara_next_stage_20261028/mainline/r2/B36_FROZEN_ASSETS_R1.json', PROFILE)


def load_handoff(stage, card, profile):
    paths = {}
    for name, descriptor in profile['A32_handoff_files'].items():
        path = Path(stage)/descriptor['path']
        require(sha(path) == descriptor['sha256'], 'Original A32 file changed: '+name)
        paths[name] = path
    package = read_handoff(paths)
    host, uuid = profile['A_host'], profile['A_gpu_uuid']
    bound = bind_handoff(card, package, host=host, gpu_uuid=uuid, source_root=stage)
    capture = record(package, 'capture')
    launch = record(capture, 'launch')
    require(bound['CPU_fixture_only'] is False, 'A metadata fixture cannot admit a GPU card')
    require(bound['frozen_file_sha256'] == profile['A_frozen_sha256']
            and launch['launch_id'] == profile['A_launch_id'], 'Wrong original A32 continuation')
    bound.update(A_billing_sha256=capture['files']['billing']['sha256'],
                 A_source_revision=launch['source_revision'],
                 A_model_sha256=launch['model_sha256'],
                 A_precision=record(capture, 'precision'),
                 A_runtime_source_sha256=record(capture, 'registration')['runtime_source_sha256'])
    return bound


class Pool(CentralPool):
    """The existing central ledger; an A release never grants B funds or replay."""
    def reserve(self, job, gpu, binding):
        host = job['host']
        limit = LIMITS[host]
        require(job['job_id'] == job['run_id'] == RUN and job['phase'] == 'B'
                and job['physical_paths'] == 36, 'Only the complete registered B36')
        require(binding['CPU_fixture_only'] is False
                and all(binding.get(key) is True for key in (
                    'phase_A_GPU_released', 'phase_A_cost_settled', 'phase_A_technical_accepted')),
                'Accepted real A32 required before B reservation')
        require(job['host'] == binding['host'] and job['gpu_uuid'] == binding['gpu_uuid']
                and job['A_launch_id'] == binding['A_launch_id']
                and job['frozen_file_sha256'] == binding['frozen_file_sha256']
                and job['scope_sha256'] == binding['scope_sha256']
                and job['launch_id'] not in ('', binding['A_launch_id']), 'B handoff identity differs')
        require(job['billed_limit_GPUh'] == limit and finite(job['forecast_GPUh'])
                and 0 < job['forecast_GPUh'] <= limit, 'Complete host B quote required')
        name, capability = {'four_card': ('RTX 6000 Ada', '8.9'),
                            'two_card': ('RTX A6000', '8.6')}[host]
        require(gpu['uuid'] == job['gpu_uuid'] and name in gpu['name']
                and gpu['compute_cap'] == capability and not gpu['pids']
                and gpu['utilization_percent'] == 0 and 0 <= gpu['memory_used_mib'] <= 1024
                and 0 <= time.time()-gpu['unix'] <= 60, 'Fresh idle physical B GPU required')
        with self.transaction() as value:
            require(value is not None and not value.get('budget_overrun_recorded'), 'Valid central ledger required')
            require(RUN not in value['jobs'], 'Recover the original B intent; never replay on either host')
            original = value['jobs'][A_RUN]
            require(original['status'] == 'SETTLED' and original['launch_id'] == binding['A_launch_id']
                    and original['billing_sha256'] == binding['A_billing_sha256']
                    and original['host'] == host and original['gpu_uuid'] == binding['gpu_uuid'],
                    'Original A32 cost must already be settled in the one central ledger')
            admit_host(value, host)
            require(self.accounting(value)['available_gpu_hours'] >= limit, 'Whole B funds required')
            value['jobs'][RUN] = dict(copy.deepcopy(job), status='RESERVED_OR_RUNNING', kind='V2',
                reserved_unix=time.time(), central_ledger_host='four_card')
            self.commit(value, dict(type='FAST_B36_SEPARATE_WHOLE_RESERVATION', job_id=RUN))
            return copy.deepcopy(value)


def admitted_inputs(project, stage):
    """Validate source, the real A handoff and separate human authority before reserve."""
    project, stage = Path(project), Path(stage)
    registration = read(stage/'registration.json')
    require(all(sha(stage/name) == expected for name, expected in registration['payload_sha256'].items()),
            'Staged B source differs')
    require(all(sha(project/'runtime'/name) == expected
                for name, expected in registration['runtime_source_sha256'].items()), 'Pinned runtime differs')
    card = load_card(stage, SPEC)
    profile, quote = read(stage/PROFILE), read(stage/QUOTE)
    require(profile['run_id'] == RUN and profile['phase'] == 'B' and profile['physical_paths'] == 36
            and profile['scope_sha256'] == quote['scope_sha256'] == card['scope_sha256']
            and profile['billing']['owner']=='HOST_GUARDIAN', 'B scope/billing policy differs')
    bound = load_handoff(stage, card, profile)
    require(registration['runtime_source_sha256'] == bound['A_runtime_source_sha256'],
            'B must use the unchanged A pinned runtime')
    authority = read(stage/'pg-GPU-authorization.json')
    host = authority['host']
    limit = LIMITS[host]
    require(authority.get('direct_user_authorization') is True and bool(authority.get('user_quote'))
            and authority.get('new_B36_authorization') is True and authority.get('authorizes_replay') is False,
            'Separate direct human authorization for the new B36 is required')
    expected = dict(run_id=RUN, phase='B', physical_paths=36, whole_GPUh=limit,
        host=bound['host'], gpu_uuid=bound['gpu_uuid'], A_launch_id=bound['A_launch_id'],
        frozen_file_sha256=bound['frozen_file_sha256'], scope_sha256=card['scope_sha256'],
        source_revision=registration['source_revision'], registration_sha256=sha(stage/'registration.json'))
    require(all(authority.get(key) == value for key, value in expected.items()), 'B authority differs')
    require(authority['launch_id'] not in ('', bound['A_launch_id'])
            and quote['host_quotes'][host]['phases']['B']['proposed_hard_GPUh'] == limit,
            'New launch and complete B host quote required')
    for filename, key in [('B36-core-CPU-proof.json', 'core_CPU_proof_sha256'),
                          ('execution-CPU-proof.json', 'CPU_proof_sha256')]:
        proof = read(stage/filename)
        require(proof.get('passed') is True and authority[key] == sha(stage/filename)
                and all(registration['payload_sha256'].get(name) == expected
                        for name, expected in proof['critical_source_sha256'].items()),
                'Affected B CPU acceptance/source differs: '+filename)
        require(host in proof['receipts'] and proof['receipts'][host]['runtime_source_sha256']
                == registration['runtime_source_sha256'], 'CPU/runtime proof differs')
    proof = read(stage/'execution-CPU-proof.json')
    require(set(EXECUTION_SOURCES) <= set(proof['critical_source_sha256']), 'Untested B execution source')
    return card, registration, authority, bound


def validate(project, stage):
    """The running card additionally requires its unique reserved central envelope."""
    card, registration, authority, bound = admitted_inputs(project, stage)
    stage = Path(stage)
    envelope = read(stage/'central-reservation.json')
    require(envelope['central_ledger_host'] == 'four_card' and envelope['new_reservation'] is True,
            'The two-card ledger replica grants no B funds')
    job = envelope['job']
    expected = dict(job_id=RUN, run_id=RUN, phase='B', physical_paths=36,
        host=authority['host'], gpu_uuid=authority['gpu_uuid'], launch_id=authority['launch_id'],
        A_launch_id=bound['A_launch_id'], frozen_file_sha256=bound['frozen_file_sha256'],
        scope_sha256=card['scope_sha256'], source_revision=registration['source_revision'],
        stage=str(stage), registration_sha256=authority['registration_sha256'],
        billed_limit_GPUh=authority['whole_GPUh'], authorization_sha256=sha(stage/'pg-GPU-authorization.json'),
        status='RESERVED_OR_RUNNING')
    require(all(job.get(key) == value for key, value in expected.items()), 'Original B central envelope differs')
    launch_binding = read(stage/'launch-binding.json')
    require(launch_binding['authorization_sha256'] == sha(stage/'pg-GPU-authorization.json')
            and launch_binding['central_reservation_sha256'] == sha(stage/'central-reservation.json')
            and launch_binding['A_handoff_package_sha256'] == bound['package_sha256'], 'B launch binding differs')
    return card, registration, authority, bound
