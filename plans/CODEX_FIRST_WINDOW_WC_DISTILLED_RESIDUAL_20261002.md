# WC-D 首个探索窗口：接口与可预测性，专家化条件后置

2026-10-02（北京时间）；v0.1；状态：PROPOSED / DESIGN_ONLY。完整数学、样本、对照、参数与停止条件见[66设计](../research/66_WC_DISTILLED_RESIDUAL_EXPLORATION_DESIGN.md)，来源见[记录](../manifests/plan_update_sources_distillation_20261002.json)。本文是未来执行卡，不是已完成实验或预算授权。

## 1. 接续与本窗口目标

先核对 `AGENTS.md`、`EXPERIMENT_REPORT.md`、`research/02_CURRENT_STATE.md`、`research/09_NEXT_ACTIONS.md`、`memory/handoffs/LATEST.md` 和账本。当前冻结工作先完成并审计，不中断已有job、不替换WC-S/H队列。WC-D不以稀疏方法成功为前置，但需要另行分配具体窗口；同一时间只有一个昂贵GPU任务。

目标是回答：**缓存误差有没有低维结构；历史之外的当前廉价状态能否恢复这部分误差？** 不把首窗口扩大成完整MoE、论文CONF、少步蒸馏或新底座训练。

## 2. A窗口：D0，非GPU准备

建议CPU≤2h、GPU0；当前仅设计，程序尚未实现。

1. 审计旧W1同状态资产是否含post-warp P、同probe真Y与因果Z。已有聚合误差/QKV不能冒充标签。
2. 固定upstream、运行适配、现有真anchor/CFG/reset/70-counter语义。第一版纠正加在官方flow-warp之后、final_layer之前。
3. 完成零纠正、shadow无状态写入、标签目录隔离、reset/finite、solver-history恢复的CPU契约；真实无扰动性留D1实机smoke验收。
4. 冻结FIT24/CAL8/CONF8的新场景分组清单、input/prompt hash和历史使用表，禁止CAL8技术集作CONF；先抽FIT8+CAL4。
5. 冻结Z字段、projection seed17、token seed29、≤12labels/轨迹、2048分层token/call、文件schema/预算/存储估计。

交付 `reports/wc_d0_interface.json` 和未来的 `manifests/wc_d_split.json`、`manifests/wc_d_label_protocol.json`。未出现前不要假设collector、data或模型已就绪。

## 3. B窗口：D1采集 → D2离线，条件执行

建议GPU cap4h含load/shadow/失败/flush，CPU拟合≤4h；这些均未拨款。本项目旧4h余额约317.69秒不能转换成该窗口。实际单视频/label成本核定后，写有界scope与timeout再执行。

| 顺序 | 工作 | 主要控制 | 必须输出 |
|---|---|---|---|
| 1 | 1 TECH轨迹observer OFF/ON | 同权重/input/seed/protocol，trace与最终输出对等 | paired无扰动回执；未通过停止 |
| 2 | FIT8+CAL4同状态labels | Y/P面对同probe，shadow不更新student anchor | 全label/缺失/拒绝、source/data SHA、真实cost |
| 3 | train-only μ/U，q16/32/64 | 同scene划分，oracle只评分 | rank谱、重建能力、均值效应 |
| 4 | ridge / 条件小MLP | zero/μ/scalar/shrink；历史vs当前输入；直接Y公平学生 | 原空间η、系数误差、域/phase/age/CFG、harm率 |
| 5 | 决策 | 采用66预登记初筛门与小样本证据边界 | 继续single / 改观测 / 不确定 / 暂停 |

首个candidate优先ridge；MLP仅在线性留下明确缺口时。q/λ/输入组按66有限网格选择，不能把token随机分到训练和验证。所有基、归一化、阈值只来自FIT/CAL；CONF尚不查看。

## 4. 停止与向后解锁

接口或因果性失败→TECH_BLOCKED；没有足够合格skip→记录覆盖缺口，另设计缓存强度卡；投影好/预测差→改善廉价输入而非堆专家；预测有效→提出D3固定schedule三臂闭环的具体scope与cost。首窗口不自动提交D3–D6。

D4可复用离线labels测双头，但部署以D3为前置；必须有time-conditioned single、总参数匹配single、stage-only双头和whole-call oracle。不得用token级oracle胜出支持call级gate。

状态与输出沿用PROPOSED、TECH_BLOCKED、INCONCLUSIVE、MECHANISM_ONLY等；拟合好不叫生成质量正结果。Git存方案/代码/manifest/小回执，模型、张量、视频和连接信息留ignored资产目录。

## 5. 窗口结束报告

只回答：完成了哪张卡、真实预算/缺失项、结构与预测差距、支持哪项假设、为什么继续或暂停、下张卡的准确范围与成本。没有运行的内容写UNKNOWN。提交后同步GitHub，并在总览、状态、下一步与handoff中登记相同结论；不创建额外自动化或长期goal。
