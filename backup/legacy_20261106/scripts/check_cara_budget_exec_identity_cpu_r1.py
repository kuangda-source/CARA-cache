"""Reproduce the original bootstrap-to-runner identity boundary without GPU."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--original-stage', type=Path, required=True)
    args = parser.parse_args()
    stage = args.original_stage
    sys.path.insert(0, str(stage / 'src'))
    from wcomr.cara_budget_original_handles_r1 import bind_original_process
    from wcomr.gpu_budget_pool_v2 import sha
    bootstrap = stage / 'scripts/cara_budget_process_bootstrap_r1.py'
    original = json.loads((stage / 'registration.json').read_text())
    assert original['payload_sha256']['scripts/cara_budget_process_bootstrap_r1.py'] == sha(bootstrap)
    with tempfile.TemporaryDirectory(prefix='single14-exec-CPU-') as temporary:
        fixture = Path(temporary)
        registration = {'payload_sha256': {'scripts/cara_budget_process_bootstrap_r1.py': sha(bootstrap)}}
        (fixture / 'registration.json').write_text(json.dumps(registration))
        probe = """import json,os,pathlib,sys
from wcomr.cara_budget_original_handles_r1 import bind_original_process
fixture=pathlib.Path(sys.argv[1])
before=json.loads((fixture/'runner-start.json').read_text())['identity']
after=bind_original_process(os.getpid())
print(json.dumps(dict(before=before,after=after,stable_identity_equal=all(before[k]==after[k] for k in ('pid','start_ticks','host_view')),full_dictionary_equal=before==after,original_command_changed=before['original_command_sha256']!=after['original_command_sha256'],CUDA_VISIBLE_DEVICES=os.environ.get('CUDA_VISIBLE_DEVICES'),NVIDIA_VISIBLE_DEVICES=os.environ.get('NVIDIA_VISIBLE_DEVICES'))))
"""
        launch = dict(stage=str(fixture), registration_sha256=sha(fixture/'registration.json'),
                      launch_id='CPU_EXEC_IDENTITY_DIAGNOSTIC_NO_GPU', source_revision=original['source_revision'],
                      CPU_fixture_only=True, commands={'runner': [sys.executable, '-c', probe, str(fixture)]})
        (fixture / 'GPU-launch.json').write_text(json.dumps(launch))
        environment = dict(os.environ, PYTHONPATH=str(stage/'src'), CUDA_VISIBLE_DEVICES='', NVIDIA_VISIBLE_DEVICES='void', PYTHONDONTWRITEBYTECODE='1')
        child = subprocess.Popen([sys.executable, str(bootstrap), '--stage', str(fixture), '--role', 'runner'], env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        deadline = time.monotonic()+10
        while not (fixture/'runner-start.json').exists():
            assert child.poll() is None and time.monotonic()<deadline
            time.sleep(.02)
        bound=json.loads((fixture/'runner-start.json').read_text())['identity']
        assert bound==bind_original_process(child.pid)
        (fixture/'runner-dispatch-grant.json').write_text(json.dumps(dict(identity=bound,launch_sha256=sha(fixture/'GPU-launch.json'))))
        stdout,stderr=child.communicate(timeout=10)
        assert child.returncode==0,stderr
        result=json.loads(stdout)
        assert result['stable_identity_equal'] and not result['full_dictionary_equal'] and result['original_command_changed']
        assert result['CUDA_VISIBLE_DEVICES']=='' and result['NVIDIA_VISIBLE_DEVICES']=='void'
        print(json.dumps(dict(status='ORIGINAL_BOOTSTRAP_EXEC_IDENTITY_MISMATCH_REPRODUCED_CPU_ONLY',result=result,bootstrap_sha256=sha(bootstrap),GPU_submissions=0,ledger_written=False,original_run_untouched=True)))


if __name__=='__main__':
    main()
