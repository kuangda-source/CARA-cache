# M1下一步执行承接

截至研究[828](../../../research/828_CARA_READ_WRITE_ACTUAL_LINUX_AND_FULL14_CPU_ACCEPTANCE_20261101.md)，唯一现行执行设计为[M1_FULL14_EXECUTION_R2.md](M1_FULL14_EXECUTION_R2.md)。方法总框架仍是原读写价值候选；不把它说成已有GPU结果。

## 已退出的CPU原句柄

- 组件R1：`cara-read-write-M0M1-CPU-a6000-r1-20261101-cpu`，exited/1，原失败保留，不重启。
- 组件R2：`cara-read-write-M0M1-CPU-a6000-r2-20261101-cpu`，source `522a5b8c`，exited/0；20控制/8后缀/12完整请求已接受。
- 完整14：`cara-read-write-full14-CPU-a6000-r1-20261101-cpu`，source `e324b161`，exited/0；实际模块和原冻结参数类，28个完整tiny请求已接受。

读取`reports/cara_read_write_Linux_CPU_accepted_r2_20261101.json`及`reports/cara_read_write_collection14_Linux_CPU_accepted_r1_20261101.json`即可复用。旧CPU已终态，不要再运行prepare或为刷新文档重派。GPU尚无本卡intent、launch或预约；这个结论来自本地本轮没有调用GPU派发入口，不替代未来服务端原句柄/中央责任核验。

## 可直接复用的代码

- `cara_read_write_plan_r1.build/validate`：完整14/512原协议。
- `cara_read_write_point_r1.execute`：原完整guarded请求中的同父读写干预；每路径37 paired、36 solver更新；自然形成正确latent/完整UniPC历史，无两完整GPU图同时物化。
- `cara_read_write_collection_r1.Requests/collect`：原不可变请求变体、原时间边界、逐输入准备复用、完整张量/视频工件、禁止重复、实际额外计算、无fallback与14完整分母。它不是GPU资源/预算准入器。
- 原`cara_s_endpoint_host_guardian_r1`、`cara_s_endpoint_supervisor_r1`及`cara_s_endpoint_lifecycle_r1`包含一般性的原句柄、设备模式、硬截止/90°C、释放及实际费用读者，可复用未变核心。

## 尚未完成，继续做

1. 新M1 GPU runner与来源/上下文校验、单次派发入口；旧endpoint7 dispatch/binding硬编码46/7GPUh和搜索复用，不能改常量后直接当M1准入。
2. 独立16GiB输出卷、48MiB跨盘控制journal，CPU2核/40GiB、GPU只给原runner；旧通用fresh_resources有64GiB硬编码，需对本卡补精确16GiB受影响验证。系统盘快照仅约62GiB空闲，不套用旧64GiB资源绑定，不删旧结果。
3. 整卡guardian/唯一结算、完整14释放后的等价控制与八对一次CPU评分的绑定。当前完整请求采集CPU通过，不等于这些接口已通过。
4. 最终完整报价和fresh资产/设备/资源/中央责任核验。预计1.6048、拟硬1.95GPUh，小于2的原自主规则保持；新卡原账本权限须按真实现行授权处理，不复用已完成卡身份。

下一GPU只考虑两卡原UUID `GPU-cebf7119-cf03-23b9-e192-cd196332b704`；没有新卡硬件替换或四卡实验。90°C、600秒停止释放余量、cap226与旧16.5保持。GPU若实际启动，再按实际开始与完整报价安排半程/终验；当前不要创建空监控或评分进程。
