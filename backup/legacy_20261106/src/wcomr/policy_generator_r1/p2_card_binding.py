"""Prepare physical policy aliases after P1; never determine a budget or dispatch.

Only identical requests within the same registered repeat/query can alias.
Different seeds, phases, shadow modes, timing repeats and queries stay physical.
"""
import copy
from .continuation_preparation import require
from .p2_combination import digest, validate_manifest


def deduplicate_requests(rows):
    require(rows and len({r['id'] for r in rows})==len(rows),'Distinct registered request IDs required')
    physical=[];by_signature={};aliases={};logical=[]
    for source in rows:
        row=copy.deepcopy(source)
        require(row['roles'] and len(set(row['roles']))==len(row['roles']),'Preserve named roles')
        for name in ('input_sha256','execution_signature','repeat_id','query_id'):
            require(name in row,'Explicit input, execution, repeat and query identity required')
        sig=row['execution_signature']
        require(set(sig)=={'source_sha256','policy_fingerprint','requested_steps','actual_updates','sampler_config_sha256','diagnostic_mode'},
                'Complete physical execution signature required')
        require(sig['actual_updates']==row['expected_updates'],'Actual solver mismatch')
        ref=row['reference_id']
        if ref is not None:
            require(ref in aliases,'Original reference must precede its request')
            row['reference_id']=aliases[ref]
        key=digest({k:v for k,v in row.items() if k not in ('id','roles','method')})
        if key in by_signature:
            target=by_signature[key]
            require(not set(row['roles'])&set(target['roles']),'Duplicate role within same repeated request')
            target['roles'].extend(row['roles'])
        else:
            target=row;physical.append(target);by_signature[key]=target
        aliases[row['id']]=target['id'];logical.append(dict(id=source['id'],roles=list(source['roles']),physical_id=target['id']))
    return dict(rows=physical,logical_requests=logical,aliases=aliases,
                logical_paths=len(rows),physical_paths=len(physical),saved_duplicate_paths=len(rows)-len(physical),
                budget_determined=False,query_cost_credit_assumed=False,GPU_dispatch_ready=False)


def binding_blueprint(manifest, *, P1_binding, combination_acceptance, quality_readiness):
    validate_manifest(manifest)
    require(not manifest.get('CPU_FIXTURE_ONLY'),'Synthetic manifest cannot bind a production card')
    require(P1_binding['P1_selected_policy_frozen'] is True and
            P1_binding['status']=='P2_ORIGINAL_P1_POLICY_AND_NATIVE_HISTORY_CPU_BOUND_NOT_DISPATCH',
            'Accepted complete P1 binding required')
    require(combination_acceptance['production_CPU_accepted'] is True and
            combination_acceptance['full_GPU_lifecycle_CPU_accepted'] is True,
            'Independent complete P2 combination CPU required')
    dedup=deduplicate_requests(manifest['rows'])
    for row in manifest['rows']:
        if 'CARA' in row['roles']:
            require(row['execution_signature']['policy_fingerprint']==P1_binding['roles']['CARA']['fingerprint'],
                    'CARA policy changed after P1 selection')
    physical=copy.deepcopy(manifest);physical.pop('sha256')
    physical['rows']=dedup['rows']
    physical['block_counts']={b:sum(r['block']==b for r in dedup['rows']) for b in manifest['block_counts']}
    physical['logical_requests']=dedup['logical_requests'];physical['sha256']=digest(physical)
    validate_manifest(physical)
    return dict(status='P2_PHYSICAL_BINDING_BLUEPRINT_BUDGET_AND_ADMISSION_PENDING',
        original_manifest_sha256=manifest['sha256'],P1_binding_sha256=digest(P1_binding),
        combination_acceptance_sha256=digest(combination_acceptance),quality_readiness_sha256=digest(quality_readiness),
        deduplication=dedup,physical_manifest=physical,quality_models_ready=quality_readiness.get('four_card_real_model_CPU_accepted') is True,
        final_budget_determined=False,whole_quote=None,authorization=None,GPU_submissions=0,GPU_dispatch_ready=False)
