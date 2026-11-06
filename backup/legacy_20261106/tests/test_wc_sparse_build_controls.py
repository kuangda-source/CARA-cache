"""CPU safety controls for compilation; these tests never import Torch or compile."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def test_source_drift_stops_before_child(tmp_path):
    project = tmp_path / 'project'
    (project / '.sync').mkdir(parents=True)
    source = tmp_path / 'source'
    source.mkdir()
    (source / 'setup.py').write_text('changed')
    lock = tmp_path / 'lock.json'
    lock.write_text(json.dumps({
        'status': 'COMPLETE_GIT_BLOB_AND_SHA_SOURCE_PASS_NOT_BUILD_OR_INSTALL',
        'commit': 'ae5b629ebb41e41f86b3ea2ab5a3283f13ac151a',
        'files': {'setup.py': {'bytes': 7, 'sha256': '0' * 64}},
    }))
    output = tmp_path / 'output'
    subprocess.run([sys.executable, str(ROOT / 'scripts/build_wc_sparge.py'),
        '--source', str(source), '--source-lock', str(lock), '--project-root', str(project),
        '--output', str(output), '--entry', str(ROOT / 'scripts/wc_sparge_build_entry.py')],
        check=True, capture_output=True, timeout=10)
    receipt = json.loads((output / 'receipt.json').read_text())
    assert receipt['status'] == 'TECH_BLOCKED'
    assert receipt['child_pid'] is None
    assert 'source drift' in receipt['error']


def test_over_cap_rejected_before_output(tmp_path):
    output = tmp_path / 'output'
    proc = subprocess.run([sys.executable, str(ROOT / 'scripts/build_wc_sparge.py'),
        '--source', str(tmp_path), '--source-lock', str(tmp_path / 'missing.json'),
        '--project-root', str(tmp_path), '--output', str(output),
        '--entry', str(ROOT / 'scripts/wc_sparge_build_entry.py'), '--max-wall-seconds', '901'],
        capture_output=True, text=True, timeout=10)
    assert proc.returncode != 0
    assert 'bounded CPU build cap' in proc.stderr
    assert not output.exists()


def test_visible_gpu_rejected_before_torch_import(tmp_path):
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='0', TORCH_CUDA_ARCH_LIST='8.6',
               CUDA_HOME='/usr/local/cuda-12.2')
    output = tmp_path / 'output'
    proc = subprocess.run([sys.executable, str(ROOT / 'scripts/wc_sparge_build_entry.py'),
        str(tmp_path), str(output)], env=env, capture_output=True, text=True, timeout=10)
    assert proc.returncode != 0
    assert 'CPU-only explicit architecture' in proc.stderr
    assert not output.exists()
