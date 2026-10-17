#!/usr/bin/env python3
"""Export separate observed N08 intervals; never manufacture an end-to-end sum."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    'raw': 'reports/wc_paper_N08_balanced_full40_terminal_collection_user_status_20261017.json.gz',
    'accepted': 'reports/wc_paper_N08_balanced_full40_terminal_independent_acceptance_roundoff_r1_20261017.json',
    'capture_binding': 'reports/wc_paper_N08_independent_statistics_difference_diagnosis_20261017.json',
    'previous_cost_inventory': 'reports/wc_deployment_cost_source_inventory_r1_20261016.json',
}
CODE = ('balanced_repeat_execution_r1', 'frozen_shared_execution_r1',
        'clean_speed20_r1', 'paper_baseline_grid_r1', 'simple26d_memory_r2')
SLOTS = {'FULL_NATIVE': 'NATIVE35', 'WORLD_CACHE': 'WC_HALF', 'RA_CFG_CACHE': 'RA_DEFAULT',
         'GCR_EFFICIENT': 'A_NO_P', 'CPA_HIGH_FIDELITY': 'TABLE_PHASE_H1'}
LABELS = {'NATIVE35': 'Full inference', 'WC_HALF': 'WorldCache', 'RA_DEFAULT': 'RA-CFGCache',
          'A_NO_P': 'Efficient', 'TABLE_PHASE_H1': 'High fidelity'}
FIELDS = ('core_seconds', 'guarded_pipeline_without_write_seconds', 'method_install_seconds',
          'method_cleanup_seconds', 'video_write_seconds', 'GC_before_seconds',
          'GC_after_seconds', 'frozen_cleanup_GC_seconds')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def close(x, y):
    assert math.isclose(x, y, rel_tol=1e-12, abs_tol=1e-12), (x, y)


def stats(values):
    assert len(values) == 3
    return dict(observations=3, mean=statistics.mean(values), sample_std=statistics.stdev(values),
                minimum=min(values), maximum=max(values))


def derive(project):
    project = Path(project)
    source = {k: read(project / ref) for k, ref in SOURCES.items()}
    raw, accepted, binding = (source[k] for k in ('raw', 'accepted', 'capture_binding'))
    assert digest(project / SOURCES['raw']) == binding['capture_sha256']
    assert accepted['capture_ref'] == SOURCES['raw']
    assert all(accepted[k] is True for k in ('scientific_full_scope_accepted',
        'full_raw_and_fidelity_scope_accepted', 'stable_repeated_clean_speed_claim',
        'terminal_receipt_audit_accepted', 'own_GPU_and_finance_released'))
    assert len(raw['runner']['runs']) == 40 and accepted['original_runner_paths'] == 40
    code_bindings = {}
    for name in CODE:
        ref = 'src/wcomr/' + name + '.py'
        sha = digest(project / ref)
        assert raw['registration']['payload_sha256'][ref] == sha
        code_bindings[ref] = sha
    rows = [r for r in raw['final']['rows'] if r['section'] == 'TIMED']
    assert len(rows) == 30 and all(r['status'] == 'COMPLETE' for r in rows)
    runner = {r['id']: r for r in raw['runner']['runs']}
    records = []
    for r in rows:
        assert SLOTS[r['slot']] == r['method'] and r['round'] in (1, 2, 3)
        assert r['raw_model_audit'] == r['endpoint_audit'] == 'PASS'
        assert r['in_timing_guided_copies'] == r['in_timing_hashes'] == 0
        assert r['guided_pairs'] == r['solver_steps'] == 36
        assert r['frozen_request_cleanup']['components_alive_after'] == 0
        gc = [r['request_memory_lifecycle'][key]['seconds'] for key in ('before', 'after')]
        gc.append(r['frozen_request_cleanup']['collection']['seconds'])
        t = r['timing_intervals']
        assert t['request_boundary_GC_intervals_seconds'] == gc
        assert t['overlapping_or_nested_intervals_not_a_new_end_to_end_sum'] is True
        values = {k: r[k] for k in FIELDS[:5]}
        values.update(zip(FIELDS[5:], gc))
        assert all(type(v) in (int, float) and math.isfinite(v) and v >= 0 for v in values.values())
        assert values['guarded_pipeline_without_write_seconds'] >= values['core_seconds'] > 0
        for k in FIELDS[:5]:
            assert r[k] == runner[r['id']][k]
            interval_key = 'core_text_denoise_VAE_seconds' if k == 'core_seconds' else k
            assert t[interval_key] == r[k]
        q = r['LPIPS']
        assert q['frames'] == len(q['frame_distances']) == 93
        quality = statistics.mean(q['frame_distances'])
        close(quality, q['mean_LPIPS'])
        records.append(dict(id=r['id'], scene=r['scene'], method=r['method'], slot=r['slot'],
            round=r['round'], balanced_position=r['position'], **values,
            LPIPS=quality, all93_frames_accepted=True))
    scenes = sorted({r['scene'] for r in records})
    assert len(scenes) == 2
    groups = []
    for scene in scenes:
        for slot, method in SLOTS.items():
            rr = sorted((r for r in records if r['scene'] == scene and r['method'] == method),
                        key=lambda r: r['round'])
            assert [r['round'] for r in rr] == [1, 2, 3]
            assert all(r['LPIPS'] == rr[0]['LPIPS'] for r in rr)
            measured = {k: stats([r[k] for r in rr]) for k in FIELDS}
            primary = next(p for p in accepted['timing_statistics']['scene_methods']
                           if p['scene'] == scene and p['slot'] == slot)
            close(measured['core_seconds']['mean'], primary['complete_repeat_mean_seconds'])
            close(measured['core_seconds']['sample_std'], primary['complete_repeat_sample_std_seconds'])
            groups.append(dict(scene=scene, method=method, slot=slot, repeats=3,
                intervals=measured, rounds=rr, LPIPS=rr[0]['LPIPS']))
    for g in groups:
        g['matched_speedups'] = {}
        for interval in ('core_seconds', 'guarded_pipeline_without_write_seconds'):
            g['matched_speedups'][interval] = {
                base: next(x['intervals'][interval]['mean'] for x in groups
                           if x['scene'] == g['scene'] and x['method'] == base)
                      / g['intervals'][interval]['mean']
                for base in ('NATIVE35', 'WC_HALF', 'RA_DEFAULT')}
    aggregate = []
    for method in SLOTS.values():
        gg = [g for g in groups if g['method'] == method]
        aggregate.append(dict(method=method, scenes=2, same_seed_repeat_count_per_scene=3,
            mean_intervals_seconds={k: statistics.mean(g['intervals'][k]['mean'] for g in gg) for k in FIELDS},
            mean_LPIPS=statistics.mean(g['LPIPS'] for g in gg)))
    for g in aggregate:
        g['matched_speedups'] = {interval: {
            base: next(x['mean_intervals_seconds'][interval] for x in aggregate if x['method'] == base)
                  / g['mean_intervals_seconds'][interval]
            for base in ('NATIVE35', 'WC_HALF', 'RA_DEFAULT')}
            for interval in ('core_seconds', 'guarded_pipeline_without_write_seconds')}
    inventory = source['previous_cost_inventory']
    assert inventory['historical_total_is_minimum_deployment_cost'] is False
    assert inventory['final_minimum_calibration_GPUh'] is None
    return dict(status='ACCEPTED_N08_SEPARATE_INTERVALS_POSTHOC_EXPORT_NOT_NEW_EXPERIMENT',
        source_bindings={k: dict(path=ref, sha256=digest(project / ref)) for k, ref in SOURCES.items()},
        deployed_timer_source_sha256=code_bindings, source_revision=raw['launch']['source_revision'],
        original_paths=40, formal_paths=30, scenes=scenes, scene_method_groups=groups,
        equal_scene_aggregate=aggregate, labels=LABELS,
        interval_semantics=dict(core='Synchronized text encoding, denoising and VAE; online algorithm work retained',
            guarded='Measured inference.generate request including the core and safety path; deferred writing excluded',
            install_cleanup_write='Distinct recorded wall intervals, not a new summed end-to-end timer',
            GC='Three calls reported separately: lifecycle before, lifecycle after, outer frozen cleanup',
            guarded_minus_core_is_pure_guardrail_cost=False, component_intervals_are_additive=False,
            synthesized_complete_request_latency=None, new_kernel_profile_or_independent_peak_memory=None),
        existing_calibration_evidence=dict(inventory_ref=SOURCES['previous_cost_inventory'],
            CPU_statistical_table_fit=inventory['CPU_statistical_table_fit'],
            related_historical_collection_jobs=inventory['historical_related_collection_jobs'],
            related_historical_collection_total_GPUh=inventory['historical_related_jobs_total_GPUh'],
            minimum_necessary_calibration_GPUh=None, break_even_request_count=None),
        original_N08_primary_clock_or_statistics_changed=False, independent_new_input_generalization=False,
        actual_N09_component_profile_complete=False, GPU_submissions=0, SSH_queries=0,
        model_weights_loaded=0, ledger_written=False)


def markdown(value):
    lines = ['# N08 已验收的独立计时间隔', '',
        '复用原完整40路径中的30正式记录；两旧CAL、seed0，每配置三轮。核心生成和含安全管线的调用分别统计。',
        '安装、清理、写盘及三个GC调用单列；不把嵌套区间相加成新的端到端时间，也不把两计时之差命名为纯guardrail开销。', '']
    for scene in value['scenes']:
        lines += ['## ' + scene, '', '| 配置 | 核心3轮秒数 | 核心均值±std | guarded 3轮秒数 | guarded均值±std | LPIPS |',
                  '|---|---|---:|---|---:|---:|']
        for g in value['scene_method_groups']:
            if g['scene'] != scene:
                continue
            c = g['intervals']['core_seconds']; w = g['intervals']['guarded_pipeline_without_write_seconds']
            cv = ' / '.join(f"{r['core_seconds']:.3f}" for r in g['rounds'])
            wv = ' / '.join(f"{r['guarded_pipeline_without_write_seconds']:.3f}" for r in g['rounds'])
            lines.append(f"| {value['labels'][g['method']]} | {cv} | {c['mean']:.3f}±{c['sample_std']:.3f} | {wv} | {w['mean']:.3f}±{w['sample_std']:.3f} | {g['LPIPS']:.6f} |")
        lines += ['', '| 配置 | 安装ms | 清理ms | 写盘s | 前GC s | 后GC s | frozen清理GC s | guarded倍数 Native/WC/RA |',
                  '|---|---:|---:|---:|---:|---:|---:|---|']
        for g in value['scene_method_groups']:
            if g['scene'] != scene:
                continue
            t = g['intervals']; f = lambda k: t[k]['mean']
            speed = ' / '.join(f'{v:.4f}×' for v in g['matched_speedups']['guarded_pipeline_without_write_seconds'].values())
            lines.append(f"| {value['labels'][g['method']]} | {1000*f('method_install_seconds'):.3f} | {1000*f('method_cleanup_seconds'):.3f} | {f('video_write_seconds'):.3f} | {f('GC_before_seconds'):.3f} | {f('GC_after_seconds'):.3f} | {f('frozen_cleanup_GC_seconds'):.3f} | {speed} |")
        lines.append('')
    lines += ['## 两场景等权汇总', '', '| 配置 | 核心s | guarded s | LPIPS | 核心倍数 Native/WC/RA | guarded倍数 Native/WC/RA |',
              '|---|---:|---:|---:|---|---|']
    for g in value['equal_scene_aggregate']:
        def speeds(interval):
            return ' / '.join(f'{v:.4f}×' for v in g['matched_speedups'][interval].values())
        t = g['mean_intervals_seconds']
        lines.append(f"| {value['labels'][g['method']]} | {t['core_seconds']:.3f} | {t['guarded_pipeline_without_write_seconds']:.3f} | {g['mean_LPIPS']:.6f} | {speeds('core_seconds')} | {speeds('guarded_pipeline_without_write_seconds')} |")
    lines += ['', '原N08主结果、方法、输入及控制不改。guarded为已记录的另一计时边界，不含模型加载、全部维护和写盘。',
        '四项历史相关采集合计4.383638799 GPUh是研究账，不是最低必要标定成本；原五次CPU标量拟合证据沿用，未重复测量。',
        'N09组件价格、逐请求独立显存和最低必要采集费用仍待实际生产测量；N12结果不在本包内。', '']
    return '\n'.join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        raise FileExistsError('Preserve the original interval export')
    value = derive(ROOT)
    args.output.mkdir(parents=True)
    (args.output / 'data.json').write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    (args.output / 'README.md').write_text(markdown(value))
    proof = dict(status='N08_SEPARATE_INTERVAL_EXPORT_BOUND_TO_ACCEPTED_RAW',
        original_formal_paths=30, scene_method_groups=10, original_complete_scope=40,
        exporter_sha256=digest(Path(__file__)), source_bindings=value['source_bindings'],
        output_sha256={name: digest(args.output / name) for name in ('data.json', 'README.md')},
        synthesized_complete_request_latency=False, primary_clock_or_results_changed=False,
        GPU_submissions=0, SSH_queries=0, model_weights_loaded=0, ledger_written=False)
    (args.output / 'provenance.json').write_text(json.dumps(proof, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(output=str(args.output), formal_paths=30, groups=10,
        aggregate=value['equal_scene_aggregate'], new_GPU=0), ensure_ascii=False))


if __name__ == '__main__':
    main()
