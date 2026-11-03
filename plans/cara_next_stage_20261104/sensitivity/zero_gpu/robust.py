import functools
import numpy as np
src=open('analyze.py').read(); exec(src.split("out={'proxies'")[0])
ex=open('extra.py').read(); exec(ex[ex.index('def E_interval'):ex.index('F17D=')])
F17D=[8,10,12,14,16,18,20,21,24];F19D=F17D+[27,30];F16D=F17D[:-1]
def run(v,tag):
    s=[]
    for nD,ref in ((16,F16D),(17,F17D),(19,F19D)):
        ds,m,_=place(nD,v,'v_age'); s.append(f'{nD}D {ds} ov {len(set(ds)&set(ref))}/{len(ref)}')
    ds,_,_=place(17,v,'v_age'); mk,_=assign_AC(sorted(PROT+ds),v,nA=10); c=cmp(mk,REF['F17_A2_lightC'])
    print(tag,'|',' ; '.join(s),'| 17D mask',mk,'DACham',c['DAC_hamming'],'A',c['A_overlap'],'Cj',c['C_jacc'])
for sc_,u in U.items():
    v=norm_mean([g*np.sqrt(u)]); v[0]=np.nan; run(v,'V3 '+sc_)
for p in (0.5,1,2):
    v=norm_mean([g**p*np.sqrt(u) for u in U.values()]); v[0]=np.nan; run(v,f'g^{p}*RMS')
v=norm_mean([g**2*u for u in U.values()]); v[0]=np.nan; run(v,'g2*MSE')
