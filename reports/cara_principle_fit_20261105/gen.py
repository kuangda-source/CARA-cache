import json,numpy as np,sys,math
exec(open('fit.py').read().split("N=len(EV)")[0])
MODEL=sys.argv[1] if len(sys.argv)>1 else 'M5f'
R=json.load(open('results_models.json'))['models'][MODEL]
ka=R['params']['kappa_A']; gam=R['gamma']; bl=1.0 if MODEL=='M5f' else R['params']['beta_light']
g=R['params']['extra'] if MODEL in('M5','M5f') else 0.0
kr=R['params']['extra'] if MODEL=='M1' else 1.0
T=np.arange(8,36)
def evec(feat,a,b):  # errors for steps a+1..b-1 given D at a and b (b exclusive)
    s=S[feat]; dv=DV[feat]; cum=np.cumsum(dv)
    t=np.arange(a+1,b); return s[t]*(cum[t]-cum[a])*np.maximum(SIG[t],1e-3)**g*kr**(t-a-1)
def E_mask(feat,mask,alpha,light=0):
    s=S[feat]; dv=DV[feat]; cum=np.cumsum(dv); a=0; tot=0
    for t in range(1,37):
        c=mask[t-1]
        if c=='D': a=t; continue
        e=s[t]*(cum[t]-cum[a])*max(SIG[t],1e-3)**g*kr**(t-a-1)
        tot+=e*(max(0,1-ka*alpha[t-1]) if c=='A' else (bl if light else 1))
    return tot
def T_of(nD,nA): return 7.51+6.81*nD+0.85*nA
def dp(feat,nD,nAmax):
    # D at 1..7 fixed and 36; choose nD-8 D among 8..35
    k=nD-8; INF=1e18
    # cost(a,b,j)
    cost={}
    pos=[7]+list(range(8,36))
    for a in pos:
        for b in range(a+1,37):
            if b!=36 and b<8: continue
            e=np.sort(evec(feat,a,b))[::-1]
            cs=np.concatenate([[0],np.cumsum(e)])
            cost[(a,b)]=(bl*e.sum(),cs*(bl-(1-ka)))
    # f[a][d][j]: min cost with last D at a, d free D used, j A used
    from functools import lru_cache
    best={}
    f={(7,0,0):(0.0,None)}
    order=sorted(set(pos))
    states={}
    states[7]={(0,0):(0.0,[] ,[])}
    for b in list(range(8,36))+[36]:
        states[b]={}
        for a in [x for x in states if x<b]:
            if not states[a]: continue
            tot,cs=cost[(a,b)]; L=b-a-1
            for (d,j),(v,Ds,As) in states[a].items():
                nd=d+(1 if b<36 else 0)
                if nd>k: continue
                for jj in range(0,min(L,nAmax-j)+1):
                    val=v+tot-cs[jj]
                    key=(nd,j+jj)
                    if key not in states[b] or val<states[b][key][0]:
                        top=list(np.argsort(-evec(feat,a,b))[:jj]+a+1)
                        states[b][key]=(val,Ds+([b] if b<36 else []),As+top)
    res=[(v,Ds,As,j) for (d,j),(v,Ds,As) in states[36].items() if d==k]
    return res
def mk(Ds,As):
    D=set(range(1,8))|set(Ds)|{36}
    return ''.join('D' if t in D else ('A' if t in As else 'C') for t in range(1,37))
F17='DDDDDDDDADADADADADADDAADAACCCCCCCCCD'; F19='DDDDDDDDADADADADADADDCCDCCDCCDCCCCCD'
a17=[(0.5 if t in(25,26) else 1.0) if F17[t-1]=='A' else 0 for t in range(1,37)]; a19=[1.0 if c=='A' else 0 for c in F19]
out={'model':MODEL,'params':dict(kappa_A=ka,g_sigma=g,gamma=gam),'layouts':{}}
feats=['MEAN']+list(MEM)
for nD in [16,17,19,22]:
    budget=132.98
    nAmax=max(0,int(math.floor((budget-T_of(nD,0))/0.85+1e-9))) if T_of(nD,0)<=budget else 28
    fits=T_of(nD,0)<=budget
    res=dp('MEAN',nD,nAmax); v,Ds,As,j=min(res,key=lambda r:r[0])
    m=mk(Ds,As); al=[1.0 if c=='A' else 0 for c in m]
    rel={k:(E_mask(k,m,al,1)/E_mask(k,F17,a17,1))**gam for k in feats}
    rel19={k:(E_mask(k,m,al,1)/E_mask(k,F19,a19,0))**gam for k in feats}
    out['layouts'][nD]=dict(mask=m,nD=nD,nA=m.count('A'),T_pred=round(T_of(nD,m.count('A')),2),meets_1p9x=fits,
        pred_LPIPS_ratio_vs_F17=rel,pred_LPIPS_ratio_vs_F19A1=rel19,
        overlap_D_with_F17=len({t for t in range(8,36) if m[t-1]=='D' and F17[t-1]=='D'}),
        overlap_D_with_F19=len({t for t in range(8,36) if m[t-1]=='D' and F19[t-1]=='D'}))
    # per-input optimum masks for 17D
    print(nD,m,out['layouts'][nD]['nA'],out['layouts'][nD]['T_pred'],fits,'vsF17 mean %.3f'%rel['MEAN'],'vsF19 %.3f'%rel19['MEAN'])
pin={}
for k in MEM:
    res=dp(k,17,11); v,Ds,As,j=min(res,key=lambda r:r[0]); pin[k]=mk(Ds,As)
    print('17D opt',k,pin[k])
out['per_input_17D_opt']=pin
# N3 check
out['N3_check']={k:dict(F17_over_F19_pred=(E_mask(k,F17,a17,1)/E_mask(k,F19,a19,0))**gam) for k in MEM}
print({k:round(v['F17_over_F19_pred'],3) for k,v in out['N3_check'].items()})
json.dump(out,open(f'gen_results_{MODEL}.json','w'),indent=1)
