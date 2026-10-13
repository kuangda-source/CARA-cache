"""Independent confirmation metadata and paired two-seed aggregation."""
import math
from statistics import mean
from .source_conditional_confirmation_batch_r1 import METHODS,matrix

PAIRS=(('TABLE_PHASE_H1','RA'),('TABLE_PHASE_H1','A_NO_P'),('TABLE_PHASE_H1','P_OFF'),
       ('A_NO_P','RA'),('P_OFF','RA'),('P_OFF','A_NO_P'))


def planned_rows(c):
    return [{k:v for k,v in p.items() if k!='request'}|
            {'scene':p['request']['name'],'seed':p['request']['seed']}
            for p in matrix(c['requests'],c['warmup_request'])]


def validate_matrix_rows(c,rows):
    planned=planned_rows(c)
    if len(rows)!=50 or len({r['id'] for r in rows})!=50:
        raise ValueError('All40 formal plus10 warmup rows required')
    by={r['id']:r for r in rows}
    for p in planned:
        r=by[p['id']]
        if any(r[k]!=v for k,v in p.items()):
            raise ValueError('Frozen order/input/seed/method differs')
        if r['status'] not in ('COMPLETE','VIDEO_REJECTED','TEXT_REJECTED'):
            raise ValueError('Full registered matrix must reach a terminal state')
        if (r['actual_request_seed']!=p['seed'] or
                r['request_context_seed_tag']!='fixed-seed'+str(p['seed'])+'-request'):
            raise ValueError('Actual execution seed and request context must agree')
        if r['status']!='TEXT_REJECTED':
            if r['solver_steps']!=36 or r['guided_pairs']!=36:
                raise ValueError('Complete36 actual updates required')
        if any(r[k]!=0 for k in ('in_timing_hashes','in_timing_guided_copies','research_checkpoints')):
            raise ValueError('Research copying/hashing must remain outside main timer')
    return planned


def prompt_id(request):
    marker='_SOURCECONF_seed'+str(request['seed'])
    if not request['name'].endswith(marker):
        raise ValueError('Registered prompt and seed identity required')
    return request['name'][:-len(marker)]


def aggregate(c,rows):
    validate_matrix_rows(c,rows)
    timed=[r for r in rows if r['section']=='TIMED']
    requests=c['requests'];prompts=list(dict.fromkeys(prompt_id(r) for r in requests))
    if len(prompts)!=4 or any({r['seed'] for r in requests if prompt_id(r)==p}!={17,43} for p in prompts):
        raise ValueError('Four fixed prompts each with both seeds required')
    lookup={(r['scene'],r['method']):r for r in timed}
    for r in timed:
        if 'LPIPS' not in r:continue
        d=r['LPIPS']['frame_distances']
        if (len(d)!=93 or not all(math.isfinite(x) and x>=0 for x in d)
                or not math.isclose(mean(d),r['LPIPS']['mean_LPIPS'],abs_tol=1e-12,rel_tol=1e-12)):
            raise ValueError('All93 finite frames and accurate mean required')
        native=lookup.get((r['scene'],'NATIVE'))
        if not native or 'video_artifact' not in native:
            raise ValueError('Scored candidate needs same-request accepted Native')
        if r['LPIPS']['reference_sha256']!=native['video_artifact']['sha256']:
            raise ValueError('Cross-input/seed Native reference rejected')
        if r['method']=='NATIVE' and (any(d) or r['actions'] is not None):
            raise ValueError('Native self scores zero without cache trace')
    comparisons=[]
    for candidate,baseline in PAIRS:
        values=[];groups=[]
        for request in requests:
            a,b=lookup[(request['name'],candidate)],lookup[(request['name'],baseline)]
            item={'scene':request['name'],'prompt_id':prompt_id(request),'seed':request['seed']}
            if 'LPIPS' not in a or 'LPIPS' not in b:
                values.append({**item,'status':'MISSING_OR_REJECTED_NO_ZERO_IMPUTATION'});continue
            aq,bq=a['LPIPS']['mean_LPIPS'],b['LPIPS']['mean_LPIPS']
            if bq<=0:raise ValueError('Non-Native baseline must have positive reference distortion')
            gains=[x-y for x,y in zip(b['LPIPS']['frame_distances'],a['LPIPS']['frame_distances'])]
            values.append({**item,'status':'SCORED','candidate_LPIPS':aq,'baseline_LPIPS':bq,
                'LPIPS_reduction_percent':100*(1-aq/bq),'candidate_seconds':a['core_seconds'],
                'baseline_seconds':b['core_seconds'],'seconds_saved':b['core_seconds']-a['core_seconds'],
                'speedup_baseline_over_candidate':b['core_seconds']/a['core_seconds'],
                'better_frames':sum(x>0 for x in gains),'worse_frames':sum(x<0 for x in gains),
                'equal_frames':sum(x==0 for x in gains)})
        for prompt in prompts:
            group=[v for v in values if v['prompt_id']==prompt]
            accepted=[v for v in group if v['status']=='SCORED']
            item={'prompt_id':prompt,'seed_denominator':2,'scored_seeds':len(accepted)}
            if len(accepted)!=2:
                groups.append({**item,'status':'INCOMPLETE_PROMPT_BOTH_SEEDS_RETAINED'});continue
            groups.append({**item,'status':'BOTH_SEEDS_SCORED',
                **{k:mean(v[k] for v in accepted) for k in ('candidate_LPIPS','baseline_LPIPS','candidate_seconds','baseline_seconds')}})
        accepted=[g for g in groups if g['status']=='BOTH_SEEDS_SCORED']
        result={'candidate':candidate,'baseline':baseline,'request_seed_denominator':8,
            'independent_prompt_denominator':4,'scored_request_seed_pairs':sum(v['status']=='SCORED' for v in values),
            'complete_two_seed_prompts':len(accepted),'per_request_seed':values,'per_prompt':groups,
            'frames_are_not_independent_samples':True}
        if len(accepted)==4:
            aq,bq=mean(g['candidate_LPIPS'] for g in accepted),mean(g['baseline_LPIPS'] for g in accepted)
            at,bt=mean(g['candidate_seconds'] for g in accepted),mean(g['baseline_seconds'] for g in accepted)
            result.update(prompt_equal_candidate_LPIPS=aq,prompt_equal_baseline_LPIPS=bq,
                prompt_equal_LPIPS_reduction_percent=100*(1-aq/bq),prompt_equal_seconds_saved=bt-at,
                speedup_ratio_of_prompt_equal_times=bt/at,
                improved_prompts=sum(g['candidate_LPIPS']<g['baseline_LPIPS'] for g in accepted))
        comparisons.append(result)
    return {'comparisons':comparisons,'independent_prompt_count':4,'seed_count_per_prompt':2,
            'scored_formal_videos':sum('LPIPS' in r for r in timed)}
