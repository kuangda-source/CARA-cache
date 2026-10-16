#!/usr/bin/env python3
"""Git-bound independent full40 CPU stage after accepted common testing."""
import argparse
import gzip
import json
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PYTHON = '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
ENTRIES = ['scripts/' + name for name in (
    'run_wc_paper_N08_balanced_full40_r1.py', 'supervise_wc_paper_N08_balanced_full40_r1.py',
    'watch_wc_paper_N08_post_cpu_r1.py', 'postprocess_wc_paper_N08_balanced_full40_r1.py',
    'launch_wc_paper_N08_balanced_full40_r1.py', 'capture_wc_paper_N08_balanced_full40_r1.py',
    'analyze_wc_paper_N08_balanced_full40_r1.py', 'run_wc_paper_N08_production_cpu_bundle_r1.py',
    'deploy_wc_paper_N08_production_cpu_r1.py', 'capture_wc_paper_N08_production_cpu_r1.py',
    'accept_wc_paper_N08_production_cpu_r1.py')]
TESTS = ['tests/' + name for name in (
    'test_balanced_repeat_timing_r1.py', 'test_balanced_repeat_execution_r1.py', 'test_balanced_repeat_production_r1.py',
    'test_balanced_repeat_post_r1.py', 'test_balanced_repeat_cpu_acceptance_r1.py', 'test_balanced_repeat_supervision_r1.py',
    'test_balanced_repeat_dispatch_r1.py', 'test_balanced_repeat_acceptance_r1.py', 'test_balanced_repeat_capture_r1.py',
    'test_frozen_shared_production_r1.py', 'test_frozen_shared_batch_r1.py',
    'test_frozen_shared_inputs_r1.py')]


def accepted_common_identity(acceptance, capture, *, capture_sha256, shared_config_sha256):
    """Read only completion/config identities; never select from final scores."""
    counts = acceptance.get('original_status_counts', {})
    if (acceptance.get('terminal_receipt_audit_accepted') is not True
            or acceptance.get('scientific_available_cohorts_with_registered_missingness') is not True
            or acceptance['original_runner_paths'] != 180
            or acceptance['scope_counts']['total_paths'] != 180
            or acceptance['scope_counts']['scientific_paths'] != 160
            or counts.get('TECH_FAILED', 0) or counts.get('NOT_REACHED', 0)
            or acceptance['capture_sha256'] != capture_sha256
            or acceptance['source_revision'] != capture['launch']['source_revision']
            or capture['config_sha256'] != shared_config_sha256):
        raise ValueError('Finish and accept the original whole N07 before deploying repeated timing CPU')


BOOTSTRAP = r'''
import hashlib,io,json,os,pathlib,subprocess,sys,tarfile,time
meta=json.loads(sys.stdin.buffer.readline());archive=sys.stdin.buffer.read()
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr').resolve()
for name in ('base','stage'):
 relative=pathlib.PurePosixPath(meta[name]);assert not relative.is_absolute() and '..' not in relative.parts and relative.parts[0]=='.sync'
module='src/wcomr/immutable_stage_payload_r1.py'
with tarfile.open(fileobj=io.BytesIO(archive),mode='r:gz') as stream:
 members=[m for m in stream if m.name==module];assert len(members)==1 and members[0].isfile()
 source=stream.extractfile(members[0]).read()
assert hashlib.sha256(source).hexdigest()==meta['plan']['overlay_sha256'][module]
namespace={'__name__':'git_bound_source_installer'};exec(compile(source,'GIT_BOUND_CPU_SOURCE_INSTALLER','exec'),namespace)
base=root/meta['base'];stage=root/meta['stage'];assert base.resolve()==pathlib.Path(meta['base_original_absolute']).resolve()
registration=namespace['install'](base,stage,archive,meta['plan'],source_revision=meta['source_revision'],
 cpu_scope='FROZEN_N08_PRODUCTION_CPU_PREPARATION_NO_GPU')
sys.path.insert(0,str(stage/'src'))
from wcomr.gpu_budget_pool_v2 import process_identity
command=[sys.executable,str(stage/'scripts/run_wc_paper_N08_production_cpu_bundle_r1.py'),
 '--project',str(root),'--stage',str(stage)]
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
 PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
with (stage/'N08-CPU-bundle.log').open('xb') as log:
 child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
identity=process_identity(child.pid)
assert identity['state'] not in (None,'Z','X') and 'run_wc_paper_N08_production_cpu_bundle_r1.py' in identity['command']
now=time.time()
receipt=dict(status='N08_FULL40_ACTUAL_PRODUCTION_CPU_SINGLE_DISPATCH',pid=child.pid,identity=identity,
 source_revision=meta['source_revision'],stage=str(stage),command=command,launched_unix=now,
 registration_sha256=hashlib.sha256((stage/'registration.json').read_bytes()).hexdigest(),
 payload_files=len(registration['payload_sha256']),overlay_files=len(meta['plan']['overlay_sha256']),
 expected_CPU_commands=9,first_collection_not_before_unix=now+300,
 shared_runtime_written=False,original_base_stage_written=False,GPU_submissions=0,ledger_written=False)
with (stage/'N08-CPU-launch.json').open('x') as handle:json.dump(receipt,handle,indent=2)
print(json.dumps(receipt,allow_nan=False))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-CPU-capture', type=Path, required=True)
    parser.add_argument('--N07-capture', type=Path, required=True)
    parser.add_argument('--N07-acceptance', type=Path, required=True)
    parser.add_argument('--stage', required=True); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); assert not args.output.exists()
    sys.path.insert(0, str(ROOT / 'src'))
    from wcomr.balanced_repeat_production_r1 import CONFIG, read_reference, validate_contract
    from wcomr.frozen_shared_production_r1 import CONFIG as SHARED_CONFIG, sha, validate_contract as shared_contract, verify_sampling_sources
    from wcomr.frozen_input_selection_r1 import select
    from wcomr.frozen_shared_inputs_r1 import bind_selected
    from wcomr.immutable_stage_payload_r1 import configuration_closure, git_archive, plan, relative, registered_base_reference
    relative(args.stage); assert args.stage.startswith('.sync/wc-paper-n08-') and len(Path(args.stage).parts) == 2
    config = json.loads((ROOT / CONFIG).read_text())  # Absent until the real final freeze.
    configuration_closure(ROOT, [CONFIG])
    refs = {name: read_reference(ROOT, binding) for name, binding in config['references'].items()}
    shared = refs['shared_config']; bound = validate_contract(config, refs['timing_protocol'], shared, refs['method_freeze'])
    assert config['references']['shared_config']['ref'] == SHARED_CONFIG
    assert config['references']['method_freeze'] == shared['references']['method_freeze']
    completed = json.loads(gzip.decompress(args.N07_capture.read_bytes()))
    accepted_common_identity(json.loads(args.N07_acceptance.read_text()), completed,
        capture_sha256=sha(args.N07_capture), shared_config_sha256=sha(ROOT / SHARED_CONFIG))
    shared_refs = {name: read_reference(ROOT, binding) for name, binding in shared['references'].items()}
    assert shared_refs['development']['N05'] == shared_refs['N05_acceptance']
    assert shared_refs['development']['N06'] == shared_refs['N06_acceptance']
    selected = select(shared_refs['dataset_catalog']['records'], shared_refs['local_input_inventory']['excluded_group_members'],
        shared_refs['input_protocol'], development=shared_refs['development'], method_freeze=shared_refs['method_freeze'],
        remote_audit=shared_refs['remote_identity_audit'])
    assert selected == shared_refs['selection']
    shared_bound = bind_selected(selected, {name: (ROOT / b['ref']).read_bytes() for name, b in shared['input_files'].items()})
    assert shared_bound == shared_refs['bound_inputs']; shared_contract(shared, shared_bound)
    assert shared_bound['method_ids'] == bound['final_shared_method_ids']
    numeric = verify_sampling_sources(ROOT, shared_refs['shared_CPU_raw'], shared_refs['shared_CPU_acceptance'])
    base = json.loads(gzip.decompress(args.base_CPU_capture.read_bytes()))
    assert base['status'] == 'N05_PRODUCTION_CPU_ONCE_CAPTURE' and base['registration_SHA256'] == base['launch']['registration_sha256']
    assert base['registration']['source_revision'] == '15d77ac55de7f5715a76901c47e407663d41c9d3'
    assert set(base['payload_verified']) == set(base['registration']['payload_sha256']) and all(base['payload_verified'].values())
    result = base['files']['CPU-bundle-result.json']['data']
    assert result['status'] == 'N05_CORE66_COMPLETE_PRODUCTION_CPU_PASS_NOT_GPU' and result['exit_code'] == 0
    overlay = plan(ROOT, config_roots=[CONFIG], python_entrypoints=ENTRIES, extra_files=TESTS,
        base_registration_sha256=base['registration_SHA256'], base_source_revision=base['registration']['source_revision'],
        numeric_sources=numeric['source_sha256'])
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    archive = git_archive(ROOT, overlay, revision)
    base_ref = registered_base_reference(base['registration']['stage'], base['launch']['stage'])
    metadata = dict(base=base_ref['project_relative'], base_original_absolute=base_ref['original_absolute'],
                    stage=args.stage, source_revision=revision, plan=overlay)
    envelope = json.dumps(metadata, ensure_ascii=False, allow_nan=False).encode() + b'\n' + archive
    try:
        call = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', '-o', 'ClearAllForwardings=yes',
            'gkd_minchen', PYTHON + ' -c ' + shlex.quote(BOOTSTRAP)], input=envelope, capture_output=True, timeout=180)
    except (subprocess.TimeoutExpired, OSError) as error:
        value = dict(status='N08_CPU_DISPATCH_TRANSPORT_UNKNOWN_NO_RETRY', stage=args.stage, source_revision=revision,
            error_type=type(error).__name__, error=str(error), original_stage_recovery_ref=args.stage + '/N08-CPU-launch.json',
            retry_authorized=False, task_terminal=False, GPU_submissions=0)
        args.output.write_text(json.dumps(value, indent=2) + '\n'); print(json.dumps(value)); raise
    value = dict(transport_exit_code=call.returncode, stderr=call.stderr.decode(errors='replace'), source_revision=revision,
                 overlay_plan=overlay, GPU_retry_authorized=False)
    try: value['launch'] = json.loads(call.stdout)
    except (json.JSONDecodeError, UnicodeDecodeError):
        value.update(status='N08_CPU_RESPONSE_UNKNOWN_NO_RETRY', stdout=call.stdout.decode(errors='replace'),
                     original_stage_recovery_ref=args.stage + '/N08-CPU-launch.json', task_terminal=False)
    args.output.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: v for k, v in value.items() if k != 'overlay_plan'}))
    raise SystemExit(call.returncode if 'launch' in value else (call.returncode or 1))


if __name__ == '__main__': main()
