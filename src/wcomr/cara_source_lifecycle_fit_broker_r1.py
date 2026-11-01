"""Once-only host CPU scoring for the prospective held-allocation P1 card.

The GPU client exchanges complete manifests and sealed results through one
owned directory. Only the host service constructs Docker commands. Existing
GPU admission/billing and released-card scoring remain separate boundaries.
"""
import copy
import fcntl
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time

from .cara_budget_original_handles_r1 import bind_original_process, observe_original_process
from .cara_budget_search_journal_r1 import OriginalQueryUnknown, create_record, read_record, sync_directory
from .cara_budget_supervisor_r1 import stop_original
from .cara_fast_fidelity_r1 import file_sha
from .cara_fast_spec_r1 import digest, policy_from_mask, profile_from
from .cara_read_write_score_capture_r1 import inspect_original, container_time, IMAGE
from .cara_source_lifecycle_fit_scores_r1 import (
    bind_scorer, validate_config, accept_internal_scores, BOUND, SOURCES, WORKER,
)
from .cara_source_lifecycle_p1_clock_r1 import OriginalAllocationClock
from .gpu_budget_pool_v2 import atomic_json

SOURCE = 'src/wcomr/cara_source_lifecycle_fit_broker_r1.py'
BOOTSTRAP = 'scripts/cara_source_lifecycle_fit_broker_r1.py'
REQUIRED = (*SOURCES, SOURCE, BOOTSTRAP)


def paths(spec, candidate=None):
    project, stage = Path(spec['project']), Path(spec['stage'])
    context = spec['context']
    if (not project.is_absolute() or stage.parent != project/'.sync'
            or not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', context['run_id'])):
        raise ValueError('Original isolated P1 project/stage/run paths required')
    output = project/'outputs'/context['run_id']
    queue = output/'internal-FIT-queue'
    if Path(spec['queue']) != queue or Path(spec['artifact_root']) != output/'algorithm':
        raise ValueError('Only this original card output and artifact root may be used')
    if candidate is None:
        return queue, output/'internal-FIT-scores'
    if not isinstance(candidate, str) or not re.fullmatch(r'[0-9a-f]{64}', candidate):
        raise ValueError('Full original candidate fingerprint required')
    return queue/('score-'+candidate), output/'internal-FIT-scores'/('score-'+candidate)


def verify_source(spec, *, full=False):
    stage, project, context = Path(spec['stage']), Path(spec['project']), spec['context']
    paths(spec)
    reg_file = stage/'registration.json'
    reg = read_record(reg_file)
    if (file_sha(reg_file) != spec['registration_sha256'] or reg['host'] != 'two_card'
            or (reg.get('source_revision') or reg.get('parent_git_revision')) != context['source_revision']
            or spec['CPU_fixture_only'] is not context['CPU_fixture_only']):
        raise ValueError('Original source/registration/host binding differs')
    names = reg['payload_sha256'] if full else REQUIRED
    if (not set(REQUIRED) <= set(reg['payload_sha256'])
            or any(file_sha(stage/name) != reg['payload_sha256'][name] for name in names)
            or reg['payload_sha256'][SOURCE] != file_sha(__file__)):
        raise ValueError('Registered broker and scorer sources differ')
    if full and any(file_sha(project/'runtime'/name) != value for name, value in reg['runtime_source_sha256'].items()):
        raise ValueError('Original pinned runtime differs')
    if not spec['CPU_fixture_only']:
        authority = read_record(stage/'GPU-authorization.json')
        if (authority['card_kind'] != 'CARA_SOURCE_LIFECYCLE_V1_P1_FULL146'
                or authority['CPU_fixture_only'] is not False or authority['execution_authorized'] is not True
                or authority['authorization_basis'] != 'DIRECT_USER_SINGLE_CARD'
                or not authority['user_quote']
                or authority['billed_limit_GPUh'] != context['hard_GPUh']
                or spec['work_stop_monotonic'] != context['guardian_started_monotonic']+context['hard_GPUh']*3600-600
                or any(authority[k] != context[k] for k in ('run_id', 'source_revision', 'scope_sha256', 'launch_id', 'host', 'gpu_uuid'))
                or file_sha(stage/'GPU-launch.json') != spec['GPU_launch_sha256']):
            raise ValueError('Existing approved original P1 allocation required; old card authority is not reusable')


def prepare(spec):
    """Called once by the enclosing admitted guardian, before the GPU client."""
    verify_source(spec, full=True)
    queue, outputs = paths(spec)
    queue.mkdir(parents=True, mode=0o700)
    sync_directory(queue.parent)
    outputs.mkdir(mode=0o700)
    create_record(queue/'binding.json', spec)
    create_record(queue/'service.lock', {})


def validate_query(spec, config):
    validate_config(config, cpu_validation=spec['CPU_fixture_only'])
    packet, context = config['packet'], spec['context']
    if (packet['context_sha256'] != digest(context)
            or any(packet[k] != context[k] for k in ('source_revision', 'launch_id'))
            or config['torch_home'] != spec['environment']['torch_home']
            or config['piq_site'] != spec['environment']['piq_site']
            or config['weights_sha256'] != spec['environment']['weights_sha256']):
        raise ValueError('Complete query is outside this original card/metric environment')
    root = Path(spec['artifact_root']).resolve()
    profile = profile_from(spec['profile'])
    for pair in packet['pairs']:
        for side in ('candidate', 'reference'):
            descriptor = pair[side]
            if any(not Path(descriptor[k]).resolve().is_relative_to(root) for k in ('path', 'proof_path')):
                raise ValueError('Only original card artifacts may enter internal FIT scoring')
        proof = read_record(Path(pair['candidate']['proof_path']))
        history = proof['semantic_history']
        if (len(history) != 36 or any(h['actual'] not in ('D', 'C') or h['fallback_reason'] is not None for h in history)
                or proof['timing'] != 'CLEAN'):
            raise ValueError('Registered full pure-C candidate without fallback required')
        dense = [i for i, h in enumerate(history, 1) if h['actual'] == 'D']
        if len(dense) not in (19, 22) or policy_from_mask(profile, dense)['fingerprint'] != packet['candidate_id']:
            raise ValueError('Candidate is not in the same19D/22D grammar as the V1 DP')


def score_command(spec, config, directory):
    from four_card_bank24_execution_tools_r1 import process_environment
    from four_card_policy_assets_port_r1 import container_command
    stage, project, directory = Path(spec['stage']), Path(spec['project']), Path(directory)
    _, expected = paths(spec, config['packet']['candidate_id'])
    if directory != expected:
        raise ValueError('Original score output path required')
    env = process_environment(project, directory/'caches')
    env.update(TORCH_HOME=config['torch_home'], TORCHINDUCTOR_COMPILE_THREADS='1')
    label = digest(config)
    command = container_command(project, stage, 'cpu-worker', label, env, spec['uid'], spec['gid'])
    name = 'cara-p1-fit-'+spec['context']['launch_id']+'-'+config['packet']['candidate_id']
    command[command.index('--name')+1] = name
    command[command.index('--memory')+1] = '8g'
    command[command.index(str(stage)+':'+str(stage)+':rw')] = str(stage)+':'+str(stage)+':ro'
    index = command.index('--entrypoint')
    command[index:index] = ['--memory-swap', '8g', '--cpuset-cpus', '26,27',
                          '--cidfile', str(directory/'container.cid'), '-v', str(directory)+':'+str(directory)+':rw']
    end = command.index('--entrypoint')+3
    command = command[:end]+[str(stage/WORKER), '--manifest', str(directory/'manifest.json'),
                            '--output', str(directory/'scores.json')]
    if spec['CPU_fixture_only']:
        command.append('--cpu-validation')
    return command


def validate_container(container, binding, spec, config):
    _, directory = paths(spec, config['packet']['candidate_id'])
    stage, project = Path(spec['stage']), Path(spec['project'])
    state, host, settings = container['State'], container['HostConfig'], container['Config']
    command = binding['command']
    if (container['Id'] != binding['container_id'] or container['Name'] != '/'+command[command.index('--name')+1]
            or container['Image'] != IMAGE or settings['Labels']['wcomr.manifest'] != digest(config)
            or host['NanoCpus'] != 2*10**9 or host['Memory'] != host['MemorySwap'] or host['Memory'] != 8*2**30
            or host['CpusetCpus'] != '26,27' or host['DeviceRequests'] not in (None, [])
            or host['Devices'] not in (None, []) or host['CapAdd'] not in (None, [])
            or host['Privileged'] is not False or host['NetworkMode'] != 'none' or host['PidMode'] != 'host'
            or host['ReadonlyRootfs'] is not True or host['AutoRemove'] is not False
            or host['RestartPolicy']['Name'] != 'no'):
        raise ValueError('Original non-restarting2CPU8GiB/GPU-hidden score container differs')
    mounts = [(m['Source'], m['Destination'], m['RW']) for m in container['Mounts'] if m['Type'] == 'bind']
    expected = [(str(project), str(project), False), (str(stage), str(stage), False),
                (str(directory), str(directory), True)]
    if (sorted(mounts) != sorted(expected)
            or any(m['Type'] != 'bind' and (m['Type'] != 'tmpfs' or m['Destination'] != '/tmp') for m in container['Mounts'])):
        raise ValueError('Only readonly sources and the sole original CPU output may be mounted')
    env = dict(item.split('=', 1) for item in settings['Env'])
    end = command.index('--entrypoint')
    if (env.get('CUDA_VISIBLE_DEVICES') != '' or env.get('NVIDIA_VISIBLE_DEVICES') != 'void'
            or env.get('PYTHONPATH') != str(stage/'scripts')+':'+str(stage/'src')
            or settings['WorkingDir'] != str(project/'runtime')
            or settings['User'] != str(spec['uid'])+':'+str(spec['gid'])
            or settings['Entrypoint'] != [command[end+1]] or settings['Cmd'] != command[end+3:]):
        raise ValueError('Original scorer environment/user/entrypoint differs')
    return state, host


def status_file(spec, candidate, status, **values):
    query, _ = paths(spec, candidate)
    atomic_json(query/'status.json', dict(status=status, context_sha256=digest(spec['context']),
        observed_unix=time.time(), complete_FIT_denominator=2, scientific_scores_exposed=False,
        GPU_submissions=0, ledger_written=False, **values))


class Client:
    def __init__(self, spec):
        self.spec = copy.deepcopy(spec)
        self.queue, _ = paths(spec)
        if read_record(self.queue/'binding.json') != spec:
            raise ValueError('Original host service binding required; client cannot create a service')

    def __call__(self, packet, unused_output):
        config = bind_scorer(packet, self.spec['environment'], cpu_validation=self.spec['CPU_fixture_only'])
        validate_query(self.spec, config)
        query, _ = paths(self.spec, packet['candidate_id'])
        if not query.exists():
            if len(list(self.queue.glob('score-*'))) >= 42:
                raise ValueError('Original maximum42 distinct complete FIT queries reached')
            query.mkdir(mode=0o700)
            sync_directory(query.parent)
            create_record(query/'request.json', config)
        elif read_record(query/'request.json') != config:
            raise ValueError('Original query cannot be replaced or rescored with changed inputs')
        deadline = min(self.spec['work_stop_monotonic'], time.monotonic()+BOUND['wall_seconds']+30)
        while True:
            response = query/'response.json'
            if response.exists():
                record = read_record(response)
                if record['config_sha256'] != digest(config) or digest(record['payload']) != record['payload_sha256']:
                    raise ValueError('Original complete query response changed')
                if record['status'] != 'ACCEPTED_INTERNAL':
                    raise RuntimeError('Original full FIT query failed; retain denominator and never rescore')
                return record['payload']
            if time.monotonic() >= deadline:
                raise OriginalQueryUnknown('Original FIT response unresolved; recover original service/container only')
            service = read_record(self.queue/'service-start.json')
            if (service['binding_sha256'] != digest(self.spec)
                    or observe_original_process(service['identity'])['original_live'] is not True):
                raise OriginalQueryUnknown('Original host score service is not confirmed live')
            time.sleep(1.)


class Host:
    def __init__(self, spec, clock):
        if not spec['CPU_fixture_only'] and (not isinstance(clock, OriginalAllocationClock)
                                            or clock.context != spec['context']):
            raise ValueError('Original live allocation clock required for host score service')
        verify_source(spec, full=True)
        self.spec, self.clock = copy.deepcopy(spec), clock
        self.queue, _ = paths(spec)
        if read_record(self.queue/'binding.json') != spec:
            raise ValueError('Original host score service binding differs')

    @classmethod
    def reader(cls, spec):
        """Original terminal reader remains usable after the guardian has ended."""
        verify_source(spec, full=True)
        result = cls.__new__(cls)
        result.spec, result.clock = copy.deepcopy(spec), None
        result.queue, _ = paths(spec)
        if read_record(result.queue/'binding.json') != spec:
            raise ValueError('Original terminal reader binding differs')
        return result

    def recover_query(self, candidate):
        query, output = paths(self.spec, candidate)
        config = read_record(query/'request.json')
        validate_query(self.spec, config)
        intent_file = query/'launch-intent.json'
        if not intent_file.exists():
            return dict(status='ORIGINAL_FIT_UNKNOWN', dispatch_allowed=False)
        binding = read_record(intent_file)
        if (binding['config_sha256'] != digest(config) or binding['command_sha256'] != digest(binding['command'])
                or binding['command'] != score_command(self.spec, config, output)
                or read_record(output/'manifest.json') != config):
            raise ValueError('Original bound scorer intent/command/config changed')
        cid, cli_file = output/'container.cid', query/'cli-start.json'
        if not cid.exists() or not cli_file.exists():
            return dict(status='ORIGINAL_FIT_UNKNOWN', dispatch_allowed=False)
        binding['container_id'] = cid.read_text().strip()
        if not re.fullmatch(r'[0-9a-f]{64}', binding['container_id']):
            raise ValueError('Original container ID is invalid')
        cli = read_record(cli_file)
        if cli['launch_intent_sha256'] != file_sha(intent_file):
            raise ValueError('Original scorer CLI binding changed')
        observed = observe_original_process(cli['identity'])
        inspection = inspect_original(binding['container_id'])
        if inspection['status'] != 'OBSERVED' or observed['original_live'] is None:
            return dict(status='ORIGINAL_FIT_UNKNOWN', dispatch_allowed=False)
        container = inspection['container']
        state, host = validate_container(container, binding, self.spec, config)
        if state['Running'] or observed['original_live'] is True or state['Status'] in ('created', 'paused', 'restarting'):
            return dict(status='ORIGINAL_FIT_ACTIVE', dispatch_allowed=False)
        if state['Status'] != 'exited' or state['Pid'] != 0:
            return dict(status='ORIGINAL_FIT_UNKNOWN', dispatch_allowed=False)
        if state['ExitCode'] != 0 or state['OOMKilled']:
            return dict(status='ORIGINAL_FIT_FAILED', dispatch_allowed=False, complete_FIT_denominator=2)
        terminal_file = query/'cli-terminal.json'
        if not terminal_file.exists():
            return dict(status='ORIGINAL_FIT_UNKNOWN', dispatch_allowed=False)
        terminal = read_record(terminal_file)
        if terminal['identity'] != cli['identity'] or terminal['launch_intent_sha256'] != file_sha(intent_file):
            raise ValueError('Original CLI terminal differs')
        if terminal['exit_code'] != 0 or terminal['error'] is not None:
            return dict(status='ORIGINAL_FIT_FAILED', dispatch_allowed=False, complete_FIT_denominator=2)
        worker = read_record(output/'scores-intent.json')
        if worker['config_sha256'] != digest(config) or worker['no_replay'] is not True:
            raise ValueError('Original CPU worker intent differs')
        worker_observation = observe_original_process(worker['original_identity'])
        if worker_observation['original_live'] is not False:
            return dict(status='ORIGINAL_FIT_UNKNOWN', dispatch_allowed=False)
        result = read_record(output/'scores.json')
        started, ended = container_time(state['StartedAt']), container_time(state['FinishedAt'])
        if not started <= result['started_unix'] <= result['ended_unix'] <= ended:
            raise ValueError('Original scorer result is outside its container interval')
        execution = dict(config_sha256=digest(config), result_sha256=digest(result),
            source_sha256=config['source_sha256'], original_identity=worker['original_identity'],
            original_process_ended=True, original_observation=worker_observation,
            cli_observation=observed, exit_code=0, GPU_hidden=True, wall_seconds=ended-started,
            host_config=host, container_state=state, container_id=binding['container_id'])
        execution_file = output/'execution.json'
        if execution_file.exists():
            original_execution = read_record(execution_file)
            # New liveness observations have new timestamps. They must not
            # rewrite the original execution witness or its accepted digest.
            if any(original_execution[k] != value for k, value in execution.items()
                   if k not in ('original_observation', 'cli_observation')):
                raise ValueError('Original sealed CPU execution changed')
            execution = original_execution
        accepted = accept_internal_scores(config, result, execution, cpu_validation=self.spec['CPU_fixture_only'])
        response = dict(status='ACCEPTED_INTERNAL', config_sha256=digest(config),
                        payload=accepted, payload_sha256=digest(accepted))
        saved = query/'response.json'
        if saved.exists():
            if read_record(saved) != response:
                raise ValueError('Original accepted query result changed')
        else:
            if not execution_file.exists():
                create_record(execution_file, execution)
            create_record(saved, response)
        status_file(self.spec, candidate, 'ACCEPTED_INTERNAL', original_container_id=binding['container_id'])
        return dict(status='ORIGINAL_COMPLETE_FIT_ACCEPTED', dispatch_allowed=False)

    def dispatch_query(self, candidate):
        query, output = paths(self.spec, candidate)
        if (query/'launch-intent.json').exists():
            return self.recover_query(candidate)
        if self.clock is None:
            raise OriginalQueryUnknown('Terminal reader cannot admit a new CPU query')
        verify_source(self.spec)
        config = read_record(query/'request.json')
        validate_query(self.spec, config)
        self.clock()
        if time.monotonic()+BOUND['wall_seconds']+30 > self.spec['work_stop_monotonic']:
            raise ValueError('Original work deadline lacks CPU score and exit reserve')
        available = int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines()
                             if line.startswith('MemAvailable:')))*1024
        if not {26, 27} <= os.sched_getaffinity(0) or available < 12*2**30 or shutil.disk_usage(query).free < 2*2**30:
            raise ValueError('Fresh CPU26/27 memory/disk admission failed')
        checkpoint = Path(config['torch_home'])/'hub/checkpoints/alexnet-owt-7be5be79.pth'
        if (file_sha(checkpoint) != '7be5be791159472b1fbf3c69796f7cb30dca7ad8466c2df70058c37116cdee02'
                or not (Path(config['piq_site'])/'piq/__init__.py').is_file()
                or not all(file_sha(path) == value for path, value in config['weights_sha256'].items())):
            raise ValueError('Original offline Alex/PIQ weights and assets required')
        if output.exists() or (query/'cli-start.json').exists():
            raise OriginalQueryUnknown('Original partial CPU preparation exists: recovery only')
        output.mkdir(mode=0o700)
        create_record(output/'manifest.json', config)
        command = score_command(self.spec, config, output)
        name = command[command.index('--name')+1]
        original = subprocess.run(['docker', 'inspect', name], capture_output=True, text=True, timeout=20)
        if original.returncode != 1 or original.stderr.strip() not in (
                'Error: No such object: '+name, 'Error: No such container: '+name):
            raise OriginalQueryUnknown('Existing/unknown original CPU container: recovery only')
        intent = dict(config_sha256=digest(config), binding_sha256=digest(self.spec),
            command=command, command_sha256=digest(command), created_unix=time.time(), no_replay=True)
        create_record(query/'launch-intent.json', intent)
        identity = None
        child = None
        error, code = None, None
        with (output/'cli.log').open('x') as log:
            try:
                child = subprocess.Popen([sys.executable, str(Path(self.spec['stage'])/BOOTSTRAP),
                    'cpu-cli', '--queue', str(self.queue), '--candidate', candidate], stdin=subprocess.DEVNULL,
                    stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
                    env=dict(os.environ, CUDA_VISIBLE_DEVICES='', NVIDIA_VISIBLE_DEVICES='void'))
                identity = bind_original_process(child.pid)
                status_file(self.spec, candidate, 'ORIGINAL_CPU_ACTIVE', cli_identity=identity)
                deadline = min(time.monotonic()+BOUND['wall_seconds'], self.spec['work_stop_monotonic'])
                while child.poll() is None:
                    self.clock()
                    stop = self.queue/'stop-request.json'
                    if stop.exists():
                        if read_record(stop)['context_sha256'] != digest(self.spec['context']):
                            raise ValueError('Foreign service stop request')
                        raise InterruptedError('Original guardian requested service stop')
                    if time.monotonic() >= deadline:
                        raise TimeoutError('Original complete FIT CPU deadline reached')
                    try:
                        child.wait(timeout=min(2., max(.001, deadline-time.monotonic())))
                    except subprocess.TimeoutExpired:
                        continue
                code = child.returncode
            except BaseException as caught:
                error = dict(type=type(caught).__name__, message=str(caught))
                # Never stop by name: only the CID written by this original CLI
                # and validated against the full frozen command may be stopped.
                cid_file = output/'container.cid'
                if cid_file.exists():
                    cid = cid_file.read_text().strip()
                    inspection = inspect_original(cid)
                    if inspection['status'] != 'OBSERVED':
                        raise OriginalQueryUnknown('Original CPU container is unknown during cleanup') from caught
                    state, _ = validate_container(inspection['container'], dict(intent, container_id=cid), self.spec, config)
                    if state['Running']:
                        subprocess.run(['docker', 'stop', '--time', '10', cid], capture_output=True, timeout=20, check=True)
            finally:
                if child is not None:
                    stop_original(child, identity)
                    code = child.wait(timeout=10)
                cli_file = query/'cli-start.json'
                if cli_file.exists():
                    cli = read_record(cli_file)
                    create_record(query/'cli-terminal.json', dict(identity=cli['identity'],
                        launch_intent_sha256=file_sha(query/'launch-intent.json'), exit_code=code,
                        error=error, ended_unix=time.time()))
        return self.recover_query(candidate)

    def serve(self):
        if self.clock is None:
            raise OriginalQueryUnknown('Terminal reader cannot start a host service')
        with (self.queue/'service.lock').open('r+b') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.clock()
            create_record(self.queue/'service-start.json', dict(identity=bind_original_process(os.getpid()),
                binding_sha256=digest(self.spec), started_unix=time.time(), no_replay=True))
            def interrupted(signum, frame):
                raise InterruptedError('Original FIT service interrupted by signal '+str(signum))
            previous = signal.signal(signal.SIGTERM, interrupted)
            error = None
            try:
                while not (self.queue/'stop-request.json').exists():
                    self.clock()
                    if time.monotonic() >= self.spec['work_stop_monotonic']:
                        raise TimeoutError('Original allocation work stop reached')
                    queries = sorted(self.queue.glob('score-*'))
                    if len(queries) > 42:
                        raise ValueError('Original complete FIT query denominator exceeded')
                    for query in queries:
                        if not (query/'request.json').exists():
                            raise OriginalQueryUnknown('Torn original query intent; no new scorer')
                        if (query/'response.json').exists():
                            continue
                        result = self.dispatch_query(query.name.removeprefix('score-'))
                        if result['status'] != 'ORIGINAL_COMPLETE_FIT_ACCEPTED':
                            status_file(self.spec, query.name.removeprefix('score-'), result['status'])
                            if result['status'] == 'ORIGINAL_FIT_FAILED':
                                payload = dict(reason='ORIGINAL_FIT_FAILED', complete_FIT_denominator=2)
                                config = read_record(query/'request.json')
                                create_record(query/'response.json', dict(status='FAILED_ORIGINAL',
                                    config_sha256=digest(config), payload=payload, payload_sha256=digest(payload)))
                            raise OriginalQueryUnknown('Original query is failed, live or unknown: '+result['status'])
                    time.sleep(1.)
                stop = read_record(self.queue/'stop-request.json')
                if stop['context_sha256'] != digest(self.spec['context']):
                    raise ValueError('Foreign service stop request')
            except BaseException as caught:
                error = dict(type=type(caught).__name__, message=str(caught))
                raise
            finally:
                signal.signal(signal.SIGTERM, previous)
                create_record(self.queue/'service-terminal.json', dict(binding_sha256=digest(self.spec),
                    ended_unix=time.time(), error=error, GPU_submissions=0, ledger_written=False))


def exec_cli(queue, candidate):
    spec = read_record(Path(queue)/'binding.json')
    query, output = paths(spec, candidate)
    config = read_record(query/'request.json')
    validate_query(spec, config)
    intent = read_record(query/'launch-intent.json')
    command = score_command(spec, config, output)
    if intent['binding_sha256'] != digest(spec) or intent['command'] != command or intent['command_sha256'] != digest(command):
        raise ValueError('Original scorer CLI command binding differs')
    create_record(query/'cli-start.json', dict(identity=bind_original_process(os.getpid()),
        launch_intent_sha256=file_sha(query/'launch-intent.json')))
    os.execvpe(command[0], command, dict(os.environ, CUDA_VISIBLE_DEVICES='', NVIDIA_VISIBLE_DEVICES='void'))


def operational_status(spec):
    queue, _ = paths(spec)
    rows = [read_record(p) for p in queue.glob('score-*/status.json')]
    # No request, worker scores, response payload or plan is opened here.
    return dict(status='ORIGINAL_INTERNAL_FIT_OPERATIONAL_COUNTS',
        requested_queries=len(list(queue.glob('score-*'))),
        statuses={state: sum(r['status'] == state for r in rows) for state in sorted({r['status'] for r in rows})},
        scientific_scores_exposed=False, GPU_submissions=0, ledger_written=False)
