#!/usr/bin/env python3
"""Finish CPU validation of the unchanged R2-installed four-card environment."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

from repair_wc_four_card_environment_r2 import VERSIONS, metadata_fingerprint, sha


DECODER_PROBE = '''import imageio.v2 as imageio,numpy as np,decord,json,sys
frames=np.stack([np.full((64,64,3),[40+i*20,90,120],dtype=np.uint8) for i in range(4)])
path=sys.argv[1]
imageio.mimwrite(path,frames,fps=4,codec='libx264')
reader=decord.VideoReader(path,ctx=decord.cpu(0),num_threads=2)
decoded=reader.get_batch(list(range(len(reader)))).asnumpy()
assert len(reader)==4 and decoded.shape==(4,64,64,3) and decoded.dtype==np.uint8
assert np.abs(decoded.astype(np.float32)-frames).mean()<16
print(json.dumps(dict(frames=4,HWC=[64,64,3],device='cpu',synthetic_not_research_result=True)))
print('DECORD_SYNTHETIC_CPU_VIDEO_DECODE_4FRAMES_OK')
'''


def guarded_probe(source):
    tree = ast.parse(source)
    matches = [n.value for n in ast.walk(tree) if isinstance(n, ast.Assign)
               and any(isinstance(t, ast.Name) and t.id == 'guarded' for t in n.targets)]
    assert len(matches) == 1
    code = ast.literal_eval(matches[0])
    compile(code, '<frozen-production-CPU-import>', 'exec')
    return code


def atomic(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    os.replace(temporary, path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', required=True, type=Path)
    args = parser.parse_args()
    m = json.loads(args.manifest.read_text())
    root = Path(m['workspace'])
    job = root / 'bootstrap' / m['run_id']
    old = Path(m['upstream_job'])
    env = root / 'envs' / 'wc-cosmos-py310-cu128-r3'
    assert str(root) == '/data20t/gaokuangda/worldcache_workspace'
    assert args.manifest.resolve() == job / 'manifest.json'
    assert not (job / 'result.json').exists()
    assert sha(__file__) == m['worker_sha256']
    assert sha(old / 'result.json') == m['upstream_result_sha256']
    assert sha(old / 'repair_worker.py') == m['upstream_worker_sha256']
    assert sha(old / 'decord-actual-synthetic-video-CPU-decode.log') == m['upstream_decode_failure_log_sha256']
    r2 = json.loads((old / 'result.json').read_text())
    old_m = json.loads((old / 'manifest.json').read_text())
    assert r2['status'] == 'ISOLATED_ENVIRONMENT_REPAIR_FAILED_RETAINED'
    assert r2['phase'] == 'decord-actual-synthetic-video-CPU-decode'
    assert len(r2['commands']) == 7 and all(x['exit_code'] == 0 for x in r2['commands'][:6])
    assert r2['commands'][-1]['exit_code'] == 1
    assert r2['source_environment_unchanged'] and r2['runtime_critical_sources_unchanged']
    assert 'SyntaxError: invalid syntax' in (old / 'decord-actual-synthetic-video-CPU-decode.log').read_text()
    assert all(sha(root / 'runtime' / n) == h for n, h in old_m['runtime_source_sha256'].items())
    before = metadata_fingerprint(env)
    before_payload = {n: sha(env / 'lib/python3.10/site-packages' / n)
                      for n in old_m['decord_metadata_repair']['payload_sha256']}
    assert before_payload == old_m['decord_metadata_repair']['payload_sha256']
    request_log = (old / 'actual-Cosmos-request-import-CPU-only.log').read_text()
    probe = [json.loads(x) for x in request_log.splitlines()
             if x.startswith('{') and '"versions"' in x]
    assert len(probe) == 1 and probe[0]['versions'] == VERSIONS
    assert probe[0]['CUDA_initialized'] is False
    assert 'COSMOS_REQUEST_IMPORT_CPU_ONLY_OK' in request_log
    compile(DECODER_PROBE, '<CPU-decoder-probe>', 'exec')
    guarded = guarded_probe((old / 'repair_worker.py').read_text())
    started = time.time()
    v = dict(status='CPU_VALIDATION_COMPLETION_RUNNING', started_unix=started,
             source_revision=m['source_revision'], worker_sha256=sha(__file__),
             manifest_sha256=sha(args.manifest), upstream_result_sha256=sha(old / 'result.json'),
             environment_path=str(env), environment_metadata_before=before,
             upstream_successful_commands=r2['commands'][:6], reused_request_probe=probe[0],
             commands=[], GPU_submissions=0, model_weights_loaded=0, ledger_written=False,
             CUDA_initialized=False, environment_modified=False,
             production_CPU_accepted=False, GPU_dispatch_ready=False,
             driver_or_daemon_config_changed=False)

    def save():
        atomic(job / 'health.json', v)

    variables = dict(CUDA_VISIBLE_DEVICES='', NVIDIA_VISIBLE_DEVICES='void',
                     PYTHONDONTWRITEBYTECODE='1', HOME='/tmp', TMPDIR='/tmp',
                     UV_CACHE_DIR='/tmp/uv', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                     OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2',
                     LD_LIBRARY_PATH=str(root / 'system-libs-r1/usr/lib/x86_64-linux-gnu') + ':' +
                     str(root / 'system-libs-r1/lib/x86_64-linux-gnu'),
                     PATH=str(root / 'system-libs-r1/usr/bin') + ':/usr/local/bin:/usr/bin:/bin')
    container = ['docker', 'run', '--rm', '--read-only', '--name', m['run_id'],
                 '--label', 'wcomr.manifest=' + v['manifest_sha256'],
                 '--user', str(os.getuid()) + ':' + str(os.getgid()), '--cpus', '2', '--memory', '16g',
                 '--tmpfs', '/tmp:rw,size=512m', '-v', str(root) + ':' + str(root) + ':ro',
                 '-v', str(job) + ':' + str(job) + ':rw', '-w', str(job)]
    for key, value in variables.items():
        container += ['-e', key + '=' + value]
    container += ['--entrypoint', '/usr/local/bin/python', old_m['container_image_id']]
    py = str(env / 'bin/python')

    def inside(label, argv, timeout):
        v['phase'] = label
        save()
        began = time.time()
        with (job / (label + '.log')).open('xb') as output:
            code = 'import subprocess;subprocess.run(' + repr(argv) + ',check=True)'
            try:
                result = subprocess.run(container + ['-c', code], stdout=output,
                                        stderr=subprocess.STDOUT, timeout=timeout)
            except subprocess.TimeoutExpired:
                owned = subprocess.run(['docker', 'inspect', m['run_id'], '--format',
                                        '{{index .Config.Labels "wcomr.manifest"}}'],
                                       capture_output=True, text=True)
                if owned.returncode == 0 and owned.stdout.strip() == v['manifest_sha256']:
                    subprocess.run(['docker', 'stop', '--time', '20', m['run_id']],
                                   stdout=output, stderr=subprocess.STDOUT, timeout=45)
                v['commands'].append(dict(phase=label, exit_code=124, wall_seconds=time.time() - began))
                save()
                raise
        v['commands'].append(dict(phase=label, exit_code=result.returncode, wall_seconds=time.time() - began))
        save()
        assert result.returncode == 0, label

    try:
        inside('corrected-synthetic-CPU-video-decode',
               [py, '-c', DECODER_PROBE, str(job / 'synthetic-decode-smoke.mp4')], 120)
        inside('frozen-production-guarded-inference-import', [py, '-c', guarded], 240)
        inside('resolved-python-freeze', [str(root / 'tools/uv'), 'pip', 'freeze', '--python', py], 90)
        v['status'] = 'COSMOS_CPU_ENVIRONMENT_COMPLETION_READY_NOT_PRODUCTION_OR_GPU'
    except BaseException as exc:
        v.update(status='CPU_VALIDATION_COMPLETION_FAILED_RETAINED', error_type=type(exc).__name__, error=str(exc))
    finally:
        v['environment_metadata_after'] = metadata_fingerprint(env)
        v['environment_metadata_unchanged'] = before == v['environment_metadata_after']
        v['decord_payload_unchanged'] = all(sha(env / 'lib/python3.10/site-packages' / n) == h
                                           for n, h in before_payload.items())
        v['runtime_critical_sources_unchanged'] = all(sha(root / 'runtime' / n) == h
                                                    for n, h in old_m['runtime_source_sha256'].items())
        v.update(ended_unix=time.time(), wall_seconds=time.time() - started)
        save()
        atomic(job / 'result.json', v)
        print(json.dumps(v))


if __name__ == '__main__':
    main()
