"""Test actual launch helper without SSH, CUDA, ledger edits, or subprocesses."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('B_dispatch', ROOT/'scripts/launch_wc_block_saved_velocity_full312_r1.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def fixture(root):
    stage = root/'.sync/B'
    stage.mkdir(parents=True)
    def write(path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2)+'\n')
    cfg = dict(scope_counts=dict(pairs=312, videos=16, teacher_pairs=0, B_executor_pairs=0),
               run_id='B-full312', automatic_single_job_GPUh=8, forecast_complete_GPUh=2.236752758178627)
    write(stage/m.CONFIG, cfg)
    reg = dict(source_revision=m.SOURCE, payload_sha256={m.CONFIG:sha(stage/m.CONFIG)})
    write(stage/'registration.json', reg)
    proof = dict(status='BLOCK_SAVED_VELOCITY_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU', exit_code=0,
                 CUDA_initialized=False, GPU_submissions=0, registration_sha256=sha(stage/'registration.json'))
    write(stage/'production-CPU-result.json', proof)
    packet = dict(source_revision=m.SOURCE, curve_source_revision=m.CURVE_SOURCE,
                  registration_sha256=sha(stage/'registration.json'), config_sha256=sha(stage/m.CONFIG),
                  CPU_result_sha256=sha(stage/'production-CPU-result.json'), payload_files=1,
                  config_ref=m.CONFIG, python=m.PYTHON)
    curve = root/'.sync/wc-h1-cost-curve-production-r2-20261013'
    write(curve/'post-CPU-exit.json', dict(exit_code=0))
    final = dict(status='H1_COST_CURVE_FULL40_SCIENCE_ALL60_AUDITED_93FRAME_SCORED',
                 source_revision=m.CURVE_SOURCE, rows=[dict(id=i) for i in range(60)],
                 GPU_supervisor=dict(status='H1_COST_CURVE_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT', child_exit_code=0))
    write(curve/'CPU-final-results.json', final)
    return stage, packet, curve, write


def main():
    cases = []
    for kind in ('success_and_retry', 'incomplete_predecessor', 'failed_predecessor',
                 'changed_CPU_bytes', 'changed_payload', 'unknown_claim', 'existing_output', 'post_failure'):
        with TemporaryDirectory() as name:
            root = Path(name)
            stage, packet, curve, write = fixture(root)
            if kind == 'incomplete_predecessor':
                f=json.loads((curve/'CPU-final-results.json').read_text());f['rows'].pop();write(curve/'CPU-final-results.json',f)
            elif kind == 'failed_predecessor':
                write(curve/'post-CPU-exit.json', dict(exit_code=1))
            elif kind == 'changed_CPU_bytes':
                (stage/'production-CPU-result.json').write_text('{}')
            elif kind == 'changed_payload':
                (stage/m.CONFIG).write_text('{}')
            elif kind == 'unknown_claim':
                (stage/'GPU-dispatch-claim').mkdir()
            elif kind == 'existing_output':
                (root/'outputs/B-full312').mkdir(parents=True)
            calls=[]
            def fake_popen(command, **kwargs):
                calls.append((command,kwargs))
                if kind == 'post_failure' and len(calls)==2:
                    raise OSError('fixture watcher unavailable')
                return SimpleNamespace(pid=9000+len(calls))
            with patch.object(m.subprocess, 'Popen', side_effect=fake_popen):
                if kind == 'success_and_retry':
                    first=m.dispatch(root,stage,packet)
                    assert first['supervisor_pid']==9001 and first['post_watcher_pid']==9002
                    assert m.dispatch(root,stage,packet)==first and len(calls)==2
                    assert calls[0][0][2]==str(stage/'scripts/supervise_wc_block_velocity_r1.py')
                    assert calls[1][0][-2:]==['--supervisor-pid','9001']
                    assert calls[1][1]['env']['CUDA_VISIBLE_DEVICES']==''
                elif kind == 'post_failure':
                    try:m.dispatch(root,stage,packet)
                    except OSError:pass
                    else:raise AssertionError('Watcher failure discarded')
                    r=m.dispatch(root,stage,packet)
                    assert r['supervisor_pid']==9001 and r['status'].endswith('POST_WATCHER_FAILED')
                    assert len(calls)==2 and (stage/'GPU-dispatch-claim/request.json').exists()
                else:
                    try:m.dispatch(root,stage,packet)
                    except (AssertionError,FileNotFoundError):pass
                    else:raise AssertionError('Unsafe dispatch accepted: '+kind)
                    assert not calls and not (stage/'GPU-launch.json').exists()
            assert not (root/'reports/budget.json').exists()
            cases.append(kind)
    actual=m.accepted_packet()
    assert actual['payload_files']==730 and actual['source_revision']==m.SOURCE
    print(json.dumps(dict(status='B_FULL312_ACTUAL_DISPATCH_HELPER_CPU_EIGHT_CASES_PASS_NOT_GPU',
                          cases=cases, accepted_actual_CPU_source_bound=True,
                          GPU_submissions=0, server_contacts=0, ledger_written=False)))


if __name__ == '__main__':main()
