"""Full93 CPU LPIPS for new arms; frozen Native/R18C are reused unchanged."""
import argparse
import json
from pathlib import Path
import statistics
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
from wcomr.cara_sparse_refresh_probe_r1 import s1_gate


def summarize(card,rows,s1):
    gate=s1_gate(**s1)
    expected={(s['member'],s['role']) for s in card['matrix']}
    assert len(rows)==8 and {(r['slot']['member'],r['slot']['role']) for r in rows}==expected
    assert all(r['mask_matches'] and r['fidelity']['frames']==93 for r in rows)
    indexed={(r['slot']['member'],r['slot']['role']):r for r in rows}
    contrasts={}
    for role in ('b','c'):
        pairs=[]
        for ref in card['reused_R18C']:
            member=ref['slot']['member'];new=indexed[member,role]
            pairs.append(dict(member=member,delta_Alex=new['Alex']-ref['Alex'],delta_T_DD=new['T_DD']-ref['T_DD']))
        contrasts[role]=dict(per_input=pairs,mean_delta_Alex=statistics.mean(r['delta_Alex'] for r in pairs),
            mean_delta_T_DD=statistics.mean(r['delta_T_DD'] for r in pairs),improved=sum(r['delta_Alex']<0 for r in pairs))
    b,c=(contrasts[k] for k in ('b','c'))
    b_go=b['mean_delta_Alex']<0 and b['improved']>=3 and -b['mean_delta_Alex']>=.0044*max(0,b['mean_delta_T_DD'])
    c_go=c['mean_delta_T_DD']<=0 and c['improved']>=3 and c['mean_delta_Alex']<=0
    return dict(status='COMPLETE',run_id=card['run_id'],scope_sha256=card['scope_sha256'],contrasts=contrasts,
        S1=dict(measurements=s1,**gate),go=bool(gate['gate_passed'] and (b_go or c_go)),b_go=b_go,c_go=c_go,
        sync_raw_comparison='S1 local only; no raw endpoint arm or raw-endpoint closure decision',
        reused_R18C_scores=4,new_full93_pairs=8,posthoc_tuning=False,reruns=0,
        limitation='Exposed four-input development probe; cross-run R18C timing reference; no independent confirmation.')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('score','analyze'))
    for key in ('manifest','output'):p.add_argument('--'+key,type=Path,required=True)
    for key in ('collection','capture','settlement','scores','s1'):p.add_argument('--'+key,type=Path)
    args=p.parse_args();read=lambda path:json.loads(path.read_text());card=read(args.manifest)
    assert not args.output.exists(),'Recover original output rather than re-run'
    from wcomr.gpu_budget_pool_v2 import atomic_json
    if args.action=='analyze':
        scores=read(args.scores)
        assert scores['status']=='COMPLETE_PENDING_ANALYSIS' and scores['scope_sha256']==card['scope_sha256']
        atomic_json(args.output,summarize(card,scores['rows'],read(args.s1)))
    else:
        import os
        import torch
        import lpips
        from wcomr.cara_budget_lifecycle_r1 import released_lifecycle
        from wcomr.cara_fast_fidelity_r1 import score_video_pair
        capture=read(args.capture)
        release=released_lifecycle(capture,capture['files']['launch']['sha256'],read(args.settlement))
        assert all(release[k] for k in ('GPU_released','mode_restored','cost_settled','original_processes_ended','container_exit_success'))
        collection=read(args.collection)
        assert collection['status']=='COMPLETE_PENDING_RELEASE_SCORING' and collection['scope_sha256']==card['scope_sha256']
        assert os.environ['CUDA_VISIBLE_DEVICES']=='' and os.environ['NVIDIA_VISIBLE_DEVICES']=='void'
        torch.set_num_threads(2)
        alex=lpips.LPIPS(net='alex',version='0.1',verbose=False).cpu().eval()
        value=dict(status='SCORING',scope_sha256=card['scope_sha256'],rows=[])
        for row in collection['rows']:
            slot=row['slot']
            if slot['section']!='c':continue
            result=score_video_pair(row['result']['video_artifact'],card['native_references'][slot['member']]['video_artifact'],alex)
            mask=''.join(h['actual'] for h in row['result']['semantic_history'])
            value['rows'].append(dict(slot=slot,Alex=result['Alex'],T_DD=row['result']['T_DD'],fidelity=result,
                mask_matches=mask==card['roles'][slot['role']]['mask']))
            atomic_json(args.output,value)
        value.update(status='COMPLETE_PENDING_ANALYSIS',CUDA_initialized=torch.cuda.is_initialized())
        atomic_json(args.output,value)
