"""P1 full146 released artifacts and sealed-score reuse, before new CPU metrics."""
import copy
import json
import math
from pathlib import Path
import re

from .cara_budget_original_handles_r1 import observe_original_process
from .cara_budget_search_journal_r1 import read_record
from .cara_fast_fidelity_r1 import file_sha
from .cara_fast_scoring_manifest_r2 import comparison_input_digest
from .cara_fast_spec_r1 import digest
from .cara_source_lifecycle_p1_inventory_r1 import read_inventory
from .cara_source_lifecycle_p1_plan_r1 import validate as validate_card
from .cara_source_lifecycle_p1_runner_binding_r1 import RUN_ID,STAGE_NAME,CARD,PRECISION,GEOMETRY,WEIGHTS
from .cara_source_lifecycle_p1_service_r1 import KIND
from .cara_source_lifecycle_fit_broker_r1 import Host,paths
from .cara_source_lifecycle_p1_scores_r1 import pair_key,validate_metric_pair,PROTOCOL
from .cara_source_lifecycle_estimation_r1 import FAMILIES
from .cara_s_endpoint_artifacts_r1 import decode_video,verify_file
from .cara_s_endpoint_lifecycle_r1 import released_lifecycle
from .policy_price_terminal_r1 import record

SOURCE='src/wcomr/cara_source_lifecycle_p1_artifacts_r1.py'
ASSETS='plans/cara_next_stage_20261028/mainline/r2/B36_FROZEN_ASSETS_R1.json'


def descriptor(value):
    proof=value['proof']
    return dict(member=proof['member'],seed=proof['seed'],candidate_id=proof['candidate_id'],
        proof_path=value['proof_path'],proof_sha256=value['proof_sha256'],**proof['video'])


def validate_manifest(manifest,*,cpu_validation=False):
    members=manifest['FIT']+manifest['CHECK']
    roles=('UNIFORM19_C','UNIFORM22_C','F19_C','F19_A1','BUDGET_SEARCH19_C')+tuple(
        'V1-'+family+'-K'+str(k) for family in FAMILIES for k in (19,22))+('LPIPS_SEARCH-K19','LPIPS_SEARCH-K22')
    if (manifest['schema']!='CARA_V1_P1_RELEASED_SCORE_MANIFEST_R1' or manifest['CPU_fixture_only'] is not cpu_validation
            or manifest['run_id']!=RUN_ID or manifest['semantic_denominator']!=146
            or not 46<=manifest['physical_paths']<=142 or manifest['physical_model_pairs']>5176
            or len(manifest['FIT'])!=2 or len(manifest['CHECK'])!=2 or len(set(members))!=4
            or manifest['GPU_released'] is not True or manifest['cost_settled'] is not True
            or manifest['identity_controls_passed']!=12 or len(manifest['identity_controls'])!=12
            or any(c['passed'] is not True for c in manifest['identity_controls'])
            or manifest['source_label_count']!=64 or manifest['old_RGB_MSE_search_reselected'] is not False
            or manifest['internal_scores_recomputed']!=0):
        raise ValueError('Original released full146/64 labels/12 controls and score-reuse denominator required')
    positions=manifest['quality_positions']
    if (len(positions)!=52 or len({p['id'] for p in positions})!=52
            or {(p['role'],p['member']) for p in positions}!={(r,m) for r in roles for m in members}):
        raise ValueError('All52 bound original method/input quality positions required')
    expected_keys=set()
    for position in positions:
        key=pair_key(position)
        expected_keys.add(key)
        if (position['pair_key']!=key or position['reference']['candidate_id']!='NATIVE35'
                or position['timing']!='CLEAN' or position['eligible_clean_time'] is not (not cpu_validation)
                or any(type(position[k]) not in (int,float) or not math.isfinite(position[k]) or position[k]<=0
                       for k in ('T_DD','T_request'))):
            raise ValueError('Original clean dual-clock quality position identity differs')
        for side in ('candidate','reference'):
            d=position[side]
            if (d['member']!=position['member'] or d['seed']!=0 or not Path(d['path']).is_absolute()
                    or not Path(d['proof_path']).is_absolute()
                    or any(not re.fullmatch('[0-9a-f]{64}',d[k]) for k in ('sha256','proof_sha256'))):
                raise ValueError('Same-input/seed complete original P1 descriptors required')
    internals=manifest['internal_rows']
    if not set(internals)<=expected_keys or any(k!=pair_key(v['pair']) or digest(v['metrics'])!=v['metrics_sha256']
                                              for k,v in internals.items()):
        raise ValueError('Only byte-bound original internal rows used by final52 may be reused')
    new=manifest['new_pairs']
    new_keys={pair_key(p) for p in new}
    if (len(new)>32 or len(new_keys)!=len(new) or len({p['id'] for p in new})!=len(new)
            or set(internals)&new_keys or set(internals)|new_keys!=expected_keys):
        raise ValueError('Every unique final pair must be internal or new exactly once, at most32 new')
    if any(len(p['expected_decoded_RGB_sha256'])!=2 or any(not re.fullmatch('[0-9a-f]{64}',h)
           for h in p['expected_decoded_RGB_sha256']) for p in new):
        raise ValueError('Both complete released decoded RGB hashes required for every new pair')
    if manifest['protocol_sha256']!=digest(read_record(Path(__file__).resolve().parents[2]/PROTOCOL)):
        raise ValueError('Original unchanged Fidelity protocol required')
    return positions


def read_physical(index,card,precision,stage,*,cpu_validation=False,cpu_shape=None):
    if cpu_shape is not None and not cpu_validation:
        raise ValueError('Tiny geometry is explicitly CPU-fixture-only')
    shape=(93,432,768,3) if cpu_shape is None else tuple(cpu_shape)
    if shape[0]!=93 or shape[-1]!=3:
        raise ValueError('Complete original93 RGB frames required')
    from .mid_coverage import tree_digest
    import torch
    decoded,details={},{}
    inputs={r['name']:r for r in card['inputs']}
    for name,physical in index['physical'].items():
        value,slot=physical['value'],physical['slot']
        proof=value['proof']
        video=dict(proof['video'],bytes=Path(proof['video']['path']).stat().st_size)
        verify_file(video,original_output=True)
        tensor=proof['final_latent']
        latent=torch.load(tensor['path'],map_location='cpu',weights_only=True)
        if (not isinstance(latent,torch.Tensor) or not torch.isfinite(latent).all()
                or (not cpu_validation and list(latent.shape)!=read_record(Path(stage)/GEOMETRY)['expected_real_shape'])
                or tree_digest(latent)!=tensor['tensor_sha256']):
            raise ValueError('Complete finite original latent bytes/geometry differ')
        arguments_file=Path(video['path']).with_suffix('.json')
        arguments=read_record(arguments_file)
        expected={k:v for k,v in inputs[slot['member']].items() if k!='partition'}
        expected.update(seed=0,num_steps=35)
        if any(arguments.get(k)!=v for k,v in expected.items()):
            raise ValueError('Actual original saved P1 request differs')
        decoded[value['proof_sha256']]=decode_video(video,shape=shape)
        details[name]=dict(video=video,latent_file_sha256=tensor['file_sha256'],actual_latent_sha256=tree_digest(latent),
            arguments_path=str(arguments_file),arguments_sha256=file_sha(arguments_file),
            execution_request_sha256=digest(arguments),comparison_input_sha256=comparison_input_digest(arguments),
            model_sha256=precision['model_sha256'],precision_sha256=precision['precision_sha256'])
    for member in card['FIT']+card['CHECK']:
        names=[n for n,p in index['physical'].items() if p['slot']['member']==member]
        if len({details[n]['comparison_input_sha256'] for n in names})!=1:
            raise ValueError('All same-input methods must use identical complete conditioning/default arguments')
    return decoded,details


def quality_positions(index,card):
    summary=index['summary'];members=card['FIT']+card['CHECK']
    rows=[]
    def add(role,member,name):
        resolved=index['resolved'][name]
        value=resolved['value'];proof=value['proof']
        native=index['resolved']['baseline-NATIVE35-'+str(members.index(member))]['value']
        pair=dict(member=member,candidate=descriptor(value),reference=descriptor(native))
        rows.append(dict(id='P1_'+role+'_'+str(members.index(member)),role=role,**pair,pair_key=pair_key(pair),
            original_operation=resolved['original_operation'],independent_clean_sample=not resolved['alias'],
            timing=proof['timing'],eligible_clean_time=proof.get('eligible_clean_time',False),
            T_DD=proof['T_DD'],T_request=proof['T_request']))
    for role in card['baseline_roles']:
        if role=='NATIVE35':continue
        for i,member in enumerate(members):add(role,member,'baseline-'+role+'-'+str(i))
    for family in card['families']:
        for budget in card['D_budgets']:
            selected=summary['FIT_selected'][family+'-K'+str(budget)]
            plans=summary['models'][family]['families'][0]['candidates'][str(budget)]['plans']
            rank=plans.index(selected)
            for i,member in enumerate(card['FIT']):
                add(f'V1-{family}-K{budget}',member,f'fit-{family}-K{budget}-r{rank}-f{i}')
            for i,member in enumerate(card['CHECK']):add(f'V1-{family}-K{budget}',member,f'CHECK-{family}-K{budget}-{i}')
    for budget in card['D_budgets']:
        winner=summary['fair_searches'][str(budget)]['best_complete_candidate']['query_id']
        for i,member in enumerate(card['FIT']):add(f'LPIPS_SEARCH-K{budget}',member,f'search-K{budget}-q{winner}-f{i}')
        for i,member in enumerate(card['CHECK']):add(f'LPIPS_SEARCH-K{budget}',member,f'CHECK-search-K{budget}-{i}')
    if len(rows)!=52:
        raise ValueError('Complete52 selected quality positions required')
    return rows


def released_artifacts(capture,expected_launch_sha256,settlement,*,cpu_validation=False,cpu_shape=None):
    # This must precede every algorithm, score, video and label read.
    release=released_lifecycle(capture,expected_launch_sha256,settlement,cpu_validation=cpu_validation)
    if not (release['container_exit_success'] and release['GPU_released'] and release['cost_settled'] and release['mode_restored']):
        raise ValueError('Original successful release and unique actual settlement required before P1 science')
    launch,reg,guardian,authority=(record(capture,k) for k in ('launch','registration','guardian','authorization'))
    stage=Path(launch['stage']);project=stage.parents[1]
    if (launch['run_id']!=RUN_ID or stage.name!=STAGE_NAME or authority['card_kind']!=KIND
            or launch['CPU_fixture_only'] is not cpu_validation):
        raise ValueError('Only the original whole P1 card may enter its scientific reader')
    for name in (SOURCE,CARD,PRECISION,GEOMETRY,WEIGHTS,ASSETS,PROTOCOL,
                 'src/wcomr/cara_source_lifecycle_p1_inventory_r1.py','src/wcomr/cara_source_lifecycle_p1_scores_r1.py'):
        if file_sha(stage/name)!=reg['payload_sha256'][name]:
            raise ValueError('Original registered P1 reader/science source differs: '+name)
    card=read_record(stage/CARD);validate_card(card)
    if card['scope_sha256']!=launch['scope_sha256']:
        raise ValueError('Original whole P1 scope differs')
    output=project/'outputs'/RUN_ID
    spec=read_record(output/'internal-FIT-queue/binding.json')
    host=Host.reader(spec)
    queue,_=paths(spec)
    started,terminal,closed=(read_record(queue/n) for n in ('service-start.json','service-terminal.json','guardian-service-closed.json'))
    witness=guardian['FIT_service_terminal_witness']
    if (spec['CPU_fixture_only'] is not cpu_validation or spec['context']['launch_sha256']!=expected_launch_sha256
            or spec['context']['scope_sha256']!=card['scope_sha256'] or spec['context']['source_revision']!=launch['source_revision']
            or spec['context']['launch_id']!=launch['launch_id'] or witness!=closed or closed['complete'] is not True
            or spec['context']['guardian_started_monotonic']!=guardian['started_monotonic']
            or spec['context']['hard_GPUh']!=launch['billed_limit_GPUh']
            or spec['context']['admission_sha256']!=launch['admission_sha256']
            or closed['exit_code']!=0 or terminal['error'] is not None or closed['terminal_error'] is not None
            or closed['terminal_sha256']!=file_sha(queue/'service-terminal.json')
            or closed['binding_sha256']!=digest(spec) or terminal['binding_sha256']!=digest(spec)
            or closed['ended_unix']!=terminal['ended_unix']
            or started['identity']!=closed['identity'] or observe_original_process(closed['identity'])['original_live'] is not False
            or terminal['ended_unix']>record(capture,'billing')['ended_unix']):
        raise ValueError('Original held FIT service must close successfully inside its guardian interval')
    runner=read_record(output/'P1-model-runner.json')
    summary_file=output/'algorithm/algorithm-summary.json'
    if (runner['status']!='P1_FULL146_ALGORITHM_COMPLETE_PENDING_RELEASE' or runner['scope_sha256']!=card['scope_sha256']
            or runner['source_revision']!=launch['source_revision'] or runner['CPU_fixture_only'] is not cpu_validation
            or runner['semantic_positions']!=146 or runner['algorithm_summary_sha256']!=file_sha(summary_file)
            or not all(runner['loaded_model_checks'][k] for k in ('final_state_restored','caller_forward_binding_restored','shared_eval_verified'))):
        raise ValueError('Original complete P1 runner terminal and caller restoration required')
    precision=read_record(stage/PRECISION)
    model=[a for a in read_record(stage/ASSETS)['files'] if a.get('digest_kind')=='sha256' and a['digest']==precision['model_sha256']]
    if len(model)!=1:
        raise ValueError('One bound original Cosmos weight asset required')
    if not cpu_validation:
        relative=Path(model[0]['path'])
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Original model asset must stay in its project')
        path=project/relative
        if path.stat().st_size!=model[0]['bytes'] or file_sha(path)!=model[0]['digest']:
            raise ValueError('Original Cosmos weight bytes differ')
    index=read_inventory(output/'algorithm',card,spec['context'],read_record(stage/WEIGHTS)['weights'],
        read_record(stage/'whole-quote.json')['fair_search_query_bounds'],cpu_validation=cpu_validation,
        maximum_elapsed_seconds=record(capture,'billing')['wall_seconds'])
    decoded,details=read_physical(index,card,precision,stage,cpu_validation=cpu_validation,cpu_shape=cpu_shape)
    controls=[];members=card['FIT']+card['CHECK']
    for control in card['controls']:
        if 'compare_to' not in control and 'compare_parent' not in control:continue
        member=control['member'];i=members.index(member)
        other=('parent-'+control['compare_parent']+'-'+str(i) if 'compare_parent' in control else
               'baseline-'+control['compare_to']+'-'+str(i))
        left=index['resolved'][control['id']]['value'];right=index['resolved'][other]['value']
        a,b=left['proof'],right['proof']
        if (a['final_latent']['tensor_sha256']!=b['final_latent']['tensor_sha256'] or a['pre_encode_RGB']!=b['pre_encode_RGB']
                or a['post_request_RNG_sha256']!=b['post_request_RNG_sha256']
                or decoded[left['proof_sha256']]!=decoded[right['proof_sha256']]):
            raise ValueError('Full original P1 latent/pre-encode/decoded93RGB/RNG control failed')
        controls.append(dict(id=control['id'],reference=other,member=member,passed=True,
                             full_latent_and_pre_encode_and_decoded93_and_RNG_equal=True))
    internals={};cohorts=[]
    for name,operation in index['operations'].items():
        if not name.startswith('score-'):continue
        candidate=name.removeprefix('score-')
        if host.recover_query(candidate)['status']!='ORIGINAL_COMPLETE_FIT_ACCEPTED':
            raise ValueError('Original held FIT query remains failed/live/unknown')
        query,directory=paths(spec,candidate)
        response=read_record(query/'response.json')
        accepted=response['payload']
        if accepted!=operation['returned']['payload']:
            raise ValueError('Collector must consume precisely its original sealed host FIT result')
        pairs=operation['intent']['request']['pairs']
        if len(pairs)!=2 or len(accepted['full_fidelity_rows'])!=2:
            raise ValueError('Complete original two-FIT cohort required')
        for pair,row in zip(pairs,accepted['full_fidelity_rows']):
            validate_metric_pair(row,pair,decoded)
            key=pair_key(pair)
            if key in internals:
                raise ValueError('An original internal pair may be scored only once')
            internals[key]=dict(pair=pair,metrics=copy.deepcopy(row),metrics_sha256=digest(row),
                original_response_path=str(query/'response.json'),original_response_sha256=file_sha(query/'response.json'),
                original_execution_sha256=accepted['execution_sha256'])
        cohorts.append(dict(candidate_id=candidate,response_sha256=file_sha(query/'response.json'),
            config_sha256=accepted['config_sha256'],result_sha256=accepted['result_sha256'],
            execution_sha256=accepted['execution_sha256'],complete_pairs=2))
    if not 6<=len(cohorts)<=42:
        raise ValueError('All original bounded internal cohorts required')
    positions=quality_positions(index,card);used={p['pair_key'] for p in positions}
    retained={k:v for k,v in internals.items() if k in used}
    new={}
    for position in positions:
        key=position['pair_key']
        if key not in retained and key not in new:
            new[key]=dict(id='P1_NEW_'+key,**{k:position[k] for k in ('member','candidate','reference')},
                expected_decoded_RGB_sha256=[decoded[position[s]['proof_sha256']]['RGB_sha256'] for s in ('candidate','reference')])
    manifest=dict(schema='CARA_V1_P1_RELEASED_SCORE_MANIFEST_R1',run_id=RUN_ID,launch_id=launch['launch_id'],
        scope_sha256=card['scope_sha256'],FIT=card['FIT'],CHECK=card['CHECK'],CPU_fixture_only=cpu_validation,
        semantic_denominator=146,physical_paths=index['physical_paths'],physical_model_pairs=index['physical_model_pairs'],
        source_label_count=64,identity_controls=controls,identity_controls_passed=len(controls),quality_positions=positions,
        internal_rows=retained,new_pairs=list(new.values()),GPU_released=True,cost_settled=True,
        original_launch_sha256=expected_launch_sha256,algorithm_summary_sha256=index['summary_sha256'],
        protocol_sha256=digest(read_record(stage/PROTOCOL)),internal_scores_recomputed=0,old_RGB_MSE_search_reselected=False)
    validate_manifest(manifest,cpu_validation=cpu_validation)
    release.update(original_launch_sha256=expected_launch_sha256,algorithm_summary_sha256=index['summary_sha256'])
    return dict(status='P1_RELEASED_FULL146_ARTIFACTS_INTERNAL_SCORES_REUSED_PENDING_NEW_PAIRS',manifest=manifest,
        decoded=decoded,physical_artifacts=details,all_internal_cohorts=cohorts,release=release,
        CPU_fixture_only=cpu_validation,reader_sha256=file_sha(__file__),original_metrics_recomputed=0,
        scientific_accepted=False,GPU_submissions=0,ledger_written=False)
