#!/usr/bin/env python3
"""Git-bound fresh CPU stage after final freeze; never start a GPU task."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PYTHON = '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
PROJECT = '/home/gaokuangda/data/gkd/worldcache_omr'
ENTRIES = ['scripts/' + n for n in (
    'run_wc_paper_N07_frozen_shared180_r1.py', 'supervise_wc_paper_N07_frozen_shared180_r1.py',
    'watch_wc_paper_N07_post_cpu_r1.py', 'postprocess_wc_paper_N07_frozen_shared180_r1.py',
    'launch_wc_paper_N07_frozen_shared180_r1.py', 'capture_wc_paper_N07_frozen_shared180_r1.py',
    'analyze_wc_paper_N07_frozen_shared180_r1.py', 'run_wc_paper_N07_production_cpu_bundle_r1.py',
    'deploy_wc_paper_N07_production_cpu_r1.py', 'capture_wc_paper_N07_production_cpu_r1.py',
    'accept_wc_paper_N07_production_cpu_r1.py')]
TESTS = ['tests/' + n for n in (
    'test_frozen_shared_production_r1.py', 'test_frozen_shared_batch_r1.py', 'test_frozen_shared_inputs_r1.py',
    'test_frozen_shared_post_r1.py', 'test_frozen_shared_acceptance_r1.py', 'test_frozen_shared_dispatch_r1.py',
    'test_frozen_shared_cpu_acceptance_r1.py')]


BOOTSTRAP = r'''
import hashlib,io,json,os,pathlib,subprocess,sys,tarfile,time
meta=json.loads(sys.stdin.buffer.readline());archive=sys.stdin.buffer.read()
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr').resolve()
for name in ('base','stage'):
 relative=pathlib.PurePosixPath(meta[name])
 assert not relative.is_absolute() and '..' not in relative.parts and relative.parts[0]=='.sync'
module='src/wcomr/immutable_stage_payload_r1.py'
with tarfile.open(fileobj=io.BytesIO(archive),mode='r:gz') as stream:
 members=[m for m in stream if m.name==module]
 assert len(members)==1 and members[0].isfile()
 source=stream.extractfile(members[0]).read()
assert hashlib.sha256(source).hexdigest()==meta['plan']['overlay_sha256'][module]
namespace={'__name__':'source_only_stage_installer'}
exec(compile(source,'GIT_BOUND_STAGE_INSTALLER','exec'),namespace)
base=root/meta['base'];stage=root/meta['stage']
assert base.resolve()==pathlib.Path(meta['base_original_absolute']).resolve()
registration=namespace['install'](base,stage,archive,meta['plan'],source_revision=meta['source_revision'])
sys.path.insert(0,str(stage/'src'))
from wcomr.gpu_budget_pool_v2 import process_identity
command=[sys.executable,str(stage/'scripts/run_wc_paper_N07_production_cpu_bundle_r1.py'),
 '--project',str(root),'--stage',str(stage)]
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
 PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
with (stage/'CPU-bundle.log').open('xb') as log:
 child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
  env=env,start_new_session=True)
identity=process_identity(child.pid)
assert identity['state'] not in (None,'Z','X') and 'run_wc_paper_N07_production_cpu_bundle_r1.py' in identity['command']
now=time.time()
receipt=dict(status='N07_SHARED180_ACTUAL_PRODUCTION_CPU_SINGLE_DISPATCH',pid=child.pid,identity=identity,
 source_revision=meta['source_revision'],stage=str(stage),command=command,launched_unix=now,
 registration_sha256=hashlib.sha256((stage/'registration.json').read_bytes()).hexdigest(),
 payload_files=len(registration['payload_sha256']),overlay_files=len(meta['plan']['overlay_sha256']),
 expected_CPU_commands=6,first_collection_not_before_unix=now+240,
 shared_runtime_written=False,original_base_stage_written=False,GPU_submissions=0,ledger_written=False)
with (stage/'CPU-launch.json').open('x') as handle:json.dump(receipt,handle,indent=2)
print(json.dumps(receipt,allow_nan=False))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-CPU-capture', type=Path, required=True)
    parser.add_argument('--stage', required=True, help='Fresh project-relative .sync stage')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    sys.path.insert(0, str(ROOT / 'src'))
    from wcomr.frozen_shared_production_r1 import CONFIG, sha, validate_contract, verify_sampling_sources
    from wcomr.frozen_shared_inputs_r1 import bind_selected
    from wcomr.frozen_input_selection_r1 import select
    from wcomr.immutable_stage_payload_r1 import (
        configuration_closure, git_archive, plan, relative, registered_base_reference,
    )
    relative(args.stage)
    assert args.stage.startswith('.sync/wc-paper-n07-')
    config = json.loads((ROOT / CONFIG).read_text())  # Intentionally absent before actual final freeze.
    configuration_closure(ROOT, [CONFIG])
    refs = {}
    for key, binding in config['references'].items():
        path = ROOT / binding['ref']
        raw = gzip.decompress(path.read_bytes()) if path.suffix == '.gz' else path.read_bytes()
        refs[key] = json.loads(raw)
    assert refs['development']['N05'] == refs['N05_acceptance']
    assert refs['development']['N06'] == refs['N06_acceptance']
    selection = select(refs['dataset_catalog']['records'], refs['local_input_inventory']['excluded_group_members'],
        refs['input_protocol'], development=refs['development'], method_freeze=refs['method_freeze'],
        remote_audit=refs['remote_identity_audit'])
    assert selection == refs['selection']
    bound = bind_selected(selection, {n: (ROOT / binding['ref']).read_bytes() for n, binding in config['input_files'].items()})
    assert bound == refs['bound_inputs']; validate_contract(config, bound)
    numeric = verify_sampling_sources(ROOT, refs['shared_CPU_raw'], refs['shared_CPU_acceptance'])
    base = json.loads(gzip.decompress(args.base_CPU_capture.read_bytes()))
    assert base['status'] == 'N05_PRODUCTION_CPU_ONCE_CAPTURE'
    assert base['registration_SHA256'] == base['launch']['registration_sha256']
    assert base['registration']['source_revision'] == '15d77ac55de7f5715a76901c47e407663d41c9d3'
    assert all(base['payload_verified'].values())
    bundle = base['files']['CPU-bundle-result.json']['data']
    assert bundle['status'] == 'N05_CORE66_COMPLETE_PRODUCTION_CPU_PASS_NOT_GPU' and bundle['exit_code'] == 0
    overlay = plan(ROOT, config_roots=[CONFIG], python_entrypoints=ENTRIES,
        extra_files=TESTS, base_registration_sha256=base['registration_SHA256'],
        base_source_revision=base['registration']['source_revision'], numeric_sources=numeric['source_sha256'])
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    archive = git_archive(ROOT, overlay, revision)
    base_ref = registered_base_reference(base['registration']['stage'], base['launch']['stage'])
    metadata = dict(base=base_ref['project_relative'], base_original_absolute=base_ref['original_absolute'],
                    stage=args.stage, source_revision=revision, plan=overlay)
    envelope = json.dumps(metadata, ensure_ascii=False, allow_nan=False).encode() + b'\n' + archive
    try:
        result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
            '-o', 'ClearAllForwardings=yes', 'gkd_minchen', PYTHON + ' -c ' + shlex.quote(BOOTSTRAP)],
            input=envelope, capture_output=True, timeout=180)
    except (subprocess.TimeoutExpired, OSError) as error:
        value = dict(status='N07_CPU_DISPATCH_TRANSPORT_UNKNOWN_NO_RETRY', stage=args.stage,
            source_revision=revision, error_type=type(error).__name__, error=str(error),
            original_stage_recovery_ref=args.stage + '/CPU-launch.json', retry_authorized=False,
            task_terminal=False, GPU_submissions=0)
        args.output.write_text(json.dumps(value, indent=2) + '\n'); print(json.dumps(value)); raise
    value = dict(transport_exit_code=result.returncode, stderr=result.stderr.decode(),
                 source_revision=revision, overlay_plan=overlay)
    try: value['launch'] = json.loads(result.stdout)
    except json.JSONDecodeError: value['stdout'] = result.stdout.decode()
    args.output.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: v for k, v in value.items() if k != 'overlay_plan'}))
    raise SystemExit(result.returncode)


if __name__ == '__main__': main()
