"""Read only exact score identities and status; never return partial values."""
import argparse
import json
from pathlib import Path
from cara_two_card_transport_r1 import ssh

SUMMARY = r'''
import re
from collections import Counter
def summarize(progress, names):
    rows = progress['rows']
    assert len(rows) == 288
    exact = {int(n[:-5]) for n in names if re.fullmatch(r'(0|[1-9][0-9]*)\.json', n)}
    assert all(0 <= n < 288 for n in exact)
    scored = {i for i, r in enumerate(rows) if r['status'] == 'SCORED'}
    assert scored <= exact
    return dict(status=progress['status'], registered_positions=288,
        accepted_files=len(exact), scored_positions=len(scored),
        pending_status_commit=len(exact-scored),
        counts=dict(Counter(r['status'] for r in rows)),
        dimensions={d:dict(Counter(r['status'] for r in rows if r['planned']['dimension']==d))
            for d in ('MUSIQ_LONGER512','subject_consistency','motion_smoothness')},
        model_lifecycle=progress['model_lifecycle'], started_unix=progress['started_unix'])
def lpips_summary(progress):
    return {k:progress[k] for k in ('status','planned_pairs','completed_pairs','started_unix','ended_unix') if k in progress}
'''
REMOTE = SUMMARY + r'''
import pathlib,json,sys,time,os
L=json.load(sys.stdin);s=pathlib.Path(L['stage']);o=pathlib.Path(L['project'])/'outputs'/L['run_id']
assert json.loads((s/'pg-GPU-launch.json').read_text())==L
sys.path.insert(0,str(s/'src'))
from wcomr.gpu_budget_pool_v2 import same_live_process
from wcomr.history104_storage_r2 import storage_for
sup=json.loads((o/'supervisor.json').read_text())
quality=summarize(json.loads((o/'quality-progress.json').read_text()),[p.name for p in (o/'quality').iterdir()])
v=dict(observed_unix=time.time(),launch_id=L['launch_id'],quality=quality,
    post_identity=sup['post_identity'],post_live=same_live_process(sup['post_identity']),
    runner_live=same_live_process(sup['child_identity']),supervisor_live=same_live_process(sup['supervisor_identity']),
    LPIPS=lpips_summary(json.loads((o/'score-progress.json').read_text())),storage=storage_for(s).check(),
    post_exit_exists=(o/'post-exit.json').exists(),scientific_values_returned=False)
if v['post_live']:v['post_affinity']=sorted(os.sched_getaffinity(sup['post_identity']['pid']))
if v['post_exit_exists']:v['post_exit']=json.loads((o/'post-exit.json').read_text())
print(json.dumps(v))
'''

def self_test():
    scope={};exec(SUMMARY,scope)
    rows=[dict(status='SCORED' if i<2 else 'NOT_REACHED',
        planned=dict(dimension=('MUSIQ_LONGER512','subject_consistency','motion_smoothness')[i%3]),
        result={'value':'MUST_NOT_ESCAPE'}) for i in range(288)]
    p=dict(status='QUALITY_RUNNING',rows=rows,model_lifecycle=[],started_unix=0)
    result=scope['summarize'](p,['0.json','0.raw.json','1.json','1.raw.json','plan.json','2.raw.json'])
    assert result['accepted_files']==result['scored_positions']==2
    assert 'MUST_NOT_ESCAPE' not in json.dumps(result)
    assert 'MUST_NOT_ESCAPE' not in json.dumps(scope['lpips_summary']({'status':'CPU_SCORE_COMPLETE80','completed_pairs':80,'scores':{'x':{'LPIPS':'MUST_NOT_ESCAPE'}}}))
    result=scope['summarize'](p,['0.json','1.json','2.json','2.raw.json'])
    assert result['pending_status_commit']==1
    try:scope['summarize'](p,['0.json','1.json','288.json'])
    except AssertionError:pass
    else:raise AssertionError('Out-of-scope accepted filename was admitted')
    return dict(passed=True,checks=['raw_excluded','quality_values_excluded','LPIPS_values_excluded','atomic_write_gap','out_of_scope_rejected'])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--launch-ref',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--self-test',action='store_true');a=p.parse_args()
    assert not a.output.exists()
    v=self_test() if a.self_test else ssh(REMOTE,json.loads(a.launch_ref.read_text()),docker_group=True)
    a.output.write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
