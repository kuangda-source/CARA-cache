#!/usr/bin/env python3
"""Collect the original R2 now under the human's explicit waiting-time override.

Only the two local ETA guards change. Original launch, server sources, whole
scope, CPU proofs, artifact/statistics checks and cost validation stay intact.
"""
import argparse
import ast
import inspect
import json
from pathlib import Path
import sys
import time
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from wcomr import frozen_repair_gpu_r2 as gpu

LAUNCH = ROOT / 'reports/wc_paper_N07_refusal_repair180_R2_GPU_launch_20261017.json'
CPU = ROOT / 'reports/wc_paper_N07_refusal_repair180_actual_production_CPU_R1_independent_acceptance_20261016.json'
HEALTH = ROOT / 'reports/wc_paper_N07_refusal_repair180_R2_midpoint_health_late_20261017.json.gz'
AUTHORITY = ROOT / 'reports/wc_paper_N07_R2_immediate_terminal_direct_human_authority_20261017.json'
QUOTE = 'gpu 生成完了那就直接验收呗'


def authorized(authority, launch, observed):
    if (authority['human_quote'] != QUOTE or authority['scope'] != 'ORIGINAL_R2_READONLY_TERMINAL_COLLECTION_ONLY'
            or authority['launch'] != launch or authority['launch_sha256'] != gpu.sha(LAUNCH)
            or authority['CPU_acceptance_sha256'] != gpu.sha(CPU)
            or authority['GPU_done_health_sha256'] != gpu.sha(HEALTH)
            or authority['new_GPU_submissions'] != 0 or authority['server_or_budget_mutation'] is not False
            or authority['authorized_at_unix'] > observed):
        raise ValueError('Exact new human instruction and unchanged original launch/CPU/health required')
    health = gpu.json_file(HEALTH)
    if (health['technical_classification'] != 'ORIGINAL_GPU_STAGE_FINISHED_CPU_POST_ACTIVE'
            or health['identity_mismatches'] or health['read_errors']
            or health['supervisor']['child_exit_code'] != 0
            or any(health['supervisor'][key] != launch[key]
                   for key in ('source_revision', 'run_id', 'launch_id', 'gpu_uuid', 'config_sha256'))
            or health['technical_progress']['observed_positions'] != 180
            or health['observed_unix'] > authority['authorized_at_unix']):
        raise ValueError('Original successful GPU terminal evidence required before waiting override')
    return True


def replace_exact(source, edits, namespace, name):
    changed = source
    for before, after in edits:
        if changed.count(before) != 1:
            raise ValueError('A local source guard changed: ' + before)
        changed = changed.replace(before, after)
    restored = changed
    for before, after in reversed(edits):
        restored = restored.replace(after, before)
    if restored != source or ast.dump(ast.parse(restored)) != ast.dump(ast.parse(source)):
        raise ValueError('Only the declared local waiting guards may change')
    exec(compile(changed, __file__ + '#' + name, 'exec'), namespace)
    return namespace[name]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--acceptance-output', type=Path, required=True)
    args = parser.parse_args()
    launch = gpu.json_file(LAUNCH)['dispatch']
    gpu.bind_launch(launch, CPU)
    if not AUTHORITY.exists():
        authority = dict(human_quote=QUOTE, authorized_at_unix=time.time(), launch=launch,
            scope='ORIGINAL_R2_READONLY_TERMINAL_COLLECTION_ONLY', launch_sha256=gpu.sha(LAUNCH),
            CPU_acceptance_sha256=gpu.sha(CPU), GPU_done_health_sha256=gpu.sha(HEALTH),
            original_scheduled_ETA_preserved=launch['next_check_not_before_unix'],
            new_GPU_submissions=0, server_or_budget_mutation=False)
        with AUTHORITY.open('x') as handle:
            json.dump(authority, handle, ensure_ascii=False, indent=2)
            handle.write('\n')
    authority = gpu.json_file(AUTHORITY)
    allow = lambda observed: authorized(authority, launch, observed)
    allow(time.time())
    collector = replace_exact(dedent(inspect.getsource(gpu.collect_once)), [
        ("if mode=='terminal' and now<launch['next_check_not_before_unix']:",
         "if mode=='terminal' and now<launch['next_check_not_before_unix'] and not early_authorized(now):")
    ], {**vars(gpu), 'early_authorized': allow}, 'collect_once')
    value, queried = collector(ROOT, launch, 'terminal', CPU, args.output)
    if value.get('status') == 'N07_REPAIR_ORIGINAL_OBSERVATION_UNKNOWN_NO_RESTART':
        result = dict(status=value['status'], scientific_full_scope_accepted=False,
                      original_task_terminal=False, no_GPU_relaunch_authorized=True)
    else:
        accepted, raw = gpu.accepted_CPU(CPU)
        if (value.get('production_CPU_bundle_sha256') != accepted['production_CPU_bundle_sha256']
                or value.get('production_CPU_launch') != raw['launch']):
            raise ValueError('Original independently accepted CPU handle/bundle differs')
        from wcomr.frozen_repair_acceptance_r2 import accept_after_human_wait_override
        result = accept_after_human_wait_override(value, launch, authority)
    result.update(capture_ref=str(args.output), capture_sha256=gpu.sha(args.output),
        launch_ref=str(LAUNCH), launch_sha256=gpu.sha(LAUNCH),
        immediate_collection_authority_ref=str(AUTHORITY), immediate_collection_authority_sha256=gpu.sha(AUTHORITY),
        only_local_ETA_guards_overridden=True, original_180_93frame_source_and_statistics_unchanged=True,
        GPU_submissions=0, SSH_observations=int(queried), ledger_written=False)
    with args.acceptance_output.open('x') as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write('\n')
    print(json.dumps({key: val for key, val in result.items() if key != 'grouped_statistics'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
