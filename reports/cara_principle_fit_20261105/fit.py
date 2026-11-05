import csv,json,math,sys,itertools,numpy as np
from scipy.optimize import minimize
from scipy.stats import spearmanr
sys.path.insert(0,'/workspace/flat_opt'); from core import load,s_full,MEM
SIG=np.array([0.99502,0.99421,0.99323,0.99207,0.99067,0.98898,0.98694,0.98447,0.98145,0.97775,0.97320,0.96759,0.96064,0.95200,0.94122,0.92776,0.91093,0.88989,0.86365,0.83112,0.79112,0.74262,0.68494,0.61812,0.54330,0.46294,0.38079,0.30133,0.22887,0.16665,0.11630,0.07777,0.04982,0.03052,0.01784,0.00990,0.0])
sd,dvd=load()
S={k:s_full(sd[k]) for k in MEM}; DV={k:dvd[k] for k in MEM}
SL={}
for k in MEM:
    dd={}
    for r in csv.DictReader(open('/workspace/flat_opt/data/sensitivity.csv')):
        if r['member']==MEM[k]: dd[int(r['t'])]=float(r['LPIPS_Alex'])/float(r['local_guided_delta_RMS'])
    SL[k]=s_full(dd)
SL['MEAN']=np.exp(np.mean([np.log(np.maximum(SL[k],1e-9)) for k in MEM],0))
S['MEAN']=np.exp(np.mean([np.log(np.maximum(S[k],1e-9)) for k in MEM],0)); DV['MEAN']=np.mean([DV[k] for k in MEM],0)
rows=list(csv.DictReader(open('dataset.csv')))
for r in rows:
    r['LPIPS']=float(r['LPIPS']); r['feat']=r['input'] if r['input'] in MEM else 'MEAN'
    r['group']=r['batch'].split('_')[0]+':'+r['input']
    r['lkey']=r['mask']+'|'+r['alpha']+'|'+r['light_C']
    r['single']=r['layout'].startswith('SINGLE_C')
EV=[r for r in rows if not r['single']]
LK=sorted({r['lkey'] for r in EV}); G=sorted({r['group'] for r in EV})
# precompute per-point arrays over steps 8..35
T=np.arange(8,36)
def prep(r):
    m=r['mask']; al=[float(x) for x in r['alpha'].split(';')]
    s=S[r['feat']]; dv=DV[r['feat']]; sL=SL[r['feat']]
    isD=np.array([m[t-1]=='D' for t in T]); isA=np.array([m[t-1]=='A' for t in T]); a_=np.array([al[t-1] for t in T])
    last=[];a=7
    for j,t in enumerate(T):
        if isD[j]: a=t
        last.append(a)
    last=np.array(last); age=T-last
    cum=np.cumsum(dv); drift=cum[T]-cum[last]
    curv=np.array([np.sum(np.abs(dv[l+1:t+1]-dv[l])) if t>l else 0 for t,l in zip(T,last)])
    nonD_after=np.array([np.sum(~isD[j+1:]) for j in range(len(T))])
    return dict(sL=sL[T],s=s[T],dv=dv[T],drift=drift,age=age,isD=isD,isA=isA,al=a_,curv=curv,nda=nonD_after,sig=SIG[T],light=int(r['light_C']))
P=[prep(r) for r in EV]
PM={k:np.array([p[k] for p in P]) for k in P[0]}
FLAT=None
y=np.log(np.array([r['LPIPS'] for r in EV])); gidx=np.array([G.index(r['group']) for r in EV]); lidx=np.array([LK.index(r['lkey']) for r in EV])
def err(p,model,th):
    s=p['s']; nd=~p['isD']
    if model=='M3':
        c2,bl=th
        eC=p['drift']; eA=(1-p['al'])*p['drift']+p['al']*c2*p['curv']
    else:
        ka,bl=th[0],th[1]
        eC=p['drift']; eA=np.clip(1-ka*p['al'],0,None)*p['drift']
    e=np.where(p['isA'],eA,eC)*s
    e=np.where(p['isA']|(p['light']==0),e,e*bl)
    if model=='M1': e=e*th[2]**(p['age']-1)
    if model=='M2': e=e*th[2]**p['nda']
    if model in('M5','M5f'): e=e*np.maximum(p['sig'],1e-3)**th[2]
    e=np.where(nd,e,0)
    if model=='M4':
        q=th[2]; return (np.sum(e**q))**(1/q)
    if model=='RSS': return math.sqrt(np.sum(e**2))
    return np.sum(e)
NP={'M6':2,'M5f':3,'G0':2,'S0':2,'M0':2,'RSS':2,'M1':3,'M2':3,'M3':2,'M4':3,'M5':3}
X0={'M6':[0.5,1],'M5f':[0.5,1,0],'G0':[0.5,1],'S0':[0.5,1],'M0':[0.5,1],'RSS':[0.5,1],'M1':[0.5,1,1.1],'M2':[0.5,1,1.02],'M3':[1,1],'M4':[0.5,1,3],'M5':[0.5,1,0]}
def tr(model,u):  # unconstrained->params
    u=np.clip(np.asarray(u,float),-30,30); th=list(u)
    if model!='M3': th[0]=1/(1+math.exp(-u[0]))*1.2   # kappa_A in [0,1.2]
    else: th[0]=math.exp(u[0])
    th[1]=math.exp(u[1])
    if model in('M1','M2'): th[2]=math.exp(u[2])
    if model=='M4': th[2]=1+math.exp(u[2])
    return th
def tr_inv(model,th):
    u=list(th)
    u[0]=math.log(th[0]/1.2/(1-th[0]/1.2)) if model!='M3' else math.log(th[0]); u[1]=math.log(th[1])
    if model in('M1','M2'): u[2]=math.log(th[2])
    if model=='M4': u[2]=math.log(th[2]-1)
    return u
def errv(model,th,idx):
    p={k:v[idx] for k,v in PM.items()}; light=p['light'][:,None]
    s=p['s'] if model not in('G0','M6') else (np.ones_like(p['s']) if model=='G0' else p['sL'])
    drift=p['drift'] if model!='G0' else p['age']*1.0
    if model=='S0': drift=np.ones_like(drift)
    nd=~p['isD']
    if model=='M3':
        c2,bl=th[0],th[1]; eA=(1-p['al'])*drift+p['al']*c2*p['curv']
    else:
        ka,bl=th[0],(1.0 if model=='M5f' else th[1]); eA=np.clip(1-ka*p['al'],0,None)*drift
    e=np.where(p['isA'],eA,drift)*s
    e=np.where(p['isA']|(light==0),e,e*bl)
    if model=='M1': e=e*th[2]**(p['age']-1)
    if model=='M2': e=e*th[2]**p['nda']
    if model in('M5','M5f'): e=e*np.maximum(p['sig'],1e-3)**th[2]
    e=np.where(nd,e,0)
    if model=='M4': q=th[2]; return (np.sum(e**q,1))**(1/q)
    if model=='RSS': return np.sqrt(np.sum(e**2,1))
    return np.sum(e,1)
def logE(model,th,idx): return np.log(np.maximum(errv(model,th,np.asarray(idx)),1e-12))
def ols(x,yy,gg):
    # yy = b_g + gamma*x ; returns gamma,b dict
    gs=np.unique(gg); xc=x.copy(); yc=yy.copy()
    for g in gs: m=gg==g; xc[m]-=x[m].mean(); yc[m]-=yy[m].mean()
    gam=(xc@yc)/max(xc@xc,1e-12); b={g:(yy[gg==g]-gam*x[gg==g]).mean() for g in gs}
    return gam,b
def fit(model,idx):
    idx=np.array(idx)
    def loss(u):
        th=tr(model,u); x=logE(model,th,idx); gam,b=ols(x,y[idx],gidx[idx])
        res=y[idx]-gam*x-np.array([b[g] for g in gidx[idx]]); return float(res@res)
    best=None
    starts=[tr_inv(model,X0[model])]
    if model!='M3': starts.append(tr_inv(model,[0.9]+X0[model][1:]))
    for u0 in starts:
        o=minimize(loss,u0,method='Nelder-Mead',options=dict(maxiter=600,xatol=1e-3,fatol=1e-6))
        if best is None or o.fun<best.fun: best=o
    th=tr(model,best.x); x=logE(model,th,idx); gam,b=ols(x,y[idx],gidx[idx])
    return th,gam,b,best.fun
def predict(model,th,gam,b,idx,fallback):
    x=logE(model,th,idx); return np.array([gam*xi+b.get(gidx[i],fallback.get(gidx[i],0)) for xi,i in zip(x,idx)])
def paired(pred,meas,gg):
    dp=[];dm=[]
    for g in np.unique(gg):
        ii=np.where(gg==g)[0]
        for a,c in itertools.combinations(ii,2): dp.append(pred[a]-pred[c]); dm.append(meas[a]-meas[c])
    return spearmanr(dp,dm)[0] if len(dp)>2 else float('nan'),len(dp)
def within(pred,meas,gg):
    v=[];w=[]
    for g in np.unique(gg):
        ii=gg==g
        if ii.sum()>=3: v.append(spearmanr(pred[ii],meas[ii])[0]); w.append(ii.sum())
    return float(np.average(v,weights=w))
N=len(EV); ALL=np.arange(N)
out={'n_points_total':len(rows),'n_eval_points':N,'n_layout_variants_eval':len(LK),'n_groups':len(G),'models':{}}
preds={}
MODELS=sys.argv[1].split(',') if len(sys.argv)>1 else ['M0','RSS','M1','M2','M3','M4','M5','G0','S0']
for model in MODELS:
    th,gam,b,sse=fit(model,ALL)
    insample=gam*logE(model,th,ALL)+np.array([b[g] for g in gidx])
    lolo=np.zeros(N)
    for L in range(len(LK)):
        te=np.where(lidx==L)[0]; trn=np.where(lidx!=L)[0]
        th2,gam2,b2,_=fit(model,trn); lolo[te]=predict(model,th2,gam2,b2,te,{})
    # LOIO over inputs with feature data in H batch: hold out group entirely; within-group ranking only
    loio=np.full(N,np.nan)
    for g in range(len(G)):
        te=np.where(gidx==g)[0]
        if len(np.unique(lidx[te]))<3: continue
        trn=np.where(gidx!=g)[0]; th2,gam2,b2,_=fit(model,trn); loio[te]=gam2*logE(model,th2,te)
    ok=~np.isnan(loio)
    r=dict(params=dict(zip({'M3':['c_curv','beta_light']}.get(model,['kappa_A','beta_light','extra'][:NP[model]]),[float(v) for v in th])),gamma=float(gam),SSE_log=float(sse),
           insample_spearman_pooled=float(spearmanr(insample,y)[0]),
           LOLO_spearman_pooled=float(spearmanr(lolo,y)[0]),LOLO_spearman_within_input=within(lolo,y,gidx),
           LOLO_paired_diff_spearman=paired(lolo,y,gidx)[0],
           LOIO_spearman_within_input=within(loio[ok],y[ok],gidx[ok]),LOIO_paired_diff_spearman=paired(loio[ok],y[ok],gidx[ok])[0])
    out['models'][model]=r; preds[model]=lolo.tolist(); print(model,json.dumps(r),flush=True)
# baselines
for name,f in ([] if len(sys.argv)>1 else [('nD_only',lambda r:-int(r['nD'])),('T_only',lambda r:-float(r['T_pred']))]):
    x=np.array([f(r) for r in EV],float)
    out['models'][name]=dict(LOLO_spearman_pooled=float(spearmanr(x,y)[0]),LOLO_spearman_within_input=within(x,y,gidx),LOLO_paired_diff_spearman=paired(x,y,gidx)[0])
    print(name,out['models'][name])
out['n_pairs']=paired(y,y,gidx)[1]
import os
if os.path.exists('results_models.json'):
    old=json.load(open('results_models.json')); old['models'].update(out['models']); out['models']=old['models']
    oldp=json.load(open('preds.json'))['preds']; oldp.update(preds); preds=oldp
json.dump(out,open('results_models.json','w'),indent=1); json.dump(dict(preds=preds,y=y.tolist(),g=gidx.tolist(),l=lidx.tolist()),open('preds.json','w'))
