#!/usr/bin/env python3
"""Recompute the saved complete R2 result summary without SSH or new scoring."""
import collections
import gzip
import hashlib
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = 'reports/wc_paper_N07_refusal_repair180_R2_terminal_collection_20261017_1250.json.gz'
ACCEPTANCE = 'reports/wc_paper_N07_refusal_repair180_R2_terminal_canonical_independent_acceptance_20261017.json'
OUTPUT = 'reports/wc_paper_N07_R2_complete_results_analysis_20261017.json'
REPORT = 'research/547_WC_N07_R2_COMPLETE_RESULTS_FIDELITY_COST_SIMPLE_CONTROLS_AND_N08_NEXT_20261017.md'


def main():
    raw = (ROOT / CAPTURE).read_bytes()
    value = json.loads(gzip.decompress(raw))
    accepted = json.loads((ROOT / ACCEPTANCE).read_text())
    assert accepted['capture_sha256'] == hashlib.sha256(raw).hexdigest()
    assert accepted['terminal_receipt_audit_accepted'] and accepted['scientific_available_cohorts_with_registered_missingness']
    assert accepted['original_CPU_post_exit_code'] == 0 and not accepted['audit_failures']
    rows = [r for r in value['final']['rows'] if r['section'] == 'TIMED']
    assert len(rows) == 160
    cases = {c['id']: c for c in value['bound_inputs']['cases']}
    lookup = {(r['case_id'], r['method']): r for r in rows}
    grouped = value['final']['grouped_statistics']
    methods = value['bound_inputs']['method_ids']
    prompt_ids = sorted({c['prompt_id'] for c in cases.values()})
    assert len(prompt_ids) == 8
    checked_frames = 0
    for row in rows:
        if 'LPIPS' not in row:
            continue
        score = row['LPIPS']
        assert score['frames'] == 93 and len(score['frame_distances']) == 93
        assert math.isclose(statistics.mean(score['frame_distances']), score['mean_LPIPS'], abs_tol=1e-12)
        native = lookup[(row['case_id'], 'NATIVE35')]
        assert score['reference_sha256'] == native['video_artifact']['sha256']
        assert score['candidate_sha256'] == row['video_artifact']['sha256']
        checked_frames += 93
    assert checked_frames == 126 * 93
    points = {}
    for prompt in prompt_ids:
        cs = sorted([c for c in cases.values() if c['prompt_id'] == prompt], key=lambda c: c['seed'])
        assert [c['seed'] for c in cs] == [17, 43]
        points[prompt] = {}
        for method in methods:
            rs = [lookup[(c['id'], method)] for c in cs]
            t = statistics.mean(r['core_seconds'] for r in rs) if all(
                r['status'] in ('COMPLETE', 'VIDEO_REJECTED') and r.get('raw_model_audit') == 'PASS' for r in rs) else None
            q = statistics.mean(r['LPIPS']['mean_LPIPS'] for r in rs) if all('LPIPS' in r for r in rs) else None
            points[prompt][method] = dict(time=t, LPIPS=q, statuses=[r['status'] for r in rs])
    summaries = []
    for method, original in zip(methods, grouped['methods']):
        assert method == original['method']
        ts = [points[p][method]['time'] for p in prompt_ids if points[p][method]['time'] is not None]
        qs = [points[p][method]['LPIPS'] for p in prompt_ids if points[p][method]['LPIPS'] is not None]
        assert len(ts) == original['complete_two_seed_time_prompts'] and len(qs) == original['complete_two_seed_quality_prompts']
        assert math.isclose(statistics.mean(ts), original['available_complete_prompt_mean_seconds'], abs_tol=1e-10)
        assert math.isclose(statistics.mean(qs), original['available_complete_prompt_mean_LPIPS'], abs_tol=1e-12)
        rs = [r for r in rows if r['method'] == method]
        summaries.append(dict(method=method, **{k: original[k] for k in (
            'complete_two_seed_time_prompts', 'complete_two_seed_quality_prompts',
            'available_complete_prompt_mean_seconds', 'available_complete_prompt_mean_LPIPS')},
            outcomes=dict(collections.Counter(r['status'] for r in rs)),
            scored_videos=sum('LPIPS' in r for r in rs), full8_prompt_results=None))

    def comparison(candidate, baseline):
        qids = [p for p in prompt_ids if all(points[p][m]['LPIPS'] is not None for m in (candidate, baseline))]
        tids = [p for p in prompt_ids if all(points[p][m]['time'] is not None for m in (candidate, baseline))]
        joint = sorted(set(qids) & set(tids))
        qc = statistics.mean(points[p][candidate]['LPIPS'] for p in qids)
        qb = statistics.mean(points[p][baseline]['LPIPS'] for p in qids)
        speed = sum(points[p][baseline]['time'] for p in tids) / sum(points[p][candidate]['time'] for p in tids)
        return dict(candidate=candidate, baseline=baseline, quality_prompt_ids=qids, time_prompt_ids=tids,
            candidate_LPIPS=qc, baseline_LPIPS=qb, LPIPS_change_percent=100 * (qc / qb - 1) if qb else None,
            speedup=speed, time_change_percent=100 * (1 / speed - 1),
            improved_quality_prompts=sum(points[p][candidate]['LPIPS'] < points[p][baseline]['LPIPS'] for p in qids),
            joint_quality_time_prompt_ids=joint,
            joint_speedup=sum(points[p][baseline]['time'] for p in joint) / sum(points[p][candidate]['time'] for p in joint),
            joint_speed_reported_as_secondary_availability_analysis=True)
    comparisons = []
    for original in grouped['comparisons']:
        r = comparison(original['candidate'], original['baseline'])
        assert r['quality_prompt_ids'] == sorted(original['quality_complete_prompt_ids'])
        assert r['time_prompt_ids'] == sorted(original['time_complete_prompt_ids'])
        assert math.isclose(r['speedup'], original['available_complete_prompt_speedup'], abs_tol=1e-12)
        if r['LPIPS_change_percent'] is not None:
            assert math.isclose(r['LPIPS_change_percent'], original['available_complete_prompt_LPIPS_change_percent'], abs_tol=1e-10)
        r['preregistered_absolute_LPIPS_change_bootstrap95'] = original['available_cohort_LPIPS_change_prompt_bootstrap95']
        r['preregistered_speedup_bootstrap95'] = original['available_cohort_speedup_prompt_bootstrap95']
        comparisons.append(r)
    readout = comparison('FRONT_DENSE_A', 'FRONT_DENSE_C')
    result = dict(status='COMPLETE_R2_SAVED_RESULTS_INDEPENDENT_SUMMARY_NO_NEW_SCORING',
        capture_ref=CAPTURE, capture_sha256=hashlib.sha256(raw).hexdigest(), acceptance_ref=ACCEPTANCE,
        terminal_receipt_audit_accepted=True, whole160_all_success=False,
        scientific_available_cohorts_with_registered_missingness=True,
        original_scope=value['config']['scope_counts'], formal_status_counts=dict(collections.Counter(r['status'] for r in rows)),
        all126_scores_recomputed_from_11718_frame_distances=True, checked_frames=checked_frames,
        methods=summaries, prompt_seed_results=points, preregistered_comparisons=comparisons,
        secondary_fixed_front_readout_comparison=readout,
        refusal_or_missing_rows=[dict(id=r['id'], case_id=r['case_id'], method=r['method'], status=r['status'],
            LPIPS_missing_reason=r.get('LPIPS_missing_reason')) for r in rows if 'LPIPS' not in r],
        actual_GPUh=accepted['actual_GPUh'], cumulative_settled_GPUh=value['pool']['used_gpu_hours'],
        available_GPUh=value['pool']['available_gpu_hours'], stable_repeated_speed_claim=False,
        methods_or_parameters_retuned=False, SSH_queries=0, GPU_submissions=0)
    assert not (ROOT / OUTPUT).exists()
    (ROOT / OUTPUT).write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    lines = ['# N07-R2完整结果：高保真工作点得到确认，调度与低成本修正的边界更清楚', '',
        '**本轮原完整180位置已结束并完成适用原件验收：129条正式视频通过，126条具匹配参考的视频完成全部93帧LPIPS，零技术失败、零原件审计失败。H1的高保真信号跨多个新提示词保留；低成本修正未稳定优于RA，H1也尚未超过简单前密集策略。下一步按原冻结五角色执行N08重复测速。**', '',
        '## 1. 目标、方法与冻结设计', '',
        '本轮检验开发阶段冻结的方法能否推广到新提示词和双seed，并同时对照调过阈值的WorldCache/RA、原生少步与同26D简单策略。主平台Cosmos-Predict2.5-2B、单A6000；768×432、93帧、16fps；35请求步实际36更新，Native26实际27更新。', '',
        '8个预先选定提示词×seed17/43×十方法，共160正式位置；另20完整预热、一次模型加载。原source为`6e10aa31197b4c137705b9117090c3a4e538e863`，输入、方法、阈值和比较协议均未依本轮结果调整。', '',
        '主计时为同步的文本编码＋去噪＋VAE解码；加载、视频写盘、安全检查及请求外围维护另列。每个提示词/seed/方法仅测一次，两seed不是重复测速。N08负责固定相同输入的三轮重复计时。', '',
        '## 2. 完整分母与验收', '',
        '| 项目 | 结果 |', '|---|---:|', '| 完整位置 | 180/180已处理 |', '| 完整预热 | 20/20完成，十个等价控制全部PASS |',
        '| 正式位置 | 129完成／20文本拒绝／11视频拒绝 |', '| 技术失败／未到达／原件审计失败 | 0／0／0 |',
        '| 正式可解码视频 | 129 |', '| 同输入同seed Native35参考兼容评分 | 126×93＝11718帧 |', '| 接受但缺匹配原生参考 | 3，保留缺失 |',
        '| 源文件身份 | 1750/1750一致 |', '',
        '独立接受标记为`terminal_receipt_audit_accepted=true`、`scientific_available_cohorts_with_registered_missingness=true`；因存在原拒绝和参考缺失，`scientific_full_scope_accepted=false`，不将其写成160条全部成功，也不把合法拒绝判为算法失败。全8提示词无缺失均值保持空值。先合并每个提示词的两seed，再对提示词等权；置信区间按提示词bootstrap4096次，帧不作为独立样本。', '',
        '## 3. 十方法结果总表', '',
        '以下均为各方法拥有完整双seed的可用提示词均值；质量与计时覆盖数分别标明，不能直接把不同覆盖数的单列均值拼成支配结论。LPIPS越低越接近同配置Native35。', '',
        '| 内部配置 | 完成/16 | 已评分视频 | 质量提示词/8 | 平均LPIPS↓ | 计时提示词/8 | 主计时秒↓ |', '|---|---:|---:|---:|---:|---:|---:|']
    for r in summaries:
        lines.append(f"| {r['method']} | {r['outcomes'].get('COMPLETE',0)} | {r['scored_videos']} | {r['complete_two_seed_quality_prompts']} | {r['available_complete_prompt_mean_LPIPS']:.6f} | {r['complete_two_seed_time_prompts']} | {r['available_complete_prompt_mean_seconds']:.3f} |")
    lines += ['', '## 4. 预登记配对比较的关键结果', '',
        '| 候选 vs 对照 | 质量提示词数 | LPIPS相对变化 | 改善提示词 | 计时提示词数 | 对照/候选加速比 | 候选耗时变化 |', '|---|---:|---:|---:|---:|---:|---:|']
    wanted = {('A_NO_P','WC_HALF'),('A_NO_P','RA_DEFAULT'),('A_NO_P','RA_DOUBLE'),('TABLE_PHASE_H1','NATIVE35'),('TABLE_PHASE_H1','NATIVE26'),('TABLE_PHASE_H1','WC_HALF'),('TABLE_PHASE_H1','RA_DEFAULT'),('TABLE_PHASE_H1','FRONT_DENSE_C'),('TABLE_PHASE_H1','FRONT_DENSE_A')}
    for r in comparisons:
        if (r['candidate'],r['baseline']) not in wanted:continue
        delta='—（原生失真为0）' if r['LPIPS_change_percent'] is None else f"{r['LPIPS_change_percent']:+.2f}%"
        lines.append(f"| {r['candidate']} vs {r['baseline']} | {len(r['quality_prompt_ids'])} | {delta} | {r['improved_quality_prompts']}/{len(r['quality_prompt_ids'])} | {len(r['time_prompt_ids'])} | {r['speedup']:.4f}× | {r['time_change_percent']:+.2f}% |")
    lines += ['', '**最大的正结果：H1保留了高保真工作点。** 相对WorldCache，六个完整双seed质量提示词的LPIPS平均降低84.48%；七个完整计时提示词平均主计时增加约5.55%。相对近似耗时的Native26，失真降低87.71%，耗时增加约1.00%。与Native35相比，主计时约1.268×加速。它支持“较完整生成更省算、较少步或激进缓存更接近原生”的工作点，而非相对所有方法同时更快更准。', '',
        '**最大的待解决问题：当前收益还不能唯一归功于自适应分配。** H1相对简单FRONT_DENSE_C的LPIPS高0.98%，时间高约0.30%；相对FRONT_DENSE_A的LPIPS高3.53%，时间低约0.30%。两项LPIPS绝对差的提示词bootstrap区间均覆盖0，不能据小均值差宣称优胜或统计等价。简单对照必须保留在论文中。', '',
        '**低成本修正需要按新证据修正判断。** A_NO_P相对RA_DEFAULT的LPIPS平均高2.04%，主计时高约1.02%；LPIPS绝对差95%区间跨0。不能沿用R1单提示词改善6.76%来代表本轮。相对更激进RA_DOUBLE，它能降低约11.69%失真，但需要更多时间；相对WorldCache更快，同时保真更弱。', '',
        '## 5. 修正读出的补充区分', '',
        f"固定前密26D规则下，FRONT_DENSE_A相对FRONT_DENSE_C的可用双seed均值LPIPS变化为{readout['LPIPS_change_percent']:+.4f}%，{readout['improved_quality_prompts']}/{len(readout['quality_prompt_ids'])}个提示词改善；计时变化{readout['time_change_percent']:+.4f}%。这是对原冻结十方法矩阵的补充分析，不替换18项原预登记比较，也不据此选择新方法。它提供读出修正具有条件价值的线索，不能被解释为A_NO_P已普遍胜过RA。", '',
        '所有18项预登记比较、每提示词双seed原值、缺失明细、按同一质量可用队列计算的补充计时比与11718逐帧复算检查均保存在机器结果。补充共同队列速度与原预登记七提示词计时明确分开，避免跨队列拼接收益。', '',
        '## 6. 预算、执行和下一步', '',
        f"本卡原实际费用{accepted['actual_GPUh']:.9f} GPUh；累计{value['pool']['used_gpu_hours']:.9f}/113 GPUh，预留0，余额{value['pool']['available_gpu_hours']:.9f} GPUh。未重置预算窗口或重记费用。", '',
        '用户已明确要求“R2验收完后先总结完整结果，再直接推进N08重复测速”。本报告及原件接受完成后，执行原冻结N08：AV28/Human seed0×五角色×三轮，30正式＋10完整预热，一次模型加载；五角色固定Native35/WC_HALF/RA_DEFAULT/A_NO_P/TABLE_PHASE_H1。整卡预计3.6275 GPUh，小于12且目前余额可覆盖；实际生产九命令CPU、整卡绑定及fresh UUID/锁/预算/独占资源通过后直接派发。实际启动后约一半时间一次技术检查、预计结束后一次完整验收。', '',
        'N08旨在测稳定实际费用与顺序波动，不拿本次新输入结果调参或替换五角色。N09部署与N10绝对视频质量仍待；LPIPS保真不是物理/语义质量结论。F/B已关闭，不自动恢复P/新W3探索。', '',
        '## 7. 可复核入口', '',
        f'- [完整原件快照](../{CAPTURE})', f'- [独立接受（带登记缺失）](../{ACCEPTANCE})', f'- [完整机器分析](../{OUTPUT})',
        '- [复算脚本](../scripts/summarize_wc_N07_R2_complete_results_20261017.py)', '',
        '时点记录：原12:50本地入口先因源码读取失败退出，尚未SSH；修复只读验收环境后，对原任务实际查收时间按capture的`observed_unix`如实保留，约12:54。只从同一已推送Git提交恢复本地工具源码，原服务器源码/原件/任务未重启。旧回执及原17:24历史时间均保留。']
    assert not (ROOT / REPORT).exists()
    (ROOT / REPORT).write_text('\n'.join(lines) + '\n')
    print(json.dumps(dict(report=REPORT, analysis=OUTPUT, scored_videos=126, checked_frames=checked_frames,
        preregistered_comparisons=len(comparisons), secondary_fixed_front_readout=readout), ensure_ascii=False))


if __name__ == '__main__':
    main()
