"""Inspect pinned official BudCache and exercise only its search controller on CPU.

The selected original functions are compiled from an Apache-2.0 source snapshot.
All model, tensor-loss, output and CUDA operations are explicit stand-ins.
"""
import argparse
import ast
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import random
import time
from types import SimpleNamespace
from typing import List

REVISION = '14ba4c5106a17848e757e7b93ad4b4daeb5b742c'
FILES = {
    'LICENSE': 'c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4',
    'launchers/search_wan.sh': '80d35f0c4416fd1dfbf6e5aed6e396853ff9f46a0d0f266967b0d37b51df33f4',
    'configs/search_wan.yaml': '9303408df304766ac39d1e2cc7f41a4ac5169234db4faff24698d3b45e3ab2c7',
    'scripts/stage1_search_wan.py': '7b3414f198549cf650a56619d168a5b58147f3f196eef015c2547b764a8ca372',
    'src/wan/config.py': '267afa8942da8df01dddfb09e33547a1faa3b693d2aa22afa3a5a5cf36a97063',
    'src/wan/wan_generate.py': 'a1467f25f97b9004c98731b0e1ed200dcf7071274951987f98677f5f474ef6f3',
    'src/wan/dit_forward.py': '256c3dd095d7809b4fd043918ebb9a38adb86f6fdbf9b4fbe753b08e5b46879c',
}


def require(value, message):
    if not value:
        raise ValueError(message)


def controller_probe(tree, config, fixture_seed):
    import numpy as np
    # Isolate both RNGs without changing the original controller's random operators.
    python_rng = random.Random(fixture_seed)
    numpy_rng = np.random.RandomState(fixture_seed)
    cfg = SimpleNamespace(**config)
    masks, saved, teacher_calls = [], [], []

    class Model:
        pass

    class Pipeline:
        def __init__(self, **kwargs):
            self.model = Model()

    class Progress:
        def __init__(self, values, **kwargs):
            self.values = values
        def __iter__(self):
            return iter(self.values)
        def set_postfix(self, values):
            pass

    def get_latents(pipe, cfg):
        if not pipe.model.enable_budcache:
            teacher_calls.append(1)
            return 0.0
        schedule = tuple(pipe.model.cache_schedule)
        require(len(schedule) == cfg.steps and sum(schedule) == cfg.nfe, 'Original controller changed quota')
        prefix = max(1, int(cfg.nfe * 0.3))
        require(all(schedule[i] == 1 for i in range(prefix)), 'Original controller changed prefix')
        masks.append(schedule)
        return 1.0  # Deliberately flat synthetic loss; no generated latent/video exists.

    parser = SimpleNamespace(add_argument=lambda *a, **k: None,
        parse_args=lambda: SimpleNamespace(config='PINNED_CPU_FIXTURE'))
    namespace = dict(List=List, copy=copy, hashlib=hashlib, math=math, random=python_rng,
        np=SimpleNamespace(random=numpy_rng), argparse=SimpleNamespace(ArgumentParser=lambda: parser),
        os=SimpleNamespace(path=os.path, environ={'RUN_ID': 'CPU_FIXTURE'}, makedirs=lambda *a, **k: None),
        load_config=lambda path: cfg, model_path=lambda name: 'CPU_STANDIN_NO_WEIGHTS',
        make_search_exp_name_wan=lambda *a: 'CPU_FIXTURE',
        create_logger=lambda *a, **k: SimpleNamespace(info=lambda *a: None),
        src=SimpleNamespace(wan=SimpleNamespace(WanT2V=Pipeline)), WAN_CONFIGS={cfg.task: {}},
        t2v_generate=lambda *a, **k: None, budcache_forward=lambda *a, **k: None,
        get_latents=get_latents, calc_mse=lambda a, b: (a-b)**2, tqdm=Progress,
        torch=SimpleNamespace(save=lambda value, path: saved.append(value),
            cuda=SimpleNamespace(empty_cache=lambda: None)))
    names = {'mutate_schedule', 'get_swap_neighbors', 'main'}
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    require({node.name for node in nodes} == names, 'Expected original search functions missing')
    exec(compile(ast.Module(body=nodes, type_ignores=[]), 'pinned_BudCache_CPU_controller', 'exec'), namespace)
    namespace['main']()
    require(len(saved) == len(teacher_calls) == 1, 'Expected one teacher and one in-memory result')
    return dict(fixture_seed=fixture_seed, actual_teacher_standin_calls=len(teacher_calls),
        actual_candidate_standin_calls=len(masks), total_generation_standin_calls=len(masks)+len(teacher_calls),
        unique_candidate_masks=len(set(masks)), duplicate_candidate_calls=len(masks)-len(set(masks)),
        SA_history_rows=sum(row['stage']=='SA' for row in saved[0]['history']),
        HC_history_rows=sum(row['stage']=='HC' for row in saved[0]['history']),
        all_candidate_quotas_and_prefixes_verified=True,
        mask_sequence_sha256=hashlib.sha256(json.dumps(masks).encode()).hexdigest(),
        nominal_saved_speedup=saved[0]['speedup'], nominal_ratio_is_measured_speedup=False,
        CPU_fixture_only=True, actual_model_calls=0, actual_generated_videos=0, CUDA_initialized=False)


def audit(source_root):
    evidence = {}
    for name, expected in FILES.items():
        raw = (source_root/name).read_bytes()
        require(hashlib.sha256(raw).hexdigest() == expected, 'Pinned upstream bytes differ: '+name)
        evidence[name] = dict(sha256=expected, bytes=len(raw),
            url='https://github.com/Westlake-AGI-Lab/BudCache/blob/'+REVISION+'/'+name)
    source = (source_root/'scripts/stage1_search_wan.py').read_text()
    tree = ast.parse(source)
    # The pinned YAML contains only scalar fields, so no YAML loader/import is needed.
    config = {}
    for line in (source_root/'configs/search_wan.yaml').read_text().splitlines():
        if line.strip():
            key, value = line.split(':', 1)
            config[key] = ast.literal_eval(value.strip().replace('true', 'True').replace('false', 'False'))
    accessed = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name) and node.value.id == 'cfg'}
    base = controller_probe(tree, config, 12345)
    multi = controller_probe(tree, dict(config, stage0_multiStart=7), 12345)
    require(base == multi, 'Multistart configuration changed actual controller behavior')
    require(base['total_generation_standin_calls'] == 302 and base['HC_history_rows'] == 5,
        'Original flat-loss complete query denominator differs')
    return dict(status='BUDCACHE_PINNED_SOURCE_AND_SYNTHETIC_CONTROLLER_AUDITED', observed_unix=time.time(),
        upstream_revision=REVISION, paper_url='https://arxiv.org/html/2606.13496v1', evidence=evidence,
        upstream_default_config=config, cfg_fields_read_by_search_script=sorted(accessed),
        stage0_multiStart_read_by_search_script='stage0_multiStart' in accessed,
        controller_probes=[base, dict(multi, changed_config={'stage0_multiStart':7})],
        upstream_candidate_upper_bound=1+config['stage1_sa_iters']+20*config['stage2_hc_iters'],
        upstream_teacher_requests=1, two_FIT_shared_objective_prospective_upper_requests=604,
        two_FIT_count_is_adaptation_planning_not_execution=True,
        source_findings=['Wan search loss receives decoded video returned by t2v_generate',
            'HC samples up to20 neighbors per iteration rather than all legal swaps',
            'Flat-loss HC still consumes all five configured iterations',
            'Python/NumPy search RNG initialization is not tied to cfg.seed in the inspected launcher/search script',
            'Saved speedup is steps divided by selected NFE, not an elapsed-time measurement',
            'No evaluation memoization in inspected search loop; duplicate candidates still call the evaluator'],
        production_Cosmos_adapter_accepted=False, scientific_result=False,
        search_GPU_budget_frozen=False, GPU_dispatch_ready=False,
        new_GPU_submissions=0, new_reserved_GPUh=0, model_weights_loaded=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'Preserve original audit')
    result = audit(args.source_root)
    result['audit_source_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({key:result[key] for key in ('status','upstream_candidate_upper_bound','upstream_teacher_requests','new_GPU_submissions')}))


if __name__ == '__main__':
    main()
