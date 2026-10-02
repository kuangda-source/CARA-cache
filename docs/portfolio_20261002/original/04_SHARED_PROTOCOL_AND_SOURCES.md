# 共用实验协议、数据接口与来源索引

**日期：2026-10-02｜版本：v1.0**  
本文件约束全部方向。文献事实、已有计划、拟议假设与实测结果必须分开记录。

## 1. 三条线共享基础设施，不共享所有质量目标

| 方向 | 主要终点 | 训练/诊断信号 | 不允许的替代结论 |
|---|---|---|---|
| WorldCache / E-W | 对同seed原生视频的保真与时序质量、真实时间 | 同状态残差、后续刷新收益 | “模仿原生=物理正确” |
| OMR / E-O | SA、PC、Joint、真实时间与质量守卫 | JEPA能量、教师梯度/增量、方向误差 | “能量下降=物理能力提升” |
| E 独立专家 | 宿主终点+专家互补与路由净收益 | 各专家loss table、路由遗憾 | “专家使用率不同=功能解耦” |

语义遵循和物理评分按确定的评测器定义解释；推理不得把自动评分当作无误真值。

## 2. 数据划分与复用

### 2.1 优先保留既有有效划分

项目已有冻结划分时，先核对来源和泄漏风险，兼容则继续使用。本包建议的 `48训练/校准 + 16验证 + 32冻结测试` 是没有合适现成划分时的默认上限，不是要求重建数据集。

所有小样本试验取训练/验证子集。32+8、24+8等不同起点必须是同一清单的子集，不重新抽一套让曾用于训练的场景进入测试。

### 2.2 分组单位

同源视频、同场景、prompt近义改写、相同模板变体、首帧裁剪、多seed归入同一个 group。跨主干使用相同场景时保持其全局split，避免在A上调过的场景又被B当独立确认。

每步/每token/每帧是一个场景内的相关观测，不能按行随机划分。SVD、聚类、归一化、router监督、阈值和超参数都只在训练/校准分区建立；验证只作选择，测试只在冻结后确认。

### 2.3 状态与视频数据的兼容性

参考视频只能在模型、输入、seed、尺寸、solver、精度、CFG及必要实现条件一致时复用。当前状态上的深层真值、梯度或行动收益，还必须匹配该状态与历史；不能仅凭同prompt/seed就复用。

不同近似器会改变轨迹；不同adapter会改变教师；不同后续策略会改变收益标签。复用前必须检查这些版本键，不能因文件名相似就视为同一数据。

### 2.4 选择偏差

只在真实full步拿到的标签，会偏向原策略认为需要full的状态；对cache状态的结论要通过预定抽样审计补充。只选最坏失败样本可以做机制诊断，但总体测试仍需包含目标分布，不用失败集代替通用收益。

## 3. 最小运行 manifest

每个实验至少记录：

```yaml
identity:
  experiment_id: null
  parent_id: null
  scene_group_id: null
  split: null
  seed: null
  input_hash: null
model:
  generator_checkpoint_hash: null
  vae_hash: null
  teacher_or_adapter_hash: null
  upstream_commit: null
  local_commit: null
  local_diff_ref: null
config:
  resolution: null
  video_frames: null
  solver: null
  denoising_steps: null
  prediction_parameterization: null
  time_convention: null
  precision: null
  cfg: null
  attention_backend: null
  offload_or_sharding: null
policy:
  approximation_version: null
  behavior_policy_version: null
  continuation_policy_version: null
  guidance_rule_version: null
  teacher_type: null
  budget_mode: null
  protected_steps_ref: null
resources:
  gpu_model: null
  gpu_count: null
  authorization_ref: null
  actual_gpu_seconds: null
  wall_seconds: null
  peak_vram: null
```

这是字段契约示例，不声称项目已有这些API。可映射到现有schema，不重复造数据库。未知必填字段不自动补假值。

## 4. 同状态快照与因果性

快照至少包含 latent、solver历史输出/缓冲/计数、随机状态、条件、所有cache tensor与真实来源、校准统计、预算、mask/window、guidance状态和分支ID。

随机采样器的两个分支应使用相同预定未来随机数流；否则观测差异可能混入噪声。记录branch执行次序，抽查交换次序不改变结论。不同分支不能共享可变cache引用。

**推荐执行顺序：**

```text
保存真实状态与部署可用观测
       ↓
运行候选预测 / 选择动作
       ↓
单独的诊断分支获取教师标签
       ↓
标签只写离线数据，不写回正在评估的部署状态
```

禁用候选、禁用cache/纠正、标签扰动、分支顺序、条件隔离、异常回退、预算守卫都应有测试。技术smoke不能只有“脚本无报错”，也不能把bitwise不一致直接判为算法错误；先确定数值噪声容差。

## 5. 三类教师与标签接口

### 5.1 缓存残差

```text
teacher_type = cache_residual
observation = 当前合法局部特征、历史真实cache、时间/age
base_approximation_version = 固定近似器版本
target = full_deep_output(same_actual_state) - base_approximation(same_state)
```

cache步标签需要额外计算；如果只存范数，不能假装已具备训练高维输出的监督。

### 5.2 刷新收益

```text
teacher_type = refresh_value
label_mode = matched_budget | fixed_mask_diagnostic | lagrangian
initial_state_ref, initial_budget, legal_actions
continuation_policy_version, actual_future_action_trace
horizon = terminal | k4 | k8 | actual_shorter_length
loss_C, loss_F, cost_C, cost_F
signed_gain = J_C - J_F
```

固定mask诊断通常不同成本；matched budget未来具体动作可不同。K步与终点不同目标分开保存。对只剩一个合法动作的状态，不生成无意义的二选一训练标签。

### 5.3 OMR增量

```text
teacher_type = omr_delta | omr_gradient | normalized_omr_direction
clean_estimate_ref, generator_hash, adapter_hash, predictor_hash
mask_window_version, noise_time, eta, update_convention
normalization_and_reconstruction_rule
target = 对应约定下的真实教师输出
```

delta、raw gradient、归一化方向不能无标记混用。改变eta、mask或adapter不一定允许直接复用标签；必须按目标定义核对。

## 6. 评价和公平比较

### 6.1 缓存主指标

默认主要失真为逐帧LPIPS到同初始噪声的原生视频，按视频/场景聚合。PSNR/SSIM、终点latent差和同状态残差作辅助。若现有项目有更适用的已冻结契约，保留并说明原因。

辅助指标不允许事后“哪个最好看就用哪个作主结论”。相对失真改善同时报告绝对值；接近零的基线不使用巨大百分比制造收益。

### 6.2 OMR主指标

SA、PC及逐样本二者同时达标的Joint。校准侧先确定优化重点和非劣性容忍范围，不能根据测试表现切换主目标。

保真到原生不作为主要成功标准；原生错误被纠正通常会改变视频。JEPA能量用于机制解释，不替代外部任务评价。

### 6.3 共用守卫

清晰度/高频细节、事件是否实际发生、运动是否被异常压低、内容一致性、闪烁/拖影/抖动以及严重失败。二阶时间抖动J降低可能来自画面静止或模糊，必须与运动和清晰度共同检查。

没有可靠既有阈值时，先在校准侧记录重复噪声、proxy与盲评对应关系并登记容忍范围。首个小批可以把清晰度下降约5%、运动代理下降约10%作为**需人工复核的警戒线**，不是跨任务物理安全保证，也不是单指标自动淘汰。

人评小样本可用盲化A/B顺序和固定问题；评价者不能看到方法名和自动分数。付费VLM或外部标注需要相应授权。

### 6.4 三种匹配口径

| 口径 | 用途 | 必须披露 |
|---|---|---|
| 相同动作次数/位置 | 隔离近似器或梯度保持机制 | 实际时间仍可能不同 |
| 相同预算的动态策略 | 分配效率 | 保护回退、非均匀动作成本 |
| 相同真实时间或完整前沿 | 最终效率结论 | 部署所有必要开销 |

实验卡可把实际时间匹配窗口暂定为±5%，但必须同时给真实数值，并在曲线中检查结论。接近边界时优先更严格匹配；不能把超时样本静默移除。

同模型/同GPU、同precision与offload、同数据和调参次数。强基线可单独在校准侧调优，不使用只对新方法有利的默认值。

## 7. 计时与成本

### 7.1 测速协议

模型预热与必要同步，交错方法顺序。默认8个代表场景各3次干净重复作为开始；输出中位数与尾部，必要时增加重复。质量生成可以复用同条件视频，但测速不能带额外真值、profiler或dump。

**必须计入**部署实际使用的输入特征提取、规约、Head、路由、补偿重建、通信、offload、教师回退和正常解码。只记录必要纯去噪时间与端到端时间两个口径，明确文件IO是否包含。

冷启动/编译一次性成本单列；不和稳态混比。不同运行栈有缓存和编译差异时，先核对再报告加速。

### 7.2 预算账本

```text
reference_generation
behavior_trajectory_generation
same_state_teacher_calls
counterfactual_continuations
prefix_replay_and_snapshot_restore
student_training_and_hyperparameter_trials
quality_evaluation_and_decode
clean_timing_runs
failed_attempts_and_repairs
storage_and_transfer
```

同一次生产供A与E复用只扣总账一次，同时记录成本归属和被哪些实验使用。不得每个方向单独申请同一批数据再重复生成。

FVE定义为当前配置的一条原生视频纯去噪GPU秒；其他任务使用同分母归一化，只作辅助预算。跨硬件/主干要重新测分母，不能直接对比FVE数值代表绝对成本。

## 8. 统计与停止规则

配对单位是独立scene/prompt-family。每组先聚合种子，再做场景级bootstrap或其他适合的配对区间；不要把数千状态当数千独立视频。

pilot用来找机制和估成本，不宣称泛化已证实。冻结测试报告点估计和不确定性；不存在显著差异不等于两方法等价。非劣性需要预设margin和足够精度。

二值OMR评分根据开发侧配对不一致率估算可检出变化；32场景×2种子不保证能检出几个百分点。增加测试样本须保存先前冻结规则并明确序贯评估方式，不能反复查看直到显著。

同时报告均值、中位数、尾部和个体失败，避免只用极端样本驱动均值。小样本区间宽时写INCONCLUSIVE，不能为了自动调度把所有结果硬二分PASS/FAIL。

## 9. 建议证据状态

映射到项目已有状态枚举，不必须重命名：

| 状态 | 含义 |
|---|---|
| UNKNOWN | 本文无法确认，不代表尚未运行 |
| NEEDS_APPROVAL | 有可执行计划但授权不明确 |
| TECH_BLOCKED | 环境、资源、实现或数据阻塞 |
| INCONCLUSIVE | 样本或测量不足以决定 |
| MECHANISM_ONLY | 中间机制成立，尚无净终点收益 |
| PROMISING | 开发侧有可信端到端信号，尚待独立确认 |
| CONFIRMED_IN_SCOPE | 在明确配置/人群/指标范围内独立确认 |
| NO_GAIN_IN_SCOPE | 合法试验在当前范围没有有意义收益 |
| PAUSED | 因资源、优先级或边界暂缓，可恢复 |

三次未减少关键不确定性的实验触发方向审查；得到清晰的否证也可能是研究进展，不等于必须立刻停止所有探索。

## 10. 来源使用说明

以下为本轮实际核对的一手资料及项目文档。**参考方法支持可行性或对照设计，不证明本候选已有收益。**代码可用性和本地兼容性进入实验前仍需锁定版本。

文献标题和机制用于定位近邻，不宣称这是一份穷尽所有文献的首创检索。只复用抽象内容且未检验完整代码的论文，不应写成已完成方法复现。

### R1：WorldCache

*WorldCache: Content-Aware Caching for Accelerated Video World Models*, arXiv:2603.22286v1。用于定位既有probe、判据和近似机制；论文数字不当成本地基线。

`https://arxiv.org/html/2603.22286v1`

**R1b 官方实现：**2026-10-02读取到公开仓库；未审计用户本地commit或运行环境。

`https://github.com/umair1221/WorldCache`

### R2：OMR

*Off-Manifold Refinement: Guiding Video Generators with a Frozen World Model*, arXiv:2608.29904v1。核对§3的clean-time更新、adapter与predictor路径；质量和效率子集不同，不跨表混用。

`https://arxiv.org/html/2608.29904v1`

**R2b 官方资源页：**本次读取“Code and adapter weights”仍为Coming soon。此为2026-10-02访问快照，不证明用户未私下取得资源。

`https://itruonghai.github.io/omr/`

### R3：敏感性缓存

*SenCache: Accelerating Diffusion Model Inference via Sensitivity-Aware Caching*, arXiv:2602.24208。作为敏感性判据近邻；不能把普通误差预测改名为信任就视为独立创新。

`https://arxiv.org/abs/2602.24208`

### R4：预算门控

*BAG: Budget-Aware Gating for Diffusion Caching*, arXiv:2608.09231v2。可学习预算/轨迹门控的直接近邻；正式比较需匹配监督数据和离线成本。

`https://arxiv.org/html/2608.09231v2`

### R5：可学习缓存与蒸馏兼容

*DisCa: Accelerating Video Diffusion Transformers with Distillation-Compatible Learnable Feature Caching*, arXiv:2602.05449。用于审查“训练预测器补偿特征”的差异，不沿用其速度数字作为本地预期。

`https://arxiv.org/abs/2602.05449`

`https://github.com/Tencent-Hunyuan/DisCa`

### R6：阶段专家

*LESA: Learnable Stage-Aware Predictors for Diffusion Model Acceleration*, arXiv:2602.20497v1。已包含噪声阶段专家与闭环训练思路；固定阶段分工应作为专家化研究的重要对照。

`https://arxiv.org/html/2602.20497v1`

### R7：动态缓存与纠错联合学习

*OnlineCache: Learning Dynamic Caching Policies with Error Correction for Efficient Diffusion Inference*, arXiv:2607.29398。动态策略与可学习纠错组合的近邻；“何时算+怎么算”本身不足以构成全部差异。

`https://arxiv.org/abs/2607.29398`

### R8：局部失配与全局影响

*From Local Mismatch to Global Impact: Optimizing Cache Reuse Policy for Efficient Diffusion*（GCache）, arXiv:2608.13043。全局影响/策略优化近邻；反事实监督需要与其明确比较。

`https://arxiv.org/abs/2608.13043`

### R9a/R9b：闭环分布与行动成本监督

*A Reduction of Imitation Learning and Structured Prediction to No-Regret Online Learning*, AISTATS 2011。支持讨论学习策略改变访问分布的问题，不直接保证本视频实验的收敛。

`https://proceedings.mlr.press/v15/ross11a.html`

*Reinforcement and Imitation Learning via Interactive No-Regret Learning*, arXiv:1406.5979。行动后续成本监督的理论背景。

`https://arxiv.org/abs/1406.5979`

### R10：知识蒸馏基础

*Distilling the Knowledge in a Neural Network*, arXiv:1503.02531。用于区分教师—学生学习与新增能力/功能解耦主张。

`https://arxiv.org/abs/1503.02531`

### R11：稀疏专家基础

*Switch Transformers: Scaling to Trillion Parameter Models with Simple and Efficient Sparsity*, JMLR 2022。条件激活与总参数/活跃计算区分的背景，不意味着视频残差MoE已经验证。

`https://www.jmlr.org/papers/v23/21-0998.html`

### R12/R13：其他强基线入口

*Learning-to-Cache: Accelerating Diffusion Transformer via Layer Caching*, arXiv:2406.01733。

`https://arxiv.org/abs/2406.01733`

*From Reusing to Forecasting: Accelerating Diffusion Models with TaylorSeers*, arXiv:2503.06923。

`https://arxiv.org/abs/2503.06923`

## 11. 项目来源与证据范围

这些是本轮已读取的项目资料。它们保留在用户已有Library/项目中，未复制进本包；本包自身已经包含完成规划所需的新说明。

| ID | 文件 | 本轮依据 | 不能推断的内容 |
|---|---|---|---|
| P1 | `LONG_HORIZON_EXPERIMENT_PLAN_WorldCache_OMR_20260929.md` | W1/W2/W3、J0–J5、资源与12–16有效周路线 | 服务器当前已完成阶段 |
| P2 | `CODEX_FIRST_BATCH_WorldCache_OMR_20260929.md` | 先接续、因果性、首批范围与授权规则 | 当前确有剩余GPU额度 |
| P3 | `TRUST_CACHE_EXPERIMENT_PLAN_20261002.md` | 同状态分叉、预算匹配、分组划分、闭环验证 | 新Head已有效 |
| P4 | `TRUST_CACHE_MATH_AND_BOUNDARIES_20261002.md` | 刷新收益与误差的区别、观测和理论边界 | 理论已证明实际模型有廉价风险信号 |
| P5 | `AUTONOMOUS_RESEARCH_WORKFLOW_SPEC.md` | 文件记忆、事件驱动、单昂贵任务和审查边界 | 所有自治阶段已在本地验收 |

用户当前提供的研究讨论是本包的目标来源；本包未把此前助手建议当作已发生的实验结果。未找到可确认最新的执行证据，所以所有入口最终需读取现有项目状态。

## 12. 本轮明确未执行

未连接用户GPU执行生成/训练；未修改现有仓库、预算、排队任务或AGENTS；未发邮件；未启动定时任务；未下载大型权重或调用付费评分。完成的是资料核对、研究设计与本地Markdown文档打包。
