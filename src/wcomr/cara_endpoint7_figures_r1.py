"""Render the complete seven-role analysis with explicit cohort and timing provenance."""
import csv,json
from pathlib import Path
from .cara_endpoint7_analysis_r1 import ROLES
from .policy_price_terminal_r1 import require

LABELS={'F19_C':'F19-C','UNIFORM19_C':'Uniform19-C','F19_A1':'F19-A1',
 'SU19_BR_DIAG_C':'S-DIAG','SU19_CFG_C':'S-CFG','BUDGET_SEARCH19_C':'BudgetSearch','F19_RISKSWAP_C':'F19-RiskSwap'}

def render(report,output,*,cpu_validation=False):
    require(report['schema']=='CARA_ENDPOINT7_COMPLETE_ANALYSIS_R1'
        and report['CPU_fixture_only'] is cpu_validation
        and report['status']==('CPU_FIXTURE_ONLY' if cpu_validation else 'COMPLETE_ACCEPTED_E1_ANALYSIS')
        and report['formal_logical_positions']==28 and len(report['per_member'])==28
        and report['clean_timing_samples']==38,'Complete matching-mode E1 analysis required')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    fig,axes=plt.subplots(2,2,figsize=(14,10),layout='constrained')
    labels=[LABELS[r] for r in ROLES];colors=plt.get_cmap('tab10').colors
    for j,partition in enumerate(('FIT','CHECK')):
        group={r['role']:r for r in report['prompt_equal_summaries'][partition]}
        axes[0,0].bar([i+(-.19 if j==0 else .19) for i in range(7)],
            [group[r]['metrics']['Alex'] for r in ROLES],width=.38,label=partition)
    axes[0,0].set(xticks=range(7),xticklabels=labels,ylabel='Alex LPIPS to original Native',title='Quality: two FIT and two old CAL CHECK')
    axes[0,0].tick_params(axis='x',rotation=25);axes[0,0].legend()
    group={r['role']:r for r in report['prompt_equal_summaries']['ALL']}
    timed=[r for r in ROLES if group[r]['time_mean'] is not None]
    for j,clock in enumerate(('T_DD','T_request')):
        axes[0,1].bar([i+(-.19 if j==0 else .19) for i in range(len(timed))],
            [group[r]['speedup'][clock] for r in timed],width=.38,label=clock)
    axes[0,1].set(xticks=range(len(timed)),xticklabels=[LABELS[r] for r in timed],ylabel='Same-batch speedup',title='Native mean / method mean; equal prompt weights')
    axes[0,1].tick_params(axis='x',rotation=25);axes[0,1].legend();axes[0,1].axhline(1,color='gray',linewidth=.8)
    for i,r in enumerate(timed):
        axes[1,0].scatter(group[r]['time_mean']['T_DD'],group[r]['metrics']['Alex'],label=LABELS[r],color=colors[i])
    axes[1,0].set(xlabel='T_DD seconds (same batch)',ylabel='Alex LPIPS',title='Four old CAL; lower is better on both axes')
    axes[1,0].legend(fontsize=8)
    for i,comparison in enumerate(report['comparisons']['ALL'][:2]):
        values=list(comparison['per_member_difference'].values())
        axes[1,1].plot(range(1,5),values,marker='o',label=LABELS[comparison['left']]+' minus '+LABELS[comparison['right']])
    axes[1,1].axhline(0,color='gray',linewidth=.8)
    axes[1,1].set(xticks=range(1,5),xticklabels=['FIT 1','FIT 2','CHECK 1','CHECK 2'],ylabel='LPIPS difference; negative improves',title='Registered mechanism comparisons')
    axes[1,1].legend(fontsize=8)
    title='CPU SYNTHETIC FIXTURE — NOT EXPERIMENT RESULTS' if cpu_validation else 'E1: complete seven-role endpoint comparison'
    fig.suptitle(title+'\nUniform timing excluded (historical only); old CHECK is not independent TEST',fontsize=14)
    for ax in axes.flat:ax.grid(axis='y',alpha=.2)
    for suffix in ('png','pdf'):fig.savefig(output/('endpoint7.'+suffix),dpi=160)
    plt.close(fig)
    with (output/'prompt_equal_summary.csv').open('x',newline='') as f:
        writer=csv.writer(f);writer.writerow(['partition','role','prompts','Alex','SSIM','T_DD','T_request','T_DD_speedup','T_request_speedup'])
        for partition,rows in report['prompt_equal_summaries'].items():
            for r in rows:
                t=r['time_mean'] or {};s=r['speedup'] or {}
                writer.writerow([partition,r['role'],r['prompt_count'],r['metrics']['Alex'],r['metrics']['SSIM'],t.get('T_DD'),t.get('T_request'),s.get('T_DD'),s.get('T_request')])
    (output/'complete_analysis.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    return dict(CPU_fixture_only=cpu_validation,complete_positions=28,files=['endpoint7.png','endpoint7.pdf','prompt_equal_summary.csv','complete_analysis.json'])
