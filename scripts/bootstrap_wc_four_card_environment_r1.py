#!/usr/bin/env python3
"""Data-disk-only CPU environment preparation; never grants GPU admission."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024**2), b''):
            h.update(block)
    return h.hexdigest()


def atomic(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    os.replace(str(temporary), str(path))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    workspace = Path(manifest['workspace']).resolve()
    assert str(workspace).startswith('/data20t/gaokuangda/')
    job = workspace / 'bootstrap' / manifest['run_id']
    assert job.is_dir() and not (job / 'environment-result.json').exists()
    project = workspace / 'project'
    runtime = workspace / 'runtime'
    started = time.time()
    value = dict(status='CPU_ENVIRONMENT_PREPARATION_RUNNING', started_unix=started,
                 commands=[], GPU_submissions=0, model_weights_loaded=0,
                 ledger_written=False, production_CPU_accepted=False,
                 GPU_dispatch_ready=False, driver_or_daemon_config_changed=False,
                 manifest_sha256=sha(args.manifest), source_revision=manifest['source_revision'])

    def save():
        atomic(job / 'environment-health.json', value)

    def command(label, argv, timeout=1800, required=True):
        free = os.statvfs(str(workspace))
        assert free.f_bavail * free.f_frsize >= 128 * 1024**3
        value['phase'] = label
        save()
        began = time.time()
        with (job / (label + '.log')).open('xb') as output:
            try:
                call = subprocess.run(argv, stdout=output, stderr=subprocess.STDOUT,
                                      timeout=timeout, env=dict(os.environ, CUDA_VISIBLE_DEVICES=''))
            except subprocess.TimeoutExpired:
                if argv[:2] == ['docker', 'run']:
                    owned = subprocess.run(['docker', 'inspect', manifest['run_id'], '--format',
                                            '{{index .Config.Labels "wcomr.manifest"}}'],
                                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
                    if owned.returncode == 0 and owned.stdout.strip() == value['manifest_sha256']:
                        subprocess.run(['docker', 'stop', '--time', '20', manifest['run_id']],
                                       stdout=output, stderr=subprocess.STDOUT, timeout=45)
                raise
        value['commands'].append(dict(phase=label, exit_code=call.returncode,
                                      wall_seconds=time.time()-began))
        save()
        if call.returncode and required:
            raise RuntimeError('Preparation command failed: ' + label)
        return call.returncode == 0

    try:
        foundation = manifest['prerequisites']
        assert sha(foundation['result_path']) == foundation['result_sha256']
        prerequisite = json.loads(Path(foundation['result_path']).read_text())
        assert prerequisite['status'] == 'CONTAINER_AND_TORCH_CPU_PREREQUISITES_READY_NOT_PRODUCTION'
        assert prerequisite['worker_sha256'] == foundation['worker_sha256']
        assert prerequisite['base_environment_path'] == str(workspace/'envs'/manifest['environment_name'])
        assert prerequisite['GPU_submissions'] == 0 and prerequisite['ledger_written'] is False
        for name in ['source_bundle', 'runtime_archive']:
            assert sha(manifest[name]['path']) == manifest[name]['sha256']
        assert not project.exists() and not runtime.exists()
        command('git-clone-verified-bundle', ['git', 'clone', manifest['source_bundle']['path'], str(project)], 600)
        command('git-checkout-github-revision', ['git', '-C', str(project), 'checkout', manifest['source_revision']], 180)
        command('git-origin-github', ['git', '-C', str(project), 'remote', 'set-url', 'origin', manifest['github_origin']], 30)
        actual = subprocess.check_output(['git', '-C', str(project), 'rev-parse', 'HEAD'], text=True).strip()
        assert actual == manifest['source_revision']
        value['GitHub_revision_deployed'] = actual
        command('runtime-unpack', ['tar', '-xzf', manifest['runtime_archive']['path'], '-C', str(workspace)], 300)
        assert all(sha(runtime/name) == digest for name, digest in manifest['runtime_source_sha256'].items())
        (project / 'runtime').symlink_to(runtime)
        value['registered_runtime_execution_sources_match'] = True
        root_free = os.statvfs('/')
        assert root_free.f_bavail * root_free.f_frsize >= 4 * 1024**3
        command('small-cpu-base-pull', ['docker', 'pull', manifest['base_image_tag']], 900)
        image = subprocess.check_output(['docker', 'image', 'inspect', manifest['base_image_tag'],
                                         '--format', '{{.Id}}'], text=True).strip()
        value['container_image_id'] = image
        atomic(job / 'resolved-container-image.json', dict(requested=manifest['base_image_tag'], image_id=image))
        constraints = job / 'constraints.txt'
        constraints.write_text('torch==2.7.1\ntorchvision==0.22.1\ntriton==3.3.1\n'
                               'transformers==4.51.3\nhuggingface-hub==0.36.0\nnumpy==2.2.6\n'
                               'pydantic==2.11.7\nsafetensors==0.6.2\n')
        container = ['docker', 'run', '--rm', '--read-only', '--name', manifest['run_id'],
                     '--label', 'wcomr.manifest='+value['manifest_sha256'],
                     '--user', str(os.getuid()) + ':' + str(os.getgid()),
                     '--cpus', '2', '--memory', '16g', '--tmpfs', '/tmp:rw,size=512m',
                     '-v', str(workspace) + ':' + str(workspace), '-w', str(workspace)]
        variables = dict(NVIDIA_VISIBLE_DEVICES='void', CUDA_VISIBLE_DEVICES='',
                         HOME=str(workspace/'user-home'), TMPDIR=str(workspace/'tmp'),
                         UV_CACHE_DIR=str(workspace/'cache/uv'), PIP_CACHE_DIR=str(workspace/'cache/pip'),
                         HF_HOME=str(workspace/'cache/huggingface'), TORCH_HOME=str(workspace/'cache/torch'),
                         HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1',
                         OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', UV_HTTP_TIMEOUT='60',
                         UV_CONCURRENT_DOWNLOADS='3', UV_CONCURRENT_BUILDS='1')
        for key, item in variables.items():
            container += ['-e', key + '=' + item]
        container += ['--entrypoint', '/usr/local/bin/python', image]
        environment = workspace/'envs'/manifest['environment_name']
        uvtarget = workspace/'tools/uv-python'
        for path in [workspace/'user-home', workspace/'tools']:
            path.mkdir(exist_ok=True)

        def run_python(label, code, timeout=1800, required=True):
            return command(label, container+['-c', code], timeout, required)

        run_python('uv-and-python-environment',
                   'import subprocess; subprocess.run(["python","-m","pip","install","--disable-pip-version-check",'
                   '"--target",'+repr(str(uvtarget))+',"uv==0.9.5"],check=True); '
                   'subprocess.run(["python","-m","venv",'+repr(str(environment))+'],check=True); '
                   'import pathlib,os; root=pathlib.Path('+repr(str(uvtarget))+'); '
                   'bins=[p for p in root.rglob("uv") if p.is_file() and os.access(p,os.X_OK) '
                   'and p.open("rb").read(4)==b"\\x7fELF"]; assert len(bins)==1; '
                   'pathlib.Path('+repr(str(workspace/'tools/uv'))+').symlink_to(bins[0])', 600)
        uv = str(workspace/'tools/uv')
        py = str(environment/'bin/python')

        def pip(label, arguments, required=True):
            code = 'import subprocess; subprocess.run('+repr([uv,'pip','install','--python',py]+arguments)+',check=True)'
            return run_python(label, code, 2400, required)

        pip('torch-pinned-cu128', ['torch==2.7.1+cu128','torchvision==0.22.1+cu128','--no-build',
                                 '--index-url','https://download.pytorch.org/whl/cu128',
                                 '--extra-index-url','https://pypi.org/simple',
                                 '--index-strategy','unsafe-best-match'])
        pip('cosmos-and-project-base', ['--constraint',str(constraints),'-e',str(runtime/'packages/cosmos-oss'),
                                       '-e',str(runtime),'-e',str(project),'lpips==0.1.4'])
        extensions_ok = pip('registered-cuda-extension-wheels',
                            ['--constraint',str(constraints),'--no-build','flash-attn==2.7.3','natten==0.21.0',
                             'transformer-engine==2.2.0','triton==3.3.1',
                             '--extra-index-url','https://nvidia-cosmos.github.io/cosmos-dependencies/v1.2.0/cu128_torch27/simple',
                             '--index-strategy','unsafe-best-match'], False)
        check = ('import json,sys,torch; assert sys.version_info[:2]==(3,10); '
                 'assert torch.__version__.startswith("2.7.1"); assert not torch.cuda.is_initialized(); '
                 'print(json.dumps(dict(python=sys.version,torch=torch.__version__,cuda_build=torch.version.cuda,'
                 'CUDA_initialized=torch.cuda.is_initialized()))); '
                 'from cosmos_predict2.config import InferenceArguments,SetupArguments; '
                 'assert not torch.cuda.is_initialized(); print("COSMOS_REQUEST_IMPORT_CPU_ONLY_OK")')
        imports_ok = run_python('cpu-environment-import', 'import subprocess; subprocess.run('+repr([py,'-c',check])+',check=True)', 180, False)
        run_python('resolved-python-freeze', 'import subprocess; subprocess.run('+repr([uv,'pip','freeze','--python',py])+',check=True)', 90)
        value.update(status='CPU_ENVIRONMENT_BASE_READY_NOT_PRODUCTION_OR_GPU' if imports_ok and extensions_ok
                     else 'CPU_ENVIRONMENT_PARTIAL_FAILURES_RETAINED', base_environment_installed=True,
                     actual_CPU_import_passed=imports_ok, CUDA_extension_wheels_installed=extensions_ok,
                     HF_assets_ready=False, GPU_driver_compatibility_verified=False)
    except BaseException as exc:
        value.update(status='CPU_ENVIRONMENT_BOOTSTRAP_FAILED_RETAINED', error_type=type(exc).__name__, error=str(exc))
    finally:
        value.update(ended_unix=time.time(), wall_seconds=time.time()-started)
        save()
        atomic(job/'environment-result.json', value)
        print(json.dumps(value))


if __name__ == '__main__':
    main()
