"""Optional F19 diagnostic spans on an already constructed policy owner.

No action changes, launch, model loading, or clean-latency claim. The existing
profiler owns CUDA event timing; CPU timing is only an instrumentation control.
"""
from contextlib import contextmanager
from functools import wraps

from .deployment_profile_r1 import RequestProfile


@contextmanager
def profile_policy_owner(owner, scheduler, *, device='cpu'):
    readout = owner.readout
    net_function = owner.executor.denoise.__globals__['_paired_net']
    namespaces = [net_function.__globals__, readout.warp.__globals__]
    patches = []
    with RequestProfile(device=device) as profile:
        try:
            original_pair = owner.pair
            pair_was_owned = 'pair' in vars(owner)

            @wraps(original_pair)
            def pair(*args, **kwargs):
                step = readout.completed+1
                action = owner.policy['actions'][step-1]
                first_row = len(profile.rows)
                try:
                    with profile.span('pair_'+action):
                        return original_pair(*args, **kwargs)
                finally:
                    for row, _ in profile.rows[first_row:]:
                        row.update(update=step, planned_action=action)

            owner.pair = pair
            for i, block in enumerate(owner.net.blocks):
                profile.bind(block, 'forward', 'probe_shallow' if i < owner.net.probe_depth else 'deep_block')
            profile.bind(owner.net.final_layer, 'forward', 'output_head')
            profile.bind(scheduler, 'step', 'solver_update')
            profile.bind(readout, 'end', 'RF_conversion_and_fusion_inclusive')
            # These compiled namespaces are per-owner, not the pinned WC module.
            for namespace in namespaces:
                for name in ('compute_saliency_map', 'compute_optimal_gamma',
                             'estimate_optical_flow', 'warp_feature'):
                    original = namespace[name]
                    def measured(*args, _function=original, _name=name, **kwargs):
                        with profile.span(_name):
                            return _function(*args, **kwargs)
                    namespace[name] = measured
                    patches.append((namespace, name, original))
            for name in ('_mf_a_prewarp', '_mf_a_hidden', '_mf_a_output'):
                namespace = net_function.__globals__
                original = namespace[name]
                def observed(*args, _function=original, _name=name, **kwargs):
                    with profile.span(_name+'_inclusive'):
                        return _function(*args, **kwargs)
                namespace[name] = observed
                patches.append((namespace, name, original))
            yield profile
        finally:
            for namespace, name, original in reversed(patches):
                namespace[name] = original
            if 'original_pair' in locals():
                if pair_was_owned:
                    owner.pair = original_pair
                else:
                    del owner.pair
