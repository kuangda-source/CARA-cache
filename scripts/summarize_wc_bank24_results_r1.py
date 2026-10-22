"""Join the complete six-DEV endpoint bank with the preregistered X-R metrics."""
import hashlib
import json
import math
from pathlib import Path
from statistics import mean


def ranks(values):
    return [sum(w<v for w in values)+(sum(w==v for w in values)+1)/2 for v in values]


def correlation(a,b):
    da=[x-mean(a) for x in a];db=[x-mean(b) for x in b]
    scale=math.sqrt(sum(x*x for x in da)*sum(x*x for x in db))
    return sum(x*y for x,y in zip(da,db))/scale if scale else None


def main():
    gate_ref=Path('reports/wc_four_card_BANK24_retry2_frozen_gate_analysis_20261022.json')
    xr_ref=Path('reports/wc_four_card_BANK24_retry2_XR_CPU_diagnostics_r2_20261022.json')
    out=Path('reports/wc_four_card_BANK24_retry2_complete_results_analysis_20261022.json')
    assert not out.exists()
    gate=json.loads(gate_ref.read_text());xr=json.loads(xr_ref.read_text());assert xr['exit_code']==0
    rows=[]
    for r in gate['per_scene']:
        x=next(x for x in xr['result']['rows'] if x['scene']==r['scene'])
        rows.append(dict(r,**x['metrics']))
    assert len(rows)==6
    metric_map={'q_MSE':'q_Phi','q_parallel':'q_parallel','q_perp':'q_perpendicular',
        'q_edge':'q_edge','q_combo':'q_combo','visible_z':'z','visible_C_RMS':'visible_C_RMS',
        'visible_correction_RMS':'visible_correction_RMS','visible_root_proxy':'visible_root_proxy'}
    correlations={}
    for name,key in metric_map.items():
        correlations[name]={target:correlation(ranks([r[key] for r in rows]),ranks([r[target] for r in rows]))
            for target in ('A_LPIPS','delta_A_minus_D')}
    reductions=[1-r['q_Phi']/r['q_C'] for r in rows]
    result=dict(status='BANK24_COMPLETE_RESULTS_ANALYZED_FROZEN_DEV_NO_REFIT',scenes=6,
        mean_C_same_state_MSE=mean(r['q_C'] for r in rows),mean_A_same_state_MSE=mean(r['q_Phi'] for r in rows),
        reduction_of_equal_scene_mean_MSE=1-mean(r['q_Phi'] for r in rows)/mean(r['q_C'] for r in rows),
        per_scene_relative_reduction_range=[min(reductions),max(reductions)],A_lower_same_state_error_count=sum(x>0 for x in reductions),
        D_lower_endpoint_LPIPS_count=sum(r['delta_A_minus_D']>0 for r in rows),
        orthogonal_fraction_range=[min(r['q_perpendicular']/r['q_Phi'] for r in rows),max(r['q_perpendicular']/r['q_Phi'] for r in rows)],
        fixed_metric_Spearman=correlations,per_scene=rows,
        gate_same_D_quota_rank=1+gate['same_D_quota']['strictly_better_than_gate'],same_D_quota_count=20,
        gate_minus_random_expected_LPIPS=gate['same_D_quota']['gate_minus_random_expected_LPIPS'],
        equal_quota_gate_selection_advantage_observed=False,automatic_joint_policy_result_available=False,
        inference='Correction lowers the cached velocity error on all six new inputs; the frozen one-step z gate has not established allocation value. Continue the registered interval-label/action-price collection for calibration-driven planning.',
        DEV_refit=False,all_preregistered_metrics_reported=True,new_GPU_submissions=0,
        bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (gate_ref,xr_ref)})
    out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'svg.fonttype':'none'})
    fig,(left,right)=plt.subplots(1,2,figsize=(10.5,4.1),constrained_layout=True)
    labels=['AV rain','AV truck','Human box','Human ball','Geese','Robot']
    left.bar(range(6),[1]*6,color='#dce5eb',width=.72,label='Cached C')
    left.bar(range(6),[r['q_Phi']/r['q_C'] for r in rows],color='#177d8c',width=.42,label='Corrected A')
    left.set_xticks(range(6),labels,rotation=30,ha='right');left.set_ylabel('Same-state velocity MSE / C');left.set_ylim(0,1.18)
    left.set_title('(a) Correction reduces local error on all six DEV');left.legend(frameon=False,loc='upper right')
    policies=gate['all64_combinations']
    right.scatter([p['D_count'] for p in policies],[p['mean_LPIPS'] for p in policies],s=22,c='#9fb1bd',alpha=.65,label='All 64 assignments')
    q=gate['same_D_quota'];right.scatter([3],[q['random_mixture_expected_LPIPS']],s=90,marker='D',color='#177d8c',label='Random expectation (3 D)')
    right.scatter([3],[gate['frozen_z_gate']['mean_LPIPS']],s=150,marker='*',color='#ce5e35',zorder=5,label='Frozen z gate (3 D)')
    right.set_xlabel('Inputs allocated D at step 21 (of 6)');right.set_ylabel('Mean endpoint LPIPS vs Native (lower is better)')
    right.set_xticks(range(7));right.set_title('(b) Frozen gate within the full allocation bank');right.legend(frameon=False,fontsize=8)
    folder=Path('paper/figures/cara_bank24_dev6_r1_20261022');folder.mkdir(parents=True,exist_ok=False)
    for ext in ('pdf','svg','png'):fig.savefig(folder/('mechanism_and_allocation.'+ext),dpi=180)
    svg=folder/'mechanism_and_allocation.svg'
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
    (folder/'provenance.json').write_text(json.dumps(dict(result_ref=str(out),result_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),inputs=6,complete_bank_combinations=64,DEV_refit=False),indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('reduction_of_equal_scene_mean_MSE','per_scene_relative_reduction_range','fixed_metric_Spearman','gate_same_D_quota_rank')}))


if __name__=='__main__':main()
