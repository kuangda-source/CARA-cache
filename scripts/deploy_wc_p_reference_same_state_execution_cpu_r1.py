"""Copy accepted459 readonly; run complete affected post/selection CPU only."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile


def main():
    root = Path(__file__).resolve().parents[1]
    ref = 'manifests/wc_p_reference_same_state_execution_cpu_r1_preregistration_20261011.json'
    reg = json.loads((root/ref).read_text())
    target = root/'reports/wc_p_reference_same_state_execution_cpu_r1_launch_20261011.json'
    assert not target.exists()
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    for name in [ref, reg['config_ref'], reg['protocol_ref']]+list(reg['new_payload_sha256']):
        assert (root/name).read_bytes() == subprocess.check_output(['git', 'show', revision+':'+name], cwd=root), name
    blobs = {n: (root/n).read_bytes() for n in reg['new_payload_sha256']}
    assert {n: hashlib.sha256(raw).hexdigest() for n, raw in blobs.items()} == reg['new_payload_sha256']
    blobs.update({'registration.json': (root/ref).read_bytes(),
        'p-reference-same-state-config.json': (root/reg['config_ref']).read_bytes(),
        'p-reference-execution-protocol.json': (root/reg['protocol_ref']).read_bytes()})
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w:gz') as archive:
        for name, raw in blobs.items():
            entry = tarfile.TarInfo(name); entry.size = len(raw); archive.addfile(entry, io.BytesIO(raw))
    stem = 'wc-p-reference-same-state-execution-cpu-r1-20261011'
    path = root/'.sync'/(stem+'.tgz'); assert not path.exists(); path.write_bytes(buffer.getvalue())
    remote = '/home/gaokuangda/data/gkd/worldcache_omr/.sync/'+stem+'.tgz'
    subprocess.run(['scp', '-q', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', str(path), 'gkd_minchen:'+remote], check=True)
    packet = {'stem': stem, 'archive': remote, 'archive_sha256': hashlib.sha256(buffer.getvalue()).hexdigest(),
        'revision': revision, 'original': reg['original_stage'],
        'receipt_sha256': reg['original_production_CPU_receipt_sha256'], 'method': reg['method_payload_sha256']}
    code = 'P='+repr(packet)+'\n'+r'''import hashlib,json,os,pathlib,shutil,subprocess,tarfile,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');old=root/P['original'];s=root/'.sync'/P['stem']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((old/'production-CPU-receipt.json').read_text());assert r['exit_code']==0 and r['child_exit_codes']==[0,0]
assert sha(old/'production-CPU-receipt.json')==P['receipt_sha256']
assert not any(pathlib.Path('/proc/'+str(pid)).exists() for pid in [r['pid']]+[x['pid'] for x in r['actual_entry_children']])
assert {n:sha(old/n) for n in P['method']}==P['method']==r['payload_after_sha256']
assert not s.exists() and sha(pathlib.Path(P['archive']))==P['archive_sha256'];s.mkdir()
for name in P['method']:
 target=s/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(old/name,target)
shutil.copyfile(old/'production-CPU-receipt.json',s/'production-CPU-receipt.json')
with tarfile.open(P['archive']) as archive:
 for member in archive.getmembers():
  name=pathlib.PurePosixPath(member.name);assert member.isfile() and not name.is_absolute() and '..' not in name.parts
  assert not (s/member.name).exists()
 archive.extractall(s)
c=json.loads((s/'p-reference-same-state-config.json').read_text());assert not c['GPU_execution_selected']
assert {n:sha(s/n) for n in c['payload_sha256']}==c['payload_sha256']
python='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
command=[python,str(s/'scripts/check_wc_p_reference_same_state_execution_cpu_r1.py'),'--project',str(root),'--stage',str(s),'--source-revision',P['revision']]
with (s/'driver.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
  env=dict(os.environ,CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1'))
value={'status':'P_REFERENCE_COMPLETE_POST_SELECTION_CPU_DISPATCHED_NOT_GPU','stage':str(s),
 'source_revision':P['revision'],'pid':child.pid,'archive_sha256':P['archive_sha256'],
 'config_sha256':sha(s/'p-reference-same-state-config.json'),'protocol_sha256':sha(s/'p-reference-execution-protocol.json'),
 'registration_sha256':sha(s/'registration.json'),'command':command,'GPU_submissions':0,'ledger_written':False,'observed_unix':time.time()}
(s/'launch.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))
'''
    call = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', 'gkd_minchen', 'python3 -'],
        input=code, text=True, capture_output=True)
    if call.returncode: raise RuntimeError(call.stderr[-3000:])
    value = json.loads(call.stdout); target.write_text(json.dumps(value, indent=2)+'\n'); print(json.dumps(value))


if __name__ == '__main__': main()
