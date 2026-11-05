import time,json,numpy as np
from core import *
s,dv=load()
fit={t:(s['O1'][t]+s['O2'][t])/2 for t in s['O1']}
sl=s_full(fit,'linear')
ca=json.load(open(DATA+'complete_analysis.json'))['non_FIT_reconstruction']
t0=time.time()
for k in ['O3','O4','N1','N2','N3','N4']:
    r=enumerate_model(sl,dv[k],[('age',1.0,'sum')],repo=True)
    pk=r['repo_peak']; sq=r['repo_sumsq']
    cand=np.where(pk<=pk.min()*(1+1e-9))[0]; best=cand[np.argmin(sq[cand])]
    mine=[1,2,3,4,5,6,7]+bits_to_steps(r['Dmask'][best])+[36]
    print(k,mine==ca[MEM[k]]['17']['dense_steps'],mine, ca[MEM[k]]['17']['dense_steps'], 'nties_peak',len(cand), round(time.time()-t0,1))
