#!/usr/bin/env python3
"""Independently reconstruct timing ratios from complete captured CPU results."""
import json,math
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def main():
 capture=json.loads((R/'reports/wc_clean_speed20_live_or_terminal_capture_20261012.json').read_text());d=capture['final']
 assert d['status']=='CLEAN_SPEED20_COMPLETE40_ALL20_TIMINGS_AND93_FRAME_SCORES_AUDITED'
 assert d['source_revision']=='10b2a3bb5deefa123d241a7cc797b312caa101a2'
 assert not any(capture['original_processes'].values()) and all(capture['payload_verified'].values())
 assert capture['post_exit']['exit_code']==0 and d['complete_paths']==40 and d['timed_paths']==20 and d['warmup_paths']==20
 rows=[r for r in d['rows'] if r['section']=='TIMED'];assert len(rows)==20
 aliases={'av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632':'AV28','human_199':'Human'}
 labels={'NATIVE':'Native','WC':'WorldCache','RA':'RA','A_NO_P':'阶段 A（无 P）','KEEP_A_P':'KEEP＋阶段 A＋P'}
 comparisons=[];variation=[];increments=[]
 for r in rows:
  matched={a['method']:a for a in rows if a['scene']==r['scene'] and a['round']==r['round']};score=r['LPIPS'];assert score['frames']==93
  assert math.isclose(sum(score['frame_distances'])/93,score['mean_LPIPS'],rel_tol=1e-12,abs_tol=1e-12)
  recomputed={'scene':r['scene'],'method':r['method'],'round':r['round'],'core_seconds':r['core_seconds'],
      **{'speedup_vs_'+b:matched[m]['core_seconds']/r['core_seconds'] for b,m in [('Native','NATIVE'),('WC','WC'),('RA','RA')]},'LPIPS_mean':score['mean_LPIPS']}
  original=next(a for a in d['comparisons_all20'] if (a['scene'],a['method'],a['round'])==(r['scene'],r['method'],r['round']))
  assert recomputed==original;comparisons.append(recomputed)
 for scene in aliases:
  for method in labels:
   rr=sorted([r for r in rows if r['scene']==scene and r['method']==method],key=lambda r:r['round']);a,b=rr
   variation.append({'scene':scene,'method':method,'round1_seconds':a['core_seconds'],'round2_seconds':b['core_seconds'],
      'range_seconds':abs(b['core_seconds']-a['core_seconds']),'range_percent_of_mean':100*abs(b['core_seconds']-a['core_seconds'])/((b['core_seconds']+a['core_seconds'])/2),
      'rounds_RGB_equal':a['decoded_video']['RGB_sha256']==b['decoded_video']['RGB_sha256']})
  for rep in (1,2):
   a=next(r for r in rows if r['scene']==scene and r['round']==rep and r['method']=='A_NO_P');b=next(r for r in rows if r['scene']==scene and r['round']==rep and r['method']=='KEEP_A_P')
   increments.append({'scene':scene,'round':rep,'A_NO_P_seconds':a['core_seconds'],'KEEP_A_P_seconds':b['core_seconds'],'P_speedup':a['core_seconds']/b['core_seconds'],
       'P_seconds_saved':a['core_seconds']-b['core_seconds'],'LPIPS_NO_P':a['LPIPS']['mean_LPIPS'],'LPIPS_P':b['LPIPS']['mean_LPIPS'],
       'LPIPS_loss_reduction':a['LPIPS']['mean_LPIPS']-b['LPIPS']['mean_LPIPS'],'P_action_count':(b['actions'] or []).count('PP')})
 assert increments==d['P_increment_all4']
 assert len(variation)==len(d['variation_all10'])
 for a,b in zip(variation,d['variation_all10']):
  for k,v in a.items():
   if isinstance(v,float):assert math.isclose(v,b[k],rel_tol=1e-12,abs_tol=1e-12)
   else:assert v==b[k]
 independent={'status':'CLEAN_SPEED20_ALL20_TIMING_AND_SCORE_INDEPENDENT_RECONSTRUCTION_PASS','comparisons_all20':comparisons,'variation_all10':variation,'P_increment_all4':increments,'GPU_submissions':0,'ledger_written':False}
 (R/'reports/wc_clean_speed20_independent_reconstruction_20261012.json').write_text(json.dumps(independent,indent=2)+'\n')
 allpositive=all(p['P_seconds_saved']>0 for p in increments)
 slower=all(p['P_seconds_saved']<=0 for p in increments)
 conclusion='P 组合在两个场景、两轮均有净节时。' if allpositive else ('P 组合在两个场景、两轮均未产生净节时。' if slower else 'P 组合的净节时依赖场景或轮次，当前小测试没有一致的速度收益。')
 sup=d['GPU_supervisor'];ledger=sup['budget_after'];remain=ledger['cap_gpu_hours']-ledger['used_gpu_hours']
 out=['# WorldCache 小范围端到端测速结果（2026-10-12）','', '无 P 阶段 A 在两个场景、两轮均快于 WorldCache，且全93帧 LPIPS 更低；P 进一步降低 LPIPS，同时增加耗时。'+conclusion+'全部原始计时、波动与保真结果并列如下。','',
  '固定 AV28、Human，seed=0，35 请求步／36 实际更新／72 CFG，768×432、93 帧、16fps。阶段 A 为 BETA1_ONE_PHASE：第25步前α=1，之后α=0.5；有P、无P共享A，不启用E5 FAST。保持原KEEP来源规则、校准、阈值和正的P创建误差先验；未调参。','',
  f"完成20正式＋20完整预热、一次模型加载驻留；模型加载 {d['load_seconds']:.3f} 秒。每场景每配置预热2条，然后正序／反序各一轮。完整GPU全wall含加载／预热／失败／维护／写盘实计 {sup['wall_seconds']:.3f} 秒（{sup['wall_seconds']/3600:.6f} GPUh）；累计 {ledger['used_gpu_hours']:.6f}/{ledger['cap_gpu_hours']:.6f}，当前新增48预算余额 {remain:.6f} GPUh。GPU原PID已退出、锁与资源已释放。",'',
  '主计时为同步的文本编码＋去噪＋VAE解码；普通guardrail保留、含安全检查的流程总耗时另列。模型加载、算法安装、请求初态恢复、清理、输出核验与视频写盘在主计时外单列。算法推理中实际的缓存维护、候选head、修正、P投影、路由与刷新全部保留；关闭逐步审计张量复制／哈希／状态快照。倍数均按同场景同轮基线秒数÷候选秒数。','']
 for scene,label in aliases.items():
  out+=['## '+label,'','|配置|轮次|主计时秒|Native÷候选|WC÷候选|RA÷候选|全93帧LPIPS|','|---|---|---:|---:|---:|---:|---:|']
  for method,lab in labels.items():
   for r in comparisons:
    if r['scene']==scene and r['method']==method:out.append(f"|{lab}|{r['round']}|{r['core_seconds']:.3f}|{r['speedup_vs_Native']:.4f}×|{r['speedup_vs_WC']:.4f}×|{r['speedup_vs_RA']:.4f}×|{r['LPIPS_mean']:.6f}|")
  out+=['','|配置|正序秒|反序秒|两轮差秒|差值／两轮均值|','|---|---:|---:|---:|---:|']
  for v in variation:
   if v['scene']==scene:out.append(f"|{labels[v['method']]}|{v['round1_seconds']:.3f}|{v['round2_seconds']:.3f}|{v['range_seconds']:.3f}|{v['range_percent_of_mean']:.2f}%|")
  out+=['']
 out+=['## P 对同阶段 A 的净增量','','|场景|轮次|无P秒|有P秒|无P÷有P|节省秒（可负）|无P LPIPS|有P LPIPS|失真下降（可负）|P对数|','|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
 for p in increments:out.append(f"|{aliases[p['scene']]}|{p['round']}|{p['A_NO_P_seconds']:.3f}|{p['KEEP_A_P_seconds']:.3f}|{p['P_speedup']:.4f}×|{p['P_seconds_saved']:.3f}|{p['LPIPS_NO_P']:.6f}|{p['LPIPS_P']:.6f}|{p['LPIPS_loss_reduction']:.6f}|{p['P_action_count']}|")
 out+=['','P 为原 ROTATION_050 部分 MLP 更新（4/10/16/22 层、128-token块、50% 活跃块），本轮未扩大层数或替换注意力。', '',
 '这是KEEP＋A＋P整体运行系统对RA＋同A的实际增量，包含启用P所需的缓存、控制和维护；不能把完整系统差值只归因于P算子。','',
 '## 分列耗时（全部正式运行）','', '流程总秒包含上述主计时及普通安全检查／请求包装，不含写盘；该列不能再与主计时相加。加载只发生一次，未摊入单条计时。', '', '|场景|配置|轮次|含安全检查流程总秒（不含写盘）|写盘秒|安装秒|初态恢复秒|清理秒|终点核验秒|','|---|---|---|---:|---:|---:|---:|---:|---:|']
 for r in rows:out.append(f"|{aliases[r['scene']]}|{labels[r['method']]}|{r['round']}|{r['guarded_pipeline_without_write_seconds']:.3f}|{r['video_write_seconds']:.3f}|{r['method_install_seconds']:.3f}|{r['cache_rng_reset_seconds']:.3f}|{r['method_cleanup_seconds']:.3f}|{r['outside_timer_endpoint_check_seconds']:.3f}|")
 out+=['','## 预热（另计、全部保留）','','|场景|配置|预热序号|主计时秒|状态|','|---|---|---|---:|---|']
 for r in d['rows']:
  if r['section']=='WARMUP':out.append(f"|{aliases[r['scene']]}|{labels[r['method']]}|{r['round']}|{r['core_seconds']:.3f}|{r['status']}|")
 out+=['','## 实际验收与边界','','两flow60路径CPU对照、真实生产入口CPU通过；真实40路径的缓存／RNG初始化独立验收，40终点与旧审计源哈希及动作匹配、40视频各93帧完整解码并与旧RGB匹配；正式20视频各93帧LPIPS，20倍数／10波动／4增量独立重构。全部重复、预热与原范围保留，未选最快结果。','',
 '首次R1尝试在3条预热后因WC动作回执未收集而技术停止，0正式计时；3个终点均匹配旧源，两个Native视频93帧RGB已匹配。原源码、原件、CPU失败及完整范围封存，R2只补WC只读bool计数、独立重新全60CPU和真实入口门，并重新全部40路径，没有复用旧预热。R1实费0.302284958GPUh已在上述累计账本中计入；原终态为reports/wc_clean_speed20_r1_technical_attempt_terminal_20261012.json。', '',
 f"本次小测速含R1技术重试共 {sup['wall_seconds']/3600+0.302284957738852:.6f} GPUh；上述2.467250 GPUh是完整成功R2的全流程费用。CPU验证和406.242秒的全帧审计／评分未占用GPU，评分前后账本SHA完全一致。", '',
 '本轮回答这两个已曝光开发场景和固定seed下的实际运行成本与Native保真。两次重复提供运行波动，不能作为跨seed泛化或物理、语义、运动质量证明。单项结果用于改进该具体配置，不否定整个P或WorldCache方向。原P机制13.0600GPUh卡仍按用户要求暂缓，E2原卡保持；本轮不扩大搜索、训练或人评。','',
 f"执行源码：`{sup['source_revision']}`。原始完整回执：`reports/wc_clean_speed20_live_or_terminal_capture_20261012.json`；独立重构：`reports/wc_clean_speed20_independent_reconstruction_20261012.json`。服务器原件：`{capture['output']}`。"]
 # Interpretation uses the same raw rows, retaining the Human reverse RA counterexample.
 out += ['', '## 发现、实际取舍与下一步', '',
  '无 P 阶段 A：AV28 相对 Native 加速1.9508／1.9981×、相对WC加速1.1417／1.1423×，LPIPS相对WC下降22.6391%、相对RA下降23.7169%；Human 相对Native加速1.8934／1.8908×、相对WC加速1.1845／1.1846×，LPIPS相对WC下降7.7148%、相对RA下降9.0335%。这是这两个开发场景中可兑现的速度与保真正结果。', '',
  '对RA的速度差需逐轮看：AV28无P A快1.756／3.065秒；Human正序快1.353秒，反序慢3.898秒。Human RA本身两轮相差5.584秒（3.79%）。本轮支持更好的RA保真工作点，尚不能据此声称对RA稳定加速。', '',
  '加入P：AV28多18.561／18.352秒（增加12.71%／12.57%），LPIPS进一步下降0.9393%；Human多24.433／25.340秒（增加16.42%／17.07%），LPIPS进一步下降8.0486%。两轮输出RGB完全相同，保真提升可复验；这版P的价值是额外保真，同时付出明确的时间成本。相对WC，有P版本仍为1.0129／1.0147×及1.0174／1.0118×的小幅加速，保留全部差值，不将其放大为稳定大加速。', '',
  '建议下一轮保留固定无P A作为可用候选，优先安排独立场景／seed确认。P先做低成本的实际开销分解：候选head与控制、缓存维护、P部分MLP和D完整刷新；若对比E5 FAST，必须另登记并保持同一A、P、来源规则和输出等价控制。本轮没有实施这些变更，不能把额外18–25秒全部归因为P算子，也不能仅凭当前配置否定部分更新方向。', '',
  '原13.0600GPUh P机制卡仍暂缓；是否优先恢复该卡，应结合这里的保真—成本取舍讨论。没有据此次小测速自动开展下一张GPU卡。']
 (R/'research/374_WC_CLEAN_SPEED20_COMPLETE_RESULTS_20261012.md').write_text('\n'.join(out)+'\n')
 print(json.dumps({'status':independent['status'],'P_net_conclusion':conclusion,'GPUh':sup['wall_seconds']/3600,'remaining_GPUh':remain}))
if __name__=='__main__':main()
