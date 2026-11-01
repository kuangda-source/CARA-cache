"""Run the full M1 matrix on a caller-admitted, already loaded model."""
from pathlib import Path

from .cara_fast_spec_r1 import digest
from .cara_read_write_collection_r1 import Requests, collect
from .cara_s_endpoint_runner_r1 import observed_precision
from .policy_price_terminal_r1 import require
from .wc_time_collection_r1 import atomic


def collect_loaded(inference, samples, card, common, output, context, storage,
                   mode_types, snapshot_limits, *, cpu_validation=False):
    import torch
    from .full_sampling import CompleteStateRoundtrip
    from .h0_mode import establish_shared_eval, verify_shared_eval

    output = Path(output)
    state_file = output/'read-write-collection.json'
    require(not state_file.exists() and not (output/'B').exists(),
            'Original M1 collection exists; recover only')
    model, net = inference.pipe.model, inference.pipe.model.net
    require(context['host'] == 'two_card' and context['CPU_fixture_only'] is cpu_validation
            and bool(mode_types), 'Exact M1 host and mode/fixture contract required')
    precision = observed_precision(model)
    require(digest(precision) == context['model_precision_sha256'],
            'Original shared model precision differs')
    if not cpu_validation:
        require(precision['model_precision'] == 'torch.bfloat16'
                and precision['use_wan_fp32_strategy'] is True
                and precision['conditional_frame_timestep'] == .1
                and precision['outer_autocast'] is False,
                'Original production precision/backend required')
    versions = [(name, p, p._version, str(p.dtype)) for name, p in net.named_parameters()]
    mode = establish_shared_eval(net, mode_types)
    common['wc'].apply_worldcache(net, **{k.removeprefix('worldcache_'): v
                                        for k, v in card['settings'].items()})
    initial = CompleteStateRoundtrip(net, model.sample_scheduler, torch.zeros(1))
    origin, checks = initial.fingerprint(), 0

    def verify_parameters():
        current = list(net.named_parameters())
        require(len(current) == len(versions) and all(
            name == old_name and p is original and p._version == version and str(p.dtype) == dtype
            for (name, p), (old_name, original, version, dtype) in zip(current, versions)),
            'Original model parameters changed')
        require(observed_precision(model) == precision,
                'Original precision/backend changed during M1 collection')

    def before(slot):
        nonlocal checks
        storage.check()
        initial.restore()
        require(initial.fingerprint() == origin, 'Original complete request reset differs')
        verify_shared_eval(net, mode)
        verify_parameters()
        checks += 1

    adapter = Requests(inference=inference, samples=samples, card=card, common=common,
        context=context, cpu_validation=cpu_validation,
        logical_copy_cap_bytes=snapshot_limits['logical_copy_bytes'],
        CPU_storage_cap_bytes=snapshot_limits['total_CPU_images_bytes'])
    try:
        collection = collect(adapter, output/'B', before_request=before,
                             save=lambda value: atomic(state_file, value))
    finally:
        initial.restore()
        require(initial.fingerprint() == origin, 'Final complete M1 state restoration differs')
        verify_shared_eval(net, mode)
        verify_parameters()
    storage.check()
    return collection, dict(precision_sha256=digest(precision), request_boundary_checks=checks,
        final_state_restored=True, shared_eval_verified=True, CPU_fixture_only=cpu_validation,
        physical_requests=14, physical_model_pairs=512, scientific_accepted=False)
