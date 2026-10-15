"""Bind selected original benchmark bytes to the shared production requests.

This is a pure input adapter. Selection, actual model CPU validation, whole
card pricing and launch authority remain separate; no inputs are chosen here.
"""
import copy
import hashlib
import json
from pathlib import PurePosixPath

SOURCE_ROOT = 'vendor/WorldCache/Evaluation/PAI-Eval/cosmos_eval_jsons_text_only'
SOURCE_FIELDS = {'inference_type', 'seed', 'guidance', 'num_output_frames', 'resolution',
                 'negative_prompt', 'name', 'prompt'}
CATEGORIES = ('av', 'human', 'misc', 'robot')


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def safe_name(name):
    if (not isinstance(name, str) or not name or name in ('.', '..')
            or '/' in name or '\\' in name or PurePosixPath(name).name != name):
        raise ValueError('Original benchmark basename required')
    return name


def inspect_source(record, raw):
    name = safe_name(record['name'])
    value = json.loads(raw)
    if not isinstance(value, dict) or set(value) != SOURCE_FIELDS:
        raise ValueError('Original text-request schema differs')
    if (value['name'] != name or value['inference_type'] != 'text2world'
            or type(value['seed']) is not int or value['seed'] != 0
            or value['guidance'] != 7 or value['num_output_frames'] != 93
            or value['resolution'] != '432,768'
            or not isinstance(value['prompt'], str) or not value['prompt'].strip()
            or not isinstance(value['negative_prompt'], str)
            or sha_bytes(value['prompt'].encode()) != record['prompt_sha256']):
        raise ValueError('Benchmark identity, original prompt or fixed generation parameters differ')
    proof = dict(name=name, category=record['category'],
        original_relative_ref=SOURCE_ROOT + '/' + name + '.json',
        suggested_stage_ref='inputs/N07/' + name + '.json',
        file_sha256=sha_bytes(raw), prompt_sha256=record['prompt_sha256'],
        negative_prompt_sha256=sha_bytes(value['negative_prompt'].encode()),
        original_fields=sorted(value), fixed_parameters=dict(inference_type='text2world', seed=0,
            guidance=7, num_output_frames=93, resolution='432,768'))
    return value, proof


def bind_selected(selection, input_bytes_by_name):
    """Compile all160 argument variants and180 schedule slots, without running."""
    from .frozen_shared_execution_r1 import matrix, point
    if selection['status'] != 'FINAL_INPUT_SELECTION_KERNEL_RESULT_REQUIRES_PHYSICAL_INPUT_BINDING':
        raise ValueError('Use the original deterministic selection result after accepted development')
    sources, cases, methods = selection['selected_sources'], selection['cases'], selection['method_ids']
    if (len(sources) != 8 or len({r['name'] for r in sources}) != 8
            or set(input_bytes_by_name) != {r['name'] for r in sources}
            or any(sum(s['category'] == category for s in sources) != 2 for category in CATEGORIES)):
        raise ValueError('Bind every selected original source in the whole four-category scope')
    expected_cases = [dict(id=s['name'] + '_PAPER_COMMON_seed' + str(seed),
                           prompt_id=s['name'], seed=seed, category=s['category'])
                      for s in sources for seed in (17, 43)]
    if cases != expected_cases:
        raise ValueError('Final case identity/order or both seeds changed after selection')
    if not {'NATIVE35', 'A_NO_P', 'TABLE_PHASE_H1', 'FRONT_DENSE_C', 'FRONT_DENSE_A'}.issubset(methods):
        raise ValueError('Retain frozen candidates and both strong simple comparators')
    if not any(m.startswith('WC_') for m in methods) or not any(m.startswith('RA_') for m in methods):
        raise ValueError('Retain the selected WorldCache and RA workpoints')
    plan = matrix(cases, methods)
    parsed, bindings = {}, []
    for source in sources:
        value, proof = inspect_source(source, input_bytes_by_name[source['name']])
        parsed[source['name']] = value
        bindings.append(proof)
    bound_cases, requests = [], []
    for case in cases:
        source = parsed[case['prompt_id']]
        bound_cases.append(dict(case, prompt=source['prompt'],
                               prompt_sha256=sha_bytes(source['prompt'].encode())))
        for method in methods:
            original = copy.deepcopy(source)
            request = {**original, 'name': case['id'], 'seed': case['seed'],
                       'num_steps': point(method)['requested_steps']}
            changes = {k for k in set(original) | set(request) if original.get(k) != request.get(k)}
            if changes != {'name', 'seed', 'num_steps'}:
                raise ValueError('An original conditioning/guidance/geometry field changed')
            requests.append(dict(case_id=case['id'], method=method, arguments=request,
                                 changed_original_fields=sorted(changes)))
    counts = dict(prompt_groups=8, requests=16, methods=10, scientific_paths=160,
        full_warmup_paths=20, total_paths=180,
        ordinary_pairs=sum(point(row['method'])['actual_updates'] for row in plan),
        loads=1, teacher_pairs=0, score_videos=160)
    counts['ordinary_CFG_calls'] = 2 * counts['ordinary_pairs']
    return dict(status='N07_SELECTED_INPUT_BYTES_AND_FULL_ARGUMENT_MATRIX_BOUND_NOT_PRODUCTION',
        source_bindings=bindings, cases=bound_cases, method_ids=list(methods),
        argument_variants=requests, execution_plan=plan, planned_scope_counts=counts,
        changes_limited_to=['name', 'seed', 'num_steps'],
        selection_or_workpoint_decisions_made_by_adapter=False,
        original_development_selection_receipts_still_require_file_identity_verification=True,
        actual_InferenceArguments_CPU_accepted=False, actual_model_or_sampler_run=False,
        physical_input_manifest_written=False, whole_GPU_card_selected=False,
        GPU_submissions=0, SSH_queries=0, ledger_written=False)
