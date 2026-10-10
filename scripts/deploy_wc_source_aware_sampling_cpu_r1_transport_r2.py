#!/usr/bin/env python3
"""Transport the unchanged registered CPU scope as a file after stdin timeout."""
import ast
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile

REMOTE_ARCHIVE = '/home/gaokuangda/data/gkd/worldcache_omr/.sync/wc-source-aware-sampling-cpu-r1-20261010.transport-r2.tgz'


def main():
    ref = Path('manifests/wc_source_aware_sampling_cpu_r1_preregistration_20261010.json')
    reg = json.loads(ref.read_text())
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    launch = Path('reports/wc_source_aware_sampling_cpu_r1_launch_20261010.json')
    assert not launch.exists()
    failure = json.loads(Path('reports/wc_source_aware_sampling_cpu_r1_transport_failure_20261010.json').read_text())
    assert failure['remote_stage_absent_after_failure'] and failure['matching_remote_processes'] == 0
    proof = json.loads(Path(reg['accepted_A_P0_prerequisite']['capture_ref']).read_text())
    assert proof['exit_code'] == 0 and proof['independent_source_complete_results_and_actual_artifact_hashes_verified']
    assert proof['independent_tensor_reload']['actual_tensors'] == 5328
    assert proof['independent_tensor_reload']['full_partial_references'] == 32
    tree = ast.parse(Path('scripts/deploy_wc_source_aware_sampling_cpu_r1.py').read_text())
    driver = next(ast.literal_eval(node.value) for node in tree.body
                  if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'DRIVER' for t in node.targets))
    compile(driver, 'unchanged_registered_driver', 'exec')
    assert ref.read_bytes() == subprocess.check_output(['git', 'show', revision + ':' + str(ref)])
    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode='w:gz') as tar:
        files = {n: Path(n).read_bytes() for n in reg['payload_sha256']}
        for n, raw in files.items():
            assert hashlib.sha256(raw).hexdigest() == reg['payload_sha256'][n]
            assert raw == subprocess.check_output(['git', 'show', revision + ':' + n])
        files.update({'registration.json': ref.read_bytes(), 'driver.py': driver.encode()})
        for n, raw in files.items():
            entry = tarfile.TarInfo(n)
            entry.size = len(raw)
            tar.addfile(entry, io.BytesIO(raw))
    raw = archive.getvalue()
    archive_path = Path('.sync/wc-source-aware-sampling-cpu-r1-20261010.transport-r2.tgz')
    assert not archive_path.exists()
    archive_path.write_bytes(raw)
    packet = {'archive_path': REMOTE_ARCHIVE, 'archive_sha256': hashlib.sha256(raw).hexdigest(),
              'archive_bytes': len(raw), 'source_revision': revision,
              'driver_sha256': hashlib.sha256(driver.encode()).hexdigest(), 'transport': 'SCP_FILE_R2_UNCHANGED_SCOPE'}
    check = "import pathlib; assert not pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr/.sync/wc-source-aware-sampling-cpu-r1-20261010').exists(); assert not pathlib.Path(" + repr(REMOTE_ARCHIVE) + ").exists()"
    subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', 'gkd_minchen', 'python3 -'],
                   input=check, text=True, check=True, timeout=40)
    print(json.dumps({'transport': packet['transport'], 'archive_bytes': len(raw), 'phase': 'uploading'}), flush=True)
    subprocess.run(['scp', '-q', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', str(archive_path),
                    'gkd_minchen:' + REMOTE_ARCHIVE], check=True, timeout=600)
    code = 'P=' + repr(packet) + '\n' + r'''
import hashlib,io,json,os,pathlib,subprocess,tarfile,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=root/'.sync/wc-source-aware-sampling-cpu-r1-20261010'
assert not stage.exists();raw=pathlib.Path(P['archive_path']).read_bytes()
assert len(raw)==P['archive_bytes'] and hashlib.sha256(raw).hexdigest()==P['archive_sha256']
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as tar:
 for item in tar.getmembers():
  p=pathlib.PurePosixPath(item.name);assert item.isfile() and not p.is_absolute() and '..' not in p.parts
 stage.mkdir();tar.extractall(stage)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
reg=json.loads((stage/'registration.json').read_text());prerequisite=reg['accepted_A_P0_prerequisite']
assert sha(stage/'driver.py')==P['driver_sha256']
assert {n:sha(stage/n) for n in reg['payload_sha256']}==reg['payload_sha256']
old=root/prerequisite['stage'];previous=json.loads((old/'receipt.json').read_text())
assert previous['exit_code']==previous['child_exit_code']==0 and previous['source_revision']==prerequisite['source_revision']
assert not any(pathlib.Path('/proc/'+str(p)).exists() for p in (previous['pid'],previous['child_pid']))
assert sha(old/'result.json')==previous['result_sha256']
previous_reg=json.loads((old/'registration.json').read_text())
assert {n:sha(old/n) for n in previous_reg['payload_sha256']}==previous_reg['payload_sha256']==previous['payload_after_sha256']
command=['python3',str(stage/'driver.py'),str(stage),P['source_revision']]
with (stage/'driver.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'),start_new_session=True)
value={'stage':str(stage),'supervisor_pid':child.pid,'source_revision':P['source_revision'],'archive_sha256':P['archive_sha256'],
 'registration_sha256':sha(stage/'registration.json'),'driver_sha256':sha(stage/'driver.py'),'command':command,
 'transport':P['transport'],'remote_archive_path':P['archive_path'],'GPU_submissions':0,
 'ledger_written':False,'GPU_lock_acquired':False,'observed_unix':time.time()}
(stage/'launch.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))
'''
    result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', 'gkd_minchen', 'python3 -'],
                            input=code, text=True, capture_output=True, timeout=55)
    if result.returncode:
        raise RuntimeError(result.stderr[-3000:])
    value = json.loads(result.stdout)
    launch.write_text(json.dumps(value, indent=2) + '\n')
    print(json.dumps(value), flush=True)


if __name__ == '__main__':
    main()
