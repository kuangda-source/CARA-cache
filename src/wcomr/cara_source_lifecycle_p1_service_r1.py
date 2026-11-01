"""Bind one host FIT service to a prospective P1 guardian's original lifetime.

This component cannot reserve, dispatch a GPU, or create a bill. The admitted
outer guardian starts it after its epoch exists and closes it before billing.
"""
import copy
import os
from pathlib import Path
import subprocess
import sys
import time

from .cara_budget_original_handles_r1 import bind_original_process, observe_original_process
from .cara_budget_search_journal_r1 import OriginalQueryUnknown, create_record, read_record
from .cara_budget_supervisor_r1 import stop_original
from .cara_fast_fidelity_r1 import file_sha
from .cara_fast_spec_r1 import digest
from .cara_source_lifecycle_fit_broker_r1 import BOOTSTRAP, prepare, paths, operational_status
from .cara_source_lifecycle_p1_clock_r1 import OriginalAllocationClock
from .cara_source_lifecycle_p1_plan_r1 import validate as validate_card

SOURCE = 'src/wcomr/cara_source_lifecycle_p1_service_r1.py'
CARD = 'plans/cara_next_stage_20261101/source_lifecycle/V1_P1_WHOLE_MANIFEST_R1.json'
PRECISION = 'configs/cara_endpoint_proposal.json'
KIND = 'CARA_SOURCE_LIFECYCLE_V1_P1_FULL146'


def binding(project, stage, guardian, environment):
    """The runner reads this same sealed context; it never creates a service."""
    project, stage = Path(project), Path(stage)
    launch, authority = read_record(stage/'GPU-launch.json'), read_record(stage/'GPU-authorization.json')
    registration = read_record(stage/'registration.json')
    card = read_record(stage/CARD)
    validate_card(card)
    keys = ('run_id', 'launch_id', 'host', 'gpu_uuid', 'stage', 'source_revision', 'scope_sha256', 'billed_limit_GPUh')
    if (not project.is_absolute() or stage.parent != project/'.sync'
            or launch['stage'] != str(stage) or launch['scope_sha256'] != card['scope_sha256']
            or any(guardian[k] != launch[k] or authority[k] != launch[k] for k in keys)
            or launch['CPU_fixture_only'] is not False or authority['CPU_fixture_only'] is not False
            or authority['card_kind'] != KIND or authority['execution_authorized'] is not True
            or authority['authorization_basis'] != 'DIRECT_USER_SINGLE_CARD' or not authority['user_quote']
            or authority['authorizes_replay'] is not False
            or guardian['original_handles']['guardian'] != launch['guardian_identity']
            or guardian['original_handles']['guardian'] != bind_original_process(os.getpid())
            or launch['registration_sha256'] != file_sha(stage/'registration.json')
            or launch['authorization_sha256'] != file_sha(stage/'GPU-authorization.json')
            or registration['payload_sha256'][SOURCE] != file_sha(__file__)
            or registration['payload_sha256'][CARD] != file_sha(stage/CARD)
            or registration['payload_sha256'][PRECISION] != file_sha(stage/PRECISION)):
        raise ValueError('Exact admitted P1 original guardian/card/authority/source required')
    context = {k: launch[k] for k in keys}
    context.update(CPU_fixture_only=False, phase='SOURCE_LIFECYCLE_V1_P1',
        hard_GPUh=launch['billed_limit_GPUh'], guardian_started_monotonic=guardian['started_monotonic'],
        launch_sha256=file_sha(stage/'GPU-launch.json'), registration_sha256=launch['registration_sha256'],
        admission_sha256=launch['admission_sha256'],
        model_precision_sha256=read_record(stage/PRECISION)['precision_sha256'])
    clock = OriginalAllocationClock(guardian, context)
    root = project/'outputs'/context['run_id']
    spec = dict(schema='CARA_V1_INTERNAL_FIT_BROKER_BINDING_R1', project=str(project), stage=str(stage),
        context=context, profile=card['profile'], artifact_root=str(root/'algorithm'),
        queue=str(root/'internal-FIT-queue'), environment=copy.deepcopy(environment), CPU_fixture_only=False,
        registration_sha256=file_sha(stage/'registration.json'), GPU_launch_sha256=file_sha(stage/'GPU-launch.json'),
        uid=os.getuid(), gid=os.getgid(),
        work_stop_monotonic=guardian['started_monotonic']+launch['billed_limit_GPUh']*3600-600)
    return spec, clock


class HeldFITService:
    def __init__(self, project, stage, environment):
        self.project, self.stage = Path(project), Path(stage)
        self.environment = copy.deepcopy(environment)
        self.spec = self.clock = self.child = self.identity = None
        self.start_attempted = self.close_attempted = False

    def start(self, guardian):
        if self.start_attempted:
            raise OriginalQueryUnknown('Original host FIT service already attempted; recover only')
        self.start_attempted = True
        self.spec, self.clock = binding(self.project, self.stage, guardian, self.environment)
        prepare(self.spec)
        queue, _ = paths(self.spec)
        command = [sys.executable, str(self.stage/BOOTSTRAP), 'serve', '--queue', str(queue)]
        create_record(queue/'guardian-service-intent.json', dict(command=command, command_sha256=digest(command),
            binding_sha256=digest(self.spec), guardian_identity=guardian['original_handles']['guardian'], no_replay=True))
        with (queue/'service.log').open('x') as log:
            self.child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                env=dict(os.environ, CUDA_VISIBLE_DEVICES='', NVIDIA_VISIBLE_DEVICES='void',
                         OPENBLAS_NUM_THREADS='2', OMP_NUM_THREADS='2'), start_new_session=True)
        self.identity = bind_original_process(self.child.pid)
        create_record(queue/'guardian-service-child.json', dict(identity=self.identity,
            launch_intent_sha256=file_sha(queue/'guardian-service-intent.json')))
        deadline = time.monotonic()+30
        while not (queue/'service-start.json').exists():
            self.clock()
            if self.child.poll() is not None:
                raise RuntimeError('Original host FIT service failed before its start witness')
            if time.monotonic() >= deadline:
                raise OriginalQueryUnknown('Original host FIT start remains unresolved')
            time.sleep(.05)
        started = read_record(queue/'service-start.json')
        if (started['binding_sha256'] != digest(self.spec)
                or any(started['identity'][k] != self.identity[k] for k in ('pid', 'start_ticks', 'host_view'))):
            raise ValueError('Original host FIT service start differs')
        self.identity = started['identity']
        return dict(binding_sha256=digest(self.spec), identity=self.identity, clock_owner='HOST_GUARDIAN',
                    started_unix=started['started_unix'], new_GPU_bill=False)

    def check(self):
        self.clock()
        if self.child is None or self.child.poll() is not None:
            raise RuntimeError('Original host FIT service exited while the GPU entry was active')
        if observe_original_process(self.identity)['original_live'] is not True:
            raise OriginalQueryUnknown('Original host FIT service liveness unresolved')

    def close(self):
        """One bounded stop of this original service and its owned CPU query."""
        if self.close_attempted:
            raise OriginalQueryUnknown('Original service close already attempted; read original witness')
        self.close_attempted = True
        if self.spec is None:
            return dict(complete=True, kind='SERVICE_NOT_PREPARED', new_GPU_bill=False)
        queue, _ = paths(self.spec)
        request = queue/'stop-request.json'
        stop = dict(context_sha256=digest(self.spec['context']))
        if request.exists():
            if read_record(request) != stop:
                raise ValueError('Original guardian service stop request changed')
        else:
            create_record(request, stop)
        if self.child is None:
            # Once preparation begins, a missing Popen handle is not proof that
            # the service was absent; keep that original uncertainty visible.
            raise OriginalQueryUnknown('Original service preparation exists without a child witness')
        try:
            self.child.wait(timeout=40)
        except subprocess.TimeoutExpired:
            stop_original(self.child, self.identity)
        if observe_original_process(self.identity)['original_live'] is not False:
            raise OriginalQueryUnknown('Original FIT service closure unresolved')
        terminal_file = queue/'service-terminal.json'
        if not terminal_file.exists():
            raise OriginalQueryUnknown('Original host service ended without its cleanup witness')
        terminal = read_record(terminal_file)
        if terminal['binding_sha256'] != digest(self.spec):
            raise ValueError('Original host FIT service terminal differs')
        states = operational_status(self.spec)
        active = set(states['statuses'])-{'ACCEPTED_INTERNAL', 'ORIGINAL_FIT_FAILED'}
        if active:
            raise OriginalQueryUnknown('Original CPU query closure unresolved: '+','.join(sorted(active)))
        result = dict(complete=True, kind='ORIGINAL_HOST_FIT_SERVICE_TERMINAL', identity=self.identity,
            binding_sha256=digest(self.spec), terminal_sha256=file_sha(terminal_file),
            exit_code=self.child.returncode, terminal_error=terminal['error'],
            ended_unix=terminal['ended_unix'], counts=states, new_GPU_bill=False)
        create_record(queue/'guardian-service-closed.json', result)
        return result
