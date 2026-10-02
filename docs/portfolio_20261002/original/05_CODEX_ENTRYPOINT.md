# Codex 接续入口：总调度落地与首批实验

**日期：2026-10-02｜版本：v1.0**  
这是给执行线程的指令模板。必须先读取实际项目，不能根据文档里的候选名虚构现有CLI、函数或完成状态。

## 1. 可直接复制的接续指令

```text
你正在接续已有世界模型质量—效率项目，不是创建一个新项目，也不是重建科研自动化框架。

请先读取我放入项目的：
- README.md
- 00_MASTER_SCHEDULE.md
- 04_SHARED_PROTOCOL_AND_SOURCES.md
随后只完整读取当前需要执行的方向文档：
- 01_WORLD_CACHE_EXPERIMENTS.md
- 02_OMR_EXPERIMENTS.md
- 03_SPECIALIST_DISTILLATION_EXPERIMENTS.md

再读取现有项目的 AGENTS、GOAL、CURRENT_STATE、NEXT_ACTIONS、最近实验报告、预算账本和 memory/handoffs/LATEST.md。
检查 git status、当前运行任务和可复用结果，保留已有未提交修改。不要覆盖旧结果，不要重复已经完成且配置兼容的实验。

核心组织方式是：WorldCache 为默认主执行；OMR 条件解锁；专家化蒸馏保留独立实验入口但暂不新开第三个长期GPU任务。
实际入口由最新证据决定，不是无条件重跑W1。W1优化近似，W3优化刷新收益；专家蒸馏先单学生，再互补性，再路由。

本次先完成：
1. 把当前真实结果映射到新文档的实验ID，区分已完成、证据不足、技术阻塞和未知。
2. 给出一个最值得执行的下一实验，写成现有schema的实验卡。
3. OMR只核实代码、匹配adapter、predictor、配置和评测资源；无完整资源不训练随机adapter冒充复现。
4. 专家线只审查已有数据是否足够做可预测性诊断；没有已批准教师采集预算就不新增标签生成。
5. 在已有明确授权内，仅执行本批最小任务；无授权则交付状态映射、实验卡和成本，停在NEEDS_APPROVAL。

不得把本包的4/12/20 GPU·h建议值当作授权。实际取项目更严格的上限，一次最多一个昂贵GPU任务。不得自动训练主干、上LoRA、启用新backbone、跑完整96场景、发外部消息、使用付费评分或启动跨方向大组合。

决策前观测必须因果可用。cache步的真实深层输出、额外OMR梯度、反事实续推均是有成本的离线标签，不得用于本次在线决策或更新部署cache。诊断与干净测速分离。

已批准的GPU任务运行期间，等待、监控和基础解析交给确定性程序，不因查进度反复调用模型。一次完成事件至多一次主要分析。429时持久化并停止。三个未减少关键不确定性的实验触发方向审查，而不是三个不涨分就机械放弃。

报告只需：实际做了什么、证据与全部结果、配置/数据/代码版本、真实成本、未完成项、当前状态、一个最值得执行的下一任务。
更新既有CURRENT_STATE、HYPOTHESIS_LEDGER、EVIDENCE_MAP、DECISION_LOG、NEXT_ACTIONS和handoff，不另建重复的项目记忆系统。
```

这段指令中的相对路径由实际放置位置替换。项目已有明确路径时优先使用，不要求把多个文档都复制到根目录。

## 2. 首批选择树

### 情况 A：WorldCache 已有最新 W1 结果

读取结果并核对配置、主指标与真实时间。已有效则直接规划独立确认；只有局部收益则做固定掩码终点验证；明确有局部分组结构才开W2；明确有同预算重排空间才开W3。

不能因为新文档讨论了Head，就打断一个即将完成的W1确认任务。

### 情况 B：WorldCache 已可运行，但没有可用近似诊断

提出WC-W1A最小子批，复用原生/行为轨迹，最多先8场景×3预定状态；预算不足则缩小并保留部分证据。额外full真值不得写回部署状态。

### 情况 C：只有部署记录，没有可信基线

补WC-F1的2–4场景smoke和成本，不立刻跑所有方向。

### 情况 D：WorldCache 技术阻塞，OMR 已有匹配资源

如当前授权允许跨方向筛查，提出OMR-O0S；否则记录后备准备状态，提交一个范围清楚的实验卡。不能暗中把“修环境”改成训练新adapter。

### 情况 E：两条宿主都暂时无法跑

只做可复用日志分析、数据缺口、源码/配置映射、资源清单和最小实验卡。技术阻塞不是科研否证；不为“必须产结果”改做未经同意的新大项目。

## 3. 实验卡契约

沿用项目既有schema。以下示例只说明必须明确的字段；所有null都必须由真实证据填充，不允许默认批准。

```yaml
experiment_id: WC-W1A-BATCH01
parent_experiment_id: null
status: PROPOSED
owner_direction: WORLD_CACHE
scientific_question: 同状态下在线标量校准能否改善深层近似？
primary_change: 仅替换深层近似器，保留固定行为状态与策略
hypothesis: 历史真实anchor的浅深层增量具有可利用关系
entry_evidence_refs: []
existing_equivalent_result_refs: []
fixed_config_ref: null
actual_command_ref: null
code_commit: null
local_diff_ref: null
data:
  manifest_ref: null
  split: train_calibration
  scene_count_cap: 8
  states_per_scene_cap: 3
  seed_policy_ref: null
controls:
  - official_approximation
  - one_simple_history_baseline
  - online_scalar_calibration
primary_metric: same_state_relative_mse
endpoint_requirement: 局部改善只能解锁固定掩码终点验证，不能直接宣称净收益
causality_checks:
  - observation_before_teacher
  - no_diagnostic_truth_commit
  - true_anchor_provenance
budget:
  authorization_ref: null
  max_gpu_hours: null
  max_single_job_wall_seconds: null
  max_storage_gb: null
  max_paid_api_cost: 0
  reserved_recovery_budget: null
  worst_case_estimate_ref: null
permissions:
  run_gpu: false
  train_student: false
  modify_generator: false
  external_message: false
  paid_evaluation: false
outputs_ref: null
stop_conditions:
  - missing_authorization
  - causal_or_parity_test_failure
  - projected_budget_overrun
  - nonfinite_outputs
positive_interpretation: 当前设置存在可利用的近似改进信号
negative_interpretation: 当前近似器或观测可能不足，不能否定所有调度/蒸馏
next_candidates:
  - WC-W1B
  - targeted_observation_or_numerical_diagnosis
```

这是未授权示例；不要直接因复制粘贴启动。若已有批准卡，引用其授权并只在获准范围改字段，不能复制旧approval给新的训练或跨方向任务。

## 4. 权限与成本的确定性检查

启动前必须能回答：是否批准、是否已有结果、依赖是否READY、最坏新增成本是否在剩余额度内、是否存在其他昂贵作业、数据split是否正确、部署和诊断模式是否分离。

当前schema不支持某字段时，附到现有卡的notes/metadata，先保持兼容，不为执行一个实验先大改调度器。

拟议任务无法满足预算时，优先拆成更小但能区分假设的任务；不可完成的原子运行不提交。达到预算上限时保存结果并停止，不为了凑齐样本扩批。

## 5. 报告模板

```text
# 实验报告：<ID>
状态：<TECH_BLOCKED / INCONCLUSIVE / MECHANISM_ONLY / PROMISING / ...>

问题和唯一主改动：
真实配置、代码和数据版本：
复用了哪些既有结果：
实际新增执行项与未执行项：
全部样本结果及配对统计：
部署真实耗时、显存、标签/训练/评测/失败成本：
因果性与数值检查：
正面/负面证据及替代解释：
本轮是否减少了关键不确定性：
允许的有限主张与不能声称的结论：

下一任务（只选一个）：
选择理由、入口证据、最坏成本、必要权限：
需要更新的CURRENT_STATE/DECISION_LOG/NEXT_ACTIONS/handoff：
```

## 6. 应长期保留、但不写死当前阶段的规则

AGENTS适合保存因果性、预算、权限、复用、单昂贵任务和证据纪律；不应写死“永远只做W1”或“永远不训练”。当前阶段和获准范围放CURRENT_STATE与实验卡，后续通过门槛和明确审批可以合法升级。

本包不要求再建一套multi-agent系统。先把当前已有流程用于一个有价值的科学问题，复杂组件只在明确瓶颈时增加。
