"""Accepted, identity-bound records only -> prompt-equal two-clock paper table."""
import argparse
import csv
import json
import math
import random
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from wcomr.cara_fast_fidelity_r1 import file_sha


def ratio_interval(native, candidate):
    rng=random.Random(20261028);n=len(native);values=[]
    for _ in range(20000):
        indices=[rng.randrange(n) for _ in range(n)]
        values.append(sum(native[i] for i in indices)/sum(candidate[i] for i in indices))
    values.sort()
    return values[math.ceil(.025*(len(values)-1))],values[math.ceil(.975*(len(values)-1))]


def main():
    p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--figure',type=Path)
    a=p.parse_args();assert not a.output.exists()
    if a.figure and a.figure.exists():raise ValueError('Figure already exists')
    manifest=json.loads(a.manifest.read_text())
    if not manifest['accepted_batches']:
        raise ValueError('No accepted Fast results; planned values must remain empty')
    table=[]
    for batch in manifest['accepted_batches']:
        source=ROOT/batch['path']
        if file_sha(source)!=batch['sha256']:raise ValueError('Accepted batch source differs')
        data=json.loads(source.read_text())
        if (data['status']!='ACCEPTED_COMPLETE' or data['scope_sha256']!=batch['scope_sha256']
                or not data['central_settlement_accepted'] or not data['CPU_scoring_accepted']):
            raise ValueError('Complete independent technical, financial and scoring acceptance required')
        # Batches stay separate by host/UUID/source/config. Refusals/failures
        # are preserved in the acceptance receipt, never silently filtered here.
        rows=data['formal_rows'];expected={(m,r) for m in data['members'] for r in data['roles']}
        if len(rows)!=len(expected) or {(r['member'],r['role']) for r in rows}!=expected:
            raise ValueError('Incomplete formal comparison denominator')
        if any(r['status']!='COMPLETE' for r in rows):
            raise ValueError('Failure/refusal batch requires its preregistered missingness analysis')
        natives={r['member']:r for r in rows if r['role']=='NATIVE35'}
        for role in data['roles']:
            group=[r for r in rows if r['role']==role]
            clocks={k:sum(r[k] for r in group)/len(group) for k in ('T_DD_prompt_mean','T_request_prompt_mean')}
            native={k:sum(natives[r['member']][k] for r in group)/len(group) for k in clocks}
            if any(not math.isfinite(v) or v<=0 for v in [*clocks.values(),*native.values()]):
                raise ValueError('Finite positive accepted clocks required')
            lo,hi=ratio_interval([natives[r['member']]['T_DD_prompt_mean'] for r in group],
                                 [r['T_DD_prompt_mean'] for r in group])
            table.append(dict(batch=batch['id'],host=data['host'],gpu_uuid=data['gpu_uuid'],role=role,
                prompts=len(group),T_DD=clocks['T_DD_prompt_mean'],T_request=clocks['T_request_prompt_mean'],
                speedup_DD=native['T_DD_prompt_mean']/clocks['T_DD_prompt_mean'],
                speedup_DD_CI95_low=lo,speedup_DD_CI95_high=hi,
                speedup_request=native['T_request_prompt_mean']/clocks['T_request_prompt_mean'],
                Alex=sum(r['Alex'] for r in group)/len(group),
                SSIM=sum(r['SSIM'] for r in group)/len(group),
                PSNR_prompt_equal_mean_dB=sum(float(r['PSNR_video_dB'].replace('+inf','inf')) if isinstance(r['PSNR_video_dB'],str) else r['PSNR_video_dB'] for r in group)/len(group),
                reference_temporal_L1=sum(r['reference_temporal_L1'] for r in group)/len(group),
                reference_gradient_L1=sum(r['reference_gradient_L1'] for r in group)/len(group)))
    with a.output.open('x',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=list(table[0]));writer.writeheader();writer.writerows(table)
    if a.figure:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        batches=list(dict.fromkeys(r['batch'] for r in table))
        fig,axes=plt.subplots(1,len(batches),squeeze=False,figsize=(6*len(batches),4))
        for ax,batch in zip(axes[0],batches):
            values=[r for r in table if r['batch']==batch]
            ax.scatter([r['T_DD'] for r in values],[r['Alex'] for r in values])
            for row in values:ax.annotate(row['role'],(row['T_DD'],row['Alex']),xytext=(3,3),textcoords='offset points',fontsize=8)
            ax.set(xlabel='Denoise + decode wall time (s)',ylabel='Alex LPIPS to matched Native',title=batch)
            ax.grid(alpha=.2)
        fig.tight_layout();fig.savefig(a.figure);plt.close(fig)
    print(json.dumps(dict(rows=len(table),status='ACCEPTED_PROMPT_EQUAL_TABLE',source=str(a.manifest))))


if __name__=='__main__':main()
