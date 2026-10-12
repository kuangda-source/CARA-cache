"""Offline moment calibration with explicit units, cells and missing fits.

No generator, teacher calls, endpoint tuning or deployment state mutation.
The shared scale on birth/drift root proxies is an empirical tied-scale
version of the registered source model, not a covariance/error bound.
"""
import math
from statistics import mean,median

LABELS=('C','D_REFERENCE_A','FUSION_A','NEW_P')
CELLS={('D','EARLY'),('D','LATE'),('P','EARLY'),('P','LATE')}


def finite(value):return type(value) in (int,float) and math.isfinite(value) and value>=0


def cell(point,grouping):
    s=point['selection'];key=(s['source'],s['phase'])
    if key not in CELLS:raise ValueError('Known actual source and step25 phase required')
    if grouping=='SOURCE_PHASE':return '_'.join(key)
    if grouping=='SOURCE':return key[0]
    raise ValueError('Only source or source-phase grouping registered')


def feature(point):
    d=point['actual_C_paid_proxy'];state=point['parent_pre_action']
    delta=d['local_proxy'];floor=state[3]
    if (not finite(delta) or not finite(floor) or state[1]!=point['selection']['source']
            or state[1]=='D' and floor!=0):raise ValueError('Actual paid root proxy/source floor required')
    return (delta+floor)**2


def fit(points,grouping='SOURCE_PHASE',target='absolute_guided_MSE'):
    if target not in ('absolute_guided_MSE','normalized_guided_MSE'):raise ValueError('Explicit target units required')
    groups={}
    for p in points:
        key=cell(p,grouping);groups.setdefault(key,[]).append(p)
        if any(not finite(p['losses'][a][target]) for a in LABELS):raise ValueError('All four finite actual labels required')
    out={}
    for key,rows in groups.items():
        xs=mean(feature(p) for p in rows);q={a:mean(p['losses'][a][target] for p in rows) for a in LABELS}
        ready=xs>0 and q['C']>0
        out[key]={'status':'FIT' if ready else 'UNKNOWN_ZERO_FEATURE_OR_C_TARGET',
            'C_scale':q['C']/xs if ready else None,
            'A_ratios':{a:q[a]/q['C'] if ready else None for a in ('D_REFERENCE_A','FUSION_A')},
            'actual_NEW_P_birth_mean':q['NEW_P'],'mean_feature':xs,'mean_targets':q,
            'training_points':len(rows),'training_scenes':sorted({p['selection']['scene'] for p in rows})}
    return {'grouping':grouping,'target':target,'cells':out,'current_teacher_energy_is_online_feature':False}


def predict(model,point):
    c=model['cells'].get(cell(point,model['grouping']))
    if c is None or c['status']!='FIT':return None
    q=c['C_scale']*feature(point)
    return {'C':q,'D_REFERENCE_A':q*c['A_ratios']['D_REFERENCE_A'],
            'FUSION_A':q*c['A_ratios']['FUSION_A'],'NEW_P':c['actual_NEW_P_birth_mean'],'D':0.}


def action_prices(parameters,source):
    c=parameters['cost_seconds'];small=c['C']+(c['A']-c['C'])/2
    return {'C':c['C'],'D_REFERENCE_A':small,'FUSION_A':small if source=='D' else c['A'],
        'NEW_P':c['P'],'D':c['D']}


def intervals(prices,risks):
    if set(prices)!=set(risks) or any(not finite(v) for v in list(prices.values())+list(risks.values())):
        raise ValueError('Finite same-boundary prices and same-unit risks required')
    out={}
    for a in prices:
        lo,hi=0.,math.inf;empty=False
        for b in prices:
            if a==b:continue
            dq=risks[a]-risks[b];dc=prices[b]-prices[a]
            if dq>0:hi=min(hi,dc/dq)
            elif dq<0:lo=max(lo,dc/dq)
            elif dc<0:empty=True
        valid=not empty and hi>=lo and hi>=0
        out[a]={'nonempty':valid,'positive_width':valid and hi>lo,
            'lower':lo if valid else None,'upper':hi if valid and math.isfinite(hi) else None,
            'upper_infinite':valid and math.isinf(hi)}
    return out


def choose(prices,risks,lam):
    if not finite(lam):raise ValueError('Finite nonnegative lambda required')
    return min(prices,key=lambda a:(prices[a]+lam*risks[a],a))


def squared_gain(point):
    g=point['actual_C_paid_proxy']['gain']
    if not finite(g):raise ValueError('Bound actual propagation gain required')
    return g*g


def lambda_grid(train,model,parameters):
    crossings=[]
    for p in train:
        q=predict(model,p)
        if q is None:continue
        prices=action_prices(parameters,p['selection']['source']);risk={a:v*squared_gain(p) for a,v in q.items()}
        keys=sorted(q)
        for i,a in enumerate(keys):
            for b in keys[i+1:]:
                dq=risk[a]-risk[b]
                if dq:
                    v=(prices[b]-prices[a])/dq
                    if math.isfinite(v) and v>0:crossings.append(v)
    if not crossings:return None
    base=median(crossings)
    return [base*f for f in (.25,1.,4.)]


def validate_complete(points):
    scenes={p['selection']['scene'] for p in points}
    if len(points)!=16 or len(scenes)!=4:raise ValueError('All16 real points/four scenes required; no partial fit')
    for scene in scenes:
        rows=[p for p in points if p['selection']['scene']==scene]
        if len(rows)!=4 or {(p['selection']['source'],p['selection']['phase']) for p in rows}!=CELLS:
            raise ValueError('Complete four cells per scene required')
        for p in rows:
            feature(p);squared_gain(p)
            n=p['selection']['chosen']['step']
            if p['selection']['phase']!=('EARLY' if n<25 else 'LATE'):raise ValueError('Actual current phase changed')
    return sorted(scenes)


def analyze(points,parameters):
    scenes=validate_complete(points);models={g:fit(points,g) for g in ('SOURCE','SOURCE_PHASE')}
    summaries=[]
    for key in sorted(models['SOURCE_PHASE']['cells']):
        rows=[p for p in points if cell(p,'SOURCE_PHASE')==key]
        summaries.append({'cell':key,'points':4,
            'C_mean_absolute_MSE':mean(p['losses']['C']['absolute_guided_MSE'] for p in rows),
            'new_P_birth_mean_absolute_MSE':mean(p['losses']['NEW_P']['absolute_guided_MSE'] for p in rows),
            'A_better_than_C_counts':{a:sum(p['losses'][a]['absolute_guided_MSE']<p['losses']['C']['absolute_guided_MSE'] for p in rows) for a in ('D_REFERENCE_A','FUSION_A')},
            'actual_ratios':[{a:p['losses'][a]['absolute_guided_MSE']/p['losses']['C']['absolute_guided_MSE'] if p['losses']['C']['absolute_guided_MSE']>0 else None for a in ('D_REFERENCE_A','FUSION_A')} for p in rows]})
    folds=[]
    for scene in scenes:
        train=[p for p in points if p['selection']['scene']!=scene];test=[p for p in points if p['selection']['scene']==scene]
        fitted={g:fit(train,g) for g in models};grid=lambda_grid(train,fitted['SOURCE_PHASE'],parameters);held=[]
        for p in test:
            prices=action_prices(parameters,p['selection']['source'])
            actual={a:p['losses'][a]['absolute_guided_MSE'] for a in LABELS};actual['D']=0.
            risk={a:q*squared_gain(p) for a,q in actual.items()};evaluated=[]
            for grouping,model in fitted.items():
                q=predict(model,p)
                score={'grouping':grouping,'prediction':q,'unknown':q is None,'lambda_decisions':[]}
                if q is not None:
                    score['squared_prediction_errors']={a:(q[a]-actual[a])**2 for a in LABELS}
                    pred={a:v*squared_gain(p) for a,v in q.items()}
                    score['estimated_intervals']=intervals(prices,pred)
                    if grid:
                        for lam in grid:
                            action=choose(prices,pred,lam);oracle=choose(prices,risk,lam)
                            regret=prices[action]+lam*risk[action]-prices[oracle]-lam*risk[oracle]
                            assert regret>=-1e-10
                            score['lambda_decisions'].append({'lambda':lam,'chosen':action,'same_state_local_oracle':oracle,'regret_seconds_plus_weighted_local_MSE':max(0.,regret)})
                evaluated.append(score)
            held.append({'selection':p['selection'],'teacher_intervals':intervals(prices,risk),
                'prices_transfer_not_new_clean_timing':prices,'predictions':evaluated})
        folds.append({'held_scene':scene,'training_scenes':sorted({p['selection']['scene'] for p in train}),
            'lambda_grid_from_training_ONLY':grid,'models':fitted,'held_rows':held})
    return {'models':models,'cell_summaries':summaries,'leave_one_scene_out':folds,
        'frozen_gamma_previously_fitted_all_CAL':True,'not_independent_method_generalization':True,
        'model_current_teacher_energy_online_input':False,'new_lambda_not_endpoint_working_point':True,
        'prices_old_postprobe_head_transfer_NOT_this_full_pair_timer':True,
        'not_terminal_LPIPS_or_probability_error_bound':True}
