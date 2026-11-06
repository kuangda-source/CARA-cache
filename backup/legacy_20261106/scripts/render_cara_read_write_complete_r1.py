"""Export full93 M1 contrasts after complete8 acceptance; no metric computation."""
import argparse
import csv
import hashlib
import json
from pathlib import Path


def render(report, output, *, cpu_validation=False):
    if (report['status'] != 'COMPLETE_TWO_OLD_FIT_M1_CONTRASTS'
            or report['CPU_fixture_only'] is not cpu_validation
            or report['scientific_pairs'] != 8 or len(report['members']) != 2
            or len(report['equal_input_mean_Alex_frame_effects']) != 93):
        raise ValueError('Complete accepted M1 analysis and exact fixture boundary required')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np

    roles = ('RW00', 'RW10', 'RW01', 'RW11')
    effects = ('read', 'write', 'interaction', 'joint')
    colors = ('#2878B5', '#D97925', '#8560A7', '#39865A')
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), constrained_layout=True)
    labels = ('AV28 (old FIT)', 'H199 (old FIT)')
    for i, member in enumerate(report['members']):
        axes[0, 0].bar(np.arange(4)+(i-.5)*.32, [member['losses_Alex'][r] for r in roles],
            width=.32, color=colors[i], label=labels[i])
        axes[0, 1].bar(np.arange(4)+(i-.5)*.32, [member['Alex_effects'][e] for e in effects],
            width=.32, color=colors[i], label=labels[i])
    axes[0, 0].set(xticks=range(4), xticklabels=roles, ylabel='Alex LPIPS to fresh Native', title='A  Complete endpoint losses')
    axes[0, 0].legend(fontsize=8)
    axes[0, 1].set(xticks=range(4), xticklabels=effects, ylabel='Change in reference error', title='B  Signed endpoint effects')
    axes[0, 1].scatter(range(4), [report['equal_input_mean_Alex_effects'][e] for e in effects],
        color='black', marker='D', s=20, label='Equal-input mean', zorder=3)
    axes[0, 1].legend(fontsize=8, loc='upper left', bbox_to_anchor=(1.01, 1))
    frames = report['equal_input_mean_Alex_frame_effects']
    for i, effect in enumerate(effects):
        axis = axes[1, 0] if i < 2 else axes[1, 1]
        axis.plot(range(1, 94), [row[effect] for row in frames], color=colors[i], label=effect, linewidth=1.7)
    for axis, title in zip(axes[1], ('C  Mean read and write effects', 'D  Mean interaction and joint effects')):
        axis.set(title=title, xlabel='Decoded frame (all 93)', ylabel='Change in frame Alex LPIPS', xlim=(1, 93))
        axis.legend(fontsize=8)
    for axis in (axes[0, 1], *axes[1]):
        axis.axhline(0, color='#777777', linestyle='--', linewidth=.7)
    for axis in axes.flat:
        axis.spines[['top', 'right']].set_visible(False)
        axis.grid(axis='y', alpha=.18)
        axis.set_axisbelow(True)
    fig.suptitle('M1 read/write intervention: '+('EXPLICIT SYNTHETIC CPU FIXTURE' if cpu_validation else 'two old FIT inputs; seed 0'), fontsize=12)
    for suffix in ('png', 'pdf'):
        fig.savefig(output/('M1_read_write_contrasts.'+suffix), dpi=220)
    plt.close(fig)
    with (output/'all93_mean_frame_effects.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['frame_one_based', *effects])
        writer.writeheader()
        writer.writerows(dict(frame_one_based=i+1, **row) for i, row in enumerate(frames))
    with (output/'per_input_endpoint_effects.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['member', *effects])
        writer.writeheader()
        writer.writerows(dict(member=m['member'], **m['Alex_effects']) for m in report['members'])
    metadata = dict(status='COMPLETE_M1_CONTRAST_FIGURES', CPU_fixture_only=cpu_validation,
        scope_sha256=report['scope_sha256'], analysis_sha256=hashlib.sha256(json.dumps(report, sort_keys=True).encode()).hexdigest(),
        files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir())},
        all93_frames_exported=True, metrics_computed=0, GPU_submissions=0)
    with (output/'figure-report.json').open('x') as stream:
        json.dump(metadata, stream, indent=2)
        stream.write('\n')
    return metadata


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--analysis', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(render(json.loads(args.analysis.read_text()), args.output)))


if __name__ == '__main__':
    main()
