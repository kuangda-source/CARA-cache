"""Four whole OFF/ON parents, sixteen suffixes and all24 same-state points."""
import copy
import inspect
from pathlib import Path
from textwrap import dedent

import torch

from . import cfg_guided_w1_sampling as parent
from .e1_memory_diagnostic_sampling_r1 import _transform
from .e4c_matched_source_age_owner_r1 import MatchedSourceAgeOwner
from .prepared_input_persistence_r1 import bind_prepared_input_persistence
from .cfg_mf00_interface_sampling import vector_file
from .rv0_fork import official_suffix
from .mid_coverage import tree_digest


def verify_batch(state, scope):
    names = scope['sample_names']
    if (state['planned_parent_paths'] != 4 or state['planned_origins'] != 4
            or [q['sample_name'] for q in state['requests']] != names):
        raise ValueError('All four parent paths and four event positions required')
    events = points = suffixes = 0
    for request in state['requests']:
        rows = request['paths']
        if ([r['collect'] for r in rows] != [False, True]
                or len(request['prepared_input_calls']) != 2
                or request['prepared_input_calls'][0]['prepared'] != request['prepared_input_calls'][1]['prepared']):
            raise ValueError('Complete OFF/ON actual prepared-input pairing required')
        for row in rows:
            if (row['status'] != 'COMPLETE_PARENT_PATH'
                    or len(row['guided_sha256']) != 36 or len(row['solver_returns']) != 36
                    or row['counters'] != list(range(0, 70, 2))+[0]
                    or row['actions'][:7] != ['DD']*7 or row['actions'][-1] != 'DD'
                    or [p['step'] for p in row['P0_roundtrips']] != [12, 30, 35, 36]
                    or any(not p['complete_additional_state_restored'] or not p['physical_state_restored']
                           for p in row['P0_roundtrips'])
                    or not row['all_modules_eval'] or not row['parameter_versions_unchanged']
                    or row['conditions_before'] != row['conditions_after']
                    or row['condition_fields_before'] != row['condition_fields_after']
                    or row['collection_complete']['method'] != scope['method']):
                raise ValueError('Complete unchanged parent and physical-source controls missing')
            deployment = row['collection_complete']['deployment']
            if (deployment['teacher_calls'] or deployment['A_readout']['teacher_calls']
                    or len(deployment['history']) != 36
                    or [h['action'] for h in deployment['history']] != row['actions']):
                raise ValueError('Offline teachers leaked into actual parent deployment')
            for h in deployment['history']:
                policy = h['source_policy']
                decision = policy['decision']
                if (decision['reason'].startswith('E4C_')
                        or h['action'] != decision['action']*2
                        or h['action'] != 'DD' and h['true_D_before'] != h['true_D_after']
                        or h['action'] == 'PP' and policy['creation_floor_proxy_after'] <= 0):
                    raise ValueError('Intervention, teacher or false D leaked to full parent')
            expected = [e for e in scope['events'] if e['sample_name'] == request['sample_name']]
            if [r['event'] for r in row['origins']] != (expected if row['collect'] else []):
                raise ValueError('Registered early/late event missing or replaced')
            for event in row['origins']:
                if (event['status'] != 'COMPLETE4_BRANCHES_6_AGE_POINTS_NOT_ENDPOINT_QUALITY'
                        or not event['parent_restored']
                        or [b['label'] for b in event['branches']] != scope['suffix_arms']):
                    raise ValueError('Complete repeated-policy and P/D windows required')
                birth = event['event']['birth_step']
                for b in event['branches']:
                    if b['status'] != 'COMPLETE5_UPDATES_NOT_ENDPOINT_VIDEO_OR_ONLINE_POLICY':
                        raise ValueError('Partial five-update branch cannot pass')
                    if b['source']:
                        if b['actions'] != [b['source']*2] + ['CC']*4 or [p['age'] for p in b['age_points']] != [1, 2, 4]:
                            raise ValueError('Matched birth/C4 or age point scope differs')
                        for point in b['age_points']:
                            h = point['actual_source_and_decision_history']
                            if (point['step'] != birth+point['age']
                                    or point['sigma_index'] != point['step']-1
                                    or not point['teacher_state_restored_before_actual_C']
                                    or point['teacher_updates_final_deployment_anchors']
                                    or h['working_source_ages'] != [point['age']]*2
                                    or h['true_D_before'] != h['true_D_after']
                                    or any(s['kind'] != b['source'] or s['created_step'] != birth
                                           for s in h['working_sources'])):
                                raise ValueError('Same-state actual source or scalar clock proof differs')
                            points += 1
                    elif b['age_points']:
                        raise ValueError('Original policy repeat cannot contain intervention teachers')
                    suffixes += 1
                # The unmodified suffix must also recover the subsequent parent
                # output slice; equality between two wrong repeats is insufficient.
                for b in event['branches'][:2]:
                    if (b['guided_sha256'] != row['guided_sha256'][birth-1:birth+4]
                            or b['actions'] != row['actions'][birth-1:birth+4]):
                        raise ValueError('Repeated suffix does not match the original full parent')
                events += 1
        keys = ('guided_sha256', 'guided_list_sha256', 'solver_returns', 'actions', 'counters',
                'conditions_before', 'conditions_after', 'condition_fields_before',
                'condition_fields_after', 'flags_before', 'flags_after', 'rng_after',
                'final_latent_sha256', 'sample_return_sha256')
        if any(rows[0][k] != rows[1][k] for k in keys) or rows[0]['video_artifact']['sha256'] != rows[1]['video_artifact']['sha256']:
            raise ValueError('Diagnostics changed full guarded parent output or RNG')
    if (events, suffixes, points) != (4, 16, 24):
        raise ValueError('Whole registered diagnostic scope not complete')
    return {'full_parent_paths': 4, 'events': events, 'suffixes': suffixes,
        'same_state_age_points': points, 'physical_and_raw_tensor_audit_still_required': True,
        'real_GPU_or_quality_or_clean_latency_claim': False}


def compile_batch(scope, *, calibration, policy_specs):
    if (scope['scope_counts']['total_pair_computations'] != 248
            or scope['method'] != 'A_CPD_W1_ONE_PHASE' or scope['teacher_ages'] != [1, 2, 4]
            or [e['birth_step'] for e in scope['events']] != [13, 25, 12, 27]):
        raise ValueError('Exact frozen full diagnostic scope required')
    suffix = None
    def factory(model, enabled, context, runtime, wc, rf, config, output):
        nonlocal suffix
        if suffix is None:
            suffix = official_suffix(runtime/'cosmos_predict2/_src/predict2/models/text2world_model_rectified_flow.py')
        name = context[0].rsplit(':', 1)[-1]
        events = [e for e in scope['events'] if e['sample_name'] == name]
        def write(event, label, point, tensors):
            return vector_file(output/name/'source-age'/event/label/(str(point)+'.pt'), tensors)
        owner = MatchedSourceAgeOwner(model, method=scope['method'], context=context, runtime=runtime,
            wc=wc, rf=rf, calibration=calibration, spec=policy_specs[scope['method']],
            events=events, enabled=enabled, config=config, writer=write)
        return owner
    def diagnostics(owner, step, latent, capture):
        if not owner.enabled:
            return
        selected = [e for e in owner.events if e['fork_after_update'] == step]
        if not selected:
            return
        if len(selected) != 1:
            raise ValueError('Overlapping registered parent event')
        capture['in_fork'] = True
        try:
            owner.run_event(selected[0], latent, capture['noise'], capture['generator'],
                            capture['velocity'], suffix)
        finally:
            capture['in_fork'] = False
    source = dedent(inspect.getsource(parent.run_batch))
    start = source.index('                collector = GuidedW1Collector(')
    end = source.index('                factory,proof = compile_velocity', start)
    old_owner = source[start:end]
    new_owner = '''                collector = _owner(model,collect,context,runtime,wc,rf_module,config,output)
                executor = collected = collector
                core = collector.compiler
'''
    changes = [
        ('len(samples) != 4 or len(contexts) != 4', 'len(samples) != 2 or len(contexts) != 2'),
        ('Complete guarded four-request guided-W1 calibration batch required', 'Complete guarded E4c four-parent diagnostic batch required'),
        ('planned_parent_paths=8,planned_origins=8,planned_post_RF_branch_tensors=64',
         'planned_parent_paths=4,planned_origins=4,planned_post_RF_branch_tensors=96'),
        ("calibration_collection_policy='UNIFORM_SHARED_D6'", "calibration_collection_policy='E4C_MATCHED_SOURCE_AGE124_OFFLINE_DIAGNOSTIC'"),
        ('selected_steps=list(SELECTED_STEPS)', 'selected_steps=[e["birth_step"] for e in _SCOPE["events"]]'),
        (old_owner, new_owner), ("row['origins'] = collector.records", "row['origins'] = collector.event_records"),
        ('                        counter = int(net.cnt)',
         "                        if capture['in_fork']: return velocity(noise,latent,timestep)\n                        counter = int(net.cnt)"),
        ('                    if step in STATE_STEPS:',
         "                    _diagnostics(collector,step,latent,capture)\n                    if step in STATE_STEPS:"),
        ("row.setdefault('capture_gates',[]).append({'step':step,**gate})",
         "row.setdefault('capture_gates',[]).append({'step':step,**gate})\n                        row.setdefault('P0_roundtrips',[]).append({'step':step,**collector.checkpoint(snapshot,gate,config)})"),
        ('verdict=verify_batch(state)', 'verdict=_verify(state,_SCOPE)'),
        ('                    hooks.close()', '                    collector.close()\n                    hooks.close()')]
    changed, proof = _transform(source, changes)
    ns = {**vars(parent), '_SCOPE': scope, '_owner': factory,
          '_diagnostics': diagnostics, '_verify': verify_batch}
    exec(compile(changed, __file__+'#source-bound-whole-parent-E4c', 'exec'), ns)
    batch = ns['run_batch']
    def run(*args, **kwargs):
        if kwargs['config']['sample_names'] != scope['sample_names']:
            raise ValueError('All two source scenes required in registered order')
        return bind_prepared_input_persistence(batch, state=kwargs['state'], save=kwargs['save'])(*args, **kwargs)
    return run, proof
