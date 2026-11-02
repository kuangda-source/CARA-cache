# 已启动的唯一 P1 修复后 R2：原句柄与验收

先读 [实际启动](../../../reports/cara_v1_P1_successor_actual_start_accepted_r2_20261102.json)、[三个检查](../../../reports/cara_v1_P1_successor_acceptance_schedule_r2_20261102.json)、[新授权](V1_P1_SUCCESSOR_SINGLE19_AUTHORIZATION_R2.json) 和 [CPU/source/storage准备](../../../research/864_CARA_P1_PUBLICATION_RPC_REPAIRED_CPU_AND_SUCCESSOR_READY_20261102.md)。本卡已实际开始，禁止再prepare、bind、admit、refresh、reserve、dispatch、重启、换卡或改源/配置。UNKNOWN只恢复原句柄。

## 固定身份和原预算

- run：cara-source-lifecycle-V1-P1-full146-r2-20261102
- launch：498503f9cfd249f1aab929da18f04e10
- source：8cc9b30a2b08b25c23fa7c38ef63a7b64d456f99
- registration：8367f1f9877a495a2dd203c711f6d498155a64135a00da21a22f8a16aef49884
- stage：/data20t/gaokuangda/worldcache_workspace/.sync/cara-source-lifecycle-V1-P1-GPU-a6000-full146-r2-20261102
- GPU：two_card GPU-cebf7119-cf03-23b9-e192-cd196332b704
- container：629379b320ee11ce938534aa7528a237cd9bee9bb923affb2e47df3a0ed867cf
- guardian3600207/start_ticks692524957；CLI3600299/692525281；supervisor3600355/692525330；runner3600402/692525518。
- boot13495735-f30b-47a2-af0a-2496f5206a0b，host PID namespace4026531836。

原guardian实际开始 **2026-11-02T22:39:06.791125+08:00**，完整146语义／最多142物理／5176模型pair／64同状态shadow标签、19D22D和原科学scope不变。预计18.050670925709685GPUh，硬19；**原硬截止2026-11-03T17:39:06.791125+08:00，停止释放截止2026-11-03T17:29:06.791125+08:00**。90°C、GPU40GiB/CPU8GiB且不swap、每内部查询新鲜12GiB、独立64GiB/48MiB保持。50GiB仅启动前门，运行中不重做准入或据此停止原运行。

用户已明确“批准新单次19GPUh及本卡账本事务”。完整19.88194GiB生产资产内容和后续stat/现场门已通过；首个dispatch因内存门在GPU intent前拒绝，status确认无原GPU意图后恢复同一个预约，后续fresh资源通过才唯一派发。不是重启旧卡、重建源或重复预约。新卡已唯一预约19，cap250不增额；used201.95503799855743、旧16.5、预约后available12.54496200144257保持。原R1失败费用4.933201964已结算，不能重复收费或复用其部分结果。

## 原入口与三个检查

仅本机 `python3 scripts/cara_p1_successor_control_r2.py status/central-status --output 新唯一回执`。原Tailscale私有profile保持，按用户最新入口指令，不自动切LAN、不改Clash/路由。新四卡operator115文件已准备，持久化路径 `/data20t/gaokuangda/worldcache_workspace/.sync/source-lifecycle-P1-central-operator-498503f9cfd249f1aab929da18f04e10`；禁止central-prepare，四卡只做本卡原账本事务，不做实验、不迁移账本、不增cap，网络未知先central-recover。RPC输出隔离已修复。

三个单次安静线程heartbeat：p1-r2-quarter **11月3日03:10**；p1-r2-half **07:41**；p1-r2终验 **16:48**。quart/half只原句柄、146分母运维进度计数、温度、资源、独占及账本，仍运行保存一次检查，不读取部分T_DD、LPIPS或分析计划。可依据计数/实际墙钟前移同一个终验，不创建重复检查。quart/half各处理一次删除自己；原运行/原CPU仍活跃保留并调整同一终验。无变化或不可行动保持安静，完成/失败/重要状态变化/需用户操作才通知。

## 原终态、释放和唯一实耗

status必须读原完整terminal lifecycle和launch SHA，核原guardian/CLI/supervisor/runner以及FIT服务均结束、容器终态、锁释放与Default恢复。成功失败都 `settle --input 原terminal status --output 新回执`，由原guardian单调全段实耗唯一结算。网络UNKNOWN只恢复原事务，不重复收费；原19硬限不因监控时点移动。失败保存所有未达分母、原费用，不评分/冻结或自动下一卡；完整收尾后删除全部剩余检查。

## 完整成功之后的一次CPU验收与导出

完整GPU成功退出、释放且唯一结算后，才固定source在原stage调用 `wcomr.cara_source_lifecycle_p1_artifacts_r1.released_artifacts(capture,expected_launch_sha256,settlement)` 完整验证146语义/最多142物理/64标签与原等价/RGB门。保持同一原stage/source，不重新采集或重选旧冻结赢家。

以原internal-score-environment.json绑定 `wcomr.cara_source_lifecycle_p1_scores_r1.bind_post_scorer`，再 `wcomr.cara_source_lifecycle_p1_score_dispatch_r1.dispatch(stage,packet,config,registration_sha256)` 仅一次至多32新CPU对，复用本卡封存内部FIT组成52位置。post-score intent已存在、原CPU活跃或UNKNOWN只 `recover(stage)`，不重复派发，不重评旧指标/原R1部分FIT。

全部52接受后 `wcomr.cara_source_lifecycle_p1_report_r1.complete(stage)` 形成原双时钟/93帧/实际校准费用完整分析和一次原FIT冻结；已有seal只接受相同原字节，不因只读观测时间更改重跑读者。原 `scripts/cara_source_lifecycle_p1_result_bundle_r1.py export --stage 原stage` 导出原report/analysis/freeze字节与SHA，取回后在本机按独立SHA render，使用已有.sync/cara-p0-plot-python绘图环境，不在服务器安装绘图库。

按13角色/52位置、输入等权主LPIPS和原工程筛选解释。四旧CAL/曝光CHECK不是新泛化证据；保留所有A32/B36/S/Q/旧RGB-MSE搜索冻结、WC/RA FIT UNMATCHED、最终/备用16保护输入。更新canonical/完整研究记录，精确提交推送，完成后删除全部剩余检查。禁止自动P2/V2或其它GPU卡。
