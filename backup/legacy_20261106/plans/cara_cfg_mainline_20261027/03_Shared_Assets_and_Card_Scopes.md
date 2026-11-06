# 公共资产、实验卡和去重规则

## 1. 三层资产，不再默认“已有1624就什么都有”

| 资产 | 已知用途 | 不足 |
|---|---|---|
| B1：2旧CAL×6状态、两支p/r与teacher／输出、720诊断 | CFG矩校验、codec原型、局部rank分析；原Shared25父轨迹 | 不覆盖全36步；只两个已曝光prompt；不是任意solver恢复点 |
| 1624：全D父轨迹、相邻来源、guided统计 | 原条件下C/A二次量、时间支持和兼容性 | 无法从guided统计反推两支协方差；非真实稀疏history |
| 725：73槽公平基线与双计时准备 | 相同科学角色可共用完整视频参考、硬件与时钟 | 未执行，不能先用作已测标签；不静默追加shadow或改变scope |
| 726：新状态R4_COMMON_LONG准备 | 已接受的collector/隔离/双端组件可按未变SHA复用 | 原6父路径方案身份保留；不拿本轮公共卡冒名执行它 |

先列字段/来源/哈希清单，只有缺口明确才报价。所有raw大张量留在原数据位置，Git只记录manifest。

## 2. 拟议公共卡 A-CFG：一次采集服务两条线

**仅在旧资产不足以生成可辨识CFG计划时启用。**

- 训练prompt：原AV28、Human199，seed0，不用DEV128或最终组。
- 两条固定父策略：S25-C、Shared25-C。每条都按自身状态自由运行。
- 目标t为8..35中排除原保护24的27个位置；两prompt×两父=4条采集路径，108个同状态评分位置。
- 父动作D：实际D作为teacher，计算不写回的C shadow。
- 父动作C：保存实际C，只额外执行同状态双支D teacher，不提交其cache/solver/RNG更新。每条25D父有11C，因此最多44个额外Dense pairs；不是108个额外Dense。
- 每点只保留C/U/K、q_g、实际sigma、两真D时间/来源、g身份、状态和动作计数等小统计；不保存108份全部feature。
- 压缩向量仅在Shared父的预登记状态{9,22,33,35}保存：2prompt×4=8个当前状态；完整两分支r/p、两真锚点、原C/D输出及真实readout恢复字段。精确重复的旧B1状态按身份复用，不算新样本。锚点去重保存，raw存储上限在报价时按真实dtype/字段计算，不凭“8状态”假定很小。
- CPU验证parent OFF/ON、候选彼此隔离和shadow不改变父输出。完整计划上限：4采集+4 OFF控制+2 warm=10父路径，外加上述44shadow Dense pairs与108 C shadow/readout（实际C位置可复用已算输出，仍记录实际计数）。
- 此卡含研究取证，T_DD/T_request只标诊断，不能用于部署速度。

旧状态重放与新状态分开编号。若两个父都有相同prompt/seed，不计四个独立输入，统计单位仍两个prompt。

原726若同时准备，不重复派发两张高度重叠采集：保留原计划为独立历史，先登记哪个新合同承担哪些新增产物，更新完整预算/CPU后执行，不能拆开偷省审批或偷偷追加codec到725。

## 3. 资产字典最低字段

`model_weight_hash, source_revision, dtype, device_backend, prompt_id, seed, initial_noise_hash, parent_policy_hash, sigma_grid_hash, step, branch_order, cfg_coefficients, true_anchor_steps, cache_source_kind, original/probe/residual, cache_window_state, readout_inputs, teacher_branch_outputs, C_branch_outputs, output_coordinate, source_file_hashes`。

分支矩须保存每元素平均与张量元素数；FP64统计仅降低归约误差，不能把全量FP32运算称逐位等价。branch identity要求conditional/negative-prompt，不按名字猜u=真正无条件。

不自动承诺可续推solver：保存readout输入与完整采样checkpoint是两个级别。需要后缀干预时必须新增明确checkpoint合同，否则重跑完整前缀。

## 4. 去重和计费

用请求/模型/solver/初始噪声/父布局/分支/step/来源窗口/读出版本/codec版本/硬件/时钟边界构成唯一身份。

- 相同模型加载可在同一已授权card中共用；本计划不将所有工作强塞进一张巨卡。
- 一个teacher pair服务多个评分，费用只计一次，但比较双方获得同样的校准信息。
- 相同mask与codec只生成一次，保留多个别名；不是多个独立样本。
- 已有视频可复用质量，仅在RGB与Native身份兼容时；不同机器/热状态的时间不可移植。
- 不同父轨迹的局部误差不能拼作同一条真实轨迹。
- CAL/SELECT/DEV/TEST曝光分工保持；现有DEV128是冻结主方法证据，不是新CFG规则的训练集。

## 5. 完整卡规划上界（均未授权）

| 卡 | 核心输出 | 整卡其他项 | GPUh规划 |
|---|---|---|---|
| A-CFG公共标签 | 4采集父，108位置，最多44额外Dense pairs | 4OFF+2warm，写出、释放、CPU分析 | ≤约3目标，按入口报价 |
| S-END调度 | 4角色×4CAL=16视频，等价去重 | 4Native缺格+4warm+4repeat+4控制，最大32 | ≤约3目标，不是硬限 |
| Q1 codec重放 | 旧／公共向量的少数codec，真实C读出 | 端点控制、峰值、打包/解包、模型加载 | ≤约1目标 |
| Q-END压缩视频 | 至多4角色×4CAL=16 | Native/原参考缺格+warm+repeat，单独完整报价 | 后置，不在当前37h内自动占用 |
| 725基线桥接 | 原73槽合同 | 原A/B阶段、两次加载、全部warm/diag/score | 既有9.51/9.97工程预测、12提案 |

正式完整scope以预登记清单而非此处估算生效，新增失败/warm/选参不能藏在“只16视频”。所有角色同一设备的独占运行；双端准备不等于两端重复派发。

## 6. 成功与分流

调度产生新可辨识计划并改善完整结果→主线增强；压缩同bytes更好→独立memory-fidelity贡献；二者均成功才研究联合。任何一条失败不暂停Shared25确认／Q5，也不自动拉起已停IG/F/B/GRAPH。
