"""Render receipt-only descriptive diagnostics; requires optional matplotlib."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

p = argparse.ArgumentParser()
p.add_argument('--analysis', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
data = json.loads(a.analysis.read_text())
samples = [s['name'] for s in data['samples']]
fig, axes = plt.subplots(2, 3, figsize=(15, 9), constrained_layout=True)
colors = plt.get_cmap('tab10')
for j, mode in enumerate(['scalar', 'shrink']):
    ax = axes[0, j]
    excluded = 0
    for i, name in enumerate(samples):
        points = [r['candidates'][mode]['metrics'] for r in data['points'] if r['sample'] == name]
        pairs = [(r['postwarp_residual']['mse_ratio_to_official'], r['velocity']['mse_ratio_to_official']) for r in points]
        usable = [(x, y) for x, y in pairs if x is not None and y is not None and x > 0 and y > 0]
        excluded += len(pairs)-len(usable)
        if usable:
            x, y = zip(*usable)
            ax.scatter(x, y, s=22, alpha=.75, color=colors(i), label=str(i+1))
    ax.axhline(1, color='black', linestyle='--', linewidth=.8)
    ax.axvline(1, color='black', linestyle='--', linewidth=.8)
    ax.set(xscale='log', yscale='log', xlabel='Postwarp residual MSE / official',
           ylabel='Velocity MSE / official', title=f'{mode}: paired same-state errors')
    ax.grid(alpha=.2)
    if excluded:
        ax.text(.03, .03, f'{excluded} zero/undefined ratios excluded', transform=ax.transAxes, fontsize=8)
    if j == 0 and samples:
        ax.legend(title='Sample index', fontsize=7, ncol=4)
xlim = (min(ax.get_xlim()[0] for ax in axes[0, :2]), max(ax.get_xlim()[1] for ax in axes[0, :2]))
ylim = (min(ax.get_ylim()[0] for ax in axes[0, :2]), max(ax.get_ylim()[1] for ax in axes[0, :2]))
for ax in axes[0, :2]:
    ax.set(xlim=xlim, ylim=ylim)
    ticks = [.25, .5, 1, 2, 4, 8]
    x_ticks = [v for v in ticks if xlim[0] <= v <= xlim[1]]
    y_ticks = [v for v in ticks if ylim[0] <= v <= ylim[1]]
    ax.set_xticks(x_ticks, labels=[f'{v:g}' for v in x_ticks])
    ax.set_yticks(y_ticks, labels=[f'{v:g}' for v in y_ticks])
ax = axes[0, 2]
reversal_counts = [sum(r['sample'] == name for r in data['ranking_reversals']) for name in samples]
ax.bar(range(1, len(samples)+1), reversal_counts, color=[colors(i) for i in range(len(samples))])
ax.set(title='Residual / velocity ranking reversals', xlabel='Sample index', ylabel='Dependent point-mode comparisons', xticks=list(range(1, len(samples)+1)))
for j, family in enumerate(['time', 'spatial', 'channel']):
    ax = axes[1, j]
    groups = data['group_aggregate']['velocity'][family]
    labels = []
    for g in groups:
        labels.append(' '.join(f'{dict([(1,"C"),(2,"T"),(3,"H"),(4,"W")])[int(axis)]}{lo}:{hi}' for axis, (lo, hi) in g['bounds'].items()))
    x = np.arange(len(groups))
    for offset, mode, color in [(-.18, 'scalar', '#2369a5'), (.18, 'shrink', '#d66d20')]:
        values = [g['candidates'][mode]['mean_sample_sse_ratio_to_official'] for g in groups]
        ax.bar(x+offset, [v if v is not None else np.nan for v in values], width=.36, label=mode, color=color)
    ax.axhline(1, color='black', linestyle='--', linewidth=.8)
    ax.set(title=f'Velocity: latent {family} groups', ylabel='Mean sample group SSE / official', xticks=x, xticklabels=labels)
    ax.tick_params(axis='x', labelrotation=20, labelsize=8)
    ax.grid(axis='y', alpha=.2)
    if j == 0:
        ax.legend(fontsize=8)
group_limit = max(ax.get_ylim()[1] for ax in axes[1])
for ax in axes[1]:
    ax.set_ylim(0, group_limit)
status = 'PARTIAL — NO DECISION' if data['status'].startswith('LIVE_PARTIAL') else 'TERMINAL CAL — DESCRIPTIVE ONLY'
fig.suptitle(f'W1-D | {data["completed_pair_samples"]}/8 paired samples | {status}', fontsize=15)
fig.supxlabel('CAL development only. Equal sample weights; points, CFG branches and axis views are dependent. No video-quality or speed conclusion.', fontsize=9)
a.output.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(a.output, dpi=160)
plt.close(fig)
print(a.output)
