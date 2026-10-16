#!/usr/bin/env python3
"""One Git-bound N09 CPU-only stage after original N07/N08 acceptance."""
import argparse
import gzip
import json
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PYTHON = '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
ENTRIES = ['scripts/' + n for n in (
    'run_wc_paper_N09_runtime_profile40_r1.py', 'supervise_wc_paper_N09_runtime_profile40_r1.py',
    'watch_wc_paper_N09_post_cpu_r1.py', 'postprocess_wc_paper_N09_runtime_profile40_r1.py',
    'run_wc_paper_N09_production_cpu_bundle_r1.py', 'deploy_wc_paper_N09_production_cpu_r1.py',
    'capture_wc_paper_N09_production_cpu_r1.py', 'accept_wc_paper_N09_production_cpu_r1.py',
    'estimate_wc_paper_N09_runtime40_complete_cost_r1.py')]
TESTS = ['tests/' + n for n in (
    'test_runtime_profile40_execution_r1.py', 'test_runtime_profile40_production_r1.py',
    'test_runtime_profile40_post_r1.py', 'test_runtime_profile40_cost_r1.py',
    'test_runtime_profile40_supervision_r1.py', 'test_runtime_profile40_post_watcher_r1.py',
    'test_runtime_profile40_cpu_acceptance_r1.py', 'test_balanced_repeat_execution_r1.py',
    'test_frozen_shared_batch_r1.py', 'test_frozen_shared_production_r1.py',
    'test_frozen_shared_inputs_r1.py', 'test_frozen_card_cost_r1.py')]
TEST_DATA = (
    'manifests/wc_paper_N09_runtime_profile40_scope_r1_20261016.json',
    'manifests/wc_paper_N08_balanced_repeat40_protocol_r1_20261016.json',
    'manifests/wc_paper_N07_N08_method_freeze_r1_20261016.json',
    'reports/wc_simple26d_memory_full36_collection_20261016_0455.json.gz',
    'reports/wc_simple26d_memory_full36_independent_acceptance_20261016.json')


def accepted_base_identity(base, data):
    from wcomr.balanced_repeat_cpu_acceptance_r1 import accept
    accepted = accept(base)
    if (accepted.get('CPU_accepted') is not True
            or base['files']['config']['sha256'] != data['N08_capture']['config_sha256']
            or base['files']['proof']['sha256'] != data['N08_capture']['production_CPU_sha256']):
        raise ValueError('The accepted N08 CPU base must belong to the exact completed N08 GPU card')
    return accepted


BOOTSTRAP = r'''
import hashlib,io,json,os,pathlib,subprocess,sys,tarfile,time
meta=json.loads(sys.stdin.buffer.readline());archive=sys.stdin.buffer.read()
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr').resolve()
for name in ('base','stage'):
 relative=pathlib.PurePosixPath(meta[name]);assert not relative.is_absolute() and '..' not in relative.parts
 assert len(relative.parts)==2 and relative.parts[0]=='.sync'
module='src/wcomr/immutable_stage_payload_r1.py'
with tarfile.open(fileobj=io.BytesIO(archive),mode='r:gz') as stream:
 found=[m for m in stream if m.name==module];assert len(found)==1 and found[0].isfile()
 source=stream.extractfile(found[0]).read()
assert hashlib.sha256(source).hexdigest()==meta['plan']['overlay_sha256'][module]
namespace={'__name__':'git_bound_n09_CPU_installer'};exec(compile(source,'GIT_BOUND_N09_CPU_INSTALLER','exec'),namespace)
base=root/meta['base'];stage=root/meta['stage'];assert base.resolve()==pathlib.Path(meta['base_original_absolute']).resolve()
registration=namespace['install'](base,stage,archive,meta['plan'],source_revision=meta['source_revision'],
 cpu_scope='FROZEN_N09_PRODUCTION_CPU_PREPARATION_NO_GPU')
sys.path.insert(0,str(stage/'src'))
from wcomr.gpu_budget_pool_v2 import process_identity
assert meta['expected_CPU_commands']==8
with (stage/'N09-production-CPU-launch-request.json').open('x') as h:
 json.dump(dict(source_revision=meta['source_revision'],requested_unix=time.time()),h);h.flush();os.fsync(h.fileno())
command=[sys.executable,str(stage/'scripts/run_wc_paper_N09_production_cpu_bundle_r1.py'),
 '--project',str(root),'--stage',str(stage)]
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
 PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
with (stage/'N09-CPU-bundle.log').open('xb') as log:
 child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
identity=process_identity(child.pid)
assert identity['state'] not in (None,'Z','X') and 'run_wc_paper_N09_production_cpu_bundle_r1.py' in identity['command']
now=time.time()
receipt=dict(status='N09_FULL40_ACTUAL_PRODUCTION_CPU_SINGLE_DISPATCH',pid=child.pid,identity=identity,
 project=str(root),stage=str(stage),source_revision=meta['source_revision'],command=command,launched_unix=now,
 registration_sha256=hashlib.sha256((stage/'registration.json').read_bytes()).hexdigest(),
 payload_files=len(registration['payload_sha256']),overlay_files=len(meta['plan']['overlay_sha256']),
 expected_CPU_commands=8,first_collection_not_before_unix=now+300,
 shared_runtime_written=False,original_base_stage_written=False,GPU_submissions=0,ledger_written=False)
with (stage/'N09-production-CPU-launch.json').open('x') as h:
 json.dump(receipt,h,indent=2);h.flush();os.fsync(h.fileno())
print(json.dumps(receipt,allow_nan=False))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-CPU-capture', type=Path, required=True)
    parser.add_argument('--stage', required=True); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():raise FileExistsError('Preserve the original N09 CPU dispatch receipt')
    sys.path.insert(0, str(ROOT / 'src'))
    from wcomr.runtime_profile40_production_r1 import CONFIG, referenced_contract, read_reference
    from wcomr.frozen_shared_production_r1 import verify_sampling_sources
    from wcomr.immutable_stage_payload_r1 import configuration_closure, git_archive, plan, relative, registered_base_reference
    relative(args.stage)
    if not args.stage.startswith('.sync/wc-paper-n09-') or len(Path(args.stage).parts) != 2:
        raise ValueError('One fresh N09 CPU stage must be a .sync child')
    config, data, bound, _ = referenced_contract(ROOT)  # Real config absent until completed N07/N08.
    configuration_closure(ROOT, [CONFIG])
    shared_refs = {n:read_reference(ROOT, ref) for n, ref in data['shared_config']['references'].items()}
    numeric = verify_sampling_sources(ROOT, shared_refs['shared_CPU_raw'], shared_refs['shared_CPU_acceptance'])
    base = json.loads(gzip.decompress(args.base_CPU_capture.read_bytes()))
    accepted_base_identity(base, data)
    value = plan(ROOT, config_roots=[CONFIG], python_entrypoints=ENTRIES, extra_files=TESTS + list(TEST_DATA),
        base_registration_sha256=base['registration_sha256'], base_source_revision=base['registration']['source_revision'],
        numeric_sources=numeric['source_sha256'])
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    archive = git_archive(ROOT, value, revision)
    base_ref = registered_base_reference(base['registration']['stage'], base['launch']['stage'])
    metadata = dict(base=base_ref['project_relative'], base_original_absolute=base_ref['original_absolute'],
        stage=args.stage, source_revision=revision, plan=value, expected_CPU_commands=8)
    envelope = json.dumps(metadata, ensure_ascii=False, allow_nan=False).encode() + b'\n' + archive
    try:
        call = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', '-o', 'ClearAllForwardings=yes',
            'gkd_minchen', PYTHON + ' -c ' + shlex.quote(BOOTSTRAP)], input=envelope, capture_output=True, timeout=180)
    except (subprocess.TimeoutExpired, OSError) as error:
        result = dict(status='N09_CPU_DISPATCH_TRANSPORT_UNKNOWN_NO_RETRY', stage=args.stage, source_revision=revision,
            error_type=type(error).__name__, error=str(error), task_terminal=False, retry_authorized=False,
            original_recovery_refs=[args.stage + '/' + n for n in (
                'N09-production-CPU-launch-request.json', 'N09-production-CPU-launch.json', 'N09-CPU-bundle.log')],
            GPU_submissions=0, ledger_written=False)
        with args.output.open('x') as h:json.dump(result,h,indent=2,allow_nan=False);h.write('\n')
        raise
    result = dict(transport_exit_code=call.returncode, source_revision=revision, overlay_plan=value,
        stderr=call.stderr.decode(errors='replace'), retry_authorized=False, GPU_submissions=0, ledger_written=False)
    try:result['launch'] = json.loads(call.stdout)
    except (ValueError, UnicodeDecodeError):
        result.update(status='N09_CPU_DISPATCH_RESPONSE_UNKNOWN_NO_RETRY', task_terminal=False,
            stdout=call.stdout.decode(errors='replace'), original_recovery_ref=args.stage + '/N09-production-CPU-launch.json')
    with args.output.open('x') as h:json.dump(result,h,indent=2,allow_nan=False);h.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'overlay_plan'}))
    raise SystemExit(call.returncode if 'launch' in result else (call.returncode or 1))


if __name__ == '__main__':main()
