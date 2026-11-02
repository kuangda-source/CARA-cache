# P1 内存准入修订与唯一实际启动

P1已于 **2026-11-02T15:44:28.784080+08:00** 在两卡原A6000实际开始；本轮完成的是资源工程修订和执行启动，科学结果等待完整验收。[实际启动原件](../reports/cara_v1_P1_actual_start_accepted_r2_20261102.json)绑定原guardian/CLI/supervisor/runner PID-start ticks、容器及唯一runner CUDA。[最新运维快照](../reports/cara_v1_P1_memory50_original_running_status_r11_20261102.json)为原进程活跃、GPU100%/84°C、0个完整物理请求，未读取部分科学分数。

## 为什么初始门由52调整为50GiB

用户明确要求审查门限并根据现状推进。原52GiB是GPU容器40GiB＋内部CPU容器8GiB＋4GiB宿主余量的保守准入；40/8是上限。生产GPU客户端同步等待FIT，实际宿主服务主要做队列/元数据和流式校验，每次CPU查询另有新鲜12GiB可用内存门。保留40/8/no-swap/12及全部失败拒绝边界，将初始宿主余量从4改为2GiB，并非更改模型或评分的内存上限。其他作业仍可能使后续12GiB门拒绝，现有监督按原规则收尾，不靠再降门或重派解决。

本地及Linux各9项控制通过，包括50GiB准入、49GiB拒绝、配置/报价一致性、来源/单次派发和失败拒绝。[Linux原CPU增量](../reports/cara_v1_P1_memory50_Linux_CPU_r1_20261102.json)退出0；导入峰值约39.38MiB，整组控制峰值约43.03MiB，这些是宿主组件控制的RSS，**不是生产视频峰值**。真实模型GPU显存、40GiB容器和内部8GiB评分限保持。完整1462文件中仅binding的52→50、profile、quote的profile哈希及相应测试4文件改变；标量/DP/搜索/视频/评分算法原字节不变，原中央115文件闭包也不变。

## 在原运行不存在时正式重绑定

[新组合证明](../reports/cara_v1_P1_whole_CPU_memory50_accepted_r2_20261102.json)复用原CPU科学/入口证据并明确绑定9项资源增量；[R2记录](../plans/cara_next_stage_20261101/source_lifecycle/V1_P1_MEMORY50_AUTHORIZATION_R2.json)保留用户“批准单次19GPUh及本卡账本事务”的原批准，并准确引用本次工程审查请求。原R1授权/CPU证明不覆盖，不将用户本次话语写成新的GPU批准。

原句柄与中央均新鲜确认无GPU意图/容器/预约后，在原stage派发锁下封存4原源文件、4 sidecar和旧资产缓存，再绑定新source/registration/proof/quote/authority。[修订回执](../reports/cara_v1_P1_source_memory50_amended_r2_20261102.json)含全部新旧SHA与原封存目录；不是对运行中源码做修改。资产摘要原验收保持，逐项stat/链接一致后只重绑资产缓存身份，完整fresh资源门另行执行。没有重建源包、CPU或64GiB独立存储。

- 当前source：`6bf82dd262c082a6786588d39d9ea23da74cc907`。
- registration：`9bf9a98db7308f3fa0b867e9ec0a928c8ea0d7389c31f394fd7bda5f3715dc35`。
- 原source dd2a73060f4097ceb91dd66c8a5f98a33fe65092 / registration bded3f7a6cdbfe12f0993720e910a489230ae43b7975a48a7745259a5f96069b仍可追溯。
- run/launch/stage/GPU/scope保持原卡；scope `97c6941ebded8e829d1ba28e5f71e868aa781e20b2075fd9062c5abe47ebaad1`。

[完整fresh准入](../reports/cara_v1_P1_memory50_fresh_refresh_r3_20261102.json)通过：MemAvailable=51.275921GiB≥50，原GPU空闲57°C、CPU亲和性、生产资产/runtime/权重/存储/独占均通过。中央预约及dispatch保持60秒新鲜窗，dispatch再次检查现场资源。

## 预算、检查与后续验收

[唯一预约](../reports/cara_v1_P1_memory50_central_reservation_r1_20261102.json)按已批准范围执行必要的一次24GPUh增量，cap226→250；原used197.02183603468436、旧16.5责任不变，预约19后available17.478163965315645。实际费用仍待原guardian终态按全段实耗唯一结算。

[检查安排](../reports/cara_v1_P1_acceptance_schedule_r2_20261102.json)：p1-2为11月3日00:46半程，p1-3为09:52全程验收；原硬截止10:44:28.784080、600秒停止释放余量保持。原p1准入检查已删除，禁止重复监控/派发。

完整146语义／最多142物理／5176pair／64同状态标签、19D22D和全部选择规则保持。完整成功退出、释放并唯一结算后才接受146/64/RGB，CPU仅一次至多32新对、封存FIT复用组成52位置，原FIT一次冻结，完整便携导出并本机绘图。GPU/CPU若仍活跃只恢复；失败保留全分母和费用，不冻结或自动下一卡。详见 [原运行验收交接](../plans/cara_next_stage_20261101/source_lifecycle/P1_POST_LAUNCH_HANDOFF_20261102.md)。原科学冻结、四旧CAL/曝光CHECK和最终/备用16保护输入均保持。
