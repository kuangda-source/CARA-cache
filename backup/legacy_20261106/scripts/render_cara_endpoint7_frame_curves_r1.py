"""Export every accepted E1 frame curve without computing new metrics."""
import argparse
import csv
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = json.loads(args.report.read_text())
    assert report['status'] == 'COMPLETE_ACCEPTED_E1_ANALYSIS'
    assert report['CPU_fixture_only'] is False and report['formal_logical_positions'] == 28
    rows = report['per_member']
    members = list(dict.fromkeys(row['member'] for row in rows))
    roles = list(dict.fromkeys(row['role'] for row in rows))
    assert len(rows) == len(members) * len(roles) == 28 and len(members) == 4
    assert len({(row['member'], row['role']) for row in rows}) == 28
    assert all(len(row['metrics'][key]) == 93 for row in rows
               for key in ('Alex_frames', 'SSIM_frames'))
    args.output.mkdir(parents=True, exist_ok=False)
    with (args.output / 'all93_frame_curves.csv').open('x', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['member', 'partition', 'role', 'frame_zero_based', 'Alex', 'SSIM', 'score_id'])
        for row in rows:
            for frame, (alex, ssim) in enumerate(zip(row['metrics']['Alex_frames'], row['metrics']['SSIM_frames'])):
                writer.writerow([row['member'], row['partition'], row['role'], frame, alex, ssim, row['score_id']])
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 2, figsize=(14, 9), layout='constrained')
    for ax, member in zip(axes.flat, members):
        selected = [row for row in rows if row['member'] == member]
        for row in selected:
            ax.plot(range(93), row['metrics']['Alex_frames'], label=row['role'], linewidth=1.3)
        ax.set(title=selected[0]['partition'] + ': ' + member,
               xlabel='Frame (zero based)', ylabel='Alex LPIPS to original Native')
        ax.grid(alpha=.2)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='outside lower center', ncol=4, fontsize=9)
    fig.suptitle('E1 complete 28 positions: all 93 frames\nFour old CAL inputs; old CHECK is not independent TEST')
    for suffix in ('png', 'pdf'):
        fig.savefig(args.output / ('all93_frame_curves.' + suffix), dpi=160)
    plt.close(fig)
    print('Exported 2604 accepted frame rows and PNG/PDF curves; no metrics recomputed')


if __name__ == '__main__':
    main()
