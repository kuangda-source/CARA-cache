#!/usr/bin/env python3
"""Single original SCP transfer with pinned bytes and an ETA-only collection."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = 'scripts/relay_wc_N10_viclip_resource_r1.py'
SERVER_ROOT = '/home/gaokuangda/data/gkd/worldcache_omr'
EXPECTED = dict(
    name='ViClip-InternVid-10M-FLT.pth', bytes=1710545812,
    sha256='7a4d6ad6eac6632db3693f4b97f9f8f6445b65b1e139a6fc6686150522238c56',
    url='https://huggingface.co/OpenGVLab/VBench_Used_Models/resolve/'
        '83290ee59b4e2c0a4d198857edbc79dd186b8d44/ViClip-InternVid-10M-FLT.pth')
SSH = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
       '-o', 'ClearAllForwardings=yes', '-o', 'ServerAliveInterval=15',
       '-o', 'ServerAliveCountMax=3', 'gkd_minchen']

PREPARE = r'''
import hashlib,json,pathlib,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr').resolve()
relative=pathlib.PurePosixPath(META['remote_stage'])
assert not relative.is_absolute() and '..' not in relative.parts and len(relative.parts)==2
assert relative.parts[0]=='.sync' and relative.parts[1].startswith('wc-N10-viclip-relay-')
stage=root/relative;assert not stage.exists();stage.mkdir()
raw=META['remote_registration_text'].encode()
assert hashlib.sha256(raw).hexdigest()==META['remote_registration_sha256']
(stage/'registration.json').write_bytes(raw)
print(json.dumps(dict(status='N10_RESOURCE_RELAY_FRESH_SERVER_STAGE_PREPARED',stage=str(stage),
 registration_sha256=hashlib.sha256(raw).hexdigest(),source_revision=META['source_revision'],
 partial=str(stage/(META['expected_weight']['name']+'.part')),observed_unix=time.time(),
 GPU_submissions=0,ledger_written=False)))
'''

FINALIZE = r'''
import hashlib,json,pathlib,time
stage=pathlib.Path(PREPARED['stage']);reg=stage/'registration.json'
assert hashlib.sha256(reg.read_bytes()).hexdigest()==META['remote_registration_sha256']
expected=META['expected_weight'];part=stage/(expected['name']+'.part');target=stage/expected['name']
assert not target.exists() and not part.is_symlink() and part.is_file()
assert not (stage/'resource-result.json').exists()
before=part.stat();value=hashlib.sha256()
with part.open('rb') as handle:
 for block in iter(lambda:handle.read(8*1024*1024),b''):value.update(block)
after=part.stat();assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
assert after.st_size==expected['bytes'] and value.hexdigest()==expected['sha256']
part.rename(target)
result=dict(status='N10_PINNED_VICLIP_RESOURCE_BYTES_ACCEPTED_NOT_MODEL_RUNTIME',exit_code=0,
 source_revision=META['source_revision'],target=str(target),actual_bytes=after.st_size,
 actual_sha256=value.hexdigest(),ended_unix=time.time(),
 transport_origin='LOCAL_PINNED_RESOURCE_THEN_ORIGINAL_SCP',
 local_resource_capture_sha256=META['local_resource_capture_sha256'],
 local_download_source_revision=META['local_download_source_revision'],
 models_imported=False,weights_loaded=0,GPU_submissions=0,ledger_written=False)
with (stage/'resource-result.json').open('x') as handle:json.dump(result,handle,indent=2)
print(json.dumps(result,allow_nan=False))
'''

CAPTURE = r'''
import hashlib,json,pathlib,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr').resolve()
stage=root/META['remote_stage'];expected=META['expected_weight']
reg=stage/'registration.json';target=stage/expected['name'];part=stage/(expected['name']+'.part')
value=dict(stage=str(stage),registration_exists=reg.is_file(),target_exists=target.is_file(),
 partial_bytes=part.stat().st_size if part.is_file() else None,observed_unix=time.time(),
 result=None,server_files_written=False,GPU_submissions=0,ledger_written=False)
if reg.is_file():
 value['registration_sha256']=hashlib.sha256(reg.read_bytes()).hexdigest()
 assert value['registration_sha256']==META['remote_registration_sha256']
 result=stage/'resource-result.json'
 if result.is_file():
  raw=result.read_bytes();value['result_sha256']=hashlib.sha256(raw).hexdigest()
  try:value['result']=json.loads(raw)
  except (ValueError,UnicodeError) as error:value.update(result_parse_error=str(error),result_raw_hex=raw.hex())
if not ORIGINAL_ALIVE and target.is_file():
 assert not target.is_symlink();before=target.stat();digest=hashlib.sha256()
 with target.open('rb') as handle:
  for block in iter(lambda:handle.read(8*1024*1024),b''):digest.update(block)
 after=target.stat();assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
 value.update(independent_target_bytes=after.st_size,independent_target_sha256=digest.hexdigest())
print(json.dumps(value,allow_nan=False))
'''


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def write(path, value):
    with Path(path).open('x') as handle:
        json.dump(value, handle, indent=2, allow_nan=False)
        handle.write('\n')


def remote(code, *, timeout=150):
    result = subprocess.run(SSH + ['python3 -c ' + shlex.quote(code)],
                            capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError('Original SSH command failed: ' + result.stderr.decode(errors='replace'))
    return json.loads(result.stdout)


def accepted_local_resource(path):
    value = json.loads(Path(path).read_text())
    launch, result = value.get('launch', {}), value.get('result', {})
    if (value.get('status') != 'N10_LOCAL_PROXY_RESOURCE_ORIGINAL_ONCE_CAPTURE'
            or value.get('original_process_alive') is not False
            or value.get('local_resource_bytes_independently_accepted') is not True
            or launch.get('expected_weight') != EXPECTED
            or value['observed_unix'] < launch['first_collection_not_before_unix']
            or (value.get('independent_target_bytes'), value.get('independent_target_sha256'))
               != (EXPECTED['bytes'], EXPECTED['sha256'])
            or not result or result.get('exit_code') != 0
            or result.get('source_revision') != launch.get('source_revision')):
        raise ValueError('Accept the complete original local resource before any Git or SSH work')
    target = Path(launch['stage']) / EXPECTED['name']
    if (target.is_symlink() or not target.is_file() or result.get('target') != str(target)
            or target.stat().st_size != EXPECTED['bytes'] or sha(target) != EXPECTED['sha256']):
        raise ValueError('Original local resource bytes changed after collection')
    return value, target


def original_local_process(launch):
    result = subprocess.run(['ps', '-p', str(launch['pid']), '-o', 'pid=,lstart=,stat=,command='],
                            capture_output=True, text=True, timeout=10)
    if not result.stdout.strip():
        return False, None, result.stdout
    date = r'\w{3}\s+\w{3}\s+\d+\s+\d\d:\d\d:\d\d\s+\d{4}'
    before = re.match(r'^\d+\s+(' + date + r')\s+(.*)$', launch['process_at_admission'])
    actual = re.match(r'^\s*\d+\s+(' + date + r')\s+(\S+)\s+(.*)$', result.stdout.strip())
    assert before and actual
    worker = str(Path(launch['stage'])/'relay_wc_N10_viclip_resource_r1.py')
    # nice execs Python in the same PID. Bind the original start time and
    # immutable worker/arguments rather than its transient executable prefix.
    same = (' '.join(before[1].split()) == ' '.join(actual[1].split())
            and worker in before[2] and worker in actual[3]
            and before[2].split(worker, 1)[1] == actual[3].split(worker, 1)[1])
    return bool(same and actual[2][0] not in ('Z', 'X')), same, result.stdout


def run_worker(stage):
    stage = Path(stage).resolve()
    metadata = json.loads((stage/'registration.json').read_text())
    assert metadata['purpose'] == 'N10_PINNED_RESOURCE_ORIGINAL_SCP_ONLY'
    assert metadata['expected_weight'] == EXPECTED
    assert sha(Path(__file__)) == metadata['worker_sha256']
    assert sha(metadata['local_resource_capture_ref']) == metadata['local_resource_capture_sha256']
    write(stage/'relay-dispatch-fence.json', dict(source_revision=metadata['source_revision'], unix=time.time()))
    value = dict(status='N10_ORIGINAL_RESOURCE_RELAY_FAILED_RETAINED_NO_RETRY', exit_code=1,
                 source_revision=metadata['source_revision'], GPU_submissions=0, ledger_written=False)
    try:
        _, target = accepted_local_resource(metadata['local_resource_capture_ref'])
        prepared = remote('META='+repr(metadata)+'\n'+PREPARE)
        write(stage/'server-prepared.json', prepared)
        assert prepared['status'] == 'N10_RESOURCE_RELAY_FRESH_SERVER_STAGE_PREPARED'
        assert prepared['source_revision'] == metadata['source_revision']
        assert prepared['registration_sha256'] == metadata['remote_registration_sha256']
        remote_stage = Path(prepared['stage'])
        assert remote_stage.parts[-2:] == Path(metadata['remote_stage']).parts
        assert prepared['partial'] == str(remote_stage/(EXPECTED['name']+'.part'))
        # The original scp process owns the sole transfer; never resume/retry it automatically.
        before = target.stat()
        command = ['scp', '-q', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
                   '-o', 'ClearAllForwardings=yes', '-o', 'ServerAliveInterval=15',
                   '-o', 'ServerAliveCountMax=3', str(target), 'gkd_minchen:'+prepared['partial']]
        call = subprocess.run(command, capture_output=True)
        write(stage/'scp-exit.json', dict(exit_code=call.returncode,
              stdout=call.stdout.decode(errors='replace'), stderr=call.stderr.decode(errors='replace')))
        if call.returncode:
            raise RuntimeError('Original SCP failed; preserve the partial and original handle')
        after = target.stat()
        assert (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns)
        final = remote('META='+repr(metadata)+'\nPREPARED='+repr(prepared)+'\n'+FINALIZE)
        assert (final['actual_bytes'], final['actual_sha256']) == (EXPECTED['bytes'], EXPECTED['sha256'])
        value.update(status='N10_ORIGINAL_SCP_TRANSFER_AND_REMOTE_HASH_COMPLETE_NOT_MODEL_RUNTIME',
                     exit_code=0, remote_result=final)
    except Exception as error:
        value.update(error_type=type(error).__name__, error=str(error), retry_authorized=False)
    finally:
        value['ended_unix'] = time.time()
        write(stage/'relay-result.json', value)
    return value['exit_code']


def launch(args):
    captured, target = accepted_local_resource(args.local_resource_capture)
    source = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    raw = (ROOT/SCRIPT).read_bytes()
    assert subprocess.check_output(['git', 'show', source+':'+SCRIPT], cwd=ROOT) == raw
    relative = Path(args.stage)
    assert not relative.is_absolute() and '..' not in relative.parts and len(relative.parts) == 2
    assert relative.parts[0] == '.sync' and relative.parts[1].startswith('wc-N10-viclip-relay-')
    stage = ROOT/relative
    stage.mkdir()
    worker = stage/'relay_wc_N10_viclip_resource_r1.py'
    worker.write_bytes(raw)
    reg = dict(purpose='N10_PINNED_RESOURCE_ORIGINAL_SCP_ONLY', source_revision=source,
        expected_weight=EXPECTED, worker_sha256=hashlib.sha256(raw).hexdigest(),
        local_resource_capture_ref=str(args.local_resource_capture.resolve()),
        local_resource_capture_sha256=sha(args.local_resource_capture),
        local_download_source_revision=captured['launch']['source_revision'],
        remote_stage=str(relative), transport_origin='LOCAL_PINNED_RESOURCE_THEN_ORIGINAL_SCP',
        GPU_submissions=0, ledger_written=False, models_imported=False, weights_loaded=0)
    remote_registration = json.dumps(reg, indent=2, allow_nan=False)+'\n'
    reg.update(remote_registration_text=remote_registration,
               remote_registration_sha256=hashlib.sha256(remote_registration.encode()).hexdigest())
    write(stage/'registration.json', reg)
    command = ['/usr/bin/nice', '-n', '10', str(ROOT/'.venv/bin/python'), str(worker), 'run', '--stage', str(stage)]
    started = time.time()
    with (stage/'relay.log').open('xb') as log:
        child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1'),
            cwd=ROOT, start_new_session=True)
    identity = subprocess.check_output(['ps', '-p', str(child.pid), '-o', 'pid=,lstart=,command='],
                                       text=True, timeout=10).strip()
    assert str(worker) in identity
    value = dict(status='N10_ORIGINAL_LOCAL_SCP_RELAY_SINGLE_DISPATCHED', pid=child.pid,
        process_at_admission=identity, process_platform='LOCAL_MACOS', source_revision=source,
        stage=str(stage), remote_stage=str(relative), expected_weight=EXPECTED,
        registration_sha256=sha(stage/'registration.json'), worker_sha256=sha(worker),
        remote_registration_sha256=reg['remote_registration_sha256'], started_unix=started,
        first_collection_not_before_unix=started+1800, estimated_wall_minutes=[10, 30],
        original_local_download_capture=str(args.local_resource_capture),
        GPU_submissions=0, ledger_written=False, models_imported=False, weights_loaded=0)
    write(args.output, value)
    print(json.dumps(value, allow_nan=False))


def capture(args):
    launch = json.loads(args.launch_ref.read_text())
    if time.time() < launch['first_collection_not_before_unix']:
        raise SystemExit('Before the original SCP ETA; no PID, file or SSH query')
    stage = Path(launch['stage'])
    assert sha(stage/'registration.json') == launch['registration_sha256']
    assert sha(stage/'relay_wc_N10_viclip_resource_r1.py') == launch['worker_sha256']
    metadata = json.loads((stage/'registration.json').read_text())
    alive, same, process = original_local_process(launch)
    observed = remote('META='+repr(metadata)+'\nORIGINAL_ALIVE='+repr(alive)+'\n'+CAPTURE)
    common = dict(stage=observed['stage'], source_revision=launch['source_revision'],
        expected_weight=EXPECTED, first_collection_not_before_unix=launch['first_collection_not_before_unix'],
        original_process_platform='LOCAL_MACOS_SCP_RELAY', pid=launch['pid'],
        process_at_admission=launch['process_at_admission'], remote_registration_sha256=launch['remote_registration_sha256'])
    value = dict(status='N10_ORIGINAL_RESOURCE_ONCE_CAPTURE', launch=common, observed_unix=time.time(),
        original_process_alive=alive, PID_identity_matches=same, local_process_stdout=process,
        original_relay_launch_ref=str(args.launch_ref), original_relay_launch_sha256=sha(args.launch_ref),
        transport_origin='LOCAL_PINNED_RESOURCE_THEN_ORIGINAL_SCP',
        result=observed['result'], target_exists=observed['target_exists'],
        independent_target_bytes=observed.get('independent_target_bytes'),
        independent_target_sha256=observed.get('independent_target_sha256'),
        remote_observation=observed, local_relay_result=None,
        GPU_submissions=0, ledger_written=False, server_files_written=False, models_imported=False, weights_loaded=0)
    local = stage/'relay-result.json'
    if local.is_file():
        value['local_relay_result'] = json.loads(local.read_text())
        value['local_relay_result_sha256'] = sha(local)
    log = stage/'relay.log'
    if not alive and log.is_file():
        value['original_relay_log_tail'] = log.read_text(errors='replace')[-6000:]
    result = value['result'] or {}
    value['resource_bytes_independently_accepted'] = bool(not alive
        and observed.get('registration_sha256') == launch['remote_registration_sha256']
        and result.get('exit_code') == 0 and result.get('source_revision') == launch['source_revision']
        and result.get('status') == 'N10_PINNED_VICLIP_RESOURCE_BYTES_ACCEPTED_NOT_MODEL_RUNTIME'
        and (result.get('actual_bytes'), result.get('actual_sha256')) == (EXPECTED['bytes'], EXPECTED['sha256'])
        and (value['independent_target_bytes'], value['independent_target_sha256']) == (EXPECTED['bytes'], EXPECTED['sha256'])
        and result.get('target') == str(Path(common['stage'])/EXPECTED['name']))
    write(args.output, value)
    print(json.dumps({k:value[k] for k in ('status', 'original_process_alive', 'resource_bytes_independently_accepted')}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest='mode', required=True)
    p = modes.add_parser('launch')
    p.add_argument('--local-resource-capture', type=Path, required=True)
    p.add_argument('--stage', required=True)
    p.add_argument('--output', type=Path, required=True)
    p = modes.add_parser('run')
    p.add_argument('--stage', type=Path, required=True)
    p = modes.add_parser('capture')
    p.add_argument('--launch-ref', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.mode == 'run':
        raise SystemExit(run_worker(args.stage))
    assert not args.output.exists()
    (launch if args.mode == 'launch' else capture)(args)


if __name__ == '__main__':
    main()
