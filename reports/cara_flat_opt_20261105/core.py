"""Zero-GPU flatness analysis of 17D cache layouts (s * dv error model). CPU only."""
import csv, itertools, math, numpy as np
from math import comb
DATA='/workspace/flat_opt/data/'
MEM={'O1':'av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632','O2':'human_199','O3':'misc_13398218_3840_2160_60fps',
     'O4':'av_51b45829-502e-4143-9c32-c026bd6ab191','N1':'av_cc90f226-5312-4e0f-959a-39cd4eb4d90d',
     'N2':'human_034','N3':'misc_9699390-uhd_3840_2160_30fps','N4':'physics_017'}
T=np.arange(8,36)          # free/non-protected steps (28)
NF=28; KD=9; NA=10
def load():
    s={k:{} for k in MEM}; dv={k:np.zeros(37) for k in MEM}
    inv={v:k for k,v in MEM.items()}
    for r in csv.DictReader(open(DATA+'sensitivity.csv')):
        s[inv[r['member']]][int(r['t'])]=float(r['s'])
    for r in csv.DictReader(open(DATA+'native_delta_v.csv')):
        if r['guided_delta_RMS']: dv[inv[r['member']]][int(r['step'])]=float(r['guided_delta_RMS'])
    return s,dv
def s_full(sd,interp='loglin'):
    """returns array indexed by step (len 37), filled for 8..35"""
    out=np.zeros(37)
    for t in range(8,36):
        if t in sd: out[t]=sd[t]; continue
        if t==35:
            out[t]=math.exp(math.log(sd[34])+0.5*(math.log(sd[34])-math.log(sd[32]))) if interp=='loglin' else sd[34]
        else:
            a,b=sd[t-1],sd[t+1]
            out[t]=math.exp(0.5*(math.log(a)+math.log(b))) if interp=='loglin' else 0.5*(a+b)
    return out
def mask_of(steps): return sum(1<<(t-8) for t in steps if 8<=t<=35)
F17_D=[1,2,3,4,5,6,7,8,10,12,14,16,18,20,21,24,36]; F17_A=[9,11,13,15,17,19,22,23,25,26]
F19_D=[1,2,3,4,5,6,7,8,10,12,14,16,18,20,21,24,27,30,36]; F19_A=[9,11,13,15,17,19]   # F19_A1 (repo zero_gpu/analyze.py REF)
F16_D=[1,2,3,4,5,6,7,8,10,12,14,16,18,20,21,36]; F16_A=[]
def errvec(Dbool,s,dv,form):
    """Dbool [N,28] for steps 8..35. returns e [N,28] (0 at D)."""
    N=Dbool.shape[0]
    a=np.where(Dbool,T[None,:],7); a=np.maximum.accumulate(a,axis=1)
    if form=='drift':
        C=np.cumsum(dv)            # C[t]=sum_{u<=t} dv(u)
        e=s[T][None,:]*(C[T][None,:]-C[a])
    elif form=='age':
        e=(T[None,:]-a)*(s[T]*dv[T])[None,:]
    else: raise ValueError(form)
    return np.where(Dbool,0.0,e)
def total(e,Abool,alpha,agg):
    f=np.where(Abool,alpha,1.0)
    return (e*f).sum(1) if agg=='sum' else np.sqrt(((e*f)**2).sum(1))
def eval_layout(D,A,s,dv,form,alpha,agg,split=None):
    Db=np.array([[t in D for t in T]]); Ab=np.array([[t in A for t in T]])
    e=errvec(Db,s,dv,form)[0]*np.where(Ab[0],alpha,1.0)
    if split is None: return float(e.sum()) if agg=='sum' else float(np.sqrt((e**2).sum()))
    return e
def repo_intervals(Dbool,e_age):
    """repo-exact: interval masses sum_{t in (a,b)} (t-a) w(t), A ignored. returns peak, sumsq"""
    N=Dbool.shape[0]; r=np.zeros(N); pk=np.zeros(N); sq=np.zeros(N)
    for j in range(NF):
        d=Dbool[:,j]; pk=np.where(d,np.maximum(pk,r),pk); sq=np.where(d,sq+r*r,sq); r=np.where(d,0.0,r+e_age[:,j])
    pk=np.maximum(pk,r); sq=sq+r*r
    return pk,sq
_COMB=None
def combos():
    global _COMB
    if _COMB is None:
        n=comb(NF,KD)
        _COMB=np.fromiter(itertools.chain.from_iterable(itertools.combinations(range(NF),KD)),dtype=np.int8,count=n*KD).reshape(n,KD)
    return _COMB
def enumerate_model(s,dv,variants,chunk=400_000,repo=False):
    """exact enumeration over all C(28,9) free-D sets, optimal A (top-10 e among non-D) per set.
    returns Dmask[int32], Amask[int32], dict variant->err(float32), (+repo peak,sumsq)"""
    cb=combos(); n=len(cb); w=(1<<np.arange(NF)).astype(np.int64)
    Dm=np.empty(n,np.int32); out={v:np.empty(n,np.float32) for v in variants}
    Am={f:np.empty(n,np.int32) for f in {v[0] for v in variants}}
    if repo: rp=np.empty(n,np.float64); rs=np.empty(n,np.float64)
    for i in range(0,n,chunk):
        c=cb[i:i+chunk]; m=len(c); Db=np.zeros((m,NF),bool); Db[np.arange(m)[:,None],c]=True
        Dm[i:i+m]=(Db*w).sum(1)
        for form in Am:
            e=errvec(Db,s,dv,form)
            idx=np.argpartition(-e,NA-1,axis=1)[:,:NA]
            Ab=np.zeros((m,NF),bool); Ab[np.arange(m)[:,None],idx]=True
            Am[form][i:i+m]=(Ab*w).sum(1)
            for v in variants:
                if v[0]!=form: continue
                out[v][i:i+m]=total(e,Ab,v[1],v[2])
            if repo and form=='age':
                p,q=repo_intervals(Db,e); rp[i:i+m]=p; rs[i:i+m]=q
    res=dict(Dmask=Dm,Amask=Am,err=out)
    if repo: res.update(repo_peak=rp,repo_sumsq=rs)
    return res
def bits_to_steps(m): return [8+j for j in range(NF) if (int(m)>>j)&1]
def popc(x): return np.bitwise_count(np.asarray(x,dtype=np.int64)) if False else np.bitwise_count(np.asarray(x).astype(np.uint32))
