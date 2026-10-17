#!/usr/bin/env python3
"""Raw-receipt-derived N07 tables and N07/N08 figures; no models or server."""
import argparse,collections,gzip,hashlib,json,math,statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCES=dict(
    N07_raw='reports/wc_paper_N07_refusal_repair180_R2_terminal_collection_20261017_1250.json.gz',
    N07_acceptance='reports/wc_paper_N07_refusal_repair180_R2_terminal_canonical_independent_acceptance_20261017.json',
    N07_analysis='reports/wc_paper_N07_R2_complete_results_analysis_20261017.json',
    N08_raw='reports/wc_paper_N08_balanced_full40_terminal_collection_user_status_20261017.json.gz',
    N08_original_capture_binding='reports/wc_paper_N08_independent_statistics_difference_diagnosis_20261017.json',
    N08_acceptance='reports/wc_paper_N08_balanced_full40_terminal_independent_acceptance_roundoff_r1_20261017.json')
LABELS=dict(NATIVE35='Full inference',NATIVE26='Native (26 requested)',WC_HALF='WorldCache (tuned)',
    RA_HALF='RA (0.5 threshold)',RA_DEFAULT='RA-CFGCache',RA_DOUBLE='RA (2.0 threshold)',
    A_NO_P='Efficient',TABLE_PHASE_H1='High fidelity',FRONT_DENSE_C='Front-dense (C)',FRONT_DENSE_A='Front-dense + GCR')
SLOTS=dict(FULL_NATIVE='NATIVE35',WORLD_CACHE='WC_HALF',RA_CFG_CACHE='RA_DEFAULT',
    GCR_EFFICIENT='A_NO_P',CPA_HIGH_FIDELITY='TABLE_PHASE_H1')

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(n):
    p=ROOT/n;b=p.read_bytes();return json.loads(gzip.decompress(b) if p.suffix=='.gz' else b)
def close(x,y):assert math.isclose(x,y,rel_tol=1e-12,abs_tol=1e-12),(x,y)
def quality(row):
    if row.get('endpoint_audit')!='PASS' or not row.get('LPIPS'):return None
    q=row['LPIPS'];assert len(q['frame_distances'])==q['frames']==93
    value=statistics.mean(q['frame_distances']);close(value,q['mean_LPIPS']);return value
def pair_mean(values):return statistics.mean(values) if all(v is not None for v in values) else None

def derive():
    sources={k:read(n) for k,n in SOURCES.items()};r=sources['N07_raw'];a=sources['N07_analysis'];n=sources['N08_raw'];accepted=sources['N08_acceptance']
    assert sources['N07_acceptance']['terminal_receipt_audit_accepted']
    assert sources['N07_acceptance']['scientific_available_cohorts_with_registered_missingness']
    assert a['capture_sha256']==sha(ROOT/SOURCES['N07_raw']) and a['all126_scores_recomputed_from_11718_frame_distances']
    assert accepted['scientific_full_scope_accepted'] and accepted['stable_repeated_clean_speed_claim']
    assert sources['N08_original_capture_binding']['capture_sha256']==sha(ROOT/SOURCES['N08_raw'])
    assert accepted['capture_ref']==SOURCES['N08_raw']
    raw=[q for q in r['final']['rows'] if q['section']=='TIMED'];cases=r['runner']['cases'];methods=r['bound_inputs']['method_ids']
    assert len(raw)==160 and len(cases)==16 and len(methods)==10
    lookup={(q['case_id'],q['method']):q for q in raw};prompts=sorted({q['prompt_id'] for q in cases});matrix={}
    for prompt in prompts:
        ids=[q['id'] for q in cases if q['prompt_id']==prompt];assert len(ids)==2
        matrix[prompt]={}
        for method in methods:
            rr=[lookup[case,method] for case in ids]
            times=[q.get('core_seconds') if q['status'] in ('COMPLETE','VIDEO_REJECTED') else None for q in rr]
            values=[quality(q) for q in rr];mean_time=pair_mean(times);mean_q=pair_mean(values)
            old=a['prompt_seed_results'][prompt][method]
            if mean_q is not None:close(mean_q,old['LPIPS'])
            else:assert old['LPIPS'] is None
            if mean_time is not None:close(mean_time,old['time'])
            else:assert old['time'] is None
            matrix[prompt][method]=dict(main_seconds=mean_time,LPIPS=mean_q,statuses=[q['status'] for q in rr])
    comparisons=[]
    for q in a['preregistered_comparisons']+[a['secondary_fixed_front_readout_comparison']]:
        candidate,baseline=q['candidate'],q['baseline']
        common=[p for p in prompts if all(matrix[p][m]['LPIPS'] is not None and matrix[p][m]['main_seconds'] is not None for m in (candidate,baseline))]
        assert common==sorted(q['joint_quality_time_prompt_ids'])==sorted(q['quality_prompt_ids'])
        qc,qb=[statistics.mean(matrix[p][m]['LPIPS'] for p in common) for m in (candidate,baseline)]
        tc,tb=[statistics.mean(matrix[p][m]['main_seconds'] for p in common) for m in (candidate,baseline)]
        close(qc,q['candidate_LPIPS']);close(qb,q['baseline_LPIPS']);close(tb/tc,q['joint_speedup'])
        comparisons.append(dict(candidate=candidate,baseline=baseline,registered_prompt_denominator=8,
            complete_joint_prompts=common,joint_n=len(common),candidate_LPIPS=qc,baseline_LPIPS=qb,
            absolute_LPIPS_change=qc-qb,LPIPS_change_percent=100*(qc/qb-1) if qb else None,
            joint_candidate_seconds=tc,joint_baseline_seconds=tb,joint_speedup_baseline_over_candidate=tb/tc,
            original_primary_time_prompts=q['time_prompt_ids'],original_primary_time_speedup=q['speedup'],
            original_absolute_LPIPS_change_bootstrap95=q.get('preregistered_absolute_LPIPS_change_bootstrap95'),
            secondary_front_readout_comparison=q==a['secondary_fixed_front_readout_comparison']))
    common=[p for p in prompts if all(matrix[p][m]['LPIPS'] is not None and matrix[p][m]['main_seconds'] is not None for m in methods)]
    scatter=[dict(method=m,main_seconds=statistics.mean(matrix[p][m]['main_seconds'] for p in common),
        LPIPS=statistics.mean(matrix[p][m]['LPIPS'] for p in common)) for m in methods]
    nrows=[q for q in n['final']['rows'] if q['section']=='TIMED'];assert len(nrows)==30
    scenes=sorted({q['scene'] for q in nrows});assert len(scenes)==2
    nmethods=list(SLOTS.values());nsummary=[]
    for scene in scenes:
        for method in nmethods:
            rr=sorted([q for q in nrows if q['scene']==scene and q['method']==method],key=lambda q:q['round'])
            assert [q['round'] for q in rr]==[1,2,3] and all(q['status']=='COMPLETE' for q in rr)
            times=[q['core_seconds'] for q in rr];qq=[quality(q) for q in rr];assert all(x==qq[0] for x in qq)
            slot=next(k for k,v in SLOTS.items() if v==method)
            original=next(q for q in accepted['timing_statistics']['scene_methods'] if q['scene']==scene and q['slot']==slot)
            close(statistics.mean(times),original['complete_repeat_mean_seconds'])
            close(statistics.stdev(times),original['complete_repeat_sample_std_seconds'])
            close(qq[0],original['complete_repeat_mean_LPIPS'])
            nsummary.append(dict(scene=scene,method=method,repeats=3,rounds=[dict(round=q['round'],position=q['position'],
                main_seconds=q['core_seconds'],LPIPS=quality(q),video_write_seconds=q['video_write_seconds'],
                guarded_pipeline_without_write_seconds=q['guarded_pipeline_without_write_seconds'],
                method_install_seconds=q['method_install_seconds'],method_cleanup_seconds=q['method_cleanup_seconds'],
                request_boundary_collection_seconds=sum(q['request_memory_lifecycle'][k]['seconds'] for k in ('before','after'))) for q in rr],
                main_mean_seconds=statistics.mean(times),main_min_seconds=min(times),main_max_seconds=max(times),
                main_sample_std_seconds=statistics.stdev(times),LPIPS=qq[0]))
    for q in nsummary:
        q['speedups_baseline_over_candidate']={base:next(x['main_mean_seconds'] for x in nsummary if x['scene']==q['scene'] and x['method']==base)/q['main_mean_seconds'] for base in ('NATIVE35','WC_HALF','RA_DEFAULT')}
    aggregate=[]
    for method in nmethods:
        rr=[q for q in nsummary if q['method']==method]
        seconds=statistics.mean(q['main_mean_seconds'] for q in rr)
        aggregate.append(dict(method=method,scenes=2,mean_main_seconds=seconds,mean_LPIPS=statistics.mean(q['LPIPS'] for q in rr),
            speedups_baseline_over_candidate={base:sum(q['main_mean_seconds'] for q in nsummary if q['method']==base)/sum(q['main_mean_seconds'] for q in rr) for base in ('NATIVE35','WC_HALF','RA_DEFAULT')}))
    return dict(status='ACCEPTED_RAW_N07_N08_PAPER_DATA_EXPORT_NO_NEW_EXPERIMENT',labels=LABELS,
        source_bindings={k:dict(path=p,sha256=sha(ROOT/p)) for k,p in SOURCES.items()},
        N07=dict(registered_formal_paths=160,registered_prompts=8,formal_status_counts=dict(collections.Counter(q['status'] for q in raw)),
            per_prompt_method_matrix=matrix,paired_comparisons=comparisons,full_eight_prompt_means=None,
            secondary_all_method_scatter=dict(availability_only_prompt_ids=common,prompt_count=len(common),seeds_per_prompt=2,methods=10,
                formal_videos=len(common)*2*10,points=scatter,changes_registered_primary_cohorts=False),
            latency_is_repeated_clean=False),
        N08=dict(registered_total_paths=40,warmup_paths=10,formal_paths=30,scenes=scenes,scene_methods=nsummary,scene_equal_aggregate=aggregate,
            repeats_are_not_independent_prompts=True,latency_is_repeated_clean=True,independent_new_input_generalization=False,
            resident_model_load_seconds=n['runner']['load_seconds'],whole_GPU_bill_hours=n['billing']['actual_GPUh'],whole_GPU_wall_seconds=n['billing']['wall_seconds'],
            whole_GPU_bill_is_not_single_generation_latency=True),
        pending_results=dict(N12=None,N10_quality=None),scoring_cost_is_generation_latency=False,
        main_timer='TEXT_ENCODING_DENOISING_VAE_ONLINE_CACHE_UPDATE_CORRECTION_REFRESH; REQUEST_INSTALL_BOUNDARY_GC_CLEANUP_LOAD_GUARD_WRITE_SEPARATE',
        new_quality_scores_computed=False,new_GPU_submissions=0,SSH_queries=0,weights_loaded=0)

def f(x,n=4):return '--' if x is None else f'{x:.{n}f}'
def tables(data,output):
    lines=['# N07：原配对统计与共同质量队列时间','',
        '保留原18个比较及前密A/C次级比较。LPIPS和共同队列时间使用同一完整双seed提示词；原主时间统计的队列及倍数另列。全8均值仍为空。','',
        '| Candidate | Baseline | n quality | n original time | LPIPS C | LPIPS B | LPIPS change % | Original time speedup | Joint quality-cohort speedup |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for q in data['N07']['paired_comparisons']:
        lines.append('| '+' | '.join([q['candidate'],q['baseline'],str(q['joint_n']),str(len(q['original_primary_time_prompts'])),f(q['candidate_LPIPS'],6),f(q['baseline_LPIPS'],6),f(q['LPIPS_change_percent'],3),f(q['original_primary_time_speedup']),f(q['joint_speedup_baseline_over_candidate'])])+' |')
    lines+=['','## 共同质量队列的实际主计时（次级配对视图）','',
        '| Candidate | Baseline | prompts | C seconds | B seconds | B / C |','|---|---|---:|---:|---:|---:|']
    for q in data['N07']['paired_comparisons']:
        lines.append('| '+' | '.join([q['candidate'],q['baseline'],str(q['joint_n']),f(q['joint_candidate_seconds'],3),f(q['joint_baseline_seconds'],3),f(q['joint_speedup_baseline_over_candidate'])])+' |')
    (output/'N07_paired_results.md').write_text('\n'.join(lines)+'\n')
    lines=['# N08：两个旧CAL场景的完整三轮测速','',
        '30正式视频均已接受；10完整预热不进入均值。每场景每方法3次，以下标准差仅描述硬件计时波动；不是6个独立提示词。倍数为匹配基线平均耗时除以候选平均耗时。','',
        '| Scene | Method | LPIPS | R1 seconds | R2 seconds | R3 seconds | Mean | SD | Min--Max | Native / C | WC / C | RA / C |',
        '|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|']
    for q in data['N08']['scene_methods']:
        scene='AV28' if q['scene'].startswith('av_28') else 'Human199'
        lines.append('| '+' | '.join([scene,q['method'],f(q['LPIPS'],6)]+[f(r['main_seconds'],3) for r in q['rounds']]+[f(q['main_mean_seconds'],3),f(q['main_sample_std_seconds'],3),f(q['main_min_seconds'],3)+'--'+f(q['main_max_seconds'],3)]+[f(q['speedups_baseline_over_candidate'][m]) for m in ['NATIVE35','WC_HALF','RA_DEFAULT']])+' |')
    (output/'N08_repeated_results.md').write_text('\n'.join(lines)+'\n')

def plots(data,output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import rc_context
    colors=dict(NATIVE35='#6b7280',NATIVE26='#828282',WC_HALF='#4a7eb0',RA_HALF='#7188a1',RA_DEFAULT='#476178',RA_DOUBLE='#6f879f',
        A_NO_P='#8b5bb5',TABLE_PHASE_H1='#11856b',FRONT_DENSE_C='#a97644',FRONT_DENSE_A='#cf9b5d')
    marks=dict(NATIVE35='*',NATIVE26='x',WC_HALF='s',RA_HALF='v',RA_DEFAULT='^',RA_DOUBLE='v',A_NO_P='o',TABLE_PHASE_H1='D',FRONT_DENSE_C='s',FRONT_DENSE_A='p')
    def point(ax,q,xkey='main_seconds',ykey='LPIPS',label=True,offset=(6,6)):
        method=q['method'];ax.scatter(q[xkey],q[ykey],c=colors[method],marker=marks[method],s=60 if method!='NATIVE35' else 100,zorder=4,edgecolors='white' if method!='NATIVE26' else None,linewidths=.6)
        if label:ax.annotate(data['labels'][method],(q[xkey],q[ykey]),xytext=offset,textcoords='offset points',fontsize=8,color=colors[method],ha='left' if offset[0]>=0 else 'right')
    with rc_context({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'svg.hashsalt':'worldcache-accepted-20261017'}):
        fig,ax=plt.subplots(figsize=(8.3,4.6));values=data['N07']['secondary_all_method_scatter'];rows=values['points']
        offsets=dict(NATIVE35=(-7,7),NATIVE26=(-5,-12),WC_HALF=(-6,-13),RA_HALF=(6,7),RA_DEFAULT=(6,9),RA_DOUBLE=(6,7),A_NO_P=(7,-13))
        for q in rows:point(ax,q,label=q['method'] in offsets,offset=offsets.get(q['method'],(6,6)))
        ax.annotate('High-fidelity group',(220,.053),xytext=(245,.13),textcoords='data',fontsize=8,arrowprops={'arrowstyle':'-','color':'#9ca3af'},color='#374151')
        inset=ax.inset_axes([.61,.47,.36,.40]);high=[q for q in rows if q['method'] in ['TABLE_PHASE_H1','FRONT_DENSE_C','FRONT_DENSE_A']]
        for q in high:point(inset,q,label=False)
        inset.set(xlim=(218.9,222.0),ylim=(.0505,.0542),title='High-fidelity detail')
        inset.tick_params(labelsize=7);inset.set_xlabel('Main latency (s)',fontsize=7);inset.set_ylabel('LPIPS',fontsize=7)
        inset.grid(alpha=.18)
        for q,off in zip(high,[(4,8),(-4,8),(4,-12)]):
            text={'TABLE_PHASE_H1':'High fidelity','FRONT_DENSE_C':'Front C','FRONT_DENSE_A':'Front + GCR'}[q['method']]
            inset.annotate(text,(q['main_seconds'],q['LPIPS']),xytext=off,textcoords='offset points',fontsize=6.5,ha='right' if off[0]<0 else 'left',color=colors[q['method']])
        ax.set(xlim=(122,301),ylim=(-.012,.515),xlabel='Main latency: text + denoising + VAE (s)',ylabel='LPIPS to matched full inference (lower is better)',title=f"N07: all ten methods on {values['prompt_count']} common prompts, two seeds")
        ax.grid(alpha=.18);fig.tight_layout()
        fig.savefig(output/'N07_common_cohort_quality_time.svg',metadata={'Date':'2026-10-17'})
        fig.savefig(output/'N07_common_cohort_quality_time.png',dpi=220);plt.close(fig)
        fig,axes=plt.subplots(1,2,figsize=(10.5,4.1),sharey=True)
        for ax,scene in zip(axes,data['N08']['scenes']):
            rr=[q for q in data['N08']['scene_methods'] if q['scene']==scene]
            for q in rr:
                x,y=q['main_mean_seconds'],q['LPIPS'];method=q['method']
                ax.errorbar(x,y,xerr=[[x-q['main_min_seconds']],[q['main_max_seconds']-x]],fmt='none',ecolor=colors[method],elinewidth=1,capsize=2,zorder=3)
                ax.scatter([r['main_seconds'] for r in q['rounds']],[y]*3,color=colors[method],s=10,alpha=.45,zorder=2)
                off={'NATIVE35':(-5,8),'A_NO_P':(6,-13),'RA_DEFAULT':(6,7),'WC_HALF':(-4,7),'TABLE_PHASE_H1':(7,8)}[method]
                point(ax,q,xkey='main_mean_seconds',offset=off)
            ax.set(xlim=(132,300),ylim=(-.012,.48),title='AV28' if scene.startswith('av_28') else 'Human199',xlabel='Main latency (s)')
            ax.grid(alpha=.18)
        axes[0].set_ylabel('LPIPS to matched full inference (lower is better)')
        fig.suptitle('N08: three balanced timing rounds; whiskers show observed min--max',fontsize=10)
        fig.tight_layout(rect=(0,0,1,.93))
        fig.savefig(output/'N08_repeated_quality_time.svg',metadata={'Date':'2026-10-17'})
        fig.savefig(output/'N08_repeated_quality_time.png',dpi=220);plt.close(fig)
    return matplotlib.__version__

def main():
    p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();assert not a.output_dir.exists()
    a.output_dir.mkdir(parents=True);data=derive()
    (a.output_dir/'data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    tables(data,a.output_dir);version=plots(data,a.output_dir)
    readme='''# 已接受结果的论文图表数据包：N07与N08

日期2026-10-17。图表展示低费用与高保真两个工作点以及简单调度对照；所有数据从已接受原件重算，来源与SHA见provenance.json，完整数字见data.json。内部ID始终保留，Efficient对应A_NO_P，High fidelity对应TABLE_PHASE_H1；论文工作名称沿用总映射。

## 文件与阅读顺序

- [N07原19项配对表](N07_paired_results.md)：18个原比较＋前密A/C次级比较；分别列质量共同队列、原主时间队列与同质量队列倍数。
- [N08逐场景三轮表](N08_repeated_results.md)：全部30正式计时、每轮秒数、均值/SD/最小最大、逐场景LPIPS以及Native/WC/RA基线除以候选。
- [N07共同队列图](N07_common_cohort_quality_time.svg)：十方法全部可比的5提示词×双seed，按可用性选队列，图为次级同队列可视化；原8提示词的拒绝与缺失在data.json保留，全8均值仍为空。
- [N08重复测速图](N08_repeated_quality_time.svg)：两个旧CAL分别显示，误差线为三轮观测最小/最大值；重复次数不当作独立提示词数。
- data.json保存全部双seed提示词矩阵、19项完整配对、30原始计时和源文件SHA。N12/N10未完成结果留空。

![N07](N07_common_cohort_quality_time.png)

![N08](N08_repeated_quality_time.png)

## 计时与质量口径

主计时为文本编码、去噪、VAE及在线缓存更新/修正/刷新。请求安装、边界GC、清理、模型加载、guardrail和写盘按原记录另列，N08每轮分量也保存在data.json。整卡GPU账单包含加载和预热等，不能替代单视频延迟。

N07每配置/seed一次正式计时，N08固定相同输入三轮平衡计时。两批分别使用自身匹配原生参考的93帧LPIPS；LPIPS刻画接近原生视频的程度，物理/语义质量补充由N10另测。N07共同5提示词图不改变原配对表的5/6提示词统计，也不将旧CAL计时替代新输入质量证据。图中无方法点插值或推断的Pareto连线。

## 可用英文图注

**N07.** Latency--fidelity trade-offs for all ten frozen N07 methods on five common prompts with two seeds each. Video LPIPS is averaged over both seeds and then equally over prompts; latency uses the same cohort. The inset resolves the high-fidelity configurations. This all-method visualization uses complete cases from the eight-prompt registered set; the original pairwise tables retain their respective available cohorts and all refusals.

**N08.** Repeated main latency and reference fidelity on two calibration scenes. Markers show three-round mean timings; whiskers span the observed minimum and maximum, with individual timings shown faintly. All three rounds reproduce the same accepted output for each method and scene. Main latency covers text encoding, denoising, VAE decoding and online cache computations; request setup/cleanup, initialization, guardrails and writing are recorded separately. Speedup is matched baseline time divided by candidate time.

## 复现

从仓库根运行 `MPLCONFIGDIR=/tmp/wc-paper-mpl .venv/bin/python scripts/export_wc_paper_accepted_figures_r1.py --output-dir 一个不存在的新目录`。脚本禁止覆盖既有输出；读取已保存原件，不查询服务器、不加载模型、不生成新视频或质量分数。图源为Matplotlib标准科学绘图，SVG可编辑、PNG供预览。
'''
    (a.output_dir/'README.md').write_text(readme)
    provenance=dict(status=data['status'],source_bindings=data['source_bindings'],exporter_ref=str(Path(__file__).resolve().relative_to(ROOT)),exporter_sha256=sha(Path(__file__)),matplotlib_version=version,
        outputs={p.name:dict(sha256=sha(p),bytes=p.stat().st_size) for p in a.output_dir.iterdir() if p.is_file()},GPU_submissions=0,SSH_queries=0,weights_loaded=0)
    (a.output_dir/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print(json.dumps(dict(status=data['status'],output=str(a.output_dir),N07_original_pairs=len(data['N07']['paired_comparisons']),N07_plot_prompt_count=data['N07']['secondary_all_method_scatter']['prompt_count'],N08_formal_paths=30,new_quality_scores=0,GPU_submissions=0,SSH_queries=0)))

if __name__=='__main__':main()
