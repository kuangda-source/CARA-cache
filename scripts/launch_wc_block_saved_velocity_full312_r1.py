"""Dispatch the accepted immutable B stage once, after full60 GPU/post acceptance.

Without --launch this prints a local plan and does not contact the server.
The numerical source and existing CPU proofs are never changed by this helper.
"""
import argparse
import hashlib
import inspect
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
SERVER = '/home/gaokuangda/data/gkd/worldcache_omr'
STAGE = SERVER + '/.sync/wc-block-velocity-production-r1-20261013'
PYTHON = '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
CONFIG = 'configs/wc_block_velocity_suffix3_full312_production_r1_20261013.json'
SOURCE = '988ace1834af14c4ed535ed7b025c9619fec948e'
CURVE_SOURCE = '361ea5c9372332299f7ca29dbffe0ab942274d0f'
HOST = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
        '-o', 'ClearAllForwardings=yes', 'gkd_minchen']


def accepted_packet():
    acceptance_path = ROOT/'reports/wc_block_velocity_production_r1_CPU_independent_acceptance_20261013.json'
    accepted = json.loads(acceptance_path.read_text())
    capture_path = ROOT/accepted['source_capture_ref']
    assert hashlib.sha256(capture_path.read_bytes()).hexdigest() == accepted['source_capture_sha256']
    capture = json.loads(capture_path.read_text())
    proof = capture['result']
    assert accepted['CPU_ended'] and accepted['payload_files'] == 730
    assert accepted['source_revision'] == capture['source_revision'] == SOURCE
    assert accepted['GPU_submissions'] == 0 and not accepted['ledger_written']
    assert accepted['scope_counts']['pairs'] == 312 and accepted['scope_counts']['videos'] == 16
    assert proof['source_revision'] == SOURCE and proof['exit_code'] == 0
    assert not proof['CUDA_initialized'] and proof['watcher_proof']['actual_config_derived_paths_verified']
    return dict(source_revision=SOURCE, curve_source_revision=CURVE_SOURCE,
                CPU_result_sha256=capture['result_sha256'],
                registration_sha256=proof['registration_sha256'],
                config_sha256=proof['config_sha256'], payload_files=730,
                config_ref=CONFIG, python=PYTHON,
                local_acceptance_sha256=hashlib.sha256(acceptance_path.read_bytes()).hexdigest())


def dispatch(root, stage, packet):
    """This exact function is sent to SSH; fixture tests exercise its dispatch path."""
    root, stage = Path(root), Path(stage)
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    read = lambda p: json.loads(p.read_text())
    def store(p, value):
        temporary = p.with_name(p.name + '.tmp')
        temporary.write_text(json.dumps(value, indent=2) + '\n')
        temporary.replace(p)
    reg = read(stage/'registration.json')
    proof = read(stage/'production-CPU-result.json')
    assert reg['source_revision'] == packet['source_revision']
    assert sha(stage/'registration.json') == packet['registration_sha256']
    assert sha(stage/'production-CPU-result.json') == packet['CPU_result_sha256']
    assert sha(stage/packet['config_ref']) == packet['config_sha256']
    assert proof['status'] == 'BLOCK_SAVED_VELOCITY_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU'
    assert proof['exit_code'] == 0 and not proof['CUDA_initialized'] and proof['GPU_submissions'] == 0
    assert proof['registration_sha256'] == packet['registration_sha256']
    assert len(reg['payload_sha256']) == packet['payload_files']
    for name, digest in reg['payload_sha256'].items():
        path = (stage/name).resolve()
        assert path.is_relative_to(stage.resolve()) and sha(path) == digest
    cfg = read(stage/packet['config_ref'])
    assert cfg['scope_counts']['pairs'] == 312 and cfg['scope_counts']['videos'] == 16
    assert cfg['scope_counts']['teacher_pairs'] == cfg['scope_counts']['B_executor_pairs'] == 0
    assert cfg['automatic_single_job_GPUh'] == 8 and 0 < cfg['forecast_complete_GPUh'] <= 8
    receipt_path = stage/'GPU-launch.json'
    if receipt_path.exists():
        receipt = read(receipt_path)
        assert receipt['source_revision'] == reg['source_revision']
        assert receipt['accepted_CPU_sha256'] == packet['CPU_result_sha256']
        return receipt  # Never re-dispatch a possibly live or terminal original handle.
    claim = stage/'GPU-dispatch-claim'
    assert not claim.exists(), 'Unknown original dispatch: inspect claim, never resubmit'
    assert not (stage/'GPU-supervisor.log').exists() and not (stage/'post-watcher.log').exists()
    assert not (root/'outputs'/cfg['run_id']).exists()
    curve = root/'.sync/wc-h1-cost-curve-production-r2-20261013'
    previous = read(curve/'CPU-final-results.json')
    post = read(curve/'post-CPU-exit.json')
    assert post['exit_code'] == 0
    assert previous['status'] in ('H1_COST_CURVE_FULL40_SCIENCE_ALL60_AUDITED_93FRAME_SCORED',
                                  'H1_COST_CURVE_FULL_SCOPE_REJECTIONS_OR_MISSING_REFERENCE_RETAINED')
    assert previous['source_revision'] == packet['curve_source_revision']
    assert len(previous['rows']) == 60
    assert previous['GPU_supervisor']['status'] == 'H1_COST_CURVE_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT'
    assert previous['GPU_supervisor']['child_exit_code'] == 0
    command = [packet['python'], '-u', str(stage/'scripts/supervise_wc_block_velocity_r1.py'),
               '--project', str(root), '--stage', str(stage), '--source-revision', reg['source_revision']]
    claim.mkdir()  # Atomic exclusion of simultaneous launchers; retained on every failure.
    store(claim/'request.json', dict(packet=packet, command=command, requested_unix=time.time()))
    with (stage/'GPU-supervisor.log').open('x') as log:
        child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                                 start_new_session=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
    receipt = dict(status='B_FULL312_SUPERVISOR_DISPATCHED_POST_PENDING',
                   supervisor_pid=child.pid, source_revision=reg['source_revision'], stage=str(stage),
                   run_id=cfg['run_id'], command=command, started_unix=time.time(),
                   accepted_CPU_sha256=packet['CPU_result_sha256'],
                   predecessor_full60_sha256=sha(curve/'CPU-final-results.json'),
                   predecessor_post_exit_sha256=sha(curve/'post-CPU-exit.json'))
    store(receipt_path, receipt)  # Preserve the original supervisor before starting the watcher.
    post_command = [packet['python'], '-u', str(stage/'scripts/watch_wc_block_velocity_cpu_r1.py'),
                    '--project', str(root), '--stage', str(stage), '--supervisor-pid', str(child.pid)]
    try:
        with (stage/'post-watcher.log').open('x') as log:
            watcher = subprocess.Popen(post_command, stdout=log, stderr=subprocess.STDOUT,
                                       start_new_session=True, env=dict(os.environ, CUDA_VISIBLE_DEVICES=''))
        receipt.update(status='B_FULL312_DISPATCHED_ADMISSION_PENDING', post_watcher_pid=watcher.pid,
                       post_command=post_command)
    except BaseException as error:
        receipt.update(status='B_FULL312_ORIGINAL_SUPERVISOR_DISPATCHED_POST_WATCHER_FAILED',
                       post_error_type=type(error).__name__, post_error=str(error))
        store(receipt_path, receipt)
        raise
    store(receipt_path, receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--launch', action='store_true')
    args = parser.parse_args()
    packet = accepted_packet()
    if not args.launch:
        print(json.dumps(dict(status='B_FULL312_LOCAL_PLAN_NO_SERVER_CONTACT', stage=STAGE,
                              packet=packet, forecast_GPUh=2.236752758178627)))
        return
    code = ('import hashlib,json,os,subprocess,time\nfrom pathlib import Path\n'
            + inspect.getsource(dispatch) + '\nprint(json.dumps(dispatch('
            + repr(SERVER) + ',' + repr(STAGE) + ',' + repr(packet) + ')))\n')
    compile(code, 'B-full312-single-dispatch', 'exec')
    # A timeout means unknown observation, never a reason to start another supervisor.
    receipt = json.loads(subprocess.check_output(HOST+['python3 -'], input=code, text=True, timeout=120))
    target = ROOT/'reports/wc_block_saved_velocity_full312_r1_GPU_launch_20261013.json'
    if target.exists():
        assert json.loads(target.read_text()) == receipt
    else:
        target.write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
