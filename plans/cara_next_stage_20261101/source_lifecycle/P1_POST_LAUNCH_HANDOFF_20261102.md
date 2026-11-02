# P1 原运行与完整验收交接

唯一 P1 已于 **2026-11-02 15:44:28.784080 Asia/Shanghai** 实际开始。先读 [实际启动原件](../../../reports/cara_v1_P1_actual_start_accepted_r2_20261102.json) 和 [半程/终验](../../../reports/cara_v1_P1_acceptance_schedule_r2_20261102.json)。禁止再 dispatch、重启、改源或改资源配置；UNKNOWN 仅恢复原句柄。

## 已冻结的执行身份

- run：cara-source-lifecycle-V1-P1-full146-r1-20261102
- launch：a2b1dcf993774897902a5f0cc0858220
- source：6bf82dd262c082a6786588d39d9ea23da74cc907
- registration：9bf9a98db7308f3fa0b867e9ec0a928c8ea0d7389c31f394fd7bda5f3715dc35
- scope：97c6941ebded8e829d1ba28e5f71e868aa781e20b2075fd9062c5abe47ebaad1
- stage：/data20t/gaokuangda/worldcache_workspace/.sync/cara-source-lifecycle-V1-P1-GPU-a6000-full146-r1-20261102
- two_card A6000：GPU-cebf7119-cf03-23b9-e192-cd196332b704
- container：17f4c9b55d6718569733ebf6ac5fbf6c1efd70d98c06c0cd87189abfd203035e
- guardian PID/ticks：3356855 / 690037143；CLI 3356977 / 690037544；supervisor 3357037 / 690037602；runner 3357113 / 690037864。
- boot：13495735-f30b-47a2-af0a-2496f5206a0b；host PID namespace 4026531836。

完整146语义／最多142物理／5176模型pair／64同状态标签、自动19D/22D、嵌套消融和同实际费用LPIPS搜索保持。硬限19GPUh，90°C，停止释放余量600秒。**硬截止2026-11-03 10:44:28.784080；停止释放截止10:34:28.784080。** GPU40GiB/CPU8GiB且不swap，每次内部查询仍须新鲜12GiB可用内存。初始50GiB仅在启动前工程修订，CPU增量和原字节封存见 [修订回执](../../../reports/cara_v1_P1_source_memory50_amended_r2_20261102.json)；现在不得再次修改。原dd2/bded及R1授权/CPU证明均保留。

## 运维恢复与监控

本机仅调用 `scripts/cara_source_lifecycle_p1_memory50_control_r2.py status/central-status`，每次输出新的唯一reports路径。用户切手机热点并明确要求原Tailscale，使用 `.sync/cara-fast-mainline-tailscale-20261030/ssh_config.p0_qos_none.private`；不要自动切LAN、修改Clash/路由或泄露stdin凭据。原GPU/CPU/存储均已启动或结束，只恢复原件，禁止 prepare。

`p1-2` 半程为11月3日00:46；`p1-3` 终验为09:52。无变化或不可行动保持安静；半程只查原句柄、完整146分母的运维计数、温度、资源、独占和账本。可用计数/墙钟前移同一终验，禁止部分科学结果和重复检查。原准入p1在两个新检查验证后删除。

中央已唯一预约19，按用户批准必要的一次24GPUh增量使cap226→250；used197.02183603468436、旧16.5责任保持，预约后available17.478163965315645。见 [预约原件](../../../reports/cara_v1_P1_memory50_central_reservation_r1_20261102.json)。四卡仅本卡原中央事务，不做实验、不迁账本。原operator115文件缓存不变，禁止 central-prepare。所有A32/B36/S/Q/旧RGB-MSE搜索冻结、WC/RA FIT UNMATCHED、四旧CAL/曝光CHECK范围及最终/备用16保护输入保持。

## 原终态、释放与唯一费用

成功失败都先用memory50 control的status取原完整terminal lifecycle与launch SHA，检查原guardian容器终态、CLI/runner退出、锁释放与Default恢复。settle --input 原terminal status回执，唯一结算原guardian全段实耗。网络UNKNOWN先恢复原中央事务；不得再次收费。四卡只做本卡原中央事务，不跑实验、不迁账本。失败保留全分母和实际费用，不冻结、不评分、不自动下一卡；收尾后删除剩余检查。

## 完整成功后的CPU接受与导出

完整GPU成功释放且唯一结算后，在原stage固定source调用wcomr.cara_source_lifecycle_p1_artifacts_r1.released_artifacts(capture,expected_launch_sha256,settlement)。它先验证release，再完整读取146/最多142物理、64标签、所有等价/RGB与原封存FIT。不得在此前查看部分科学分数。

用原internal-score-environment.json的torch_home/piq_site/weights_sha256调用wcomr.cara_source_lifecycle_p1_scores_r1.bind_post_scorer，随后原wcomr.cara_source_lifecycle_p1_score_dispatch_r1.dispatch(stage,packet,config,registration_sha256)仅派一次至多32新对。post-score-control/intent.json存在则只recover(stage)，不得重派。原bootstrap和固定CPU资源/截止/原PID-start ticks必须验证。完整52接受时已封存内部FIT原样复用，不重评旧指标或重选任何原FIT赢家。

之后原wcomr.cara_source_lifecycle_p1_report_r1.complete(stage)完整汇总输入等权结果/双时钟/93帧/实际校准费用，一次冻结原FIT计划；原分析seal消除只读观测时间变化，已有结果只接受相同原字节。使用原scripts/cara_source_lifecycle_p1_result_bundle_r1.py export --stage 原stage导出完整report/analysis/freeze原字节和SHA；取回原导出包后在本机按独立SHA render，不在服务器安装绘图库、不再评分。固定13角色52位置及FIT/曝光CHECK/四旧CAL分别解释，工程筛选不是论文成立线。更新canonical、研究记录及原件引用，精确提交推送；完整接受后删除终验和多余检查。
