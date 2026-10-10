"""Full E2 pair coverage, prompt/seed estimates and balanced timing summaries."""
import itertools
import math
import statistics

METHODS=('WC','RA','W1_ONE_PHASE','BETA1_ONE_PHASE')
CANDIDATES=METHODS[2:]


def pair_slots(rows):
    if len(rows)!=76 or len({r['id'] for r in rows})!=76:
        raise ValueError('All76 E2 original positions required')
    pairs=[{'id':r['id'],'section':r['section'],'request_name':r['request_name'],'method':r['method']}
           for r in rows if r['method']!='NATIVE']
    if len(pairs)!=68 or sum(p['section']=='CONFIRMATION' for p in pairs)!=32:
        raise ValueError('All32 confirmation and all68 available-pair positions required')
    return pairs


def bind_pairs(rows,old_runner,old_raw,model_context):
    """All68 positions; missing exact CAL bridges stay unavailable."""
    slots=pair_slots(rows);by_id={r['id']:r for r in rows}
    native={r['request_name']:r for r in rows if r['method']=='NATIVE'}
    old_native={r['sample_name']:r for r in old_runner['comparison']['references']}
    old_methods={(q['sample_name'],r['method']):r for q in old_runner['comparison']['batch']['requests'] for r in q['paths']}
    old_pairs={(r['sample_name'],r['method']):r for r in old_raw['matched_fidelity_pairs']}
    parity={r['method']:r for r in rows if r['section']=='PARITY'};answer=[]
    for slot in slots:
        row=by_id[slot['id']];pair={**slot,'status':'UNPAIRED','reason':'CANDIDATE_REJECTED','score':None}
        if row['status']!='COMPLETE_PATH':answer.append(pair);continue
        pair['candidate']=row['video_artifact']
        if row['section']=='CONFIRMATION':
            ref=native[row['request_name']]
            if ref['status']!='COMPLETE_PATH':pair['reason']='MATCHED_NATIVE_REJECTED'
            elif (row['first_velocity_input_sha256']!=ref['first_velocity_input_sha256']
                    or row['condition_fields_before']!=ref['condition_fields_before']
                    or row['prepared_input_calls'][0]['prepared']!=ref['prepared_input_calls'][0]['prepared']
                    or row['flags_before']!=ref['flags_before']):
                raise ValueError('Actual matched CONF reference input or flags differs')
            else:pair.update(status='PAIRED',reason=None,reference=ref['video_artifact'],reference_source='CURRENT_MATCHED_NATIVE')
        else:
            name=row['request_name'];ref=old_native.get(name);old=old_methods.get((name,row['method']))
            witness=parity[row['method']] if name==parity[row['method']]['request_name'] else row
            known=old_pairs.get((name,row['method']))
            valid=bool(ref and old and known and ref['outcome']=='ACCEPTED'
                and old_runner['model_context']==model_context
                and row['request']==ref['request'] and row['flags_before']==old['flags_before']==ref['flags_before']
                and witness['status']=='COMPLETE_PATH' and witness['actions']==old['actions']
                and witness['final_latent_sha256']==old['final_latent_sha256']
                and witness['video_artifact']['sha256']==old['video_artifact']['sha256']
                and known['reference']['sha256']==ref['artifact']['sha256'])
            if valid and witness['mode']=='AUDIT':
                valid=(witness['guided_sha256']==old['guided_sha256']
                    and witness['first_velocity_input_sha256']==old['first_velocity_input_sha256']
                    and witness['condition_fields_before']==old['condition_fields_before'])
            if valid and row is not witness:
                valid=(row['actions']==witness['actions'] and row['final_latent_sha256']==witness['final_latent_sha256']
                    and row['video_artifact']['sha256']==witness['video_artifact']['sha256'])
            if valid:pair.update(status='PAIRED',reason=None,reference=ref['artifact'],reference_source='AUDITED_OLD_NATIVE_EXACT_METHOD_OUTPUT_BRIDGE')
            else:pair['reason']='CAL_NATIVE_BRIDGE_NOT_EXACT_OLD_OUTPUT'
        answer.append(pair)
    return answer


def _mean(values):return sum(values)/len(values) if values else None


def _percentile(values,q):
    a=sorted(values);x=(len(a)-1)*q;l=int(x);h=min(l+1,len(a)-1)
    return a[l]+(a[h]-a[l])*(x-l)


def summarize(rows,pairs,inputs):
    expected=pair_slots(rows)
    if len(pairs)!=68 or any(any(p.get(k)!=v for k,v in e.items()) for p,e in zip(pairs,expected)):
        raise ValueError('Every pair, rejection and unpaired E2 slot must stay in order')
    scored={}
    for p in pairs:
        score=p.get('score')
        if p['status']=='PAIRED':
            if (not score or score['frames']!=93 or len(score['frame_distances'])!=93
                    or len(score['pts'])!=93 or any(not math.isfinite(v) for v in score['frame_distances'])
                    or not math.isclose(score['mean_LPIPS'],_mean(score['frame_distances']),rel_tol=1e-12,abs_tol=1e-12)):
                raise ValueError('Every available pair needs actual all93 finite distances')
            scored[p['id']]=p
        elif p['status']!='UNPAIRED' or score is not None or not p.get('reason'):
            raise ValueError('Unpaired reasons cannot be replaced by zero scores')
    requests=inputs['requests'];names=[r['name'] for r in requests]
    if len(names)!=8 or len(set(names))!=8:raise ValueError('Eight exact frozen CONF inputs required')
    lookup={(r['request_name'],r['method']):r for r in rows if r['section']=='CONFIRMATION'}
    primary=[]
    for method in CANDIDATES:
        prompt_units=[];seed_units=[]
        for request in requests:
            name=request['name'];candidate=scored.get(lookup[(name,method)]['id']);baseline=scored.get(lookup[(name,'RA')]['id'])
            unit={'request_name':name,'prompt':name.rsplit('_E2_seed',1)[0],'seed':request['seed'],
                  'status':'MATCHED' if candidate and baseline else 'UNAVAILABLE'}
            if candidate and baseline:
                a=candidate['score'];b=baseline['score']
                if a['reference_sha256']!=b['reference_sha256'] or a['pts']!=b['pts']:
                    raise ValueError('Candidate/RA references and all93 timestamps differ')
                unit.update(candidate_LPIPS=a['mean_LPIPS'],RA_LPIPS=b['mean_LPIPS'],
                    LPIPS_gain=b['mean_LPIPS']-a['mean_LPIPS'],
                    relative_gain_percent=100*(b['mean_LPIPS']-a['mean_LPIPS'])/b['mean_LPIPS'] if b['mean_LPIPS'] else None,
                    improved_frames=sum(x<y for x,y in zip(a['frame_distances'],b['frame_distances'])),
                    harmful_frames=sum(x>y for x,y in zip(a['frame_distances'],b['frame_distances'])))
            seed_units.append(unit)
        groups=list(dict.fromkeys(v['prompt'] for v in seed_units))
        if len(groups)!=4:raise ValueError('Four prompt units required, never93 independent frames')
        for prompt in groups:
            seeds=[u for u in seed_units if u['prompt']==prompt];valid=all(u['status']=='MATCHED' for u in seeds)
            if len(seeds)!=2 or [u['seed'] for u in seeds]!=[17,43]:raise ValueError('Both registered seeds must stay')
            u={'prompt':prompt,'status':'COMPLETE_TWO_SEEDS' if valid else 'INCOMPLETE_TWO_SEEDS','seeds':seeds}
            if valid:
                u.update(candidate_LPIPS=_mean([s['candidate_LPIPS'] for s in seeds]),
                    RA_LPIPS=_mean([s['RA_LPIPS'] for s in seeds]),LPIPS_gain=_mean([s['LPIPS_gain'] for s in seeds]))
            prompt_units.append(u)
        complete=[u for u in prompt_units if u['status']=='COMPLETE_TWO_SEEDS'];gains=[u['LPIPS_gain'] for u in complete]
        a=_mean([u['candidate_LPIPS'] for u in complete]);b=_mean([u['RA_LPIPS'] for u in complete])
        boot=[_mean(v) for v in itertools.product(gains,repeat=len(gains))] if gains else []
        primary.append({'candidate':method,'baseline':'RA','all_four_prompt_units':prompt_units,
            'complete_prompt_units':len(complete),'planned_prompt_units':4,'prompt_equal_candidate_LPIPS':a,
            'prompt_equal_RA_LPIPS':b,'prompt_equal_LPIPS_gain':_mean(gains),
            'relative_gain_percent_of_means':100*(b-a)/b if b else None,
            'worst_prompt_gain':min(gains) if gains else None,
            'descriptive_prompt_bootstrap_95_gain_interval':[_percentile(boot,.025),_percentile(boot,.975)] if len(gains)>=2 else None,
            'bootstrap_resamples':len(boot),'independent_frame_count_claim':False,
            'confirmation_or_multiplicity_acceptance_claim':False})
    timing=[]
    names=list(dict.fromkeys(r['request_name'] for r in rows if r['section']=='TIMING'))
    for name in names:
        for method in METHODS:
            runs=[r for r in rows if r['section']=='TIMING' and r['request_name']==name and r['method']==method]
            if len(runs)!=4 or [r['round'] for r in runs]!=[1,2,3,4]:raise ValueError('Every balanced four-round timing stays')
            costs=[r['online_setup_pipeline_cleanup_seconds'] for r in runs]
            if any(not math.isfinite(v) or v<0 for v in costs):raise ValueError('Finite complete timing costs required')
            accepted=[r for r in runs if r['status']=='COMPLETE_PATH']
            identities={(tuple(r['actions']),r['final_latent_sha256'],r['video_artifact']['sha256']) for r in accepted}
            timing.append({'request_name':name,'method':method,'all_four_runs':[
                {'id':r['id'],'round':r['round'],'position':r['position'],'status':r['status'],
                 'pipeline_seconds':r['pipeline_wall_seconds'],'online_seconds':r['online_setup_pipeline_cleanup_seconds'],
                 'full_branch_calls':r['block_counts']['full_calls'],
                 'extra_heads':r['A_readout']['extra_candidate_heads'] if r.get('A_readout') else 0} for r in runs],
                'all_executed_online_mean_seconds':_mean(costs),'all_executed_online_median_seconds':statistics.median(costs),
                'all_executed_online_range_seconds':[min(costs),max(costs)],'accepted_runs':len(accepted),
                'accepted_four_output_identity_equal':len(accepted)==4 and len(identities)==1,
                'audit_parity_runs':sum(bool(r.get('actual_audit_timing_endpoint_and_action_parity')) for r in runs)})
    contrasts=[]
    for name in names:
        for method in CANDIDATES:
            values=[]
            for round_id in range(1,5):
                a=next(r for r in rows if r['section']=='TIMING' and r['request_name']==name and r['method']==method and r['round']==round_id)
                b=next(r for r in rows if r['section']=='TIMING' and r['request_name']==name and r['method']=='RA' and r['round']==round_id)
                values.append({'round':round_id,'candidate_status':a['status'],'RA_status':b['status'],
                    'online_seconds_saved':b['online_setup_pipeline_cleanup_seconds']-a['online_setup_pipeline_cleanup_seconds']})
            contrasts.append({'request_name':name,'candidate':method,'baseline':'RA','four_rounds':values,
                'mean_online_seconds_saved':_mean([v['online_seconds_saved'] for v in values])})
    return {'planned_paths':76,'planned_scientific_paths':72,'planned_pairs':68,'scored_pairs':len(scored),
        'unpaired':[p for p in pairs if p['status']=='UNPAIRED'],'actual_full_frame_distances':93*len(scored),
        'co_primary_comparisons':primary,'timing_eight_groups':timing,'timing_four_contrasts':contrasts,
        'all_rejections_and_harmful_values_preserved':True,'automatic_direction_rejection':False}
