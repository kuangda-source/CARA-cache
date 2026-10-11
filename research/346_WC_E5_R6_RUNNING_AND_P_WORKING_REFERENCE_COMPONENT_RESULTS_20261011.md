# E5 完整 CPU 继续与 P 工作参考组件结果（2026-10-11）

**已将完整来源年龄发现落实为一个可检验的近似候选，并完成其数学与来源保护的 CPU 组件验证。** 它计算 `r_P + beta_D*(p_current-p_P)`，当前只接受实际 P 来源的分支／请求／出生步元数据以及合法 prewarp 几何；beta 取真实 D 统计的同一裁剪公式。`unit` 是 beta=1 强对照，不增加拟合或教师信息。

原 R1 小型测试的 unit 合成例子碰巧与 D 参考公式相同，区分断言失败，原退出1／2.215284秒、源码、log与账本不变结果保留。R2 **只改合成 P residual 偏移**，候选源码 0a0ed115 不改，旧结果不覆写。实际 2fb05a3／CPU supervisor 4100194 退出0、2.138206秒，七绑定文件前后 hash 保持。scalar 与 unit 均符合预注册公式且与该合成 D 参考区分；七 fallback（未来P、错分支、异请求、P当零风险、错几何、缺P、不足D拟合）和异请求真D拒绝全部通过，完整真D状态／RNG保持，不访问模型、head、teacher、CUDA或权重，也不写预算。

这仅是**数学和来源保护组件**，尚未确认传入张量来自实际生产 P cache 的正确 prewarp 坐标，也没有执行 Flow Warp、同状态双分支读出、完整 physical／owned 恢复或终点视频。下一步依照 [335](335_WC_E4C_FIRST_FIXED_WINDOW_TENSOR_FINDING_AND_A_TARGET_ALIGNMENT_20261011.md) 与 [345](345_WC_E4C_COMPLETE_SOURCE_AGE_RESULTS_AND_E5_POLICY_RECEIPT_REPAIR_20261011.md) 接受两 flow、D／P、旧／工作参考／unit、fallback、D统计不变及完整恢复后，才冻结全部固定点教师比较的实际 GPU 卡。新方法不改旧 E4c 或冻结 E2／E3 的策略，不直接放宽 C 阈值。

## E5 原新完整范围正在实际运行

R6 source **ac0282350a2c807f321fde070cb8541e921d7f47**，原 CPU supervisor **4099331**／sampler **4099333**，独立 stage `.sync/wc-e5-complete-sampling-cpu-r6-20261011`。Unix1791689261.597 实查两 PID 存活，434绑定文件未改，已写 flow OFF／固定族五条路径；完整 24／444比较／888张量／96恢复未验收。新旧语义 policy 只规范化跨对象的 `decision.owner`，同时检查各路径 owner稳定、正整数、step／action合法，其余所有字段严格相等；R4数值／head与原生 Meta source/result精确保持，旧R1–R5失败保留。准备好的终态只读入口为 `scripts/capture_wc_e5_complete_sampling_cpu_r6.py`，不重复提交 sampler。

完整 CPU 与原件独立等价通过后，才继续 E5 真实全24范围的实际接线／生产CPU／GPU选择。whole cost提案 **5.126846282 GPUh** 位于本轮≤8授权范围，但仍非GPU ready、实测省时或最终质量—时间前沿。原 head控制 OFF与两个修正模式、完整24路径、顺序重复和四次加载均保留，不为适配预算改矩阵。

## 科学结果与预算保持

E4c 四完整父、16短分支、24教师点全范围已验收，四视频全93帧，原件与12对全重建见345。Human早期 age4的 P/D 局部误差 **8.4598** 是值得修读出目标的信号，不否定P／稀疏整体方向，不等同终点质量退化。

实账累计 **41.908688946／77.895246590 GPUh**，新48剩 **35.986557644 GPUh**，78次提交、无登记GPU在途；现场指定A6000为24MiB、0利用率、无compute app。CPU全部为零GPU提交，不改远端账本。本轮≤8完整卡自主、严格>8整卡具体确认；E2／E3原问题仍待，不拆卡、不重问、不引入训练或人工评审，goal active。

证据：[组件R2结果](../reports/wc_p_working_reference_component_cpu_r2_20261011.json)，[组件R1旧失败](../reports/wc_p_working_reference_component_cpu_r1_20261011.json)，[R6原launch](../reports/wc_e5_complete_sampling_cpu_r6_launch_20261011.json)，[最新活状态](../reports/wc_e5_complete_sampling_cpu_r6_live_20261011.json)。
