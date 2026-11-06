"""Loaded tiny P1 algorithm plus original offline93-frame internal score children.

Tiny sampler outputs seed explicit synthetic93x64 media. That fixture encoding
is not a model video or a production resize. Operation-cost ticks are synthetic,
separate from measured CPU wall time and never a GPU quote.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import patch

import torch

from wcomr import clean_speed20_r1 as clean
from wcomr.cara_budget_original_handles_r1 import bind_original_process, observe_original_process
from wcomr.cara_budget_search_journal_r1 import create_record
from wcomr.cara_budget_supervisor_r1 import stop_original
from wcomr.cara_fast_fidelity_r1 import file_sha
from wcomr.cara_fast_spec_r1 import digest
from wcomr.cara_source_lifecycle_fit_scores_r1 import bind_scorer, accept_internal_scores, SOURCES, WORKER
from wcomr.cara_source_lifecycle_p1_plan_r1 import build
from wcomr.cara_source_lifecycle_p1_runner_r1 import collect_loaded
from wcomr.cara_s_endpoint_runner_r1 import observed_precision
from wcomr.h0_mode import mode_snapshot

import check_cara_read_write_point_cpu_r1 as point
from check_cara_s_endpoint_real_video_r1 import write_video

ROOT = Path(__file__).resolve().parents[1]


def score_child(packet, output, *, environment, deadline):
    config = bind_scorer(packet, environment, cpu_validation=True)
    manifest, result_file = output/'manifest.json', output/'scores.json'
    create_record(manifest, config)
    command = [sys.executable, str(ROOT/WORKER), '--manifest', str(manifest),
               '--output', str(result_file), '--cpu-validation']
    started = time.monotonic()
    with (output/'worker.log').open('x') as log:
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='', NVIDIA_VISIBLE_DEVICES='void'))
        identity = bind_original_process(process.pid)
        try:
            code = process.wait(timeout=min(600, max(.01, deadline-time.monotonic())))
        finally:
            stop_original(process, identity)
    observed = observe_original_process(identity)
    assert observed['original_live'] is False
    result = json.loads(result_file.read_bytes()) if result_file.exists() else None
    execution = dict(config_sha256=digest(config), result_sha256=digest(result), exit_code=code,
        original_process_ended=True, GPU_hidden=True, original_identity=identity, original_observation=observed,
        wall_seconds=time.monotonic()-started, source_sha256={p: file_sha(ROOT/p) for p in SOURCES})
    create_record(output/'execution.json', execution)
    assert code == 0, (output/'worker.log').read_text()[-2500:]
    accepted = accept_internal_scores(config, result, execution, cpu_validation=True)
    create_record(output/'accepted.json', accepted)
    return accepted


@torch.no_grad()
def body(inference, selected, wc, rf, settings, inference_module, runtime, config, flow, artifact_root, **unused):
    model, net = inference.pipe.model, inference.pipe.model.net
    model.config.state_ch = 8
    model.config.conditional_frame_timestep = .1
    model.precision, net.use_wan_fp32_strategy = torch.float32, False

    class Head(torch.nn.Module):
        def forward(self, value, *args, **kwargs):
            return value+.01*value.square()

    net.final_layer = Head().eval()
    net.unpatchify = lambda x: x[:, :, ::2, ::2, :].movedim(-1, 1).contiguous()
    cls, _ = point.load('check_rv0_video_actions_cpu').pinned_video_condition(runtime, wc.DataType)
    model.conditioner.get_condition_with_negative_prompt = lambda batch: tuple(
        cls(crossattn_emb=torch.ones(1, 3, 4)*(1+b), fps=batch['fps'],
            use_video_condition=torch.tensor([True])).set_video_condition(
                torch.zeros(1, 8, 2, 8, 8), 0, 0, num_conditional_frames=0) for b in (0, 1))
    model.get_data_and_condition = lambda batch: (None, torch.zeros(1, 8, 2, 8, 8), None)
    read = lambda p: json.loads((ROOT/p).read_bytes())
    parent = read('plans/cara_next_stage_20261101/e1/ENDPOINT7_46_MANIFEST_R1.json')
    design = read('plans/cara_next_stage_20261101/source_lifecycle/V1_CALIBRATION64_DESIGN_R1.json')
    card = build(parent, design)
    weights = read('reports/cara_v1_frozen_UniPC_current_input_scale_r1_20261102.json')['weights']
    from cosmos_predict2.config import InferenceArguments
    samples = {r['name']: InferenceArguments.model_validate({**{k: v for k, v in r.items() if k != 'partition'},
        'resolution': '16,16'}) for r in card['inputs']}

    def native(self, *args, **kwargs):
        threshold = self.worldcache_rel_l1_thresh
        self.worldcache_rel_l1_thresh = -1.
        try:
            return wc.worldcache_mini_train_dit_forward(self, *args, **kwargs)
        finally:
            self.worldcache_rel_l1_thresh = threshold

    stage = ROOT
    output = Path(artifact_root)/('P1-loaded-'+str(flow))
    output.mkdir(parents=True)
    media_cache = output/'media-cache'
    media_cache.mkdir()

    def writer(video, path, fps):
        import hashlib
        import shutil
        raw = video.detach().float().cpu().contiguous().numpy().tobytes()
        tag = hashlib.sha256(raw).hexdigest()
        source = media_cache/(tag+'.mp4')
        if not source.exists():
            write_video(source, 'P1_EXPLICIT_SYNTHETIC_93x64_'+tag, height=64, width=64)
        # The pinned pipeline passes a filename stem, just like its original
        # save_img_or_video; the public request result already includes .mp4.
        shutil.copyfile(source, str(path)+'.mp4')

    context = dict(scope_sha256=card['scope_sha256'], host='two_card', CPU_fixture_only=True,
        source_revision=json.loads((stage/'registration.json').read_text())['parent_git_revision'],
        launch_id=digest({'synthetic_CPU_only': str(flow)})[:32], admission_sha256='0'*64,
        model_precision_sha256=digest(observed_precision(model)))
    clock = [0.]

    class Storage:
        checks = 0
        def check(self):
            self.checks += 1

    storage = Storage()
    common = dict(runtime=runtime, wc=wc, rf=rf, inference_module=inference_module,
        expected_shape=[1, 8, 2, 8, 8], CPU_native=native)
    environment = dict(torch_home=str(stage.parent/'wc-time-score-CPU-two_card-r1-20261027/torch'),
        piq_site=str(stage.parent/'wc-time-score-CPU-two_card-r1-20261027/site'), weights_sha256={})
    score_calls = []
    deadline = float(os.environ['CARA_V1_P1_CPU_DEADLINE_MONOTONIC'])

    def score(packet, directory):
        result = score_child(packet, directory, environment=environment, deadline=deadline)
        clock[0] += .2
        score_calls.append(dict(packet_sha256=digest(packet), accepted_sha256=digest(result), pairs=2))
        return result

    # Synthetic tick accounting is explicitly isolated from actual CPU clocks.
    # It exercises both calibrated search stages without pricing a GPU from CPU.
    from wcomr.cara_source_lifecycle_p1_requests_r1 import Requests
    execute = Requests.__call__
    def tick(self, slot, directory):
        result = execute(self, slot, directory)
        clock[0] += 10. if slot['kind'] == 'scalar' else 1.
        return result

    started = time.monotonic()
    args = dict(inference=inference, samples=samples, card=card, common=common, context=context,
        output=output/'collection', storage=storage, mode_types=mode_snapshot(net)['module_types'],
        snapshot_limits=dict(logical_copy_bytes=1 << 30, total_CPU_images_bytes=1 << 30),
        weights=weights, score=score, elapsed_seconds=lambda: clock[0],
        query_bounds=dict(path_seconds=1., FIT_score_seconds=.2, overhead_seconds=.01), cpu_validation=True)
    with clean.patched(inference_module, 'save_img_or_video', writer), patch.object(Requests, '__call__', tick):
        result, proof = collect_loaded(**args, create=True, allow_new=True)
        assert 'failure' not in result, result.get('failure')
        assert proof['caller_forward_binding_restored']
        assert result['status'] == 'P1_ALGORITHM_COMPLETE_PENDING_ORIGINAL_RELEASE_SETTLEMENT_AND_SCIENCE'
        assert len(result['source_labels']['rows']) == 64 and len(result['FIT_selected']) == 6
        assert len(result['semantic_positions']) == 146
        assert all(s['configured_search_finished'] for s in result['fair_searches'].values())
        calls_before, clock_before = len(score_calls), clock[0]
        recovered, recovery = collect_loaded(**args, create=False, allow_new=False)
        assert 'failure' not in recovered, recovered.get('failure')
        assert recovered['FIT_selected'] == result['FIT_selected']
        assert recovered['new_callback_calls'] == 0 and recovery['request_boundary_checks'] == recovery['score_boundary_checks'] == 0
        assert recovery['caller_forward_binding_restored']
        assert len(score_calls) == calls_before and clock[0] == clock_before
        owned_forward, original_forward = 'forward' in vars(net), net.forward
        class FailedStorage:
            def check(self):
                raise OSError('CPU storage refusal before the first sampler request')
        try:
            collect_loaded(**{**args, 'output': output/'failed-storage', 'storage': FailedStorage()},
                           create=True, allow_new=True)
        except OSError as error:
            assert 'CPU storage refusal' in str(error)
        else:
            raise AssertionError('Loaded entry ignored storage refusal')
        assert net.forward == original_forward and ('forward' in vars(net)) == owned_forward
        assert not list((output/'failed-storage').rglob('*.pt'))
        assert len(score_calls) == calls_before and clock[0] == clock_before
    return [dict(status='P1_ACTUAL_LOADED_TINY_ALGORITHM_AND_INTERNAL_CPU_SCORES_PASS', flow=flow,
        source_scalar_rows=64, semantic_positions=146, actual_complete_tiny_requests=proof['request_boundary_checks'],
        accepted_internal_FIT_cohorts=score_calls, actual93_frame_metric_pairs=2*len(score_calls),
        source_labels=digest(result['source_labels']), FIT_selected=result['FIT_selected'],
        shared_state_and_parameters_restored=True, recovery_new_physical_and_score_callbacks=0,
        caller_forward_binding_restored_on_success_recovery_and_failure=True,
        actual_Cosmos_arguments=True, real_Alex_weights_on_synthetic_media=True,
        synthetic_media_rule='tiny_output_digest_to_explicit93x64_fixture; not_real_model_video',
        cost_clock='SYNTHETIC_OPERATION_SECONDS_NOT_GPU_QUOTE',
        original_CPU_wall_seconds=time.monotonic()-started, actual_Cosmos_weights=False,
        whole_GPU_entry_accepted=False, scientific_method_efficacy=False, GPU_submissions=0, ledger_written=False)]


def run(runtime, artifact_root):
    with patch.object(point, 'body', body):
        return point.run(runtime, artifact_root, actual_modules=True)
