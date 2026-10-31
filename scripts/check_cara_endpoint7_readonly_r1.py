import sys,subprocess,shlex,json,time,os,signal
from pathlib import Path
if Path('reports/cara_endpoint7_readonly_assets_resources_r1_20261101.json').exists():
    raise FileExistsError('Original read-only receipt exists; retain it and use a new explicit receipt for any future check')
sys.path.insert(0,'scripts')
from cara_two_card_transport_r1 import password
remote=r'''
import pathlib,subprocess,json,hashlib,time
root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace');runtime=root/'runtime'
def command(args):
 r=subprocess.run(args,capture_output=True,text=True,timeout=15);return dict(code=r.returncode,stdout=r.stdout,stderr=r.stderr)
names=['cosmos_predict2/_src/predict2/models/video2world_model_rectified_flow.py','cosmos_predict2/_src/predict2/models/text2world_model_rectified_flow.py','cosmos_predict2/_src/predict2/models/fm_solvers_unipc.py']
sources={n:dict(sha256=hashlib.sha256((runtime/n).read_bytes()).hexdigest(),text=(runtime/n).read_text()) for n in names}
assets=json.loads(payload)
checked=[]
for a in assets:
 p=pathlib.Path(a['path']);checked.append(dict(path=str(p),expected_sha256=a['sha256'],actual_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size))
s=__import__('os').statvfs(root)
print(json.dumps(dict(observed_unix=time.time(),host=command(['hostname']),gpu=command(['nvidia-smi','--query-gpu=uuid,temperature.gpu,memory.used,utilization.gpu,compute_mode','--format=csv,noheader']),apps=command(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader']),containers=command(['docker','ps','--format','{{.Names}} {{.Status}}']),available_disk_bytes=s.f_bavail*s.f_frsize,sources=sources,assets=checked,central_ledger_accessed=False,GPU_submissions=0)))
'''
p=json.load(open('plans/cara_next_stage_20261101/e1/ENDPOINT7_46_MANIFEST_R1.json'))
assets={a['path']:a for r in p['formal_matrix'] if r['mode']=='REUSE_COMPLETE_SCORE' for a in [r['source'],r['reference']]}
code='import sys;payload=sys.stdin.read();exec('+repr(remote)+')'
secret=password();cmd="sudo -S -p '' -u gaokuangda -g docker /home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -c "+shlex.quote(code)
child=subprocess.Popen(['ssh','-F','.sync/cara-fast-mainline-tailscale-20261030/ssh_config.budget_direct.private','-o','BatchMode=yes','-o','ConnectTimeout=20','-o','ServerAliveInterval=10','-o','ServerAliveCountMax=3','two_card_lan',cmd],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
try:out,err=child.communicate((secret+'\n'+json.dumps(list(assets.values()))).encode(),timeout=90)
except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);out,err=child.communicate()
result=json.loads(out) if child.returncode==0 else None
if result:
 sources=result.pop('sources');folder=Path('.sync/euler35-source-20261101');folder.mkdir(exist_ok=True)
 for name,item in sources.items():(folder/Path(name).name).write_text(item['text'])
 result['runtime_source_sha256']={n:v['sha256'] for n,v in sources.items()}
record=dict(exit_code=child.returncode,result=result,stderr=err.decode().replace(secret,'[REDACTED]'))
Path('reports/cara_endpoint7_readonly_assets_resources_r1_20261101.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(dict(exit_code=child.returncode,assets=len((result or {}).get('assets',[])),gpu=(result or {}).get('gpu'),containers=(result or {}).get('containers'))))
