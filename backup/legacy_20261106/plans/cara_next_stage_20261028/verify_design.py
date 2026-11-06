"""CPU-only synthetic checks for the written design. Not CARA/model evidence."""
from pathlib import Path
import json
import numpy as np

root = Path(__file__).resolve().parent
cfg = json.loads((root/'experiment_registry.json').read_text())
results = []
def check(name, ok, **detail):
    if not bool(ok):
        raise AssertionError(name)
    results.append({'name': name, 'passed': True, **detail})

def age(dense, t):
    older=[s for s in dense if s<t]
    if not older:
        raise ValueError('No historical true anchor')
    return t-max(older)

m = cfg['masks']
protected = set(range(1,8))|{24,36}
for name,n in [('Shared25_C',25),('F19',19),('F18',18)]:
    d=m[name]
    check(name+'_count', len(d)==n and len(set(d))==n and d==sorted(d))
    check(name+'_protected', protected<=set(d))
    check(name+'_supported_age', max(age(d,t) for t in range(2,37) if t not in d)<=6)
for layout, a_key in [('F19','F19_A1'),('F18','F18_A1')]:
    check(layout+'_A1', all(t not in m[layout] and age(m[layout],t)==1 for t in m[a_key]))
check('F18_step9_is_age2_C', age(m['F18'],9)==2 and 9 not in m['F18_A1'])
asset=next(c for c in cfg['cards'] if c['id']=='A-SQ-FAST')
check('targets27',len(asset['targets'])==27)
check('labels108',len(asset['targets'])*2*2==asset['formal_state_labels'])
extra=sum(sum(t not in m[name] for t in asset['targets']) for name in ['Shared25_C','F19'])*2
check('shadow56',extra==56==asset['max_extra_dense_pairs'])
check('parents10',asset['on_paths']+asset['off_paths_max']+asset['warm_paths_max']==10)
fast=next(c for c in cfg['cards'] if c['id']=='F19')
check('F19_full_scope56',sum(fast[k] for k in ['formal_paths_max','tuning_paths_max','warm_paths_max','repeat_paths_max','control_paths_max'])==56)

b0=set(m['F19'])
i={'remove':10,'add':9}; j={'remove':27,'add':23}
for name, edits in [('i',[i]),('j',[j]),('ij',[i,j])]:
    d=set(b0)
    for e in edits:
        check('swap_'+name+'_identity_'+str(e['remove']),e['remove'] in d and e['add'] not in d)
        d.remove(e['remove']);d.add(e['add'])
    check('swap_'+name+'_legal',len(d)==19 and protected<=d and max(age(d,t) for t in range(2,37) if t not in d)<=6)

rng=np.random.default_rng(20261028)
ec,eu=rng.normal(size=(2,5000))
C,U,K=np.mean(ec*ec),np.mean(eu*eu),np.mean(ec*eu)
q=64*C+49*U-112*K
check('guided_moments',np.isclose(q,np.mean((8*ec-7*eu)**2),rtol=1e-12))
em=(ec+eu)/2;ed=ec-eu
check('common_difference_energy',np.isclose(q,np.mean(em*em)+56.25*np.mean(ed*ed)+15*np.mean(em*ed),rtol=1e-12))

Jc=rng.normal(size=(11,17)); Ju=rng.normal(size=(11,17))
a=rng.normal(size=17);b=rng.normal(size=17)
left=8*Jc@(a+b/2)-7*Ju@(a-b/2)
right=(8*Jc-7*Ju)@a+(4*Jc+3.5*Ju)@b
check('hidden_codec_jacobian',np.allclose(left,right,rtol=1e-12,atol=1e-12))

E,di,dj=rng.normal(size=(3,400))
loss=lambda x:float(np.dot(x,x))
check('terminal_single_identity',np.isclose(loss(E+di)-loss(E),2*np.dot(E,di)+loss(di)))
check('terminal_pair_identity',np.isclose(loss(E+di+dj)-loss(E+di)-loss(E+dj)+loss(E),2*np.dot(di,dj)))

# Predictive encoding uses a common reconstructed anchor; no model inference.
Rprev=rng.normal(size=512);R=rng.normal(size=512)
prev_hat=np.round(Rprev/.1)*.1
Delta=R-prev_hat
Qdelta=np.round(Delta/.05)*.05
Rhat=prev_hat+Qdelta
check('synchronized_predictive_codec_identity',np.allclose(Rhat-R,Qdelta-Delta,atol=1e-14))

pool=sum(cfg['planning_pools_GPUh'].values())
check('planning_pool_sum',abs(pool-cfg['facts']['last_known_available'])<1e-10,total=pool)
check('no_execution_authorized',not cfg['gpu_authorized'] and cfg['gpu_submissions']==0 and cfg['new_budget_reserved_GPUh']==0)

out={'kind':'SYNTHETIC_CPU_DESIGN_CHECK_ONLY','seed':20261028,'GPU_initialized':False,'model_loaded':False,'scientific_model_results':False,'checks':results,'all_passed':True}
(root/'design_check_results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(f'{len(results)} design checks passed; no model or GPU execution.')
