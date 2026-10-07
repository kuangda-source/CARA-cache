# H-T39：零掩码GT差异的独立CPU取证

2026-10-08。[H-T38完整原GPU](153_WC_W3_PAIRED_CFG_CPU_AND_EXECUTION.md)保持source aa996ed、1父/8完整后缀/5新视频/1旧Native/两主要比较，继续原运行。新取证不是新的GPU实验，不修改原严格历史门或覆盖它的失败。

## 发现与范围

旧、新seed2的44调用前缀，仅kwargs.gt_frames的hash不同；其余输入、预测、deep、缓存和solver完全一致。新OFF1和BASE_first的MP4又与旧BASE逐字节一致。实际AST/CPU证明T2W条件帧数0、真实全尺寸mask为零；16个零mask组合一致、4个非零mask正对照有效，冻结WC forward不读GT额外参数。差异来源没有唯一定位，不据此宣称编码器随机或缓存错误。

[下一轮登记](../manifests/wc_w3_paired_inactive_gt_cpu_preregistration_20261008.json)先于联合臂质量曝光：允许新增CPU条件化解释，但原输入严格相同判据及其失败原件保留。GT在原有限性追踪中已经检查；新CPU也保留非有限拒绝。

## 新CPU审计与评分入口

[取证规则](../scripts/wc_w3_inactive_gt_forensic.py)只接受历史kwargs.gt_frames这一差异。原GPU必须完成完整生成、仅因原历史输入桥拒绝而exit1，原CPU必须保持exit1/零评分；共享锁/GPU/PID释放及全部费用结算后才能运行。其余全部历史输入、输出、缓存、deep、solver、完整终态、BASE/SINGLE pre46和编码字节必须一致；当前所有分支的输入仍严格相同，所有296个输入记录必须使用已证明的零mask。

[CPU入口](../scripts/audit_score_wc_w3_inactive_gt_forensic_cpu.py)先调用冻结verify_paired_row检查完整八后缀/四严格重复/恢复/动作与原生继续，再实际调用未改的历史验证器，记录其原拒绝。条件化桥通过后才用原冻结资源和读取/LPIPS函数：六视频全93解码、BASE/SINGLE/PAIRED三Native损失、两signed比较。BASE和SINGLE的93帧损失必须与旧CPU结果完全相同。任何其他差异均拒绝取证；新CPU成功也不称原GPU严格验收。

[新规则CPU检查](../reports/wc_w3_inactive_gt_forensic_new_gate_cpu_r1_20261008.json)复用实际旧轨迹和真实44输入前缀，0.309秒通过：GT-only接受；27项其他输入、mask、状态、编码、证明和帧均值破坏拒绝。额外构造“修复单槽但仅持平BASE”的有界夹具，明确不能报净收益，额外两次当前完整计算保留。这是规则检查，不是真实新评分；不重跑旧模型/AST夹具。

[新CPU监督](../scripts/deploy_wc_w3_inactive_gt_forensic_cpu.py)只等原三个PID及终态，原件按字节另存，再绑定新CPU评分。CPU没有GPU提交/下载，源和原件前后哈希一致。[原失败捕获](../scripts/capture_wc_w3_paired_cfg_refusal_cpu.py)独立归档原失败、全部生成和实际费用；[独立重建](../scripts/summarize_wc_w3_inactive_gt_forensic_cpu.py)从原始组件、输入、deep、逐帧损失和实际时间核算，先报告PAIRED对BASE的净效果，再报告对SINGLE的修复效果。

## 保持的解释边界

H-T38严格失败与H-T39条件化取证可以同时存在。即使取证通过，结果仍限于一个已曝光seed2/step23，完整重放和93帧不增加跨场景独立样本量；两次控制耗时属于诊断，完整GPUwall包含父、八后缀、编码、加载和审计。保真、未来实际计算和总费用分别报告，不作物理/语义接受或清洁端到端速度主张。

没有新GPU/Native、训练、稀疏扩展、人工评审或预算追加。累计24GPUh、旧全部费用及≤2h整卡自主政策保持。原GPU和新CPU实际终态、全部原件和新科学结果待后续记录。

## 原任务仍在运行，新CPU仅绑定等待

CPU source `30a81a82cdfc04204df6ed808bebabb5c9993be0`，独立 `.sync/wc-w3-inactive-gt-forensic-cpu-r1-20261008`，driver3294574。实际[启动回执](../reports/wc_w3_inactive_gt_forensic_cpu_r1_launch_20261008.json)及[现场绑定](../reports/wc_w3_inactive_gt_forensic_cpu_r1_live_binding_20261008.json)验证10份新CPU载荷、255份原GPU载荷、manifest/driver原字节和实际CLI。当前只等原GPU3285362/3285375与原CPU3285718终态，零新评分、GPU提交0；已部署不等于条件化审计通过。

截至本次现场核对，OFF1/OFF2、BASE_first、SINGLE_second和PAIRED_first五后缀已完成，PAIRED_second在跑；联合严格重复、SINGLE编码/历史桥、完整原拒绝和费用结算、条件化审计/评分仍待。原GT严格前缀失败保留，原GPU代码未改，根budget仍是最近结算21.127299587h；服务器24h为在途余额预留。

待原件终态和条件化CPU完成后，通过[独立CPU原件捕获](../scripts/capture_wc_w3_inactive_gt_forensic_cpu.py)及独立重建验收，不重启原GPU/旧CPU或修改已部署源码。原GPU严格验收、CPU条件化可解释性和科学净收益分别记录。
