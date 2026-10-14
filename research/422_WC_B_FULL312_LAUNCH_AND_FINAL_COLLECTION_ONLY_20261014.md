# B 原完整312卡正在运行；验收后停止新增实验并收束

2026-10-14，北京时间。用户最新要求：**有正在运行的实验，按预计时间验收，不开启新实验；没有正在运行的实验，就按此前总结收束。** 该要求覆盖此前自主续开后续卡的安排。

## 1. 现场状态与下一次查收

本轮在用户这条新要求到达前已按原授权派发独立 B 卡。15:15:32 的一次现场观察确认原 supervisor、runner 与 CPU post watcher 存活，A6000 的实际计算进程为本卡 runner；锁由原任务持有。此后不持续查询进度或读取新增视频。

| 项目 | 原任务身份 |
|---|---|
| 完整卡 | WC-B-SAVED-VELOCITY-FULL312-SUFFIX12-VIDEOS16-R1-20261013-A |
| 派发 / 准入 | 2026-10-14 15:12:17 / 15:13:30 Asia/Shanghai |
| supervisor / runner / CPU post watcher | 710803 / 710917 / 710804 |
| source / payload | 988ace1834af14c4ed535ed7b025c9619fec948e / 730 份 |
| stage | .sync/wc-block-velocity-production-r1-20261013 |
| run | wc-block-saved-velocity-full312-r1 |
| 服务器 / SSH | /home/gaokuangda/data/gkd/worldcache_omr / gkd_minchen |
| GPU UUID | GPU-cebf7119-cf03-23b9-e192-cd196332b704 |
| 下一次查收最早时间 | **2026-10-14 17:45:00 Asia/Shanghai**，unix 1791971100 |

预计 GPU 计算约 1.5–2.25 小时，加 CPU 审计和全帧评分，按约 2–2.5 小时安排一次查收。此估时不是新的秒数终止条件；原单次 8 GPUh 与累计余额限制保持。旧 `worldcache` 成本曲线自动化已暂停，新 `b-worldcache` 仅负责原 B 验收与收束，完成后暂停。提示词还绑定上述绝对时刻，避免提前查收。

[原启动回执](../reports/wc_block_saved_velocity_full312_r1_GPU_launch_20261013.json) · [唯一准入观察](../reports/wc_block_saved_velocity_full312_initial_admission_20261014.json)。回执名中的 20261013 是原卡身份，实际启动为 10 月 14 日。

## 2. 本卡验证什么

保留原四状态：AV28 step21（P、age2）/step27（D、age2），Human step15（P、age2）/step29（D、age2）。每点一个完整父路径与三个完整后缀：C_REPLAY、DENSE_VELOCITY、L2_VELOCITY。总共 **4 父＋12 后缀、16 输出位置、312 pairs／624 CFG、一次模型加载**；不新增 teacher 或 B executor 调用。

三个分支首次都执行实际 C，首次缓存状态相同；只改变第一次返回给求解器的速度，Dense/L2 值来自已经审计的保存原件。后续仍由原 pi0 自然续推。该实验把已有 Block 局部近似误差接到最终视频，检验其后果和阶段条件。

**本卡不能直接证明实际 B 刷新来源寿命、线上闭环或端到端加速。** 后缀计时含取证和恢复，不作为 clean latency。独立 B 仍不合入冻结主线；原约 7.1% 局部算子节时与本卡终点结果分开报告。

## 3. 费用与启动修复

fresh 准入时 GPU 空闲、24 MiB、compute apps 为空；账本前值 **79.19501253167144 / 104.97136333301378 GPUh**，可用 **25.776350801342346 GPUh**。完整 B 预测 **2.236752758178627 GPUh**，规划后余额 **23.53959804316372 GPUh**；这些不是本卡实际结算。运行期间 `used=cap` 是在途预留，验收使用 supervisor 完整 wall 结算，不重置新增 48 GPUh 的起点。

首次启动辅助脚本在派发前因服务器系统 Python 缺少 `Path.is_relative_to` 报错。随后的只读检查确认没有 claim、launch、日志或输出。只将本地辅助脚本的 SSH dispatcher 改为已经验收的生产 Python 3.10.19，九项本地 CPU 控制通过后完成唯一派发；原 server source、730 份 payload、配置和生产代码均未改变。原失败保留，不把它归为算法失败。

[原失败和无派发证明](../reports/wc_block_saved_velocity_pre_dispatch_python_failure_20261014.json) · [九项 CPU 补验](../reports/wc_block_saved_velocity_dispatch_helper_CPU_runtime_r2_20261014.json)。

## 4. 17:45 的验收与终止续开

到时执行一次只读 [capture](../scripts/capture_wc_block_saved_velocity_full312_r1.py)，写入新的 `.json.gz` 回执，不覆盖旧文件。检查原源码与句柄、全部 16 分母、原 4 父／12 后缀、GPU 与 post 退出、所有兼容视频 93 帧评分、实际结算和锁/GPU释放。`runner.runs` 只有四父，不能把四行误判为仅四个输出。

除现有 post 控制，利用完整 capture 本地独立检查 C_REPLAY 是否逐位恢复本父：

```python
replay["guided_sha256"] == parent["guided_sha256"][step - 1:]
replay["final_latent_sha256"] == parent["final_latent_sha256"]
replay["actions"] == parent["actions"][step - 1:]
```

再比较同 index 的 PARENT_PI0 与 C_REPLAY 解码 RGB SHA；不要求有损编码文件 SHA 相同。任何拒绝、失败、缺失保留原位置，不补样本。若原任务未结束，按剩余工作量重新估时，只安排下一次查收并结束当轮；不能循环等待、重启或重投。

**验收后不续开任何新 GPU 卡、F/B 科学实验、训练或人评。** 整理逐状态终点效应、已有主线贡献与待补证据，更新最终收束报告和论文框架；原强基线、少步、共同冻结测试和第二模型等均保留为待讨论建议，不执行。旧 P 大卡暂缓继续保持。

## 5. 主线收束依据保持

[420 原60完整归因](420_WC_FULL60_COST_CURVE_COMPLETE_RESULTS_AND_CONVERGENCE_20261014.md)已接受，不重复查收。原 H1_MID 与固定 A 的四正式终态/动作/RGB 等价，两轮 AV28 预热 144 guided 逐位等价；固定 A 对 plain 平均 LPIPS 低 3.5196%、约多 0.8762 秒，3/4 改善。三 lambda 均 26D/0P，不主张宽连续成本前沿或在线内容自适应增量。

[421 收束决定](421_WC_PAPER_CONVERGENCE_TASKS_AND_MAIN_TEXT_FRAMEWORK_20261014.md)、[收尾设计](../plans/WORLD_CACHE_PAPER_CONVERGENCE_AND_FINAL_EXPERIMENTS_20261014.md)与[正文框架](../paper/WORLD_CACHE_MAIN_TEXT_OUTLINE_20261014.md)继续围绕 **CFG 一致修正读出＋对实际动作校准的阶段计算分配**。原效率配置与高保真配置分别报告；B/F 保留独立边界。此处只有运行状态，没有新 B 科学结果。
