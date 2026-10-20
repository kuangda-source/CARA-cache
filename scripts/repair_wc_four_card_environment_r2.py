#!/usr/bin/env python3
"""Repair a copied four-card CPU environment using verified official wheels."""
import argparse
import base64
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import time


VERSIONS = {'torch': '2.7.1+cu128', 'torchvision': '0.22.1+cu128',
            'flash-attn': '2.7.3+cu128.torch27', 'natten': '0.21.0+cu128.torch27',
            'transformer-engine': '2.2+cu128.torch27', 'triton': '3.3.1',
            'xformers': '0.0.31', 'decord': '0.6.0'}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4*1024**2), b''):
            h.update(block)
    return h.hexdigest()


def atomic(path, value):
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value, indent=2)+'\n')
    os.replace(temporary, path)


def metadata_fingerprint(environment):
    files = sorted((environment/'lib/python3.10/site-packages').glob('*.dist-info/METADATA'))
    assert files
    entries = {str(p.relative_to(environment)): sha(p) for p in files}
    return hashlib.sha256(json.dumps(entries, sort_keys=True).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', required=True, type=Path)
    args = parser.parse_args()
    m = json.loads(args.manifest.read_text())
    root = Path(m['workspace']).resolve()
    assert str(root) == '/data20t/gaokuangda/worldcache_workspace'
    job = root/'bootstrap'/m['run_id']
    assert args.manifest.resolve() == job/'manifest.json'
    assert not (job/'result.json').exists()
    original_job = Path(m['original_job'])
    assert original_job == root/'bootstrap/wc-fourcard-env-r1-20261020'
    assert sha(original_job/'environment-result.json') == m['original_result_sha256']
    original = json.loads((original_job/'environment-result.json').read_text())
    assert original['status'] == 'CPU_ENVIRONMENT_PARTIAL_FAILURES_RETAINED'
    original_proc = Path('/proc/'+str(m['original_PID'])+'/stat')
    if original_proc.exists():
        fields = original_proc.read_text().rsplit(') ',1)[1].split()
        assert int(fields[19]) != m['original_start_ticks'] or fields[0] in ('Z','X')
    source_env = root/'envs'/m['source_environment_name']
    environment = root/'envs'/m['environment_name']
    assert source_env != environment and source_env.is_dir() and not environment.exists()
    assert environment.name == 'wc-cosmos-py310-cu128-r3'
    assert sha(__file__) == m['worker_sha256']
    assert subprocess.check_output(['git','-C',str(root/'project'),'rev-parse','HEAD'],text=True).strip() == m['original_project_revision']
    assert all(sha(root/'runtime'/name) == expected for name, expected in m['runtime_source_sha256'].items())
    assert all(sha(root/'runtime/packages/cosmos-cuda'/name) == expected for name, expected in m['sentinel_source_sha256'].items())
    assert sha(root/'system-libs-r1/native-library-manifest.json') == m['native_library_manifest_sha256']
    for wheel in m['wheels']:
        p = root/'staging/official-cu128-torch27-wheels-r1'/wheel['filename']
        assert p.is_file() and p.stat().st_size == wheel['bytes'] and sha(p) == wheel['sha256']
    before = metadata_fingerprint(source_env)
    started = time.time()
    value = dict(status='ISOLATED_ENVIRONMENT_REPAIR_RUNNING', started_unix=started,
                 worker_sha256=sha(__file__), manifest_sha256=sha(args.manifest),
                 repair_source_revision=m['repair_source_revision'], original_project_revision=m['original_project_revision'],
                 commands=[], GPU_submissions=0, model_weights_loaded=0, ledger_written=False,
                 production_CPU_accepted=False, GPU_dispatch_ready=False,
                 driver_or_daemon_config_changed=False, source_environment_metadata_before=before,
                 environment_path=str(environment), original_environment_path=str(source_env))

    def save():
        atomic(job/'health.json', value)

    def command(label, argv, timeout=900):
        s = os.statvfs(root)
        assert s.f_bavail*s.f_frsize >= 128*1024**3
        value['phase'] = label
        save()
        began = time.time()
        with (job/(label+'.log')).open('xb') as output:
            try:
                p = subprocess.run(argv, stdout=output, stderr=subprocess.STDOUT, timeout=timeout,
                                   env=dict(os.environ, CUDA_VISIBLE_DEVICES=''))
            except subprocess.TimeoutExpired:
                if argv[:2] == ['docker','run']:
                    owned = subprocess.run(['docker','inspect',m['run_id'],'--format',
                                            '{{index .Config.Labels "wcomr.manifest"}}'],
                                           capture_output=True,text=True)
                    if owned.returncode == 0 and owned.stdout.strip() == value['manifest_sha256']:
                        subprocess.run(['docker','stop','--time','20',m['run_id']],
                                       stdout=output,stderr=subprocess.STDOUT,timeout=45)
                value['commands'].append(dict(phase=label,exit_code=124,wall_seconds=time.time()-began,timed_out=True))
                save()
                raise
        value['commands'].append(dict(phase=label, exit_code=p.returncode, wall_seconds=time.time()-began))
        save()
        if p.returncode:
            raise RuntimeError('Repair phase failed: '+label)

    native = root/'system-libs-r1'
    variables = dict(CUDA_VISIBLE_DEVICES='', NVIDIA_VISIBLE_DEVICES='void', PYTHONDONTWRITEBYTECODE='1',
                     HOME=str(root/'user-home'), TMPDIR=str(root/'tmp'),
                     UV_CACHE_DIR=str(root/'cache/uv-repair-r2'), PIP_CACHE_DIR=str(root/'cache/pip-repair-r2'),
                     HF_HOME=str(root/'cache/huggingface'), TORCH_HOME=str(root/'cache/torch'),
                     HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', UV_HTTP_TIMEOUT='60',
                     OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', UV_CONCURRENT_DOWNLOADS='2',
                     LD_LIBRARY_PATH=str(native/'usr/lib/x86_64-linux-gnu')+':'+str(native/'lib/x86_64-linux-gnu'),
                     PATH=str(native/'usr/bin')+':/usr/local/bin:/usr/bin:/bin')
    container = ['docker','run','--rm','--read-only','--name',m['run_id'],
                 '--label','wcomr.manifest='+value['manifest_sha256'],
                 '--user',str(os.getuid())+':'+str(os.getgid()),'--cpus','2','--memory','16g',
                 '--tmpfs','/tmp:rw,size=512m','-v',str(root)+':'+str(root),'-w',str(root)]
    for name, item in variables.items():
        container += ['-e',name+'='+item]
    container += ['--entrypoint','/usr/local/bin/python',m['container_image_id']]
    py = str(environment/'bin/python')
    uv = str(root/'tools/uv')

    def inside(label, argv, timeout=600):
        code = 'import subprocess; subprocess.run('+repr(argv)+',check=True)'
        command(label, container+['-c',code], timeout)

    try:
        command('copy-existing-base-to-independent-environment',
                ['cp','-a','--reflink=auto',str(source_env),str(environment)], 900)
        assert (source_env/'pyvenv.cfg').stat().st_ino != (environment/'pyvenv.cfg').stat().st_ino
        value['copied_environment_metadata_matches'] = metadata_fingerprint(environment) == before
        assert value['copied_environment_metadata_matches']
        # Correct packaging declarations only in the independent copy. Keep
        # every decoder payload byte and every registered runtime source intact.
        site = environment/'lib/python3.10/site-packages'
        decord = m['decord_metadata_repair']
        assert decord['target_tag'] == 'py3-none-manylinux2010_x86_64'
        assert all(sha(site/name)==expected for name,expected in decord['payload_sha256'].items())
        wheel = site/'decord-0.6.0.dist-info/WHEEL'
        assert sha(wheel)==decord['internal_WHEEL_sha256']
        original_text = wheel.read_text()
        assert original_text.count('Tag: cp36-cp36m-manylinux2010_x86_64') == 1
        wheel.write_text(original_text.replace('Tag: cp36-cp36m-manylinux2010_x86_64',
                                              'Tag: '+decord['target_tag']))
        record = wheel.parent/'RECORD'
        records = list(csv.reader(io.StringIO(record.read_text())))
        wheel_record = str(wheel.relative_to(site))
        matches = [row for row in records if row[0] == wheel_record]
        assert len(matches)==1
        matches[0][1:] = ['sha256='+base64.urlsafe_b64encode(hashlib.sha256(wheel.read_bytes()).digest()).decode().rstrip('='),
                          str(wheel.stat().st_size)]
        stream = io.StringIO();csv.writer(stream,lineterminator='\n').writerows(records)
        record.write_text(stream.getvalue())
        value['decord_retag_preserves_all_payload_SHA'] = all(sha(site/n)==h for n,h in decord['payload_sha256'].items())
        value['decord_WHEEL_before_SHA256'] = decord['internal_WHEEL_sha256']
        value['decord_WHEEL_after_SHA256'] = sha(wheel)
        overlay = job/'runtime-packaging-overlay'
        shutil.copytree(root/'runtime',overlay,symlinks=True,ignore=shutil.ignore_patterns('__pycache__','.git','.venv'))
        project_metadata = overlay/'pyproject.toml'
        text = project_metadata.read_text()
        assert text.count('"cosmos-oss==0.1.0"')==1
        value['original_runtime_pyproject_SHA256'] = sha(root/'runtime/pyproject.toml')
        project_metadata.write_text(text.replace('"cosmos-oss==0.1.0"','"cosmos-oss==1.4.0"'))
        value['runtime_packaging_overlay_pyproject_SHA256'] = sha(project_metadata)
        value['runtime_overlay_critical_sources_identical'] = all(sha(overlay/n)==h for n,h in m['runtime_source_sha256'].items())
        assert value['runtime_overlay_critical_sources_identical']
        paths = [str(root/'staging/official-cu128-torch27-wheels-r1'/x['filename']) for x in m['wheels']]
        inside('install-verified-local-cuda-wheels',
               [uv,'pip','install','--python',py,'--no-index','--no-build','--no-deps',*paths])
        inside('install-matching-official-cosmos-cuda-package',
               [uv,'pip','install','--python',py,'--no-deps','--index-url','https://pypi.org/simple',
                '-e',str(root/'runtime/packages/cosmos-cuda')])
        inside('install-runtime-packaging-dependency-alignment',
               [uv,'pip','install','--python',py,'--no-deps','--index-url','https://pypi.org/simple','-e',str(overlay)])
        inside('installed-dependency-check',[uv,'pip','check','--python',py])
        probe = '''import importlib.metadata as md,json,sys,torch
assert sys.version_info[:2]==(3,10)
def forbidden(*a,**k): raise RuntimeError('CPU environment repair prohibits CUDA, weights and downloads')
torch.cuda._lazy_init=forbidden;torch.load=forbidden;torch.hub.download_url_to_file=forbidden
expected=EXPECTED
versions={name:md.version(name) for name in expected}
assert versions==expected,(versions,expected)
import cosmos_predict2,cosmos_cuda
assert cosmos_predict2.__version__==cosmos_cuda.__version__
from cosmos_predict2.config import InferenceArguments,SetupArguments
assert not torch.cuda.is_initialized()
print(json.dumps(dict(versions=versions,Cosmos_version=cosmos_predict2.__version__,CUDA_initialized=False,model_weights_loaded=0)))
print('COSMOS_REQUEST_IMPORT_CPU_ONLY_OK')
'''.replace('EXPECTED',repr(VERSIONS))
        inside('actual-Cosmos-request-import-CPU-only',[py,'-c',probe],180)
        decoder_probe = '''import imageio.v2 as imageio,numpy as np,decord,json
frames=np.stack([np.full((64,64,3),[40+i*20,90,120],dtype=np.uint8) for i in range(4)])
path=VIDEO
imageio.mimwrite(path,frames,fps=4,codec='libx264')
reader=decord.VideoReader(path,ctx=decord.cpu(0),num_threads=2)
decoded=reader.get_batch(list(range(len(reader)))).asnumpy()
assert len(reader)==4 and decoded.shape==(4,64,64,3) and decoded.dtype==np.uint8
assert np.abs(decoded.astype(np.float32)-frames).mean()<16
print(json.dumps(dict(frames=4,HWC=[64,64,3],device='cpu',synthetic_not_research_result=True)))
print('DECORD_SYNTHETIC_CPU_VIDEO_DECODE_4FRAMES_OK')
'''.replace('VIDEO',repr(str(job/'synthetic-decode-smoke.mp4')))
        inside('decord-actual-synthetic-video-CPU-decode',[py,'-c',decoder_probe],120)
        # Use the same import-only CUDA/Triton boundary as the frozen production
        # CPU entry; it neither initializes a device nor replaces an operator.
        guarded = '''import torch
def forbidden(*a,**k): raise RuntimeError('CPU import only: no CUDA, weights or downloads')
torch.cuda._lazy_init=forbidden;torch.load=forbidden;torch.hub.download_url_to_file=forbidden
import triton
class ImportOnlyDriver:
 def get_benchmarker(self):return forbidden
 def __getattr__(self,n):raise RuntimeError('CPU import denies Triton execution: '+n)
triton.runtime.driver.active=ImportOnlyDriver()
import transformers.utils as hu
from transformers.utils import import_utils as iu
hu.is_flash_attn_2_available=iu.is_flash_attn_2_available=lambda:True
torch.cuda.current_device=lambda:0
import cosmos_predict2.inference
from cosmos_predict2._src.predict2.inference import worldcache_utils
from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow
assert not torch.cuda.is_initialized()
print('FROZEN_PRODUCTION_GUARDED_INFERENCE_IMPORT_CPU_ONLY_OK')
'''
        inside('guarded-production-inference-import-CPU-only',[py,'-c',guarded],180)
        inside('resolved-python-freeze',[uv,'pip','freeze','--python',py],90)
        value.update(status='ISOLATED_COSMOS_CPU_ENVIRONMENT_REPAIR_READY_NOT_PRODUCTION_OR_GPU',
                     exact_versions=VERSIONS, actual_CPU_request_import_passed=True,
                     guarded_production_import_passed=True, dependency_check_passed=True,
                     verified_wheels=m['wheels'], same_version_cosmos_cuda_installed=True)
    except BaseException as exc:
        value.update(status='ISOLATED_ENVIRONMENT_REPAIR_FAILED_RETAINED',error_type=type(exc).__name__,error=str(exc))
    finally:
        value['source_environment_metadata_after'] = metadata_fingerprint(source_env)
        value['source_environment_unchanged'] = value['source_environment_metadata_after'] == before
        value['runtime_critical_sources_unchanged'] = all(sha(root/'runtime'/n)==h for n,h in m['runtime_source_sha256'].items())
        value.update(ended_unix=time.time(),wall_seconds=time.time()-started)
        save()
        atomic(job/'result.json',value)
        print(json.dumps(value))


if __name__ == '__main__':
    main()
