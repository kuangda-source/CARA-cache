# A＋P0 完整 CPU 验收与动态来源选择接续

2026-10-10。**显式 A＋P0 的普通采样、来源管理、真实 head 计数和恢复链路已经通过完整 CPU 验收。** 下一步进入 [239 动态来源选择](239_WC_DYNAMIC_SOURCE_AWARE_A_P0_FULL_SAMPLER_CPU_20261010.md)，不再只在预设 P 位置上执行组合。

原 source `bc0ad2499dcb68c106557a53fee6e23496643e59`、232 载荷、两个 flow、四 Toy 请求、18 方法/控制，全部保留。原监督/子 PID 3919183/3919184 均消失，exit0，CPU2953.913617秒；独立捕获实际源和输出通过：

| 验证对象 | 完整结果 |
|---|---:|
| 成功完整路径／完整末写出故障路径 | 144／144，共288×36 |
| UniPC 更新／正常 net 调用 | 10368／20736 |
| 成功张量独立重读 | 5328 |
| 完整 GEMM 后替换的部分轨迹参照 | 32 |
| 物理＋额外状态扰动恢复 | 576 |
| 变异拒绝／实际文件截断／末写出故障 | 22／2／2 |
| P 来源继续 C／连续 P 检查 | 720／400 |
| A 成功路径／实际原 head／额外 head | 40／2880／896 |

A OFF 与 P0 整条输出相同；P 不进入旧 A 的 D 观察，C 修正读取同一组过去实际 D 校准。原 R1 漏依赖、0生成失败保留，R2 完整范围并未缩减。

这证明的是 Toy 权重/attention/prepare/decode/writer 下，实际 pinned Block、WC/RF、普通 UniPC 和 guarded pipeline 的组合能力。没有加载真实 Cosmos 权重，没有新方法视频质量或真实加速结论，CPU896额外 head也不是GPU计时。

新动态卡已绑定249载荷：四请求×八动态方法/控制×两flow成功64，另完整故障64，共128×36；2304 guided＋64 latent＝2368成功张量，512物理/额外恢复，以及原RA/no-P、A OFF、部分/完整GEMM整轨迹参照。真实完整旧288卡已验收，新128卡回答新增动态问题，不替代旧卡。

已发现旧真实 P0 父轨迹保存八个 teacher 起点的双 paid probes，后续先登记离线创建误差单位映射；未拟合数值，不为已有记录重复生成。clean动作成本和P来源未来年龄误差仍需实际测量。

预算仍34.372880296/77.895246590 GPUh，新增48窗口余43.522366294。本轮GPU0；完整单次≤4GPUh自主、严格>4GPUh具体确认。原RA＋A完整5.147707517GPUh确认未到、未选GPU，不拆卡，无非必要人评。

证据：[原完整独立捕获](../reports/wc_a_p0_sampling_cpu_r2_terminal_20261010_capture.json)、[完整结果汇总](../reports/wc_a_p0_sampling_cpu_r2_complete_result_summary_20261010.json)、[新动态登记](../manifests/wc_source_aware_sampling_cpu_r1_preregistration_20261010.json)、[已有 paid-probe 资产](../reports/wc_source_aware_existing_paid_probe_availability_cpu_20261010.json)。
