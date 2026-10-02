# WC-S0：官方缓存剩余成本与12组真实 QKV 已审计

2026-10-01，R3/source `fb43d93`，A6000 sm86，官方 Cosmos2B/WC，固定 CAL8 第一场景 seed0。[冻结范围与两次保留失败](60_WC_S0_PROFILE_REAL_QKV.md)、[终态](../reports/wc_s0_profile_r3_terminal_20261001.json)、[独立审计](../reports/wc_s0_profile_r3_fresh_audit_20261001.json)、[成本重算](../reports/wc_s0_profile_r3_summary_20261001.json)、[7438条原始事件](../reports/wc_s0_profile_r3_raw_events_20261001.json)。

## 成本结论：先深层 self-attention，模块删减不是主要加速来源

profile-only 轮端到端208.541671秒，去噪同步wall141.264395秒。72 CFG调用中，34次执行全部深层、38次复用深层；每个深层核心调用884次，每个probe组件144次，逐行事件/调用覆盖已独立重算。保持官方flow/saliency/OSI/dynamic-decay、eager/offload/guardrails与已验收decode policy。

| 组件 | CUDA-event总秒 | 相对去噪同步wall |
|---|---:|---:|
| deep self-attention核心（层2..27） | 66.915474 | 47.369% |
| probe self-attention核心（层0/1） | 10.752441 | 7.612% |
| deep MLP | 16.432873 | 11.633% |
| probe MLP | 2.658658 | 1.882% |
| self Q/K/V/output projections，全部层 | 9.303067 | 6.586% |
| cross-attention核心，全部层 | 1.345065 | 0.952% |
| optical flow | 1.835296 | 1.299% |
| warp，76次调用 | 1.336626 | 0.946% |
| saliency，56次调用 | 0.193782 | 0.137% |

net inclusive总129.478553秒包含这些子项，不重复求和；未测部分包括norm/门控/其他投影、缓存决策与CPU/launch等待等。CUDA-event区间也包含launch间隙，表格不能当纯device-active kernel trace或clean吞吐复现。

单个已消费开发场景的结果支持下一步集中 **deep self-attention块选择**。cross核心占比不足1%，暂不投入多模态注意力架构重写；cross投影/norm未完全细分，因此不称整个多模态路径只占1%。光流+所有warp合计约2.25%，即使零成本移除也不是主要上限，而且质量作用尚未验证。`warped_state`死计算仍可作小范围等价优化候选，不把删它当论文主贡献；76次warp合计不是被确认可删那38次的精确成本。

假定deep self核心被零成本、零误差完全消除，去噪Amdahl上限约1.900019×；这是理想上限，实际路由、packing、量化/误差、保留块与端到端其他阶段会压低收益。不能将S1合成QKV加速比乘WC加速比或宣称当前取得这个收益。

## 实际模型接口与观察一致性

模型实际绑定28层、16heads、D128、`minimal_a2a`/`MinimalA2AAttnOp`。capture-only轮调用1/2/71/72×层2/14/27共12个QKV，在真实attn_op入口、Q/K norm与self RoPE之后采集。全部是BF16 `[1,31104,16,128]`，NHD stride `[63700992,2048,128,1]`，finite；每个文件/原tensor字节SHA、CPU roundtrip均独立重验，CFG slot来自当时实际cache counter，采集均处于执行深层的full调用。

12个文件总4,586,498,352字节，bulk保留在服务器ignored `.sync/wc-s0-profile-r3/gpu-r3/diagnostic/capture/`，Git只有元数据。capture端到端244.368441秒，包含copy/hash/IO；不能与profile轮做加速或回归比较。

两轮原sampling（35请求/36实际步/72CFG/horizon70）、34/38调用数、全部执行trace、最终latent witness/outcome完全一致，两份通过官方guardrail保存的视频文件SHA也一致。观察器不替换输出/输入，不更新cache决策，不调用shadow，不改RNG。只读一致性不是视频质量金标准，两轮都是官方WC，未运行稀疏生成臂或新方法视频质量评估。

## 预算与接续

成功R3监督墙钟611.180966879707秒，预约750秒返还138.819033秒；原PIDs2555212/2555227/2555229、CPU检查PIDs2555018/2555031均退出，global锁/GPU已释放，部署/source/checkpoint/SHA与原始事件/12文件通过独立审计。

R1路径错误69.455334秒、R2缓存错误125.141735秒同样保留并计账；该S0工作共805.778036秒。账本精确3.8783313720900976/4GPUh，26次job、无inflight、余438.007060秒（约7.30分钟）。不扩额、不训练/付费评价/默认人评。

下一仍可在既有余额内准备 **最多180秒真实QKV kernel门**：当前dense、匹配no-PV全块、数据驱动块选择，记录实际保留率/数值误差/路由及packing净成本；保留全12输入，不按好结果挑层/调用。采用已有上游选择策略先排除技术问题，不把组合现成模块当已证新颖贡献。第一轮固定band的合成输入大误差依旧不能接入生成。

在真实QKV数值与净成本通过前，不解锁四臂闭环/自由三档控制。后续完整质量—时间验证若超出原余额，重新提出具体scope与成本，不自动执行原clean50或新4GPUh提案。继续WorldCache的依据是已测瓶颈和可执行内核；尚没有新方法正质量—时间结果，不据此切换研究方向或承诺论文。
