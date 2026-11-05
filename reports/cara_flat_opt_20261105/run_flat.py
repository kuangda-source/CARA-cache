import json,time,numpy as np
from scipy.stats import spearmanr,pearsonr
from core import *
s_raw,dv=load()
VARS=[(f,a,g) for f in ('drift','age') for a in (0.3,0.5) for g in ('sum','rss')]
vname=lambda v:f'{v[0]}_a{v[1]}_{v[2]}'
PRIMARY=('drift',0.5,'sum')
F17Dm=mask_of(F17_D); F17Am=mask_of(F17_A)
fit_sd={t:(s_raw['O1'][t]+s_raw['O2'][t])/2 for t in s_raw['O1']}
def q(x): x=np.asarray(x); return dict(median=float(np.median(x)),min=int(x.min()),p10=float(np.percentile(x,10)),max=int(x.max()),frac_ge7=float((x>=7).mean()))
def summarize(r,v,s,dvk,full=True):
    err=r['err'][v].astype(np.float64); Am=r['Amask'][v[0]]; Dm=r['Dmask']
    i=int(np.argmin(err)); opt=err[i]; oD,oA=int(Dm[i]),int(Am[i])
    out=dict(opt_err=opt,opt_freeD=bits_to_steps(oD),opt_A=bits_to_steps(oA))
    if not full: return out
    rel=err/opt-1; n=len(err)
    out['within']={f'{p}%':dict(n=int((rel<=p/100).sum()),frac=float((rel<=p/100).mean())) for p in (1,2,5,10)}
    out['overlap']={}
    for p in (2,5):
        sel=rel<=p/100
        d=Dm[sel]; a=Am[sel]
        out['overlap'][f'{p}%']=dict(n=int(sel.sum()),
            freeD_vs_opt=q(popc(d&oD)),A_vs_opt=q(popc(a&oA)),
            freeD_vs_F17=q(popc(d&F17Dm)),A_vs_F17=q(popc(a&F17Am)))
    fe=eval_layout(F17_D,F17_A,s,dvk,*v)
    out['F17']=dict(err=fe,gap_pct=100*(fe/opt-1),rank=int((err<fe).sum())+1,rank_frac=float((err<fe).mean()),
                    freeD_overlap_opt=len(set(F17_D)&set(out['opt_freeD'])),A_overlap_opt=len(set(F17_A)&set(out['opt_A'])))
    j=np.where(Dm==F17Dm)[0][0]
    out['F17_D_optA']=dict(err=float(err[j]),gap_pct=float(100*(err[j]/opt-1)),A=bits_to_steps(int(Am[j])))
    out['rel_err_quantiles']={str(p):float(np.percentile(rel,p)) for p in (0.001,0.01,0.1,1,10,50)}
    return out
res=dict(meta=dict(n_layouts=int(comb(28,9)),variants=[vname(v) for v in VARS],primary=vname(PRIMARY)),own={},own_linear={},repo_exact={},transfer={},sanity={})
hist={}
t0=time.time()
for k in MEM:
    for interp,key in (('loglin','own'),('linear','own_linear')):
        s=s_full(s_raw[k],interp)
        r=enumerate_model(s,dv[k],VARS,repo=(interp=='linear'))
        res[key][k]={vname(v):summarize(r,v,s,dv[k],full=True) for v in VARS}
        if interp=='loglin':
            rel=r['err'][PRIMARY]/r['err'][PRIMARY].min()-1
            hist[k]=dict(rel=np.sort(rel)[:: 20].astype(np.float32),F17=res[key][k][vname(PRIMARY)]['F17']['gap_pct']/100)
            # alt variant hist
            for v in VARS: 
                if v!=PRIMARY and v==('age',0.5,'sum'):
                    rr=r['err'][v]/r['err'][v].min()-1; hist[k]['rel_age']=np.sort(rr)[::20].astype(np.float32); hist[k]['F17_age']=res[key][k][vname(v)]['F17']['gap_pct']/100
        else:
            # repo-exact on own s (linear, A ignored): peak & sumsq flatness
            pk,sq=r['repo_peak'],r['repo_sumsq']; Dm=r['Dmask']; Am=r['Amask']['age']
            cand=np.where(pk<=pk.min()*(1+1e-9))[0]; b=cand[np.argmin(sq[cand])]
            d=dict(opt_freeD=bits_to_steps(int(Dm[b])),opt_A=bits_to_steps(int(Am[b])))
            for nm,x in (('peak',pk),('sumsq',sq)):
                rel=x/x[b]-1
                d[nm]={f'{p}%':int((rel<=p/100).sum()) for p in (1,2,5,10)}
                sel=rel<=0.05
                d[nm+'_overlap5']=dict(freeD_vs_opt=q(popc(Dm[sel]&int(Dm[b]))),freeD_vs_F17=q(popc(Dm[sel]&F17Dm)),A_vs_opt=q(popc(Am[sel]&int(Am[b]))))
                j=np.where(Dm==F17Dm)[0][0]; d[nm+'_F17_gap_pct']=float(100*(x[j]/x[b]-1)); d[nm+'_F17_rank']=int((x<x[j]).sum())+1
            res['repo_exact'][k]=d
        print(k,interp,round(time.time()-t0),flush=True)
np.savez_compressed('/workspace/flat_opt/hist.npz',**{f'{k}_{kk}':np.asarray(vv) for k,h in hist.items() for kk,vv in h.items()})
# ---- transfer
sfit=s_full(fit_sd,'loglin')
targets=['O3','O4','N1','N2','N3','N4']
models={k:(sfit,dv[k]) for k in targets}; models['universal']=(sfit,(dv['O1']+dv['O2'])/2)
for name,(s,dvk) in models.items():
    r=enumerate_model(s,dvk,VARS)
    res['transfer'][name]={}
    for v in VARS:
        sm=summarize(r,v,s,dvk,full=False); D=list(range(1,8))+sm['opt_freeD']+[36]; A=sm['opt_A']
        tg=[name] if name!='universal' else targets
        d=dict(fit_layout_freeD=sm['opt_freeD'],fit_layout_A=sm['opt_A'],per_target={})
        for k in tg:
            st=s_full(s_raw[k],'loglin'); own=res['own'][k][vname(v)]
            e=eval_layout(D,A,st,dv[k],*v)
            d['per_target'][k]=dict(gap_pct=100*(e/own['opt_err']-1),F17_gap_pct=own['F17']['gap_pct'],
                freeD_overlap_ownopt=len(set(sm['opt_freeD'])&set(own['opt_freeD'])),freeD_overlap_F17=len(set(sm['opt_freeD'])&set(F17_D)),
                A_overlap_F17=len(set(A)&set(F17_A)))
        res['transfer'][name][vname(v)]=d
    print('transfer',name,round(time.time()-t0),flush=True)
# ---- sanity
meas_F17_F19={'N1':0.006719,'N2':0.003856,'N3':0.070686,'N4':0.005028}
import csv
for r in csv.DictReader(open(DATA+'per_input_LPIPS_CAL35.csv')):
    k=[a for a,b in MEM.items() if b==r['member']][0]
    meas_F17_F19[k]=float(r['F17_A2_LIGHT_C'])-float(r['F19_A1'])
meas_F16_F19={[a for a,b in MEM.items() if b==r['member']][0]:float(r['F16_C'])-float(r['F19_A1']) for r in csv.DictReader(open(DATA+'per_input_LPIPS_CAL35.csv'))}
res['sanity']['measured_F17_minus_F19A1']=meas_F17_F19; res['sanity']['measured_F16_minus_F19A1_old4']=meas_F16_F19
res['sanity']['note_F17_LPIPS_old_from']='figures/cara_f19_speed190_CAL35_r1_20261104/per_input_LPIPS.csv (O1-O4, original CAL35 run); N1-N4 from COMPLETE_RESULTS.md'
for v in VARS:
    d={}
    for k in MEM:
        s=s_full(s_raw[k],'loglin')
        e17=eval_layout(F17_D,F17_A,s,dv[k],*v,split=True); e19=eval_layout(F19_D,F19_A,s,dv[k],*v,split=True); e16=eval_layout(F16_D,F16_A,s,dv[k],*v,split=True)
        tot=(lambda e:float(e.sum())) if v[2]=='sum' else (lambda e:float(np.sqrt((e**2).sum())))
        mid=T<=22
        d[k]=dict(F17=tot(e17),F19A1=tot(e19),F16=tot(e16),diff_F17_F19=tot(e17)-tot(e19),diff_F16_F19=tot(e16)-tot(e19),
                  F17_mid=tot(e17[mid]),F17_tail=tot(e17[~mid]),diff_mid=tot(e17[mid])-tot(e19[mid]),diff_tail=tot(e17[~mid])-tot(e19[~mid]),
                  F17_per_step={int(t):float(x) for t,x in zip(T,e17)})
    new=['N1','N2','N3','N4']; allk=list(MEM)
    sp=lambda ks,key,meas:float(spearmanr([d[k][key] for k in ks],[meas[k] for k in ks]).statistic)
    d['spearman_new4_F17-F19']=sp(new,'diff_F17_F19',meas_F17_F19)
    d['spearman_all8_F17-F19']=sp(allk,'diff_F17_F19',meas_F17_F19)
    d['pearson_all8_F17-F19']=float(pearsonr([d[k]['diff_F17_F19'] for k in allk],[meas_F17_F19[k] for k in allk]).statistic)
    d['spearman_old4_F16-F19']=sp(['O1','O2','O3','O4'],'diff_F16_F19',meas_F16_F19)
    res['sanity'][vname(v)]=d
json.dump(res,open('/workspace/flat_opt/results.json','w'),indent=1)
print('done',round(time.time()-t0))
