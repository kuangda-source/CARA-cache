import json,csv,numpy as np,matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from collections import Counter
rows=list(csv.DictReader(open('dataset.csv')))
pr=json.load(open('preds.json')); y=np.exp(np.array(pr['y'])); g=np.array(pr['g'])
EV=[r for r in rows if not r['layout'].startswith('SINGLE_C')]
bat=np.array([r['batch'] for r in EV])
fig,ax=plt.subplots(1,3,figsize=(15,4.8))
cols={'H':'tab:blue','A6000_CAL66':'tab:orange','A6000_DEV128':'tab:green'}
for a,m in zip(ax,['M0','M1','M5f']):
    p=np.exp(np.array(pr['preds'][m]))
    for b,c in cols.items():
        s=bat==b; a.scatter(p[s],y[s],s=12,c=c,label=b,alpha=.7)
    lo,hi=0.03,0.7; a.plot([lo,hi],[lo,hi],'k--',lw=.8); a.set_xscale('log'); a.set_yscale('log')
    from matplotlib.ticker import NullFormatter,FixedLocator,FixedFormatter
    for ax_ in (a.xaxis,a.yaxis): ax_.set_minor_formatter(NullFormatter()); ax_.set_major_locator(FixedLocator([.03,.05,.1,.2,.4,.7])); ax_.set_major_formatter(FixedFormatter(['.03','.05','.1','.2','.4','.7']))
    a.set_xlabel('leave-one-layout-out predicted LPIPS'); a.set_ylabel('measured LPIPS-Alex'); a.set_title(m)
ax[0].legend(fontsize=8)
plt.tight_layout(); plt.savefig('pred_vs_measured.png',dpi=130)
M=json.load(open('results_models.json')); S=json.load(open('results_subsets.json'))
res=dict(dataset=dict(total_points=len(rows),eval_points_multi_step=len(EV),single_C_points=len(rows)-len(EV),
   by_source=Counter(r['source'].split(' ')[0] for r in rows),by_batch=Counter(r['batch'] for r in rows),
   distinct_layout_variants=len({(r['mask'],r['alpha'],r['light_C']) for r in rows}),
   distinct_multistep_layout_variants=M['n_layout_variants_eval'],input_batch_groups=M['n_groups']),
   models=M['models'],subsets=S,generated={m:json.load(open(f'gen_results_{m}.json')) for m in ['M5f','M1','M0']})
json.dump(res,open('results.json','w'),indent=1,default=str)
print(json.dumps(res['dataset'],default=str))
