"""Actual host queue and isolated CPU containers on explicit synthetic media.

The host parent/service have their own RLIMIT/affinity witnesses. They are not
described as containers. Only the media generator and three original scorers
use Docker; none can see a GPU, use networking or read experiment videos.
"""
import argparse
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'scripts'), str(ROOT/'tests')]

from wcomr.cara_budget_original_handles_r1 import bind_original_process, observe_original_process
from wcomr.cara_budget_search_journal_r1 import create_record, read_record
from wcomr.cara_budget_supervisor_r1 import stop_original
from wcomr.cara_fast_fidelity_r1 import file_sha
from wcomr.cara_fast_spec_r1 import digest, profile_from, uniform_mask, policy_from_mask
from wcomr.cara_source_lifecycle_fit_broker_r1 import (
    Client, Host, prepare, paths, operational_status, inspect_original,
)
from wcomr.cara_source_lifecycle_search_r1 import legal_swaps
from wcomr.cara_read_write_score_capture_r1 import IMAGE

SOURCE = 'scripts/check_cara_source_lifecycle_fit_host_cpu_r1.py'


def host_limits():
    assert os.environ['CUDA_VISIBLE_DEVICES'] == '' and os.environ['NVIDIA_VISIBLE_DEVICES'] == 'void'
    assert {26, 27} <= os.sched_getaffinity(0)
    os.sched_setaffinity(0, {26, 27})
    resource.setrlimit(resource.RLIMIT_AS, (4*2**30, 4*2**30))
    resource.setrlimit(resource.RLIMIT_CPU, (1200, 1200))
    def interrupted(signum, frame):
        raise TimeoutError('Original CPU host probe interrupted by '+str(signum))
    signal.signal(signal.SIGALRM, interrupted)
    signal.signal(signal.SIGTERM, interrupted)
    signal.alarm(1200)
    return dict(affinity=sorted(os.sched_getaffinity(0)),
                RLIMIT_AS=list(resource.getrlimit(resource.RLIMIT_AS)),
                RLIMIT_CPU=list(resource.getrlimit(resource.RLIMIT_CPU)), work_seconds=1200,
                Docker_container=False, GPU_visible=False)


def media_command(project, stage, artifacts, control, environment, label):
    from four_card_policy_assets_port_r1 import container_command
    from four_card_bank24_execution_tools_r1 import process_environment
    env = process_environment(project, artifacts/'caches')
    env.update(TORCH_HOME=environment['torch_home'])
    command = container_command(project, stage, 'cpu-worker', label, env, os.getuid(), os.getgid())
    command[command.index('--name')+1] = stage.name+'-synthetic-media-cpu'
    command[command.index('--memory')+1] = '8g'
    command[command.index(str(stage)+':'+str(stage)+':rw')] = str(stage)+':'+str(stage)+':ro'
    index = command.index('--entrypoint')
    command[index:index] = ['--memory-swap', '8g', '--cpuset-cpus', '26,27',
        '--cidfile', str(control/'media.cid'), '-v', str(artifacts)+':'+str(artifacts)+':rw']
    end = command.index('--entrypoint')+3
    return command[:end]+[str(stage/SOURCE), 'media', '--stage', str(stage), '--output', str(artifacts)]


def media(output):
    assert os.environ['CUDA_VISIBLE_DEVICES'] == '' and os.environ['NVIDIA_VISIBLE_DEVICES'] == 'void'
    assert os.sched_getaffinity(0) == {26, 27}
    signal.alarm(600)
    from check_cara_s_endpoint_real_video_r1 import write_video
    files = {}
    for i in range(2):
        for kind in ('reference', 'K19', 'K22', 'SWAP19'):
            path = output/(kind+'-'+str(i)+'.mp4')
            assert not path.exists()
            if kind == 'SWAP19' and i == 1:
                path.write_bytes(b'INTENTIONALLY_INVALID_CPU_FIXTURE_CODEC_NOT_A_MODEL_VIDEO')
            else:
                tag = 'SAME_REFERENCE' if i == 1 else kind
                write_video(path, 'P1_HOST_CPU_SYNTHETIC_'+str(i)+'_'+tag, height=64, width=64)
            files[path.name] = dict(path=str(path), sha256=file_sha(path))
    create_record(output/'media-complete.json', dict(status='SYNTHETIC93X64_CPU_MEDIA_COMPLETE',
        shape=[93, 64, 64, 3], fps=16, files=files, generative_weights=False,
        intentional_bad_video='SWAP19-1.mp4', GPU_submissions=0))


def validate_media_container(container, command, project, stage, artifacts, label, cid):
    host, config, state = container['HostConfig'], container['Config'], container['State']
    assert container['Id'] == cid and container['Name'] == '/'+command[command.index('--name')+1]
    assert container['Image'] == IMAGE and config['Labels']['wcomr.manifest'] == label
    assert host['NanoCpus'] == 2*10**9 and host['Memory'] == host['MemorySwap'] == 8*2**30
    assert host['CpusetCpus'] == '26,27' and host['DeviceRequests'] in (None, []) and host['Devices'] in (None, [])
    assert not host['Privileged'] and host['CapAdd'] in (None, []) and host['NetworkMode'] == 'none'
    assert host['ReadonlyRootfs'] and host['PidMode'] == 'host' and not host['AutoRemove']
    assert host['RestartPolicy']['Name'] == 'no'
    mounts = [(m['Source'], m['Destination'], m['RW']) for m in container['Mounts'] if m['Type'] == 'bind']
    assert sorted(mounts) == sorted((str(p), str(p), rw) for p, rw in ((project, False), (stage, False), (artifacts, True)))
    env = dict(x.split('=', 1) for x in config['Env'])
    assert env['CUDA_VISIBLE_DEVICES'] == '' and env['NVIDIA_VISIBLE_DEVICES'] == 'void'
    index = command.index('--entrypoint')
    assert config['Entrypoint'] == [command[index+1]] and config['Cmd'] == command[index+3:]
    assert config['User'] == str(os.getuid())+':'+str(os.getgid()) and config['WorkingDir'] == str(project/'runtime')
    return state, host


def execute_media(command, project, stage, artifacts, control, label):
    name = command[command.index('--name')+1]
    absent = subprocess.run(['docker', 'inspect', name], capture_output=True, text=True, timeout=20)
    assert absent.returncode == 1 and absent.stderr.strip() in ('Error: No such object: '+name, 'Error: No such container: '+name)
    create_record(control/'media-intent.json', dict(command=command, command_sha256=digest(command), no_replay=True))
    child = None
    identity = None
    started = time.monotonic()
    try:
        with (control/'media.log').open('x') as log:
            child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                     start_new_session=True)
            identity = bind_original_process(child.pid)
            create_record(control/'media-cli.json', dict(identity=identity, command_sha256=digest(command)))
            code = child.wait(timeout=600)
        assert code == 0, (control/'media.log').read_text()[-2000:]
    finally:
        if child is not None:
            if child.poll() is None and (control/'media.cid').exists():
                cid = (control/'media.cid').read_text().strip()
                inspected = inspect_original(cid)
                assert inspected['status'] == 'OBSERVED'
                state, _ = validate_media_container(inspected['container'], command, project, stage, artifacts, label, cid)
                if state['Running']:
                    subprocess.run(['docker', 'stop', '--time', '10', cid], capture_output=True, timeout=20, check=True)
            stop_original(child, identity)
    assert observe_original_process(identity)['original_live'] is False
    cid = (control/'media.cid').read_text().strip()
    inspected = inspect_original(cid)
    assert inspected['status'] == 'OBSERVED'
    state, host = validate_media_container(inspected['container'], command, project, stage, artifacts, label, cid)
    assert state['Status'] == 'exited' and state['Pid'] == state['ExitCode'] == 0 and not state['Running'] and not state['OOMKilled']
    result = dict(container_id=cid, state=state, host_config=host, cli_identity=identity,
                  cli_ended=True, wall_seconds=time.monotonic()-started, command_sha256=digest(command))
    create_record(control/'media-terminal.json', result)
    return result


def cohort(spec, policy, kind):
    from wcomr.cara_budget_search_r1 import FIT_MEMBERS, SCHEDULE_SHA256
    root = Path(spec['artifact_root'])
    candidate = policy['fingerprint']
    pairs = []
    for i, member in enumerate(FIT_MEMBERS):
        pair = dict(member=member)
        for side, tag in (('candidate', kind), ('reference', 'reference')):
            path = root/(tag+'-'+str(i)+'.mp4')
            proof_file = root/(tag+'-'+str(i)+'-proof.json')
            proof = dict(status='COMPLETE', CPU_fixture_only=True, synthetic_generation_witness=True,
                context_sha256=digest(spec['context']), source_revision=spec['context']['source_revision'],
                launch_id=spec['context']['launch_id'], member=member, seed=0,
                candidate_id=candidate if side == 'candidate' else 'NATIVE35',
                actual_updates=36, solver_steps=36, guided_pairs=36, fallback_count=0, timing='CLEAN',
                semantic_history=[dict(actual=a, fallback_reason=None)
                                  for a in (policy['actions'] if side == 'candidate' else ['D']*36)],
                video=dict(path=str(path), sha256=file_sha(path)))
            if proof_file.exists():
                original = read_record(proof_file)
                # References are shared by all queries. Their D/C history is a
                # CPU generation witness, not an observed model trajectory.
                if side == 'reference':
                    proof = original
                else:
                    assert original == proof
            else:
                create_record(proof_file, proof)
            pair[side] = dict(member=member, seed=0, candidate_id=proof['candidate_id'],
                proof_path=str(proof_file), proof_sha256=file_sha(proof_file), **proof['video'])
        pairs.append(pair)
    return dict(schema='CARA_V1_INTERNAL_COMPLETE_FIT_ARTIFACTS_R1', purpose='P1_INTERNAL_FIT_CALIBRATION',
        CPU_fixture_only=True, FIT_members=list(FIT_MEMBERS), schedule_sha256=SCHEDULE_SHA256,
        source_revision=spec['context']['source_revision'], launch_id=spec['context']['launch_id'],
        context_sha256=digest(spec['context']), candidate_id=candidate, query_id='score-'+candidate,
        score_shape=[93, 64, 64, 3], pairs=pairs)


def probe(stage, output, bounds):
    project = stage.parents[1]
    reg = read_record(stage/'registration.json')
    assert reg['host'] == 'two_card'
    assert all(file_sha(stage/n) == h for n, h in reg['payload_sha256'].items())
    assert all(file_sha(project/'runtime'/n) == h for n, h in reg['runtime_source_sha256'].items())
    assert not output.exists()
    parent = read_record(stage/'plans/cara_next_stage_20261101/e1/ENDPOINT7_46_MANIFEST_R1.json')
    profile = profile_from(parent['profile'])
    dense19, _ = uniform_mask(parent['schedule'], profile, 19)
    p19 = policy_from_mask(profile, dense19)
    p22 = policy_from_mask(profile, uniform_mask(parent['schedule'], profile, 22)[0])
    swap = policy_from_mask(profile, legal_swaps(profile, dense19, 19)[0][2])
    run_id = stage.name+'-cpu'
    root = project/'outputs'/run_id
    root.mkdir(mode=0o700)
    artifacts, control = root/'algorithm', root/'CPU-control'
    artifacts.mkdir(); control.mkdir()
    started = time.time()
    context = dict(run_id=run_id, host='two_card', CPU_fixture_only=True,
        source_revision=reg['parent_git_revision'], scope_sha256=digest(dict(kind='HOST_FIT_CPU_PROBE', policies=[p19,p22,swap])),
        launch_id=digest(dict(stage=str(stage), registration=file_sha(stage/'registration.json')))[:32])
    environment = dict(torch_home=str(stage.parent/'wc-time-score-CPU-two_card-r1-20261027/torch'),
        piq_site=str(stage.parent/'wc-time-score-CPU-two_card-r1-20261027/site'), weights_sha256={})
    spec = dict(schema='CARA_V1_INTERNAL_FIT_BROKER_BINDING_R1', project=str(project), stage=str(stage),
        context=context, profile=parent['profile'], artifact_root=str(artifacts), queue=str(root/'internal-FIT-queue'),
        environment=environment, CPU_fixture_only=True, registration_sha256=file_sha(stage/'registration.json'),
        uid=os.getuid(), gid=os.getgid(), work_stop_monotonic=time.monotonic()+1100)
    media_result = execute_media(media_command(project, stage, artifacts, control, environment, digest(spec)),
                                 project, stage, artifacts, control, digest(spec))
    prepare(spec)
    queue, _ = paths(spec)
    spec_file = queue/'binding.json'
    service = None
    service_identity = None
    success = []
    error = None
    try:
        with (control/'service.log').open('x') as log:
            service = subprocess.Popen([sys.executable, str(stage/SOURCE), 'service', '--stage', str(stage),
                '--output', str(spec_file)], stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                start_new_session=True, env=dict(os.environ, CUDA_VISIBLE_DEVICES='', NVIDIA_VISIBLE_DEVICES='void'))
            service_identity = bind_original_process(service.pid)
            create_record(control/'service-cli.json', dict(identity=service_identity))
            deadline = time.monotonic()+30
            while not (queue/'service-start.json').exists() and service.poll() is None and time.monotonic() < deadline:
                time.sleep(.1)
            assert (queue/'service-start.json').exists(), (control/'service.log').read_text()[-2000:]
            service_start = read_record(queue/'service-start.json')
            assert all(service_start['identity'][k] == service_identity[k]
                       for k in ('pid', 'start_ticks', 'host_view'))
            service_identity = service_start['identity']
            client = Client(spec)
            packets = [cohort(spec, p, kind) for p, kind in ((p19,'K19'),(p22,'K22'),(swap,'SWAP19'))]
            for packet in packets[:2]:
                accepted = client(packet, None)
                assert accepted['status'] == 'ACCEPTED_INTERNAL_CALIBRATION_ONLY' and len(accepted['rows']) == 2
                query, directory = paths(spec, packet['candidate_id'])
                before = (query/'response.json').read_bytes()
                original_cid = (directory/'container.cid').read_bytes()
                original_intent = (query/'launch-intent.json').read_bytes()
                assert client(packet, None) == accepted and (query/'response.json').read_bytes() == before
                assert (directory/'container.cid').read_bytes() == original_cid
                assert (query/'launch-intent.json').read_bytes() == original_intent
                success.append(dict(candidate=packet['candidate_id'], response_sha256=file_sha(query/'response.json'),
                    accepted_sha256=digest(accepted), complete_pairs=2,
                    original_container_id=original_cid.decode().strip(),
                    launch_intent_sha256=file_sha(query/'launch-intent.json')))
            try:
                client(packets[2], None)
            except RuntimeError as failed:
                assert 'Original full FIT query failed' in str(failed)
            else:
                raise AssertionError('Partial failed cohort entered the algorithm')
            assert service.wait(timeout=30) != 0
        assert observe_original_process(service_identity)['original_live'] is False
        raw_service = read_record(queue/'service-terminal.json')
        assert raw_service['error'] is not None
        for row in success:
            query, _ = paths(spec, row['candidate'])
            assert Host.reader(spec).recover_query(row['candidate'])['status'] == 'ORIGINAL_COMPLETE_FIT_ACCEPTED'
            assert file_sha(query/'response.json') == row['response_sha256']
        failed_query, failed_output = paths(spec, swap['fingerprint'])
        failed = read_record(failed_output/'scores.json')
        assert failed['status'] == 'FAILED_INTERNAL_FIT_DENOMINATOR_RETAINED'
        assert len(failed['registered_FIT_members']) == 2 and len(failed['rows']) == 1
        assert failed['CUDA_initialized'] is False
        operational = operational_status(spec)
        assert operational['requested_queries'] == 3 and operational['statuses'] == {'ACCEPTED_INTERNAL':2, 'ORIGINAL_FIT_FAILED':1}
        containers = []
        for packet in packets:
            query, directory = paths(spec, packet['candidate_id'])
            cid = (directory/'container.cid').read_text().strip()
            observed = inspect_original(cid)
            assert observed['status'] == 'OBSERVED'
            state = observed['container']['State']
            assert state['Status'] == 'exited' and state['Pid'] == 0 and not state['Running']
            containers.append(dict(container_id=cid, state=state, command_sha256=read_record(query/'launch-intent.json')['command_sha256']))
        proof = dict(status='ACTUAL_HOST_FIT_BROKER_CPU_TWO_COMPLETE_ONE_FAILED_COHORT_PASS',
            source_revision=reg['parent_git_revision'], registration_sha256=file_sha(stage/'registration.json'),
            payload_sha256=reg['payload_sha256'], runtime_source_sha256=reg['runtime_source_sha256'],
            host='two_card', CPU_fixture_only=True, started_unix=started, ended_unix=time.time(),
            parent_bounds=bounds, parent_identity=bind_original_process(os.getpid()), service_identity=service_identity,
            original_service_ended=True, actual_media_container=media_result, actual_score_containers=containers,
            accepted_successes=success, complete_accepted_metric_pairs=4,
            expected_failed_cohort_denominator=2, failed_cohort_complete_pairs=1,
            duplicate_client_new_dispatches=0, terminal_reader_new_dispatches=0, accepted_bytes_unchanged=True,
            operational=operational, actual_Cosmos_weights=False, real_V1_video=False,
            whole_GPU_entry_accepted=False, P1_GPU_authorized=False, GPU_submissions=0, ledger_written=False)
        create_record(output, proof)
    except BaseException as caught:
        error = dict(type=type(caught).__name__, message=str(caught))
        raise
    finally:
        if service is not None:
            if service.poll() is None:
                request = queue/'stop-request.json'
                if not request.exists(): create_record(request, dict(context_sha256=digest(context)))
                try: service.wait(timeout=25)
                except subprocess.TimeoutExpired: stop_original(service, service_identity)
            create_record(control/'probe-terminal.json', dict(error=error, service_exit_code=service.returncode,
                service_identity=service_identity, service_ended=observe_original_process(service_identity)['original_live'] is False))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('role', choices=('probe', 'service', 'media'))
    parser.add_argument('--stage', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.role == 'media':
        media(args.output)
    elif args.role == 'service':
        host_limits()
        spec = read_record(args.output)
        assert spec['CPU_fixture_only'] is True
        started = time.monotonic()
        Host(spec, lambda: time.monotonic()-started).serve()
    else:
        bounds = host_limits()
        identity = bind_original_process(os.getpid())
        create_record(args.stage/'host-start.json', dict(identity=identity, parent_bounds=bounds,
            started_unix=time.time(), CPU_fixture_only=True, GPU_submissions=0))
        error = None
        try:
            deadline = time.monotonic()+30
            grant = args.stage/'host-dispatch-grant.json'
            while not grant.exists() and time.monotonic() < deadline:
                time.sleep(.05)
            assert grant.exists(), 'Original host launch grant absent; never start another probe'
            assert read_record(grant)['identity'] == identity
            probe(args.stage, args.output, bounds)
        except BaseException as caught:
            error = dict(type=type(caught).__name__, message=str(caught))
            raise
        finally:
            create_record(args.stage/'host-terminal.json', dict(identity=identity,
                ended_unix=time.time(), error=error, CPU_fixture_only=True,
                GPU_submissions=0, ledger_written=False))


if __name__ == '__main__':
    main()
