# 834 — M1完整验收：未来缓存写入价值可辨识，推进M2

读写框架获得了首个真实机制信号。原完整14生成、四组完整latent/93RGB等价、八对正式评分、费用与图表全部接受。在Uniform19的固定第8更新上，仅移植Dense缓存写入使两旧FIT平均Alex参考误差降低**19.51%**，仅替换当前读出/求解器状态降低**2.02%**；完整Dense刷新降低**19.24%**。写项在两个输入及各自全部93帧上均改善。

这使后续主线明确进入M2：估计候选自身轨迹上的终点读写价值，再用少数合法固定K交换检验行动效用。M1是同父状态的机制干预；尚未产生新的19D调度方法或独立输入效果。

## 固定设计与实际执行

两旧FIT为AV28与Human199，seed0，原35请求/36实际更新、CFG7。Uniform19的D为1–7、16、19、22–29、31、36。第8步按“第一个合法C且下一步仍C”的动作/来源规则事前选定；9–15持续复用，没有按科学分数选点。

四格为00=(yC,cacheC)、10=(yD,cacheC)、01=(yC,cacheD)、11=(yD,cacheD)。y包括latent及完整UniPC预测历史/last_sample，cache包含两CFG分支、物理窗口、来源/工作状态。各完整请求重复同一前缀，实际支付14请求、504solver更新、512paired/1024CFG；八科学输出、四独立控制、两新Native。不是历史242-call共享前缀原型。

[完整接受](../reports/cara_read_write_complete_acceptance_r1_20261101.json)绑定原launch7949388215944eb98c7f64f21e8e1dd1、source b930df4b04a0924d8bea0af32c0f7aaf8c33a5c8及原A6000 UUID。14/14成功，00对独立Uniform19、11对独立D8的四组完整latent与93RGB逐值等价，四角父状态及冻结未来动作核对通过。参考均为本卡同输入的新Native，没有复用/重评旧A32/B36/E1指标。

## 完整终点结果

Alex LPIPS相对同输入新Native，越低越好；每输入93帧先平均，再对两个输入等权。

|输入|00 C读/C写|10 D读/C写|01 C读/D写|11 D读/D写|
|---|---:|---:|---:|---:|
|AV28|0.394613490|0.386051666|0.301383648|0.302752899|
|Human199|0.572739166|0.561786584|0.477232619|0.478490916|
|等权均值|0.483676328|0.473919125|0.389308134|0.390621907|

有符号分解采用原方案：read=L10−L00，write=L01−L00，interaction=L11−L10−L01+L00，joint=L11−L00；负值表示参考误差降低。

|作用|平均Alex变化|相对00平均损失|
|---|---:|---:|
|read|-0.0097572031|-2.0173%|
|write|-0.0943681945|-19.5106%|
|interaction|+0.0110709767|+2.2889%|
|joint|-0.0930544210|-19.2390%|

AV28写项降低23.6256%，Human199降低16.6754%；两个输入各93/93帧写项均为负。这是同一位置、同一父计划的两输入结果，93帧不当作93个独立样本。

平均写项绝对量约为读项的9.67倍。交互项为正，抵消部分单独收益；在已写入Dense缓存的条件下，再换Dense当前读出反而增加约0.001314 Alex（两个输入均为正）。因此不能把read和write当作可直接相加的硬收益，也不能用本点推导所有位置的固定重要性。

MSE和1−SSIM的写项在两个输入均改善；Human199的时序L1与梯度L1写项恶化，完整原数值见[分析JSON](../reports/cara_read_write_complete_analysis_r1_20261101.json)。本卡没有新的无参考质量或独立人类评价，不以参考LPIPS下降宣称全面视频质量改善。

## 对主方法的含义

同父干预支持“刷新通过更新后续复用来源产生终点作用”，不是只有当前输出纠错。只看当前局部q会遗漏这条状态通路的可能性，现在有真实端点机制证据支撑继续检验。

10/01均支付获得Dense真值的计算，不是免费写入或便宜部署动作。11的独立控制是额外增加第8步D的20D计划，00为19D；19.51%不是新19D调度相对强基线的部署收益。本卡时间是诊断时间，不报告clean speed或时间匹配结论。原A32冻结、WC/RA FIT UNMATCHED、B36/S/Q/搜索/E1决策及旧CAL范围保持，最终16/备用16没有访问。

## 技术、费用和原件

- [原GPU终态](../reports/cara_read_write_final_original_r1_20261101.json)、[释放接受](../reports/cara_read_write_final_release_accepted_r1_20261101.json)：guardian全段18:49:24.756至20:19:26.989，5402.233秒，原四进程/锁结束、Default恢复，硬1.95GPUh未超。
- [唯一中央结算](../reports/cara_read_write_final_settlement_r1_20261101.json)：实际**1.50062026643246 GPUh**，cap226、旧16.5责任保持。结算后used195.54048154808925、reserved16.5、available13.959518451910753；这是本卡结束快照，不替代新卡fresh准入。
- [完整工件接受](../reports/cara_read_write_final_artifact_accepted_r1_20261101.json)：原CPU20:24:59–20:25:38退出0，全部14工件/四等价门接受。[原评分终态](../reports/cara_read_write_final_score_CPU_capture_r2_20261101.json)及[八对完整接受](../reports/cara_read_write_final_scores_accepted_r1_20261101.json)：原评分CPU20:30:06–20:34:14退出0，247.152秒，八对/744候选帧全部完整；未重复评分。
- [四面板PNG](../reports/cara_read_write_complete_figures_r1_20261101/M1_read_write_contrasts.png)、[PDF](../reports/cara_read_write_complete_figures_r1_20261101/M1_read_write_contrasts.pdf)、[93帧CSV](../reports/cara_read_write_complete_figures_r1_20261101/all93_mean_frame_effects.csv)、[逐输入CSV](../reports/cara_read_write_complete_figures_r1_20261101/per_input_endpoint_effects.csv)均已导出并[图面/原件SHA检查](../reports/cara_read_write_complete_figures_visual_QA_r1_20261101.json)。无重算指标。
- [最终检查清单](../reports/cara_read_write_acceptance_schedule_r3_20261101.json)：同一终验曾为原CPU接受调整至20:34/20:40，完整接受后已删除；半程m1与终验m1-2均确认不存在，没有重复检查。

## M2继续顺序

[既定M2安排](../plans/cara_next_stage_20261101/read_write/M2_ADJOINT_IMPLEMENTATION_AND_HARD_ACTION_PLAN_R1.md)保持三个估值器：原S局部q、同一终点伴随的read-only、完整read+write。相同Uniform起点、两FIT/seed、合法约束、候选额度，先检验真实导数，再检验完整硬swap排序与正式终点评价。每轮最多两个不同候选，接受新计划后在自身轨迹重算；M3最多三轮。固定19D与实测双时钟分别验收。

缓存转移与离散伴随已按[833](833_CARA_M2_ORIGINAL_LINUX_ADJOINT_ACCEPTED_AND_VAE_BACKWARD_BOUNDARY_20261101.md)各五项实际Linux CPU接受。等待本卡评分时新增`cara_read_write_vae_r1.py`：在私有Wan2.1 wrapper上仅去掉核对过的no_grad包装，保留原normalization/dtype和时间缓存，原生产解码器不改。[本地三项R3](../reports/cara_read_write_vae_CPU_component_r3_20261101.json)通过一帧/全93小模型硬前向等价、调用者缓存保持、跨块VJP有限差分（误差4.00e-15）及模式拒绝；R1/R2缺log/time的CPU namespace失败原件保留。

下一项是该VAE适配的实际Linux导入与真实模型单转移/终点反向、全局固定槽/来源映射及48GiB峰值/全段费用。CPU小权重不替代真实Cosmos/VAE权重VJP或视频Alex梯度。M2新GPU范围与原账本许可仍需按完整卡准备；本卡单次许可不继承、不自动重派GPU。
