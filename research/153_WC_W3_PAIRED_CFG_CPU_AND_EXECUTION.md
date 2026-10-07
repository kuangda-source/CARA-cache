# H-T38 同状态联合CFG区分：接口、CPU与后续执行

2026-10-08，依据[152条件分析及信号可用性更正](152_WC_W3_D46_EXISTING_CONDITION_CPU_RESULTS.md)，继续有限W3区分。新[设计](../plans/WORLD_CACHE_PAIRED_CFG_REFRESH_20261008.md)和[登记](../manifests/wc_w3_paired_cfg_preregistration_20261008.json)在新实验前冻结：seed2、step23，原C/C、单槽C/D和联合D/D；1新WC父、8完整后缀、5新视频、1旧匹配Native、两主要signed比较。原正负例、no-op、失败和费用均保留。

## 新接口已经写好，实际CPU尚待

[动作接口](../src/wcomr/rv0_paired_cfg_actions.py)复用已验证OneActionRouter的原forward AST、同CFG真实历史/有限性/付费probe/年龄检查，只允许step23的OFF、D46或D45+D46；当前调用之外使用各自原生自适应。旧OneAction和D46源未改。

[完整核心](../src/wcomr/rv0_paired_cfg_causal.py)在step22/call44共享完整快照，原完整采样loop复用；三臂的call45和46模型输入一致，联合D45之后pre46缓存状态可合法变化。[审计](../src/wcomr/rv0_paired_cfg_evaluation.py)验证四组严格重复、前状态/输入、两动作实际deep执行、原策略后缀、70reset和71/72D、完整终态组件、5新编码和历史BASE/SINGLE字节桥。不把双动作报单动作RV标签。

[CPU夹具](../tests/check_rv0_paired_cfg_cpu.py)将使用冻结真实sampler/WorldCache AST和Video2World条件类、CPU Toy模型，执行四个成功父/32后缀/20mock，覆盖当前原C/C和D/D no-op；第二次动作失败、联合分支writer/guardrail失败均需恢复原完整状态和方法。18类双重复证据破坏及历史bridge破坏都要被拒绝。模拟输出不是真视频或GPU可行性证明。

[CPU载荷清单](../manifests/wc_w3_paired_cfg_core_cpu_r1_20261008.json)绑定7项新载荷和已完成D46 R3的232项有效合并源载荷（实际文件数以清单为准）；独立CPU目录，只在现有SSH上传并执行CPU。当前仅语法和源码准备通过，实际CPU、新生产入口和GPU提交均未完成。

完整保守预测1.660984884GPUh，≤2且在余2.872700413h内，按用户自主约定。累计21.127299587/24h、58jobs/noinflight保持。实际受影响CPU、生产缓存/完整延迟依赖/source/assets、绑定配置和fresh资源/锁/费用准入通过后才能唯一提交；不重启D46旧身份、不删控制或恢复旧秒数deadline。
