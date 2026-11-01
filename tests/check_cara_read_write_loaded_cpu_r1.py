"""Full14 tiny sampling through the actual M1 loaded-model entry boundary."""
import json
from pathlib import Path

import torch

from wcomr import clean_speed20_r1 as clean
from wcomr.cara_fast_spec_r1 import digest
from wcomr.cara_read_write_plan_r1 import build
from wcomr.cara_read_write_runner_r1 import collect_loaded
from wcomr.cara_s_endpoint_runner_r1 import observed_precision
from wcomr.h0_mode import mode_snapshot

import check_cara_read_write_collection_cpu_r1 as fixture

ROOT = Path(__file__).resolve().parents[1]


@torch.no_grad()
def loaded_body(inference, selected, wc, rf, settings, inference_module, runtime, config, flow, artifact_root,
                *, actual_arguments=False, target_update=8):
    model, net = inference.pipe.model, inference.pipe.model.net
    model.precision = torch.float32
    net.use_wan_fp32_strategy = False
    model.config.conditional_frame_timestep = .1
    card = build(json.loads((ROOT/'plans/cara_next_stage_20261101/e1/ENDPOINT7_46_MANIFEST_R1.json').read_text()))
    if target_update == 20:
        from wcomr.cara_source_lifecycle_p0_plan_r1 import execution_scope
        card = execution_scope(json.loads((ROOT/'plans/cara_next_stage_20261101/e1/ENDPOINT7_46_MANIFEST_R1.json').read_text()))
    assert card['target_update'] == target_update
    if actual_arguments:
        from cosmos_predict2.config import InferenceArguments
        samples = {row['name']:InferenceArguments.model_validate({**{k:v for k,v in row.items() if k != 'partition'},
            'resolution':'16,16'}) for row in card['inputs']}
    else:
        samples = {name:fixture.TinyArguments(name=name, prompt=name) for name in card['FIT']}

    def native(self, *args, **kwargs):
        threshold = self.worldcache_rel_l1_thresh
        self.worldcache_rel_l1_thresh = -1.
        try:
            return wc.worldcache_mini_train_dit_forward(self, *args, **kwargs)
        finally:
            self.worldcache_rel_l1_thresh = threshold

    class Storage:
        def __init__(self, fail=False, parameter=False):
            self.calls, self.fail = 0, fail
            self.parameter = parameter

        def check(self):
            self.calls += 1
            if self.fail:
                raise OSError(28, 'CPU private storage low-water')
            if self.parameter:
                next(net.parameters()).add_(0)

    context = dict(scope_sha256=card['scope_sha256'], host='two_card', CPU_fixture_only=True,
        launch_id='CPU_ONLY_LOADED_M1', source_revision='CPU_ONLY_SOURCE', admission_sha256='CPU_NO_GPU',
        model_precision_sha256=digest(observed_precision(model)))
    common = dict(runtime=runtime, wc=wc, rf=rf, inference_module=inference_module,
        expected_shape=[1,8,2,8,8], CPU_native=native)
    output = Path(artifact_root)/('loaded_'+str(flow))
    output.mkdir(parents=True, exist_ok=False)
    args = dict(inference=inference, samples=samples, card=card, common=common, output=output,
        context=context, storage=Storage(), mode_types=mode_snapshot(net)['module_types'],
        snapshot_limits=dict(logical_copy_bytes=1 << 30, total_CPU_images_bytes=1 << 30), cpu_validation=True)
    owned_forward, original_forward = 'forward' in vars(net), vars(net).get('forward')
    try:
        state, evidence = collect_loaded(**args)
        assert len(state['rows']) == evidence['request_boundary_checks'] == 14
        assert state['physical_model_pairs'] == 512 and args['storage'].calls == 15
        assert evidence['final_state_restored'] and evidence['shared_eval_verified']
        try:
            collect_loaded(**args)
        except ValueError as error:
            assert 'recover only' in str(error)
        else:
            raise AssertionError('Original collection replayed')
        for fault in ('precision', 'mode', 'storage', 'parameter'):
            target = output/fault
            target.mkdir()
            modified = {**args, 'output':target, 'context':dict(context),
                'storage':Storage(fault == 'storage', fault == 'parameter')}
            if fault == 'precision':
                modified['context']['model_precision_sha256'] = '0'*64
            if fault == 'mode':
                modified['mode_types'] = {'CPU.invalid.Module':1}
            try:
                collect_loaded(**modified)
            except (ValueError, OSError) as error:
                assert {'precision':'precision differs', 'mode':'topology differs', 'storage':'low-water',
                        'parameter':'parameters changed'}[fault] in str(error)
            else:
                raise AssertionError('M1 loaded boundary accepted '+fault)
            failed = target/'read-write-collection.json'
            if fault in ('storage', 'parameter'):
                failure = json.loads(failed.read_text())
                assert failure['status'] == 'FAILED_NO_REPLAY' and failure['rows'][0]['status'] == 'TECH_FAILED'
                assert all(r['status'] == 'NOT_REACHED' for r in failure['rows'][1:])
                assert not list((target/'B').glob('*.pt'))
            else:
                assert not failed.exists()
        return [dict(status='FULL14_LOADED_M1_TINY_CPU_PASS', flow=flow,
            target_update=target_update,
            complete_paths=14, physical_model_pairs=512, request_boundary_checks=14, storage_checks=15,
            final_state_restored=True, shared_eval_verified=True, replay_refused=True,
            precision_mode_storage_parameter_refusals=True, actual_Cosmos_arguments=actual_arguments,
            actual_Cosmos_weights=False, real_encoded_video=False, GPU_submissions=0)]
    finally:
        if owned_forward:
            net.forward = original_forward
        else:
            vars(net).pop('forward', None)


def run(runtime, artifact_root, *, actual_modules=False, target_update=8):
    original = fixture.collect_body
    fixture.collect_body = loaded_body
    try:
        return fixture.run(runtime, artifact_root, actual_modules=actual_modules, target_update=target_update)
    finally:
        fixture.collect_body = original
