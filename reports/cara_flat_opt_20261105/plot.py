import numpy as np,json,matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from core import MEM
h=np.load('hist.npz'); R=json.load(open('results.json'))
fig,axs=plt.subplots(2,4,figsize=(18,8),sharex=True)
for ax,k in zip(axs.flat,MEM):
    for key,fk,c,lab in (('rel','F17','C0','drift a0.5 sum (primary)'),('rel_age','F17_age','C1','age a0.5 sum')):
        x=h[f'{k}_{key}']*100
        ax.hist(np.clip(x,0,60),bins=120,histtype='step',color=c,label=lab,density=True)
        ax.axvline(min(float(h[f'{k}_{fk}'])*100,60),color=c,ls='--')
    for p in (2,5): ax.axvline(p,color='gray',lw=.6)
    w=R['own'][k]['drift_a0.5_sum']['within']
    ax.set_title(f"{k} {MEM[k][:14]}\n<=2%: {w['2%']['n']:,}  <=5%: {w['5%']['n']:,}  F17 gap {R['own'][k]['drift_a0.5_sum']['F17']['gap_pct']:.1f}%",fontsize=9)
    ax.set_yscale('log')
axs[0,0].legend(fontsize=7)
for ax in axs[1]: ax.set_xlabel('predicted error above optimum (%) [clipped at 60]')
fig.suptitle('All 6,906,900 17D layouts (9 free D in 8..35, optimal 10 A): predicted-error distribution; dashed = F17, 0 = optimum; grey = 2%/5%')
fig.tight_layout(); fig.savefig('flatness.png',dpi=110)
