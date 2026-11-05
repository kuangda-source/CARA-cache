"""Explicitly authorized partial CPU scoring; never accepts the whole failed run."""
import argparse
import json
import os
from pathlib import Path
import statistics
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from plans.cara_next_stage_20261105.confirm10.postprocess import interval


def complete_groups(card,collection):
    rows=[r for r in collection['rows'] if r['status']=='COMPLETE' and r['slot']['section']!='warm']
    return [m for m in card['inputs_by_alias'].values()
        if {r['slot']['role'] for r in rows if r['slot']['member']==m}==set(card['roles'])]


def analyze(card,scores):
    members=scores['complete_members'];rows=scores['rows']
    indexed={(r['slot']['member'],r['slot']['role']):r for r in rows}
    means={role:dict(Alex=statistics.mean(indexed[m,role]['Alex'] for m in members),
        T_DD=statistics.mean(indexed[m,role]['T_DD'] for m in members)) for role in card['roles'] if role!='NATIVE35'}
    means['NATIVE35']=dict(Alex=0.,T_DD=statistics.mean(scores['native_T_DD'].values()))
    predictions={}
    for role,pred in card['frozen_predictions_vs_F17'].items():
        ratios=[indexed[m,role]['Alex']/indexed[m,'F17_A2_LIGHT_C']['Alex'] for m in members]
        predictions[role]=dict(frozen_prediction=pred,mean_ratio=statistics.mean(ratios),
            absolute_error_of_mean=abs(statistics.mean(ratios)-pred),
            mean_prompt_absolute_error=statistics.mean(abs(v-pred) for v in ratios),per_input=dict(zip(members,ratios)))
    contrasts=[]
    for role in ('R18C','R16C','R21C'):
        pairs=[dict(member=m,delta_Alex=indexed[m,role]['Alex']-indexed[m,'F17_A2_LIGHT_C']['Alex'],
            delta_T_DD=indexed[m,role]['T_DD']-indexed[m,'F17_A2_LIGHT_C']['T_DD']) for m in members]
        values=[p['delta_Alex'] for p in pairs]
        contrasts.append(dict(candidate=role,reference='F17_A2_LIGHT_C',mean_delta=statistics.mean(values),
            descriptive_CI95=interval(values,card['bootstrap']),improved=sum(v<0 for v in values),per_input=pairs))
    return dict(status='INCOMPLETE_PARTIAL',run_id=card['run_id'],scope_sha256=card['scope_sha256'],
        full_run_verdict='NOT_EVALUABLE_INCOMPLETE',complete_members=members,completed_requests=21,original_requests=51,
        scored_pairs=len(rows),planned_pairs=40,frames_per_pair=93,mean_metrics=means,
        frozen_prediction_comparison=predictions,contrasts=contrasts,
        monotonic_mean_LPIPS=means['R16C']['Alex']>=means['R18C']['Alex']>=means['R21C']['Alex'],
        all_masks_match=all(r['mask_matches'] for r in rows),CI_method=card['bootstrap'],
        noninferiority_test=False,significance_test=False,whole_run_success=False,
        limitation='Only first4 of10 frozen prompts, all av; complete-case descriptive results cannot establish the registered10-prompt endpoint.')


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('score','analyze'))
    for name in ('manifest','output'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('collection','release','scores'):p.add_argument('--'+name,type=Path)
    a=p.parse_args();read=lambda path:json.loads(path.read_text())
    from wcomr.gpu_budget_pool_v2 import atomic_json
    card=read(a.manifest)
    assert not a.output.exists(),'Recover original partial output; no score replay'
    if a.action=='analyze':
        s=read(a.scores);assert s['status']=='PARTIAL_SCORES_COMPLETE' and s['scope_sha256']==card['scope_sha256']
        atomic_json(a.output,analyze(card,s));return
    release=read(a.release)
    assert all(release[k] for k in ('cost_settled','GPU_released','mode_restored','original_processes_ended'))
    assert os.environ['CUDA_VISIBLE_DEVICES']=='' and os.environ['NVIDIA_VISIBLE_DEVICES']=='void'
    collection=read(a.collection)
    assert collection['run_id']==card['run_id'] and collection['scope_sha256']==card['scope_sha256']
    members=complete_groups(card,collection)
    completed=[r for r in collection['rows'] if r['status']=='COMPLETE' and r['slot']['section']!='warm'
        and r['slot']['member'] in members]
    references={r['slot']['member']:r for r in completed if r['slot']['role']=='NATIVE35'}
    import torch,lpips
    from wcomr.cara_fast_fidelity_r1 import score_video_pair
    torch.set_num_threads(2);torch.set_num_interop_threads(1)
    def forbidden(*args,**kw):raise RuntimeError('Partial scoring forbids CUDA/downloads')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
    alex=lpips.LPIPS(net='alex',version='0.1',verbose=False).cpu().eval()
    result=dict(status='PARTIAL_SCORING',scope_sha256=card['scope_sha256'],run_id=card['run_id'],
        complete_members=members,rows=[],release=release,native_T_DD={m:r['result']['T_DD'] for m,r in references.items()})
    atomic_json(a.output,result)
    for r in completed:
        s=r['slot']
        if s['role']=='NATIVE35':continue
        f=score_video_pair(r['result']['video_artifact'],references[s['member']]['result']['video_artifact'],alex)
        result['rows'].append(dict(slot=s,Alex=f['Alex'],T_DD=r['result']['T_DD'],fidelity=f,
            mask_matches=''.join(h['actual'] for h in r['result']['semantic_history'])==''.join(card['roles'][s['role']]['policy']['actions'])))
        atomic_json(a.output,result)
    result.update(status='PARTIAL_SCORES_COMPLETE',CUDA_initialized=torch.cuda.is_initialized())
    atomic_json(a.output,result)


if __name__=='__main__':main()
