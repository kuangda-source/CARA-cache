"""Read-only live identity, monitor-prefix and cross-disk storage check."""
import argparse,json
from pathlib import Path
from cara_two_card_transport_r1 import ssh
from wc_four_card_resource_cpu_r4 import write

REMOTE=r'''
import pathlib,json,sys,time,hashlib
L=json.load(sys.stdin);s=pathlib.Path(L['stage']);root=pathlib.Path(L['project']);o=root/'outputs'/L['run_id']
assert json.loads((s/'pg-GPU-launch.json').read_text())==L
sys.path[:0]=[str(s/'src'),str(s/'scripts')]
from wcomr.history104_storage_r2 import storage_for
from wcomr.policy_generator_r1.production_exclusive import verify,observe
from wcomr.policy_asset_price_review_r1 import exclusive_gate
from wcomr.gpu_budget_pool_v2 import same_live_process
sup=json.loads((o/'supervisor.json').read_text());runner=sup['child_identity'];snap=observe(L['gpu_uuid'])
live=same_live_process(runner)
if live:verify(snap,L['gpu_uuid'],runner)
raw=(o/'exclusive-monitor.jsonl').read_bytes();lines=raw.splitlines(keepends=True)
partial_tail=bool(lines and not lines[-1].endswith(b'\n'))
rows=[json.loads(x) for x in (lines[:-1] if partial_tail else lines) if x.strip()];bad=[]
for i,r in enumerate(rows):
 active=bool(r['snapshot']['compute_apps'])
 kw=dict(gpu_uuid=L['gpu_uuid'],phase='active' if active else 'idle',now=r['snapshot']['observed_unix'])
 if active:kw['runner']=runner
 result=exclusive_gate(r['snapshot'],**kw)
 if not result['observation_passed']:bad.append(dict(index=i,result=result))
gaps=[b['monotonic_elapsed']-a['monotonic_elapsed'] for a,b in zip(rows,rows[1:])]
g=storage_for(s);check=g.check();telemetry=g.journal.read('telemetry')
assert telemetry['launch_id']==L['launch_id'] and telemetry['run_id']==L['run_id'] and telemetry['runner']==runner
age=time.time()-telemetry['sample']['snapshot']['observed_unix']
if live:assert 0<=age<=45
print(json.dumps(dict(status='CAL66_A6000_TECHNICAL_READONLY',observed_unix=time.time(),launch_id=L['launch_id'],source_revision=L['source_revision'],gpu_uuid=L['gpu_uuid'],runner=runner,runner_live=live,supervisor=sup['supervisor_identity'],current_GPU=snap,monitor_prefix_samples=len(rows),maximum_interval_seconds=max(gaps,default=0),violations=bad,monitor_prefix_sha256=hashlib.sha256(raw).hexdigest(),incomplete_tail=partial_tail,storage=check,storage_contract=g.config,cross_disk_telemetry_age_seconds=age,health=json.loads((o/'runner-health.json').read_text()),actual_unique_runner_accepted=live,complete_terminal_accepted=False)))
'''

def main():
    p=argparse.ArgumentParser();p.add_argument('--launch-ref',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists()
    v=ssh(REMOTE,json.loads(a.launch_ref.read_text()),docker_group=True);write(a.output,v)
    print(json.dumps({k:v[k] for k in ('status','health','runner_live','monitor_prefix_samples','maximum_interval_seconds','violations','storage','cross_disk_telemetry_age_seconds')}))

if __name__=='__main__':main()
