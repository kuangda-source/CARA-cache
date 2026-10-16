# N07生产CPU打包修复：完整测试依赖进入独立stage

2026-10-16。**原真实CPU验证发现后处理测试依赖漏传，已修正打包闭合并通过隔离stage回归；完整方法、八新输入、180分母及费用不变。** 这是执行准备的技术失败，未运行模型或产生新视频；不据此判断方法效果。

## 原失败与定位

12:27按约一次查原source3138e03/PID1111360，进程已终态，1724payload SHA全通过；原六命令在第三组测试中退出1：`test_full180_with_all_actual_warm_lengths_and_160_N10_ready_artifacts`导入`wcomr.automatic_quality_r1`失败。前两组6+5控制通过，第三组7通过/1错误，真实Cosmos CPU入口尚未到达。原CPU-bundle退出1、21.436405秒和全部原stage/回执保留；独立接受明确CPU_accepted=false，没有追认原6命令全通过。

本地原打包计划157文件确实不含automatic_quality；部署器把测试文件作为extra_files复制，却只为入口脚本展开静态wcomr导入。工作树能找到该模块，因此单机测试曾通过；独立stage暴露了缺口。

## 最小修复与CPU证据

`immutable_stage_payload_r1.plan`现在为extra_files中的Python文件也展开本地导入闭合。测试文件仍完整保留，原入口/选择/采样/评分/失败规则不改；新计划158文件仅新增automatic_quality模块。新的临时Git仓库→归档→独立stage→隔离Python实际导入控制通过，与原打包8控制共9项接受。

受同一打包器影响的N08生产打包7项控制重新通过，其中真实隔离stage复跑原八组CPU测试通过；不把这些合成控制当最终生产或视频。数值执行99依赖重新核对全部原SHA一致，原952证据复用，不重跑952。

准备R2 fresh stage `.sync/wc-paper-n07-production-cpu-r2-20261016`，重新执行原完整六CPU命令；原R1目录只读保留，不拼接前两命令成功结果，不缩完整180、6318pairs/12636CFG或160实际参数范围。GPU和预算仍等完整CPU通过后的具体人类批准；没有新GPU/服务器预算修改。

## 预算增量入口准备

另外补齐独立`gpu_budget_cap_extension_v2.extend_cap`，仅在明确直接人类批准后提高同一累计cap，保留全部jobs、origin、实际费用与活动预留；幂等与冲突、错误窗口/未批准提案/坏账拒绝等5项临时账本CPU通过。它不构造授权、不启动任务、不写旧ledger，也没有被用于当前服务器。原v2 reserve/settle与原99数值执行源保持。

完整N07报价15.055555556GPUh、N08原完整40为3.6275；113仅为拟议cap，实际服务器104.971363333与余11.389538676快照不改。CPU未接受前不提出最终执行确认，不把技术修复变成调参。F/B关闭、无训练/OMR/人评。

## 原件

- [wc_paper_N07_actual_production_CPU_R1_collection_20261016_1227.json.gz](../reports/wc_paper_N07_actual_production_CPU_R1_collection_20261016_1227.json.gz) · SHA256 `6c83b588d03543c1667956627da387723af4d80425653904dae8e8ae39fe73d0`
- [wc_paper_N07_actual_production_CPU_R1_independent_acceptance_20261016.json](../reports/wc_paper_N07_actual_production_CPU_R1_independent_acceptance_20261016.json) · SHA256 `5868cbee547ee57915ee8b77d89600fd6c89f04bd4508fdef83c6db1bd25057d`
- [wc_paper_N07_actual_packaging_R2_repair_and_unchanged_scope_20261016.json](../reports/wc_paper_N07_actual_packaging_R2_repair_and_unchanged_scope_20261016.json) · SHA256 `1ecbdb9348d718440e78425fb49805c78af1cc0af18bd21e047c3348ba590a32`
- [wc_gpu_budget_cap_extension_local_CPU_preparation_20261016.json](../reports/wc_gpu_budget_cap_extension_local_CPU_preparation_20261016.json) · SHA256 `9b98c4907772156ac47891dd9b05789b43039d5817261a24349eeed467f41f55`
