import sys,json,gzip,base64,hashlib,subprocess,shlex,os,signal,time
from pathlib import Path
sys.path[:0]=['scripts','src']
from cara_budget_calibration_cpu_hosts_r3 import REMOTE
from cara_two_card_transport_r1 import password
from wcomr.cara_budget_cpu_resources_r2 import HOST_CONFIG
REMOTE=REMOTE.replace("registration=reg,", "registration=None,")
payload=dict(action='capture',host='two_card',stage_name='cara-budget-dispatch-child-CPU-a6000-r1-20261031')
code="import io,sys,json,gzip,base64,hashlib\nsys.stdin=io.StringIO("+repr(json.dumps(payload))+")\noriginal_stdout=sys.stdout\nsys.stdout=io.StringIO()\nexec("+repr(REMOTE)+")\nraw=sys.stdout.getvalue().encode()\nsys.stdout=original_stdout\nprint(json.dumps(dict(gzip_base64=base64.b64encode(gzip.compress(raw)).decode(),raw_sha256=hashlib.sha256(raw).hexdigest())))\n"
secret=password()
command="sudo -S -p '' -u gaokuangda -g docker /home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -c "+shlex.quote('import sys;exec(sys.stdin.read())')
cmd=['ssh','-C','-F','.sync/cara-fast-mainline-tailscale-20261030/ssh_config.budget_direct.private','-o','BatchMode=yes','-o','ConnectTimeout=35','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=3','two_card_lan',command]
started=time.time();p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
try:out,err=p.communicate((secret+'\n'+code).encode(),timeout=100)
except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGTERM);out,err=p.communicate()
result=None
if p.returncode==0:
 wrapped=json.loads(out);raw=gzip.decompress(base64.b64decode(wrapped['gzip_base64']));assert hashlib.sha256(raw).hexdigest()==wrapped['raw_sha256'];result=json.loads(raw)
 base=json.loads(Path('reports/cara_budget_current_CPU_two_R4_capture_r4_20261031.json').read_text())['result']
 revision='978488c4c308c1604e109bf07260814c9b97c73d'
 names=['tests/check_cara_budget_dispatch_child_fixture_r1.py','tests/test_cara_budget_dispatch_child_r1.py','scripts/check_cara_budget_dispatch_child_cpu_r1.py']
 delta={n:hashlib.sha256(subprocess.check_output(['git','show',revision+':'+n])).hexdigest() for n in names}
 reg=dict(host='two_card',stage=result['launch']['stage'],payload_sha256={**base['registration']['payload_sha256'],**delta},runtime_source_sha256=base['registration']['runtime_source_sha256'],parent_git_revision=revision,source_identity='EXACT_PAYLOAD_SHA_WORKTREE_CPU_ONLY',expected_host_config=HOST_CONFIG,original_endpoint_stage=base['launch']['stage'],base_registration_sha256=base['registration_sha256'])
 assert hashlib.sha256((json.dumps(reg,indent=2)+'\n').encode()).hexdigest()==result['registration_sha256']
 result['registration']=reg
 result['registration_reconstructed_from_original_base_and_published_delta_verified_remote_SHA']=True
r=dict(action='capture',host='two_card',stage=payload['stage_name'],source_revision='978488c4c308c1604e109bf07260814c9b97c73d',started_unix=started,observed_unix=time.time(),exit_code=p.returncode,result=result,stderr=err.decode(errors='replace').replace(secret,'[REDACTED]'),remote_code_sha256=hashlib.sha256(code.encode()).hexdigest(),local_transport_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),transport='SSH_COMPRESSION_WITH_CODE_ON_STDIN',recovery_only_on_unknown=True,GPU_submissions=0)
output=Path(sys.argv[1])
with output.open('x') as stream:json.dump(r,stream,indent=2);stream.write('\n')
print(json.dumps(dict(exit_code=p.returncode,status=(result or {}).get('status'),state=(result or {}).get('container_state'),log_tail=(result or {}).get('log_tail'))))
