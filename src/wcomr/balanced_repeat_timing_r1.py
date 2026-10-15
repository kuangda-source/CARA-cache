"""Two fixed scenes, five frozen method slots and three balanced repeats."""
import math
from statistics import mean,stdev

SLOTS=('FULL_NATIVE','WORLD_CACHE','RA_CFG_CACHE','GCR_EFFICIENT','CPA_HIGH_FIDELITY')
SCENES=('av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632','human_199')
BASE_ORDERS=((0,1,2,3,4),(4,2,0,3,1),(3,1,4,2,0))
STATUSES={'COMPLETE','TEXT_REJECTED','VIDEO_REJECTED','TECH_FAILED','NOT_REACHED'}

def orders(scene_index):
    if scene_index not in (0,1):raise ValueError('The two original timing scenes are fixed')
    # Relabel the second scene to change predecessor relationships. Every
    # method's sum of positions remains6 (mean2) over its three formal rounds.
    return tuple(tuple(SLOTS[(n+2*scene_index)%5] for n in row) for row in BASE_ORDERS)

def matrix():
    rows=[]
    for i,scene in enumerate(SCENES):
        order=orders(i)
        for position,slot in enumerate(order[1]):
            rows.append(dict(id=f'warm_{i}_{slot}',scene=scene,seed=0,slot=slot,section='WARMUP',round=0,position=position))
        for number,sequence in enumerate(order,1):
            for position,slot in enumerate(sequence):
                rows.append(dict(id=f'timed_{i}_r{number}_{slot}',scene=scene,seed=0,slot=slot,
                    section='TIMED',round=number,position=position))
        if any(sum(sequence.index(s) for sequence in order)!=6 for s in SLOTS):
            raise ValueError('Every method needs the same mean execution position within each scene')
    if len(rows)!=40 or len({r['id'] for r in rows})!=40:raise ValueError('Complete40 timing matrix required')
    return rows

def summaries(rows):
    plan=matrix()
    if len(rows)!=40 or any(any(r.get(k)!=v for k,v in p.items()) for r,p in zip(rows,plan)):
        raise ValueError('All40 original ordered warm/formal positions must be retained')
    if any(r['status'] not in STATUSES for r in rows):raise ValueError('Explicit original terminal status required')
    costs={};qualities={};lookup={(r['scene'],r['slot'],r['round']):r for r in rows}
    parity=[]
    for row in rows:
        if row['section']!='TIMED':continue
        key=(row['scene'],row['slot'],row['round'])
        if row['status'] in ('COMPLETE','VIDEO_REJECTED') and row.get('raw_model_audit')=='PASS':
            value=row.get('core_seconds')
            if (not isinstance(value,(int,float)) or isinstance(value,bool) or not math.isfinite(value) or value<=0
                    or row['audit'] or row['in_timing_hashes'] or row['in_timing_guided_copies'] or row['research_checkpoints']
                    or not row['write_deferred_after_main_timer']):
                raise ValueError('Clean formal clock must exclude research copies/hashes/writes')
            costs[key]=value
        if row['status']=='COMPLETE' and row.get('endpoint_audit')=='PASS':
            warm=lookup[(row['scene'],row['slot'],0)]
            if warm['status']=='COMPLETE' and warm.get('endpoint_audit')=='PASS':
                if any(row[k]!=warm[k] for k in ('final_latent_sha256','actions','A_history')) or (
                        row['decoded_video']['RGB_sha256']!=warm['decoded_video']['RGB_sha256']):
                    raise ValueError('Same input/seed/method repeated a different algorithm endpoint')
                parity.append(dict(id=row['id'],status='PASS_FORMAL_TO_WARM_ENDPOINT_ACTION_HISTORY_RGB'))
            else:parity.append(dict(id=row['id'],status='WARM_PARITY_UNAVAILABLE_REJECTION_OR_FAILURE_RETAINED'))
            lp=row.get('LPIPS')
            if lp is not None:
                ref=lookup[(row['scene'],'FULL_NATIVE',row['round'])]
                if ref['status']!='COMPLETE' or ref.get('endpoint_audit')!='PASS':
                    raise ValueError('All93-frame fidelity needs its registered same-round Native')
                dist=lp['frame_distances']
                if (lp['frames']!=93 or len(dist)!=93 or any(not math.isfinite(v) or v<0 for v in dist)
                        or not math.isclose(mean(dist),lp['mean_LPIPS'],rel_tol=1e-11,abs_tol=1e-12)
                        or lp['reference_sha256']!=ref['video_artifact']['sha256']
                        or lp['candidate_sha256']!=row['video_artifact']['sha256']):
                    raise ValueError('Actual frame mean or matched reference changed')
                qualities[key]=mean(dist)
        elif row.get('LPIPS') is not None:raise ValueError('Rejected or failed output cannot have an accepted score')
    results=[]
    for scene in SCENES:
        for slot in SLOTS:
            rounds=[]
            for n in (1,2,3):
                key=(scene,slot,n);row=lookup[key];time=costs.get(key)
                rounds.append(dict(round=n,position=row['position'],status=row['status'],main_seconds=time,
                    LPIPS=qualities.get(key),speedup_baseline_over_candidate={baseline:
                        costs[(scene,baseline,n)]/time for baseline in SLOTS[:3]
                        if time is not None and (scene,baseline,n) in costs}))
            timed=[r['main_seconds'] for r in rounds if r['main_seconds'] is not None]
            quality=[r['LPIPS'] for r in rounds if r['LPIPS'] is not None]
            results.append(dict(scene=scene,slot=slot,registered_repeats=3,rounds=rounds,
                valid_time_repeats=len(timed),valid_quality_repeats=len(quality),
                complete_repeat_mean_seconds=mean(timed) if len(timed)==3 else None,
                complete_repeat_min_seconds=min(timed) if len(timed)==3 else None,
                complete_repeat_max_seconds=max(timed) if len(timed)==3 else None,
                complete_repeat_sample_std_seconds=stdev(timed) if len(timed)==3 else None,
                complete_repeat_mean_LPIPS=mean(quality) if len(quality)==3 else None))
    contrasts=[]
    for candidate in SLOTS[3:]:
        for baseline in SLOTS[:3]:
            paired=[dict(scene=s,round=n,baseline_seconds=costs[(s,baseline,n)],candidate_seconds=costs[(s,candidate,n)])
                for s in SCENES for n in (1,2,3) if (s,baseline,n) in costs and (s,candidate,n) in costs]
            ratio=sum(r['baseline_seconds'] for r in paired)/sum(r['candidate_seconds'] for r in paired) if paired else None
            contrasts.append(dict(candidate=candidate,baseline=baseline,registered_paired_rounds=6,actual_paired_rounds=len(paired),
                full_registered_speedup=ratio if len(paired)==6 else None,available_paired_round_speedup=ratio,paired_rounds=paired))
    return dict(full_denominator=40,formal_denominator=30,full_warmup_denominator=10,
        scene_methods=results,contrasts=contrasts,formal_to_warm_parity_controls=parity,
        warmups_excluded_from_speed_means=True,algorithm_or_threshold_selected_by_timing=False,
        independent_new_input_or_quality_generalization_claim=False,
        three_repeats_are_not_three_independent_prompts=True)
