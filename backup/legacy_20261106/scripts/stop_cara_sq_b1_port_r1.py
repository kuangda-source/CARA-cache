"""Stop only this owned CPU copy after a verified transport bottleneck.

The original source, complete files, partial files, process costs and wall-time
envelope are retained. This has no GPU, model or shared-ledger operation.
"""
import argparse
import hashlib
import json
from pathlib import Path

from cara_sq_b1_port_cpu_r1 import STAGE
from cara_two_card_transport_r1 import four_ssh,ssh


STOP=r'''
import hashlib,json,os,pathlib,signal,sys,time
p=json.load(sys.stdin);L=p['launch'];s=pathlib.Path(L['stage']);project=pathlib.Path('/data20t/gaokuangda/worldcache_workspace')
sys.path.insert(0,str(project/'.sync/cara-sq-q1-saved-four-card-r1-20261028/src'))
from wcomr.gpu_budget_pool_v2 import atomic_json,process_identity,same_live_process
assert s==pathlib.Path('/home/user/cara_sq_b1_port_cpu_r1_20261029')
assert json.loads((s/'launch.json').read_text())==L
if (s/'operator-stop.json').exists():print((s/'operator-stop.json').read_text());sys.exit(0)
assert hashlib.sha256((s/'registration.json').read_bytes()).hexdigest()==L['registration_sha256']
reg=json.loads((s/'registration.json').read_text());assert all(hashlib.sha256((s/n).read_bytes()).hexdigest()==v for n,v in reg['payload_sha256'].items())
assert not (s/'result.json').exists(),'Original CPU copy already completed; accept it without a switch'
w=json.loads((s/'worker.json').read_text());ids=[L['identity'],w['identity']]
snap=[]
for identity in ids:
 q=pathlib.Path('/proc')/str(identity['pid']);snap.append(dict(identity=process_identity(identity['pid']),stat=(q/'stat').read_text() if q.exists() else None,io=(q/'io').read_text() if q.exists() else None))
if same_live_process(L['identity']):
 pid=L['identity']['pid'];assert os.getpgid(pid)==pid and (pathlib.Path('/proc')/str(pid)).stat().st_uid==os.getuid()
 assert same_live_process(w['identity']) and os.getpgid(w['identity']['pid'])==pid
 os.killpg(pid,signal.SIGTERM);until=time.monotonic()+10
 while time.monotonic()<until and any(same_live_process(i) for i in ids):time.sleep(.1)
 if any(same_live_process(i) for i in ids):
  assert same_live_process(L['identity']) and os.getpgid(pid)==pid
  os.killpg(pid,signal.SIGKILL)
assert not any(same_live_process(i) for i in ids),'Recover original CPU processes before continuation'
progress=json.loads((s/'progress.json').read_text()) if (s/'progress.json').exists() else None
folder=project/'outputs/cara-ig-b1-r2-20261027/assets/.sq-b1-port-cpu-r1-20261029'
partials=[dict(name=f.name,bytes=f.stat().st_size) for f in folder.iterdir()] if folder.exists() else []
value=dict(status='B1_R1_OWNED_CPU_TRANSPORT_OPERATOR_STOPPED',launch=L,stopped_unix=time.time(),wall_seconds=time.time()-L['started_unix'],reason='Verified bounded32 SFTP read has byte-identical prefix and >3x throughput; no model/GPU scope change',diagnostic_ref=p['diagnostic_ref'],diagnostic_sha256=p['diagnostic_sha256'],process_snapshots_before_stop=snap,source_server=w['source_server'],original_payload_intact=True,original_destination_handles_live=False,last_progress=progress,unverified_partials_retained=partials,original_deadline_unix=L['started_unix']+7200,GPU_submissions=0,ledger_writes=0)
atomic_json(s/'operator-stop.json',value);print(json.dumps(value))
'''

RELEASE=r'''
import json,os,pathlib,signal,sys,time
p=json.load(sys.stdin);sys.path.insert(0,'/data20t/gaokuangda/worldcache_workspace/.sync/cara-sq-q1-saved-two-card-r1-20261028/src')
from wcomr.gpu_budget_pool_v2 import process_identity,same_live_process
identity=p['identity'];until=time.monotonic()+5
while same_live_process(identity) and time.monotonic()<until:time.sleep(.1)
signaled=False
if same_live_process(identity):
 actual=process_identity(identity['pid']);assert actual['command'].strip()=='/usr/lib/openssh/sftp-server -R'
 assert (pathlib.Path('/proc')/str(identity['pid'])).stat().st_uid==os.getuid()
 os.kill(identity['pid'],signal.SIGTERM);signaled=True;until=time.monotonic()+5
 while same_live_process(identity) and time.monotonic()<until:time.sleep(.1)
assert not same_live_process(identity),'Recover the original source CPU file server first'
print(json.dumps(dict(status='B1_R1_SOURCE_CPU_HANDLE_RELEASE_VERIFIED',observed_unix=time.time(),identity=identity,original_source_live=False,own_source_signaled=signaled,GPU_submissions=0,ledger_writes=0)))
'''


def main():
    p=argparse.ArgumentParser();p.add_argument('--launch-ref',type=Path,required=True)
    p.add_argument('--diagnostic',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--source-output',type=Path,required=True);args=p.parse_args()
    if args.output.exists() or args.source_output.exists():raise FileExistsError('Preserve original CPU switch evidence')
    launch=json.loads(args.launch_ref.read_text());diagnostic=json.loads(args.diagnostic.read_text())
    if (launch['stage']!=STAGE or diagnostic['status']!='B1_SFTP_BOUNDED_TRANSPORT_DIAGNOSTIC_ONLY'
            or diagnostic['ratio']<3 or len(diagnostic['rows'])!=2
            or diagnostic['rows'][0]['sha256']!=diagnostic['rows'][1]['sha256']):
        raise ValueError('A measured byte-identical transport benefit and original own CPU handle are required')
    value=four_ssh(STOP,dict(launch=launch,diagnostic_ref=str(args.diagnostic),
        diagnostic_sha256=hashlib.sha256(args.diagnostic.read_bytes()).hexdigest()))
    with args.output.open('x') as f:json.dump(value,f,indent=2);f.write('\n')
    released=ssh(RELEASE,dict(identity=value['source_server']),docker_group=True)
    with args.source_output.open('x') as f:json.dump(released,f,indent=2);f.write('\n')
    print(json.dumps(dict(status=value['status'],source_release=released['status'],retained_partials=value['unverified_partials_retained'],original_deadline_unix=value['original_deadline_unix'])))


if __name__=='__main__':main()
