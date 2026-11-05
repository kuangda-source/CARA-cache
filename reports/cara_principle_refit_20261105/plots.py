import json,numpy as np,matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
d=json.load(open('refit_models.json'))['models']; ARMS=['F17_A2_LIGHT_C','G17','G17_TAIL','G19','G22']; INP=['O1','O3','N1','N3']
fig,ax=plt.subplots(1,3,figsize=(15,4.5),sharey=True)
for a_,(m,k,t) in zip(ax,[('M5f','G_frozen_old','M5f, old-data fit (pre-registered)'),('M0A','G_prospective_exclG','M0A, fit excluding all G layouts'),('M0A','G_LOLO','M0A, LOLO')]):
    g=d[m][k]['per_input']
    for i,inp in enumerate(INP):
        xs=[g[inp][a]['pred_ratio'] for a in ARMS]; ys=[g[inp][a]['meas_ratio'] for a in ARMS]
        a_.scatter(xs,ys,label=inp)
        for a,x,y in zip(ARMS,xs,ys):
            if a!='F17_A2_LIGHT_C': a_.annotate(a.replace('G17_TAIL','tail'),(x,y),fontsize=7)
    a_.axhline(1,c='gray',lw=.5);a_.axvline(1,c='gray',lw=.5);a_.plot([.4,1.4],[.4,1.4],'k:',lw=.7)
    a_.set_title(t,fontsize=10);a_.set_xlabel('predicted LPIPS ratio vs F17')
ax[0].set_ylabel('measured LPIPS ratio vs F17');ax[0].legend()
plt.tight_layout();plt.savefig('fig_G_pred_vs_meas.png',dpi=120)
s=json.load(open('subsample.json'))['summary']
fig,ax=plt.subplots(1,2,figsize=(12,4.5))
for n,c in zip(['1','2','4','6','all'],['C0','C1','C2','C3','C4']):
    ks=[k for k in s if k.startswith(f'M0A|N={n}|')]
    ks=sorted(ks,key=lambda k:s[k]['gpuh_mean'])
    ax[0].plot([s[k]['gpuh_mean'] for k in ks],[s[k]['median'] for k in ks],'o-',c=c,label=f'N={n}')
    ax[0].plot([s[k]['gpuh_mean'] for k in ks],[s[k]['p10'] for k in ks],'x:',c=c)
    ax[1].plot([s[k]['gpuh_mean'] for k in ks],[s[k]['G19worst_frac'] for k in ks],'o-',c=c,label=f'N={n}')
ax[0].set_xlabel('calibration GPUh (runs + native + s(t) 0.946/input)');ax[0].set_ylabel('held-out-fold paired Spearman (o median, x p10)');ax[0].legend();ax[0].set_title('M0A subsampling (G layouts excluded from training)')
ax[1].set_xlabel('calibration GPUh');ax[1].set_ylabel('fraction of inputs where G19 predicted worst');ax[1].set_title('M0A: G19 identified as worst');ax[1].legend()
plt.tight_layout();plt.savefig('fig_subsample.png',dpi=120)
