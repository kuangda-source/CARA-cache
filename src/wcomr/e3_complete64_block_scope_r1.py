"""CPU-only structural validation of the intact64 experiment and20 run blocks."""
STRATEGIES=('WORKING_P_AGE_KEEP_INTERVAL','WORKING_P_AGE_NONZERO_REBASE')
NAMES=('av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632','human_199',
       'misc_13398218_3840_2160_60fps','av_51b45829-502e-4143-9c32-c026bd6ab191')
METHODS=('SOURCE_RA','DYNAMIC_NO_P','CPD','REF_CPD','A_CPD_OFF',
         'A_CPD_W1_ONE_PHASE','A_CPD_BETA1_ONE_PHASE','DENSE_CONTROL')


def validate_scope(scope):
    if (scope.get('identity')!='E3_COMPLETE64_REUSE10_FRESH54_BLOCK_SCOPE_PREREGISTRATION_NOT_GPU'
        or tuple(scope.get('strategies',()))!=STRATEGIES or tuple(scope.get('sample_names',()))!=NAMES
        or tuple(scope.get('methods',()))!=METHODS
        or [scope.get(k) for k in ('scientific_positions','reused_DEV_positions','generated_complete_positions',
            'fresh_model_processes','maximum_paths_per_model_process')]!=[64,10,54,20,3]
        or not scope.get('one_complete_GPU_card_not20_independent_cards')
        or not scope.get('reuse_is_not_independent_confirmation')):
        raise ValueError('Intact E3 scientific scope and single complete card required')
    expected=[(s,n,m) for s in STRATEGIES for n in NAMES for m in METHODS]
    slots=scope.get('all64_slots',[])
    if len(slots)!=64 or [(r['strategy'],r['sample_name'],r['method']) for r in slots]!=expected:
        raise ValueError('Original64 method/control positions required')
    reuse={(STRATEGIES[0],NAMES[0],m) for m in METHODS}
    reuse|={(STRATEGIES[0],NAMES[1],m) for m in ('A_CPD_W1_ONE_PHASE','A_CPD_BETA1_ONE_PHASE')}
    fresh={}
    for i,(key,row) in enumerate(zip(expected,slots)):
        if row['slot']!=i:raise ValueError('Original64 indices changed')
        if key in reuse:
            binding=row.get('reuse_binding',{})
            if (row['disposition']!='REUSE_QUALIFIED_DEV_OUTPUT'
                or tuple(binding.get(k) for k in ('strategy','sample_name','method'))!=key
                or not all(binding.get(k,{}).get('sha256') and binding[k].get('bytes',0)>0
                           for k in ('video_artifact','vector_artifact'))):
                raise ValueError('Only ten actually qualified bindings may be reused')
        elif row['disposition']!='GENERATE_COMPLETE_PATH' or 'reuse_binding' in row:
            raise ValueError('Every remaining original position must generate a complete path')
        else:fresh[key]=i
    blocks=[]
    for i,name in enumerate(NAMES):
        for strategy in STRATEGIES if i%2==0 else tuple(reversed(STRATEGIES)):
            offset=(2*i+STRATEGIES.index(strategy))%8
            ordered=METHODS[offset:]+METHODS[:offset]
            chosen=[m for m in ordered if (strategy,name,m) in fresh]
            for start in range(0,len(chosen),3):
                methods=chosen[start:start+3]
                blocks.append({'id':'E3_BLOCK_'+str(len(blocks)+1).zfill(2),'strategy':strategy,
                    'paths':[{'sample_name':name,'method':m,'slot':fresh[(strategy,name,m)]} for m in methods]})
    if scope.get('blocks')!=blocks or len(blocks)!=20 or sum(len(b['paths']) for b in blocks)!=54:
        raise ValueError('All54 positions in the preregistered20 bounded run blocks required')
    return {'complete_scientific_positions':64,'qualified_reused_positions':10,
            'generated_complete_positions':54,'fresh_model_processes':20,'maximum_paths_per_process':3}


def validate_block(block,scope):
    validate_scope(scope)
    if block not in scope['blocks']:raise ValueError('One exact block of the intact E3 card required')
    names=list(dict.fromkeys(p['sample_name'] for p in block['paths']))
    if len(names)!=1 or not 1<=len(block['paths'])<=3:raise ValueError('Bounded same-request model lifetime required')
    return names,{n:tuple(p['method'] for p in block['paths'] if p['sample_name']==n) for n in names}
