import json,csv,sys
sys.path.insert(0,'/workspace/flat_opt'); from core import MEM
INV={v:k for k,v in MEM.items()}
S='src/'
def mstr(D,A=(),n=36):
    return ''.join('D' if t in D else ('A' if t in A else 'C') for t in range(1,n+1))
rows=[]; seen=set()
def add(inp,lid,mask,alpha,light,avar,batch,lp,src):
    key=(inp,mask,tuple(alpha),light,avar,batch)
    if key in seen: return
    seen.add(key)
    nD,nA,nC=mask.count('D'),mask.count('A'),mask.count('C')
    T=7.51+6.81*nD+0.85*nA+(0 if light else 0.66)*nC
    rows.append(dict(input=INV.get(inp,inp),input_name=inp,layout=lid,mask=mask,alpha=';'.join(f'{a:g}' for a in alpha),
      light_C=int(light),A_variant=avar,batch=batch,nD=nD,nA=nA,nC=nC,T_pred=round(T,2),LPIPS=lp,source=src))
def alpha_of(mask,special={}):
    return [special.get(i+1,1.0) if c=='A' else 0.0 for i,c in enumerate(mask)]
# endpoint7 / B36 roles (two_card)
e7m=json.load(open(S+'e7_46_manifest.json'))['roles']
e7=json.load(open(S+'endpoint7_score.json'))['source_rows']
for k,v in e7.items():
    r=v['role']; m=''.join(a[0] for a in e7m[r]['policy']['actions'])
    add(v['member'],r,m,alpha_of(m),0,'A1' if 'A' in m else '-', 'H',v['Alex'],'endpoint7/B36 '+k)
# C1 pure-C rows
for r in json.load(open(S+'c1_audit.json'))['endpoint_rows']:
    m=mstr(set(r['dense_steps']))
    for inp,lp in r['per_input_LPIPS'].items():
        add(inp,'C1_'+r['origins'][0],m,alpha_of(m),0,'-','H',lp,'C1 audit P1 '+r['candidate_id'][:10])
# CAL35
cm=json.load(open(S+'cal35_manifest.json'))
def find_masks(x,out):
    if isinstance(x,dict):
        for k,v in x.items():
            if isinstance(v,dict) and 'actions' in v and isinstance(v['actions'],(list,str)): out.setdefault(k,v)
            find_masks(v,out)
    elif isinstance(x,list):
        for v in x: find_masks(v,out)
F19='DDDDDDDDADADADADADADDCCDCCDCCDCCCCCD'; F17='DDDDDDDDADADADADADADDAADAACCCCCCCCCD'; F16='DDDDDDDDCDCDCDCDCDCDDCCCCCCCCCCCCCCD'
cal35={'F19_A1':(F19,alpha_of(F19),0,'A1'),'F19_A1_LIGHT_C':(F19,alpha_of(F19),1,'A1'),
       'F17_A2_LIGHT_C':(F17,alpha_of(F17,{25:.5,26:.5}),1,'A2'),'F16_C':(F16,alpha_of(F16),0,'-')}
for r in csv.DictReader(open('/workspace/flat_opt/data/per_input_LPIPS_CAL35.csv')):
    for role,(m,al,li,av) in cal35.items(): add(r['member'],role,m,al,li,av,'H',float(r[role]),'CAL35 per-input')
# confirm4
sc=json.load(open(S+'sens8_complete_results.json'))
pi=sc['confirmation']['per_input']
for inp,v in (pi.items() if isinstance(pi,dict) else [(x['member'],x) for x in pi]):
    for role,kk in [('F17_A2_LIGHT_C','F17_Alex'),('F19_A1','F19_Alex')]:
        val=v[kk]
        m,al,li,av=cal35[role]; add(inp,role,m,al,li,av,'H',float(val),'sensitivity8 confirm4')
# single C
for r in csv.DictReader(open('/workspace/flat_opt/data/sensitivity.csv')):
    t=int(r['t']); m=''.join('C' if i==t else 'D' for i in range(1,37))
    add(r['member'],f'SINGLE_C_t{t}',m,alpha_of(m),0,'-','H',float(r['LPIPS_Alex']),'sensitivity8 single-C')
# CAL66 (A6000 batch) and DEV128
sp=json.load(open(S+'cal66_scope.json'))['roles']
def a66(role):
    p=sp[role]['policy']; m=''.join(a[0] for a in p['actions']); al=[ (x if x is not None else 0.0) for x in p['shared_alpha']]
    al=[al[i] if c=='A' else 0.0 for i,c in enumerate(m)]; return m,al
for f,b in [('cal66_analysis.json','A6000_CAL66'),('dev128_analysis.json','A6000_DEV128')]:
    d=json.load(open(S+f))
    for role,s in d['summaries'].items():
        if role.startswith('NATIVE'): continue
        m,al=a66(role)
        for pp in s['per_prompt']: add(pp['member'],role,m,al,0,'A_PHASE' if 'A' in m else '-',b,pp['LPIPS'],f)
with open('dataset.csv','w',newline='') as fo:
    w=csv.DictWriter(fo,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
from collections import Counter
print(len(rows),Counter(r['batch'] for r in rows),len({(r['mask'],r['alpha'],r['light_C']) for r in rows}),Counter(r['source'].split(' ')[0] for r in rows))
