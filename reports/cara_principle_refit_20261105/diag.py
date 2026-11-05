import sys,json;sys.path.insert(0,'.');from common import *
rows=load_rows(); EV=[r for r in rows if not r['single']]
PM=stack([prep(r) for r in EV]); y=np.log([r['LPIPS'] for r in EV])
G=sorted({r['group'] for r in EV}); gidx=np.array([G.index(r['group']) for r in EV])
old=np.array([not r['new'] for r in EV])
INP=['O1','O3','N1','N3']; ARMS=['F17_A2_LIGHT_C','G17','G17_TAIL','G19','G22']
def idx_of(inp,lay): return [i for i,r in enumerate(EV) if r['input']==inp and r['batch']=='H' and r['layout']==lay][0]
out={}
for model in ['M0','M1','M5f','M5']:
    F=fit(model,PM,y,gidx,np.where(old)[0]); x=logE(F['th'],PM)
    R={'params':F['th'],'gamma':F['gam'],'per_input':{}}
    for k in INP:
        f=idx_of(k,ARMS[0]); d={}
        for a in ARMS:
            i=idx_of(k,a); d[a]=dict(pred_ratio=float(np.exp(F['gam']*(x[i]-x[f]))),meas_ratio=float(np.exp(y[i]-y[f])),meas=float(np.exp(y[i])))
        R['per_input'][k]=d
    R['mean_pred_ratio']={a:float(np.mean([R['per_input'][k][a]['pred_ratio'] for k in INP])) for a in ARMS}
    R['mean_meas_ratio']={a:float(np.mean([R['per_input'][k][a]['meas_ratio'] for k in INP])) for a in ARMS}
    R['pred_order']=sorted(ARMS,key=lambda a:R['mean_pred_ratio'][a]); R['meas_order']=sorted(ARMS,key=lambda a:R['mean_meas_ratio'][a])
    # spearman per input over 5 arms
    R['per_input_spearman_5arms']={k:float(spearmanr([R['per_input'][k][a]['pred_ratio'] for a in ARMS],[R['per_input'][k][a]['meas_ratio'] for a in ARMS])[0]) for k in INP}
    # also the other new arms (N1,N3) in-sample-of-old: pred vs meas diff vs F17
    oth={}
    for k in ['N1','N3']:
        f=idx_of(k,ARMS[0])
        for a in ['F19_A1','F19_A1_LIGHT_C','F17_ORIGINAL_C','F19_A2_LATE4_LIGHT_C','F17_D27_LIGHT_C']:
            i=idx_of(k,a); oth[f'{k}:{a}']=dict(pred_ratio=float(np.exp(F['gam']*(x[i]-x[f]))),meas_ratio=float(np.exp(y[i]-y[f])))
    R['decomp_arms_vs_F17']=oth
    out[model]=R
    print(model,{n:round(v,3) for n,v in F['th'].items()},'gam %.3f'%F['gam'])
    print('  pred',{a:round(v,3) for a,v in R['mean_pred_ratio'].items()}); print('  meas',{a:round(v,3) for a,v in R['mean_meas_ratio'].items()})
    print('  per-input rho',{k:round(v,2) for k,v in R['per_input_spearman_5arms'].items()})
    print('  decomp',{k:(round(v['pred_ratio'],3),round(v['meas_ratio'],3)) for k,v in oth.items()})
# per-step error decomposition for G17 vs G19 under M5f and M1 (mean over 4 inputs, normalized to F17 total)
dec={}
for model in ['M1','M5f']:
    th=out[model]['params']; D={}
    for a in ['F17_A2_LIGHT_C','G17','G19','G22']:
        acc=np.zeros(28)
        for k in INP:
            i=idx_of(k,a); f=idx_of(k,'F17_A2_LIGHT_C'); p=sub(PM,[i]); pf=sub(PM,[f])
            ka=th.get('ka',0); bl=th.get('bl',1.0)
            def per(p):
                fA=np.clip(1-ka*p['al'],0,None); fct=np.where(p['isA'],fA,np.where(p['light']==1,bl,1.0)); e=p['s']*p['drift']*fct
                if 'kr' in th: e=e*th['kr']**(p['age']-1)
                if 'g' in th: e=e*np.maximum(p['sig'],1e-3)**th['g']
                return np.where(p['isD'],0,e)[0]
            acc+=per(p)/per(pf).sum()/4
        D[a]={'steps8_20':float(acc[:13].sum()),'steps21_27':float(acc[13:20].sum()),'steps28_35':float(acc[20:].sum()),'total':float(acc.sum())}
    dec[model]=D; print(model,'share of F17 total error by window',{a:{w:round(v,3) for w,v in d.items()} for a,d in D.items()})
# s(t) early profile for the 4 inputs vs mean
prof={k:{int(t):float(S[k][t]/S['MEAN'][t]) for t in range(8,21)} for k in INP}
print('s/s_mean steps 8-20',{k:[round(prof[k][t],2) for t in range(8,21)] for k in INP})
json.dump(dict(frozen_old=out,error_by_window=dec,s_over_mean_8_20=prof),open('diag.json','w'),indent=1)
