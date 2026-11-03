import numpy as np,matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
src=open('analyze.py').read(); exec(src.split("out={'proxies'")[0])
F17=REF['F17_A2_lightC']; P='DDDDDDDDADADADADADAADAAADCCCDCCCCCCD'
col={'D':'#d62728','A':'#ff7f0e','C':'#2ca02c'}
fig,ax=plt.subplots(2,1,figsize=(11,6.5),gridspec_kw={'height_ratios':[4,1]},sharex=True)
for k,lab,st in (('V1_RMS_dv','V1 RMS|Δv_guided| (2 FIT scenes)','-o'),('V3_g_RMS_dv','V3 g(t)·RMS|Δv| (weighted by sensitivity prior)','-s'),('V4_abs_dsigma','V4 |Δσ| (weak proxy)','--'),('V5_abs_dlogSNR','V5 |ΔlogSNR| (weak proxy)',':')):
    ax[0].plot(steps,proxies[k],st,ms=3,label=lab)
for i,c in enumerate(F17): ax[0].axvspan(i+0.5,i+1.5,color=col[c],alpha=0.12,lw=0)
ax[0].set_yscale('log'); ax[0].set_ylabel('v(t), normalized per scene to mean(2..36)=1'); ax[0].legend(fontsize=8); ax[0].grid(alpha=.3)
ax[0].set_title('v(t) proxies; background = F17-A2+lightC (red D / orange A / green C); step1 undefined')
for row,(m,name) in enumerate(((F17,'F17'),(P,'principle 17D\n(V3, v·age minimax)'))):
    for i,c in enumerate(m): ax[1].add_patch(plt.Rectangle((i+0.5,1-row-0.4),1,0.8,color=col[c])); ax[1].text(i+1,1-row,c,ha='center',va='center',fontsize=7,color='w')
ax[1].set_yticks([1,0]); ax[1].set_yticklabels(['F17','principle 17D'],fontsize=8); ax[1].set_ylim(-0.6,1.6); ax[1].set_xlim(0.5,36.5); ax[1].set_xticks(range(1,37)); ax[1].tick_params(axis='x',labelsize=7); ax[1].set_xlabel('UniPC step t')
plt.tight_layout(); plt.savefig('/workspace/vt_curve.png',dpi=130)
