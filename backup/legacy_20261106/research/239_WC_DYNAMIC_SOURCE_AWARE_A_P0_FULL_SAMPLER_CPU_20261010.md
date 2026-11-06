# 动态来源选择＋A＋P0：普通完整采样接线

2026-10-10。接续 237/238 的来源感知规则，进入现行多精度设计的实际动态轨迹。新卡不替代原 236 的 288 条固定 P/A CPU，也不改变原 RA＋A 32 条 GPU 卡的范围和确认状态。

## 本轮新增能力

控制器根据当前双 paid probes 和已完成历史选择共同 C/P/D，不再读取预设 P/D 步表。C 执行原 WC 读出，可接既有共享强度 A；P 执行实际 gather→缩小 MLP GEMM→scatter，再进入原 RF/UniPC 更新；D 更新真实校准锚点。保护 warmup/new cycle 仍来自原执行器。

只有两个分支完成才提交控制器和来源。P 创建 floor、工作创建步、dense anchor、区间累积分数与连续 P 次数纳入独立额外状态恢复。第35步原缓存周期清理不伪装成 D；下一步36由原保护逻辑执行实际 D，再建立新周期。

独立参照在同一动态策略下执行完整 GEMM 后替换非活跃投影，另独立重建轮换 mask；记录真实完整 Linear 行数，不能把参照冒充部分计算。原 RA 参考使用冻结 `JointCDController/JointPolicyPairExecutor`，新关闭 P 策略须与它整条轨迹一致。A OFF 须与无 A 的 CPD 完全一致。

## 完整新卡范围

四 Toy 请求 AV28/Human/misc/AV51，flow OFF/ON。每个请求八条完整36步路径：SOURCE_RA、DYNAMIC_NO_P、CPD、REF_CPD、A_CPD_OFF、A_CPD_W1_ONE_PHASE、A_CPD_BETA1_ONE_PHASE、DENSE_CONTROL。

每 flow 成功32条，另同样32条末写出故障控制；两 flow 共128条完整路径，4608 UniPC 更新、9216正常 net 调用。成功64文件，2304 guided＋64 latent＝2368张量独立重读。每成功路径在12/30/35/36恢复实际物理与额外状态，共512次恢复；原 RA/no-P、CPD/A OFF 各八整轨迹严格参照，另八部分/完整GEMM参照。

CPU 校准、P floor/漂移系数和动作成本全部显式 SYNTHETIC，只验证动态计算与恢复能力。本轮不生成生产 P 校准参数，不以 Toy 耗时或 mock mp4 声称视频质量/真实加速。原18方法固定卡已有其独立完整分母，新卡八方法是新增动态问题的完整范围，绝不将旧卡缩成八方法。

## 控制与接续

核对实际 Linear 行数、C 不执行深层、P 非零创建风险且不改 dense anchor/不清区间风险、A 真实额外头费用及语义 P 绕过 D 观察。保留两个完整末写出故障、所有请求和全部方法；对丢方法、改 P 来源/风险、删恢复、改头费用、改强度、伪造 Linear 等作拒绝检查。

先等待原 236 独立终态验收，再将新载荷同步到独立 CPU stage；不得修改原在途 stage。随后实际质量/成本单位校准与完整视频另登记，单次≤4 GPUh自主、严格>4 GPUh需具体确认。预算不因本 CPU 卡重设或扣费，原新增48窗口保持。

本轮已核对原真实 P0 runner 的八父路径：16个 OFF/ON 对照起点都有两 paid-probe 字段，其中八个 COLLECT teacher 起点可与旧同状态 guided moments 对齐。只做完整 schema/源哈希核对，未读它们来拟合 floor 或选策略。下一轮先登记离线单位映射，再决定缺哪些真实测量；不为已有的创建状态记录重复生成。该资产仍未提供 P 来源的未来年龄误差或 clean 动作成本。[资产核对](../reports/wc_source_aware_existing_paid_probe_availability_cpu_20261010.json)
