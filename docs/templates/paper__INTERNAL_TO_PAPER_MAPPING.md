# CARA-Cache 术语与实现映射

此页解释论文名词、代码标识与实验身份。规范身份来自[机器映射](repo:paper/internal_to_paper_mapping.json)；运行状态统一看[当前状态](repo:research/02_CURRENT_STATE.md)。历史名字不会改写代码、配置、原始回执或已部署目录。

## 核心动作

{{actions}}

C包含原WorldCache的probe/window/warp/head/RF读出，并非单纯复制旧速度。A在post-RF分支速度上修正，共享alpha后做CFG融合；语义C/A都可能显示为物理CC。D对两CFG支做完整深层计算，更新真实D历史，但不会抹掉已有轨迹误差。WorldCache自己的决策可能出现DC/CD。

旧P/P0是指定层的部分MLP刷新，仍支付相应attention/gate；新Pc/Pu是单CFG支补偿读出，二者不是同一动作。Pc/Pu不更新working/true-D来源。CPA的“precision”指近似保真度，不指低比特量化。

## 名词与稳定标识

{{mapping_table}}

## 身份与统计规则

检索方法必须同时给出实验命名空间、内部ID、配置SHA、参数/来源规则及源码版本。旧归一化H1/H2、TABLE_PHASE_H1/H1_MID和新生成器不能只凭“H1”名称合并；Efficient与High-Fidelity是历史冻结工作点，B1/B2仍是候选身份。

- LPIPS越低表示更接近同输入Native，不直接等于语义或物理质量。
- 百分比使用同批场景均值之比；prompt为统计分组，帧数不是独立样本量。
- 各批次与方法版本分别报告；缺失、拒绝不填零，配对队列明确分母。
- 主延迟包含驻留模型下文本编码、去噪、VAE及实际维护/读出/刷新；完整实验GPUh另含加载、失败和后处理。

映射JSON中的旧公式数值、evidence_batches和file_bindings均是对应版本的记录。当前自动生成器流程见[计划](repo:plans/cara_policy_generator_20261020/README.md)，全部旧术语说明见[归档](repo:docs/archive/README.md)。
