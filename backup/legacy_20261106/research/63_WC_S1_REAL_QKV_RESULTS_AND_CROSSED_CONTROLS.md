# S1真实 QKV：默认策略不具备稳定净收益，补交叉阈值控制

2026-10-01，real-qkv-r1/source `cab2b7c`，A6000、全部12输入×6臂=72case，1warmup/3repeat，no-PV；[原范围](62_WC_S1_REAL_QKV_ROUTING_GATE.md)、[终态](../reports/wc_s1_real_qkv_r1_terminal_20261001.json)、[独立审计](../reports/wc_s1_real_qkv_r1_fresh_audit_20261001.json)、[全部输入结果](../reports/wc_s1_real_qkv_r1_summary_20261001.json)。

## 结果与边界

全部72输出finite、BF16/正确形状、actual Flash SDPA reference与3repeat完整。vanilla全mask及两组routed-full共36控制，最大relative RMSE 0.00752739（0.753%），全部通过预登记5%技术筛查；量化全块与matched-full误差很小，激进mask误差不能主要归于这个混杂。

| 现有策略 | 中位块保留率 | 中位dense/稀疏wall | 最大相对dense RMSE | 数值筛查 | 至少1.1×净速度 | 同时通过 |
|---|---:|---:|---:|---:|---:|---:|
| public默认 sim0.6/cdf0.98 | 94.553% | 1.01852× | 1.349% | 12/12 | 1/12 | 1/12 |
| utils默认 sim0.1/cdf0.9 | 37.319% | 2.13874× | 24.040% | 2/12 | 12/12 | 2/12 |

public有两个early layer14输入回退到100%块执行，甚至比dense慢；稀疏组最高1.138×，其余多数增益很小。utils有1.619–4.071×实际净速度，但10个输入超过5%误差；late layer27仅保留约12.9%、RMSE约23.9–24.0%，与matched-full误差也相近。utils的两个数值通过输入恰是late layer2（调用71/72），误差约3.92%、速度约2.13×，不据这两个挑选结果解锁全模型部署。

同步操作wall已计routing、validation、packing、quant、LUT、stats与输出检查；不能把matched routed-full/sparse比值当当前dense基线收益。三个热repeat不是稳定吞吐确认，单场景/seed与四CFG调用不是跨场景/闭环质量证据。full控制的5%容差不等于视频质量可接受，12/12低误差也不是原创方法验收。

原三PIDs2558878/2558895/2558897与CPU PID2558737退出/global锁与GPU释放，10payload/8package/12文件/dense与S0 attestation hash不变、所有72原始3repeat中位数/覆盖独立核对。GPU监督墙钟62.910135268699秒，180秒返还117.089865秒；累计3.8958064096647362/4GPUh、27jobs、余375.096925秒，无inflight/扩额/人评。

## 下一有界交叉控制

不能将默认两策略差异直接归于某一个参数：它们同时改变了sim和cdf。补两非对角组合 **sim0.1/cdf0.98** 与 **sim0.6/cdf0.9**，完成既有2×2因子控制，区分“相似性fallback保留过多”和“低CDF丢失重要块”。不增加模型/输入/训练，不做额外阈值网格搜索或按最佳输入报告。

[冻结crossed配置](../configs/wc_s1_crossed_qkv.json)沿用相同12输入/6臂/1warmup+3repeat/每策略matched-full与无PV；新任务内重测dense/vanilla控制，跨job测速变化不能伪装参数效应。最多120秒（child110秒/5秒kill/15秒余额余量）从现有375秒划拨。未知policy_set、参数/arm/cap/重复变化均拒绝；新scope与预算本地3控制通过，实际环境门与GPU尚未提交。

若交叉控制仍无稳定净收益，保留真实硬件可行、量化误差小、瓶颈47.37%这些事实，暂停简单叠加，下一判断低开销误差控制/有条件刷新是否值得开发。不能据稀疏率或最快case宣称保质加速/论文，不能直接跳到自由三档/四臂昂贵生成。
