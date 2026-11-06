# 完整校准执行入口与四卡CPU验证

2026-10-30。14GPUh方案的完整校准流程已组合到同一CPU准备入口：两次预热、两份新Native教师、Native计时控制、allD输出控制、Uniform计时控制，以及完整51次双FIT查询。实际GPU授权、准入、guardian和科学冻结仍需独立接通；当前入口明确拒绝GPU执行。

## 统一物理范围与恢复

[Calibration组件](../src/wcomr/cara_budget_calibration_r1.py)复用原生产Requests、完整采样路由、RGB读写和持久化查询日志。每个物理请求先写独占意图，完整RGB保存后再写完成记录；原路径存在而完成记录缺失时只报UNKNOWN，不重新生成。整个校准持有同一控制锁，完整返回重放不会调用原生成器。

两份教师为所有查询共用。原Native的计时ON/OFF和allD必须通过RGB与CPU RNG一致性；首个Uniform19查询与独立OFF控制一致后，才返回首个双FIT目标。两FIT都完成后才形成目标值；完整搜索还要求精确的112个物理完成位置和全部51次查询，不能用额外工件填补缺项。完整恢复会重读原RGB核对日志目标，但不新增生成。

7项本地控制通过，包含实际原控制器的完整51查询/112路径（显式合成RGB）、完整恢复0新增请求、预控制失败不重试、输出不等停止、第二FIT失败或policy fallback不接受、配置与GPU入口拒绝，以及损坏RGB或查询返回缺失的恢复拒绝。

## 实际四卡CPU原运行

[事前登记](../plans/cara_next_stage_20261028/mainline/r2/BUDGET_CALIBRATION_CPU_FRAGMENT_R1.json)绑定所有新增与继承源码SHA，只开放四卡；两卡继续保持原S优先。资源为1CPU、4GiB、零swap、无GPU/网络、只读根文件系统，工作2400秒及退出60秒。

[唯一启动](../reports/cara_budget_calibration_four_card_CPU_launch_r1_20261030.json)于18:46:12开始：stage为`cara-budget-calibration-CPU-ada-r1-20261030`，Docker CLI PID4182013，registration SHA为`1d44598101bd443cac8fe63763761448ca048b52126528844e2ce1efc1a6a91d`。18:56原容器仍在运行，PID4182060，实际资源与登记一致；[原观察](../reports/cara_budget_calibration_four_card_CPU_terminal_probe_r1_20261030.json)没有终态证明，不能据此接受完整CPU结果。

计划在两个实际采样flow上各执行112完整设计路径，再加首个writer失败、第二FIT拒绝和policy fallback三类失败/无重试控制；每flow共136次物理尝试，预计133成功及3预定失败。完整矩阵应为224设计路径、102双FIT目标、266成功物理路径及6预定失败，连同21项校准/生命周期控制。这里是待验收的分母，尚不是已通过计数。

18:58[原运维计数](../reports/cara_budget_calibration_four_card_CPU_counts_r1_20261030.json)仍见同一容器PID4182060运行：flow_False下266份完成文件、flow_True下68份，共334份；每个成功物理路径有物理与RGB两份完成文件。该计数仅用于进度观察，不代替完整终态证明或完整矩阵验收。

原容器结束后只读取同一stage，使用[接收器](../scripts/accept_cara_budget_calibration_cpu_r1.py)核对启动、源码、实际资源、原证明与完整分母。不能凭仅部分fixture输出或退出码0接受完整矩阵，不能重复启动来刷新文档。

## 只读终态采集准备

[新采集入口](../src/wcomr/cara_budget_lifecycle_capture_r1.py)仅读取原启动、guardian、worker起始、容器、锁、费用及释放元数据。原进程仍活跃或身份未知时，只返回运维状态，不打开查询结果、RGB或科学指标。它不改变设备模式、不停止进程、不写账本。

[10项本地控制](../reports/cara_budget_calibration_capture_acceptor_local_CPU_r1_20261030.json)包含采集器6项及完整校准接收器4项。Docker观察超时保持UNKNOWN；容器缺失或替换不能通过财务终态；忙锁仅被观察，原持锁者不被解锁。接收器控制使用显式合成终态，不是对当前活跃CPU容器的实际接受。

尚需补齐一个已识别失败分支：若guardian在创建资源锁前失败，当前财务验证会因锁未知而拒绝；必须由源绑定的“从未取得锁/从未派容器”证据解决，不以缺失文件自行推定释放。本轮不修改已复制到原CPU容器的源码。真实GPU采集与guardian组合、完整监控/科学接受、双端生产CPU、费用和存储仍待；原14GPUh方案未获启动批准。本轮新增GPU与中央账本写入均为0。
