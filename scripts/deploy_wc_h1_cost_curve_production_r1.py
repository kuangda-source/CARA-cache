"""Prepare isolated full60 production CPU; explicit later serial GPU dispatch."""
import argparse
import base64
import hashlib
import io
import json
import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER = '/home/gaokuangda/data/gkd/worldcache_omr'
HOST = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
        '-o', 'ClearAllForwardings=yes', 'gkd_minchen']
BASE = SERVER + '/.sync/wc-h1-cost-curve-cpu-r1-20261013'
OLD = SERVER + '/.sync/wc-source-phase-h1-production-r2-20261013'
CONFIG = 'configs/wc_h1_cost_curve_full60_production_r1_20261013.json'
NEW = [CONFIG, 'src/wcomr/h1_cost_curve_production_r1.py',
       'src/wcomr/h1_cost_curve_post_r1.py', 'tests/check_h1_cost_curve_production_cpu_r1.py',
       'scripts/run_wc_h1_cost_curve_r1.py', 'scripts/supervise_wc_h1_cost_curve_r1.py',
       'scripts/postprocess_wc_h1_cost_curve_cpu_r1.py', 'scripts/watch_wc_h1_cost_curve_cpu_r1.py',
       'scripts/deploy_wc_h1_cost_curve_production_r1.py',
       'configs/wc_source_phase_h1_full24_production_r1_20261013.json']
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def remote(code):
    compile(code, 'cost-curve-production-remote', 'exec')
    return subprocess.check_output(HOST + ['python3 -'], input=code, text=True, timeout=120)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--launch', action='store_true')
    p.add_argument('--suffix', choices=('r1', 'r2', 'r3'), default='r1')
    a = p.parse_args()
    stage = SERVER + '/.sync/wc-h1-cost-curve-production-' + a.suffix + '-20261013'
    c = json.loads((ROOT / CONFIG).read_text())
    old = json.loads((ROOT / NEW[-1]).read_text())
    names = NEW + [c['cost_ref'], c['middle_baseline_ref']]
    names += [old[k + '_ref'] for k in ('authority', 'cost', 'baseline', 'previous_parameters')]
    names += [x['ref'] for x in old['table_parameters'].values()]
    names = list(dict.fromkeys(names))
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    packet = dict(source_revision=revision, new_payload_sha256={n: sha(ROOT/n) for n in names})
    for n, digest in packet['new_payload_sha256'].items():
        assert hashlib.sha256(subprocess.check_output(['git','show',revision+':'+n],cwd=ROOT)).hexdigest() == digest
    if not a.launch:
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode='w:gz') as archive:
            for name in names: archive.add(ROOT/name, arcname=name)
        code = ('P='+repr(packet)+'\nBASE='+repr(BASE)+'\nOLD='+repr(OLD)+'\nSTAGE='+repr(stage)
                +'\nROOT='+repr(SERVER)+'\nARCHIVE='+repr(base64.b64encode(buffer.getvalue()).decode())+'\n') + r'''
import pathlib,json,hashlib,shutil,subprocess,os,time,base64,io,tarfile,sys
base=pathlib.Path(BASE);old=pathlib.Path(OLD);stage=pathlib.Path(STAGE);root=pathlib.Path(ROOT)
if (stage/'production-CPU-launch.json').exists():
 reg=json.loads((stage/'registration.json').read_text())
 assert reg['new_payload_sha256']==P['new_payload_sha256'], 'Existing immutable CPU source differs'
 print((stage/'production-CPU-launch.json').read_text());sys.exit(0)
assert not (stage/'production-CPU.log').exists(), 'Unknown original CPU handle; no duplicate'
proof=json.loads((base/'CPU-result.json').read_text());reg=json.loads((base/'registration.json').read_text())
assert proof['status']=='H1_COST_CURVE_TWO_FLOW_ALL160_CPU_PASS_NOT_GPU'
assert proof['actual_CPU_paths']==160 and not proof['CUDA_initialized'] and proof['GPU_submissions']==0
assert reg['source_revision']=='055b55755dbc0c745fd2fa2da2a69c82476f71e4'
assert proof['payload_sha256']==reg['payload_sha256']
old_cpu=json.loads((old/'production-CPU-result.json').read_text())
assert old_cpu['status']=='SOURCE_PHASE_H1_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU' and old_cpu['exit_code']==0
stage.mkdir(exist_ok=True)
def store(path,data):
 path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists():assert path.read_bytes()==data
 else:path.write_bytes(data)
for name,digest in reg['payload_sha256'].items():
 source=base/name;assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
 store(stage/name,source.read_bytes())
for source,target in [(base/'CPU-result.json','curve-sampling-CPU-result.json'),
                      (base/'registration.json','curve-sampling-CPU-registration.json'),
                      (old/'sampling-CPU-result.json','sampling-CPU-result.json'),
                      (old/'sampling-CPU-registration.json','sampling-CPU-registration.json'),
                      (old/'production-CPU-result.json','old36-production-CPU-result.json')]:
 store(stage/target,source.read_bytes())
with tarfile.open(fileobj=io.BytesIO(base64.b64decode(ARCHIVE)),mode='r:gz') as archive:
 for member in archive.getmembers():
  assert member.isfile() and member.name in P['new_payload_sha256']
  data=archive.extractfile(member).read()
  assert hashlib.sha256(data).hexdigest()==P['new_payload_sha256'][member.name]
  store(stage/member.name,data)
payload=dict(reg['payload_sha256'])
for name,digest in P['new_payload_sha256'].items():
 if name in payload:assert payload[name]==digest
 assert hashlib.sha256((stage/name).read_bytes()).hexdigest()==digest
 payload[name]=digest
final={'source_revision':P['source_revision'],'payload_sha256':payload,
       'new_payload_sha256':P['new_payload_sha256'],'runtime_source_sha256':reg['runtime_source_sha256'],
       'base_source_revision':reg['source_revision'],'CPU_only_dispatch':True,'GPU_execution_selected':False}
store(stage/'registration.json',(json.dumps(final,indent=2)+'\n').encode())
command=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python','-u',
 str(stage/'scripts/run_wc_h1_cost_curve_r1.py'),'--project',str(root),'--stage',str(stage),'--cpu-check']
with (stage/'production-CPU.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
  env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2'))
receipt={'status':'H1_COST_CURVE_FULL60_PRODUCTION_CPU_STARTED_NOT_GPU','CPU_pid':child.pid,
 'source_revision':P['source_revision'],'stage':str(stage),'command':command,'started_unix':time.time(),
 'payload_files':len(payload),'expected_actual_sampling_CPU_paths':160,'GPU_submissions':0,
 'ledger_written':False,'inflight_confirmation_not_inspected_or_modified':True}
store(stage/'production-CPU-launch.json',(json.dumps(receipt,indent=2)+'\n').encode())
print(json.dumps(receipt))
'''
        receipt = json.loads(remote(code))
        (ROOT/'reports'/('wc_h1_cost_curve_production_'+a.suffix+'_CPU_launch_20261013.json')).write_text(json.dumps(receipt,indent=2)+'\n')
        print(json.dumps(receipt)); return
    code = ('P='+repr(packet)+'\nSTAGE='+repr(stage)+'\nROOT='+repr(SERVER)+'\nCONFIG='+repr(CONFIG)+'\n') + r'''
import pathlib,json,hashlib,subprocess,os,time
stage=pathlib.Path(STAGE);root=pathlib.Path(ROOT)
proof=json.loads((stage/'production-CPU-result.json').read_text());reg=json.loads((stage/'registration.json').read_text())
assert proof['status']=='H1_COST_CURVE_FULL60_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU' and proof['exit_code']==0
assert proof['post_tests']['all60_slots_40_formal_20_warm']
assert proof['registration_sha256']==hashlib.sha256((stage/'registration.json').read_bytes()).hexdigest()
assert reg['new_payload_sha256']==P['new_payload_sha256']
for name,digest in reg['payload_sha256'].items():assert hashlib.sha256((stage/name).read_bytes()).hexdigest()==digest
assert not (stage/'GPU-launch.json').exists()
c=json.loads((stage/CONFIG).read_text());assert not (root/'outputs'/c['run_id']).exists()
# The supervisor verifies the finished CONF/post, fresh kernel lock/UUID and
# ledger. Dispatch cannot bypass it or convert a live reservation into spend.
command=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python','-u',
 str(stage/'scripts/supervise_wc_h1_cost_curve_r1.py'),'--project',str(root),'--stage',str(stage),
 '--source-revision',reg['source_revision']]
with (stage/'GPU-supervisor.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
  env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
post_command=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python','-u',
 str(stage/'scripts/watch_wc_h1_cost_curve_cpu_r1.py'),'--project',str(root),'--stage',str(stage),
 '--supervisor-pid',str(child.pid)]
with (stage/'post-watcher.log').open('x') as log:
 post=subprocess.Popen(post_command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
  env=dict(os.environ,CUDA_VISIBLE_DEVICES=''))
receipt={'status':'H1_COST_CURVE_FULL60_DISPATCHED_ADMISSION_PENDING','supervisor_pid':child.pid,
 'post_watcher_pid':post.pid,'stage':str(stage),'source_revision':reg['source_revision'],
 'command':command,'post_command':post_command,'started_unix':time.time(),'run_id':c['run_id']}
(stage/'GPU-launch.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
'''
    receipt=json.loads(remote(code))
    (ROOT/'reports'/('wc_h1_cost_curve_production_'+a.suffix+'_GPU_launch_20261013.json')).write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))


if __name__ == '__main__': main()
