"""Score only the new videos; merge frozen G17/F17 controls for CPU analysis."""
import argparse
import json
import os
from pathlib import Path
import statistics
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from plans.cara_next_stage_20261105.g17_minitest.postprocess import interval

OLD=ROOT/'reports/cara_g17_minitest_nonfast_r1_20261105'


def summarize(card,rows):
    old=json.loads((OLD/'scores.json').read_text())
    old_analysis=json.loads((OLD/'complete_analysis.json').read_text())
    controls=[r for r in old['rows'] if r['slot']['role'] in ('F17_A2_LIGHT_C','G17')]
    indexed={(r['slot']['member'],r['slot']['role']):r for r in controls+rows}
    effects=[]
    for contrast in card['contrasts']:
        pairs=[dict(member=m,delta_Alex=indexed[m,contrast['candidate']]['Alex']-indexed[m,contrast['reference']]['Alex'],
            delta_T_DD=indexed[m,contrast['candidate']]['T_DD']-indexed[m,contrast['reference']]['T_DD']) for m in contrast['members']]
        values=[p['delta_Alex'] for p in pairs]
        effects.append(dict(**contrast,mean_delta=statistics.mean(values),CI95=interval(values),
            improved=sum(v<0 for v in values),equal=sum(v==0 for v in values),per_input=pairs,
            mean_delta_T_DD=statistics.mean(p['delta_T_DD'] for p in pairs)))
    ratios={}
    for role in card['roles']:
        values=[indexed[m,role]['Alex']/indexed[m,'F17_A2_LIGHT_C']['Alex'] for m in card['inputs_by_alias'].values()]
        ratios[role]=dict(mean=statistics.mean(values),CI95=interval(values),
            per_input=dict(zip(card['inputs_by_alias'],values)),
            predictions={model:pred[role] for model,pred in card['frozen_predictions'].items()})
    errors={model:statistics.mean(abs(ratios[role]['mean']-pred[role]) for role in card['primary_prediction_arms'])
        for model,pred in card['frozen_predictions'].items()}
    means={role:dict(Alex=statistics.mean(indexed[m,role]['Alex'] for m in card['inputs_by_alias'].values()),
        T_DD=statistics.mean(indexed[m,role]['T_DD'] for m in card['inputs_by_alias'].values()))
        for role in list(card['roles'])+['F17_A2_LIGHT_C','G17']}
    return dict(status='COMPLETE',run_id=card['run_id'],scope_sha256=card['scope_sha256'],
        contrasts=effects,ratios_vs_F17=ratios,mean_metrics=means,primary_model_MAE=errors,
        descriptive_closest_parameter_set=min(errors,key=errors.get),
        model_comparison=card['model_comparison'],noninferiority_test=False,significance_test=False,
        CI_method='Exact paired-input bootstrap 4^4 ordered resamples; linear percentile95, descriptive only',
        reused_control_report=str(OLD.relative_to(ROOT)),reused_control_count=len(controls),
        reused_scope_sha256=old_analysis['scope_sha256'],same_run_control=False,
        all_fixed_masks_matched=all(r['mask_matches'] for r in rows),formal_new_scores=len(rows))


def write_results(output,result):
    from wcomr.gpu_budget_pool_v2 import atomic_json
    atomic_json(output,result)
    atomic_json(output.parent/'outcome_summary.json',dict(run_id=result['run_id'],
        primary_model_MAE=result['primary_model_MAE'],descriptive_closest_parameter_set=result['descriptive_closest_parameter_set'],
        ratios_vs_F17=result['ratios_vs_F17'],all_fixed_masks_matched=result['all_fixed_masks_matched'],
        formal_new_scores=result['formal_new_scores'],reused_control_count=result['reused_control_count']))
    lines=['# AVSLC 完整结果','',f"run_id: {result['run_id']}",
        '',f"{result['formal_new_scores']}个新正式结果；8个旧F17/G17结果复用，不重跑、不重算。旧对照属于前一卡的同协议H批次，不是本run的新同时计时。",
        '','|arm|mean Alex|mean T_DD(s)|mean ratio/F17|95%描述性CI|M0A_all|M0A_exclG|','|---|---:|---:|---:|---|---:|---:|']
    for role,r in result['ratios_vs_F17'].items():
        v=result['mean_metrics'][role]
        lines.append(f"|{role}|{v['Alex']:.6f}|{v['T_DD']:.4f}|{r['mean']:.6f}|{r['CI95']}|{r['predictions']['M0A_all']:.6f}|{r['predictions']['M0A_exclG']:.6f}|")
    lines += ['',f"两主臂绝对预测误差MAE：{result['primary_model_MAE']}；描述性最近参数集：{result['descriptive_closest_parameter_set']}。",
        '不重拟合β_L，不做n=4非劣或显著性检验；逐输入方向与效应/CI见complete_analysis.json。',
        '','|对比|mean ΔAlex|95%描述性CI|改善数/4|mean ΔT_DD(s)|','|---|---:|---|---:|---:|']
    for c in result['contrasts']:
        lines.append(f"|{c['candidate']}−{c['reference']}|{c['mean_delta']:+.6f}|{c['CI95']}|{c['improved']}|{c['mean_delta_T_DD']:+.4f}|")
    (output.parent/'COMPLETE_RESULTS.md').write_text('\n'.join(lines)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('score','analyze'))
    for name in ('manifest','output'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('collection','capture','settlement','scores'):p.add_argument('--'+name,type=Path)
    args=p.parse_args();read=lambda path:json.loads(Path(path).read_text())
    from wcomr.gpu_budget_pool_v2 import atomic_json
    card=read(args.manifest)
    if args.action=='analyze':
        scores=read(args.scores)
        assert scores['status']=='COMPLETE_PENDING_ANALYSIS' and scores['scope_sha256']==card['scope_sha256']
        assert not args.output.exists(),'Recover existing analysis, do not replay'
        write_results(args.output,summarize(card,scores['rows']));sys.exit(0)
    from wcomr.cara_budget_lifecycle_r1 import released_lifecycle
    capture=read(args.capture);release=released_lifecycle(capture,capture['files']['launch']['sha256'],read(args.settlement))
    assert all(release[k] for k in ('GPU_released','mode_restored','cost_settled','original_processes_ended','container_exit_success'))
    collection=read(args.collection);launch=json.loads(capture['files']['launch']['raw_utf8'])
    assert launch['run_id']==card['run_id'] and launch['scope_sha256']==card['scope_sha256']
    assert collection['status']=='COMPLETE_PENDING_RELEASE_SCORING' and collection['scope_sha256']==card['scope_sha256']
    assert os.environ['CUDA_VISIBLE_DEVICES']=='' and os.environ['NVIDIA_VISIBLE_DEVICES']=='void'
    assert not args.output.exists(),'Recover existing scores, do not replay'
    import torch,lpips
    from wcomr.cara_fast_fidelity_r1 import score_video_pair
    torch.set_num_threads(2);torch.set_num_interop_threads(1)
    def forbidden(*a,**kw):raise RuntimeError('CPU scorer forbids CUDA/downloads')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
    alex=lpips.LPIPS(net='alex',version='0.1',verbose=False).cpu().eval()
    state=dict(status='SCORING',scope_sha256=card['scope_sha256'],rows=[],release=release);atomic_json(args.output,state)
    for row in collection['rows']:
        slot=row['slot']
        if slot['section']=='warm':continue
        result=score_video_pair(row['result']['video_artifact'],card['native_references'][slot['member']]['video_artifact'],alex)
        actual=''.join(h['actual'] for h in row['result']['semantic_history'])
        state['rows'].append(dict(slot=slot,Alex=result['Alex'],T_DD=row['result']['T_DD'],fidelity=result,
            mask_matches=actual==''.join(card['roles'][slot['role']]['policy']['actions'])))
        atomic_json(args.output,state)
    state.update(status='COMPLETE_PENDING_ANALYSIS',CUDA_initialized=torch.cuda.is_initialized());atomic_json(args.output,state)
