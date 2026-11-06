"""S-FAST19 FP64 local moments and fail-closed, common-grammar interfaces.

Missing parent/step coverage cannot become zero risk or an executable S plan.
Legal numerical history support must be supplied independently of risk scores.
"""
import hashlib
import json
import math

import torch

TARGETS = tuple(s for s in range(8, 36) if s != 24)
F19 = tuple(range(1, 9)) + (10,12,14,16,18,20,21,24,27,30,36)
PROTECTED = tuple(range(1, 8)) + (24,36)


def branch_moments(candidate, teacher, *, a=8., b=-7.):
    if len(candidate) != 2 or len(teacher) != 2 or any(x.shape != teacher[0].shape for x in (*candidate,*teacher)):
        raise ValueError('Same-state aligned branch outputs required')
    if any(not x.numel() or not torch.isfinite(x).all() for x in (*candidate,*teacher)):
        raise ValueError('Nonempty finite outputs required')
    c, u = (v.double()-d.double() for v,d in zip(candidate,teacher))
    C, U, K = (float(c.square().mean()), float(u.square().mean()), float((c*u).mean()))
    direct = float((a*c+b*u).square().mean())
    diag = a*a*C+b*b*U
    formula = diag+2*a*b*K
    tolerance = 128*torch.finfo(torch.float64).eps*max(diag, abs(2*a*b*K), 1e-300)
    if abs(direct-formula) > tolerance:
        raise ArithmeticError('FP64 guided identity outside cancellation bound')
    energy = sum(float(d.double().square().mean()) for d in teacher)/2
    if energy <= 0 or not math.isfinite(energy):
        raise ValueError('Positive shared teacher energy required; no hidden epsilon')
    return dict(C=C,U=U,K=K,BR=(C+U)/2,DIAG=diag,CFG=direct,
                CFG_formula=formula,identity_abs_error=abs(direct-formula),identity_tolerance=tolerance,
                teacher_branch_energy=energy,normalization='MEAN_TEACHER_BRANCH_ENERGY',
                normalized=dict(BR=(C+U)/2/energy,DIAG=diag/energy,CFG=direct/energy),
                coefficients=[a,b],reduction_dtype='FP64')


def coverage(rows, prompts, parents):
    expected = {(p,h,t) for p in prompts for h in parents for t in TARGETS}
    actual = [(r['prompt'],r['parent'],r['step']) for r in rows]
    if len(set(actual)) != len(actual) or set(actual)-expected:
        raise ValueError('Duplicate or foreign risk row')
    missing = sorted(expected-set(actual))
    return dict(complete=not missing,expected=len(expected),present=len(actual),
                missing=[dict(prompt=p,parent=h,step=t) for p,h,t in missing])


def aggregate(rows, *, prompts, parent_weights, propagation):
    c = coverage(rows,prompts,tuple(parent_weights))
    if not c['complete']:
        raise ValueError('INCOMPLETE_BRANCH_MOMENTS: %d/%d; no interpolation or zero fill' % (c['present'],c['expected']))
    if set(propagation) != set(TARGETS) or any(not math.isfinite(g) or g < 0 for g in propagation.values()):
        raise ValueError('One shared complete propagation table required')
    if any(w <= 0 or not math.isfinite(w) for w in parent_weights.values()) or not math.isclose(sum(parent_weights.values()),1):
        raise ValueError('Frozen positive normalized parent weights required')
    out = {j:{} for j in ('BR','DIAG','CFG')}
    for t in TARGETS:
        for j in out:
            out[j][t] = sum(parent_weights[r['parent']]*propagation[t]**2*r['moments']['normalized'][j]
                            for r in rows if r['step'] == t)/len(prompts)
    return out


def histories(dense):
    if len(set(dense)) != len(dense) or not set(PROTECTED) <= set(dense) or any(s not in range(1,37) for s in dense):
        raise ValueError('Unique full36 mask and common protected set required')
    past=[];result=[]
    for t in range(1,37):
        if t in dense:
            past.append(t)
        else:
            if len(past) < 2:
                raise ValueError('Two true strictly past D anchors required')
            result.append((t,past[-2],past[-1]))
    return result


def exchanges(*, base=F19, max_age, supports_history):
    """Common legal remove/add syntax, no model/risk dependent screening."""
    if len(base) != 19 or type(max_age) is not int or max_age <= 0:
        raise ValueError('Frozen 19D and positive age bound required')
    histories(base)
    rows=[]
    for remove in sorted(set(base)-set(PROTECTED)):
        for add in sorted(set(TARGETS)-set(base)):
            dense=tuple(sorted((set(base)-{remove})|{add}))
            hs=histories(dense)
            if all(t-last <= max_age and supports_history(t,old,last) for t,old,last in hs):
                rows.append(dict(remove=remove,add=add,dense=list(dense),history=[list(h) for h in hs]))
    return rows


def choose(risk, candidates, *, execution_identity):
    if set(risk) != {'BR','DIAG','CFG'} or any(set(r) != set(TARGETS) for r in risk.values()):
        raise ValueError('Complete common risk support required')
    if not execution_identity:
        raise ValueError('Readout/model/grid/precision/alpha identity required')
    choices={};scores={}
    for j,r in risk.items():
        if any(not math.isfinite(x) or x < 0 for x in r.values()):
            raise ValueError('Finite nonnegative risk required')
        ranked=[dict(c,score=r[c['add']]-r[c['remove']]) for c in candidates]
        ranked.sort(key=lambda c:(-c['score'],c['remove'],c['add']))
        best=ranked[0] if ranked and ranked[0]['score'] > 0 else None
        choices[j]=dict(dense=list(F19) if best is None else best['dense'],exchange=best)
        scores[j]=ranked
    classes={}
    for j,c in choices.items():
        key=hashlib.sha256(json.dumps([execution_identity,c['dense']],sort_keys=True).encode()).hexdigest()
        classes.setdefault(key,[]).append(j)
    return dict(choices=choices,candidate_scores=scores,equivalence_classes=classes,
                endpoint_benefit_established=False,execution_ready=False)
