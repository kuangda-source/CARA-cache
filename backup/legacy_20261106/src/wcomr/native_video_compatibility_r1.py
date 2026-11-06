"""Check same-input/solver/protected-prefix pairing; no generation or scoring."""


def assess(batch, references, expected_methods):
    names=[r['sample_name'] for r in references]
    if len(names)!=4 or len(set(names))!=4 or [r['sample_name'] for r in batch['requests']]!=names:
        raise ValueError('Complete original four reference/request identities required')
    result=[]
    for request,ref in zip(batch['requests'],references):
        rows=request['paths'];prepared=request['prepared_input_calls']
        if ([r.get('collect',r.get('method')) for r in rows]!=list(expected_methods)
            or len(prepared)!=len(rows) or ref['outcome']!='ACCEPTED'
            or ref['solver_steps']!=36 or ref['CFG_calls']!=72 or ref['worldcache_enabled']
            or ref['request']['seed']!=0 or ref['request']['guidance']!=7
            or ref['request']['num_steps']!=35 or ref['request']['num_output_frames']!=93):
            raise ValueError('Complete method denominator or accepted full Native source differs')
        for row,entry in zip(rows,prepared):
            checks={'complete36_guided':len(row.get('guided_sha256',[]))==36,
                'same_prepared_call_arguments':entry.get('request')==ref['prepared_input_calls'][0]['request'],
                'same_prepared_data':entry.get('prepared')==ref['prepared_input_calls'][0]['prepared'],
                'same_condition_fields_before':row.get('condition_fields_before')==ref['condition_fields_before'],
                'same_condition_fields_after':row.get('condition_fields_after')==ref['condition_fields_after'],
                'same_conditions_before':row.get('conditions_before')==ref['conditions_before'],
                'same_conditions_after':row.get('conditions_after')==ref['conditions_after'],
                'same_actual_solver_configuration':row.get('actual_raw_solver_configuration')==ref['actual_raw_solver_configuration'],
                'same_first_seven_dense_guided':row.get('guided_sha256',[])[:7]==ref['guided_sha256'][:7]}
            result.append({'sample_name':request['sample_name'],'method':row.get('collect',row.get('method')),
                'compatible':all(checks.values()),'checks':checks,
                'incompatible_fields':[k for k,v in checks.items() if not v],
                'video_artifact':row.get('video_artifact'),'Native_artifact':ref['artifact'],
                'no_replacement_or_other_seed':True})
    return {'complete_pairing_slots':len(result),'compatible_pairs':sum(r['compatible'] for r in result),
        'incompatible_pairs':sum(not r['compatible'] for r in result),'pairs':result,
        'new_trajectory_or_quality_claim':False,'GPU_submissions':0}
