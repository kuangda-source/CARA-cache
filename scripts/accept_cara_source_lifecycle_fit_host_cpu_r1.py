"""Accept the original ended synthetic host/broker probe; never run its readers."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'scripts')]

from cara_s_initialization_selector_cpu_r1 import BASE_CAPTURE, BASE_ACCEPTED
from cara_source_lifecycle_fit_host_cpu_r1 import STAGE, OVERLAY


def accept(launch_file, capture_file):
    read = lambda path: json.loads(Path(path).read_bytes())
    sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
    launch, capture = read(launch_file), read(capture_file)
    assert launch['exit_code'] == capture['exit_code'] == 0
    cap, launched = capture['result'], launch['result']
    assert launched == cap['launch'] and Path(launched['stage']).name == STAGE
    assert launched['status'] == 'ORIGINAL_HOST_FIT_CPU_PROBE_LAUNCHED_NOT_GPU'
    assert cap['status'] == 'ORIGINAL_HOST_FIT_CPU_CAPTURE_ONLY'
    assert cap['original_host_observation']['original_live'] is False
    assert cap['payload_intact'] and cap['runtime_intact']
    reg, terminal = cap['registration'], cap['host_terminal']
    revision = launch['source_revision']
    assert revision == capture['source_revision'] == reg['parent_git_revision'] == launched['source_revision']
    assert subprocess.check_output(['git', 'rev-parse', revision], cwd=ROOT, text=True).strip() == revision
    reg_sha = hashlib.sha256((json.dumps(reg, indent=2, allow_nan=False)+'\n').encode()).hexdigest()
    assert reg_sha == cap['registration_sha256'] == launched['registration_sha256']
    base, accepted_base = read(ROOT/BASE_CAPTURE)['result'], read(ROOT/BASE_ACCEPTED)
    assert accepted_base['capture_sha256'] == sha(ROOT/BASE_CAPTURE) and accepted_base['total_controls_passed'] == 113
    expected = {**base['registration']['payload_sha256'], **{
        n: hashlib.sha256(subprocess.check_output(['git', 'show', revision+':'+n], cwd=ROOT)).hexdigest() for n in OVERLAY}}
    assert reg['payload_sha256'] == expected
    assert reg['runtime_source_sha256'] == base['registration']['runtime_source_sha256']
    assert reg['source_identity'] == 'EXACT_PAYLOAD_HOST_FIT_CPU_ONLY' and reg['CPU_fixture_only'] is True
    assert launched['parent_Docker_container'] is False and launched['CPU_fixture_only'] is True
    assert launched['work_seconds'] == 1200 and launched['exit_seconds'] == 60
    bounds = launched['parent_bounds']
    assert bounds == dict(affinity=[26,27], RLIMIT_AS=[4*2**30]*2, RLIMIT_CPU=[1200]*2,
                         work_seconds=1200, Docker_container=False, GPU_visible=False)
    assert terminal['identity'] == launched['identity'] and terminal['error'] is None
    assert launched['started_unix'] < terminal['ended_unix'] <= launched['started_unix']+1200
    raw = base64.b64decode(cap['CPU_proof_base64'])
    assert hashlib.sha256(raw).hexdigest() == cap['CPU_proof_sha256']
    proof = json.loads(raw)
    assert proof == cap['CPU_proof']
    assert proof['status'] == 'ACTUAL_HOST_FIT_BROKER_CPU_TWO_COMPLETE_ONE_FAILED_COHORT_PASS'
    assert proof['source_revision'] == revision and proof['registration_sha256'] == reg_sha
    assert proof['payload_sha256'] == expected and proof['runtime_source_sha256'] == reg['runtime_source_sha256']
    assert proof['parent_bounds'] == bounds and proof['parent_identity'] == launched['identity']
    assert launched['started_unix'] <= proof['started_unix'] < proof['ended_unix'] <= terminal['ended_unix']
    assert proof['original_service_ended'] and proof['accepted_bytes_unchanged']
    assert proof['complete_accepted_metric_pairs'] == 4 and len(proof['accepted_successes']) == 2
    assert proof['failed_cohort_complete_pairs'] == 1 and proof['expected_failed_cohort_denominator'] == 2
    assert proof['duplicate_client_new_dispatches'] == proof['terminal_reader_new_dispatches'] == 0
    assert proof['operational']['requested_queries'] == 3
    assert proof['operational']['statuses'] == {'ACCEPTED_INTERNAL':2, 'ORIGINAL_FIT_FAILED':1}
    assert not proof['operational']['scientific_scores_exposed']
    containers = proof['actual_score_containers']
    assert len(containers) == 3 and len({r['container_id'] for r in containers}) == 3
    for row in containers:
        state = row['state']
        assert state['Status'] == 'exited' and state['Pid'] == 0 and not state['Running']
        assert not any(state[k] for k in ('Paused', 'Restarting', 'OOMKilled', 'Dead'))
    assert sorted(r['state']['ExitCode'] for r in containers) == [0,0,1]
    for success in proof['accepted_successes']:
        assert success['complete_pairs'] == 2
        assert next(r for r in containers if r['container_id'] == success['original_container_id'])['state']['ExitCode'] == 0
    media = proof['actual_media_container']
    assert media['cli_ended'] and media['state']['Pid'] == media['state']['ExitCode'] == 0
    host = media['host_config']
    assert host['NanoCpus'] == 2*10**9 and host['Memory'] == host['MemorySwap'] == 8*2**30
    assert host['CpusetCpus'] == '26,27' and host['NetworkMode'] == 'none' and host['ReadonlyRootfs']
    assert host['DeviceRequests'] in (None,[]) and host['Devices'] in (None,[]) and not host['Privileged']
    assert proof['CPU_fixture_only'] is True
    assert all(proof[k] is False for k in ('actual_Cosmos_weights', 'real_V1_video', 'whole_GPU_entry_accepted', 'P1_GPU_authorized', 'ledger_written'))
    assert proof['GPU_submissions'] == launched['GPU_submissions'] == cap['GPU_submissions'] == 0
    return dict(status='ORIGINAL_ACTUAL_HOST_FIT_BROKER_LINUX_CPU_ACCEPTED_SYNTHETIC_ONLY',
        source_revision=revision, CPU_stage=STAGE, launch_ref=str(launch_file), launch_sha256=sha(launch_file),
        capture_ref=str(capture_file), capture_sha256=sha(capture_file), original_proof_sha256=cap['CPU_proof_sha256'],
        registration_sha256=reg_sha, original_host_ended=True, original_service_ended=True,
        original_host_identity=launched['identity'], host_parent_limits=bounds, score_containers=containers,
        complete_accepted_metric_pairs=4, failed_cohort_complete_pairs=1, failed_cohort_denominator=2,
        original_duplicate_and_terminal_recovery_new_dispatches=0, original_accepted_bytes_unchanged=True,
        actual_Cosmos_weights=False, real_V1_video=False, whole_GPU_entry_accepted=False,
        P1_GPU_authorized=False, P1_central_ledger_authorized=False, GPU_submissions=0, ledger_written=False), raw


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for key in ('launch', 'capture', 'output', 'proof-output'):
        parser.add_argument('--'+key, type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists() and not args.proof_output.exists()
    accepted, raw = accept(args.launch, args.capture)
    with args.proof_output.open('xb') as stream: stream.write(raw)
    accepted['original_proof_ref'] = str(args.proof_output)
    with args.output.open('x') as stream:
        json.dump(accepted, stream, indent=2, allow_nan=False); stream.write('\n')
    print(json.dumps({k: accepted[k] for k in ('status', 'complete_accepted_metric_pairs', 'failed_cohort_denominator', 'P1_GPU_authorized')}))
