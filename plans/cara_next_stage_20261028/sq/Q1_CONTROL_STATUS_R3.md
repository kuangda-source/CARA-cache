# Q1 控制入口与 S 父状态组件进度

2026-10-29 更新。**Q1 两端 R3 的各 45 项 GPU 隐藏 CPU 检查均已接受，固定同一源码。真实 CUDA 数值门、codec 科学结果和新的 GPU 执行均未发生。** [双端进度与后续准备](DUAL_HOST_PROGRESS_20261029.md)。

## Q1 当前证据

- 固定生产源码为 `f3be7662175889c77e3719521fecb9c4d3be83af`；后续仓库编辑不重绑定该源包。唯一提交、恢复、运行/终态捕获、中央结算与释放后 CPU 分析入口已实现。
- [四卡 R3 接受](../../../reports/cara_sq_q1_control_four_card_cpu_accepted_r3_20261028.json)：34 项核心和 11 项包装控制全部通过，零跳过；容器退出 0。进程 CPU 含子进程约 52.84 秒，worker 墙钟约 332.51 秒、峰值 RSS 0.552 GiB。它验证小张量/临时账本与实际 Linux 子进程，不验证真实 CUDA 原 C 输出或部署效果。
- [两卡 R3 接受](../../../reports/cara_sq_q1_control_two_card_cpu_accepted_r3_20261029.json)：同一固定源码的 34+11 项、五种实际 Linux 子进程场景均通过，零跳过；00:52:47 容器退出 0。worker 墙钟 47.53 秒、进程 CPU 含子进程 30.00 秒、峰值 RSS 0.568 GiB。[双端组合接受](../../../reports/cara_sq_q1_control_dual_cpu_accepted_r3_20261029.json)核对全部 25 个关键源码 SHA 相同；原 C CUDA 门和真实账本结算仍为 false。
- [R1 超时原件](../../../reports/cara_sq_q1_control_cpu_timeout_diagnostic_r1_20261028.json)保留：两卡 R1 的 45 项通过；四卡 R1 的后处理 CLI 超过测试脚本的 60 秒限制。生产报价原已绑定 300 秒，后续测试按该原上限验证，未增加 GPU 范围或预算。
- [R2 绑定诊断](../../../reports/cara_sq_q1_control_r2_binding_diagnostic_20261028.json)保留：共享容器函数发生内存参数变化后，旧核心证据的整体复用被正确拒绝。R3 显式传入 16 GiB、只生成一组 memory-swap 参数，并在改变 GPU 模式前完成命令构造。
- [前阶段资源观察](../../../reports/cara_sq_q1_control_r3_allocation_readonly_20261028.json)保留：当时两卡 A32 占用 CPU 24/25、40 GiB。本轮[新的 CPU 准备观察](../../../reports/cara_sq_two_card_cpu_admission_readonly_20261029_0051.json)确认两卡无运行容器、约 46 GiB 可用内存且 R3 stage 不存在，随后单次启动该 CPU stage；本对话没有改变主线原件或裁定其科学结果。两卡原件见[启动](../../../reports/cara_sq_q1_control_two_card_cpu_launch_r3_20261029.json)、[终态](../../../reports/cara_sq_q1_control_two_card_cpu_capture_r3_20261029.json)。瞬时资源观察不是 GPU 准入。
- 四卡已[暂存独立 Q1 源包](../../../reports/cara_sq_q1_four_card_source_prepared_r1_20261028.json)、准备 [1 GiB SSD 输出与异盘 48 MiB 日志](../../../reports/cara_sq_q1_four_card_storage_prepared_r1_20261028.json)，[宿主命令探针](../../../reports/cara_sq_q1_four_card_native_probe_r1_20261028.json)通过。B1 的 32 文件/20.80 GB [原件直传](../../../reports/cara_sq_b1_port_terminal_r2_20261029.json)已完成并经目标 SHA 核验；原 R1 片段/费用和两小时总 envelope 保持，已知传输句柄退出。[原 Q1 独立资产 CPU 扫描](../../../reports/cara_sq_q1_four_card_asset_cpu_recovery_r1_20261029.json)已退出 0，33 项原件/权重 SHA/实际身份通过。
- 两卡也已完成[同源码独立源包](../../../reports/cara_sq_q1_two_card_source_prepared_r1_20261029.json)、[私有存储](../../../reports/cara_sq_q1_two_card_storage_prepared_r1_20261029.json)与[原生命令探针](../../../reports/cara_sq_q1_two_card_native_probe_r1_20261029.json)；[原资产 CPU 终态](../../../reports/cara_sq_q1_two_card_asset_cpu_terminal_r1_20261029.json)已退出 0，33 项 SHA/实际身份通过。GPU 尚无新授权或提交。

新卡仍是[原完整范围](Q1_WHOLE_SCOPE_R1.json)：两个旧 FIT × 六位置，96 正式 C pair，加预热/预检/Dense-hidden 控制共 **111 pair / 222 heads**，新增 deep、父轨迹、视频均为 0。[原双端整卡报价](Q1_WHOLE_PREPARATION_R1.md)保持，A6000 预测 54.33 分钟/硬限 1.25 GPUh，Ada 预测 109.28 分钟/硬限 2 GPUh，均为含未实测 GPU 余量的规划值。

原 C 和 Dense-hidden 必须与 B1 逐值相等；原 CPU 重放失败的诊断保持，不调整精度/容差来拟合。任何原数值门失败均停止后续 codec，不从部分状态选方向。全部释放、中央结算和终态接受之后，才在 2 核/8 GiB、300 秒 CPU 范围内进行 LOPO。实际新 GPU launch 后才创建半程及终态检查。

## S 的下一项

新增 [PolicyOwner 状态回滚组件](../../../src/wcomr/sq_s_owner_roundtrip_r1.py)覆盖实际父 owner、读出历史、校准器和 executor 元数据；未知字段、策略绑定变化、已推进的父 pair 或 poisoned owner 均拒绝。发现元数据被影子计算改变时，只清理恢复并报错，不接受该采集证据。物理模型、求解器、buffer 和 RNG 由既有 CompleteStateRoundtrip 单独负责。

已准备[完整 CPU 检查](../../../tests/check_sq_s_owner_roundtrip_cpu_r1.py)：两父策略、flow 开/关、OFF/ON 共八条声明小权重路径，核对全 36 pair、最终 latent 与占位视频字节。本地运行时缺少 OmegaConf，改用已登记 Linux 环境。四卡 R1 于 10 月 29 日 00:07:31 退出 1，未进入组件检查：GPU 隐藏时官方模块导入触发 FlashAttention 可用性断言。[原终态](../../../reports/cara_sq_s_owner_four_card_cpu_failed_terminal_r1_20261029.json)和[诊断](../../../reports/cara_sq_s_owner_cpu_import_failure_diagnostic_r1_20261029.json)保留；容器墙钟约 450.17 秒，实际 CPU 秒未留存，不解释为方法失败。

新 R2 复用仓库已接受的 PG CPU 导入适配，导入后恢复探针，执行同样八路径/十六边界；模型权重加载和 Triton 执行仍禁止。另修正 fixture 回执读取为其 `checks` 字段，未改变 cohort。[四卡 R2 原终态](../../../reports/cara_sq_s_owner_four_card_cpu_capture_r2_20261029.json)退出 0，八条完整 CPU 路径、十六检查边界均通过；worker 墙钟 219.11 秒、进程 CPU 68.70 秒、峰值 RSS 0.874 GiB。[独立接受](../../../reports/cara_sq_s_owner_four_card_cpu_accepted_r2_20261029.json)同时拒绝运行中、缺边界、缺父策略、CUDA 和真实视频五类伪回执。记录中源码缩写 `8779bb25` 已按 Git 唯一解析到完整提交，原回执未改。

该接受仅覆盖 CPU 实现，不含真实 Cosmos 权重、S 科学标签或完整 GPU 采集卡。[双端 S owner 与存储组合](../../../reports/cara_sq_s_dual_cpu_accepted_r2_20261029.json)现已接受：每端 owner 八路径/十六边界、完整存储十六路径；每个 flow 为 108 行、56 Dense/52 C 和八 raw，完整 OFF/ON 相等。R2 保留实际噪声坐标与直接复用的原 C，24 个旧锚点去重，每端 280 数据文件重载。两卡原挂载拒绝和修正见[双端进度](DUAL_HOST_PROGRESS_20261029.md)，真实 raw/部署收益未接受。

Q1 [完整新卡审阅](Q1_NEXT_CARD_REVIEW_R1.md)现已齐备，后续需单独 GPU 授权与 fresh 准入；双端各 33 项真实资产已独立接受。S 继续真实存储/RAM边界、整卡入口和完整报价；[真实几何解析下界](../../../reports/cara_sq_s_resource_analytical_floor_r1_20261029.json)已排除沿用 Q1/tiny 资源 profile，不能据此声称实测物理峰值。Q1 原 CUDA 数值门仍未过；S 的完整 CPU 接受不替代它。S/Q 各自完成端点验证前不组合。全局 canonical、主线 A32 源码与预算未由本对话修改。
