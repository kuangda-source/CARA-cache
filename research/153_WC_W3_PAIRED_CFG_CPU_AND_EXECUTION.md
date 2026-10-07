# H-T38 同状态联合CFG区分：接口、CPU与后续执行

2026-10-08，依据[152条件分析及信号可用性更正](152_WC_W3_D46_EXISTING_CONDITION_CPU_RESULTS.md)，继续有限W3区分。新[设计](../plans/WORLD_CACHE_PAIRED_CFG_REFRESH_20261008.md)和[登记](../manifests/wc_w3_paired_cfg_preregistration_20261008.json)在新实验前冻结：seed2、step23，原C/C、单槽C/D和联合D/D；1新WC父、8完整后缀、5新视频、1旧匹配Native、两主要signed比较。原正负例、no-op、失败和费用均保留。

## 新接口已经写好，实际CPU尚待

[动作接口](../src/wcomr/rv0_paired_cfg_actions.py)复用已验证OneActionRouter的原forward AST、同CFG真实历史/有限性/付费probe/年龄检查，只允许step23的OFF、D46或D45+D46；当前调用之外使用各自原生自适应。旧OneAction和D46源未改。

[完整核心](../src/wcomr/rv0_paired_cfg_causal.py)在step22/call44共享完整快照，原完整采样loop复用；三臂的call45和46模型输入一致，联合D45之后pre46缓存状态可合法变化。[审计](../src/wcomr/rv0_paired_cfg_evaluation.py)验证四组严格重复、前状态/输入、两动作实际deep执行、原策略后缀、70reset和71/72D、完整终态组件、5新编码和历史BASE/SINGLE字节桥。不把双动作报单动作RV标签。

[CPU夹具](../tests/check_rv0_paired_cfg_cpu.py)将使用冻结真实sampler/WorldCache AST和Video2World条件类、CPU Toy模型，执行四个成功父/32后缀/20mock，覆盖当前原C/C和D/D no-op；第二次动作失败、联合分支writer/guardrail失败均需恢复原完整状态和方法。18类双重复证据破坏及历史bridge破坏都要被拒绝。模拟输出不是真视频或GPU可行性证明。

[CPU载荷清单](../manifests/wc_w3_paired_cfg_core_cpu_r1_20261008.json)绑定7项新载荷和已完成D46 R3的233项有效合并源载荷；独立CPU目录，只在现有SSH上传并执行CPU。此段记录首次准备状态，实际CPU结果见下。

完整保守预测1.660984884GPUh，≤2且在余2.872700413h内，按用户自主约定。累计21.127299587/24h、58jobs/noinflight保持。实际受影响CPU、生产缓存/完整延迟依赖/source/assets、绑定配置和fresh资源/锁/费用准入通过后才能唯一提交；不重启D46旧身份、不删控制或恢复旧秒数deadline。

## 核心实际CPU及独立原件审计通过

冻结source `4565685d92e6611cf296b94dc98fa03825471b1f`，独立目录 `.sync/wc-w3-paired-cfg-core-cpu-r1-20261008`。服务器实际夹具209.409041秒，监督全CPU耗时212.026552秒，exit0、CUDA未初始化、GPU提交0；原supervisor3283484/child3283485已确认退出。

四个成功父轨迹、32条完整后缀、20个模拟输出以及每父四组严格重复全部通过。原C/C下分别实际形成C/C、C/D和D/D，联合操作合法改变pre46缓存；原D/D下保持no-op。第二次动作、writer和guardrail故障均恢复完整父状态与方法。独立读取原始记录重建76次证据破坏拒绝，没有仅依赖汇总标签。

7项新载荷及233项继承载荷，在原目录、独立复制目录和执行前后SHA均一致；六份压缩原字节、退出句柄和费用也已验收。根账本SHA保持，累计21.127299587/24GPUh、58jobs、无在途，余额2.872700413h。见[终态原件捕获](../reports/wc_w3_paired_cfg_core_cpu_r1_20261008_terminal_capture.json)、[独立原始重建](../reports/wc_w3_paired_cfg_core_cpu_r1_independent_audit_20261008.json)和[实际启动身份](../reports/wc_w3_paired_cfg_core_cpu_r1_launch_20261008.json)。

本结果证明冻结真实sampler/WorldCache AST在CPU Toy上可以执行和恢复；不证明真实权重、GPU可行性、历史真实视频桥或终点质量。下一步继续生产入口、源码资产/延迟导入、监督与评分绑定的必要CPU验收，再进行fresh GPU/锁/预算准入。已完成核心CPU身份消耗，不重跑、不改通过核心。
