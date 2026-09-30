import json
import os
from pathlib import Path
import time

import pytest
import torch
from safetensors.torch import save_file, load_file
from wcomr.lora_cpu_fusion import file_hash, prepare_inputs, fuse


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', '')
    upstream = Path(os.environ.get('L0_UPSTREAM_MERGER', '.sync/l0_sources_20261001/code/LongLive-Plug/scripts/merge_lora.py')).resolve()
    assert file_hash(upstream) == '7b5b6438dd71e36ca30d356313fc7fbaabe60afdcc66f77c527db023a8c2cbec'
    base = tmp_path / 'base'; base.mkdir()
    cache = tmp_path / 'cache'; cache.mkdir()
    save_file({'layer.weight': torch.arange(12.).reshape(4, 3),
               'condition.weight': torch.tensor([9.])}, str(base / 's1.safetensors'))
    save_file({'aux.weight': torch.tensor([7.])}, str(base / 's2.safetensors'))
    (base / 'config.json').write_text('{}')
    (base / 'index.json').write_text(json.dumps({'weight_map': {'layer.weight': 's1.safetensors',
        'condition.weight': 's1.safetensors', 'aux.weight': 's2.safetensors'}}))
    (base / 'vae.bin').write_bytes(b'conditioning asset')
    def identity(p):
        return {'path': p.name, 'size': p.stat().st_size, 'lfs': {'oid': file_hash(p)}}
    adapters = {}
    a = torch.tensor([[1., 2., 3.], [4., 5., 6.]])
    b = torch.tensor([[1., 0.], [0., 1.], [1., 1.], [2., 1.]])
    for name, multiplier in [('cfg', 1.), ('few_step', 2.)]:
        repo = 'test/' + name; revision = 'r1'
        path = cache / ('models--' + repo.replace('/', '--')) / 'snapshots' / revision
        path.mkdir(parents=True)
        save_file({'base_model.model.layer.lora_A.weight': a * multiplier,
                   'base_model.model.layer.lora_B.weight': b}, str(path / 'adapter_model.safetensors'))
        (path / 'adapter_config.json').write_text(json.dumps({'peft_type': 'LORA', 'bias': 'none',
            'r': 2, 'lora_alpha': 6, 'target_modules': ['layer'], 'base_model_name_or_path': 'test/base'}))
        adapters[name] = {'repo': repo, 'revision': revision, 'files': [identity(p) for p in sorted(path.iterdir())]}
    protocol = {'base_repo': 'test/base', 'base_files': [identity(p) for p in sorted(base.iterdir())],
        'index': 'index.json', 'shards': ['s1.safetensors', 's2.safetensors'], 'adapters': adapters,
        'upstream_sha256': file_hash(upstream), 'cpu_threads': 1,
        'recipes': [{'name': 'cfg_only', 'adapters': [{'name': 'cfg', 'weight': 1.}]},
                    {'name': 'few_step_cfg', 'adapters': [{'name': 'few_step', 'weight': 1.},
                                                         {'name': 'cfg', 'weight': .5}]}],
        'formula_rtol': 1e-5, 'formula_atol': 1e-6, 'auxiliary_paths': ['vae.bin']}
    return protocol, base, cache, upstream, tmp_path / 'new-output', a, b


def run(data):
    protocol, base, cache, upstream, output, a, b = data
    paths, index, records = prepare_inputs(protocol, base, cache, upstream, output)
    return fuse(protocol, base, paths, upstream, output, index,
                {'started_unix': time.time(), 'input_integrity': records, 'gpu_workload_started': False})


def test_two_real_serialized_recipes_and_all_untargeted_weights(fixture):
    protocol, base, cache, upstream, output, a, b = fixture
    before = {p.name: file_hash(p) for p in base.iterdir()}
    result = run(fixture)
    assert result['status'] == 'CPU_FUSION_COMPLETE_NOT_MODEL_LOAD_TASK_OR_GPU_READY'
    original = load_file(str(base / 's1.safetensors'))
    for name, scale in [('cfg_only', 3.), ('few_step_cfg', 7.5)]:
        saved = load_file(str(output / name / 's1.safetensors'))
        assert torch.equal(saved['layer.weight'], original['layer.weight'] + scale * b @ a)
        assert torch.equal(saved['condition.weight'], original['condition.weight'])
        assert torch.equal(load_file(str(output / name / 's2.safetensors'))['aux.weight'], torch.tensor([7.]))
        assert (output / name / 'vae.bin').is_symlink()
        assert (output / name / 'vae.bin').read_bytes() == (base / 'vae.bin').read_bytes()
        assert json.loads((output / name / 'index.json').read_text()) == json.loads((base / 'index.json').read_text())
    assert {p.name: file_hash(p) for p in base.iterdir()} == before
    assert all(len(arm['tensors']) == 3 and len(arm['shards']) == 2 for arm in result['arms'])
    assert not torch.cuda.is_initialized()


def test_corrupted_input_refused_without_output(fixture):
    protocol, base, cache, upstream, output, *_ = fixture
    (base / 'vae.bin').write_bytes(b'wrong')
    with pytest.raises(ValueError, match='byte count'):
        prepare_inputs(protocol, base, cache, upstream, output)
    assert not output.exists()


def test_existing_output_refused(fixture):
    protocol, base, cache, upstream, output, *_ = fixture
    output.mkdir(); (output / 'keep').write_text('old')
    with pytest.raises(ValueError, match='new output'):
        prepare_inputs(protocol, base, cache, upstream, output)
    assert (output / 'keep').read_text() == 'old'


def test_output_inside_base_refused(fixture):
    protocol, base, cache, upstream, output, *_ = fixture
    with pytest.raises(ValueError, match='separate'):
        prepare_inputs(protocol, base, cache, upstream, base / 'new')


def test_wrong_upstream_refused_before_import(fixture, tmp_path):
    protocol, base, cache, upstream, output, *_ = fixture
    p = tmp_path / 'wrong.py'; p.write_text('raise RuntimeError("must never execute")')
    with pytest.raises(ValueError, match='Upstream merger digest'):
        prepare_inputs(protocol, base, cache, p, output)
    assert not output.exists()


def test_partial_adapter_refused_without_output(fixture):
    protocol, base, cache, upstream, output, *_ = fixture
    row = protocol['adapters']['cfg']
    p = cache / ('models--' + row['repo'].replace('/', '--')) / 'snapshots' / row['revision'] / 'adapter_model.safetensors'
    p.unlink()
    with pytest.raises(FileNotFoundError):
        prepare_inputs(protocol, base, cache, upstream, output)
    assert not output.exists()


def test_duplicate_arm_refused_without_output(fixture):
    protocol, base, cache, upstream, output, *_ = fixture
    protocol['recipes'].append(protocol['recipes'][0])
    with pytest.raises(ValueError, match='duplicate recipe'):
        prepare_inputs(protocol, base, cache, upstream, output)
    assert not output.exists()


def test_nonfinite_adapter_refused(fixture):
    protocol, base, cache, upstream, output, a, b = fixture
    row = protocol['adapters']['cfg']
    p = cache / ('models--' + row['repo'].replace('/', '--')) / 'snapshots' / row['revision'] / 'adapter_model.safetensors'
    a[0, 0] = float('nan')
    save_file({'base_model.model.layer.lora_A.weight': a,
               'base_model.model.layer.lora_B.weight': b}, str(p))
    for f in row['files']:
        if f['path'] == p.name: f['lfs']['oid'] = file_hash(p)
    with pytest.raises(ValueError, match='Nonfinite adapter'):
        run(fixture)
    assert not (output / 'cfg_only' / 's1.safetensors').exists()
    assert not torch.cuda.is_initialized()
