"""Prompt-grouped final evaluation; never select a method from test outputs."""
import math
import random
from statistics import mean

STATUSES={'COMPLETE','TEXT_REJECTED','VIDEO_REJECTED','TECH_FAILED','NOT_REACHED'}

def number(x):return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)

def percentile(values,p):
    values=sorted(values);at=(len(values)-1)*p;left=int(at);right=min(left+1,len(values)-1)
    return values[left]+(values[right]-values[left])*(at-left)

def interval(values):return [percentile(values,.025),percentile(values,.975)]

def analyze(cases,methods,rows,comparisons,*,reference_method,frames=93,bootstrap_repetitions=4096,bootstrap_seed=20261016):
    """Cases explicitly bind request IDs to prompt groups and original seeds.

    The complete registered matrix is supplied separately from observations.
    Missing rows must be present as NOT_REACHED; missing seeds never become
    one-seed primary prompt estimates. Timing and quality cohorts stay explicit.
    """
    if (len(cases)!=16 or len({c['id'] for c in cases})!=16 or len(set(methods))!=len(methods)
            or reference_method not in methods or bootstrap_repetitions<1 or frames<1):
        raise ValueError('Whole registered eight-prompt two-seed matrix required')
    prompts=sorted({c['prompt_id'] for c in cases})
    if len(prompts)!=8:raise ValueError('Prompt groups, not frames or seeds, are the statistical units')
    for prompt in prompts:
        if sorted(c['seed'] for c in cases if c['prompt_id']==prompt)!=[17,43]:
            raise ValueError('Both frozen seeds per original prompt required')
    expected={(c['id'],m) for c in cases for m in methods}
    indexed={(r['case_id'],r['method']):r for r in rows}
    if len(rows)!=len(indexed) or set(indexed)!=expected:
        raise ValueError('Keep every rejected, failed and unreached matrix position')
    if len(set(tuple(c) for c in comparisons))!=len(comparisons) or any(
            len(c)!=2 or any(m not in methods for m in c) for c in comparisons):
        raise ValueError('Distinct preregistered candidate/baseline comparisons required')
    values={};statuses=[]
    for c in cases:
        ref=indexed[(c['id'],reference_method)]
        ref_good=ref['status']=='COMPLETE' and ref.get('endpoint_audit')=='PASS'
        for method in methods:
            row=indexed[(c['id'],method)];status=row['status']
            if status not in STATUSES:raise ValueError('Explicit original terminal status required')
            seconds=row.get('core_seconds');cost=None;quality=None
            if status in ('COMPLETE','VIDEO_REJECTED') and row.get('raw_model_audit')=='PASS':
                if not number(seconds) or seconds<=0:raise ValueError('Complete observed compute needs a positive timer')
                cost=seconds
            lp=row.get('LPIPS')
            if lp is not None:
                if status!='COMPLETE' or row.get('endpoint_audit')!='PASS' or not ref_good:
                    raise ValueError('LPIPS requires accepted candidate and registered matched Native')
                dist=lp['frame_distances']
                if lp['frames']!=frames or len(dist)!=frames or any(not number(x) or x<0 for x in dist):
                    raise ValueError('All registered frames with finite nonnegative scores required')
                quality=mean(dist)
                if not math.isclose(quality,lp['mean_LPIPS'],rel_tol=1e-11,abs_tol=1e-12):
                    raise ValueError('Whole-video mean differs from actual frame scores')
                if (lp['reference_sha256']!=ref['video_artifact']['sha256']
                        or lp['candidate_sha256']!=row['video_artifact']['sha256']):
                    raise ValueError('Reference input/seed identity differs')
            values[(c['id'],method)]={'time':cost,'quality':quality}
            statuses.append(dict(case_id=c['id'],prompt_id=c['prompt_id'],seed=c['seed'],method=method,
                original_status=status,time_available=cost is not None,quality_available=quality is not None))
    def prompt_value(prompt,method,field):
        v=[values[(c['id'],method)][field] for c in cases if c['prompt_id']==prompt]
        return mean(v) if all(x is not None for x in v) else None
    method_rows=[]
    for method in methods:
        per_prompt=[dict(prompt_id=p,time=prompt_value(p,method,'time'),LPIPS=prompt_value(p,method,'quality')) for p in prompts]
        times=[r['time'] for r in per_prompt if r['time'] is not None]
        losses=[r['LPIPS'] for r in per_prompt if r['LPIPS'] is not None]
        method_rows.append(dict(method=method,registered_prompts=8,registered_seed_cases=16,
            complete_two_seed_time_prompts=len(times),complete_two_seed_quality_prompts=len(losses),
            full_registered_mean_seconds=mean(times) if len(times)==8 else None,
            full_registered_mean_LPIPS=mean(losses) if len(losses)==8 else None,
            available_complete_prompt_mean_seconds=mean(times) if times else None,
            available_complete_prompt_mean_LPIPS=mean(losses) if losses else None,prompt_rows=per_prompt))
    results=[]
    for candidate,baseline in comparisons:
        quality=[];times=[];joint=[]
        for prompt in prompts:
            qc,qb=prompt_value(prompt,candidate,'quality'),prompt_value(prompt,baseline,'quality')
            tc,tb=prompt_value(prompt,candidate,'time'),prompt_value(prompt,baseline,'time')
            if qc is not None and qb is not None:quality.append(dict(prompt_id=prompt,candidate=qc,baseline=qb,change=qc-qb))
            if tc is not None and tb is not None:times.append(dict(prompt_id=prompt,candidate=tc,baseline=tb))
            if None not in (qc,qb,tc,tb):joint.append(dict(prompt_id=prompt,candidate_LPIPS=qc,baseline_LPIPS=qb,candidate_seconds=tc,baseline_seconds=tb))
        rng=random.Random(bootstrap_seed)
        qboot=[];relative_boot=[];tboot=[]
        for _ in range(bootstrap_repetitions):
            if quality:
                sample=[quality[rng.randrange(len(quality))] for _ in quality]
                qboot.append(mean(r['change'] for r in sample))
                denominator=sum(r['baseline'] for r in sample)
                if denominator>0:
                    relative_boot.append(100*(sum(r['candidate'] for r in sample)/denominator-1))
            if times:
                sample=[times[rng.randrange(len(times))] for _ in times]
                tboot.append(sum(r['baseline'] for r in sample)/sum(r['candidate'] for r in sample))
        loss=mean(r['change'] for r in quality) if quality else None
        denominator=sum(r['baseline'] for r in quality)
        relative=100*(sum(r['candidate'] for r in quality)/denominator-1) if denominator>0 else None
        speed=sum(r['baseline'] for r in times)/sum(r['candidate'] for r in times) if times else None
        results.append(dict(candidate=candidate,baseline=baseline,registered_prompt_denominator=8,
            quality_complete_prompt_ids=[r['prompt_id'] for r in quality],time_complete_prompt_ids=[r['prompt_id'] for r in times],
            missing_quality_prompt_ids=[p for p in prompts if p not in {r['prompt_id'] for r in quality}],
            missing_time_prompt_ids=[p for p in prompts if p not in {r['prompt_id'] for r in times}],
            full_registered_mean_LPIPS_change=loss if len(quality)==8 else None,
            full_registered_LPIPS_change_percent=relative if len(quality)==8 else None,
            full_registered_speedup_sum_baseline_over_sum_candidate=speed if len(times)==8 else None,
            full_registered_LPIPS_change_prompt_bootstrap95=interval(qboot) if len(quality)==8 else None,
            full_registered_LPIPS_change_percent_prompt_bootstrap95=interval(relative_boot)
                if len(quality)==8 and len(relative_boot)==bootstrap_repetitions else None,
            full_registered_speedup_prompt_bootstrap95=interval(tboot) if len(times)==8 else None,
            available_complete_prompt_LPIPS_change=loss,available_complete_prompt_speedup=speed,
            available_complete_prompt_LPIPS_change_percent=relative,
            available_cohort_LPIPS_change_prompt_bootstrap95=interval(qboot) if quality else None,
            available_cohort_speedup_prompt_bootstrap95=interval(tboot) if times else None,
            prompt_quality_rows=quality,prompt_time_rows=times,joint_quality_cost_prompt_rows=joint,
            joint_paired_cohort_speedup=sum(r['baseline_seconds'] for r in joint)/sum(r['candidate_seconds'] for r in joint) if joint else None,
            joint_paired_cohort_mean_LPIPS_change=mean(r['candidate_LPIPS']-r['baseline_LPIPS'] for r in joint) if joint else None,
            no_test_winner_selection=True,available_cohorts_do_not_replace_registered_test=True))
    return dict(status='FROZEN_SHARED_MATRIX_PROMPT_GROUPED_STATISTICS',registered_formal_denominator=len(expected),
        registered_prompt_groups=8,seed_cases=16,frames_per_video=frames,methods=method_rows,comparisons=results,
        original_statuses=statuses,bootstrap=dict(unit='PROMPT_WITH_BOTH_REGISTERED_SEEDS',seed=bootstrap_seed,
            repetitions=bootstrap_repetitions,interval='95_PERCENTILE',frames_resampled_as_independent=False),
        final_method_or_GPU_card_selected_by_this_function=False,method_training=False,GPU_submissions=0)
