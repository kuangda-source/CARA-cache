"""Six method trajectories and two matching ordinary full-compute references.

The accepted three-method executor is unchanged. Reference generation reuses
the audited single-request Native implementation, restores the same initial
physical state, and binds prepared input, first noise/latent/time and conditions.
"""
import inspect
from pathlib import Path
import types

import torch

from .cfg_ra_baseline_sampling import run_batch, verify_batch, vector_file, audit_vectors
from .decoder_policy import backend_flags
from .full_sampling import CompleteStateRoundtrip
from .light_sampling import Hooks, synchronize
from .mid_coverage import tree_digest
from .prepared_input import PreparedInputReplay
from .rv0_fork import object_state
from .w1_native_reference_sampling import run_native_request


def run_comparison(inference, samples, wc, settings, *, state, save, output,
                   inference_module, contexts, mode_setup, runtime, config,
                   rf_module, calibration, threshold, sampling_policy,
                   writer=vector_file):
    if state or len(samples) != 2:
        raise ValueError('Fresh complete six-method-path/two-Native-reference card required')
    output = Path(output)
    state.update(planned_paths=8, planned_method_paths=6, planned_reference_paths=2,
                 batch={}, references=[], status='METHODS_RUNNING',
                 clean_latency_claim=False, independent_confirmation_claim=False)
    save()
    run_batch(inference, samples, wc, settings, state=state['batch'], save=save,
              output=output/'methods', inference_module=inference_module,
              contexts=contexts, mode_setup=mode_setup, runtime=runtime,
              config=config, rf_module=rf_module, calibration=calibration,
              threshold=threshold, writer=writer)
    model, net = inference.pipe.model, inference.pipe.model.net
    scheduler = model.sample_scheduler
    initial = CompleteStateRoundtrip(net, scheduler, torch.zeros(1))
    before = initial.fingerprint()
    state['status'] = 'MATCHED_NATIVE_REFERENCES_RUNNING'
    save()
    try:
        for sample, request in zip(samples, state['batch']['requests']):
            initial.restore()
            row = {'sample_name': sample.name, 'request': sample.model_dump(mode='json'),
                   'status': 'STARTED', 'guided_sha256': [], 'solver_returns': []}
            state['references'].append(row)
            save()
            hooks, conditions, values, captured = Hooks(), [], [], {}
            original = model.get_velocity_fn_from_batch
            prepared = PreparedInputReplay(inference.pipe._get_data_batch_input)
            def factory(m, *args, **kwargs):
                velocity = original(*args, **kwargs)
                cells = inspect.getclosurevars(velocity).nonlocals
                if (set(cells) != {'self', 'condition', 'uncondition', 'guidance'}
                        or cells['self'] is not m or cells['guidance'] != 7):
                    raise ValueError('Ordinary Native RF/condition/CFG closure differs')
                conditions.extend((cells['condition'], cells['uncondition']))
                row['conditions_before'] = tree_digest([object_state(c) for c in conditions])
                def observe(noise, latent, timestep):
                    if not values:
                        row['first_velocity_input_sha256'] = tree_digest((noise, latent, timestep))
                    value = velocity(noise, latent, timestep)
                    if value.dtype != torch.float32 or list(value.shape) != config['expected_shape']:
                        raise ValueError('Native actual guided output geometry differs')
                    values.append(value.detach().cpu().clone())
                    row['guided_sha256'].append(tree_digest(values[-1]))
                    return value
                return observe
            def after_step(value):
                row['solver_returns'].append(tree_digest(value))
                if len(row['solver_returns']) == 36:
                    captured['final_latent'] = value[0].squeeze(0).detach().cpu().clone()
            try:
                hooks.stack.callback(setattr, model, 'get_velocity_fn_from_batch', original)
                model.get_velocity_fn_from_batch = types.MethodType(factory, model)
                hooks.stack.callback(setattr, inference.pipe, '_get_data_batch_input', inference.pipe._get_data_batch_input)
                inference.pipe._get_data_batch_input = prepared
                hooks.wrap(scheduler, 'step', after=after_step)
                run_native_request(inference, sample, state=row, save=save,
                    output=output/'references'/sample.name, inference_module=inference_module,
                    sampling_policy=sampling_policy, expected_flags=backend_flags(), synchronize=synchronize)
                row['prepared_input_calls'] = prepared.calls
                if row['outcome'] == 'ACCEPTED':
                    if len(values) != 36 or len(row['solver_returns']) != 36:
                        raise ValueError('Matching Native full36 raw outputs missing')
                    row.update(conditions_after=tree_digest([object_state(c) for c in conditions]),
                        guided_list_sha256=tree_digest(values), final_latent_sha256=tree_digest(captured['final_latent']))
                    baseline = request['paths'][0]
                    if row['conditions_before'] != row['conditions_after']:
                        raise ValueError('Native conditions changed')
                    if row['conditions_before'] != baseline['conditions_before']:
                        raise ValueError('Native and candidate conditions differ')
                    if row['first_velocity_input_sha256'] != baseline['first_velocity_input_sha256']:
                        raise ValueError('Native and candidate first noise/latent/time differ')
                    if len(prepared.calls) != 1 or prepared.calls[0]['prepared'] != request['prepared_input_calls'][0]['prepared']:
                        raise ValueError('Matching Native actual prepared input differs')
                    row['vector_artifact'] = writer(output/'reference-vectors'/(sample.name+'_NATIVE.pt'),
                        {'guided': values, 'final_latent': captured['final_latent']})
                    row['status'] = 'MATCHED_NATIVE_COMPLETE_REQUIRES_CPU_FULL_DECODE'
                    save()
                else:
                    # Original guardrail outcomes remain in the denominator.
                    row['fidelity_reference_available'] = False
                    save()
            except BaseException as error:
                row.update(status='MATCHED_NATIVE_FAILED_COMPLETE_SCOPE_RETAINED',
                           error_type=type(error).__name__, error=str(error))
                state['status'] = 'COMPARISON_FAILED_COMPLETE_SCOPE_RETAINED'
                save()
                raise
            finally:
                hooks.close()
                values.clear()
        state.update(verdict=verify_comparison(state), status='COMPLETE_RA_COMPARISON_REQUIRES_CPU_AUDIT')
        save()
    finally:
        initial.restore()
        if initial.fingerprint() != before:
            raise ValueError('Matching Native references leaked initial physical state')
        state['reference_initial_state_restored'] = True
        save()


def verify_comparison(state):
    if (state.get('planned_paths') != 8 or state.get('planned_method_paths') != 6
            or state.get('planned_reference_paths') != 2 or len(state.get('references', [])) != 2):
        raise ValueError('Complete six method paths and two reference slots required')
    verify_batch(state['batch'])
    accepted = 0
    for ref, request in zip(state['references'], state['batch']['requests']):
        if ref['sample_name'] != request['sample_name']:
            raise ValueError('Matching Native request identity differs')
        if ref['outcome'] != 'ACCEPTED':
            if (ref['outcome'] not in ('TEXT_REJECTED', 'VIDEO_REJECTED')
                    or ref['status'] != ref['outcome'] or ref['artifact'] is not None
                    or 'vector_artifact' in ref or ref.get('fidelity_reference_available') is not False):
                raise ValueError('Reference rejection replaced or zero-filled')
            continue
        base = request['paths'][0]
        if (ref['status'] != 'MATCHED_NATIVE_COMPLETE_REQUIRES_CPU_FULL_DECODE'
                or len(ref['guided_sha256']) != len(ref['solver_returns']) or len(ref['solver_returns']) != 36
                or (ref['CFG_calls'], ref['solver_steps'], ref['prepare_calls']) != (72, 36, 1)
                or ref['block_counts']['full_calls'] != 72 or not all(x['deep_executed'] for x in ref['trace'])
                or ref['first_velocity_input_sha256'] != base['first_velocity_input_sha256']
                or ref['conditions_before'] != ref['conditions_after'] or ref['conditions_before'] != base['conditions_before']
                or ref['prepared_input_calls'][0]['prepared'] != request['prepared_input_calls'][0]['prepared']
                or ref['vector_artifact']['tensor_sha256']['guided'] != ref['guided_list_sha256']
                or ref['vector_artifact']['tensor_sha256']['final_latent'] != ref['final_latent_sha256']):
            raise ValueError('Matching Native actual full36/inputs/raw artifacts differ')
        accepted += 1
    return {'complete_method_paths': 6, 'attempted_reference_slots': 2, 'accepted_reference_slots': accepted,
            'rejected_reference_slots': 2-accepted, 'planned_solver_updates': 288, 'planned_net_calls': 576,
            'clean_latency_claim': False, 'independent_confirmation_claim': False}


def audit_comparison_vectors(state, root, loader, expected_shape):
    verify_comparison(state)
    root = Path(root).resolve()
    base_paths = {str(Path(r['paths'][0]['vector_artifact']['path']).resolve()) for r in state['batch']['requests']}
    prefixes = {}
    def remember_prefix(path, **kwargs):
        values = loader(path, **kwargs)
        key = str(Path(path).resolve())
        if key in base_paths:
            prefixes[key] = values['guided'][:7]
        return values
    result = audit_vectors(state['batch'], root/'methods', remember_prefix, expected_shape)
    result['reference_files'] = []
    by_name = {r['sample_name']: r for r in state['batch']['requests']}
    for ref in state['references']:
        if ref['outcome'] != 'ACCEPTED':
            continue
        art = ref['vector_artifact']; path = Path(art['path']).resolve()
        import hashlib
        if (not path.is_relative_to(root/'reference-vectors') or path.stat().st_size != art['bytes']
                or hashlib.sha256(path.read_bytes()).hexdigest() != art['sha256']):
            raise ValueError('Matching Native vector file changed')
        values = loader(path, weights_only=True, map_location='cpu')
        if (set(values) != {'guided', 'final_latent'} or len(values['guided']) != 36
                or any(v.dtype != torch.float32 or list(v.shape) != expected_shape or not bool(torch.isfinite(v).all())
                    for v in values['guided']+[values['final_latent']])
                or {k: tree_digest(v) for k, v in values.items()} != art['tensor_sha256']
                or [tree_digest(v) for v in values['guided']] != ref['guided_sha256']):
            raise ValueError('Matching Native actual full36 FP32 tensors differ')
        base = by_name[ref['sample_name']]['paths'][0]['vector_artifact']
        candidate_prefix = prefixes[str(Path(base['path']).resolve())]
        if not all(torch.equal(a, b) for a, b in zip(values['guided'][:7], candidate_prefix)):
            raise ValueError('Native and candidate diverged before eligible policy decisions')
        result['reference_files'].append({'sample_name': ref['sample_name'], 'path': str(path),
                                          'bytes': art['bytes'], 'sha256': art['sha256']})
    if {str(p.resolve()) for p in (root/'reference-vectors').glob('*.pt')} != {x['path'] for x in result['reference_files']}:
        raise ValueError('Matching Native reference artifact set differs')
    result.update(actual_reference_guided_reloaded=36*len(result['reference_files']),
                  actual_reference_latents_reloaded=len(result['reference_files']),
                  actual_reference_initial7_direct_equal=True, reference_rejections_not_replaced=True)
    return result
