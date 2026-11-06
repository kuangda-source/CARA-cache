"""Complete H-T54 cases; actual module globals with declared Toy model modules."""
import copy
from dataclasses import asdict
import importlib.util
from pathlib import Path
import types

import torch

from wcomr.cfg_paired_probe_forward import (
    forced_reference, RF_PATH,
)
from wcomr.mid_coverage import tree_digest
from wcomr.prepared_input import input_signatures
from wcomr.cfg_paired_probe_production import compile_production, ProductionPairedExecutor


FIELDS = ('cnt', 'accumulated_rel_l1_distance', 'residual_cache',
          'probe_residual_cache', 'residual_window', 'probe_residual_window',
          'previous_internal_states', 'previous_input', 'previous_output',
          'resume_flag', 'affline_scale_log_info', 'affline_emb', 'crossattn_emb',
          'probe_depth')


def load(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def state(net):
    names = sorted(set(FIELDS) | {n for n in vars(net) if n.startswith('worldcache_')})
    return {'WC': {n: getattr(net, n) for n in names},
            'buffers': {n: b for n, b in net.named_buffers()},
            'eval': [m.training for m in net.modules()]}


def exercise(*, inference, wc, flow, runtime, **kwargs):
    # Never mutate the parent fixture model: check_full_sampling verifies that.
    from cosmos_predict2._src.predict2.inference import worldcache_utils as actual_wc
    from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as actual_rf
    wc = actual_wc
    base = copy.deepcopy(inference.pipe.model.net)
    namespace = dict(wc.worldcache_mini_train_dit_forward.__globals__)
    load('check_full_sampling').load_functions(runtime / 'cosmos_predict2/_src/predict2/inference/worldcache_utils.py',
                                              ['compute_saliency_map'], namespace)
    observer_events = []
    observer_fault = [None]
    def before(net, slot, args, kwargs):
        if observer_fault[0] == 'before_second' and slot == 1:
            raise ValueError('Injected second before observer failure')
        observer_events.append({'kind':'before', 'slot':slot, 'signature':input_signatures(args, kwargs)})
    def after(net, slot, value):
        if observer_fault[0] == 'after_first' and slot == 0:
            raise ValueError('Injected first after observer failure')
        observer_events.append({'kind':'after', 'slot':slot, 'output_sha256':tree_digest(value)})
    net_generator, denoise_generator, compiler = compile_production(runtime, wc, actual_rf, before=before, after=after)
    denoise_original = actual_rf.Video2WorldModelRectifiedFlow.denoise
    references = {a: forced_reference(runtime, namespace, a) for a in ('CC', 'DD')}
    base.prepare_embedded_sequence = lambda x, **kw: (x[:, :2048].movedim(1, -1).contiguous(), None, None)
    # apply_worldcache takes network calls, not requested sampler updates.
    # Full sampling supplies 2*35=70; retain that exact two-CFG cycle here.
    wc.apply_worldcache(base, num_steps=70, ret_ratio=.06, rel_l1_thresh=.08,
                        probe_depth=2, osi_enabled=True, flow_enabled=flow, flow_scale=1)
    base.worldcache_saliency_enabled = True
    base.worldcache_saliency_weight = 5.0
    base.worldcache_dynamic_decay = True
    base.eval()
    shape = (1, 2048, 2, 8, 8)
    noise = torch.linspace(-.8, .9, 2048 * 2 * 8 * 8).reshape(shape)
    latent = noise * .72 + .08
    condition_class, class_sha = load('check_rv0_video_actions_cpu').pinned_video_condition(runtime, namespace['DataType'])
    conditions = tuple(condition_class(crossattn_emb=torch.ones(1, 3, 4) * (1 + s),
        fps=torch.tensor([16.]), use_video_condition=torch.tensor([True]),
        padding_mask=torch.zeros(1, 1, 8, 8)).set_video_condition(
            noise * .1 + s * .02, 0, 0, num_conditional_frames=1) for s in (0, 1))
    input_state = lambda: tree_digest({'noise': noise, 'latent': latent,
        'conditions': [vars(c) for c in conditions]})
    input_before = input_state()
    records = []
    def model(net):
        m = types.SimpleNamespace(net=net, tensor_kwargs={'device': 'cpu', 'dtype': torch.float32},
            config=types.SimpleNamespace(conditional_frame_timestep=.15, denoise_replace_gt_frames=True))
        m.denoise = types.MethodType(denoise_original, m)
        return m
    def executor_for(m):
        return ProductionPairedExecutor(m, denoise_generator, torch,
            wc_forward=wc.worldcache_mini_train_dit_forward, rf_denoise=denoise_original)
    def original_pair(m, xt, ts):
        return tuple(denoise_original(m, noise, xt, ts, c) for c in conditions)
    def block_counts(net):
        return [float(b.visits) for b in net.blocks]
    with torch.no_grad():
        # Two protected initialization comparisons, one in each flow configuration.
        initial_ref, initial_new = model(copy.deepcopy(base)), model(copy.deepcopy(base))
        initial_ref.net.forward = types.MethodType(references['DD'], initial_ref.net)
        initial_new.net.forward = types.MethodType(wc.worldcache_mini_train_dit_forward, initial_new.net)
        executor = executor_for(initial_new)
        initial_rng = torch.get_rng_state().clone()
        expected = original_pair(initial_ref, latent, torch.tensor([.8]))
        def forbidden(_):
            raise AssertionError('Protected pair called selector')
        observed = executor.pair(noise, latent, torch.tensor([.8]), conditions, forbidden)
        assert all(torch.equal(a, b) for a, b in zip(expected, observed))
        assert torch.equal(expected[0] + 7 * (expected[0] - expected[1]),
                           observed[0] + 7 * (observed[0] - observed[1]))
        assert torch.equal(initial_rng, torch.get_rng_state()) and input_state() == input_before
        assert tree_digest(state(initial_ref.net)) == tree_digest(state(initial_new.net))
        assert executor.last['protected'] and executor.last['action'] == 'DD'
        assert block_counts(initial_new.net) == [2., 2., 2., 2.]
        records.append({'kind': 'protected_initialization', 'flow': flow, 'status': 'PASS',
                        'counter': initial_new.net.cnt, 'block_visits': block_counts(initial_new.net),
                        'original_order_outputs_sha256': tree_digest(expected),
                        'paired_order_outputs_sha256': tree_digest(observed),
                        'original_order_state_sha256': tree_digest(state(initial_ref.net)),
                        'paired_order_state_sha256': tree_digest(state(initial_new.net)),
                        'CPU_RNG_equal': True, 'input_conditions_equal': True, 'guided_FP32_equal': True})
        # Build both CFG histories with the entire preregistered 22 updates.
        anchor = model(base)
        anchor.net.forward = types.MethodType(references['DD'], anchor.net)
        for step in range(22):
            original_pair(anchor, latent * (1 + .003 * step), torch.tensor([.8 - .02 * step]))
        assert anchor.net.cnt == 44
        for action in ('CC', 'DD'):
            for repetition in range(2):
                ref, new = model(copy.deepcopy(base)), model(copy.deepcopy(base))
                ref.net.forward = types.MethodType(references[action], ref.net)
                # The prototype directly compiles the unchanged body; the saved
                # net.forward is restored to the actual pinned WC method here.
                new.net.forward = types.MethodType(wc.worldcache_mini_train_dit_forward, new.net)
                executor = executor_for(new)
                before_ref, before_new = block_counts(ref.net), block_counts(new.net)
                rng = torch.get_rng_state().clone()
                reference_events = []
                raw_reference = references[action]
                def observed_reference(net, *args, **kwargs):
                    slot = int(net.cnt) % 2
                    reference_events.append({'kind':'before','slot':slot,'signature':input_signatures(args,kwargs)})
                    value = raw_reference(net,*args,**kwargs)
                    reference_events.append({'kind':'after','slot':slot,'output_sha256':tree_digest(value)})
                    return value
                ref.net.forward = types.MethodType(observed_reference, ref.net)
                expected = original_pair(ref, latent, torch.tensor([.34]))
                assert torch.equal(rng, torch.get_rng_state())
                saw = []
                def choose(packets):
                    saw.extend(packets)
                    assert [p.slot for p in packets] == [0, 1]
                    assert [p.counter for p in packets] == [44, 45]
                    # Before decision, only both prefixes have been paid for.
                    delta = [a-b for a, b in zip(block_counts(new.net), before_new)]
                    assert delta == [2., 2., 0., 0.]
                    return action
                observer_start = len(observer_events)
                observed = executor.pair(noise, latent, torch.tensor([.34]), conditions, choose)
                paired_events = observer_events[observer_start:]
                assert [(r['kind'],r['slot']) for r in paired_events] == [('before',0),('before',1),('after',0),('after',1)]
                assert [(r['kind'],r['slot']) for r in reference_events] == [('before',0),('after',0),('before',1),('after',1)]
                assert {(r['kind'],r['slot']):r for r in paired_events} == {(r['kind'],r['slot']):r for r in reference_events}
                assert len(saw) == 2 and not executor.last['protected']
                assert all(torch.equal(a, b) for a, b in zip(expected, observed))
                # Keep the actual FP32 arithmetic ordering used by Cosmos.
                guided_ref = expected[0] + 7 * (expected[0] - expected[1])
                guided_new = observed[0] + 7 * (observed[0] - observed[1])
                assert torch.equal(guided_ref, guided_new)
                assert torch.equal(rng, torch.get_rng_state())
                assert input_state() == input_before
                digest_ref, digest_new = tree_digest(state(ref.net)), tree_digest(state(new.net))
                assert digest_ref == digest_new
                visits_ref = [a-b for a, b in zip(block_counts(ref.net), before_ref)]
                visits_new = [a-b for a, b in zip(block_counts(new.net), before_new)]
                assert visits_ref == visits_new == ([2., 2., 0., 0.] if action == 'CC' else [2., 2., 2., 2.])
                assert ref.net.cnt == new.net.cnt == 46
                records.append({'kind': 'main_pair', 'flow': flow, 'action': action,
                    'repetition': repetition, 'status': 'PASS', 'WC_and_buffer_digest': digest_new,
                    'original_order_outputs_sha256': tree_digest(expected),
                    'paired_order_outputs_sha256': tree_digest(observed),
                    'original_order_state_sha256': digest_ref, 'paired_order_state_sha256': digest_new,
                    'original_order_guided_sha256': tree_digest(guided_ref),
                    'paired_order_guided_sha256': tree_digest(guided_new),
                    'outputs_equal': True, 'guided_FP32_equal': True, 'input_conditions_equal': True,
                    'CPU_RNG_equal': True, 'counter': new.net.cnt, 'block_visit_delta': visits_new,
                    'paid_probes': [asdict(p) for p in saw],
                    'reference_observer_events': reference_events, 'paired_observer_events': paired_events,
                    'observer_per_branch_input_output_equal': True})
        for failure in ('selector_exception', 'mixed_action', 'counter_mutation', 'outer_net_hook',
                        'forward_attribute_wrapper', 'denoise_attribute_wrapper', 'before_second', 'after_first'):
            m = model(copy.deepcopy(base))
            m.net.forward = types.MethodType(wc.worldcache_mini_train_dit_forward, m.net)
            executor = executor_for(m)
            def choose(_):
                if failure == 'selector_exception':
                    raise ValueError('Injected selector exception')
                if failure == 'counter_mutation':
                    m.net.cnt = -123
                return 'DC' if failure == 'mixed_action' else 'CC'
            hook = m.net.register_forward_hook(lambda *a: None) if failure == 'outer_net_hook' else None
            if failure == 'forward_attribute_wrapper':
                original = m.net.forward
                m.net.forward = lambda *args, **kwargs: original(*args, **kwargs)
            if failure == 'denoise_attribute_wrapper':
                original = m.denoise
                m.denoise = lambda *args, **kwargs: original(*args, **kwargs)
            observer_fault[0] = failure if failure in ('before_second', 'after_first') else None
            try:
                executor.pair(noise, latent, torch.tensor([.34]), conditions, choose)
            except ValueError as error:
                reason = str(error)
            else:
                raise AssertionError('Failure case returned output: ' + failure)
            assert executor.poisoned
            try:
                executor.pair(noise, latent, torch.tensor([.34]), conditions, lambda _: 'DD')
            except ValueError as error:
                assert 'Poisoned' in str(error)
            else:
                raise AssertionError('Poisoned executor continued')
            if hook is not None:
                hook.remove()
            observer_fault[0] = None
            records.append({'kind': 'failure_control', 'flow': flow, 'failure': failure,
                'status': 'EXPECTED_REJECTION', 'reason': reason, 'poisoned_continuation_rejected': True,
                'whole_fixture_copy_discarded': True, 'arbitrary_fault_rollback_claim': False})
    assert input_state() == input_before
    assert not torch.cuda.is_initialized()
    records.append({'kind': 'source_contract', 'flow': flow, 'status': 'PASS',
                    'compiler': dict(compiler), 'pinned_video_class_AST_SHA': class_sha,
                    'Toy_weights_attention_condition_construction': True})
    return records


def run(runtime):
    runtime = Path(runtime)
    records = load('check_full_sampling').run(runtime,
        exercise=lambda **kwargs: exercise(runtime=runtime, **kwargs))
    # run() returns a wrapped receipt in the historical helper; retain all rows.
    return records
