"""Deploy a separate CPU reader; preserve original GPU and CPU sources."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile


def main():
    root = Path(__file__).resolve().parents[1]
    registration = root/'manifests/wc_e4c_readonly_reader_cpu_r1_20261011.json'
    reg = json.loads(registration.read_text())
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    blobs = {n: (root/n).read_bytes() for n in reg['new_payload_sha256']}
    for n, raw in blobs.items():
        assert hashlib.sha256(raw).hexdigest() == reg['new_payload_sha256'][n]
        assert raw == subprocess.check_output(['git', 'show', revision+':'+n], cwd=root)
    blobs['registration.json'] = registration.read_bytes()
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w:gz') as archive:
        for name, raw in blobs.items():
            info = tarfile.TarInfo(name); info.size = len(raw); archive.addfile(info, io.BytesIO(raw))
    name = reg['stage_name']; local = root/'.sync'/(name+'.tgz'); assert not local.exists()
    local.write_bytes(buffer.getvalue())
    remote = '/home/gaokuangda/data/gkd/worldcache_omr/.sync/'+name+'.tgz'
    subprocess.run(['scp', '-q', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', str(local), 'gkd_minchen:'+remote], check=True)
    packet = dict(reg, revision=revision, archive=remote,
                  archive_sha256=hashlib.sha256(buffer.getvalue()).hexdigest())
    code = 'P='+repr(packet)+'\n'+r'''import hashlib,json,os,pathlib,subprocess,tarfile,time
project=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');s=project/'.sync'/P['stage_name'];old=project/P['original_stage']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((old/'receipt.json').read_text());assert r['exit_code']==r['child_exit_code']==0
assert sha(old/'receipt.json')==P['original_receipt_sha256'] and sha(old/'result.json')==P['original_result_sha256']
assert not any(pathlib.Path('/proc/'+str(pid)).exists() for pid in (r['pid'],r['child_pid']))
assert {n:sha(old/n) for n in P['original_payload_sha256']}==P['original_payload_sha256']==r['payload_after_sha256']
assert not s.exists() and sha(pathlib.Path(P['archive']))==P['archive_sha256'];s.mkdir()
with tarfile.open(P['archive']) as archive:
 for member in archive.getmembers():
  p=pathlib.PurePosixPath(member.name);assert member.isfile() and not p.is_absolute() and '..' not in p.parts
 archive.extractall(s)
assert {n:sha(s/n) for n in P['new_payload_sha256']}==P['new_payload_sha256']
py='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
command=[py,str(s/'scripts/supervise_wc_e4c_readonly_reader_cpu_r1.py'),'--stage',str(s),'--original-stage',str(old),'--revision',P['revision']]
with (s/'supervisor.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
  env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1'))
launch={'status':'E4C_READONLY_CPU_READER_DISPATCHED_NOT_GPU','stage':str(s),'supervisor_pid':child.pid,
 'source_revision':P['revision'],'registration_sha256':sha(s/'registration.json'),
 'GPU_submissions':0,'ledger_written':False,'observed_unix':time.time()}
(s/'launch.json').write_text(json.dumps(launch,indent=2)+'\n');print(json.dumps(launch))
'''
    result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', 'gkd_minchen',
                             'python3 -'], input=code, text=True, capture_output=True)
    if result.returncode: raise RuntimeError(result.stderr[-3000:])
    value = json.loads(result.stdout)
    target = root/'reports/wc_e4c_readonly_reader_cpu_r1_launch_20261011.json'; assert not target.exists()
    target.write_text(json.dumps(value, indent=2)+'\n'); print(json.dumps(value))


if __name__ == '__main__': main()
