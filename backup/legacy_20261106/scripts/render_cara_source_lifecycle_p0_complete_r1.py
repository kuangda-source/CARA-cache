"""Export complete two-position P0 effects; no metric recomputation."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

ROLES = ('RW00', 'RW10', 'RW01', 'RW11')
EFFECTS = ('read', 'write', 'interaction', 'joint')


def validate(report, cpu_validation):
    if (report.get('status') != 'COMPLETE16_SCIENTIFIC_POSITIONS_WITH_ORIGINAL_POINT8_REUSED'
            or report.get('CPU_fixture_only') is not cpu_validation
            or report.get('target_updates') != [8, 20]
            or report.get('complete_scientific_positions') != 16
            or report.get('new_scoring_pairs') != 8 or report.get('reused_original_scoring_rows') != 8
            or report.get('original_point8_new_scoring') != 0):
        raise ValueError('Complete16 with eight original rows reused and explicit fixture boundary required')
    members = report['old_FIT_members']
    points = report['point_summaries']
    if (len(members) != 2 or len(set(members)) != 2 or len(points) != 2
            or [p['target_update'] for p in points] != [8, 20]):
        raise ValueError('Two old FIT inputs at both registered points required')
    for point in points:
        if (point['CPU_fixture_only'] is not cpu_validation or point['scientific_pairs'] != 8
                or len(point['members']) != 2 or {m['member'] for m in point['members']} != set(members)
                or len(point['equal_input_mean_Alex_frame_effects']) != 93):
            raise ValueError('Complete two-FIT93-frame point summaries required')
        for member in point['members']:
            if (set(member['losses_Alex']) != set(ROLES) or len(member['Alex_frame_effects']) != 93
                    or any(not math.isfinite(member['losses_Alex'][r]) for r in ROLES)
                    or any(set(row) != set(EFFECTS) or any(not math.isfinite(v) for v in row.values())
                           for row in member['Alex_frame_effects'])):
                raise ValueError('Complete finite per-input losses and all93 effect curves required')
    return points


def render(report, output, *, cpu_validation=False):
    points = validate(report, cpu_validation)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np

    names = {m: ('AV28' if m.startswith('av_') else 'H199') for m in report['old_FIT_members']}
    colors = ('#2878B5', '#D97925')
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)
    upper = max(m['losses_Alex'][r] for p in points for m in p['members'] for r in ROLES)*1.15
    for axis, point in zip(axes[0], points):
        for i, member in enumerate(point['members']):
            axis.bar(np.arange(4)+(i-.5)*.32, [member['losses_Alex'][r] for r in ROLES],
                     width=.32, color=colors[i], label=names[member['member']])
        axis.set(xticks=range(4), xticklabels=['00', '10', '01', '11'], ylim=(0, max(upper, .01)),
                 ylabel='Alex LPIPS to Native', title='Update '+str(point['target_update'])+': endpoint losses')
        axis.legend(fontsize=8)
    groups = [(point, key) for point in points for key in ('W_C', 'W_D')]
    axis = axes[1, 0]
    for i, member in enumerate(report['old_FIT_members']):
        values = [next(m for m in p['members'] if m['member'] == member)['Alex_write_values'][key]
                  for p, key in groups]
        axis.bar(np.arange(4)+(i-.5)*.32, values, width=.32, color=colors[i], label=names[member])
    axis.scatter(range(4), [p['equal_input_mean_Alex_write_values'][key] for p, key in groups],
                 marker='D', color='black', s=22, zorder=3, label='Equal-input mean')
    axis.set(xticks=range(4), xticklabels=[f"t={p['target_update']} {key}" for p, key in groups],
             ylabel='LPIPS reduction (positive is better)', title='Writing under both current-read conditions')
    axis.legend(fontsize=8)
    axis.axhline(0, color='#777777', linestyle='--', linewidth=.7)
    axis = axes[1, 1]
    for point, style in zip(points, ('-', '--')):
        frames = point['equal_input_mean_Alex_frame_effects']
        axis.plot(range(1, 94), [-r['write'] for r in frames], linestyle=style, color=colors[0],
                  label=f"t={point['target_update']} W_C", linewidth=1.5)
        axis.plot(range(1, 94), [-r['write']-r['interaction'] for r in frames], linestyle=style, color=colors[1],
                  label=f"t={point['target_update']} W_D", linewidth=1.5)
    axis.set(xlabel='Decoded frame (all 93)', ylabel='Frame LPIPS reduction', xlim=(1, 93),
             title='Complete equal-input write-value curves')
    axis.legend(fontsize=8)
    axis.axhline(0, color='#777777', linestyle='--', linewidth=.7)
    for axis in axes.flat:
        axis.spines[['top', 'right']].set_visible(False)
        axis.grid(axis='y', alpha=.18)
        axis.set_axisbelow(True)
    scope = 'EXPLICIT SYNTHETIC CPU FIXTURE' if cpu_validation else 'two old FIT inputs; seed 0; paid interventions'
    fig.suptitle('P0 source-writing mechanism: '+scope, fontsize=12)
    for extension in ('png', 'pdf'):
        fig.savefig(output/('P0_two_position_write_values.'+extension), dpi=220)
    plt.close(fig)

    def table(name, fields, rows):
        with (output/name).open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
            writer.writeheader()
            writer.writerows(rows)

    endpoints, frames, means = [], [], []
    for point in points:
        t = point['target_update']
        for member in point['members']:
            endpoints.append(dict(target_update=t, member=member['member'], **member['losses_Alex'],
                                  **member['Alex_write_values'], **member['Alex_effects']))
            frames.extend(dict(target_update=t, member=member['member'], frame_one_based=i+1,
                               W_C=-row['write'], W_D=-row['write']-row['interaction'], **row)
                          for i, row in enumerate(member['Alex_frame_effects']))
        means.extend(dict(target_update=t, frame_one_based=i+1, W_C=-row['write'],
                          W_D=-row['write']-row['interaction'], **row)
                     for i, row in enumerate(point['equal_input_mean_Alex_frame_effects']))
    table('per_input_endpoint_contrasts.csv', ['target_update', 'member', *ROLES, 'W_C', 'W_D', *EFFECTS], endpoints)
    table('all93_per_input_effects.csv', ['target_update', 'member', 'frame_one_based', 'W_C', 'W_D', *EFFECTS], frames)
    table('all93_equal_input_effects.csv', ['target_update', 'frame_one_based', 'W_C', 'W_D', *EFFECTS], means)
    metadata = dict(status='COMPLETE_P0_TWO_POSITION_FIGURES', CPU_fixture_only=cpu_validation,
                    analysis_sha256=hashlib.sha256(json.dumps(report, sort_keys=True).encode()).hexdigest(),
                    complete_scientific_positions=16, independent_input_count=2,
                    reused_original_scoring_rows=8, new_scored_rows=8,
                    all93_frames_exported=True, per_input_frame_rows=len(frames), mean_frame_rows=len(means),
                    matplotlib_version=matplotlib.__version__, numpy_version=np.__version__,
                    metrics_computed=0, GPU_submissions=0,
                    files={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir())})
    with (output/'figure-report.json').open('x') as stream:
        json.dump(metadata, stream, indent=2)
        stream.write('\n')
    return metadata


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--analysis', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(render(json.loads(args.analysis.read_text()), args.output)))
