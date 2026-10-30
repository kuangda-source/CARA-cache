import sys,json,hashlib,base64,subprocess,shlex,os,signal,time
from pathlib import Path
sys.path[:0]=['scripts','src']
from cara_budget_calibration_cpu_hosts_r3 import REMOTE as ORIGINAL
from cara_two_card_transport_r1 import password
from wcomr.cara_budget_cpu_resources_r2 import HOST_CONFIG
stage='cara-budget-calibration-CPU-a6000-r4-20261031'
action=sys.argv[1];output=Path(sys.argv[2]);assert action in ('prepare','capture') and not output.exists()
remote=ORIGINAL
payload=dict(action=action,host='two_card',stage_name=stage)
revision='c2b079781ceb8a2d458f5eb3680fb267326a3927'
if action=='prepare':
 cap=json.loads(Path('reports/cara_budget_current_CPU_two_capture_r2_20261031.json').read_text())['result']
 base=cap['registration'];names=['src/wcomr/cara_budget_supervisor_r1.py','tests/test_cara_budget_context_readiness_r1.py','scripts/check_cara_budget_readiness_cpu_r1.py']
 raw={name:subprocess.check_output(['git','show',revision+':'+name]) for name in names}
 assert all(Path(name).read_bytes()==data for name,data in raw.items())
 hashes={**base['payload_sha256'],**{n:hashlib.sha256(b).hexdigest() for n,b in raw.items()}}
 payload.update(base_stage=cap['launch']['stage'],base_registration_sha256=cap['registration_sha256'],parent_git_revision=revision,
  expected_host_config=HOST_CONFIG,minimum_available_memory_GiB=8,files={n:base64.b64encode(b).decode() for n,b in raw.items()},
  overlay_sha256={n:hashlib.sha256(b).hexdigest() for n,b in raw.items()},full_mapping_sha256=hashlib.sha256(json.dumps(hashes,sort_keys=True,separators=(',',':')).encode()).hexdigest())
 wrapper="""import json,sys,hashlib,io
from pathlib import Path
p=json.load(sys.stdin)
if p['action']=='prepare':
 b=Path(p['base_stage'])/'registration.json';assert hashlib.sha256(b.read_bytes()).hexdigest()==p['base_registration_sha256']
 p['hashes']={**json.loads(b.read_text())['payload_sha256'],**p.pop('overlay_sha256')}
 assert hashlib.sha256(json.dumps(p['hashes'],sort_keys=True,separators=(',',':')).encode()).hexdigest()==p.pop('full_mapping_sha256')
sys.stdin=io.StringIO(json.dumps(p))
"""
 remote=wrapper+'\nexec('+repr(remote)+')\n'
binding=dict(action=action,host='two_card',stage=stage,started_unix=time.time(),source_revision=revision,
 remote_code_sha256=hashlib.sha256(remote.encode()).hexdigest(),local_transport_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 payload_sha256=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest(),GPU_submissions=0,work_seconds=2400,exit_seconds=60)
with output.with_name(output.stem+'_binding.json').open('x') as f:json.dump(binding,f,indent=2);f.write('\n')
secret=password();command="sudo -S -p '' -u gaokuangda -g docker /home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -c "+shlex.quote(remote)
cmd=['ssh','-F','.sync/cara-fast-mainline-tailscale-20261030/ssh_config.budget_direct.private','-o','BatchMode=yes','-o','ConnectTimeout=35','-o','ServerAliveInterval=5','-o','ServerAliveCountMax=2','two_card_lan',command]
child=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
try:out,err=child.communicate((secret+'\n'+json.dumps(payload)).encode(),timeout=100)
except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGTERM);out,err=child.communicate()
row=dict(binding,observed_unix=time.time(),exit_code=child.returncode,stderr=err.decode(errors='replace').replace(secret,'[REDACTED]'),result=json.loads(out) if child.returncode==0 else None,recovery_only_on_unknown=True)
with output.open('x') as f:json.dump(row,f,indent=2);f.write('\n')
print(json.dumps(dict(output=str(output),exit_code=child.returncode,result_status=(row['result'] or {}).get('status'))))
