"""Fixed confirmation test and s*delta-v reconstruction. No outcome tuning."""
import argparse
from functools import lru_cache
import itertools
import json
import math
from pathlib import Path
import statistics


def permutation_test(old,new,margin=0.):
    """One-sided lower-tail exact shift test of new-old >= margin."""
    shifted=[v-margin for v in new]
    pooled=list(old)+shifted;n=len(new)
    observed=statistics.mean(shifted)-statistics.mean(old)
    differences=[]
    for indices in itertools.combinations(range(len(pooled)),n):
        selected=set(indices)
        a=[v for i,v in enumerate(pooled) if i in selected]
        b=[v for i,v in enumerate(pooled) if i not in selected]
        differences.append(statistics.mean(a)-statistics.mean(b))
    return sum(v<=observed+1e-12 for v in differences)/len(differences)


def reconstruct(weights,nD):
    """Minimize (max interval weighted-age mass, sum squared masses, dense tuple)."""
    def cost(a,b):return sum((t-a)*weights[t-1] for t in range(a+1,b))
    # First find the exact minimum peak; then minimize squared mass at that peak.
    possible=sorted({cost(a,b) for a in range(7,36) for b in range(a+1,37)})
    def at_peak(limit):
        @lru_cache(None)
        def dp(last,remaining):
            if remaining==0:
                c=cost(last,36)
                return (c*c,(36,)) if c<=limit else None
            best=None
            for d in range(last+1,36-remaining+1):
                c=cost(last,d)
                if c>limit:continue
                tail=dp(d,remaining-1)
                if tail is not None:
                    candidate=(c*c+tail[0],(d,)+tail[1])
                    if best is None or candidate<best:best=candidate
            return best
        return dp(7,nD-8)
    lo,hi=0,len(possible)-1
    while lo<hi:
        mid=(lo+hi)//2
        if at_peak(possible[mid]) is None:lo=mid+1
        else:hi=mid
    result=at_peak(possible[lo])
    dense=list(range(1,8))+list(result[1])
    age=0;scores={}
    for t in range(8,36):
        age=0 if t in dense else age+1
        if t not in dense:scores[t]=age*weights[t-1]
    A=sorted(scores,key=lambda t:(-scores[t],t))[:10] if nD==17 else []
    return dict(dense_steps=dense,A_steps=sorted(A),peak=possible[lo],sum_square=result[0])


def interpolate(values):
    out=[0.]*36
    for t in range(8,36):
        if t>=34:out[t-1]=values[34]
        else:
            a=t if t%2==0 else t-1;b=a+2
            out[t-1]=values[a]+(t-a)/2*(values[b]-values[a])
    return out


def analyze(card,collection,scores,old_scores,root):
    formal=[r for r in collection['rows'] if r['slot']['section']=='c']
    time={(r['slot']['member'],r['slot']['role']):r['result']['T_DD'] for r in formal}
    new_lp=[r['result']['Alex'] for r in scores['LPIPS'] if r['slot']['role']=='F17_A2_LIGHT_C']
    old_lp=[r['result']['Alex'] for r in old_scores['LPIPS'] if r['role']=='F17_A2_LIGHT_C']
    means={role:statistics.mean(time[m,role] for m in card['new_confirm']) for role in card['roles']}
    speed=means['NATIVE35']/means['F17_A2_LIGHT_C']
    quality={(r['planned']['case_id'],r['planned']['role'],r['planned']['dimension']):r['result']['value']
             for r in scores['quality_rows']}
    gates=[]
    for reference in ('NATIVE35','F19_A1'):
        for dimension,minimum in card['quality']['independent_quality_min_differences'].items():
            difference=statistics.mean(quality[m,'F17_A2_LIGHT_C',dimension]-quality[m,reference,dimension]
                                       for m in card['new_confirm'])
            gates.append(dict(reference=reference,dimension=dimension,difference=difference,minimum=minimum,passed=difference>=minimum))
    p=permutation_test(old_lp,new_lp,margin=.027)
    result=dict(latent_controls=[dict(slot=r['slot'],**r['result']['latent_bridge']) for r in collection['rows'] if 'latent_bridge' in r['result']],
        RGB_controls=scores.get('RGB_controls',[]),speedup_T_DD=speed,mean_LPIPS_new=statistics.mean(new_lp),mean_LPIPS_old=statistics.mean(old_lp),
        NI_margin=.027,NI_permutation_p=p,NI_passed=p<=.05,quality_gates=gates,
        confirmation_passed=speed>=1.9 and means['F17_A2_LIGHT_C']<=133 and statistics.mean(new_lp)<=.27
            and p<=.05 and all(g['passed'] for g in gates))
    if card['counts']['b']==0:
        return dict(result,sensitivity_status='PENDING_ORIGINAL_CARD')
    fit_s={t:statistics.mean(math.sqrt(r['latent_MSE'])/max(r['local_guided_delta_RMS'],1e-12)
        for r in scores['sensitivity'] if r['member'] in card['FIT'] and r['t']==t) for t in card['sensitivity_steps']}
    sensitivity=interpolate(fit_s);predictions={}
    # FIT sensitivity curve is transferred unchanged to all six non-FIT inputs.
    for member in card['old_CHECK']+card['new_confirm']:
        source=Path(card['reuse']['output_root']) if 'reuse' in card and member in card['reuse']['members'] else Path(root)
        metrics=json.loads((source/'native_states'/member/'metrics.json').read_text())
        weights=[0. if row['step'] in (*range(1,8),36) else sensitivity[row['step']-1]*row['guided_delta_RMS'] for row in metrics]
        scale=statistics.mean(weights[7:35]);weights=[v/scale for v in weights]
        predictions[member]={str(n):reconstruct(weights,n) for n in (16,17,19,22,25)}
        prediction=predictions[member]['17']
        reference=card['roles']['F17_A2_LIGHT_C']['policy']['actions']
        D={t for t in range(8,36) if reference[t-1]=='D'}
        A={t for t in range(8,36) if reference[t-1]=='A'}
        actualD=set(prediction['dense_steps']);actualA=set(prediction['A_steps'])
        referenceC={t for t in range(1,37) if reference[t-1]=='C'}
        actualC=set(range(1,37))-actualD-actualA
        prediction.update(freeD_overlap=len(D&actualD),A_overlap=len(A&actualA),
            DAC_Hamming=sum(('D' if t in actualD else 'A' if t in actualA else 'C')!=reference[t-1] for t in range(1,37)),
            C_Jaccard=len(referenceC&actualC)/len(referenceC|actualC))
    return dict(result,
        FIT_sensitivity=fit_s,non_FIT_reconstruction=predictions,
        principle_supported=statistics.median(p['17']['freeD_overlap'] for p in predictions.values())>=7
            and statistics.median(p['17']['A_overlap'] for p in predictions.values())>=7,
        interpretation='Four new inputs, seed0. Inconclusive NI is not confirmation; reconstructed masks are analysis, never an automatic GPU candidate.')


def reuse_confirmation(card,collection,scores):
    """Merge the released F17 measurements; its scientific verdict is unchanged."""
    read=lambda path:json.loads(Path(path).read_text())
    source=card['reuse_confirmation'];release=read(source['release'])
    if release['launch_id']!=source['launch_id'] or not all(release[k] for k in
            ('GPU_released','mode_restored','cost_settled','original_processes_ended','container_exit_success')):
        raise ValueError('Original F17 card must be successfully released and settled')
    confirmation=read(source['collection']);accepted=read(source['scores'])
    if (confirmation['scope_sha256']!=source['scope_sha256'] or accepted['scope_sha256']!=source['scope_sha256']
            or accepted['status']!='COMPLETE_PENDING_ANALYSIS'):
        raise ValueError('Original F17 scoring scope or completeness differs')
    collection=dict(collection,rows=collection['rows']+[r for r in confirmation['rows'] if r['slot']['section']=='c'])
    scores=dict(scores,LPIPS=scores['LPIPS']+accepted['LPIPS'],quality_rows=accepted['quality_rows'])
    return collection,scores


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for key in ('manifest','collection','scores','old-scores','root','output'):p.add_argument('--'+key,type=Path,required=True)
    args=p.parse_args();read=lambda path:json.loads(path.read_text())
    card=read(args.manifest);collection=read(args.collection);scores=read(args.scores)
    collection=dict(collection,rows=collection.get('carried_rows',[])+collection['rows'])
    if 'reuse_confirmation' in card:collection,scores=reuse_confirmation(card,collection,scores)
    result=analyze(card,collection,scores,read(args.old_scores),args.root)
    with args.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
