"""Read original complete P1 operation bytes without replaying the collector.

The outer artifact reader must establish original release/settlement first.
This module validates full semantic/physical denominators and original choices;
it cannot dispatch, score, fit, plan, select a new winner, or freeze a result.
"""
import copy
import math
from pathlib import Path

from .cara_budget_search_journal_r1 import read_record
from .cara_fast_fidelity_r1 import file_sha
from .cara_fast_spec_r1 import digest, policy_from_mask
from .cara_source_lifecycle_estimation_r1 import complete_samples
from .cara_source_lifecycle_p1_plan_r1 import validate as validate_card, SEARCH_CONFIG

SOURCE = 'src/wcomr/cara_source_lifecycle_p1_inventory_r1.py'
COLLECTION_SOURCES = ('cara_source_lifecycle_p1_collection_r1.py','cara_source_lifecycle_p1_plan_r1.py',
    'cara_source_lifecycle_search_r1.py','cara_source_lifecycle_fit_scores_r1.py',
    'cara_source_lifecycle_estimation_r1.py','cara_source_lifecycle_planner_r1.py')


def semantic_slots(card, summary):
    profile = validate_card(card)
    members = card['FIT']+card['CHECK']
    slots = {}
    def put(name, member, kind, *, policy=None, timing='CLEAN', parent_id=None, skipped=None):
        if name in slots or member not in members:
            raise ValueError('Duplicate or unregistered P1 semantic position')
        candidate = 'NATIVE35' if kind=='native' else 'ALLD' if kind=='allD' else policy['fingerprint']
        slots[name] = dict(id=name, member=member, kind=kind, policy=copy.deepcopy(policy),
            candidate_id=candidate, seed=0, timing=timing, parent_id=parent_id, skipped=skipped)
    for control in card['controls']:
        role = card['roles'].get(control.get('role'), {})
        put(control['id'],control['member'],control['kind'],timing=control['timing'],
            policy=control.get('policy',role.get('policy')))
    for i, member in enumerate(members):
        for role in card['baseline_roles']:
            definition = card['roles'][role]
            put('baseline-'+role+'-'+str(i),member,definition['kind'],policy=definition.get('policy'))
    for i, member in enumerate(card['FIT']):
        for parent in card['calibration_design']['parents']:
            put('parent-'+parent['id']+'-'+str(i),member,'scalar',policy=parent['policy'],
                timing='DIAGNOSTIC',parent_id=parent['id'])
    if set(summary['models'])!=set(card['families']):
        raise ValueError('All three original estimator families required')
    selection_keys = {family+'-K'+str(k) for family in card['families'] for k in card['D_budgets']}
    if set(summary['FIT_selected']) != selection_keys:
        raise ValueError('All six original complete-FIT selections required')
    for family in card['families']:
        model = summary['models'][family]
        if len(model['families']) != 1 or model['families'][0]['family'] != family:
            raise ValueError('Original separately metered single-family fit required')
        for budget in card['D_budgets']:
            plans = model['families'][0]['candidates'][str(budget)]['plans']
            if len(plans)!=3 or len({p['policy']['fingerprint'] for p in plans})!=3:
                raise ValueError('Complete three distinct original candidates required on this registered legal grid')
            for rank, plan in enumerate(plans):
                if len(plan['dense_steps'])!=budget or policy_from_mask(profile,plan['dense_steps'])!=plan['policy']:
                    raise ValueError('Original candidate left the exact19D/22D grammar')
                for i, member in enumerate(card['FIT']):
                    put(f'fit-{family}-K{budget}-r{rank}-f{i}',member,'policy',policy=plan['policy'])
            selected = summary['FIT_selected'][family+'-K'+str(budget)]
            if selected not in plans:
                raise ValueError('Original complete-FIT selection is not one of its registered candidates')
            for i, member in enumerate(card['CHECK']):
                put(f'CHECK-{family}-K{budget}-{i}',member,'policy',policy=selected['policy'])
    if set(summary['fair_searches'])!={'19','22'}:
        raise ValueError('Both original fair-search budgets required')
    for budget in card['D_budgets']:
        search = summary['fair_searches'][str(budget)]
        queries = search['queries']
        best = search['best_complete_candidate']
        if (search['failure'] is not None or search['termination'] not in
                ('CONFIGURED_SA_HC_FINISHED','MEASURED_COST_ADMISSION_STOP')
                or not 1<=len(queries)<=SEARCH_CONFIG.max_evaluations
                or [q['query_id'] for q in queries]!=list(range(1,len(queries)+1))
                or search['requested_queries']!=len(queries)
                or search['completed_queries']!=sum(q['status']=='COMPLETE' for q in queries)
                or not 0<=search['measured_charged_seconds']<=search['measured_cost_cap_seconds'] or best is None):
            raise ValueError('Original complete or measured-budget-stopped search required')
        for qid in range(1,SEARCH_CONFIG.max_evaluations+1):
            query = queries[qid-1] if qid<=len(queries) else None
            if query and query['status'] not in ('COMPLETE','NOT_ADMITTED'):
                raise ValueError('Failed or unknown query cannot enter full P1 acceptance')
            if query:
                dense = query['dense']
                policy = policy_from_mask(profile,dense)
                if len(dense)!=budget or policy['fingerprint']!=query['policy_fingerprint']:
                    raise ValueError('Original fair search query left its legal budget')
            else:
                policy = policy_from_mask(profile,best['dense'])
            skipped = (None if query and query['status']=='COMPLETE' else
                       'BUDGET_NOT_ADMITTED' if query else 'BUDGET_STOP_NOT_REACHED')
            for i, member in enumerate(card['FIT']):
                put(f'search-K{budget}-q{qid}-f{i}',member,'policy',policy=policy,skipped=skipped)
        if best is None or not any(q['status']=='COMPLETE' and q['query_id']==best['query_id']
                and q['dense']==best['dense'] and q['policy_fingerprint']==best['policy_fingerprint'] for q in queries):
            raise ValueError('Original search winner must have a complete original query')
        policy = policy_from_mask(profile,best['dense'])
        for i, member in enumerate(card['CHECK']):
            put(f'CHECK-search-K{budget}-{i}',member,'policy',policy=policy)
    if len(slots)!=146:
        raise ValueError('Whole146 semantic positions must be preserved, including budget stops')
    return slots


def read_inventory(root, card, context, weights, query_bounds, *, cpu_validation=False, maximum_elapsed_seconds):
    root = Path(root)
    if root.is_symlink() or not root.is_absolute() or not math.isfinite(maximum_elapsed_seconds) or maximum_elapsed_seconds<=0:
        raise ValueError('Original isolated algorithm root and complete original bill interval required')
    bound = read_record(root/'binding.json')
    expected = dict(schema='CARA_V1_P1_COLLECTION_BINDING_R1',context=context,scope_sha256=card['scope_sha256'],
        weights=weights,query_bounds=query_bounds,
        source_sha256={n:file_sha(Path(__file__).parent/n) for n in COLLECTION_SOURCES})
    if bound!=expected or context['CPU_fixture_only'] is not cpu_validation:
        raise ValueError('Original registered collector binding/source/weights/query costs differ')
    summary = read_record(root/'algorithm-summary.json')
    if (summary['status']!='P1_ALGORITHM_COMPLETE_PENDING_ORIGINAL_RELEASE_SETTLEMENT_AND_SCIENCE'
            or summary.get('failure') is not None or summary['scope_sha256']!=card['scope_sha256']
            or summary['CPU_fixture_only'] is not cpu_validation or summary['whole_card_scientific_accepted'] is not False
            or summary['original_RGB_MSE_search_reselected'] is not False
            or summary['internal_metric_results_recomputed'] is not False):
        raise ValueError('Original full P1 algorithm success required before scientific acceptance')
    expected_slots = semantic_slots(card,summary)
    positions = summary['semantic_positions']
    if (len(positions)!=146 or len({p['id'] for p in positions})!=146
            or {p['id'] for p in positions}!=set(expected_slots)
            or summary['complete_semantic_positions']!=sum(p['status'] in ('COMPLETE','QUALITY_AND_CLEAN_SAMPLE_ALIAS') for p in positions)):
        raise ValueError('Complete original146 position denominator differs')
    operations = {}
    if {p.name for p in (root/'operations').iterdir()}!=set(summary['operations']):
        raise ValueError('Torn, unaccounted or missing original operation retained')
    for name, descriptor in summary['operations'].items():
        directory = root/'operations'/name
        intent, returned = read_record(directory/'intent.json'),read_record(directory/'return.json')
        if (intent['name']!=name or intent['context_sha256']!=digest(context) or returned['kind']!='COMPLETE'
                or returned['request_sha256']!=digest(intent) or digest(returned['payload'])!=returned['payload_sha256']
                or descriptor['return_sha256']!=file_sha(directory/'return.json')
                or descriptor['charged_seconds']!=returned['charged_seconds']
                or any(type(returned[k]) not in (int,float) or not math.isfinite(returned[k])
                       for k in ('before_seconds','after_seconds','charged_seconds'))
                or not 0<=returned['before_seconds']<=returned['after_seconds']<=maximum_elapsed_seconds
                or returned['charged_seconds']<0):
            raise ValueError('Original complete operation bytes, identity or bill interval differs: '+name)
        operations[name]=dict(intent=intent,returned=returned)
    physical, resolved = {}, {}
    seen = set()
    for position in positions:
        name = position['id'];slot=expected_slots[name]
        if slot['skipped'] is not None:
            if position['status']!=slot['skipped'] or position.get('independent_clean_sample') is not False:
                raise ValueError('Original not-admitted/not-reached search denominator changed')
            continue
        operation = position['original_operation']
        original = operations[operation]
        wanted = {k:v for k,v in slot.items() if k!='skipped'}
        wanted['context_sha256']=digest(context)
        actual = original['intent']['request']
        if position['status']=='COMPLETE':
            if operation!=name or actual!=wanted or operation in physical:
                raise ValueError('Original physical slot identity differs')
        elif position['status']=='QUALITY_AND_CLEAN_SAMPLE_ALIAS':
            if (slot['timing']!='CLEAN' or operation not in seen
                    or position['independent_clean_sample'] is not False
                    or any(actual[k]!=wanted[k] for k in ('member','kind','candidate_id','seed','timing','parent_id'))):
                raise ValueError('Only original identical clean policy/input/seed may be aliased')
        else:
            raise ValueError('Failed/unknown semantic slot cannot enter complete acceptance')
        value = original['returned']['payload']
        proof_file = root/'operations'/operation/'request-complete.json'
        proof = read_record(proof_file)
        if (value['operation']!=operation or Path(value['proof_path'])!=proof_file.resolve()
                or value['proof_sha256']!=file_sha(proof_file) or value['proof']!=proof
                or proof['status']!='COMPLETE' or proof['CPU_fixture_only'] is not cpu_validation
                or proof['context_sha256']!=digest(context)
                or any(proof[k]!=context[k] for k in ('source_revision','launch_id'))
                or any(proof[k]!=slot[k] for k in ('member','seed','candidate_id','timing'))
                or any(proof[k]!=36 for k in ('actual_updates','solver_steps','guided_pairs'))
                or proof['fallback_count']!=0 or proof['physical_model_pairs']!=(44 if slot['kind']=='scalar' else 36)):
            raise ValueError('Original full36 physical proof differs')
        for artifact, field in ((proof['video'],'sha256'),(proof['final_latent'],'file_sha256')):
            path=Path(artifact['path'])
            if (path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to((root/'operations'/operation/'generation').resolve())
                    or file_sha(path)!=artifact[field]):
                raise ValueError('Original physical video/latent bytes or isolated location differ')
        if slot['kind'] in ('policy','scalar'):
            history=proof.get('semantic_history')
            if history is not None and ([h['actual'] for h in history]!=slot['policy']['actions']
                    or any(h['fallback_reason'] is not None for h in history)):
                raise ValueError('Original physical policy history differs')
            if not cpu_validation and history is None:
                raise ValueError('Actual original complete production policy history required')
        if slot['timing']=='CLEAN' and (not cpu_validation and proof['eligible_clean_time'] is not True):
            raise ValueError('Only the original clean clock may enter deployment comparisons')
        clocks=('T_request',) if slot['timing']=='OFF' else ('T_DD','T_request')
        if (any(type(proof[k]) not in (int,float) or not math.isfinite(proof[k]) or proof[k]<=0 for k in clocks)
                or (slot['timing']=='OFF' and proof['T_DD'] is not None)):
            raise ValueError('Complete original positive dual-clock request times required')
        if position['status']=='COMPLETE':
            physical[operation]=dict(slot=actual,value=value)
            seen.add(operation)
        resolved[name]=dict(original_operation=operation,slot=slot,value=value,
            alias=position['status']=='QUALITY_AND_CLEAN_SAMPLE_ALIAS')
    if not 46<=len(physical)<=142 or sum(v['value']['proof']['physical_model_pairs'] for v in physical.values())>5176:
        raise ValueError('Original bounded whole P1 physical path/model-pair inventory differs')
    parents=[v['value']['proof'] for v in physical.values() if v['slot']['kind']=='scalar']
    if len(parents)!=8 or summary['source_labels']['rows']!=[row for p in parents for row in p['scalar_labels']]:
        raise ValueError('All64 same-state labels must come from the eight original parent proofs')
    complete_samples(summary['source_labels'],card['calibration_design'],card['schedule'])
    for family in card['families']:
        fit=operations['fit-'+family]['returned']['payload']
        if fit!=summary['models'][family]:
            raise ValueError('Original estimator summary changed')
        for budget in card['D_budgets']:
            key=family+'-K'+str(budget)
            selected=operations['select-'+key]['returned']['payload']
            if selected['candidate_id']!=summary['FIT_selected'][key]['policy']['fingerprint']:
                raise ValueError('Original once-written FIT selection changed')
    first_check=min(operations[v['original_operation']]['returned']['before_seconds']
                    for v in resolved.values() if v['slot']['member'] in card['CHECK'])
    if any(operations['select-'+family+'-K'+str(k)]['returned']['after_seconds']>first_check
           for family in card['families'] for k in card['D_budgets']):
        raise ValueError('All six FIT selections must precede the first CHECK output')
    return dict(summary=summary,summary_sha256=file_sha(root/'algorithm-summary.json'),
        binding=bound,operations=operations,physical=physical,resolved=resolved,
        semantic_positions=positions,semantic_denominator=146,physical_paths=len(physical),
        physical_model_pairs=sum(v['value']['proof']['physical_model_pairs'] for v in physical.values()),
        original_generation_or_score_callbacks=0,scientific_accepted=False,GPU_submissions=0,ledger_written=False)
