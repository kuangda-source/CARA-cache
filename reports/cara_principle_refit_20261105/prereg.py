import json,sys;sys.path.insert(0,'.');from common import *
from gen2 import E_mask,a17,F17
g=json.load(open('gen2.json'))
arms={'G17':'DDDDDDDDDDDDDADADAADAAAAAAACCCCCCCCD','G17_ATAIL':'DDDDDDDDDDDDDADADAADAAAAAAAAAAAAAAAD','G17_CALL':'DDDDDDDDDDDDDCDCDCCDCCCCCCCCCCCCCCCD','G17_A21_24':'DDDDDDDDDDDDDADADAADAAAACCCCCCCCCCCD','R18C':'DDDDDDDDDDDDCDCDCCDCCDCCCDCCCCCCCCCD','R17A':'DDDDDDDDADADADADADADAADAAADCCCCCCCCD'}
out={}
for tag in ['M0A_all','M0A_exclG']:
    th=g[tag]['params']; gam=g[tag]['gamma']; out[tag]={}
    for k,m in arms.items():
        al=[1.0 if c=='A' else 0 for c in m]
        r=[(E_mask(th,i,m,al)/E_mask(th,i,F17,a17))**gam for i in ['O1','O3','N1','N3']]
        out[tag][k]=float(np.mean(r))
    print(tag,{k:round(v,3) for k,v in out[tag].items()})
json.dump(out,open('prereg_next.json','w'),indent=1)
