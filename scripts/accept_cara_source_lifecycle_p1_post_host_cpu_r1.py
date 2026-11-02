"""Accept saved original post-score/serve CPU evidence without invoking readers."""
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
from cara_source_lifecycle_p1_post_host_cpu_r1 import STAGE, OVERLAY


def accept(launch_file, capture_file):
    read = lambda path: json.loads(Path(path).read_bytes())
    sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
    launch, capture = read(launch_file), read(capture_file)
    assert launch['exit_code'] == capture['exit_code'] == 0
    cap, launched = capture['result'], launch['result']
    assert launched == cap['launch'] and Path(launched['stage']).name == STAGE
    assert launched['status'] == 'ORIGINAL_P1_POST_SCORE_CPU_PROBE_LAUNCHED_NOT_GPU'
    assert cap['status'] == 'ORIGINAL_P1_POST_SCORE_CPU_CAPTURE_ONLY'
    assert cap['original_host_observation']['original_live'] is False
    assert cap['payload_intact'] and cap['runtime_intact']
    reg, terminal = cap['registration'], cap['host_terminal']
    revision = launch['source_revision']
    assert revision == capture['source_revision'] == reg['parent_git_revision'] == launched['source_revision']
    reg_sha = hashlib.sha256((json.dumps(reg, indent=2, allow_nan=False)+'\n').encode()).hexdigest()
    assert reg_sha == cap['registration_sha256'] == launched['registration_sha256']
    base, accepted_base = read(ROOT/BASE_CAPTURE)['result'], read(ROOT/BASE_ACCEPTED)
    assert accepted_base['capture_sha256'] == sha(ROOT/BASE_CAPTURE) and accepted_base['total_controls_passed'] == 113
    expected = {**base['registration']['payload_sha256'], **{
        n: hashlib.sha256(subprocess.check_output(['git', 'show', revision+':'+n], cwd=ROOT)).hexdigest() for n in OVERLAY}}
    assert reg['payload_sha256'] == expected
    assert reg['runtime_source_sha256'] == base['registration']['runtime_source_sha256']
    assert reg['source_identity'] == 'EXACT_PAYLOAD_P1_POST_SCORE_CPU_ONLY' and reg['CPU_fixture_only'] is True
    assert launched['parent_Docker_container'] is False and launched['CPU_fixture_only'] is True
    assert launched['work_seconds'] == 1200 and launched['exit_seconds'] == 60
    bounds = dict(affinity=[26,27], RLIMIT_AS=[4*2**30]*2, RLIMIT_CPU=[1200]*2,
                  work_seconds=1200, Docker_container=False, GPU_visible=False)
    assert launched['parent_bounds'] == bounds
    assert terminal['identity'] == launched['identity'] and terminal['error'] is None
    assert launched['started_unix'] < terminal['ended_unix'] <= launched['started_unix']+1200
    raw = base64.b64decode(cap['CPU_proof_base64'], validate=True)
    assert hashlib.sha256(raw).hexdigest() == cap['CPU_proof_sha256']
    proof = json.loads(raw)
    assert proof == cap['CPU_proof'] and proof['status'] == 'ACTUAL_P1_POST_DOCKER_ONCE_RECOVERY_CPU_PASS'
    assert proof['source_revision'] == revision and proof['registration_sha256'] == reg_sha
    assert proof['payload_sha256'] == expected and proof['runtime_source_sha256'] == reg['runtime_source_sha256']
    assert proof['parent_bounds'] == bounds and proof['parent_identity'] == launched['identity']
    assert launched['started_unix'] <= proof['started_unix'] < proof['ended_unix'] <= terminal['ended_unix']
    assert proof['tests_run'] == 31 and proof['logical_quality_positions'] == 52
    assert proof['real_new_metric_pairs'] == 2 and proof['simulated_internal_rows'] == 50
    assert proof['expected_failed_denominator'] == 2 and proof['expected_failed_completed_pairs'] == 1
    assert proof['original32_pair_worker_experiment_replayed'] is False
    scores = proof['actual_post_score_containers']
    assert len(scores) == 2 and {r['status'] for r in scores} == {
        'ORIGINAL_COMPLETE52_P1_SCORE_ACCEPTED', 'ORIGINAL_SCORE_FAILED'}
    media = proof['actual_media_container']
    assert len({media['container_id'], *(r['container_id'] for r in scores)}) == 3
    for row in scores+[media]:
        state = row['container_state'] if 'container_state' in row else row['state']
        host = row['host_config']
        assert state['Status'] == 'exited' and state['Pid'] == 0 and not state['Running']
        assert not any(state[k] for k in ('Paused', 'Restarting', 'OOMKilled', 'Dead'))
        assert host['NanoCpus'] == 2*10**9 and host['Memory'] == host['MemorySwap'] == 8*2**30
        assert host['CpusetCpus'] == '26,27' and host['NetworkMode'] == 'none' and host['ReadonlyRootfs']
        assert host['DeviceRequests'] in (None,[]) and host['Devices'] in (None,[]) and not host['Privileged']
    assert media['cli_ended'] and media['state']['ExitCode'] == 0
    for row in scores:
        success = row['status'] == 'ORIGINAL_COMPLETE52_P1_SCORE_ACCEPTED'
        assert row['container_state']['ExitCode'] == (0 if success else 1)
        assert row['original_supervisor_ended'] and row['supervisor_terminal']['cleanup_error'] is None
        assert row['success_new_pairs'] == (2 if success else 0)
        assert row['expected_failed_denominator'] == (0 if success else 2)
        assert row['expected_failed_completed_pairs'] == (0 if success else 1)
        assert row['new_dispatches_on_duplicate'] == row['new_dispatches_on_terminal_recovery'] == 0
    service = proof['production_serve_branch']
    assert service['actual_production_serve_branch'] and service['CPU_only_allocation_metadata_simulation']
    assert service['actual_affinity'] == [26,27] and service['actual_RLIMIT_AS_bytes'] == 4*2**30
    assert service['original_process_ended'] and service['internal_queries_dispatched'] == 0
    assert service['GPU_allocation_created'] is False and service['GPU_submissions'] == 0 and not service['ledger_written']
    assert service['start']['identity'] == service['terminal']['identity']
    assert service['terminal']['complete'] and service['terminal']['exit_code'] == 0
    assert service['terminal']['terminal_error'] is None and not service['terminal']['new_GPU_bill']
    assert service['terminal']['counts']['requested_queries'] == 0
    assert proof['CPU_fixture_only'] is True
    assert all(proof[k] is False for k in ('actual_Cosmos_weights', 'real_V1_video',
        'whole_GPU_entry_accepted', 'P1_GPU_authorized', 'ledger_written'))
    assert proof['GPU_submissions'] == launched['GPU_submissions'] == cap['GPU_submissions'] == 0
    return dict(status='ORIGINAL_P1_POST_DOCKER_AND_PRODUCTION_SERVE_LINUX_CPU_ACCEPTED_SYNTHETIC_ONLY',
        source_revision=revision, CPU_stage=STAGE, launch_ref=str(launch_file), launch_sha256=sha(launch_file),
        capture_ref=str(capture_file), capture_sha256=sha(capture_file), original_proof_sha256=cap['CPU_proof_sha256'],
        registration_sha256=reg_sha, original_host_ended=True, original_host_identity=launched['identity'],
        host_parent_limits=bounds, started_unix=launched['started_unix'], ended_unix=terminal['ended_unix'],
        tests_run=31, actual_score_containers=scores, actual_media_container_id=media['container_id'],
        production_serve_branch=service, logical_quality_positions=52, real_new_metric_pairs=2,
        simulated_internal_rows=50, failed_denominator=2, failed_completed_pairs=1,
        original32_pair_worker_experiment_replayed=False, actual_Cosmos_weights=False, real_V1_video=False,
        whole_GPU_entry_accepted=False, P1_GPU_authorized=False, P1_central_ledger_authorized=False,
        GPU_submissions=0, ledger_written=False), raw


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
    print(json.dumps({k: accepted[k] for k in ('status', 'real_new_metric_pairs', 'failed_denominator', 'P1_GPU_authorized')}))
