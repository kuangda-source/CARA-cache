import sys,json,time;sys.path.insert(0,'.');from common import *
from multiprocessing import Pool
rows=load_rows(); EV=[r for r in rows if not r['single']]
PM=stack([prep(r) for r in EV]); y=np.log([r['LPIPS'] for r in EV])
G=sorted({r['group'] for r in EV}); gidx=np.array([G.index(r['group']) for r in EV])
LK=sorted({r['lkey'] for r in EV}); lidx=np.array([LK.index(r['lkey']) for r in EV])
isnew=np.array([r['new'] for r in EV]); N=len(EV)
INP=['O1','O3','N1','N3']; ARMS=['F17_A2_LIGHT_C','G17','G17_TAIL','G19','G22']
def idx_of(inp,lay): return [i for i,r in enumerate(EV) if r['input']==inp and r['batch']=='H' and r['layout']==lay][0]
GL=sorted({lidx[idx_of('O1',a)] for a in ARMS[1:]})
def pred_from(F,te): x=logE(F['th'],sub(PM,te)); return np.array([F['gam']*xi+F['b'].get(int(gidx[i]),0.0) for xi,i in zip(x,te)])
def lolo_one(args):
    model,L=args; te=np.where(lidx==L)[0]; tr=np.where(lidx!=L)[0]
    F=fit(model,PM,y,gidx,tr); return te,pred_from(F,te)
def g_check(pred):
    R={}
    for k in INP:
        f=idx_of(k,ARMS[0]); R[k]={a:dict(pred_ratio=float(np.exp(pred[idx_of(k,a)]-pred[f])),meas_ratio=float(np.exp(y[idx_of(k,a)]-y[f]))) for a in ARMS}
    mp={a:float(np.mean([R[k][a]['pred_ratio'] for k in INP])) for a in ARMS}; mm={a:float(np.mean([R[k][a]['meas_ratio'] for k in INP])) for a in ARMS}
    four=['F17_A2_LIGHT_C','G17','G19','G22']
    po=sorted(four,key=lambda a:mp[a]); mo=sorted(four,key=lambda a:mm[a])
    per_in={k:float(spearmanr([R[k][a]['pred_ratio'] for a in four],[R[k][a]['meas_ratio'] for a in four])[0]) for k in INP}
    g19_worst=sum(max(four,key=lambda a:R[k][a]['pred_ratio'])=='G19' for k in INP)
    # pairwise sign accuracy among the 5 arms per input
    sa=[];
    for k in INP:
        for a,b in itertools.combinations(ARMS,2):
            sa.append(np.sign(R[k][a]['pred_ratio']-R[k][b]['pred_ratio'])==np.sign(R[k][a]['meas_ratio']-R[k][b]['meas_ratio']))
    return dict(per_input=R,mean_pred_ratio=mp,mean_meas_ratio=mm,pred_order_4=po,meas_order_4=mo,order_correct=po==mo,
                spearman_4arms_per_input=per_in,G19_pred_worst_inputs=g19_worst,pair_sign_acc_5arms=float(np.mean(sa)))
if __name__=='__main__':
    MODELSRUN=sys.argv[1].split(',') if len(sys.argv)>1 else ['M0','M1','M5f','M5','M0A','M1A','M5fA','M5fF','M5fAF','M5A']
    out={'n_eval_points':N,'n_layouts':len(LK),'n_groups':len(G),'n_new_points':int(isnew.sum()),'models':{}}
    old=~isnew; oldpairs_sel=old
    with Pool(8) as pool:
        for model in MODELSRUN:
            t0=time.time()
            Fall=fit(model,PM,y,gidx,np.arange(N))
            lolo=np.zeros(N)
            for te,p in pool.map(lolo_one,[(model,L) for L in range(len(LK))]): lolo[te]=p
            # prospective: hold out all 4 G layouts at once
            tr=np.where(~np.isin(lidx,GL))[0]; Fp=fit(model,PM,y,gidx,tr); pros=pred_from(Fp,np.arange(N))
            # old-data-only fit (frozen) predictions
            Fo=fit(model,PM,y,gidx,np.where(old)[0]); froz=pred_from(Fo,np.arange(N))
            R=dict(n_params=len(MODELS[model]),params_all=Fall['th'],gamma_all=Fall['gam'],params_excl_G=Fp['th'],params_old_only=Fo['th'],
                   LOLO_paired_all=paired(lolo,y,gidx),LOLO_paired_old_points=paired(lolo,y,gidx,old),LOLO_paired_new_groups_H_O1O3N1N3=paired(lolo,y,gidx,np.isin(gidx,[G.index('H:'+k) for k in INP])),
                   LOLO_pooled_spearman=float(spearmanr(lolo,y)[0]),
                   G_LOLO=g_check(lolo),G_prospective_exclG=g_check(pros),G_frozen_old=g_check(froz))
            out['models'][model]=R
            g=R['G_LOLO']; gp=R['G_prospective_exclG']
            print(f"{model:6s} np={R['n_params']} LOLOpaired={R['LOLO_paired_all'][0]:.3f} (old {R['LOLO_paired_old_points'][0]:.3f}, H4 {R['LOLO_paired_new_groups_H_O1O3N1N3'][0]:.3f}) "
                  f"| LOLO G order {g['pred_order_4']} ok={g['order_correct']} G19worst={g['G19_pred_worst_inputs']}/4 sign5={g['pair_sign_acc_5arms']:.2f} "
                  f"| pros order {gp['pred_order_4']} G19worst={gp['G19_pred_worst_inputs']}/4 sign5={gp['pair_sign_acc_5arms']:.2f} | {time.time()-t0:.0f}s",flush=True)
            print('      params',{k:round(v,3) for k,v in Fall['th'].items()},'| LOLO mean pred ratio',{a[:5]:round(v,3) for a,v in g['mean_pred_ratio'].items()},flush=True)
            np.save(f'lolo_{model}.npy',lolo)
    out['measured_mean_ratio']=out['models'][MODELSRUN[0]]['G_LOLO']['mean_meas_ratio']
    import os
    if os.path.exists('refit_models.json'):
        o=json.load(open('refit_models.json')); o['models'].update(out['models']); out['models']=o['models']
    json.dump(out,open('refit_models.json','w'),indent=1,default=float)
