"""Complete accepted B36 analysis -> fixed tables and diagnostic figure panels."""
import csv
import hashlib
import json
from pathlib import Path

from .cara_fast_b36_analysis_r1 import analyze_complete, CLOCKS
from .cara_fast_binding_r2 import load_card
from .cara_fast_execution_r2 import SPEC, require

ROOT = Path(__file__).resolve().parents[2]
INPUTS = ('capture', 'settlement', 'manifest', 'score-capture', 'accepted-scores')
MEMBERS = ('AV28', 'Human199', 'Misc13398218', 'AV51')


def verify_analysis(path, *, receipt_root=ROOT, cpu_validation=False):
    """Rebuild the aggregate from its five original byte-bound receipts."""
    raw = Path(path).read_bytes()
    analysis = json.loads(raw)
    status = 'CPU_METADATA_FIXTURE_ONLY' if cpu_validation else 'COMPLETE_ACCEPTED_B36_ANALYSIS'
    require(analysis['status'] == status and analysis['CPU_fixture_only'] is cpu_validation,
            'Only complete accepted analysis; CPU fixtures require the isolated CPU test path')
    files = analysis['input_file_sha256']
    require(set(files) == set(INPUTS), 'Five explicit original analysis inputs required')
    values = {}
    for name in INPUTS:
        source = Path(files[name]['path'])
        source = source if source.is_absolute() else Path(receipt_root)/source
        data = source.read_bytes()
        require(hashlib.sha256(data).hexdigest() == files[name]['sha256'], 'Changed analysis input: '+name)
        values[name] = json.loads(data)
    proof = json.loads((ROOT/'reports/cara_fast_B36_analysis_CPU_acceptance_r1_20261029.json').read_bytes())
    require(proof['passed'] and all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == expected
            for name, expected in proof['critical_source_sha256'].items()), 'Original CPU-accepted analysis source changed')
    sources = {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in (
        'scripts/analyze_cara_fast_b36_complete_r1.py', 'src/wcomr/cara_fast_b36_analysis_r1.py')}
    rebuilt = analyze_complete(values['capture'], load_card(ROOT, SPEC), values['settlement'],
        values['manifest'], files['manifest']['sha256'], values['score-capture'], values['accepted-scores'],
        cpu_validation=cpu_validation)
    rebuilt.update(input_file_sha256=files, analysis_source_sha256=sources)
    require(analysis == rebuilt, 'Analysis differs from the complete original accepted evidence')
    return analysis, hashlib.sha256(raw).hexdigest()


def label(analysis, role):
    family = {'WC_FAST': 'WC', 'RA_FAST': 'RA', 'NATIVE_K': 'NATIVE_K'}.get(role)
    if family is None:
        return role
    frozen = analysis['frozen_baselines'][family]
    return frozen['candidate']+' [FIT '+frozen['time_match']+']'


def write_csv(path, rows):
    with path.open('x', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def export_report(analysis, output, ratio_interval, *, cpu_validation=False):
    """Caller verifies original receipts; this function owns output and layout."""
    expected = 'CPU_METADATA_FIXTURE_ONLY' if cpu_validation else 'COMPLETE_ACCEPTED_B36_ANALYSIS'
    require(analysis['status'] == expected and analysis['CPU_fixture_only'] is cpu_validation,
            'Unaccepted or fixture analysis cannot produce production tables or figures')
    output = Path(output)
    require(not output.exists(), 'Fresh report directory required; preserve partial and complete originals')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    output.mkdir()
    rows = analysis['per_member']
    roles = [row['role'] for row in analysis['prompt_equal_summaries']['ALL']]
    members = list(dict.fromkeys(row['member'] for row in rows))
    colors = dict(zip(roles, plt.get_cmap('tab10').colors))
    marker = dict(CPU_fixture_only=cpu_validation)
    scalars, curves, groups, sensitivity = [], [], [], []
    native = {row['member']: row for row in rows if row['role'] == 'NATIVE35'}
    for row in rows:
        scalar = dict(marker, member=row['member'], partition=row['partition'], role=row['role'],
            concrete_role=row['concrete_role'], FIT_baseline_time_match=row['FIT_baseline_time_match'],
            score_id=row['score_id'], formal_slot_id=row['formal_slot_id'], source_phase=row['source_phase'],
            reused_A_score_id=row['reused_A_score_id'], timing_samples=len(row['timing_samples']),
            T_DD=row['time_mean']['T_DD'], T_request=row['time_mean']['T_request'],
            speedup_DD=row['speedup']['T_DD'], speedup_request=row['speedup']['T_request'])
        scalar.update({key: value for key, value in row['metrics'].items() if not key.endswith('_frames')})
        scalars.append(scalar)
        curves.extend(dict(marker, member=row['member'], partition=row['partition'], role=row['role'],
            score_id=row['score_id'], frame_zero_based=index, Alex=alex, SSIM=ssim)
            for index, (alex, ssim) in enumerate(zip(row['metrics']['Alex_frames'], row['metrics']['SSIM_frames'])))
    for partition, summaries in analysis['prompt_equal_summaries'].items():
        for row in summaries:
            selected = [item for item in rows if item['member'] in row['members'] and item['role'] == row['role']]
            low, high = ratio_interval([native[item['member']]['time_mean']['T_DD'] for item in selected],
                                      [item['time_mean']['T_DD'] for item in selected])
            groups.append(dict(marker, partition=partition, role=row['role'], prompts=row['prompt_count'],
                FIT_baseline_time_match=row['FIT_baseline_time_match'],
                T_DD=row['time_mean']['T_DD'], T_request=row['time_mean']['T_request'],
                speedup_DD=row['speedup']['T_DD'], speedup_request=row['speedup']['T_request'],
                speedup_DD_CI95_low=low, speedup_DD_CI95_high=high, **row['metrics'],
                gradient_energy_ratio=row['gradient_energy_ratio'], gradient_ratio_status=row['gradient_ratio_status'],
                undefined_gradient_members=json.dumps(row['undefined_gradient_members']),
                PSNR_per_member=json.dumps(row['PSNR_per_member'])))
    for baseline in analysis['FIT_phase_A_only_sensitivity']:
        for row in baseline['per_member']:
            sensitivity.append(dict(marker, role=baseline['role'], member=row['member'],
                FIT_baseline_time_match=baseline['FIT_baseline_time_match'],
                native_slot_id=row['native_slot_id'], baseline_slot_id=row['baseline_slot_id'],
                native_T_DD=row['native_time']['T_DD'], baseline_T_DD=row['baseline_time']['T_DD'],
                native_T_request=row['native_time']['T_request'], baseline_T_request=row['baseline_time']['T_request'],
                speedup_DD=row['speedup']['T_DD'], speedup_request=row['speedup']['T_request']))
    for name, table in [('per_member', scalars), ('frame_curves', curves), ('prompt_equal', groups), ('FIT_A_only', sensitivity)]:
        write_csv(output/(name+'.csv'), table)

    def save(fig, name):
        fig.text(.5, .015, 'Four old CAL inputs; CHECK is within-CAL. Frame count is not independent sample size.',
                 ha='center', fontsize=9)
        if cpu_validation:
            fig.text(.5, .5, 'CPU LAYOUT ONLY\nNO B36 RESULTS', ha='center', va='center',
                     fontsize=33, color='crimson', alpha=.28, rotation=22)
        fig.savefig(output/(name+'.png'), dpi=140)
        fig.savefig(output/(name+'.pdf'))
        plt.close(fig)

    handles = [plt.Line2D([], [], marker='o', linestyle='', color=colors[role],
        label=str(index+1)+'. '+label(analysis, role)) for index, role in enumerate(roles)]
    for clock in CLOCKS:
        fig, axes = plt.subplots(2, 2, figsize=(14, 9))
        for ax, member, title in zip(axes.flat, members, MEMBERS):
            group = [row for row in rows if row['member'] == member]
            for row in group:
                index = roles.index(row['role'])
                x, y = row['speedup'][clock], row['metrics']['Alex']
                ax.scatter([x], [y], color=colors[row['role']], s=40)
                ax.annotate(str(index+1), (x, y), xytext=(5+(index % 2)*10, 7+(index//2)*9),
                            textcoords='offset points', fontsize=8)
            ax.set(xlabel='Native / role '+clock+' (input mean)', ylabel='Alex LPIPS, all93 mean',
                   title=group[0]['partition']+' | '+title)
            ax.margins(x=.18, y=.35)
            ax.grid(alpha=.2)
        fig.legend(handles=handles, loc='lower center', ncol=4, bbox_to_anchor=(.5, .045), fontsize=8)
        fig.suptitle('Speed versus reference fidelity | '+clock, fontsize=15)
        fig.tight_layout(rect=(0, .14, 1, .95))
        save(fig, clock+'_speed_fidelity')
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    for ax, member, title in zip(axes.flat, members, MEMBERS):
        group = [row for row in rows if row['member'] == member]
        for row in group:
            metrics = row['metrics']
            ax.plot(range(93), metrics['Alex_frames'], color=colors[row['role']], linewidth=1.1)
            worst = metrics['Alex_first_worst_frame_zero_based']
            ax.scatter([worst], [metrics['Alex_worst']], color=colors[row['role']], s=12)
        ax.set(xlabel='Frame index (zero based)', ylabel='Alex LPIPS to same-input Native',
               title=group[0]['partition']+' | '+title, xlim=(0, 92))
        ax.grid(alpha=.2)
    fig.legend(handles=handles, loc='lower center', ncol=4, bbox_to_anchor=(.5, .045), fontsize=8)
    fig.suptitle('All93 frame curves | dots mark each first worst frame', fontsize=15)
    fig.tight_layout(rect=(0, .14, 1, .95))
    save(fig, 'Alex_frame_curves')
    fig, axes = plt.subplots(3, 3, figsize=(15, 11))
    for column, (partition, summaries) in enumerate(analysis['prompt_equal_summaries'].items()):
        for index, metric in enumerate(('reference_temporal_L1', 'reference_gradient_L1', 'gradient_energy_ratio')):
            ax = axes[index, column]
            for position, row in enumerate(summaries):
                value = row['gradient_energy_ratio'] if metric == 'gradient_energy_ratio' else row['metrics'][metric]
                if value is None:
                    ax.text(position, .03, 'undefined', transform=ax.get_xaxis_transform(),
                            rotation=90, ha='center', va='bottom', fontsize=7)
                else:
                    ax.bar(position, value, color=colors[row['role']])
            ax.set_xticks(range(len(roles)), roles, rotation=45, ha='right', fontsize=7)
            ax.set_ylabel(metric, fontsize=8)
            ax.set_title(partition+' | '+str(summaries[0]['prompt_count'])+' CAL inputs', fontsize=10)
            ax.grid(axis='y', alpha=.2)
    fig.suptitle('Temporal and detail diagnostics | no supplemental veto thresholds', fontsize=15)
    fig.tight_layout(rect=(0, .06, 1, .96))
    fig.text(.5, .035, 'WC/RA: FIT UNMATCHED; Native22: FIT MATCHED. Undefined ratios retain every input.', ha='center', fontsize=9)
    save(fig, 'temporal_detail')
    return dict(status='CPU_FIGURE_LAYOUT_ONLY' if cpu_validation else 'COMPLETE_ACCEPTED_B36_FIGURES',
        CPU_fixture_only=cpu_validation, CSV_rows=dict(per_member=32, frame_curves=32*93, prompt_equal=24, FIT_A_only=6),
        figure_panels=4, formats=['png', 'pdf'], GPU_submissions=0, metric_networks_executed=False,
        no_new_selection=True, files={path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(output.iterdir())})
