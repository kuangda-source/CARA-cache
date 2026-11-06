"""Complete source-scalar parent requests against independent ordinary controls."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import torch

from wcomr import clean_speed20_r1 as clean
from wcomr.cara_fast_spec_r1 import digest, profile_from
from wcomr.cara_source_lifecycle_estimation_r1 import complete_samples
from wcomr.cara_source_lifecycle_scalar_collection_r1 import execute
from wcomr.cara_source_lifecycle_weights_r1 import current_velocity_weights
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.policy_generator_r1.production_sampling import execute as ordinary
from wcomr.prepared_input import PreparedInputReplay

import check_cara_read_write_point_cpu_r1 as point


@torch.no_grad()
def body(inference, selected, wc, rf, settings, inference_module, runtime, config,
         flow, artifact_root, **unused):
    model, net = inference.pipe.model, inference.pipe.model.net
    scheduler = model.sample_scheduler
    model.config.state_ch = 8

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
    initial = CompleteStateRoundtrip(net, scheduler, torch.zeros(1))
    origin = initial.fingerprint()
    root = Path(__file__).resolve().parents[1]
    design = json.loads((root/'plans/cara_next_stage_20261101/source_lifecycle/V1_CALIBRATION64_DESIGN_R1.json').read_text())
    manifest = json.loads((root/'plans/cara_next_stage_20261101/e1/ENDPOINT7_46_MANIFEST_R1.json').read_text())
    scale_spec = importlib.util.spec_from_file_location('source_scalar_original_UniPC_scale',
        runtime/'cosmos_predict2/_src/predict2/models/fm_solvers_unipc.py')
    scale_module = importlib.util.module_from_spec(scale_spec)
    sys.modules[scale_spec.name] = scale_module
    scale_spec.loader.exec_module(scale_module)
    scale_solver = scale_module.FlowUniPCMultistepScheduler(
        num_train_timesteps=1000, shift=1, use_dynamic_shifting=False)
    scale_solver.set_timesteps(35, device='cpu', shift=5, use_kerras_sigma=True)
    scale = current_velocity_weights(scale_solver)
    assert scale['sigmas'] == manifest['schedule']['sigmas']
    profile = profile_from(manifest['profile'])
    common = dict(runtime=runtime, wc=wc, rf=rf, settings=settings, calibration=None, specs={},
                  inference_module=inference_module, expected_shape=[1, 8, 2, 8, 8], audit=True)
    labels, controls, prepared = [], [], []
    try:
        for member in design['FIT']:
            replay = PreparedInputReplay(inference.pipe._get_data_batch_input)
            for parent in design['parents']:
                output = Path(artifact_root)/(str(flow)+'_'+member+'_'+parent['id'])
                with clean.patched(inference.pipe, '_get_data_batch_input', replay):
                    initial.restore()
                    result = execute(inference, selected[0], profile=profile, policy=parent['policy'],
                                     label_states=parent['states'], member=member, parent_id=parent['id'],
                                     logical_copy_cap_bytes=1 << 30, CPU_storage_cap_bytes=1 << 30,
                                     output=output/'scalar', **common)
                    initial.restore()
                    baseline = ordinary(inference, selected[0], profile=profile, policy=parent['policy'],
                                        output=output/'ordinary', **common)
                assert result['status'] == baseline['status'] == 'COMPLETE'
                assert result['physical_model_pairs'] == 44 and len(result['scalar_labels']) == 8
                assert result['guided_pairs'] == result['solver_steps'] == 36
                assert torch.equal(result['final_latent'], baseline['final_latent'])
                assert Path(result['video_path']).read_bytes() == Path(baseline['video_path']).read_bytes()
                assert [r['actual'] for r in result['semantic_history']] == parent['policy']['actions']
                assert all(r['fallback_reason'] is None for r in result['semantic_history'])
                labels.extend(result['scalar_labels'])
                controls.append(dict(member=member, parent=parent['id'], D=parent['D'],
                                     complete_scalar_pairs=44, ordinary_pairs=36,
                                     final_latent_and_mock_RGB_bitwise_equal=True))
            assert len(replay.calls) == 8 and all(c['prepared'] == replay.calls[0]['prepared'] for c in replay.calls)
            prepared.append(dict(member=member, complete_requests=8, prepared_replay_identical=True))
        packet = dict(schema='CARA_V1_SAME_STATE_SCALAR_LABELS_R1', status='COMPLETE',
                      input_kind='SYNTHETIC_CPU', design_scope_sha256=design['scope_sha256'],
                      schedule_sha256=digest(manifest['schedule']), rows=labels,
                      provenance=dict(teacher='candidate_own_current_state_shadow_D',
                                      teacher_writes_parent=False, target_normalized=False,
                                      target='FP64_MSE_OF_ACTUAL_SAME_STATE_FP32_CFG'))
        samples = complete_samples(packet, design, manifest['schedule'])
        labels_file = Path(artifact_root)/('source-scalar-labels-'+str(flow)+'.json')
        scale_file = Path(artifact_root)/('original-UnIPC-scale-'+str(flow)+'.json')
        candidates_file = Path(artifact_root)/('source-scalar-candidates-'+str(flow)+'.json')
        for file, value in ((labels_file, packet), (scale_file, scale)):
            with file.open('x') as stream:
                json.dump(value, stream, indent=2, allow_nan=False)
                stream.write('\n')
        fitted = subprocess.run([sys.executable, str(root/'scripts/fit_cara_source_lifecycle_v1_r1.py'),
                                 '--labels', str(labels_file), '--weights', str(scale_file),
                                 '--fixture-only', '--output', str(candidates_file)],
                                capture_output=True, text=True, timeout=60)
        assert fitted.returncode == 0, fitted.stderr
        candidates = json.loads(candidates_file.read_text())
        assert candidates['CPU_fixture_only'] and not candidates['endpoint_selection_performed']
        assert len(samples) == 64 and len(candidates['families']) == 3
        initial.restore()
        assert initial.fingerprint() == origin
        return [dict(status='COMPLETE_SOURCE_SCALAR_PARENTS_CPU_PASS', flow=flow,
                     complete_scalar_requests=8, complete_independent_ordinary_requests=8,
                     complete_requests=16, scalar_rows=64, scalar_physical_pairs=352,
                     independent_control_pairs=288, controls=controls, prepared=prepared,
                     packet=packet, original_UniPC_scale=scale,
                     candidates=candidates, caller_restored=True,
                     actual_Cosmos_weights=False, real_video_efficacy=False)]
    finally:
        initial.restore()


def run(runtime, artifact_root, *, actual_modules=False):
    with patch.object(point, 'body', body):
        return point.run(runtime, artifact_root, actual_modules=actual_modules)
