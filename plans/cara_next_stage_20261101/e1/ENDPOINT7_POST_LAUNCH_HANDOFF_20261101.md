# E1 七角色46路径：唯一原运行交接

2026-11-01，Asia/Shanghai。用户直接批准“批准单次7 GPUh及本卡原账本事务”，本卡已唯一预约与启动。后续只恢复原句柄，任何连接UNKNOWN不代表允许重试。原生产源、配置和容器不能修改。

## 固定身份与时间

- run `cara-S-endpoint-seven46-r1-20261101`；launch `8d750a6de77d4d4fa2c84c4f97fff7f3`。
- source `af7c7d8e6d6348a1c87c5e13ce2c88bda86db16e`，1268文件payload原SHA保持；外部运输脚本单独版本化。
- 两卡 `GPU-cebf7119-cf03-23b9-e192-cd196332b704`，A6000 SM86。
- stage `/data20t/gaokuangda/worldcache_workspace/.sync/cara-S-endpoint-GPU-a6000-seven46-r1-20261101`；容器为该stage名加`-gpu`。
- 原guardian PID2664540/start676735584；CLI2664627/676735793；supervisor2664683/676735833；runner2664726/676735962。完整boot/namespace/command身份见原启动接受回执，不凭PID单独恢复。
- launch SHA `866315c096ede0d823cfddb76f5438a26c4f067f8785897a8c25df849326cb63`。
- 实际guardian开始02:47:33.142001；半程05:49（e1）、终验08:50（e1-2）；硬截止09:47:33.142001，09:37:33.142001进入600秒停止释放余量。时间均为11月1日北京时间。
- 硬7GPUh，90C；guardian全生命周期单调时钟唯一计费。cap226、旧16.5责任保持；预约后中央可用11.515811725GPUh。此处预算是启动时快照，不是后续新卡准入。

## 仅运维恢复

本地入口`scripts/cara_endpoint7_control_r1.py`；每次`--output`指定未存在的reports新JSON。远程固定SSH配置为`.sync/cara-fast-mainline-tailscale-20261030/ssh_config.budget_direct.private`；不输出秘密、不配置新入口。

```bash
.venv/bin/python scripts/cara_endpoint7_control_r1.py status --output reports/cara_endpoint7_runtime_<unique>.json
.venv/bin/python scripts/cara_endpoint7_control_r1.py central-status --output reports/cara_endpoint7_ledger_<unique>.json
```

status只导出46分母的COMPLETE/TECH_FAILED/RUNNING/NOT_REACHED计数、GPU/磁盘、原句柄与运行控制状态，不导出部分T_DD、质量或策略结果；encoded_video_files仅编码工件数，不等于完成路径。完整终态前不调用科学读者。只运行status/central-status，不再bind/admit/refresh/reserve/dispatch/prepare。连接失败保存UNKNOWN，恢复原句柄；不得更换UUID或重派。

四卡例外仅限本卡原中央账本读取、已完成预约恢复和最终实际结算；不检查四卡其他GPU/容器，不迁移账本。原中央operator缓存为`/tmp/endpoint7-central-operator-8d750a6de77d4d4fa2c84c4f97fff7f3`，已绑定原source闭包；禁止重复central-prepare。

## 原终态与唯一结算

status的`result.lifecycle.status`为`ORIGINAL_ENDPOINT_LIVE_OR_UNKNOWN`时继续恢复。完整`ORIGINAL_ENDPOINT_LIFECYCLE_CAPTURE`才进入原生命周期验证。成功失败均核验原全部PID-start退出、容器终态、独占/UUID锁释放、Default恢复或对应原释放证据、原guardian完整费用。

```bash
.venv/bin/python scripts/cara_endpoint7_control_r1.py settle --input reports/<original_terminal_status>.json --output reports/cara_endpoint7_final_settlement_<unique>.json
```

settle使用原stage固定模块`cara_s_endpoint_lifecycle_r1.financial_terminal`及`cara_endpoint7_central_r1.settle`。网络未知先`central-recover`保存原事务；既有同一账单返回原结算，不重复收费。守护者失败/超限不抹除原费用，不自动新卡。

## 成功后的完整CPU接受

只有完整46成功终态、原释放及唯一结算后，在**原stage源**中调用`cara_s_endpoint_pipeline_r1.released_artifacts(lifecycle, launch_sha, settlement)`：回读完整collection/原精度和13个RGB身份门，产生完整packet。不得提前读取或只接受子集；任何门失败保留失败记录，不派评分。

使用`cara_s_endpoint_scores_r1.bind_scorer(packet, environment)`绑定原离线Alex/PIQ资产；实际路径和SHA从本卡原资产声明及原评分准备回执核验，不猜测环境。调用`cara_s_endpoint_score_dispatch_r1.dispatch(stage, packet, config, registration_sha)`只一次16新对CPU；2线程、cpuset26,27、8GiB、无额外swap、硬2小时、无GPU。实际资源准入由原模块执行。

原CPU控制在`stage/endpoint-score-control`；输出为`outputs/cara-S-endpoint-seven46-r1-20261101/endpoint-score-CPU`；容器为stage名加`-endpoint-score-cpu`。若原intent存在，仅调用`cara_s_endpoint_score_dispatch_r1.recover(stage)`；不重复派发，不重评分B36原12对。保存原manifest/packet/result/execution/accepted字节与SHA，完整`ORIGINAL_COMPLETE28_SCORE_ACCEPTED`后用`scripts/analyze_cara_endpoint7_complete_r1.py`明确七份原输入并一次导图。

分析入口参数：`--card --collection --accepted --packet --config --result --execution --output`，可附`--figures`新目录。正式28逻辑位置＝16新对＋12原行；46物理、13RGB门、38clean timing，四旧CAL/seed0。双时钟、93帧曲线和原PNG/PDF/CSV一起保留；完整后按`plans/cara_next_stage_20261101/DECISION_AND_FREEZE_GATE.md`解释，不重选搜索赢家或覆写旧freeze。

CPU活跃则只恢复并调整同一e1-2，不新建检查。半程e1处理一次后删除；完整接受或真实失败收尾后删除e1-2和多余半程。无变化或不可行动保持安静，仅实质进展/完成/失败/需要用户行动通知。

## 原件与边界

- 启动接受：`reports/cara_endpoint7_actual_start_accepted_r1_20261101.json`
- 预约：`reports/cara_endpoint7_central_reservation_r1_20261101.json`
- 日程：`reports/cara_endpoint7_acceptance_schedule_r1_20261101.json`
- 独占启动观察：`reports/cara_endpoint7_original_context_r2_20261101.json`
- 审批前准备：`reports/cara_endpoint7_whole_CPU_accepted_r1_20261101.json`及单次审批卡。

A32/B36/S/Q/完整112/51搜索结果和原冻结保持，WC/RA保留FIT UNMATCHED；不读取保护TEST，不自动Euler或其它GPU卡。本次启动只是执行进展，尚无E1科学结果。
