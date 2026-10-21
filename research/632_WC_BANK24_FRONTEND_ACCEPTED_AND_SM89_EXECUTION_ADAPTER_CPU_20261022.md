# BANK24 新机前端已接受，独立 SM89 执行适配 CPU 卡

2026-10-22。此卡继续已授权的四卡资源与执行准备，不新增科研 GPU 范围。

## 当前已接受的部分

原 BANK24 新机前端 R1 于 06:13:25.442153 一次终态收件，随后仅离线独立验收，19 项全部通过。原 source `907d20cbb81eb3d898b93d71b03398ec558d1888`、9 件 payload、manifest、1,789 件冻结依赖及 1,772 件入口子集完整一致；六个真实 Cosmos 请求、24 个保护入口和 12 类范围变更拒绝通过。原 worker wall 120.487787 秒，supervisor wall 121.278840 秒；原进程、本人容器和资源锁均退出。

- 原件：[terminal](../reports/wc_four_card_BANK24_host_CPU_R1_terminal_20261022.json)。
- 独立接受：[independent_acceptance](../reports/wc_four_card_BANK24_host_CPU_R1_independent_acceptance_20261022.json)。
- 只能将 `host_boundary_CPU_accepted` 设为 true。完整新机 scope CPU、实际 CUDA、整卡新机报价和 GPU-ready 仍为 false；原八项价格仍为 null。

## 需要独立适配的执行问题

原入口把 SM86、旧 HF 缓存、项目配置与 stage/src 路径绑定在一起；原预算池也限定 A6000/8.6。仅去掉硬件断言不足以迁移。另一个问题是旧验证链追溯历史父卡的物理 Native 视频，而本 BANK24 要重新生成自己的六条 Native。

本卡保留原 `2bd41dc8` 生命周期闭包与 `c1c95ce0` 入口，不修改捕获 registration 或旧 stage。额外登记 29 件来自同一 `2bd41dc8` Git revision 的真实历史元数据，7,068,879 字节，压缩包 2,015,550 字节／SHA `3445cff98f3c971ea6a146991470e6d1b01152a08a72397be9e9e5fe2341abc7`。原 1,789 件分母保持，额外 29 件单列，禁止覆盖原文件。

用原纯元数据函数重建真实校准、成本排序、H1 与 prior 参数：校准 fingerprint `9ab1d77c303560823ed2f32f43b2982318cdd9835828a46da4835a1b95ea7d7a`，H1 `34ef948ed2a309e8b1cae4b72b780c14e21d63383fa1eadcdfc8803c3d5beef8`，gamma `0.7235237005554214`，输入 fingerprint `6ff3902a8a6272529ad5ad558699b994be1940b7efa1de24adfd37cae0aad90e`。四个历史 Native 槽只保留来源说明，不读取它们的旧视频或冒充本卡六条 Native。DEV 不拟合，四 CAL 的 mu／中位秩及较大 z 留 D、平局 >= 不变。

## 此次实际 CPU 范围

配置为 [独立 CPU 配方](../manifests/wc_four_card_bank24_execution_adapter_cpu_r1_20261022.json)；[额外元数据登记](../manifests/wc_four_card_bank24_execution_metadata_r1_20261022.json) 单独绑定原源。

1. 在新 job/inputs 复制并重读服务器已有完整 1,789 件依赖，合并单独核对的 29 件真实元数据。原 job、注册和环境只读。
2. 用原代码重建完整真实执行输入及完整六 DEV × D21/A21/Native35 的 18 正式＋6 warm／24 路径、864 pairs／1,728 CFG／1 load／6 Native 范围。没有重复旧 248 数值、六请求前端或资源导入验证。
3. 对原普通受保护 runner 做六类可逆主机替换，显式保留 `(8,9)`、28 blocks、普通 guardrails、owner／FD 锁和全部输出逻辑；登记原科学 source 与新适配 source。三个生成源逐件独立 SHA 验证。
4. 原 BudgetPool 只可逆替换硬件谓词，实际 reserve／settle 方法在内存 transaction 中跑 21 项控制，含忙显存、错误架构、重复句柄／UUID、余额不足、整卡预留、实际全 wall 加法和结算冲突。不开权威账本、不初始化余额、不写任何实际 reservation。
5. 新 GPU 前置拒绝必须保持：本前端接受或本适配 CPU 接受均不能单独赋予 GPU 准入。

本地 7 项单元控制和完整真实元数据重建／生成源编译／21 项内存费用控制已通过，见 [local_controls](../reports/wc_four_card_BANK24_execution_adapter_local_controls_20261022.json)。本地 Torch 版本与服务器不同，不能当四卡实际 CPU；必须 GitHub 发布新 source 后单次派发新 job，收件再独立接受。

## 资源与收件

单次 CPU job：`/data20t/gaokuangda/worldcache_workspace/bootstrap/wc-fourcard-bank24-execution-adapter-cpu-r1-20261022`。原 1,789 件直接复用服务器 SHA 副本，只传约 2 MB 元数据和必要新代码。2 CPU／16 GiB、隐藏全部 GPU、network none、readonly root／workspace／Torch 缓存，仅新 job 与自身五缓存可写。规划 180 秒，最长 900 秒，0 GPUh；此时间不是科研 GPU 报价。

启动：`python3 scripts/wc_four_card_bank24_execution_adapter_cpu_r1.py launch --output reports/wc_four_card_BANK24_execution_adapter_CPU_R1_launch_20261022.json`。已存在 job 仅返回原句柄，不重派或覆盖。未知连接不能当未启动。

实际启动后一次 admission；按实际 start+60 秒和 start+300 秒向上取整分钟，分别安排一次 `capture --kind halfway`、`capture --kind terminal`。原件保存后离线 `accept`；只读 health 的半程不能提前接受。未完成只根据实际阶段重估一次，失败留存再按独立版本修复。

## 接续及仍缺的部分

此卡通过只能接受执行输入和可逆 SM89 组件 CPU，`full_new_host_scope_production_CPU_accepted=false`。仍需独立实现 GPU 容器的 supervisor／PID／FD／逐 UUID 锁传递、post／完整 24 终态验收、整卡新机报价，以及权威 v2 唯一写入交接。原 host 上的 FD 或 PID 不能直接冒充容器内的父进程和继承句柄；后续必须实际 CPU 验证这一契约，不能将本卡生成源编译当完整生命周期已通过。

实际 CUDA 兼容需要计费 GPU 执行，并计入完整卡的 setup／失败费用；没有免费 GPU probe。未取得双卡权威 v2 全历史、settlements、全部活动整卡上限预留和唯一写入权交接前，不开四卡科研 GPU，不能复制旧 `116.825` 快照建立新账本。cap226／origin79.99637737158223 与历史保持。

新机整卡价的八项仍分别待测，不将旧 forecast3.407222222／cap4.5 变成 Ada 实测。完整 BANK24 接受及实费结清后，接既定 X-R／同 D 配额 CPU 诊断，再接已具体批准整卡 12 GPUh 的完整 1624 卡。原批准不重问，不拆缩；PG-P1 等后续仍沿原独立冻结／CPU／报价门。F/B 关闭，无训练、人评、付费 VLM／OMR；54 科研行和 status_counts 不变。

实际新 source／launch／admission／两次检查的回执在启动后补入本报告和机器索引。两卡四小时只读监控保持，本卡不追加双卡 SSH。

## R1 控制面预检失败与独立 R1.1

source `242070556de95727101ecc656b922a2591d7e3a4` 首次部署返回远端 Python 异常，原 UNKNOWN 回执保持。离线核对原发布 SETUP 的第 30 行和原异常栈，确定控制面 Python 3.8 缺 `Path.is_relative_to`，错误在 `job.mkdir` 和 `Popen` 之前，0 CPU 启动；这是控制面适配问题，不能说网络／模型／CUDA 失败。[原部署回执](../reports/wc_four_card_BANK24_execution_adapter_CPU_R1_launch_20261022.json) 与 [源码顺序失败边界](../reports/wc_four_card_BANK24_execution_adapter_CPU_R1_predispatch_failure_boundary_20261022.json) 均保留。

独立 [R1.1 配方](../manifests/wc_four_card_bank24_execution_adapter_cpu_r1_1_20261022.json) 改用 Python 3.8 支持的路径祖先检查，最先只读检查原 R1 stage，若存在就恢复而不派新任务。新 job 为 `wc-fourcard-bank24-execution-adapter-cpu-r1-1-20261022`；不重用原回执或 intent。容器内 Python 3.10 的科学代码、CPU worker、额外 29 件元数据、完整 24 分母和三个生成源码均不改。7 项本地控制重新通过，加入控制面路径 API 与原 stage 拒绝检查。新版本 GitHub 发布后才单次部署；无真实新 launch 时不虚排半程或成功验收。

## R1.1 实际启动、技术完成与两次独立查收

GitHub source `a3cfddd9dafe3eb885e8e650aa1212e6dcd764c9` 发布后，R1.1 于 **2026-10-22 06:41:04.063354**（unix `1792622464.0633543`）单次启动，supervisor PID `625584`／start `940752742`。原 R1 stage 的优先恢复检查通过才进入新部署；原 1,789 件从已验服务器目录逐 SHA 复制，没有重传基础包或下载模型。manifest SHA `f56653a71f914f543341c82a328919ee9f91a836c23d84ae8cee0c67e7a4badf`，worker SHA `ba53b257ec27f0c565f0c1b1976f16747bf21d01a73d527b1a8606e72c0d7bf2`。

一次 admission 已保存，16 项身份与技术边界核对通过。收件时原 supervisor 和本人容器已退出，health 报告新 CPU 命令退出 0／精确 marker，通过真实元数据重建、可逆 SM89 组件生成及 21 项内存费用控制，worker wall **18.459398 秒**。这不是终态独立 SHA 接受：尚未读取最终 result／日志或执行独立终态 hash，`execution_adapter_CPU_accepted` 仍为 false，完整新机 scope／GPU-ready 继续 false。

- [实际 launch](../reports/wc_four_card_BANK24_execution_adapter_CPU_R1_1_launch_20261022.json)。
- [一次 admission](../reports/wc_four_card_BANK24_execution_adapter_CPU_R1_1_admission_20261022.json) 与 [技术边界](../reports/wc_four_card_BANK24_execution_adapter_CPU_R1_1_admission_technical_boundary_20261022.json)。
- [按真实 launch 读回的两次检查](../reports/wc_four_card_BANK24_execution_adapter_CPU_R1_1_actual_two_once_checks_20261022.json)：`bank24-sm89-cpu-r1-1` 于 **06:43** 技术半程（最早 06:42:04.063354），`bank24-sm89-cpu-r1-1-2` 于 **06:47** 独立终态（最早 06:46:04.063354）。只恢复同一原句柄，不因早完成重派或提前接受。

原 `bank24-cpu-2` 的 19 项前端验收原因已完成，且新两次检查创建／读回后已删除。两卡四小时只读自动化保持，本轮没有查询双卡、GPU 或权威账本。后续终态接续已明确完整容器 supervisor／PID-FD／锁与费用／post／collector 的独立 CPU 工作，不能以本组件 CPU 代替。
