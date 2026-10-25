"""New A6000 stage and full affected CPU entry. Never launches a GPU task."""
import argparse
import ast
import base64
import hashlib
import json
import re
from pathlib import Path
import subprocess
import sys
from cara_two_card_transport_r1 import ssh
from cara_cal66_a6000_profile_r1 import adapt, STAGE, RUN, VERSION, QUOTE
from wc_four_card_resource_cpu_r4 import write

ROOT = Path(__file__).resolve().parents[1]
REMOTE = '/data20t/gaokuangda/worldcache_workspace'
ADAPTED = ['src/wcomr/policy_generator_r1/shared66_card.py', 'scripts/run_cara_shared66_r1.py',
           'src/wcomr/gpu_budget_pool_v2.py', 'tests/check_cara_shared66_lifecycle_cpu_r1.py',
           'tests/check_shared66_storage_cpu_r1.py']
EXTRA = ['scripts/check_cara_cal66_a6000_cpu_r1.py', 'scripts/cara_cal66_a6000_profile_r1.py',
         'tests/test_cara_cal66_a6000_profile_r1.py', 'scripts/check_cara_cal66_entry_cpu_r2.py',
         'tests/check_cara_cal66_sampling_cpu_r2.py', 'tests/test_cara_pg_p2_production_batch.py',
         'scripts/check_wc_policy_price_refresh_cpu_r1.py', QUOTE]


def cpu_source_names():
    """Include literal dynamic sibling loaders as well as ordinary imports."""
    from wcomr.immutable_stage_payload_r1 import local_python_closure
    names=set(ADAPTED+EXTRA)
    while True:
        old=set(names)
        names.update(local_python_closure(ROOT,[n for n in names if n.endswith('.py')]))
        for name in list(names):
            if not name.endswith('.py'):continue
            for node in ast.walk(ast.parse((ROOT/name).read_text())):
                if isinstance(node,ast.Constant) and isinstance(node.value,str):
                    value=node.value
                    if re.fullmatch(r'[A-Za-z_]\w*(?:\.py)?',value):
                        sibling=Path(name).parent/(value if value.endswith('.py') else value+'.py')
                        if (ROOT/sibling).is_file():names.add(str(sibling))
        if old==names:return names

PREPARE = r'''
import pathlib,sys,json,base64,hashlib,subprocess,time,os,shutil
p=json.load(sys.stdin);root=pathlib.Path(p['root']);base=root/'.sync/cara-shared66-full-ada-r2-20261025';stage=root/'.sync'/p['stage_name']
assert not stage.exists(),'Existing stage must be recovered, never recreated'
read=lambda f:json.loads(pathlib.Path(f).read_text())
sha=lambda f:hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest()
original=read(base/'registration.json');assert sha(base/'registration.json')==p['base_registration_sha256']
assert all(sha(base/n)==h for n,h in original['payload_sha256'].items())
assert all(sha(root/'runtime'/n)==h for n,h in original['runtime_source_sha256'].items())
stage.mkdir(mode=0o700);names=set(original['payload_sha256'])
# A parent execution's proof is historical input, never the new output path.
# It remains intact in the mirrored parent and the failed first CPU stage.
names.difference_update({'shared66-recovery-CPU.json','pg-independent-CPU-acceptance.json'})
for n in names:
 target=stage/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(base/n,target)
for n,raw in p['files'].items():
 data=base64.b64decode(raw);assert hashlib.sha256(data).hexdigest()==p['hashes'][n]
 target=stage/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data);names.add(n)
# Copy the unchanged, source/weight-bound quality packet explicitly.
shutil.copyfile(base/'quality-binding.json',stage/'quality-binding.json');names.add('quality-binding.json')
sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
from wcomr.policy_generator_r1.shared66_card import RUN,VERSION,COUNTS,MANIFEST,execution_quote
card=read(stage/MANIFEST);q=execution_quote(card)
c=dict(version=VERSION,run_id=RUN,scope_counts=COUNTS,matrix=card['matrix'],forecast_complete_GPUh=q['forecast_GPUh'],billed_limit_GPUh=8.0,storage_contract_required=True,thermal_telemetry_required=True)
for n,v in [('pg-config.json',c),('pg-whole-quote.json',q),('a6000-adaptation.json',p['adaptation'])]:
 (stage/n).write_text(json.dumps(v,indent=2)+'\n');names.add(n)
# No old acceptance is permission to clear this new host.
names.discard('pg-independent-CPU-acceptance.json');(stage/'pg-independent-CPU-acceptance.json').unlink(missing_ok=True)
# A fresh run-specific storage contract is supplied by the scoped provisioner.
storage=read(root/'.sync/storage-reservations/cal66-a6000-r1/provision.json')['storage_contract']
assert storage['run_id']==RUN
(stage/'history104-storage.json').write_text(json.dumps(storage,indent=2)+'\n');names.add('history104-storage.json')
reg=dict(original,namespace=VERSION,stage=str(stage),source_revision=p['revision'],payload_sha256={n:sha(stage/n) for n in sorted(names)},host_adaptation=p['adaptation'],parent_registration_sha256=p['base_registration_sha256'])
(stage/'registration.json').write_text(json.dumps(reg,indent=2)+'\n')
from wcomr.policy_generator_r1.shared66_card import validate
validate(root,stage)
bank=root/'.sync/wc-bank24-fourcard-full-execution-r3-20261022';sys.path.insert(0,str(bank))
from four_card_bank24_execution_tools_r1 import process_environment
from four_card_policy_assets_port_r1 import container_command
command=container_command(root,stage,'cpu-worker',sha(stage/'registration.json'),process_environment(root,stage/'CPU-caches'),os.getuid(),os.getgid())
command[command.index('--cpus')+1]='2';command[command.index('--memory')+1]='8g'
at=command.index('--entrypoint');command[at:at]=['--tmpfs','/fault:rw,size=64m,mode=1777','--tmpfs','/fixture:rw,size=256m,mode=1777']
old=str(stage/'scripts/wc_policy_interval_assets_lifecycle_r1.py');i=command.index(old)
command=command[:i]+[str(stage/'scripts/check_cara_cal66_a6000_cpu_r1.py'),'--project',str(root),'--stage',str(stage),'--output',str(stage/'shared66-recovery-CPU.json')]
(stage/'CPU-command.json').write_text(json.dumps(command))
with (stage/'CPU.log').open('x') as log:
 child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
stat=pathlib.Path('/proc/%d/stat'%child.pid).read_text().rsplit(')',1)[1].split()
v=dict(status='CAL66_A6000_CPU_COMBINATION_LAUNCHED_NOT_GPU',project=str(root),stage=str(stage),source_revision=p['revision'],registration_sha256=sha(stage/'registration.json'),container=stage.name+'-cpu',identity=dict(pid=child.pid,start_ticks=int(stat[19])),started_unix=time.time(),GPU_submissions=0,ledger_written=False)
(stage/'A6000-CPU-launch.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
'''

CAPTURE = r'''
import pathlib,sys,json,subprocess,time,hashlib
L=json.load(sys.stdin);s=pathlib.Path(L['stage'])
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
reg=read(s/'registration.json');assert sha(s/'registration.json')==L['registration_sha256']
r=subprocess.run(['docker','inspect',L['container']],capture_output=True,text=True,timeout=20)
con=json.loads(r.stdout)[0] if r.returncode==0 else None
proof=s/'shared66-recovery-CPU.json'
v=dict(status='CAL66_A6000_ORIGINAL_CPU_CAPTURE',observed_unix=time.time(),launch=L,registration=reg,registration_sha256=sha(s/'registration.json'),payload_actual_sha256={n:sha(s/n) for n in reg['payload_sha256']},runtime_actual_sha256={n:sha(pathlib.Path(L['project'])/'runtime'/n) for n in reg['runtime_source_sha256']},container=con,proof=read(proof) if proof.exists() else None,proof_sha256=sha(proof) if proof.exists() else None,log_tail=(s/'CPU.log').read_text(errors='replace')[-14000:],GPU_submissions=0)
print(json.dumps(v))
'''


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','capture'])
    p.add_argument('--launch-ref',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists()
    if a.command=='capture':v=ssh(CAPTURE,json.loads(a.launch_ref.read_text()),docker_group=True)
    else:
        rev=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        files={};hashes={};evidence=[]
        sys.path.insert(0,str(ROOT/'src'))
        from wcomr.immutable_stage_payload_r1 import local_python_closure
        names=cpu_source_names()
        for n in sorted(names):
            raw=(ROOT/n).read_bytes()
            assert subprocess.check_output(['git','show',rev+':'+n],cwd=ROOT)==raw,'Commit exact source first'
            if n in ADAPTED:
                text,proof=adapt(n,raw.decode());raw=text.encode();evidence.append(proof)
            files[n]=base64.b64encode(raw).decode();hashes[n]=hashlib.sha256(raw).hexdigest()
        v=ssh(PREPARE,dict(root=REMOTE,stage_name=STAGE,revision=rev,files=files,hashes=hashes,adaptation=evidence,base_registration_sha256='48193714a15f219b33fd62a6f929ee8e7a5c17b1b6c3dfd9c7615318318c7561'),docker_group=True)
    write(a.output,v);print(json.dumps({k:v.get(k) for k in ('status','stage','started_unix','proof_sha256')}))


if __name__=='__main__':main()
