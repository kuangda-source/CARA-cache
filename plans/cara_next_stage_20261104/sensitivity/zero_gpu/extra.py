import json,numpy as np,functools
from scipy.stats import spearmanr
exec(open('analyze.py').read().split("out={'proxies'")[0])
def E_interval(a,b,vv,kind):
    if kind=='int_v': return vv[a:b].sum()            # sum v(s), s=a+1..b
    if kind=='v_age': return sum(vv[t-1]*(t-a) for t in range(a+1,b))
    if kind=='drift': return sum(vv[a:t].sum() for t in range(a+1,b))
def place(nD,v,kind):
    vv=np.nan_to_num(v);K=nD-8
    @functools.lru_cache(None)
    def f(last,k):
        if k==0: c=E_interval(last,36,vv,kind); return (c,c*c,())
        best=None
        for d in range(last+1,36-k+1):
            c=E_interval(last,d,vv,kind); m,sq,t=f(d,k-1); cand=(max(c,m),sq+c*c,(d,)+t)
            if best is None or cand[:2]<best[:2]: best=cand
        return best
    m,sq,ds=f(7,K); return list(ds),m,sq
def obj(D,v,kind):
    vv=np.nan_to_num(v);Ds=[7]+[d for d in sorted(D) if 8<=d<=35]+[36]
    E=[E_interval(a,b,vv,kind) for a,b in zip(Ds,Ds[1:])]; return max(E),sum(e*e for e in E)
F17D=[8,10,12,14,16,18,20,21,24];F19D=F17D+[27,30];F16D=[8,10,12,14,16,18,20,21]
for name in ('V1_RMS_dv','V2_MSE_dv','V3_g_RMS_dv'):
    v=proxies[name]
    for kind in ('int_v','v_age','drift'):
        line=[]
        for nD,ref in ((16,F16D),(17,F17D),(19,F19D),(22,None)):
            ds,m,sq=place(nD,v,kind)
            s=f'{nD}D opt={ds} max={m:.3f}'
            if ref: rm,rsq=obj(ref,v,kind); s+=f' | ref max={rm:.3f} ({rm/m:.2f}x) overlap={len(set(ds)&set(ref))}/{len(ref)}'
            line.append(s)
        print(name,kind); [print('   ',x) for x in line]
        if kind!='int_v':
            ds,_,_=place(17,v,kind); D=sorted(PROT+ds)
            m,th=assign_AC(D,v,nA=10); print('    17D mask',m,cmp(m,REF['F17_A2_lightC']))
# Spearman excluding F19_C/BudgetSearch (within "search/stage" pool)
er=json.load(open(R+'reports/cara_source_coverage_C1_zero_GPU_audit_r1_20261103.json'))['endpoint_rows']
for name in ('V1_RMS_dv','V2_MSE_dv','V3_g_RMS_dv'):
    v=proxies[name]
    for nD in (19,22):
        rows=[r for r in er if r['D']==nD and r['original_query']]
        L=[r['LPIPS'] for r in rows]; S=[scores(r['dense_steps'],v)['max'] for r in rows]; S2=[scores(r['dense_steps'],v)['sq'] for r in rows]
        print('orig-only',name,nD,len(rows),round(spearmanr(S,L).statistic,3),round(spearmanr(S2,L).statistic,3))
# naive baseline: count of D in 8..16
for nD in (19,22):
    rows=[r for r in er if r['D']==nD]; L=[r['LPIPS'] for r in rows]
    c=[-sum(8<=d<=16 for d in r['dense_steps']) for r in rows]; first=[min(d for d in r['dense_steps'] if d>7) for r in rows]
    print('baseline',nD,'-#D(8..16)',round(spearmanr(c,L).statistic,3),'first free D',round(spearmanr(first,L).statistic,3))
