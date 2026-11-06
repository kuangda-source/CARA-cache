"""Bind one fresh CPU stage to committed sources; do not alter live E4c."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile


def main():
    root=Path(__file__).resolve().parents[1]
    manifest=root/'manifests/wc_e5_early_head_cpu_r2_20261011.json'
    reg=json.loads(manifest.read_text());revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    blobs={n:(root/n).read_bytes() for n in reg['new_payload_sha256']}
    for n,raw in blobs.items():
        assert hashlib.sha256(raw).hexdigest()==reg['new_payload_sha256'][n]
        assert raw==subprocess.check_output(['git','show',revision+':'+n],cwd=root)
    assert manifest.read_bytes()==subprocess.check_output(['git','show',revision+':'+str(manifest.relative_to(root))],cwd=root)
    blobs['registration.json']=manifest.read_bytes();buffer=io.BytesIO()
    with tarfile.open(fileobj=buffer,mode='w:gz') as archive:
        for n,raw in blobs.items():
            item=tarfile.TarInfo(n);item.size=len(raw);archive.addfile(item,io.BytesIO(raw))
    name=reg['stage_name'];local=root/'.sync'/(name+'.tgz');assert not local.exists();local.write_bytes(buffer.getvalue())
    remote='/home/gaokuangda/data/gkd/worldcache_omr/.sync/'+name+'.tgz'
    subprocess.run(['scp','-q','-o','BatchMode=yes','-o','ConnectTimeout=15',str(local),'gkd_minchen:'+remote],check=True)
    packet=dict(reg,revision=revision,archive=remote,archive_sha256=hashlib.sha256(buffer.getvalue()).hexdigest())
    code='P='+repr(packet)+'\n'+r'''import hashlib,json,os,pathlib,shutil,subprocess,tarfile,time
project=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');old=project/P['inherited_stage'];stage=project/'.sync'/P['stage_name']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert {n:sha(old/n) for n in P['inherited_payload_sha256']}==P['inherited_payload_sha256']
assert not stage.exists() and sha(pathlib.Path(P['archive']))==P['archive_sha256'];stage.mkdir()
for n in P['inherited_payload_sha256']:
 q=stage/n;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(old/n,q)
with tarfile.open(P['archive']) as archive:
 for m in archive.getmembers():
  q=pathlib.PurePosixPath(m.name);assert m.isfile() and not q.is_absolute() and '..' not in q.parts
 archive.extractall(stage)
allfiles=dict(P['inherited_payload_sha256'],**P['new_payload_sha256']);assert {n:sha(stage/n) for n in allfiles}==allfiles
py='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
command=[py,str(stage/'scripts/supervise_wc_e5_early_head_cpu_r2.py'),'--stage',str(stage),'--revision',P['revision']]
with (stage/'supervisor.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
  env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
v={'status':'E5_EARLY_HEAD_CPU_DISPATCHED_NOT_GPU','pid':child.pid,'stage':str(stage),
 'source_revision':P['revision'],'payload_files':len(allfiles),'GPU_submissions':0,'ledger_written':False,'observed_unix':time.time()}
(stage/'launch.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],input=code,text=True,capture_output=True)
    if call.returncode:raise RuntimeError(call.stderr[-3500:])
    value=json.loads(call.stdout);path=root/'reports/wc_e5_early_head_cpu_r2_launch_20261011.json';assert not path.exists()
    path.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))


if __name__=='__main__':main()
