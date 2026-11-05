"""Refit of layout-error principle with G17 mini-test points. CPU only."""
import csv,json,math,sys,itertools,numpy as np
from scipy.optimize import minimize
from scipy.stats import spearmanr
sys.path.insert(0,'/workspace/flat_opt'); from core import load,s_full,MEM
INV={v:k for k,v in MEM.items()}
SIG=np.array([0.99502,0.99421,0.99323,0.99207,0.99067,0.98898,0.98694,0.98447,0.98145,0.97775,0.97320,0.96759,0.96064,0.95200,0.94122,0.92776,0.91093,0.88989,0.86365,0.83112,0.79112,0.74262,0.68494,0.61812,0.54330,0.46294,0.38079,0.30133,0.22887,0.16665,0.11630,0.07777,0.04982,0.03052,0.01784,0.00990,0.0])
sd,dvd=load()
S={k:s_full(sd[k]) for k in MEM}; DV={k:dvd[k] for k in MEM}
S['MEAN']=np.exp(np.mean([np.log(np.maximum(S[k],1e-9)) for k in MEM],0)); DV['MEAN']=np.mean([DV[k] for k in MEM],0)
NEWSRC='/workspace/principle_refit/src/'
def new_rows():
    man=json.load(open(NEWSRC+'manifest_with_nonfast.json'))['roles']
    sc=json.load(open(NEWSRC+'scores.json'))['rows']
    out=[]
    for r in sc:
        role=r['slot']['role']; p=man[role]['policy']; m=''.join(p['actions'])
        al=[(a if a is not None else 0.0) for a in p['shared_alpha']]; al=[al[i] if c=='A' else 0.0 for i,c in enumerate(m)]
        light=int(bool(man[role]['light_C']))
        nD,nA,nC=m.count('D'),m.count('A'),m.count('C')
        out.append(dict(input=INV[r['slot']['member']],input_name=r['slot']['member'],layout=role,mask=m,alpha=';'.join(f'{a:g}' for a in al),
            light_C=light,A_variant='A',batch='H',nD=nD,nA=nA,nC=nC,T_pred=round(7.51+6.81*nD+0.85*nA+(0 if light else 0.66)*nC,2),
            LPIPS=r['Alex'],T_DD=r['T_DD'],source='G17mini '+r['slot']['id']))
    return out
def load_rows(include_new=True):
    rows=list(csv.DictReader(open('/workspace/principle_fit/dataset.csv')))
    for r in rows: r['LPIPS']=float(r['LPIPS']); r['light_C']=int(r['light_C']); r['nD']=int(r['nD']); r['T_pred']=float(r['T_pred'])
    if include_new:
        seen={(r['batch'],r['input'],r['mask'],r['alpha'],r['light_C']):r for r in rows}
        for r in new_rows():
            k=(r['batch'],r['input'],r['mask'],r['alpha'],r['light_C'])
            if k in seen:
                assert abs(seen[k]['LPIPS']-r['LPIPS'])<1e-5,(k,seen[k]['LPIPS'],r['LPIPS'])  # bit-reproduced duplicate
                continue
            rows.append(r); seen[k]=r
    for r in rows:
        r['feat']=r['input'] if r['input'] in MEM else 'MEAN'
        r['group']=r['batch'].split('_')[0]+':'+r['input']
        r['lkey']=r['mask']+'|'+r['alpha']+'|'+str(r['light_C'])
        r['single']=r['layout'].startswith('SINGLE_C')
        r['new']=r['source'].startswith('G17mini')
    return rows
T=np.arange(8,36)
def prep(r,feat=None):
    f=feat or r['feat']; m=r['mask']; al=[float(x) for x in r['alpha'].split(';')]
    s=S[f]; dv=DV[f]
    isD=np.array([m[t-1]=='D' for t in T]); isA=np.array([m[t-1]=='A' for t in T]); a_=np.array([al[t-1] for t in T])
    last=[];a=7
    for j,t in enumerate(T):
        if isD[j]: a=t
        last.append(a)
    last=np.array(last); age=T-last
    cum=np.cumsum(dv); drift=cum[T]-cum[last]
    return dict(t=T.astype(float),s=s[T],drift=drift,age=age.astype(float),isD=isD,isA=isA,al=a_,sig=SIG[T],light=np.full(len(T),int(r['light_C'])))
def stack(P): return {k:np.array([p[k] for p in P]) for k in P[0]}
# ---------------- generic model -----------------
# params by name; each model = list of free params with transforms
PDEF={'ka':(lambda u:1.2/(1+math.exp(-u)), lambda v:math.log(v/1.2/(1-v/1.2)), 0.25),
      'bl':(math.exp, math.log, 1.0),
      'kr':(math.exp, math.log, 0.9),
      'g':(lambda u:u, lambda v:v, 1.0),
      'rho':(math.exp, math.log, 0.05),       # A-age penalty: A factor = max(0,1-ka*al) + rho*al*(age-1)
      'phi':(math.exp, math.log, 0.05),       # sigma-weight floor: w = sig^g + phi
      'rl':(math.exp, math.log, 0.05),        # log-age A penalty: A factor += rl*al*log(age)
      'lt':(math.exp, math.log, 0.05),        # late-A penalty: A factor += lt*al for t>=28 (sigma<0.1)
      }
MODELS={'M0':['ka','bl'],'M1':['ka','bl','kr'],'M5f':['ka','g'],'M5':['ka','bl','g'],
        'M0A':['ka','bl','rho'],'M1A':['ka','bl','kr','rho'],'M5fA':['ka','g','rho'],'M5fF':['ka','g','phi'],'M5fAF':['ka','g','rho','phi'],
        'M5A':['ka','bl','g','rho'],'M1F':['ka','bl','kr','g','phi'],'M0L':['ka','bl','lt'],'M0AL':['ka','bl','rho','lt'],'M0Alog':['ka','bl','rl'],'M5fAlog':['ka','g','rl']}
def th_of(model,u): return {n:PDEF[n][0](float(np.clip(x,-30,30))) for n,x in zip(MODELS[model],u)}
def u_of(model,th): return [PDEF[n][1](th[n]) for n in MODELS[model]]
def errv(th,p):
    ka=th.get('ka',0); bl=th.get('bl',1.0)
    fA=np.clip(1-ka*p['al'],0,None)+th.get('rho',0)*p['al']*(p['age']-1)+th.get('lt',0)*p['al']*(p['t']>=28)+th.get('rl',0)*p['al']*np.log(np.maximum(p['age'],1))
    f=np.where(p['isA'],fA,np.where(p['light']==1,bl,1.0))
    e=p['s']*p['drift']*f
    if 'kr' in th: e=e*th['kr']**(p['age']-1)
    if 'g' in th: e=e*(np.maximum(p['sig'],1e-3)**th['g']+th.get('phi',0))
    return np.sum(np.where(p['isD'],0,e),1)
def logE(th,p): return np.log(np.maximum(errv(th,p),1e-12))
def sub(PM,idx): return {k:v[idx] for k,v in PM.items()}
def ols(x,yy,gg):
    ng=int(gg.max())+1; cnt=np.bincount(gg,minlength=ng).astype(float); cnt[cnt==0]=1
    xm=np.bincount(gg,x,ng)/cnt; ym=np.bincount(gg,yy,ng)/cnt
    xc=x-xm[gg]; yc=yy-ym[gg]
    gam=(xc@yc)/max(xc@xc,1e-12); b={int(g):float(ym[g]-gam*xm[g]) for g in np.unique(gg)}
    return gam,b
def fit(model,PM,y,gidx,idx,x0=None):
    idx=np.asarray(idx); p=sub(PM,idx); yy=y[idx]; gg=gidx[idx]
    def loss(u):
        x=logE(th_of(model,u),p)
        ng=int(gg.max())+1; cnt=np.bincount(gg,minlength=ng).astype(float); cnt[cnt==0]=1
        xc=x-(np.bincount(gg,x,ng)/cnt)[gg]; yc=yy-(np.bincount(gg,yy,ng)/cnt)[gg]
        gam=(xc@yc)/max(xc@xc,1e-12); res=yc-gam*xc; return float(res@res)
    starts=[u_of(model,{n:PDEF[n][2] for n in MODELS[model]})]
    alt={n:PDEF[n][2] for n in MODELS[model]}; alt['ka']=0.9
    if 'g' in alt: alt['g']=2.5
    starts.append(u_of(model,alt))
    if x0 is not None: starts.append(list(x0))
    best=None
    for u0 in starts:
        o=minimize(loss,u0,method='Nelder-Mead',options=dict(maxiter=400*len(u0),xatol=1e-3,fatol=1e-7))
        if best is None or o.fun<best.fun: best=o
    th=th_of(model,best.x); x=logE(th,p); gam,b=ols(x,yy,gg)
    return dict(th=th,u=list(best.x),gam=gam,b=b,sse=best.fun)
def paired(pred,meas,gg,sel=None):
    dp=[];dm=[]
    ii_all=np.arange(len(pred)) if sel is None else np.where(sel)[0]
    for g in np.unique(gg[ii_all]):
        ii=ii_all[gg[ii_all]==g]
        for a,c in itertools.combinations(ii,2): dp.append(pred[a]-pred[c]); dm.append(meas[a]-meas[c])
    if len(dp)<3: return float('nan'),len(dp),float('nan')
    dp=np.array(dp); dm=np.array(dm)
    return float(spearmanr(dp,dm)[0]),len(dp),float(np.mean(np.sign(dp)==np.sign(dm)))
