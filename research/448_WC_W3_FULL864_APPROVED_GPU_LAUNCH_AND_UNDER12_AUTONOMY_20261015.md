# W3 完整标签卡启动与执行授权更新（2026-10-15）

用户已明确批准完整 W3 标签卡，原卡于 **2026-10-15 12:27:22 北京时间**通过锁内准入并启动。该卡用八个新 EXPL_DEV 输入，采集同一实际状态下 C／A／D 的真实误差，为 W3 风险预测与动作选择补齐监督；当前尚无本卡科学结果。

## 1. 新授权如何执行

用户原话：

> 批准，以后少于 12gpuh 时的都不用问了，直接启动

- 本完整卡获得具体批准，预计费用 **11.645827780 GPUh**，批准单次计费上限 **12 GPUh**。
- 后续完整单次预计费用 **严格小于 12 GPUh**，在已定研究范围、原累计余额和资源条件内直接推进；**等于或超过 12 GPUh** 仍需具体批准。不能拆卡或删对照来规避整卡判断。
- 累计 cap **104.971363333 GPUh** 不变，历史实结 **79.996377372 GPUh** 不变，启动前剩余 **24.974985961 GPUh**。这次更新没有新增或重置 48 GPUh。
- 原停止新 GPU 和旧 >8 询问规则，由本次明确批准及新阈值覆盖。旧 CPU 阶段“等待许可”的文字按当时状态保留。
- P-ACR 仍为可选增强，尚未选定启动；F/B 已结束，主线 A/H1 冻结，不新增生成器训练、OMR 或人工评审。

授权：[本卡直接回复](../manifests/wc_w3_label64_full864_direct_human_approval_20261015.json)、[后续少于12规则](../manifests/wc_execution_autonomy_authorization_20261015_under12gpuh.json)。服务器 ledger 已仅更新执行政策和历史，费用、cap、作业数在该政策写入时保持不变。此后运行中的临时预留不是实际支出，费用以原 supervisor 终态结算为准。

## 2. 已通过的准备与实际启动

最终生产 CPU 见[447](447_WC_W3_COMPLETE_CPU_CLOSED_AND_WHOLE864_PERMISSION_DECISION_20261015.md)：原 source **047dcf181a3ab706002b2965e74b626e4648deea**，1627 源文件与完整23控制接受。已接受 stage 和输入没有修改；新增授权以独立运行文件传入。

启动前重新核对项目锁空闲、无计算进程、两张 A6000、余额和原 source／registration／CPU／scope SHA、原 run／dispatch claim 不存在。选用 fresh UUID `GPU-cebf7119-cf03-23b9-e192-cd196332b704`，准入时24MiB、sm8.6、无计算 PID；磁盘约329.47GiB可用。

| 原句柄 | 值 |
|---|---|
| 卡 | `WC-W3-LABEL-EXPLDEV8-PARENT18-LOCAL64-FULL864-R1-20261015-A` |
| run | `wc-w3-label-expldev8-parent18-local64-full864-r1` |
| stage | `.sync/wc-w3-label64-production-cpu-r3-20261015` |
| supervisor / child / CPU post watcher | **876730 / 876879 / 876731** |
| GPU 启动 | **2026-10-15 12:27:22 Asia/Shanghai** |
| 单次计费上限 | **12 GPUh**，费用含加载、teacher、取证/恢复/IO及失败 wall |
| 原秒数期限 | 不启用 |

[唯一派发回执](../reports/wc_w3_label64_full864_GPU_launch_20261015.json)、[启动准入确认](../reports/wc_w3_label64_full864_GPU_startup_confirmation_20261015.json)、[fresh资源](../reports/wc_w3_label64_pre_GPU_fresh_admission_20261015_1227.json)、[政策落账](../reports/wc_w3_label64_under12_policy_remote_record_20261015.json)。首次即时检查时尚处于资源校验，后一次启动确认已见原 supervisor/child running；这两次仅核对启动，没有查局部标签或中间指标。此后不持续监听。

## 3. 完整范围和要回答的问题

八个冻结 EXPL_DEV 提示词、四类各二、seed0。16条正式普通H1/诊断父路径加2条完整预热，共 **18父路径**；每条36更新，**64正式+8预热=72个计划状态**，每个支持状态独立执行非提交式 C/A/D，同状态真实 D teacher 不复用普通路径的 D。普通648对加诊断最多216对，共 **最多864pairs／1728 CFG／一次模型加载**。

最多90原件、1242张量；18个视频位置，接受输出完整93帧解码。未知、保护边界、不支持、拒绝、技术失败均保留在18父/72状态分母，不补点凑864，不替换输入。诊断输出不得改变普通H1的36步输出、动作、修正历史、终态或RGB。普通H1原合法动作集包括旧P0，不能为诊断CAD而删掉。

本轮关键是测得真实 `q_C`、`q_A`、`q_D`，保留 `g² q_A` 和 `g²(q_C-q_A)`，负动作收益也是合法标签。输入只用普通父路径的动作前因果信息、真实连续噪声坐标和短历史，teacher／未来状态不进入特征。本卡不产生新策略终点或净加速结论，也没有新Native参考。

## 4. 预计完成与一次查收

预计 GPU 运行 **约8—12小时**，另留 CPU 全原件审计时间；预算 forecast 是规划估计，并非已观察的耗时。安排 **2026-10-16 01:00 北京时间**一次查收（unix **1792083600**），此前不看partial、不反复SSH。

查收命令：

```sh
.venv/bin/python scripts/capture_wc_w3_label64_full864_r1.py \
  --launch-ref reports/wc_w3_label64_full864_GPU_launch_20261015.json \
  --cpu-launch-ref reports/wc_w3_label64_actual_production_CPU_r3_launch_20261015.json \
  --not-before-unix 1792083600 \
  --output reports/wc_w3_label64_full864_collection_20261016_0100.json.gz
```

仅读取原source、原句柄、supervisor/runner、全18父/72状态/90原件和CPU-final/post-exit、全部兼容视频93帧RGB控制、实际费用与锁/GPU释放。局部输出或单独 GPU exit 不等于完整接受；无Native，不能要求本轮视频LPIPS。若未完成，按剩余工作量重估一次并结束，不循环等待；连接失败先检查本任务自己的本地FRPC，不重派原卡。读回工具语法及未到时间零SSH分支已本地检查，不改变GPU代码或stage。

## 5. 查收后如何推进

1. 完整接收后先检查父路径非提交等价、真实标签与因果隔离，分开统计支持/未知/保护/拒绝/失败与全部原分母。
2. 在CPU上按提示词分组比较 T0旧H1、T1当前观察ridge、T2短历史；优先看动作后悔值和边界误排，MSE只作辅助，不随机拆step冒充泛化。
3. 若真实动作价值出现可用增量，按既定W3路线冻结预测器与费用并登记完整闭环卡，在新授权阈值与原余额内执行；仍需匹配Native、质量和真实计时来确认端点。仅预测更准而动作/端点不变，不合入主线。
4. 保留A/H1现有主稿证据，正式强基线、同预算简单调度、冻结测试、重复clean计时和部署/自动质量仍为论文收尾待项；不为本轮标签成果抢先宣称这些已完成。
