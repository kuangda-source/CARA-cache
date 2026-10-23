#!/usr/bin/env python3
"""Offline only: complete original terminal + independent acceptance -> report."""
import argparse, hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from wcomr.policy_generator_r1.historical_result_analysis_r1 import analyze_accepted, exposure_inventory


def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

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
    lines+=['',f"冻结计时判据：{t['status']}；平均绝对相对误差{t['mean_absolute_relative_error']:.3%}，最坏低估{t['maximum_underestimate_seconds']:.3f}s；B={t['budget_seconds']:.6f}s，余量固定{t['margin_seconds']:.1f}s。",'',
        '表中全部布局保留。相同D数不能替代同实测时间；每项prompt差值、描述性区间、顺序漂移和组件闭合见同名JSON。诊断时钟不用作速度证据；年龄因果、独立感知质量和泛化需后续受控实验。','',
        f"P1准备分支：`{d['P1_continuation']['action']}`。本报告不选择最终策略，不派GPU，不修改预算；新合同、曝光核查、完整报价与生产CPU通过后方可准入。"]
    return '\n'.join(lines)+'\n'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('capture','accepted','launch-ref','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    if a.output.suffix != '.json':raise ValueError('Output must be a new JSON path')
    md=a.output.with_suffix('.md')
    if a.output.exists() or md.exists():raise FileExistsError('Use unique output; originals are immutable')
    result=analyze_accepted(read(a.capture),read(a.accepted),capture_sha256=sha(a.capture),expected_launch=read(a.launch_ref))
    old_analysis=ROOT/'reports/cara_PG_P1_complete_budget_attribution_20261024.json'
    from wcomr.policy_price_terminal_r1 import record
    result['information_exposure']=exposure_inventory(record(read(a.capture),'card'),read(old_analysis))
    result['evidence']={name:dict(path=str(path),sha256=sha(path)) for name,path in [('capture',a.capture),('accepted',a.accepted),('launch',a.launch_ref),('old_P1_analysis',old_analysis),('analyzer',Path(__file__)),('analysis_module',ROOT/'src/wcomr/policy_generator_r1/historical_result_analysis_r1.py')]}
    raw=json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n'; text=render(result)
    with a.output.open('x') as f:f.write(raw)
    with md.open('x') as f:f.write(text)
    print(json.dumps(dict(status=result['status'],next_preparation=result['P1_continuation']['action'],GPU_submissions=0)))
if __name__=='__main__':main()
