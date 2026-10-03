"""Six outputs: strict D/D, then common D plus full/small/cadenced S."""
from .fixed_refresh_diagnostic import FixedRefreshDiagnosticAdapter
from .fixed_refresh_mask import FixedRefreshMask
from .light_output import run_light_dense_control
from .light_sampling import run_light_pair
from .prepared_input import RNGState
from .selective_refresh_diagnostic import SelectiveFixedRefreshAdapter
from .selective_refresh_policy import SparseRefreshPolicy


def run_selective_output(inference, sample, wc, settings, mask, policies, *,
                         state, save, output, inference_module, context, mode_setup,
                         fallback=(6, 23, 27), kernel=None, expected_video=(93, 432, 768),
                         expected_D_sha256=None, expected_full_S_sha256=None):
    if not isinstance(mask, FixedRefreshMask) or sample.name != mask.sample_name:
        raise ValueError('Single selective diagnostic sample must match mask')
    mask.bind(context)
    if (type(policies) is not tuple or len(policies) != 3
            or any(not isinstance(p, SparseRefreshPolicy) for p in policies)):
        raise ValueError('Three predeclared full/small/low-frequency policies required')
    full, small, cadence = policies
    group = tuple(v for v in range(inference.pipe.model.net.probe_depth,
        len(inference.pipe.model.net.blocks)) if v not in fallback)
    if (full.sparse_layers != group or full.every != 1 or cadence.sparse_layers != group
            or cadence.every != 2 or small.every != 1
            or not set(small.sparse_layers) < set(full.sparse_layers)):
        raise ValueError('One-factor full/small/cadenced comparison differs')
    for p in policies:
        p.validate_geometry(inference.pipe.model.net.probe_depth,
                            len(inference.pipe.model.net.blocks), fallback)
    for digest in (expected_D_sha256, expected_full_S_sha256):
        if digest is not None and (type(digest) is not str or len(digest) != 64
                or any(v not in '0123456789abcdef' for v in digest)):
            raise ValueError('Historical output binding must be an explicit SHA256')
    if state.get('dense_control') or state.get('measurement'):
        raise ValueError('Existing selective identity; inspect instead of rerun')
    state.update(planned_total_phases=6, planned_output_files=6,
        role='OFFLINE_SELECTIVE_FIXED_MASK_DIAGNOSTIC_NOT_DEPLOYMENT_POLICY',
        fixed_mask=mask.to_dict(), reference_context=list(context),
        policies=[p.to_dict() for p in policies],
        dense_control={'status':'NOT_STARTED','phases':[]},
        measurement={'status':'NOT_STARTED_DD_PENDING','phases':[],
            'diagnostic_observers':False,'performance_sample':True})
    save()
    entry_rng = RNGState()
    def dense_factory(kind, ctx):
        return None if kind == 'official' else FixedRefreshDiagnosticAdapter(ctx, mask,
            sparse=False, fallback_layers=tuple(fallback))
    index = [0]
    def measure_factory(kind, ctx):
        if kind == 'official':
            return FixedRefreshDiagnosticAdapter(ctx, mask, sparse=False,
                fallback_layers=tuple(fallback))
        previous = state['measurement']['phases'][-2]
        if index[0] == 0 and previous['artifacts'] != state['dense_control']['phases'][0]['artifacts']:
            raise ValueError('Light fixed D differs before any S measurement')
        if (index[0] == 1 and expected_full_S_sha256 is not None
                and previous['artifacts'][0]['sha256'] != expected_full_S_sha256):
            raise ValueError('Legacy full S output differs; new variants not started')
        policy = policies[index[0]]
        index[0] += 1
        return SelectiveFixedRefreshAdapter(ctx, mask, policy, sparse=True,
            fallback_layers=tuple(fallback), kernel=kernel)
    try:
        entry_rng.restore()
        run_light_dense_control(inference, sample, wc, settings,
            state=state['dense_control'], save=save, output=output/'dense-control',
            inference_module=inference_module, context=context, mode_setup=mode_setup,
            fallback=fallback, expected_video=expected_video, adapter_factory=dense_factory)
        if (expected_D_sha256 is not None and
                state['dense_control']['phases'][0]['artifacts'][0]['sha256'] != expected_D_sha256):
            raise ValueError('Official D differs from historical bound video')
        entry_rng.restore()
        run_light_pair(inference, sample, wc, settings, state=state['measurement'], save=save,
            output=output/'measurement'/sample.name, inference_module=inference_module,
            context=context, mode_setup=mode_setup, expected_video=expected_video,
            adapter_factory=measure_factory, sequence=('official','candidate','candidate','candidate'),
            sequence_policy='reference_then_candidates')
        phases = state['dense_control']['phases'] + state['measurement']['phases']
        if len(phases) != 6 or any(tuple(p['deep_executed'] for p in phase['trace']) != mask.dense_calls for phase in phases):
            raise ValueError('All six actual refresh traces must match common mask')
        if phases[0]['artifacts'] != phases[1]['artifacts'] or phases[0]['artifacts'] != phases[2]['artifacts']:
            raise ValueError('Three ordinary/fixed dense outputs differ')
        state['measurement']['variant_names'] = ['fixed_D','full_S','small_S','cadenced_S']
        state['measurement']['status'] = 'SELECTIVE_D_AND_THREE_S_OUTPUTS_REQUIRE_METRICS'
        state['status'] = 'SIX_SELECTIVE_OUTPUTS_COMPLETE_REQUIRE_INDEPENDENT_AUDIT'
    except BaseException as error:
        state.update(status='TECH_BLOCKED_SELECTIVE_SIX_OUTPUT_DENOMINATOR_PRESERVED',
                     error_type=type(error).__name__,error=str(error))
        raise
    finally:
        save()
