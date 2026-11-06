"""Independent-input batch using unchanged algorithms and actual seed identities."""
import ast,copy,hashlib,inspect

from . import clean_speed20_r1 as clean
from .source_phase_absolute_h1_batch_r1 import execute as development_execute

METHODS=('NATIVE','RA','A_NO_P','P_OFF','TABLE_PHASE_H1')
RUN='wc-source-conditional-confirmation-full40-r1'


def derive_seed_context_execute():
    original=clean.execute
    if original.__closure__:raise ValueError('Closure-free original batch entry required')
    source=inspect.getsource(original);tree=ast.parse(source)
    assignments=[n for n in ast.walk(tree) if isinstance(n,ast.Assign)
        and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='context']
    if len(assignments)!=1:raise ValueError('One explicit original request context required')
    node=assignments[0]
    if (not isinstance(node.value,ast.Tuple) or len(node.value.elts)!=3
            or not isinstance(node.value.elts[2],ast.Constant)
            or node.value.elts[2].value!='fixed-seed0-request'):
        raise ValueError('Original seed0 context binding changed')
    original_ast=ast.dump(tree,include_attributes=False)
    old=copy.deepcopy(node.value.elts[2])
    node.value.elts[2]=ast.parse("'fixed-seed'+str(sample.seed)+'-request'",mode='eval').body
    changed_ast=ast.dump(tree,include_attributes=False)
    # Independently restore only the declared node: all remaining source must
    # be the exact original AST. No sampling/timing/cost branches are edited.
    check=copy.deepcopy(tree)
    target=next(n for n in ast.walk(check) if isinstance(n,ast.Assign)
        and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='context')
    target.value.elts[2]=old
    if ast.dump(check,include_attributes=False)!=original_ast:
        raise ValueError('Undeclared sampler edit outside seed identity')
    namespace={**original.__globals__,'RUN':RUN}
    exec(compile(ast.fix_missing_locations(tree),__file__+'#seed-context-only','exec'),namespace)
    function=namespace['execute']
    proof={'original_source_sha256':hashlib.sha256(source.encode()).hexdigest(),
        'original_AST_sha256':hashlib.sha256(original_ast.encode()).hexdigest(),
        'seed_identity_AST_sha256':hashlib.sha256(changed_ast.encode()).hexdigest(),
        'only_context_seed_tag_and_run_namespace_changed':True,
        'sampling_seed_forwarding_algorithm_timing_and_cost_unchanged':True}
    return function,proof


def matrix(requests,warmup):
    if (len(requests)!=8 or len({r['name'] for r in requests})!=8
            or [r['seed'] for r in requests]!=[17]*4+[43]*4 or warmup['seed']!=0):
        raise ValueError('Frozen four prompts/two seeds and separate CAL seed0 warmup required')
    rows=[]
    for repeat in (1,2):
        order=METHODS if repeat==1 else METHODS[::-1]
        for method in order:rows.append({'id':f'warm_{repeat}_{method}','request':warmup,
            'method':method,'section':'WARMUP','round':repeat})
    for index,request in enumerate(requests):
        # Each prompt has opposite order in its two seeds. Both seed blocks
        # and each prompt therefore give every method mean position three.
        order=METHODS if (index%4+index//4)%2==0 else METHODS[::-1]
        for method in order:rows.append({'id':f'timed_{index}_{method}','request':request,
            'method':method,'section':'TIMED','round':1})
    if len(rows)!=50 or sum(r['section']=='TIMED' for r in rows)!=40:
        raise ValueError('Complete40 confirmation plus10 warmups required')
    return rows


def execute(inference,sample,method,*,table_parameters,previous_parameters,**kwargs):
    if method not in METHODS:raise ValueError('Registered independent batch method required')
    if type(sample.seed) is not int or sample.seed not in (0,17,43):
        raise ValueError('Explicit CAL warmup or preregistered confirmation seed required')
    original=clean.execute;seed_entry,proof=derive_seed_context_execute()
    with clean.patched(clean,'execute',seed_entry):
        result,plan=development_execute(inference,sample,method,
            table_parameters=table_parameters,previous_parameters=previous_parameters,**kwargs)
    if clean.execute is not original:raise ValueError('Request context adapter leaked into another batch')
    result['actual_request_seed']=sample.seed
    result['request_context_seed_tag']='fixed-seed'+str(sample.seed)+'-request'
    result['request_context_derivation']=proof
    return result,plan
