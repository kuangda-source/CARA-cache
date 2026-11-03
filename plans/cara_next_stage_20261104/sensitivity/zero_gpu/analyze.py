import json,math,itertools,numpy as np
from scipy.stats import spearmanr
R='/workspace/CARA-cache/'
sc=json.load(open(R+'reports/wc_scout_saved_assets_actual_CPU_r1_20261018.json'))['result']['X_S_native_variations']
gains=json.load(open(R+'plans/scouts_20261018/SCOUT_READONLY_CPU_PLAN.json'))['gains']
tn=json.load(open(R+'plans/cara_next_stage_20261103/source_coverage/c1/PHASE_SINGLE7_CANDIDATE_POOLS_R3.json'))['pools']['19']['sigmas']  # 37 normalized
T=36; steps=np.arange(1,37)
def norm_mean(rows):  # per-scene normalize by mean over steps2..36, scene-equal mean (repo convention)
    out=[]
    for r in rows:
        r=np.array(r,float); out.append(r/ r[1:].mean())
    return np.mean(out,0)
U={s['scene'][:6]:np.array(s['unweighted']) for s in sc}
g=np.array(gains)
proxies={
 'V1_RMS_dv':norm_mean([np.sqrt(u) for u in U.values()]),
 'V2_MSE_dv':norm_mean(list(U.values())),
 'V3_g_RMS_dv':norm_mean([g*np.sqrt(u) for u in U.values()]),
 'V4_abs_dsigma':None,'V5_abs_dlogSNR':None}
tn=np.array(tn); ds=np.abs(np.diff(tn)); proxies['V4_abs_dsigma']=ds/ds[1:].mean()
eps=1e-6; t2=np.clip(tn,eps,1-eps); lsnr=2*np.log((1-t2)/t2); dl=np.abs(np.diff(lsnr)); dl[-1]=dl[-2]  # last step to sigma 0 is infinite; copy previous
proxies['V5_abs_dlogSNR']=dl/dl[1:].mean()
for k in proxies: proxies[k][0]=np.nan  # step1 undefined/protected
PROT=list(range(1,8))+[36]
def interval_costs(D,v):
    D=sorted(D); return [v[a:b].sum() for a,b in zip(D,D[1:])]  # sum_{s=a+1}^{b} v(s) (v index s-1)
def place_D(nD,v):
    K=nD-8; free=list(range(8,36)); best=None
    # DP minimax over positions; exact via DP on prefix
    import functools
    vv=np.nan_to_num(v)
    @functools.lru_cache(None)
    def f(last,k):
        if k==0:
            c=vv[last:36].sum(); return (c,c*c,())
        res=None
        for d in range(last+1,36-k+1):
            c=vv[last:d].sum(); m,sq,tail=f(d,k-1)
            cand=(max(c,m),sq+c*c,(d,)+tail)
            if res is None or cand[:2]<res[:2]: res=cand
        return res
    m,sq,ds=f(7,K)
    return sorted(PROT+list(ds))
def place_D_quantile(nD,v):
    K=nD-8; vv=np.nan_to_num(v); c=np.cumsum(vv[7:36]); tot=c[-1]; ds=[]
    for k in range(1,K+1):
        t=int(np.searchsorted(c,k*tot/(K+1)))+8; 
        while t in ds or t>=36: t-=1
        ds.append(t)
    return sorted(PROT+ds)
def ages(D):
    a=[];last=0
    for t in range(1,37):
        if t in D: last=t;a.append(0)
        else: a.append(t-last)
    return np.array(a)
def assign_AC(D,v,nA=None,theta=None,score='v'):
    vv=np.nan_to_num(v); ag=ages(D)
    s=vv if score=='v' else vv*ag
    nonD=[t for t in range(1,37) if t not in D]
    if nA is not None:
        order=sorted(nonD,key=lambda t:-s[t-1]); A=set(order[:nA]); th=s[order[nA-1]-1] if nA else None
    else:
        A={t for t in nonD if s[t-1]>=theta}; th=theta
    return ''.join('D' if t in D else ('A' if t in A else 'C') for t in range(1,37)),th
def mask(D=None,A=()):
    return ''.join('D' if t in D else ('A' if t in A else 'C') for t in range(1,37))
REF={
 'F17_A2_lightC':mask([1,2,3,4,5,6,7,8,10,12,14,16,18,20,21,24,36],[9,11,13,15,17,19,22,23,25,26]),
 'F19_C':mask([1,2,3,4,5,6,7,8,10,12,14,16,18,20,21,24,27,30,36]),
 'F19_A1':mask([1,2,3,4,5,6,7,8,10,12,14,16,18,20,21,24,27,30,36],[9,11,13,15,17,19]),
 'F16_C':mask([1,2,3,4,5,6,7,8,10,12,14,16,18,20,21,36]),
 'Uniform19_C':mask([1,2,3,4,5,6,7,16,19,22,23,24,25,26,27,28,29,31,36]),
 'Shared25_C':'DDDDDDDDDDDDDDDDDDDDDCCDCCDCCDCCCCCD',
}
def cmp(a,b):
    Da={i+1 for i,c in enumerate(a) if c=='D'};Db={i+1 for i,c in enumerate(b) if c=='D'}
    Aa={i+1 for i,c in enumerate(a) if c=='A'};Ab={i+1 for i,c in enumerate(b) if c=='A'}
    Ca={i+1 for i,c in enumerate(a) if c=='C'};Cb={i+1 for i,c in enumerate(b) if c=='C'}
    fa=Da-set(PROT);fb=Db-set(PROT)
    return dict(freeD_overlap=f'{len(fa&fb)}/{len(fb)}',D_hamming=len(Da^Db),A_overlap=f'{len(Aa&Ab)}/{len(Ab)}',C_jacc=round(len(Ca&Cb)/max(1,len(Ca|Cb)),2),DAC_hamming=sum(x!=y for x,y in zip(a,b)))
out={'proxies':{k:[None if np.isnan(x) else round(float(x),4) for x in v] for k,v in proxies.items()}}
res={}
for name,v in proxies.items():
    r={}
    D17=place_D(17,v); m17,th=assign_AC(D17,v,nA=10)
    m17va,thva=assign_AC(D17,v,nA=10,score='vage')
    r['17']=dict(D=D17,mask=m17,theta_A=th,cmp_F17=cmp(m17,REF['F17_A2_lightC']),mask_vage=m17va,cmp_F17_vage=cmp(m17va,REF['F17_A2_lightC']),
                 D_quantile=place_D_quantile(17,v))
    for nD in (16,19,22,25):
        D=place_D(nD,v); m,_=assign_AC(D,v,theta=th)
        e=dict(D=D,mask=m,nA=m.count('A'),D_quantile=place_D_quantile(nD,v))
        if nD==19: e['cmp_F19_C']=cmp(m.replace('A','C'),REF['F19_C']); e['cmp_F19_A1']=cmp(m,REF['F19_A1']); e['cmp_Uniform19']=cmp(m.replace('A','C'),REF['Uniform19_C'])
        if nD==16: e['cmp_F16_C']=cmp(m.replace('A','C'),REF['F16_C'])
        if nD==25: e['cmp_Shared25']=cmp(m.replace('A','C'),REF['Shared25_C'])
        r[str(nD)]=e
    # interval costs of reference masks under this v
    r['ref_intervals']={k:[round(x,3) for x in interval_costs([i+1 for i,c in enumerate(m) if c=='D'],np.nan_to_num(v))] for k,m in REF.items()}
    res[name]=r
out['results']=res
# step 4 spearman
er=json.load(open(R+'reports/cara_source_coverage_C1_zero_GPU_audit_r1_20261103.json'))['endpoint_rows']
def scores(D,v):
    vv=np.nan_to_num(v); ag=ages(D); E=[];cur=0
    Ds=sorted(D)
    for a,b in zip(Ds,Ds[1:]):
        E.append(sum(vv[t-1]*ag[t-1] for t in range(a+1,b)))
    E=np.array(E); 
    drift=[];  # accumulated drift per reuse step
    for a,b in zip(Ds,Ds[1:]):
        for t in range(a+1,b): drift.append(vv[a:t].sum())
    return dict(max=E.max(),sq=(E**2).sum(),drift_max=max(drift) if drift else 0,drift_sq=sum(x*x for x in drift))
sp={}
for name,v in proxies.items():
    sp[name]={}
    for nD in (19,22):
        rows=[r for r in er if r['D']==nD]; L=[r['LPIPS'] for r in rows]
        d={}
        for key in ('max','sq','drift_max','drift_sq'):
            S=[scores(r['dense_steps'],v)[key] for r in rows]; d[key]=round(spearmanr(S,L).statistic,4)
            for inp in ('av_28b','human_'):
                Li=[[x for k,x in r['per_input_LPIPS'].items() if k.startswith(inp)][0] for r in rows]
                d[key+'_'+inp]=round(spearmanr(S,Li).statistic,4)
        d['n']=len(rows); sp[name][nD]=d
out['spearman']=sp
json.dump(out,open('/workspace/vt/results.json','w'),indent=1,default=str)
for name in proxies:
    r=res[name]; print('\n###',name)
    print(' v(8..36):',' '.join(f'{x:.2f}' for x in proxies[name][7:]))
    print(' 17D:',r['17']['mask'],r['17']['cmp_F17'],'| vage:',r['17']['mask_vage'],r['17']['cmp_F17_vage'],'| quantD',r['17']['D_quantile'])
    for nD in ('16','19','22','25'):
        e=r[nD]; print(f' {nD}D:',e['mask'],'nA',e['nA'],{k:v for k,v in e.items() if k.startswith('cmp')},'quantD',e['D_quantile'][7:])
    print(' ref intervals:',r['ref_intervals'])
    print(' spearman',sp[name])
