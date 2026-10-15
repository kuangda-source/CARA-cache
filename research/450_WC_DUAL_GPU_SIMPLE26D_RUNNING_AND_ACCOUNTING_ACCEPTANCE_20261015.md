# 双卡锁与记账已验收，同26D主线完整卡已启动

**双卡兼容已完成，空闲GPU0已用于同26D简单调度对照，原GPU1 W3继续原任务。** 本轮完成的是实现、CPU验证和真实GPU准入，实验终点尚待查收。

## 当前两卡

| GPU | 任务 | 原句柄 | 范围 | 一次查收 |
|---|---|---|---|---|
| GPU0 / UUID-de9a5370-cd87-0f1c-a48e-288888777dd3 | SIMPLE26D，source36f5583 | supervisor909867 / runner910056 / post909868 | 六配置×四CAL，24正式＋12完整预热，1296pairs，1load | 2026-10-15 23:00北京时间 |
| GPU1 / UUID-cebf7119-cf03-23b9-e192-cd196332b704 | 原W3，source047dcf1 | supervisor876730 / runner876879 / post876731 | 原18父、64正式＋8warm状态、最多864pairs | 原定2026-10-16 01:00北京时间 |

新卡16:17:32单次派发，**16:18:09锁内fresh准入**。GPU0为A6000 sm8.6、489MiB背景占用、无计算PID；完整源和CPU结果绑定后才取得本卡8GPUh预留。16:18:51资源身份确认新runner存活、两UUID锁分别持有、旧W3原进程仍存活。该确认只读句柄/资源与账本，没有读取任何中间科学结果。模型初始化属于运行过程，不计作实验接受。

原W3代码、stage、输出、supervisor、child、post及查收时间均未修改。原账本启动前后及资源确认时SHA均为 `410925d15266329320b0a5e4f5aa2e63e14230fa5dc92c4cdea2afeafe944a45`。

## 锁与费用机制

- 逐UUID锁：`.sync/gpu-locks/<GPU-UUID>.lock`，不同卡独立，同卡互斥；子进程继承本卡锁FD并核对其实际路径。
- 新权威账本：`reports/gpu-budget-v2.json`；只在短事务锁 `.sync/gpu-budget-v2.lock` 内原子预留/结算，不把模型运行时间放在共享账本锁中。
- 每个完整任务绑定run、launch UUID、源码、配置、GPU、完整上限及计费原件。按每卡任务墙钟时间分别加费；同一账单重复导入为幂等，冲突拒绝，超费保留真实值并阻止新准入。
- 原W3桥接909859在新stage持有GPU1兼容锁，只读原W3终态账单后将实费导入v2。原CPU post终态前绝不写旧账本；之后可生成兼容镜像。旧启动器见永久协议标记必须拒绝，不能继续用旧快照账本准入。

| 当前费用身份 | GPUh |
|---|---:|
| 原累计cap，保持不变 | 104.971363333 |
| 已实结起点，未把运行预留当实费 | 79.996377372 |
| 原W3完整上限预留 | 12 |
| 新SIMPLE26D完整上限预留 | 8 |
| 两任务全部上限预留后可准入余额 | 4.974985961 |

新卡完整预测 **5.766054749 GPUh**，含一次加载、36完整路径、写盘、启动/清理、1.5并发余量，计费上限8；满足用户“严格少于12GPUh直接执行”。不增加或重置预算，不拆卡规避阈值；预留释放后才根据实际账单重新计算余额。

## CPU与实现验证

[原CPU查收](../reports/wc_simple26d_full96_CPU_collection_20261015_1616.json.gz)与[独立接受](../reports/wc_simple26d_full96_CPU_independent_acceptance_20261015.json)：source36f5583、全部1644源文件一致，96条两flow完整Toy采样（四输入×六执行器×audit/lean×两flow）通过，36步/26D、修正历史、真实锚点、状态恢复及最终输出等价通过。真实生产入口绑定四原输入、完整36矩阵、配置/模型资源、11项变更拒绝，CPU整组398.441482秒，原CPU进程已结束。CUDA未初始化、GPU提交0、旧账本与W3 stage写入0。

服务器完成5项并发预算测试与2项scope/分母测试。本地另执行实际桥接脚本的进程测试，验证旧CPU读阶段账本不变、终态之后才允许镜像。完整卡发起前进一步对所有60个非D计划步逐一核对真实calibration的(anchor,step)与gain支持，不用Toy支持冒充真实资源支持。

## 实验设计与论文用途

完整事前设计见[双卡与同26D预登记](449_WC_DUAL_GPU_ACCOUNTING_AND_SIMPLE26D_COMPLETE36_PREREG_20261015.md)。原FIXED_A/PLAIN不改；UNIFORM及FRONT_DENSE各有A/C读出。所有26D；原FIXED_A为5A/5C，新的A两臂为10A，C臂为10C。因此报告同时给实际A/头/主计时，不能把同D配额称为同总成本。

这张卡回答论文总表 **N06 / Simple Schedules at Matched Dense Budget**：现有高保真阶段安排是否优于普通均匀/粗阶段安排，以及修正的作用是否依赖位置。N05强基线公平调优仍待，原D14固定等价结果保留；新W3标签本身不代表新调度已有效。F/B仍关闭。

**本卡与W3并发，共享主机资源，所有时间标为 `CONCURRENT_DIAGNOSTIC_NOT_CLEAN_LATENCY`。** 终点保真与相同mask的原件等价可以验收，正式净加速结论待独占重复测速；不拿并发秒数与旧独占秒数直接比较。

## 后续查收

已建立独立 `worldcache-26d` heartbeat：今晚23:00一次查收。原 `p-acr-cpu` W3查收仍在明日01:00，只增加对新账本兼容关系的说明。两者均不得持续监听；未完成则按剩余量重新估时安排一次后立即结束。

新卡命令：

```sh
.venv/bin/python scripts/capture_wc_simple26d_full36_r1.py --launch-ref reports/wc_simple26d_full36_GPU_launch_20261015.json --output reports/新的终态回执.json.gz
.venv/bin/python scripts/analyze_wc_simple26d_full36_r1.py --capture reports/新的终态回执.json.gz --output reports/新的独立接受.json
```

验收全部36原位置、12warm重复的全部36guided/动作/终态/RGB、八原420 fixed端点、四匹配Native身份、全部有效兼容正式视频93帧评分，独立重算均值与实际动作、费用和本UUID释放。拒绝、缺失、技术失败保留，不填零、不替换样本。GPU1其他合法作业在途不是GPU0验收失败，反之亦然。验收后整理结果、更新论文总表并推送；本次查收不自动追加新GPU卡。

原件入口：[启动回执](../reports/wc_simple26d_full36_GPU_launch_20261015.json)、[双卡资源/准入确认](../reports/wc_simple26d_full36_dual_GPU_startup_confirmation_20261015.json)。
