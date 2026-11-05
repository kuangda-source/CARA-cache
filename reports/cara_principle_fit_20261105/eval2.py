import json,csv,itertools,numpy as np
from scipy.stats import spearmanr
exec(open('fit.py').read().split("N=len(EV)")[0])   # reuse data/prep defs
pr=json.load(open('preds.json')); y=np.array(pr['y']); meas=np.exp(y)
bat=np.array([r['batch'] for r in EV]); inp=np.array([r['input'] for r in EV]); lay=np.array([r['layout'] for r in EV])
def pairs(sel):
    I=[]
    for g in np.unique(gidx[sel]):
        ii=np.where(sel&(gidx==g))[0]; I+=list(itertools.combinations(ii,2))
    return I
subsets={
 'H_O1O2(C1+endpoint, ~45 layouts/input)':(bat=='H')&np.isin(inp,['O1','O2']),
 'H_O3O4':(bat=='H')&np.isin(inp,['O3','O4']),
 'A6000_CAL66 (24/25D, 10 layouts x 4)':bat=='A6000_CAL66',
 'A6000_DEV128 (4 layouts x16 inputs)':bat=='A6000_DEV128',
 'competitive (measured LPIPS <= 1.25x group best)':None,
 'same nD pairs':None,'close pairs |dLPIPS|<0.02':None}
best={g:meas[gidx==g].min() for g in np.unique(gidx)}
comp=np.array([meas[i]<=1.25*best[gidx[i]] for i in range(len(y))])
res={}
RM=json.load(open('results_models.json'))['models']
big=np.array([len(set(lidx[gidx==gidx[i]]))>=3 for i in range(len(y))])
for m,p in pr['preds'].items():
    p=np.array(p); R={}
    for name,sel in subsets.items():
        if name.startswith('competitive'): I=pairs(comp)
        elif name=='same nD pairs': I=[(a,b) for a,b in pairs(np.ones(len(y),bool)) if EV[a]['nD']==EV[b]['nD']]
        elif name.startswith('close'): I=[(a,b) for a,b in pairs(np.ones(len(y),bool)) if abs(meas[a]-meas[b])<0.02]
        else: I=pairs(sel)
        dp=[p[a]-p[b] for a,b in I]; dm=[y[a]-y[b] for a,b in I]
        R[name]=dict(n_pairs=len(I),spearman=round(float(spearmanr(dp,dm)[0]),3),sign_acc=round(float(np.mean(np.sign(dp)==np.sign(dm))),3))
    # F17 vs F19_A1 per input (H batch)
    f=[]
    for k in ['O1','O2','O3','O4','N1','N2','N3','N4']:
        a=[i for i in range(len(y)) if inp[i]==k and bat[i]=='H' and lay[i]=='F17_A2_LIGHT_C'][0]
        b=[i for i in range(len(y)) if inp[i]==k and bat[i]=='H' and lay[i]=='F19_A1'][0]
        th=[RM[m]['params'][q] for q in RM[m]['params']]
        lr=RM[m]['gamma']*(logE(m,th,[a])[0]-logE(m,th,[b])[0])
        f.append(dict(input=k,meas=round(meas[a]-meas[b],4),pred_insample=round(float(meas[b]*(math.exp(lr)-1)),4)))
    R['F17_minus_F19A1']=f
    I=pairs(big); dp=[p[a]-p[b] for a,b in I]; dm=[y[a]-y[b] for a,b in I]
    R['LOLO_paired_all_groups_ge3_layouts']=dict(n_pairs=len(I),spearman=round(float(spearmanr(dp,dm)[0]),3),sign_acc=round(float(np.mean(np.sign(dp)==np.sign(dm))),3))
    res[m]=R
    print(m,{k:(v['spearman'],v['sign_acc'],v['n_pairs']) for k,v in R.items() if not k.startswith('F17')})
    print('   F17-F19',[(x['input'],x['meas'],x['pred_insample']) for x in f])
json.dump(res,open('results_subsets.json','w'),indent=1)
