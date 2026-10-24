#!/usr/bin/env python3
"""Offline only: complete original terminal + independent acceptance -> report."""
import argparse, hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from wcomr.policy_generator_r1.historical_result_analysis_r1 import analyze_accepted, exposure_inventory


def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_handoff(spec, launch, launch_sha256, capture):
    """Bind a prepared handoff to one complete run, without remote access."""
    if (spec['launch_sha256']!=launch_sha256 or
            any(spec[k]!=launch[k] for k in ('launch_id','source_revision','run_id','scope_counts')) or
            spec['card_sha256']!=capture['files']['card']['sha256']):
        raise ValueError('Prepared handoff launch/source/scope/card differs')

def render(d):
    lines=['# 104路径完整结果分析','',
        '仅由完整终态与独立接受生成；四CAL、seed0，两轮先按prompt合并。LPIPS表示相对Native的保真。','',
        '| 布局 | 两轮均时/s | LPIPS | 验证轮均时/s | 验证轮预算余量/s | 预测加6s可行 |',
        '|---|---:|---:|---:|---:|---|']
    for r in d['baseline_role_table']:
        q='—' if r['LPIPS_mean'] is None else f"{r['LPIPS_mean']:.6f}"
        lines.append(f"| {r['role']} | {r['full_request_mean_seconds']:.3f} | {q} | {r['formal_round_means_seconds'][1]:.3f} | {r['validation_headroom_seconds']:.3f} | {r.get('planning_feasible_with_fixed_margin','—')} |")
    lines+=['','| 预登记比较（左减右） | 时间差/s | LPIPS差 | 四prompt改善数 | 描述性关系 |',
            '|---|---:|---:|---:|---|']
    for r in d['registered_comparisons']:
        lines.append(f"| {r['left']} − {r['right']} | {r['time_delta_seconds']['mean']:.3f} | {r['LPIPS_delta']['mean']:.6f} | {r['LPIPS_delta']['negative_prompts']}/4 | {r['observed_relation']} |")
    t=d['timing']['frozen_result']
    lines+=['','| 24/25D布局 | 第一轮/s | 第二轮/s | 实测≤B | 预测+6≤B | 跨轮越界 |',
            '|---|---:|---:|---|---|---|']
    for r in d['budget_boundaries']:
        lines.append(f"| {r['role']} | {r['formal_round_means_seconds'][0]:.3f} | {r['formal_round_means_seconds'][1]:.3f} | {r['validation_measured_feasible']} | {r['planning_feasible_with_fixed_margin']} | {r['round_feasibility_disagrees']} |")
    lines+=['','| 冻结计时检查 | 实际值 | 原门槛 | 通过 |','|---|---:|---:|---|']
    for r in d['timing']['acceptance_checks']:
        lines.append(f"| {r['check']} | {r['value']} | {r['limit']} | {r['passed']} |")
    lines+=['',f"冻结计时判据：{t['status']}；平均绝对相对误差{t['mean_absolute_relative_error']:.3%}，最坏低估{t['maximum_underestimate_seconds']:.3f}s；B={t['budget_seconds']:.6f}s，余量固定{t['margin_seconds']:.1f}s。",'',
        '表中全部布局保留。相同D数不能替代同实测时间；每项prompt差值、描述性区间、顺序漂移和组件闭合见同名JSON。诊断时钟不用作速度证据；年龄因果、独立感知质量和泛化需后续受控实验。','',
        f"P1准备分支：`{d['P1_continuation']['action']}`。本报告不选择最终策略，不派GPU，不修改预算；新合同、曝光核查、完整报价与生产CPU通过后方可准入。"]
    lines+=['','固定掩码的最大复用年龄（当前步减最近真实D步）：',
            '', '| 布局 | 最大复用年龄 |', '|---|---:|']
    for r in d['anchor_age_inventory']:
        lines.append(f"| {r['role']} | {r['max_reuse_age']} |")
    lines+=['',
        '年龄表是布局描述，不是有效阈值：短年龄已有正证据，不等于只有年龄≤3才有效；SHARED26_C的最大年龄为5。年龄、位置、状态与alpha尚未单独隔离。',
        '同D数用于消融，同实测时间用于方法竞争力比较。不同D/A组合也可构成有效优势，不能只以同D数胜负裁定贡献。少步Native按实测时间配平，并补独立质量指标。',
        '固定6秒只加在预测提案上，实际时间门槛仍为B；不要求实测≤B−6。超预算3.89秒只描述时间差，不能由历史某次删D推断保真损失或修复难度。',
        '增加重复可改善均值估计，不能自动消除系统偏差或缩减余量；当前余量不变，未来修改须独立校准验证。',
        f"接续诊断：`{d['P1_continuation']['diagnosis']}`。若模型通过而布局实测超B，优先研究更低成本候选；若实测可行但预测缺余量，单列提案保守性，不改写实测失败。"]
    return '\n'.join(lines)+'\n'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('capture','accepted','launch-ref','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--handoff-spec',type=Path,help='Optional frozen run binding for the prepared R2 handoff')
    a=p.parse_args()
    if a.output.suffix != '.json':raise ValueError('Output must be a new JSON path')
    md=a.output.with_suffix('.md')
    if a.output.exists() or md.exists():raise FileExistsError('Use unique output; originals are immutable')
    capture=read(a.capture);launch=read(a.launch_ref)
    if a.handoff_spec:verify_handoff(read(a.handoff_spec),launch,sha(a.launch_ref),capture)
    result=analyze_accepted(capture,read(a.accepted),capture_sha256=sha(a.capture),expected_launch=launch)
    old_analysis=ROOT/'reports/cara_PG_P1_complete_budget_attribution_20261024.json'
    from wcomr.policy_price_terminal_r1 import record
    result['information_exposure']=exposure_inventory(record(read(a.capture),'card'),read(old_analysis))
    result['evidence']={name:dict(path=str(path),sha256=sha(path)) for name,path in [('capture',a.capture),('accepted',a.accepted),('launch',a.launch_ref),('old_P1_analysis',old_analysis),('analyzer',Path(__file__)),('analysis_module',ROOT/'src/wcomr/policy_generator_r1/historical_result_analysis_r1.py')]}
    if a.handoff_spec:result['evidence']['handoff_spec']=dict(path=str(a.handoff_spec),sha256=sha(a.handoff_spec))
    result['evidence']['frozen_acceptance_modules']={n:sha(ROOT/n) for n in (
        'src/wcomr/policy_generator_r1/historical_terminal.py',
        'src/wcomr/policy_generator_r1/historical_timing_analysis.py',
        'src/wcomr/policy_generator_r1/historical_collection.py')}
    raw=json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n'; text=render(result)
    with a.output.open('x') as f:f.write(raw)
    with md.open('x') as f:f.write(text)
    print(json.dumps(dict(status=result['status'],next_preparation=result['P1_continuation']['action'],GPU_submissions=0)))
if __name__=='__main__':main()
