"""Independent CPU stage, full frozen inherited source plus new speed20 files."""
import argparse,hashlib,io,json,subprocess,tarfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]
NEW=['src/wcomr/clean_speed20_r1.py','tests/check_clean_speed20_cpu_r1.py',
 'scripts/check_wc_clean_speed20_cpu_r1.py','configs/wc_clean_speed20_r1_20261012.json',
 'research/373_WC_CLEAN_SPEED20_PREREGISTRATION_20261012.md']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--suffix',default='r2');args=parser.parse_args()
 prior=json.loads(subprocess.check_output(['ssh','-o','BatchMode=yes','-o','ClearAllForwardings=yes','gkd_minchen',"python3 -c \"import json;print(json.dumps(json.load(open('/home/gaokuangda/data/gkd/worldcache_omr/.sync/wc-e3-complete64-selected-r1-20261011/e3-complete64-config.json'))['payload_sha256']))\""],text=True))
 new=NEW+[str(p.relative_to(R)) for p in sorted((R/'src/wcomr').glob('*.py')) if str(p.relative_to(R)) not in prior and str(p.relative_to(R)) not in NEW]
 rev=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
 packet={'source_revision':rev,'new_payload':{n:sha(R/n) for n in new}}
 buf=io.BytesIO()
 with tarfile.open(fileobj=buf,mode='w:gz') as tar:
  for name in new:tar.add(R/name,arcname=name)
 archive=buf.getvalue()
 packet['stage_name']='wc-clean-speed20-cpu-'+args.suffix+'-20261012'
 code='P='+repr(packet)+'\n'+r'''import pathlib,json,hashlib,shutil,subprocess,os
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');old=root/'.sync/wc-e3-complete64-selected-r1-20261011'
stage=root/'.sync'/P['stage_name'];assert not stage.exists();stage.mkdir()
c=json.loads((old/'e3-complete64-config.json').read_text())
for n,h in c['payload_sha256'].items():
 p=old/n;assert hashlib.sha256(p.read_bytes()).hexdigest()==h
 target=stage/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
print(str(stage))
'''
 call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen','python3 -'],input=code,text=True,capture_output=True,check=True)
 stage=call.stdout.strip()
 subprocess.run(['ssh','-o','BatchMode=yes','-o','ClearAllForwardings=yes','gkd_minchen','tar -xzf - -C '+stage],input=archive,check=True)
 code='P='+repr(packet)+'\nS='+repr(stage)+'\n'+r'''import pathlib,json,hashlib,subprocess,os,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=pathlib.Path(S);old=root/'.sync/wc-e3-complete64-selected-r1-20261011'
c=json.loads((old/'e3-complete64-config.json').read_text());payload=dict(c['payload_sha256'],**P['new_payload'])
for n,h in payload.items():assert hashlib.sha256((stage/n).read_bytes()).hexdigest()==h
parent=root/c['parent_stage'];pc=json.loads((parent/'current-birth-full64-config.json').read_text())
reg={'source_revision':P['source_revision'],'payload_sha256':payload,'runtime_source_sha256':pc['runtime_source_sha256'],'new_payload_sha256':P['new_payload']}
(stage/'registration.json').write_text(json.dumps(reg,indent=2)+'\n')
command=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python',str(stage/'scripts/check_wc_clean_speed20_cpu_r1.py'),'--stage',str(stage),'--runtime',str(root/'runtime'),'--output',str(stage/'CPU-result.json')]
with (stage/'CPU.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
receipt={'stage':str(stage),'source_revision':P['source_revision'],'CPU_pid':child.pid,'command':command,'GPU_submissions':0,'ledger_written':False,'started_unix':time.time(),'payload_files':len(payload),'new_payload_sha256':P['new_payload']}
(stage/'CPU-launch.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
'''
 call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen','python3 -'],input=code,text=True,capture_output=True,check=True)
 receipt=json.loads(call.stdout);(R/'reports/wc_clean_speed20_cpu_'+args.suffix+'_launch_20261012.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
if __name__=='__main__':main()
