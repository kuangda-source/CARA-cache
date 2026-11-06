# 744：A32 GPU完整接受、唯一结算，释放后CPU评分中

00:47原定半程检查发现原A32已于2026-10-29 **00:33:01** 正常结束，完整32/32：6预热、12三臂数值控制、2干净Native锚点、12有限FIT校准。原容器退出0、无OOM，guardian/容器CLI/supervisor/runner全部退出，GPU锁与模式owner锁释放，Default恢复。[半程原句柄捕获](../reports/cara_fast_A6000_halfway_capture_20261029_0047.json)。没有重派GPU或启动B36。

## 原技术接受与实际费用

[原终态捕获](../reports/cara_fast_A6000_terminal_20261029_0050.json)读取并核对3,718,544,806字节原视频/张量工件，登记源与runtime字节完整。原完整三臂门、实际参数、角色与更新数、干净计时计数、独占与释放链通过。3559份原独占观测完整，最大间隔4.715004秒，最高88°C，未触发90°C热保护；原exact runner上下文、无MPS/外来计算上下文、最终释放均接受。[独立预核验](../reports/cara_fast_A6000_terminal_precheck_20261029_0051.json)。这接受的是该卡GPU技术范围，不是F19收益或新输入结论。

实际原wall bill为**8120.5398196922615秒 / 2.2557055054700728 GPUh**。[中央唯一结算](../reports/cara_fast_A6000_central_settlement_20261029_0052.json)在four_card运行原受测validator完成，cap226、原16.5未知责任与所有其他jobs保持；used178.06156527233628、reserved16.5、available31.43843472766372。两卡旧副本未写费用，没有第二次job。[结算执行身份](../reports/cara_fast_A6000_central_settlement_execution_20261029_0052.json)。工程报价与硬限是预算，不据本次整卡账单推断某方法加速。

[技术/释放/费用完整接受](../reports/cara_fast_A6000_release_accepted_20261029_0053.json)已通过。原A32三臂门通过后，才允许后续有限基线校准；目前尚无已接受的12对真实评分，也未冻结实际基线。

## 释放后CPU评分

从原完整接受链派生[恰好12个FIT配对](../reports/cara_fast_A6000_score_manifest_20261029_0053.json)，只引用两个新干净Native锚点；不访问CHECK或保护输入、不扩阈值网格。[原CPU单次启动](../reports/cara_fast_A6000_CPU_score_launch_20261029_0056.json)于**00:55:16** 开始，容器 `cara-fast-cal-a32-a6000-r2-20261028-A-score-cpu`，manifest SHA `7937a4895626d1555864bf30b78b3ee33f345e870ed53e84af93f3be2d33c767`。2CPU/8GiB、cores26,27、禁swap、无网、root及原source/产物只读，只有评分目录可写，最多2小时，无GPU可见性。

评分worker/度量实现与原R15 CPU接受源码逐字节一致，使用原Alex与PIQ协议。外层单次调度器只增加原件完整接受、原manifest、资源和唯一intent/launch的约束；存在原receipt时恢复它，不重新评分。00:58捕获为 `FAST_A32_SCORE_LIVE_OPERATIONAL_ONLY`，不返回部分分数。实际基线须待CPU容器正常退出、12/12完整帧/曲线/汇总与原源码/cgroup接受后，再由原冻结规则一次选出；没有自动B36。

## 检查安排

一次半程自动化`a32`已完成并删除。原03:15检查`a32-2`已更新为原CPU评分与冻结验收，保留原manifest/settlement/launch与新CPU容器身份，不再等待已经结束的GPU。后续必须复用本次中央结算文件，不能把一次幂等重结算生成的新快照替换到manifest绑定链中。所有历史60行科学记录保持；只有完整评分接受后才解释校准结果。
