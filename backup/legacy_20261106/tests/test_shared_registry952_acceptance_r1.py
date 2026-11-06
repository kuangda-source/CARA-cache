"""Synthetic analyzer controls only; never read the running original CPU job."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load_analyzer():
    path = ROOT / 'scripts/accept_wc_shared_registry952_local_cpu_r1.py'
    spec = importlib.util.spec_from_file_location('registry952_analyzer_controls', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture(root):
    source = root / 'source'
    grid_ref = 'manifests/wc_paper_N05_core66_preregistration_r1_20261016.json'
    simple_ref = 'configs/wc_simple26d_memory_full36_r2_20261015.json'
    for ref in (grid_ref, simple_ref):
        path = source / ref
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((ROOT / ref).read_bytes())
    code = source / 'synthetic.py'
    code.write_text('# Synthetic analyzer fixture, not actual execution evidence\n')
    binding = {'synthetic.py': hashlib.sha256(code.read_bytes()).hexdigest()}
    grid = json.loads((source / grid_ref).read_text())
    simple = json.loads((source / simple_ref).read_text())
    methods = [x['id'] for x in grid['methods']] + simple['methods']
    scenes = ['AV28_CPU', 'Human_CPU', 'misc_CPU', 'AV51_CPU']
    outputs = []

    def mock_file(folder):
        path = root / folder / 'synthetic.mp4'
        path.parent.mkdir(parents=True, exist_ok=True)
        data = dict(CPU_MOCK_WRITER_NOT_VIDEO=True, value=dict(shape=[3, 93, 16, 16]))
        path.write_text(json.dumps(data))
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        outputs.append(dict(path=str(path.relative_to(root)), sha256=digest, data=data, error=None))
        return str(path), digest

    flows = []
    for flag in (False, True):
        rows, bridges = [], []
        for scene in scenes:
            for method in methods:
                updates = int(grid['actual_native_updates'][method[6:]]) if method.startswith('NATIVE') else 36
                for seed in (0, 17, 43):
                    a, digest = mock_file(f'{flag}/{scene}/{method}/{seed}/audit')
                    b, _ = mock_file(f'{flag}/{scene}/{method}/{seed}/lean')
                    row = dict(scene=scene, method=method, seed=seed, actual_sampler_seed=seed,
                        audit_lean_final_actions_Ahistory_sourcehistory_mock_equal=True,
                        components_released=True, actual_updates=updates,
                        guided_sha256=['synthetic-guided'] * updates,
                        installed_contexts=[[scene, 'synthetic', 'fixed-seed0-request' if seed == 0
                                             else 'frozen-input-seed' + str(seed)]],
                        native_block_CFG_counts={'first': updates * 2, 'last': updates * 2},
                        semantic_plan=simple['plans'].get(method),
                        audit_mock_video_path=a, lean_mock_video_path=b, mock_video_sha256=digest,
                        initial_noise_sha256=hashlib.sha256((scene + str(seed)).encode()).hexdigest())
                    rows.append(row)
                    if seed == 0:
                        path, h = mock_file(f'{flag}/{scene}/{method}/{seed}/legacy')
                        bridges.append(dict(scene=scene, method=method,
                            all_guided_final_actions_Ahistory_sourcehistory_mock_equal=True,
                            original_guided_count=updates, mock_video_path=path, mock_video_sha256=h))
        flows.append(dict(flow=flag, status='PASS', complete_CPU_paths=476,
                          ordinary_pairs=16408, CFG_calls=32816,
                          audit_lean_checks=rows, seed0_legacy_bridges=bridges))
    value = dict(status='FROZEN_SHARED_FULL952_LOCAL_REGISTRY_CPU_PASS_NOT_PRODUCTION',
        source_revision='SYNTHETIC_FIXTURE', source_sha256=binding, runtime_source_sha256={},
        actual_CPU_paths=952, ordinary_pairs=32816, CFG_calls=65632,
        available_methods=methods, seeds=[0, 17, 43], checks=flows)
    value.update({k: False for k in ('CUDA_initialized', 'production_CPU_accepted',
        'real_video_quality_or_speed_claim', 'final_inputs_selected', 'final_methods_selected',
        'weights_loaded', 'real_videos_generated', 'GPU_submissions', 'SSH_queries', 'ledger_written')})
    launch = dict(pid=987654, source_revision='SYNTHETIC_FIXTURE', first_collection_not_before_unix=1,
        test_source_ref='source', runtime_ref='runtime', payload_sha256=binding,
        registration_sha256='synthetic-registration', result_ref='result.json', exit_ref='exit.json')
    end = dict(pid=987654, exit_code=0, result_sha256='synthetic-result',
               source_revision='SYNTHETIC_FIXTURE', source_sha256=binding,
               started_unix=0, ended_unix=1)
    return dict(status='SHARED_REGISTRY952_ORIGINAL_LOCAL_CPU_ONCE_CAPTURE', at_unix=2,
        launch=launch, original_handle_confirmed_live_now=False,
        payload_verified={'synthetic.py': True}, registration_sha256='synthetic-registration',
        files={'exit.json': dict(exists=True, data=end),
               'result.json': dict(exists=True, data=value, sha256='synthetic-result')}, mock_outputs=outputs)


class IndependentAcceptance(unittest.TestCase):
    def test_complete_synthetic_matrix_and_eight_corruptions(self):
        analyzer = load_analyzer()
        with tempfile.TemporaryDirectory(prefix='wc_registry952_synthetic_analysis_') as directory:
            root = Path(directory)
            analyzer.ROOT = root
            original = fixture(root)
            result = analyzer.accept(original)
            self.assertEqual(result['actual_CPU_paths'], 952)
            self.assertEqual(result['native_grid_count_controls'], 72)
            self.assertFalse(result['production_CPU_accepted'])
            mutations = [
                lambda v: v['files']['result.json']['data']['checks'][0]['audit_lean_checks'].pop(),
                lambda v: v['files']['result.json']['data'].update(actual_CPU_paths=951),
                lambda v: v['files']['result.json']['data']['checks'][0]['audit_lean_checks'][0].update(actual_sampler_seed=43),
                lambda v: v['files']['result.json']['data']['checks'][0]['audit_lean_checks'][0].update(components_released=False),
                lambda v: v['files']['result.json']['data']['checks'][0]['audit_lean_checks'][0]['native_block_CFG_counts'].update(first=2),
                lambda v: v['files']['result.json']['data']['checks'][0]['audit_lean_checks'][1]['installed_contexts'][0].__setitem__(2, 'fixed-seed0-request'),
                lambda v: v['files']['exit.json']['data'].update(result_sha256='different'),
                lambda v: v.update(original_handle_confirmed_live_now=True),
            ]
            for index, change in enumerate(mutations):
                with self.subTest(mutation=index):
                    broken = copy.deepcopy(original)
                    change(broken)
                    with self.assertRaises(AssertionError):
                        analyzer.accept(broken)


if __name__ == '__main__':
    unittest.main()
