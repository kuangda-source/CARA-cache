#!/usr/bin/env python3
"""Local evidence inventory and CPU table-fit timing, without GPU or SSH."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import platform
from statistics import mean
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(name):
    data=(ROOT/name).read_bytes()
    return json.loads(gzip.decompress(data) if name.endswith('.gz') else data)

def inventory():
    refs={
        'accepted40_capture':'reports/wc_h1_cost_curve_full60_collection_20261014_0245.json.gz',
        'accepted40_independent':'reports/wc_h1_cost_curve_full60_independent_acceptance_20261014.json',
        'H1':'manifests/wc_source_phase_absolute_h1_parameters_r1_20261013.json',
        'math_parameters':'manifests/wc_math_n2_frozen_parameters_r1_20261012.json',
        'RA_table':'reports/wc_ra_calibration_r1_terminal_20261010_calibration_table_native.gz',
        'RA_calibration':'reports/wc_ra_calibration_r1_terminal_20261010_capture_and_independent_audit.json',
        'action_profile':'reports/wc_action_cost_real_r1_terminal_20261010_capture_and_independent_audit.json',
        'source16':'reports/wc_source_phase16_live_or_terminal_capture_20261012.json',
        'source16_independent':'reports/wc_source_phase16_complete_scalar_and_cell_analysis_20261012.json',
        'N1':'reports/wc_math_n1_live_or_terminal_capture_20261012.json',
        'N1_independent':'reports/wc_math_n1_complete_independent_scalar_reconstruction_20261012.json',
        'old_prices':'reports/wc_action_cost_real_r1_bound_ranking_inputs_20261010.json',
        'readout_source':'src/wcomr/cfg_guided_w1_deployment.py',
        'H1_controller_source':'src/wcomr/source_phase_absolute_h1_control_r1.py',
        'table_fit_source':'src/wcomr/source_phase_table_fit_r1.py',
        'memory_source':'src/wcomr/simple26d_memory_r2.py',
        'grid_source':'src/wcomr/paper_baseline_grid_r1.py'}
    v={k:read(n) for k,n in refs.items() if n.endswith(('.json','.gz'))}
    source=v['accepted40_capture'];proof=v['accepted40_independent']
    assert proof['status']=='FULL60_RECEIPT_AND_ALL40_FULL93_AGGREGATES_INDEPENDENTLY_ACCEPTED'
    assert digest(ROOT/refs['accepted40_capture'])==proof['stored_input_sha256']
    raw=gzip.decompress((ROOT/refs['accepted40_capture']).read_bytes())
    assert hashlib.sha256(raw).hexdigest()==proof['input_sha256']
    final=source['final'];assert len(final['rows'])==60 and final['scored_scientific_paths']==40
    rows=[r for r in final['rows'] if r['section']=='TIMED']
    assert len(rows)==40 and all(r['endpoint_audit']=='PASS' and r['status']=='COMPLETE' for r in rows)
    methods=sorted({r['method'] for r in rows});scenes=sorted({r['scene'] for r in rows})
    assert len(methods)==10 and len(scenes)==4 and len({(r['scene'],r['method']) for r in rows})==40
    observations=[]
    for r in rows:
        d=r['LPIPS'];assert d['frames']==len(d['frame_distances'])==93
        assert math.isclose(mean(d['frame_distances']),d['mean_LPIPS'],rel_tol=1e-12,abs_tol=1e-12)
        names=('method_install_seconds','core_seconds','guarded_pipeline_without_write_seconds','method_cleanup_seconds','video_write_seconds')
        assert all(math.isfinite(r[n]) and r[n]>=0 for n in names)
        assert r['guarded_pipeline_without_write_seconds']>=r['core_seconds']
        observations.append(dict(scene=r['scene'],method=r['method'],**{n:r[n] for n in names},
            recorded_guardrails_and_outer_pipeline_seconds=r['guarded_pipeline_without_write_seconds']-r['core_seconds'],
            recorded_install_guarded_cleanup_seconds=r['method_install_seconds']+r['guarded_pipeline_without_write_seconds']+r['method_cleanup_seconds'],
            LPIPS=mean(d['frame_distances']),GPU_peak_allocated_bytes=None,
            current_memory_repair_boundary_seconds=None,
            fixed_source_version_not_final_profile=True))
    aggregates=[]
    timing_keys=(*names,'recorded_guardrails_and_outer_pipeline_seconds',
        'recorded_install_guarded_cleanup_seconds')
    for m in methods:
        chosen=[r for r in observations if r['method']==m];assert len(chosen)==4
        aggregates.append(dict(method=m,denominator=4,means={n:mean(r[n] for r in chosen) for n in timing_keys},
            mean_LPIPS=mean(r['LPIPS'] for r in chosen)))
    # Existing labels only: verify the tiny statistical fit reproduces the
    # deployed frozen table before measuring its CPU runtime.
    from wcomr.source_phase_table_fit_r1 import fit,validate_complete
    points=v['source16']['final']['points'];validate_complete(points)
    assert v['source16']['post_exit']['exit_code']==0
    assert v['source16_independent']['all8_parent_controls_pass']
    assert fit(points)==v['H1']['table_model']
    repeats=[]
    for _ in range(5):
        wall=time.perf_counter();cpu=time.process_time();table=fit(points)
        cpu=time.process_time()-cpu;wall=time.perf_counter()-wall
        assert table==v['H1']['table_model'];repeats.append(dict(wall_seconds=wall,CPU_process_seconds=cpu))
    history=[]
    for key,role in [('RA_calibration','RA joint-error and propagation prior'),('action_profile','Old post-probe action prices'),
                     ('N1','Source fusion coefficient and development diagnostics'),('source16','Four source-phase error cells and controls')]:
        record=v[key]
        if 'actual_GPU_wall_seconds' in record:
            assert record['GPU_exit_code']==record['CPU_exit_code']==0 and record['independent_checks']['success']
            seconds=record['actual_GPU_wall_seconds'];scope=record['planned_scope']
        else:
            assert record['supervisor']['child_exit_code']==0 and record['post_exit']['exit_code']==0
            seconds=record['supervisor']['wall_seconds'];scope=record['final']['scope_counts']
        history.append(dict(role=role,ref=refs[key],wall_seconds=seconds,actual_GPUh=seconds/3600,
            scope=scope,includes_controls_loads_outputs_or_research_capture=True,
            minimum_deployment_calibration_cost=False))
    table=v['RA_table'];assert len(table['observed_rows'])==table['defined_rho_count']==6
    assert table['guided_weights']==[8,-7] and table['maximum_estimated_reuse_age']==6
    cells=v['H1']['table_model']['cells'];assert len(cells)==4 and sum(c['training_points'] for c in cells.values())==16
    for p in (v['H1'],v['math_parameters']):
        for n,h in p['sources'].items():assert digest(ROOT/n)==h
    return dict(status='DEPLOYMENT_COST_SOURCE_INVENTORY_AND_CPU_FIT_MEASURED_NOT_FINAL_GPU_PROFILE',
        source_bindings={k:dict(path=n,sha256=digest(ROOT/n),stored_bytes=(ROOT/n).stat().st_size) for k,n in refs.items()},
        old_accepted_formal_paths=40,old_scored_frames=3720,old_batch_per_scene=observations,old_batch_method_aggregates=aggregates,
        method_dependencies={
            'A_NO_P':dict(paper_name='GCR efficient workpoint',beta=1.,shared_alpha={'steps_1_to_24':1.,'steps_25_to_36':.5},
                selector='Frozen RA prior',RA_table_fingerprint=table['fingerprint'],actual_D_history_only=True,
                learned_generator_parameters=0,online_teacher_calls=0,offline_GCR_residual_regression_required=False),
            'TABLE_PHASE_H1':dict(paper_name='Calibrated phase allocation high-fidelity workpoint',
                H1_fingerprint=v['H1']['fingerprint'],math_fingerprint=v['math_parameters']['fingerprint'],
                cells={k:{x:c[x] for x in ('training_points','C_scale','A_ratios','actual_NEW_P_birth_mean')} for k,c in cells.items()},
                fitted_cell_scalars_used_for_C_A_P_risk=12,model_specific_RA_prior_retained=True,
                old_action_price_scope=v['H1']['prices_scope'],online_teacher_calls=0,learned_generator_parameters=0)},
        CPU_statistical_table_fit=dict(host=platform.platform(),python=platform.python_version(),labels=16,cells=4,
            identical_to_frozen_table=True,one_untimed_verification_then_five_measured_fits=repeats,
            average_wall_seconds=mean(r['wall_seconds'] for r in repeats),label_generation_or_GPU_cost_included=False),
        historical_related_collection_jobs=history,
        historical_related_jobs_total_GPUh=sum(r['actual_GPUh'] for r in history),
        historical_total_is_minimum_deployment_cost=False,
        final_minimum_calibration_GPUh=None,final_request_GPU_peak_allocated_bytes=None,
        missing_final_measurements=['Minimum necessary label acquisition workload, separately from controls and prior exploration',
            'Matched final-code C/A/D prices after the same paid two-probe prefix',
            'Final request init/cleanup and boundary GC alongside primary text-denoise-VAE time',
            'Per-request CUDA allocated/reserved peaks with an explicit reset boundary',
            'Probe/warp/head/RF/controller/cache-maintenance split with paired output/action parity'],
        current_peak_counter_semantics='Existing max_memory_allocated is process-cumulative without per-request reset; not a per-method peak comparison',
        break_even_request_count=None,break_even_requires_matching_quality_and_measured_calibration_cost=True,
        new_video_or_final_latency_claim=False,active_N06_or_N05_stage_changed=False,GPU_submissions=0,SSH_queries=0,ledger_written=False)

def markdown(v):
    rows=['# 部署成本证据盘点与最终profiling待项','',
        '**已把两个冻结工作点的实际依赖、四格表CPU拟合和已有40条请求的计时边界整理为可复算证据。** 本轮仅使用本地已验原件，零GPU、SSH或预算写，不触碰同26D或新强基线生产stage。','',
        '## 已确定的部署依赖','',
        '- A_NO_P使用β=1与共享阶段强度：1—24步为1、25—36步为0.5；依赖冻结RA先验和请求内真实D锚点，不需要拟合新的生成器或GCR残差回归。',
        '- H1额外使用来源×阶段四格统计表，16个开发状态产生12个C/A/P风险统计标量，保留原RA与近似来源语义。在线没有教师或生成器训练。',
        '- 表格拟合已用原16点重建，与冻结表完全相同；五次CPU拟合均保留。该耗时只覆盖标量统计，不包含获取教师标签。','',
        f"本机五次表拟合平均 {1000*v['CPU_statistical_table_fit']['average_wall_seconds']:.6f} ms。固定H1完整参数文件为 {v['source_bindings']['H1']['stored_bytes']} 字节；包含来源元信息，不声称是最小部署包。",'',
        '## 已有采集费用及其用途','',
        '|相关采集|原GPUh|包含的实验工作|','|---|---:|---|']
    for r in v['historical_related_collection_jobs']:
        rows.append(f"|{r['role']}|{r['actual_GPUh']:.9f}|完整原scope、加载、对照、研究采集与输出均保留|")
    rows+=['',f"四项相关历史卡合计 {v['historical_related_jobs_total_GPUh']:.9f} GPUh。它记录已发生的相关研究采集成本，**不是最低必要标定成本，也不是每次部署都需重跑的费用**。最低必要采集的实测值仍为空。",'',
        '## 已接受420批次的计时边界复算','',
        '下面是四个原CAL等权均值，仅重算旧批次计时字段。主计时是文本编码＋去噪＋VAE；guarded还包含安全管线与外层流程，安装和清理另列。旧批次早于当前GC修复，不能代替最终N08/N09计时。全10方法、40条逐场景记录在机器回执，不拼场景赢家。','',
        '|配置|主计时s|guarded流程s|安装＋guarded＋清理s|写盘s|','|---|---:|---:|---:|---:|']
    for r in v['old_batch_method_aggregates']:
        t=r['means'];rows.append(f"|{r['method']}|{t['core_seconds']:.4f}|{t['guarded_pipeline_without_write_seconds']:.4f}|{t['recorded_install_guarded_cleanup_seconds']:.4f}|{t['video_write_seconds']:.4f}|")
    rows+=['','这些字段包含并行性与原顺序条件，不能用两层计时相减声称某个单一模块的纯耗时；本表也没有把额外费用加到旧加速倍数。','',
        '## 最终需要补的N09测量','',
        '1. 固定最终代码和硬件后，测同一双probe之后的C/A/D真实价格，校验当前旧head费用转移与实际执行器一致。',
        '2. 记录完整请求安装、初始化、清理及请求边界GC，与主计时和guarded流程并列；加载、预热、写盘继续单列。',
        '3. 给每请求显存峰值规定reset时刻。现有max_memory_allocated未逐请求reset，不能据此比较不同方法的独立峰值；修复后owner全释放是生命周期证据。',
        '4. profile与lean成对核对全步输出、动作、历史和终态。分组件CUDA事件留到最终一次同步后读取，profiling路径不计入clean速度均值。',
        '5. 把最低必要标签采集与RA基础、对照重复、候选搜索、视频输出分别计费。现有采集可复用，但不从完整研究账单臆造最低部署成本或回本数量。','',
        '可在最终N08整卡中显式登记额外profiling路径并合并估价，也可单独完整登记N09；所有额外路径/预热/控制在GPU准入前计入整体费用。这里尚未选定新GPU卡，不隐含增加当前N05的66路径。','',
        '原N06仍04:55一次验收，N05完整生产CPU已接受并待其后准入。正式主线顺序和原预算不变；F/B、P/T1探索、人评、训练、OMR均没有新增。','']
    return '\n'.join(rows)

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--markdown',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists() and not a.markdown.exists()
    v=inventory();v['script_sha256']=digest(Path(__file__))
    a.output.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n');a.markdown.write_text(markdown(v))
    print(json.dumps(dict(status=v['status'],old_formal_paths=40,identical_CPU_table_fit=True,
        average_fit_ms=1000*v['CPU_statistical_table_fit']['average_wall_seconds'],historical_related_GPUh=v['historical_related_jobs_total_GPUh'],
        final_minimum_calibration_GPUh=None,GPU_submissions=0,SSH_queries=0)))

if __name__=='__main__':main()
