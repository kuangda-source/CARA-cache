# CARA-Cache 当前交接

先读[当前状态](repo:research/02_CURRENT_STATE.md)、[实验顺序](repo:research/09_NEXT_ACTIONS.md)与[价格独占655记录](repo:research/655_CARA_PRICE_GPU3_EXCLUSIVE_ADMITTED_AND_COORDINATED_SCHEDULE_20261023.md)。它们共用规范数据；旧长交接已完整归档。

{{snapshot}}

{{run_details}}

## 接续规则

- 原1624 launch已于08:26完整接受，原件见[649](repo:research/649_CARA_FULL1624_ACCEPTED_PRICE_AUDIT_AND_REFRESH_SCOPE_20261023.md)，不重复验收/提交。[独立价格刷新](repo:plans/cara_policy_generator_20261020/FULL1624_PRICE_REFRESH_R1_20261023.md)完整生产CPU已接受；修复host兼容入口后37项相关CPU检查通过。13:13:24沿原意图实际恢复并验证GPU3硬件独占，见[655](repo:research/655_CARA_PRICE_GPU3_EXCLUSIVE_ADMITTED_AND_COORDINATED_SCHEDULE_20261023.md)。GMSD已释放该卡，用户授权CARA优先。
- `--launch-ref`固定价格实际恢复启动`reports/wc_policy_price_refresh_full1624_GPU_actual_recovery_launch_20261023_1313.json`。unknown只恢复原句柄；已有恢复intent/launch，不能再次launch-gpu或resume-host-entry。提前退出保留实际终态与费用，原12:59解释器前失败不能冒充实际GPU启动时间。原R1 CPU失败、BANK24原ffprobe失败和后续恢复均保留。
- 使用已授权四卡私有入口；不恢复两卡、不触碰他人任务、不更改在跑stage。完整范围/预算/冻结门控不变，DEV不回流调阈值。
- 原1624标签和独占价格已完整接受，原价格6.916276 GPUh已结算。PG-P1已实际独占启动；只capture/recover原PG句柄，禁止再次launch或resume-authorization。新半程00:52、终态05:32绑定同launch；[661](repo:research/661_CARA_EXCLUSIVE_PRICES_ACCEPTED_PG_P1_ACTUALLY_ADMITTED_20261023.md)记录全部原件和接续。小历史诊断与少步Native维持P2独立完整报价。
- 有意义的进度、完成、失败或需用户行动时才通知；文档整理不构成新的实验观测。
- P1/P2接续准备见[652](repo:research/652_CARA_PG_P1_P2_CPU_PREPARATION_AND_HANDOFF_20261023.md)及[可执行接入设计](repo:plans/cara_policy_generator_20261020/P1_P2_CPU_HANDOFF_R1_20261023.md)。SELECT审计范围内无执行证据，首次端点前检查新增记录；P1最新[657](repo:research/657_CARA_PG_P1_FULL_CARD_COMBINATION_CPU_ACCEPTED_AND_PRICE_HANDOFF_20261023.md)及[整卡交接](repo:plans/cara_policy_generator_20261020/P1_FULL_CARD_COMBINATION_HANDOFF_R3_20261023.md)已完成整卡监督、真实93帧评分与终态复算组合CPU接受，报价8.844444/10.5不变。复用R3组合CPU原件，等待原价格完整接受与结算释放；新stage绑定标签/价格SHA，fresh资源准入后单次派发64位置完整卡，在本卡取得干净Native预算后生成提案。历史shadow和少步Native选择成本另外完整计入P2，不能因本轮CPU控制通过就直接派GPU。

后续修改规范数据和模板，再运行`python3 docs/tools/render_repository_docs.py`及`--check`；有意义的代码、配置、结果须同步私有GitHub。完整历史见[归档入口](repo:docs/archive/README.md)。

## P2并行准备

P1原64位置、10.5 GPUh及半程/终态安排保持不变。R2组合CPU已接受；新增真实五模型评分入口、去重绑定及34项本地控制完成。五原权重/固定源码已在本地齐备，四卡实际模型CPU待独立环境和磁盘准入。 本轮仅四卡只读核查和本地准备，未改P1环境或stage。最新磁盘约34.7GiB，未降低40GiB准入线。最终预算等P1完整接受及策略物理去重后确定，未新增GPU预算或派发。见[667真实质量入口与整卡绑定](repo:research/667_CARA_PG_P2_REAL_QUALITY_ENTRY_AND_CARD_BINDING_PREPARED_20261023.md)。

P2 CPU原件与绑定命令见[生产接续方案](repo:plans/cara_policy_generator_20261020/P2_NATIVE_HISTORY_PRODUCTION_HANDOFF_R1_20261023.md)。不重复已接受CPU；全P2监督/评分/终态组合尚待完成。78.5GPUh为未去重整体上界，不是已批额度；原累计226、退役两卡16.5责任保留。
