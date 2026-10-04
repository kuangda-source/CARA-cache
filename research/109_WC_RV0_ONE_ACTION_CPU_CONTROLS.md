# W3/RV0单次C/D动作CPU通过，真实刷新收益尚未验证

2026-10-04。承接[108未干预后缀与成本草案](108_WC_RV0_CPU_SUFFIX_CONTROLS_AND_COST.md)和[68反事实刷新设计](68_WC_COUNTERFACTUAL_REFRESH_VALUE_DESIGN.md)。本轮完成当前一次C/D决策接口、原后缀回归、顺序与失败恢复控制及独立原件审计。新增GPU提交、预付、真实RV标签和Head训练均为0；尚未选择下一GPU卡。

## 当前实现的因果问题

[OneActionRouter及OneActionSuffixControl](../src/wcomr/rv0_actions.py)保持官方WorldCache源码不变，从固定源码AST生成独立forward，仅增加调用起点、阈值谓词和分支完成三个hook。在**当前浅层probe已经执行、cache/full分支副作用尚未执行**的位置强制一次C或D：C使用原缓存近似，D继续原deep计算并刷新。累计误差、残差窗口、OSI/warp、resume、head和70周期计数器仍由官方函数处理；不事后伪造skip标志或把C作为true-full锚点。

当前决策单位为一个CFG分支调用。后缀快照位于step22的双CFG完成之后，测试分别干预step23的call45/CFG0与call46/CFG1；后者的CFG0前缀也必须一致。不是每次干预两个CFG分支，也不把72个调用当成36个同成本刷新。

动作之后沿用**同一个原WorldCache自适应策略函数**。动作会改变缓存和轨迹，因此未来full/cache选择可能不同：本接口既不是固定未来动作掩码，也不是预算匹配策略。不输出有符号收益Y，不把C/D终点互距称收益。若后续要采标签，必须另冻结后缀口径、Native参考、主要损失、配额单位和计时范围。

接口只允许下一完整solver步内的一次动作；显式绑定request/model/condition、模型/expert和CFG槽位，单进程eval、WC70、Karras36，拒绝稀疏adapter。C/D配对须同时可行：当前已付probe与原cache有效、两个过去同CFG真实full锚点、warm/tail保护、有限信号、最大age均满足。最大age限制在此用于诊断配对的可行性；不能把它解释为生产中禁止旧缓存处执行D的策略。当前deep真值、未计算attention和未来trace不进入决策。

router的过去真实full时间戳、请求上下文、动作及计数作为独立sidecar随分叉恢复；保存的只是当前进程内状态，仍不支持独立进程重启。基础[SamplerSuffixControl](../src/wcomr/rv0_fork.py)新增eval模式漂移保护及内部动作回调，其原未干预接口本轮重新回归，旧R3原件不追认修改后的源码。

## 实际CPU证据

[实际R1报告](../reports/wc_rv0_actions_cpu_r1_20261004.json)、[独立原件审计](../reports/wc_rv0_actions_cpu_audit_20261004.json)、[测试源](../tests/check_rv0_actions_cpu.py)、[只读审计器](../scripts/audit_wc_rv0_actions_cpu.py)。服务器Torch2.7.1+cu128，CUDA不可见且lazy init被禁止；完整测试耗时**181.728276秒**。33份当前依赖及五份官方源码逐SHA核对，服务器原始回执SHA为 `3e5edc8ec2ae394858723dfe940ca4d6cd607afcdde51e13185e45fb62b4576f`。独立审计不导入Torch、不重跑套件或GPU任务。

| 检查 | 覆盖及结果 |
|---|---|
| 未干预后缀回归 | flow OFF/ON × forced full/cache四组，原父36更新/72CFG和每组四条14更新/28CFG后缀通过；包含原身份、网格、条件、有限性和恢复拒绝门 |
| OFF等价 | 新四组原forward与router OFF的全部72输入/输出/deep/cache、solver、最终latent、RNG、mock产物及状态相等；插入诊断后父轨迹仍相等 |
| C/C、D/D与交换顺序 | 每组两个CFG槽位各OFF/OFF、C→D、D→C，共12条完整后缀；四组合计48条，每条14更新/28CFG；相同行动的全后缀与最终状态相等 |
| 同一当前输入 | C/D输入在目标调用之前及目标处相等；CFG1另验证同一CFG0前缀；目标C执行0个deep block，D执行全部剩余deep block |
| 历史锚点 | 目标D登记step23真实full，C不登记；只读当前已付probe和过去同CFG锚点；与原策略相同的动作复现OFF |
| 拒绝与恢复 | 六种非法计划、缺true-full历史、eval漂移通过；forced cache两组另触发过期age拒绝；失败断言TECH_BLOCKED及父状态恢复，调用方mode/cache/solver/RNG/config/function也恢复 |

报告保存逐组断言摘要和源码绑定；并非每条失败的生产采集记录。本测试没有建立科学标签分母，未来collector仍须显式保留全部候选位置、不可行与技术失败记录。

forced full/cache阈值仅用于CPU分支与恢复控制。网络、embedding/block、条件/noise准备、decoder/writer等为明确Toy替身；没有真实权重、GPU算子、VAE或编码视频。当前通过属于动作和恢复接口证据，**不等于真实模型RV0验收、C/D正收益或等预算调度有效**。

## 快照成本与剩余工作

新增`snapshot_storage()`只遍历已保存的副本，按device和物理storage去重，不额外克隆或转CPU。本轮Toy快照独占CPU tensor storage为24,270,820 bytes（full）或24,270,828 bytes（cache）；逻辑tensor字节分别28,465,148/28,465,156，另有2,496 bytes NumPy RNG。它不包含live权重、Python元数据、router事件字典、瞬时restore副本、算子workspace和峰值分配，不能外推真实GPU显存或耗时。

独立审计再次读取服务器账本：**10.713586944446/12GPUh、44jobs**，无inflight，剩余**1.286413055554h＝4631.087秒**。CPU前后原账本相等。原[104点单次补验](75_WC_FULL104_R4_CARD_AND_RESULTS.md)1153.547616秒已完成，其≤1800秒授权不再复用。

[原成本草案](../reports/wc_rv0_suffix_cost_draft_20261004.json)的3300/4500秒候选仍未选择或准入。动作接口缺口已经缩小，但真实快照/条件恢复/哈希及传输成本、额外峰值显存依然UNKNOWN；两cap不能共同承诺。不能用本轮Toy CPU时间或24MB快照升级为完整GPU成本上界。

下一步先具体化一张诊断卡的真实同路径恢复控制、合法点选择、动作单位、后缀和参考损失；保留原强规则/失败分母，先恢复可信再采收益。在真实开销和内存包络、冻结source、实际部署与fresh资源/余额门通过前，不提交GPU。训练、复杂Head、稀疏三动作与大规模RV采集仍后置。

[107](107_WC_FAIR_CAL_RESULTS_AND_DIRECTION_GATE.md)的科学结论保持：当前稀疏候选未形成可信端到端净收益，W3是下一候选而非已验证替代。既有自主goal继续CPU准备；重要方向节点留待讨论，不引入新人工评审或付费评分。
