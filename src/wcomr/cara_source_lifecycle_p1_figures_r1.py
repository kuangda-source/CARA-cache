"""Standalone scientific tables and figures from complete original P1 analysis."""
import csv
from pathlib import Path

from . import cara_source_lifecycle_p1_report_r1 as report
from .cara_budget_search_journal_r1 import create_record, read_record
from .cara_fast_fidelity_r1 import file_sha
from .cara_source_lifecycle_estimation_r1 import FAMILIES
from .policy_price_terminal_r1 import require

SOURCE = 'src/wcomr/cara_source_lifecycle_p1_figures_r1.py'
CLI = 'scripts/render_cara_source_lifecycle_p1_figures_r1.py'
LABELS = {'UNIFORM19_C':'Uniform19-C', 'UNIFORM22_C':'Uniform22-C', 'F19_C':'F19-C',
    'F19_A1':'F19-A1', 'BUDGET_SEARCH19_C':'Frozen RGB-MSE search19'}
for k in (19,22):
    LABELS['LPIPS_SEARCH-K'+str(k)] = 'New LPIPS search'+str(k)
    for family, label in zip(FAMILIES, ('Stage', 'Stage + age', 'V1: stage + age + previous gap')):
        LABELS['V1-'+family+'-K'+str(k)] = label+' ('+str(k)+'D)'


def write_csv(path, fields, rows):
    with path.open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader();writer.writerows(rows)


def export_tables(analysis, directory):
    means, frames, rows, costs = [], [], [], []
    for group, table in analysis['tables'].items():
        for role, value in table.items():
            means.append(dict(group=group, role=role, **{k:value[k] for k in
                ('inputs','LPIPS','SSIM','MSE_video','T_DD','T_request','independent_clean_samples','quality_aliases')},
                infinite_PSNR_inputs='|'.join(value['infinite_PSNR_inputs']),
                undefined_gradient_inputs='|'.join(value['undefined_gradient_inputs'])))
            for i in range(93):
                frames.append(dict(group=group, role=role, frame_zero_based=i,
                    LPIPS=value['LPIPS_curve'][i], SSIM=value['SSIM_curve'][i]))
    for row in analysis['rows']:
        rows.append(dict(role=row['role'], member=row['member'], T_DD=row['T_DD'], T_request=row['T_request'],
            independent_clean_sample=row['independent_clean_sample'],
            **{k:row['metrics'][k] for k in ('Alex','SSIM','MSE_video','PSNR_video_dB','PSNR_is_infinite',
                'reference_temporal_L1','gradient_energy_ratio','gradient_ratio_status')}))
    for k, value in analysis['calibration_costs_and_original_plans'].items():
        costs.append(dict(budget_D=k, **{name:value[name] for name in (
            'main_V1_shared_calibration_and_complete_FIT_cap_seconds','search_measured_charged_seconds',
            'search_termination','configured_search_finished','requested_queries','completed_queries','HC_iterations_completed')}))
    for name, values in (('input-equal-means.csv',means), ('frame-curves93.csv',frames),
                         ('all52-input-rows.csv',rows), ('actual-calibration-costs.csv',costs)):
        write_csv(directory/name, list(values[0]), values)


def plots(analysis, directory):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    plt.rcParams.update({'font.size':10, 'axes.spines.top':False, 'axes.spines.right':False,
                         'pdf.fonttype':42, 'ps.fonttype':42})
    table = analysis['tables']['FOUR_OLD_CAL'];roles = list(table)
    require(set(roles) == set(LABELS), 'All13 fixed role labels required')
    palette = plt.get_cmap('tab20')
    colors = {r:palette(i) for i,r in enumerate(roles)}
    prefix = 'CPU FIXTURE - synthetic evidence only' if analysis['CPU_fixture_only'] else 'P1 - four old CAL inputs'
    fig, axes = plt.subplots(1,2,figsize=(13,7.5))
    for ax, clock, title in zip(axes, ('T_DD','T_request'), ('Denoising + decoding', 'Complete request')):
        for i, role in enumerate(roles,1):
            value = table[role];main = 'stage_age_previous_gap' in role
            ax.scatter(value[clock], value['LPIPS'], color=colors[role], marker='*' if main else 'o', s=140 if main else 50)
            ax.annotate('R'+str(i), (value[clock],value['LPIPS']), xytext=(4,4), textcoords='offset points', fontsize=8)
        ax.set(xlabel=title+' (seconds)',ylabel='LPIPS (lower is better)',title=title)
        ax.grid(alpha=.2)
    legend = ['R'+str(i)+': '+LABELS[r] for i,r in enumerate(roles,1)]
    for i, line in enumerate(legend):
        fig.text(.06+(i%3)*.32, .215-(i//3)*.033, line,fontsize=8.5,color=colors[roles[i]])
    fig.suptitle(prefix+'\nInput-equal quality and both original clocks',fontsize=13)
    fig.subplots_adjust(top=.83,bottom=.32,wspace=.25)
    for ext in ('png','pdf'):fig.savefig(directory/('quality-latency.'+ext),dpi=170)
    plt.close(fig)
    fig, axes = plt.subplots(2,2,figsize=(13,8.5))
    for column,k in enumerate((19,22)):
        selected = [r for r in roles if r == 'UNIFORM'+str(k)+'_C' or r.endswith('-K'+str(k))
                    or (k==19 and r in ('F19_C','F19_A1','BUDGET_SEARCH19_C'))]
        for row,metric in enumerate(('LPIPS','SSIM')):
            ax=axes[row,column]
            for role in selected:
                ax.plot(range(93),table[role][metric+'_curve'],label=LABELS[role],color=colors[role],
                        linewidth=2 if 'stage_age_previous_gap' in role else 1.1)
            ax.set(title=str(k)+'D: '+metric,xlabel='Frame (zero based)',ylabel=metric)
            ax.grid(alpha=.2)
            if row==0:ax.legend(fontsize=7,loc='best')
    fig.suptitle(prefix+'\nComplete93-frame input-equal curves',fontsize=13)
    fig.tight_layout(rect=(0,0,1,.92))
    for ext in ('png','pdf'):fig.savefig(directory/('complete93-curves.'+ext),dpi=170)
    plt.close(fig)


def render(stage, *, cpu_validation=False, fixture_summary=None):
    stage = Path(stage)
    reg = read_record(stage/'registration.json')
    source = {n:file_sha(report.ROOT/n) for n in (SOURCE,CLI)}
    require(all(reg['payload_sha256'].get(n) == h == file_sha(stage/n) for n,h in source.items()),
            'Original registered P1 figure source differs')
    accepted = report.complete(stage,cpu_validation=cpu_validation,fixture_summary=fixture_summary)
    analysis_path=Path(accepted['analysis_path']);analysis=read_record(analysis_path)
    directory=analysis_path.parent/'figures';receipt=directory/'figure-report.json'
    binding=dict(CPU_fixture_only=cpu_validation, analysis_sha256=file_sha(analysis_path),
        original_FIT_freeze_sha256=accepted['freeze_sha256'],source_sha256=source)
    if receipt.exists():
        original=read_record(receipt)
        require(original['binding']==binding and all(file_sha(directory/n)==h for n,h in original['files_sha256'].items()),
                'Original P1 figure bytes or source differ; preserve the original report')
        return original
    directory.mkdir(exist_ok=True)
    require(not any(directory.iterdir()),'Incomplete original P1 figure export requires inspection; never overwrite it')
    export_tables(analysis,directory);plots(analysis,directory)
    result=dict(status='P1_COMPLETE52_ORIGINAL_TABLES_AND_FIGURES_EXPORTED',binding=binding,
        directory=str(directory),files_sha256={p.name:file_sha(p) for p in sorted(directory.iterdir())},
        logical_quality_positions=52,input_equal_mean_rows=39,frame_curve_rows=3627,
        all93_frames=True, both_original_clocks=True, CHECK_is_exposed_development=True,
        original_metric_pairs_recomputed=0,original_FIT_plans_reselected=False,
        GPU_submissions=0,ledger_written=False)
    create_record(receipt,result)
    return result
