# N09完整CPU命令包、一次查收与独立接受准备

2026-10-16。**N09已补齐七组控制＋真实Cosmos无权重入口的完整CPU命令包、原进程一次查收和离线独立接受工具。** 当前源码的七组本地控制共58项通过；这增加的是执行准备，尚未执行服务器Cosmos CPU或新GPU。

原N07/source `140d0a6`、今天21:30半程健康检查和明早05:30完整验收不变。继续按N07→N08→N09/10；本轮0SSH、0资源下载、0新GPU、0服务器账本写入。N10固定权重缺口保持。

## 1. 完整CPU包

[CPU命令包](../scripts/run_wc_paper_N09_production_cpu_bundle_r1.py)将执行以下七组，再调用原驻留worker的实际`--cpu-check`，合计八条完整命令：

|控制组|当前本地通过数|用途|
|---|---:|---|
|完整40执行/归档|8|冻结角色、三模式、全分母与原件路径|
|生产合同|5|原N07/N08接受、同源输入、整卡费用与授权|
|CPU原件后处理|12|完整36步、93帧RGB、组件/显存及失败隔离|
|完整40费用|6|原成功请求、预热、规划余项及整卡报价|
|单任务监督/结算|9|UUID锁、余额、原CPU终态、异常与实费|
|CPU后处理触发|6|原GPU确切退出、一次触发与失败保留|
|CPU包/查收/独立接受|12|完整命令、全源码SHA、原进程及回执身份|

58项是本地控制数，不是视频样本或科研观测。实际服务器CPU命令还需读取真实已接受的N07/N08回执，构建十个typed请求变体，并执行两个原生guardrail拒绝控制。原102观察器与952数值证据只在原四观察/数值源码、99依赖精确相同时复用，本轮未重跑102/952或真实模型。

命令包保留每条真实命令和退出码，只在全部成功后写完整CPU通过标记。原CPU结果、bundle或退出回执存在时拒绝重复运行；新GPU监督已接入完整bundle验证，不能只凭单独的typed入口摘要准入。

## 2. 原件与进程身份

[一次CPU查收](../scripts/capture_wc_paper_N09_production_cpu_r1.py)只在原ETA后读取原stage及原PID/start_ticks，逐项计算全部登记payload的实际SHA，保存原始压缩回执后才解析。失败、缺失、坏JSON与有界日志尾分别保留。超时为状态未知，不标记原任务终止或授权重派。

[独立CPU接受核心](../src/wcomr/runtime_profile40_cpu_acceptance_r1.py)与[离线CLI](../scripts/accept_wc_paper_N09_production_cpu_r1.py)从已保存回执核对完整命令顺序、源码/配置/证明SHA、完整40矩阵、两个guard控制、原生类身份、102/99来源复用及原CPU终态。接受结果明确`whole_GPU_card_selected=false`，不自动选择新GPU卡。

新增回归发现，原新代码把CPU进程身份的整个观测字典作相等比较，会因正常的`R/S`状态变化而误拒绝。已用两条新控制重现并保留[原失败](../reports/wc_paper_N09_runtime40_CPU_identity_regression_R3_20261016.json)，随后将独立接受与GPU监督的判断统一为稳定的PID＋start_ticks；状态/命令仍保留为观察，PID复用仍拒绝。没有放宽源码、完整分母、退出码或费用规则。

## 3. 已验证与未验证

[当前完整七组58项回执](../reports/wc_paper_N09_runtime40_seven_control_groups_local_R2_identity_fixed_20261016.json)绑定当前源码，分七个独立Python进程完成；四个相关CLI的标准库冷启动`--help`通过。额外验证了实际离线CLI能读取已保存的合成CPU包，且不再SSH。

原[22项R1](../reports/wc_paper_N09_runtime40_CPU_bundle_and_acceptor_R1_20261016.json)、[25项R2](../reports/wc_paper_N09_runtime40_CPU_bundle_and_acceptor_R2_20261016.json)与[首轮七组56项](../reports/wc_paper_N09_runtime40_seven_control_groups_local_R1_20261016.json)均保留。测试中的生产接受、GPU/网络/子进程和部分输入是明确的替身；微型CPU张量、临时账本/文件锁与本地离线CLI是真实执行。没有真实Cosmos、codec、CUDA或质量/速度结果。

## 4. 下一步

实际N09配置、源码包闭合与生产CPU部署仍须在N07/N08完整接受后完成，再绑定fresh v2余额、实际UUID和完整整卡授权。后续单次派发fence、GPU终态查收及独立结果接受仍待补齐，不能把本地CPU工具准备标为服务器CPU通过。

完整40规划仍为4.245833333GPUh，尚未选定/预留；同状态C/A/P0/D报价和可复现标定采集费仍独立待测。累计cap113、原origin、完整单次严格少于12GPUh自主的规则保持。F/B关闭，不增加训练、人工评审或OMR。
