import sys,json,time;sys.path.insert(0,'.');from common import *
import refit as R
from multiprocessing import Pool
rng0=np.random.default_rng(12345)
EV=R.EV; N=R.N; LK=R.LK; lidx=R.lidx; gidx=R.gidx; y=R.y; PM=R.PM
inp=np.array([r['input'] for r in EV]); Tpred=np.array([r['T_pred'] for r in EV])
NATIVE=7.51+6.81*36; SCOST=0.946
POOL6=['O1','O2','O3','O4','N1','N3']
perm=rng0.permutation(len(LK)); FOLDS=[perm[i::5] for i in range(5)]
NS=[1,2,4,6,'all']; MS=[10,20,30,50,'all']; REP=20
def job(a):
    model,f,n,m,rep=a; rng=np.random.default_rng(hash((f,str(n),str(m),rep))%2**32)
    test=np.isin(lidx,FOLDS[f]); 
    ins=list(set(inp)) if n=='all' else list(rng.choice(POOL6,n,replace=False))
    cand=np.where(~test & np.isin(inp,ins) & ~np.isin(lidx,R.GL))[0]; lays=np.unique(lidx[cand])
    if m!='all':
        if len(lays)<m: return None
        lays=rng.choice(lays,m,replace=False)
    tr=cand[np.isin(lidx[cand],lays)]
    if len(tr)<4: return None
    F=fit(model,PM,y,gidx,tr); x=logE(F['th'],PM)
    sp,npair,sa=paired(x*np.sign(F['gam']) if F['gam']!=0 else x,y,gidx,test)
    g=R.g_check(F['gam']*x)
    ns=len([k for k in ins if k in MEM]); gpuh=(Tpred[tr].sum()+NATIVE*len(ins))/3600+SCOST*ns
    return dict(model=model,fold=f,N=str(n),M=str(m),rep=rep,n_train_pts=int(len(tr)),n_train_layouts=int(len(lays)),spearman=sp,sign_acc=sa,G19worst=g['G19_pred_worst_inputs'],Gsign5=g['pair_sign_acc_5arms'],gpuh=float(gpuh))
if __name__=='__main__':
    models=sys.argv[1].split(',') if len(sys.argv)>1 else ['M0A','M0']
    jobs=[(mo,f,n,m,r) for mo in models for f in range(5) for n in NS for m in MS for r in (range(REP) if not(n=='all' and m=='all') else [0])]
    t0=time.time()
    with Pool(8) as p: res=[r for r in p.map(job,jobs,chunksize=8) if r]
    print(len(res),'fits',round(time.time()-t0),'s')
    json.dump(res,open('subsample_raw.json','w'))
    import collections
    summ={}
    for mo in models:
        for n in NS:
            for m in MS:
                rr=[r for r in res if r['model']==mo and r['N']==str(n) and r['M']==str(m)]
                if not rr: continue
                sp=np.array([r['spearman'] for r in rr]); g=np.array([r['gpuh'] for r in rr])
                summ[f'{mo}|N={n}|M={m}']=dict(sign_acc_median=float(np.median([r['sign_acc'] for r in rr])),G19worst_frac=float(np.mean([r['G19worst']/4 for r in rr])),Gsign5_mean=float(np.mean([r['Gsign5'] for r in rr])),median=float(np.median(sp)),mean=float(np.mean(sp)),p10=float(np.percentile(sp,10)),gpuh_mean=float(g.mean()),n_fits=len(rr),train_pts=float(np.mean([r['n_train_pts'] for r in rr])))
                print(f'{mo} N={n!s:3s} M={m!s:3s} spearman med {np.median(sp):.3f} p10 {np.percentile(sp,10):.3f} signacc {np.median([r["sign_acc"] for r in rr]):.3f} G19worst {np.mean([r["G19worst"]/4 for r in rr]):.2f}  GPUh {g.mean():6.2f}  pts {np.mean([r["n_train_pts"] for r in rr]):.0f} n={len(rr)}')
    json.dump(dict(folds=[list(map(int,f)) for f in FOLDS],summary=summ),open('subsample.json','w'),indent=1)
