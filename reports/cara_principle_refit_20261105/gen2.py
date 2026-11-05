import sys,json,math;sys.path.insert(0,'.');from common import *
d=json.load(open('refit_models.json'))['models']
F17='DDDDDDDDADADADADADADDAADAACCCCCCCCCD'
OLD={'G17':'DDDDDDDDDDDDDADADAADAAAAAAACCCCCCCCD','G19':'DDDDDDDDDDDDDDDDADADAAAAAAAAAAAAAAAD','G22':'DDDDDDDDDDDDDDDDDDDDADAAAAAAAAAAAAAD'}
a17=[(0.5 if t in(25,26) else 1.0) if F17[t-1]=='A' else 0 for t in range(1,37)]
def T_of(nD,nA): return 7.51+6.81*nD+0.85*nA
def factors(th,age):  # A factor and light-C factor at given age (alpha=1)
    fA=max(0,1-th.get('ka',0))+th.get('rho',0)*(age-1); return fA,th.get('bl',1.0)
def E_mask(th,feat,mask,alpha,light=1):
    r=dict(mask=mask,alpha=';'.join(str(a) for a in alpha),light_C=light,input='X'); p=prep(r,feat); return float(errv(th,{k:v[None] for k,v in p.items()})[0])
def seg(th,feat,a,b):
    s=S[feat]; cum=np.cumsum(DV[feat]); t=np.arange(a+1,b); e=s[t]*(cum[t]-cum[a])
    fA=np.array([factors(th,ti-a)[0] for ti in t]); bl=factors(th,1)[1]
    gain=e*(bl-fA); o=np.argsort(-gain); g=np.maximum(gain[o],0)  # only positive gains
    return (bl*e).sum(), np.concatenate([[0],np.cumsum(g)]), list(t[o])
def dp(th,feat,nD,nAmax):
    k=nD-8; st={7:{(0,0):(0.0,[],[])}}
    for b in list(range(8,36))+[36]:
        st[b]={}
        for a in [x for x in st if x<b]:
            tot,cs,order=seg(th,feat,a,b); L=b-a-1
            for (dd,j),(v,Ds,As) in st[a].items():
                nd=dd+(1 if b<36 else 0)
                if nd>k: continue
                for jj in range(0,min(L,nAmax-j)+1):
                    if jj>0 and cs[jj]==cs[jj-1]: break
                    val=v+tot-cs[jj]; key=(nd,j+jj)
                    if key not in st[b] or val<st[b][key][0]: st[b][key]=(val,Ds+([b] if b<36 else []),As+order[:jj])
    return min([(v,Ds,As) for (dd,j),(v,Ds,As) in st[36].items() if dd==k],key=lambda r:r[0])
def mk(Ds,As):
    D=set(range(1,8))|set(Ds)|{36}; return ''.join('D' if t in D else ('A' if t in As else 'C') for t in range(1,37))
out={}
for tag,th,gam in [('M0A_all',d['M0A']['params_all'],d['M0A']['gamma_all']),('M0A_exclG',d['M0A']['params_excl_G'],None)]:
    if gam is None:  # gamma for excl-G fit: refit quickly
        import refit as R; F=fit('M0A',R.PM,R.y,R.gidx,np.where(~np.isin(R.lidx,R.GL))[0]); gam=F['gam']
    fa=[round(factors(th,a)[0],3) for a in range(1,9)]
    print(tag,{k:round(v,3) for k,v in th.items()},'gam %.3f'%gam,'A factor by age 1..8',fa,'lightC',round(th['bl'],3))
    out[tag]=dict(params=th,gamma=gam,A_factor_by_age=fa,layouts={})
    for nD in [17,18,19,22]:
        budget=132.98; nAmax=max(0,int(math.floor((budget-T_of(nD,0))/0.85+1e-9))) if T_of(nD,0)<=budget else 28
        v,Ds,As=dp(th,'MEAN',nD,nAmax); m=mk(Ds,As); al=[1.0 if c=='A' else 0 for c in m]
        rel={k:(E_mask(th,k,m,al)/E_mask(th,k,F17,a17))**gam for k in ['MEAN','O1','O3','N1','N3']}
        ref=OLD.get(f'G{nD}'); relold=None
        if ref:
            alo=[1.0 if c=='A' else 0 for c in ref]; relold=float(np.mean([(E_mask(th,k,ref,alo)/E_mask(th,k,F17,a17))**gam for k in ['O1','O3','N1','N3']]))
        out[tag]['layouts'][nD]=dict(mask=m,old_mask=ref,nA=m.count('A'),T_pred=round(T_of(nD,m.count('A')),2),within_132_98s=T_of(nD,0)<=budget,
            pred_ratio_vs_F17=rel,pred_ratio_old_G_mask_vs_F17_mean4=relold)
        print(f' {nD}D new {m} nA={m.count("A")} T={T_of(nD,m.count("A")):.2f}s pred/F17 mean4={np.mean([rel[k] for k in ["O1","O3","N1","N3"]]):.3f}')
        if ref: print(f'     old {ref} pred/F17 under refit={relold:.3f}')
json.dump(out,open('gen2.json','w'),indent=1,default=float)
