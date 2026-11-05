import sys,json,math;sys.path.insert(0,'.')
exec(open('gen2.py').read().split('out={}')[0])
th=d['M0A']['params_all']; gam=d['M0A']['gamma_all']
res={}
for nD in range(14,26):
    for tag,nAmax in [('DC',0),('DAC',28)]:
        if tag=='DAC':
            budget=T_of(nD,0)+0.0  # same time as DC? allow A only within +0 -> skip; instead unconstrained A
        v,Ds,As=dp(th,'MEAN',nD,nAmax); m=mk(Ds,As)
        al=[1.0 if c=='A' else 0 for c in m]
        rel={k:(E_mask(th,k,m,al)/E_mask(th,k,F17,a17))**gam for k in ['MEAN','O1','O3','N1','N3']}
        T=T_of(nD,m.count('A'))
        res[f'{tag}{nD}']=dict(mask=m,nD=nD,nA=m.count('A'),T_pred=round(T,2),speedup=round(252.67/T,3),pred_mean4=round(float(np.mean([rel[k] for k in ['O1','O3','N1','N3']])),3))
        print(tag,nD,m,'nA',m.count('A'),'T',round(T,2),'x',round(252.67/T,3),'pred',res[f'{tag}{nD}']['pred_mean4'])
json.dump(dict(params=th,gamma=gam,layouts=res),open('frozen_gen_v1.json','w'),indent=1,default=float)
