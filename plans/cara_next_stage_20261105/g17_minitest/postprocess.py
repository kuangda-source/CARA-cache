"""CPU-only post-release LPIPS and paired descriptive intervals. No dispatch."""
import argparse
import itertools
import json
import math
import os
from pathlib import Path
import statistics
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))


def interval(values):
    n=len(values)
    means=sorted(sum(values[i] for i in ix)/n for ix in itertools.product(range(n),repeat=n))
    def quantile(p):
        x=p*(len(means)-1);lo=math.floor(x);hi=math.ceil(x)
        return means[lo]+(x-lo)*(means[hi]-means[lo])
    return [quantile(.025),quantile(.975)]


def summarize(card,rows):
    indexed={(r['slot']['member'],r['slot']['role']):r for r in rows}
    for member,old in card['historical_F19_A1'].items():
        indexed[member,'F19_A1_HISTORY']=dict(Alex=old['result']['Alex'],T_DD=None)
    effects=[]
    for contrast in card['contrasts']:
        pairs=[dict(member=m,delta_Alex=indexed[m,contrast['candidate']]['Alex']-indexed[m,contrast['reference']]['Alex'],
            delta_T_DD=None if contrast['reference']=='F19_A1_HISTORY' else indexed[m,contrast['candidate']]['T_DD']-indexed[m,contrast['reference']]['T_DD']) for m in contrast['members']]
        values=[p['delta_Alex'] for p in pairs]
        effects.append(dict(**contrast,mean_delta=statistics.mean(values),CI95=interval(values),
            improved=sum(v<0 for v in values),equal=sum(v==0 for v in values),n=len(values),per_input=pairs,
            mean_delta_T_DD=None if contrast['reference']=='F19_A1_HISTORY' else statistics.mean(p['delta_T_DD'] for p in pairs)))
    fast={role:statistics.mean(indexed[m,role]['T_DD'] for m in card['inputs_by_alias'].values())
        for role in ('G17','G17_TAIL','F17_A2_LIGHT_C')}
    return dict(contrasts=effects,mean_T_DD=fast,common_budget_seconds=132.98,
        within_common_budget={k:v<=132.98 for k,v in fast.items()},
        all_fixed_masks_matched=all(r['mask_matches'] for r in rows),
        CI_method='Exact paired-input bootstrap n^n ordered resamples, linear percentile95; descriptive only',
        noninferiority_test=False,position_overlap_gate=False)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('action',choices=('score','analyze'))
    for name in ('manifest','output'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('collection','capture','settlement','scores'):p.add_argument('--'+name,type=Path)
    args=p.parse_args();read=lambda path:json.loads(Path(path).read_text())
    from wcomr.gpu_budget_pool_v2 import atomic_json
    card=read(args.manifest)
    if args.action=='analyze':
        scores=read(args.scores)
        assert scores['status']=='COMPLETE_PENDING_ANALYSIS' and scores['scope_sha256']==card['scope_sha256']
        assert not args.output.exists(),'Recover existing analysis, do not replay'
        atomic_json(args.output,dict(status='COMPLETE',run_id=card['run_id'],scope_sha256=card['scope_sha256'],
            **summarize(card,scores['rows'])))
        sys.exit(0)
    from wcomr.cara_budget_lifecycle_r1 import released_lifecycle
    capture=read(args.capture);release=released_lifecycle(capture,capture['files']['launch']['sha256'],read(args.settlement))
    assert all(release[k] for k in ('GPU_released','mode_restored','cost_settled','original_processes_ended','container_exit_success'))
    collection=read(args.collection)
    launch=json.loads(capture['files']['launch']['raw_utf8'])
    assert launch['run_id']==card['run_id'] and launch['scope_sha256']==card['scope_sha256']
    assert collection['status']=='COMPLETE_PENDING_RELEASE_SCORING' and collection['scope_sha256']==card['scope_sha256']
    assert os.environ['CUDA_VISIBLE_DEVICES']=='' and os.environ['NVIDIA_VISIBLE_DEVICES']=='void'
    assert not args.output.exists(),'Recover the existing scoring output, do not replay'
    import torch,lpips
    from wcomr.cara_fast_fidelity_r1 import score_video_pair
    torch.set_num_threads(2);torch.set_num_interop_threads(1)
    def forbidden(*a,**kw):raise RuntimeError('CPU scorer forbids CUDA/downloads')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
    alex=lpips.LPIPS(net='alex',version='0.1',verbose=False).cpu().eval()
    state=dict(status='SCORING',scope_sha256=card['scope_sha256'],rows=[],release=release)
    atomic_json(args.output,state)
    for row in collection['rows']:
        slot=row['slot']
        if slot['section']=='warm':continue
        result=score_video_pair(row['result']['video_artifact'],card['native_references'][slot['member']]['video_artifact'],alex)
        actual=''.join(h['actual'] for h in row['result']['semantic_history'])
        matched=actual==''.join(card['roles'][slot['role']]['policy']['actions'])
        state['rows'].append(dict(slot=slot,Alex=result['Alex'],T_DD=row['result']['T_DD'],fidelity=result,mask_matches=matched))
        atomic_json(args.output,state)
    state.update(status='COMPLETE_PENDING_ANALYSIS',CUDA_initialized=torch.cuda.is_initialized())
    atomic_json(args.output,state)
