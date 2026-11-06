"""Four-output offline fixed-mask diagnosis; real dense parity before D/S."""
from .fixed_refresh_diagnostic import FixedRefreshDiagnosticAdapter
from .fixed_refresh_mask import FixedRefreshMask
from .light_output import run_light_dense_control
from .light_sampling import run_light_pair
from .prepared_input import RNGState


def run_fixed_output(inference, sample, wc, settings, mask, *, state, save, output,
                     inference_module, context, mode_setup, fallback=(6, 23, 27),
                     kernel=None, expected_video=(93, 432, 768)):
    if not isinstance(mask, FixedRefreshMask) or sample.name != mask.sample_name:
        raise ValueError('One fixed diagnostic sample must match validated mask')
    mask.bind(context)
    if state.get('dense_control') or state.get('measurement'):
        raise ValueError('Existing fixed output identity; inspect instead of rerun')
    state.update(planned_total_phases=4, planned_output_files=4,
        role='OFFLINE_FIXED_MASK_FIDELITY_DIAGNOSTIC_NOT_DEPLOYMENT_POLICY',
        fixed_mask=mask.to_dict(), reference_context=list(context),
        dense_control={'status': 'NOT_STARTED', 'phases': []},
        measurement={'status': 'NOT_STARTED_DD_PENDING', 'phases': [],
                     'diagnostic_observers': False, 'performance_sample': True})
    save()
    entry_rng = RNGState()
    def dense_factory(kind, ctx):
        return None if kind == 'official' else FixedRefreshDiagnosticAdapter(
            ctx, mask, sparse=False, fallback_layers=tuple(fallback))
    def measure_factory(kind, ctx):
        return FixedRefreshDiagnosticAdapter(ctx, mask, sparse=kind == 'candidate',
            fallback_layers=tuple(fallback), kernel=kernel)
    try:
        entry_rng.restore()
        run_light_dense_control(inference, sample, wc, settings,
            state=state['dense_control'], save=save, output=output / 'dense-control',
            inference_module=inference_module, context=context, mode_setup=mode_setup,
            fallback=fallback, expected_video=expected_video, adapter_factory=dense_factory)
        # Each phase still does real prepare. Only the entry RNG is shared;
        # neither prepared tensors nor post-control cache states are reused.
        entry_rng.restore()
        run_light_pair(inference, sample, wc, settings, state=state['measurement'],
            save=save, output=output / 'measurement' / sample.name,
            inference_module=inference_module, context=context, mode_setup=mode_setup,
            expected_video=expected_video, adapter_factory=measure_factory)
        phases = state['dense_control']['phases'] + state['measurement']['phases']
        if (len(phases) != 4 or any(tuple(p['deep_executed'] for p in phase['trace']) != mask.dense_calls
                for phase in phases)):
            raise ValueError('All four actual refresh traces must match fixed mask')
        artifacts = [phase['artifacts'] for phase in phases]
        if artifacts[0] != artifacts[1] or artifacts[0] != artifacts[2]:
            raise ValueError('Ordinary/fixed dense diagnostic and light output artifacts differ')
        state['measurement']['status'] = 'FIXED_D_S_TWO_COMPLETE_OUTPUTS_REQUIRES_METRICS'
        state['status'] = 'FOUR_FIXED_DIAGNOSTIC_OUTPUTS_COMPLETE_REQUIRES_INDEPENDENT_AUDIT'
    except BaseException as error:
        state.update(status='TECH_BLOCKED_FIXED_FOUR_OUTPUT_DENOMINATOR_PRESERVED',
                     error_type=type(error).__name__, error=str(error))
        raise
    finally:
        save()
