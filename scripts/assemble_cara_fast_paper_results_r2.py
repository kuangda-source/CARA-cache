"""Bind accepted B36 evidence and existing exports into the current paper index."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from wcomr.cara_fast_b36_figures_r1 import verify_analysis, label

PANELS = ('T_DD_speed_fidelity', 'T_request_speed_fidelity', 'Alex_frame_curves', 'temporal_detail')
CSV_ROWS = dict(per_member=32, frame_curves=2976, prompt_equal=24, FIT_A_only=6)


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bound_json(root, descriptor):
    relative = Path(descriptor['path'])
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Paper evidence must use repository-relative paths')
    path = root/relative
    if file_sha(path) != descriptor['sha256']:
        raise ValueError('Changed paper evidence: '+str(relative))
    return json.loads(path.read_bytes())


def accepted_results(manifest_path, root=ROOT):
    """The complete reader owns science acceptance; this boundary owns export links."""
    root = Path(root)
    manifest = json.loads(Path(manifest_path).read_bytes())
    if (manifest['schema'] != 'CARA_FAST_PAPER_RESULTS_R2'
            or manifest['state'] != 'COMPLETE_ACCEPTED_B36_REGISTERED'
            or len(manifest['accepted_batches']) != 1):
        raise ValueError('One complete registered B36 batch required')
    parent = bound_json(root, manifest['parent_manifest'])
    batch = manifest['accepted_batches'][0]
    analysis = bound_json(root, batch['analysis'])
    rebuilt, analysis_sha = verify_analysis(root/batch['analysis']['path'], receipt_root=root)
    if analysis != rebuilt or analysis['run_id'] != batch['id']:
        raise ValueError('Original accepted B36 identity differs')
    figures = bound_json(root, batch['figures'])
    visual = bound_json(root, batch['visual_acceptance'])
    cpu = bound_json(root, batch['figure_CPU_acceptance'])
    production = bound_json(root, batch['figure_production_acceptance'])['accepted']
    if (not cpu['passed'] or any(file_sha(root/name) != sha
            for name, sha in cpu['critical_source_sha256'].items())):
        raise ValueError('Original accepted figure sources changed')
    if (figures['status'] != 'COMPLETE_ACCEPTED_B36_FIGURES' or figures['CPU_fixture_only']
            or figures['analysis_sha256'] != analysis_sha or figures['CSV_rows'] != CSV_ROWS
            or figures['figure_panels'] != 4 or figures['formats'] != ['png', 'pdf']
            or figures['metric_networks_executed'] or figures['GPU_submissions'] != 0
            or not figures['no_new_selection'] or figures['bootstrap'] != parent['statistics']):
        raise ValueError('Complete original tables, panels and statistics required')
    if (visual['status'] != 'B36_REAL_FIGURES_VISUALLY_AND_STRUCTURALLY_ACCEPTED'
            or visual['CPU_fixture_only'] or not visual['all_four_panels_inspected']
            or visual['report_sha256'] != batch['figures']['sha256']):
        raise ValueError('Original production figure visual acceptance required')
    state = production['container_state']
    if (production['status'] != 'B36_COMPLETE_FIGURES_REAL_CPU_ACCEPTED'
            or production['report_sha256'] != batch['figures']['sha256']
            or production['analysis_sha256'] != analysis_sha
            or state['Status'] != 'exited' or state['Running'] or state['Pid'] != 0
            or state['ExitCode'] != 0 or state['OOMKilled']
            or production['host_config']['DeviceRequests'] is not None
            or production['original_execution_stage_changed']
            or production['metric_networks_executed'] or production['GPU_submissions'] != 0):
        raise ValueError('Original figure CPU must have exited and been accepted')
    expected = {name+'.'+fmt for name in PANELS for fmt in ('png', 'pdf')}
    expected.update(name+'.csv' for name in CSV_ROWS)
    if set(figures['files']) != expected:
        raise ValueError('All eight figure files and four CSV files required')
    folder = Path(batch['figures']['path']).parent
    exports = {str(folder/name): sha for name, sha in figures['files'].items()}
    if any(file_sha(root/name) != sha for name, sha in exports.items()):
        raise ValueError('Changed accepted figure or CSV export')
    if any(file_sha(root/name) != sha for name, sha in figures['source_sha256'].items()):
        raise ValueError('Original production export source changed')
    with (root/folder/'prompt_equal.csv').open(newline='') as handle:
        rows = list(csv.DictReader(handle))
    expected_rows = {(partition, row['role']) for partition, group
                     in analysis['prompt_equal_summaries'].items() for row in group}
    if len(rows) != 24 or {(row['partition'], row['role']) for row in rows} != expected_rows:
        raise ValueError('Complete original prompt-equal CSV required')
    intervals = {partition: {row['role']: [float(row['speedup_DD_CI95_low']),
        float(row['speedup_DD_CI95_high'])] for row in rows if row['partition'] == partition}
        for partition in analysis['prompt_equal_summaries']}
    settlement = bound_json(root, analysis['input_file_sha256']['settlement'])
    jobs = [job for job in settlement['central_after']['jobs'].values()
            if job.get('launch_id') in (analysis['A_launch_id'], analysis['launch_id'])]
    if len(jobs) != 2 or any(job['status'] != 'SETTLED' for job in jobs):
        raise ValueError('Original A32 and B36 once-only settlements required')
    costs = [dict(run_id=job['run_id'], launch_id=job['launch_id'], actual_GPUh=job['actual_GPUh'])
             for job in jobs]
    return dict(schema='CARA_FAST_ACCEPTED_PAPER_INDEX_R2',
        status='ACCEPTED_B36_PAPER_INDEX', manifest_sha256=file_sha(manifest_path),
        run_id=analysis['run_id'], launch_id=analysis['launch_id'],
        source_revision=analysis['source_revision'], host=analysis['host'], gpu_uuid=analysis['gpu_uuid'],
        scope_sha256=analysis['scope_sha256'], analysis_sha256=analysis_sha,
        original_analysis=batch['analysis'], original_figures=batch['figures'], exports=exports,
        independent_input_clusters=4, input_scope='FOUR_OLD_CAL_WITH_INTERNAL_FIT_CHECK',
        timing_rule=analysis['timing_rule'], PSNR_rule=analysis['PSNR_rule'],
        gradient_ratio_rule=analysis['gradient_ratio_rule'], frozen_baselines=analysis['frozen_baselines'],
        prompt_equal_summaries=analysis['prompt_equal_summaries'],
        statistics=figures['bootstrap'], original_T_DD_speedup_CI95=intervals,
        FIT_phase_A_only_sensitivity=analysis['FIT_phase_A_only_sensitivity'],
        original_once_only_costs=costs, original_A32_plus_B36_GPUh=sum(j['actual_GPUh'] for j in costs),
        human_reviews_included=0, independent_new_inputs=False, new_method_claim_accepted=False,
        metrics_computed=False, GPU_submissions=0, ledger_written=False, authorizes_replay=False)


def write_index(result, output, root=ROOT):
    """Present the original prompt-equal rows without fitting or recomputing them."""
    root, output = Path(root), Path(output)
    if output.exists():
        raise ValueError('Fresh paper index directory required')
    relative = lambda path: Path(os.path.relpath(root/path, output)).as_posix()
    lines = ['# Fast19 已接受结果索引', '',
        '本页使用完整 B36 原回执与已接受图表。四个旧 CAL 输入等权；CHECK 是旧 CAL 内部留出。'
        '时间重复先在输入内平均，视频帧不增加独立输入数。', '',
        'T_DD 从去噪循环前同步计至解码后同步，T_request 为驻留模型的完整请求。'
        '表内区间原样引用原 CSV 的 20,000 次输入簇 bootstrap，属于双侧 95% 探索性区间；未重新抽样。', '',
        '| 原角色 / FIT 匹配标签 | T_DD (s) | T_request (s) | T_DD 加速比 [95%区间] | 完整请求加速比 | Alex | SSIM |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for row in result['prompt_equal_summaries']['ALL']:
        low, high = result['original_T_DD_speedup_CI95']['ALL'][row['role']]
        values = [label(result, row['role']), f"{row['time_mean']['T_DD']:.6f}",
            f"{row['time_mean']['T_request']:.6f}", f"{row['speedup']['T_DD']:.6f} [{low:.6f}, {high:.6f}]",
            f"{row['speedup']['T_request']:.6f}", f"{row['metrics']['Alex']:.6f}", f"{row['metrics']['SSIM']:.6f}"]
        lines.append('| '+' | '.join(values)+' |')
    lines += ['', 'WC/RA 保留原 FIT UNMATCHED；Native-k 的 MATCHED 仅指原 FIT 时间选择。'
        'PSNR 逐输入保留 +inf，梯度分母未定义时保留 null 和输入身份，均见完整 JSON 与原 CSV。', '',
        '## 原图表与可复核数据', '']
    for name in PANELS:
        lines.append('- '+name+': '+ ' · '.join('['+fmt.upper()+']('+relative(
            str(Path(result['original_figures']['path']).parent/(name+'.'+fmt)))+')' for fmt in ('png', 'pdf')))
    for name in CSV_ROWS:
        path=str(Path(result['original_figures']['path']).parent/(name+'.csv'))
        lines.append('- ['+name+'.csv]('+relative(path)+')')
    lines += ['', '## 原采集费用与当前范围', '',
        '| 原运行 | 唯一结算 GPUh |', '|---|---:|']
    lines += ['| '+row['run_id']+' | '+str(row['actual_GPUh'])+' |' for row in result['original_once_only_costs']]
    lines += ['', '原 A32+B36 合计 '+str(result['original_A32_plus_B36_GPUh'])+' GPUh，包含原预热、控制、校准、重复及分配开销；'
        '本索引新增 GPUh 为 0，未重新结算。', '',
        '本批支持旧 CAL 上的高速布局与保真比较；新方法增量、新输入确认及人类评审不由此索引证明。'
        '25D 原 DEV128 仍为独立历史开发证据，不与本批混合计算加速比；S/Q 方法与 F18/Q5 后续结果保持待接受。', '',
        '[原完整分析]('+relative(result['original_analysis']['path'])+') · [机器索引](accepted-results.json)', '']
    output.mkdir(parents=True)
    (output/'accepted-results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    (output/'FAST_RESULTS.md').write_text('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise ValueError('Fresh paper index directory required')
    result = accepted_results(args.manifest)
    write_index(result, args.output_dir)
    print(json.dumps(dict(status=result['status'], original_exports=len(result['exports']),
                         roles=len(result['prompt_equal_summaries']['ALL']), GPU_submissions=0)))


if __name__ == '__main__':
    main()
