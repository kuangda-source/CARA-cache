import json,sys,subprocess,shlex,time,hashlib,os,signal
from pathlib import Path
sys.path.insert(0,'scripts')
from cara_two_card_transport_r1 import password
code='''import json,subprocess,hashlib,time
from pathlib import Path
s=Path('/data20t/gaokuangda/worldcache_workspace/.sync/cara-budget-calibration-CPU-a6000-r4-20261031');l=json.loads((s/'CPU-launch.json').read_text());c=json.loads(subprocess.check_output(['docker','inspect',l['container']]))[0]
def process(pid):
 p=Path('/proc')/str(pid)/'stat'
 try:
  raw=p.read_text();fields=raw[raw.rfind(')')+2:].split();return dict(pid=pid,state=fields[0],start_ticks=int(fields[19]))
 except (FileNotFoundError,ProcessLookupError):return dict(pid=pid,missing=True)
log=(s/'CPU.log').read_text(errors='replace')
print(json.dumps(dict(launch=l,container_id=c['Id'],container_state=c['State'],boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),pid_namespace_inode=Path('/proc/self/ns/pid').stat().st_ino,cli_process=process(l['pid']),worker_process=process(c['State']['Pid']) if c['State']['Pid'] else None,host_config={k:c['HostConfig'][k] for k in ('NanoCpus','Memory','MemorySwap','CpusetCpus','DeviceRequests','NetworkMode','ReadonlyRootfs')},registration_sha256=hashlib.sha256((s/'registration.json').read_bytes()).hexdigest(),proof_exists=(s/'CPU-proof.json').exists(),log_tail=log[-1500:],observed_unix=time.time(),GPU_submissions=0)))
'''
secret=password();cmd=['ssh','-F','.sync/cara-fast-mainline-tailscale-20261030/ssh_config.budget_direct.private','-o','BatchMode=yes','-o','ConnectTimeout=35','-o','ServerAliveInterval=5','-o','ServerAliveCountMax=2','two_card_lan',"sudo -S -p '' -u gaokuangda -g docker python3 -c "+shlex.quote(code)]
p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
try:out,err=p.communicate((secret+'\n').encode(),timeout=70)
except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGTERM);out,err=p.communicate()
r=dict(exit_code=p.returncode,stderr=err.decode().replace(secret,'[REDACTED]'),remote_code_sha256=hashlib.sha256(code.encode()).hexdigest(),result=json.loads(out) if p.returncode==0 else None)
path=Path(sys.argv[1])
with path.open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(r,indent=2))
