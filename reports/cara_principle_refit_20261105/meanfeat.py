import sys,json;sys.path.insert(0,'.');import refit as R
from common import *
from multiprocessing import Pool
# replace features with MEAN s(t)/dv for every row
R.PM=stack([prep(r,'MEAN') for r in R.EV])
out={}
if __name__=='__main__':
  with Pool(8) as pool:
    for model in ['M0','M5f','M0A']:
        lolo=np.zeros(R.N)
        for te,p in pool.map(R.lolo_one,[(model,L) for L in range(len(R.LK))]): lolo[te]=p
        g=R.g_check(lolo); pa=paired(lolo,R.y,R.gidx)
        out[model]=dict(LOLO_paired_all=pa,G_LOLO_mean_pred=g['mean_pred_ratio'],G19worst=g['G19_pred_worst_inputs'],sign5=g['pair_sign_acc_5arms'])
        print(model,'MEAN-feat LOLO paired',round(pa[0],3),'G19worst',g['G19_pred_worst_inputs'],'sign5',round(g['pair_sign_acc_5arms'],2),{a[:6]:round(v,3) for a,v in g['mean_pred_ratio'].items()})
  json.dump(out,open('meanfeat.json','w'),indent=1,default=float)
