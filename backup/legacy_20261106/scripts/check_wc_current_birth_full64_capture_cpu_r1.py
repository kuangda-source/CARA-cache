#!/usr/bin/env python3
"""Preregistered complete-denominator tests for the independent64 reconstructor.

Synthetic values only. No Torch, model, metric execution, server, or real run
authorization. Existing source remains frozen; failed checks preserve evidence.
"""
import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import subprocess
import sys
import time


def main():
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / 'src'))
    from wcomr import current_birth_full64_scores_r1 as production
    import wc_current_birth_full64_independent_r1 as independent
    registry = root / 'manifests/wc_current_birth_full64_capture_source_r1_preregistration_20261010.json'
    reg = json.loads(registry.read_text())
    require = independent.require
    require({n: hashlib.sha256((root/n).read_bytes()).hexdigest() for n in reg['source_sha256']}
            == reg['source_sha256'], 'Preregistered source bytes differ')
    target = root / 'reports/wc_current_birth_full64_capture_cpu_r1_results_20261010.json'
    require(not target.exists(), 'Do not overwrite original CPU result')
    require(independent.COUNTS == production.COUNTS and independent.STRATEGIES == production.STRATEGIES
            and independent.METHODS == production.METHODS and list(independent.NAMES) == production.NAMES,
            'Independent original scope constants differ')
    started = time.perf_counter(); rng = random.Random(20261010)
    def artifact(label):
        return {'path': '/synthetic-independent64/' + label + '.mp4', 'bytes': 32,
                'sha256': hashlib.sha256(label.encode()).hexdigest()}
    def score(reference, candidate, values):
        return {'frames': 93, 'pts': [[i, '1/16'] for i in range(93)],
                'frame_distances': values, 'mean_LPIPS': sum(values)/93,
                'reference_sha256': reference['sha256'], 'candidate_sha256': candidate['sha256']}
    runner = {'planned_scope': production.COUNTS, 'completed_strategies': list(production.STRATEGIES), 'batches': {}}
    pairing = {}; pairs = []; legacy = {'pairs': []}
    for si, strategy in enumerate(production.STRATEGIES):
        requests = []; slots = []
        for ni, name in enumerate(production.NAMES):
            reference = artifact('Native-' + name); paths = []
            for mi, method in enumerate(production.METHODS):
                candidate = artifact(strategy + '-' + name + '-' + method)
                actions = ['DD'] * 7 + ['CC'] * 28 + ['DD']
                if method not in ('SOURCE_RA', 'DYNAMIC_NO_P', 'DENSE_CONTROL'):
                    actions[10:12] = ['PP', 'PP']
                if method == 'DENSE_CONTROL': actions = ['DD'] * 36
                extra = 9 if method in ('A_CPD_W1_ONE_PHASE', 'A_CPD_BETA1_ONE_PHASE') else 0
                paths.append({'collect': method, 'status': 'COMPLETE_PARENT_PATH', 'actions': actions,
                    'instrumented_parent_pipeline_wall_seconds': 200 + rng.random() * 5 + 3*mi + si,
                    'collection_complete': {'complete_pairs': 36, 'actual_original_plus_candidate_heads': [None]*(72+extra),
                        'deployment': {'A_readout': {'extra_candidate_heads': extra, 'teacher_calls': 0,
                            'extra_candidate_deep_blocks': 0}} if method != 'SOURCE_RA' else None}})
                checks = {'prepared': True, 'solver': True, 'protected_prefix': True}
                slots.append({'sample_name': name, 'method': method, 'compatible': True, 'checks': checks,
                    'incompatible_fields': [], 'no_replacement_or_other_seed': True,
                    'Native_artifact': reference, 'video_artifact': candidate})
                values = [.45 + .015*ni - .002*mi + .007*si + rng.random()*.004 for _ in range(93)]
                # Retain both isolated harmful frames and an entirely harmful scene.
                if method == 'A_CPD_W1_ONE_PHASE':
                    values[17] += .15
                    if ni == 2: values = [v + .04 for v in values]
                pairs.append({'strategy': strategy, 'sample_name': name, 'method': method,
                    'reference': reference, 'candidate': candidate, 'score': score(reference, candidate, values)})
            requests.append({'sample_name': name, 'paths': paths})
        runner['batches'][strategy] = {'requests': requests}
        pairing[strategy] = {'complete_pairing_slots': 32, 'compatible_pairs': 32, 'incompatible_pairs': 0, 'pairs': slots}
    for ni, name in enumerate(production.NAMES):
        reference = artifact('Native-' + name)
        for mi, method in enumerate(production.LEGACY_METHODS):
            candidate = artifact('Legacy-' + name + '-' + method)
            legacy['pairs'].append({'sample_name': name, 'method': method, 'reference': reference,
                'candidate': candidate, 'score': score(reference, candidate,
                    [.46 + .013*ni - .003*mi + rng.random()*.005 for _ in range(93)])})
    costs = independent.costs_from_runner(runner)
    independent.same(costs, production.actual_costs(runner))
    reference = production.summarize(pairs, pairing, costs, legacy)
    reconstructed = independent.reconstruct_summary(pairs, pairing, costs, legacy)
    independent.same(reference, reconstructed)
    require((len(reconstructed['per_slot']), reconstructed['scored_pairs'], reconstructed['actual_frame_distances'])
            == (64, 64, 5952), 'Complete64/93 fixture differs')
    c = next(c for c in reconstructed['registered_same_card_contrasts']
             if c['candidate'] == [production.STRATEGIES[0], 'A_CPD_W1_ONE_PHASE'] and c['baseline'][1] == 'CPD')
    require(c['degraded_scenes'] >= 1 and all(r['degraded_frames'] >= 1 for r in c['per_scene']), 'Harmful observations dropped')
    require(len(reconstructed['registered_same_card_contrasts']) == 24 and len(reconstructed['legacy_quality_only_contrasts']) == 48,
            'Registered contrast denominator differs')
    cases = []
    for label, removed in [('one_incompatible', {13}), ('all_incompatible', set(range(64)))]:
        pp = copy.deepcopy(pairing); actual = []
        for i, (strategy, name, method) in enumerate(independent.keys()):
            if i not in removed: actual.append(pairs[i]); continue
            slot = pp[strategy]['pairs'][i % 32]; slot['checks']['prepared'] = False
            slot['compatible'] = False; slot['incompatible_fields'] = ['prepared']
        for strategy in production.STRATEGIES:
            g = pp[strategy]; g['compatible_pairs'] = sum(s['compatible'] for s in g['pairs'])
            g['incompatible_pairs'] = 32 - g['compatible_pairs']
        a = independent.reconstruct_summary(actual, pp, costs, legacy)
        independent.same(production.summarize(actual, pp, costs, legacy), a)
        require(len(a['per_slot']) == 64 and sum(r['mean_LPIPS'] is None for r in a['per_slot']) == len(removed), 'Missing slot fabricated')
        cases.append({'case': label, 'kept_slots': 64, 'scores': len(actual), 'all93_values': 93*len(actual)})
    refused = []
    def rejects(label, function):
        try: function()
        except (ValueError, KeyError, TypeError, ZeroDivisionError): refused.append(label)
        else: raise AssertionError('Invalid independent fixture accepted: ' + label)
    rejects('drop_score', lambda: independent.reconstruct_summary(pairs[:-1], pairing, costs, legacy))
    rejects('duplicate_score', lambda: independent.reconstruct_summary(pairs[:-1]+[pairs[0]], pairing, costs, legacy))
    rejects('reorder_score', lambda: independent.reconstruct_summary(pairs[1:]+pairs[:1], pairing, costs, legacy))
    rejects('drop_strategy', lambda: independent.reconstruct_summary(pairs, {production.STRATEGIES[0]: pairing[production.STRATEGIES[0]]}, costs, legacy))
    rejects('drop_cost', lambda: independent.reconstruct_summary(pairs, pairing, costs[:-1], legacy))
    rejects('drop_legacy_score', lambda: independent.reconstruct_summary(pairs, pairing, costs, {'pairs': legacy['pairs'][:-1]}))
    for label, mutate in [('frame92', lambda x: x['score']['frame_distances'].pop()),
        ('nonfinite_frame', lambda x: x['score']['frame_distances'].__setitem__(0, float('nan'))),
        ('wrong_mean', lambda x: x['score'].__setitem__('mean_LPIPS', 1.)),
        ('duplicate_PTS', lambda x: x['score']['pts'].__setitem__(1, x['score']['pts'][0])),
        ('reversed_PTS', lambda x: x['score']['pts'].reverse()),
        ('candidate_SHA', lambda x: x['candidate'].__setitem__('sha256', '0'*64)),
        ('reference_SHA', lambda x: x['reference'].__setitem__('sha256', '1'*64))]:
        wrong = copy.deepcopy(pairs); mutate(wrong[0])
        rejects(label, lambda: independent.reconstruct_summary(wrong, pairing, costs, legacy))
    for label, key, value in [('negative_cost', 'instrumented_pipeline_wall_seconds', -1.),
        ('nonfinite_cost', 'instrumented_pipeline_wall_seconds', float('nan')),
        ('wrong_dense_count', 'complete_branch_calls', 72), ('teacher_work', 'teacher_calls', 1),
        ('extra_deep_work', 'extra_candidate_deep_blocks', 1)]:
        wrong = copy.deepcopy(costs); wrong[0][key] = value
        rejects(label, lambda: independent.reconstruct_summary(pairs, pairing, wrong, legacy))
    for label, mutate in [('missing_method', lambda x: x['paths'].pop()),
        ('wrong_head_count', lambda x: x['paths'][0]['collection_complete']['actual_original_plus_candidate_heads'].pop()),
        ('fake_dense', lambda x: x['paths'][7]['actions'].__setitem__(10, 'CC')),
        ('nonfinite_parent_cost', lambda x: x['paths'][0].__setitem__('instrumented_parent_pipeline_wall_seconds', float('nan'))),
        ('actual_A_teacher', lambda x: x['paths'][5]['collection_complete']['deployment']['A_readout'].__setitem__('teacher_calls', 1)),
        ('actual_A_deep', lambda x: x['paths'][5]['collection_complete']['deployment']['A_readout'].__setitem__('extra_candidate_deep_blocks', 1))]:
        wrong = copy.deepcopy(runner); mutate(wrong['batches'][production.STRATEGIES[0]]['requests'][0])
        rejects(label, lambda: independent.costs_from_runner(wrong))
    wrong = copy.deepcopy(reference); wrong['registered_same_card_contrasts'][0]['matched_scenes'] = 1
    rejects('changed_summary_denominator', lambda: independent.same(wrong, reconstructed))
    wrong = copy.deepcopy(reference); wrong['legacy_quality_only_contrasts'][0]['clean_speed_claim'] = True
    rejects('legacy_speed_fabrication', lambda: independent.same(wrong, reconstructed))
    require('torch' not in sys.modules, 'Independent fixture unexpectedly imported Torch')
    # Compile the actual embedded remote programs without executing or importing them remotely.
    compiled_remote = []
    for file in ['scripts/capture_wc_current_birth_full64_terminal_r1.py', 'scripts/capture_wc_current_birth_full64_score_cpu_r1.py']:
        source = (root/file).read_text(); tree = ast.parse(source); compile(source, file, 'exec')
        remote = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)
                  and 'import base64' in n.value and 'print(json.dumps' in n.value]
        require(len(remote) == 1, 'Exactly one remote capture body required')
        compile('L={}\n'+remote[0], file+'#read-only-remote', 'exec'); compiled_remote.append(file)
    # Missing launch guards must exit before SSH and write no report or selection.
    waiting = []
    watched = ['reports/wc_current_birth_full64_r1_GPU_launch_20261010.json',
               'reports/wc_current_birth_full64_score_cpu_r1_launch_20261010.json',
               'reports/wc_current_birth_full64_r1_terminal_20261010_capture_and_independent_audit.json',
               'reports/wc_current_birth_full64_score_cpu_r1_terminal_20261010_capture_and_independent_audit.json']
    require(not any((root/n).exists() for n in watched), 'Missing-launch fixture requires actual missing original handles')
    for file in compiled_remote:
        call = subprocess.run([sys.executable, str(root/file)], cwd=root, text=True, capture_output=True)
        require(call.returncode == 2 and json.loads(call.stdout)['GPU_submissions'] == 0, 'Missing original launch did not wait')
        waiting.append({'entry': file, 'exit_code': call.returncode, 'status': json.loads(call.stdout)['status']})
    require(not any((root/n).exists() for n in watched), 'Missing launch guard wrote artifacts')
    result = {'status': 'COMPLETE64_INDEPENDENT_CAPTURE_STATISTICS_CPU_PASS_NOT_GPU_OR_METRIC_RESULTS',
        'CPU_wall_seconds': time.perf_counter()-started, 'synthetic_slots': 64, 'synthetic_all93_values': 5952,
        'all64_actual_cost_shape_reconstruction_matches_frozen_production': True,
        'independent24_same_card_and48_legacy_contrasts_match_frozen_summary': True,
        'incompatible_denominator_cases': cases, 'mutation_refusals': refused,
        'harmful_scenes_and_frames_retained': True, 'compiled_remote_entrypoints': compiled_remote,
        'missing_actual_launch_guard_results': waiting, 'actual_CPU_or_GPU_terminal_capture': False,
        'actual_new64_video_or_metric_execution': False, 'direct_user_authorization_created': False,
        'torch_imported': False, 'GPU_submissions': 0, 'budget_written': False,
        'source_sha256': reg['source_sha256']}
    target.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'}))


if __name__ == '__main__': main()
