"""Whole P1 algorithm on an admitted shared loaded model, before final release."""
from pathlib import Path
import json

from . import clean_speed20_r1 as clean
from .cara_fast_spec_r1 import digest
from .cara_source_lifecycle_p1_clock_r1 import OriginalAllocationClock
from .cara_source_lifecycle_p1_collection_r1 import Collection
from .cara_source_lifecycle_p1_requests_r1 import Requests
from .cara_source_lifecycle_p1_plan_r1 import validate
from .cara_s_endpoint_runner_r1 import observed_precision


def collect_loaded(*, inference, samples, card, common, context, output, storage,
                   mode_types, snapshot_limits, weights, score, elapsed_seconds,
                   query_bounds, cpu_validation=False, create=False, allow_new=False,
                   collection_class=Collection, card_validator=validate):
    import torch
    from .full_sampling import CompleteStateRoundtrip
    from .h0_mode import establish_shared_eval, verify_shared_eval

    if not cpu_validation and (not isinstance(elapsed_seconds, OriginalAllocationClock)
                              or elapsed_seconds.context != context):
        raise ValueError('Production must use the original live guardian allocation clock')
    if not cpu_validation:
        scale_file = Path(__file__).resolve().parents[2]/'reports/cara_v1_frozen_UniPC_current_input_scale_r1_20261102.json'
        if list(weights) != json.loads(scale_file.read_bytes())['weights']:
            raise ValueError('Original once-frozen UniPC numerical scale required')
    model, net = inference.pipe.model, inference.pipe.model.net
    precision = observed_precision(model)
    if digest(precision) != context['model_precision_sha256']:
        raise ValueError('Original shared P1 precision differs')
    if not cpu_validation and (precision['model_precision'] != 'torch.bfloat16'
            or precision['use_wan_fp32_strategy'] is not True
            or precision['conditional_frame_timestep'] != .1 or precision['outer_autocast'] is not False):
        raise ValueError('Original Cosmos BF16/Wan-FP32/CFG production precision required')
    owned_forward = 'forward' in vars(net)
    original_forward = net.forward
    with clean.patched(net, 'forward', original_forward):
        mode = establish_shared_eval(net, mode_types)
        versions = [(name, p, p._version, str(p.dtype)) for name, p in net.named_parameters()]
        common['wc'].apply_worldcache(net, **{k.removeprefix('worldcache_'): v for k, v in card['settings'].items()})
        initial = CompleteStateRoundtrip(net, model.sample_scheduler, torch.zeros(1))
        origin = initial.fingerprint()
        requests_checked = scores_checked = 0

        def verify():
            verify_shared_eval(net, mode)
            current = list(net.named_parameters())
            if (len(current) != len(versions) or any(name != old or p is not original
                    or p._version != version or str(p.dtype) != dtype
                    for (name, p), (old, original, version, dtype) in zip(current, versions))
                    or observed_precision(model) != precision):
                raise ValueError('Original P1 model parameters or precision changed')

        def before(slot):
            nonlocal requests_checked
            storage.check()
            initial.restore()
            if initial.fingerprint() != origin:
                raise ValueError('Original P1 complete request reset differs')
            verify()
            requests_checked += 1

        def internal_score(packet, directory):
            nonlocal scores_checked
            storage.check()
            verify()
            result = score(packet, directory)
            verify()
            storage.check()
            scores_checked += 1
            return result

        try:
            requests = Requests(inference=inference, samples=samples, card=card, common=common, context=context,
                before_request=before, snapshot_limits=snapshot_limits, cpu_validation=cpu_validation,
                card_validator=card_validator)
            collection = collection_class(root=Path(output), card=card, context=context, weights=weights,
                execute=requests, score=internal_score, elapsed_seconds=elapsed_seconds, query_bounds=query_bounds,
                cpu_validation=cpu_validation, create=create, card_validator=card_validator)
            result = collection.run(allow_new=allow_new)
        finally:
            initial.restore()
            if initial.fingerprint() != origin:
                raise ValueError('Final complete P1 caller state restoration differs')
            verify()
        storage.check()
    if net.forward != original_forward or ('forward' in vars(net)) != owned_forward:
        raise ValueError('Original caller forward binding was not restored')
    return result, dict(request_boundary_checks=requests_checked, score_boundary_checks=scores_checked,
        final_state_restored=True, caller_forward_binding_restored=True, shared_eval_verified=True, model_precision_sha256=digest(precision),
        CPU_fixture_only=cpu_validation, original_guardian_owns_only_bill=True,
        whole_card_scientific_accepted=False, final_scores_and_released_acceptance_pending=True)
