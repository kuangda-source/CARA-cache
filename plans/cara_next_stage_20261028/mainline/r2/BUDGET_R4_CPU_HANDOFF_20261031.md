# 两卡 R4 完整 CPU 原运行交接

用户2026-10-31明确四卡维护期间只在两卡推进。不得探测/传输/提交四卡，不把未知连接当作原运行结束。

- 原启动：`reports/cara_budget_current_CPU_two_R4_launch_r1_20261031.json`，host two_card，PID 2240515，started_unix 1793379741.133709（Asia/Shanghai 01:02:21）。
- 唯一 stage：`/data20t/gaokuangda/worldcache_workspace/.sync/cara-budget-calibration-CPU-a6000-r4-20261031`；容器加 `-cpu`。
- 不可变源：`c2b079781ceb8a2d458f5eb3680fb267326a3927`；registration SHA `4a78fa4b80984cec016ffe178c0b9526110bbed2426b838e65b88a0aaabffd7a`；完整1176文件，3个增量发布文件。包 `.sync/cara-budget-two-R4-published-source-20261031`，回执 `reports/cara_budget_two_R4_published_source_r1_20261031.json`。
- 1CPU/4GiB/无额外swap，无GPU、network none、read-only root；工作2400秒，退出60秒。完整两种flow，各112设计路径/51双FIT查询、133成功与3预定失败；134执行控制+3规格控制。只检验实现，不读取或产生真实科学分数。
- 原 R3 失败容器及源保持；独立readiness CPU已26/26接受、退出0，不重复。禁止重启、改源、改限额或另派R4。

原状态短读：`python3 scripts/observe_cara_budget_current_R4_cpu_r1.py <全新本地报告路径>`。完整捕获：`python3 scripts/cara_budget_current_R4_cpu_transport_r1.py capture <全新本地报告路径>`。两者只访问两卡原入口，不使用 prepare。网络UNKNOWN只恢复同一stage/container，不派发新任务。任务私有SSH配置 `.sync/cara-fast-mainline-tailscale-20261030/ssh_config.budget_direct.private`，全局配置不改。

完整退出0、proof存在且原源/资源全部一致后，用 `scripts/accept_cara_budget_calibration_cpu_r3.py`，参数 `--capture <成功完整捕获> --original-launch reports/cara_budget_current_CPU_two_R4_launch_r1_20261031.json --package .sync/cara-budget-two-R4-published-source-20261031 --source-revision c2b079781ceb8a2d458f5eb3680fb267326a3927 --output reports/cara_budget_current_CPU_two_R4_accepted_r1_20261031.json`。该输出存在则只复核，不重建。失败保持原错误和终态，不能生成接受回执。

半程按原开始+20分钟上取整至01:23，全程检查为工作/退出窗口结束后01:44。若本轮更早已完整接受或失败收尾，删除两个多余检查；仍运行则仅保存一次运维检查并保留原终验。连接未知保留原检查承接，调整同一终验而不创建重复任务。检查ID与创建结果记 `reports/cara_budget_current_CPU_two_R4_schedule_r1_20261031.json`。

14GPUh只是设计方向，未批准实际GPU。原中央账本在四卡；维护期间不可用时，不复制旧快照建立第二账本或绕过fresh资金检查。先完成两卡CPU、真实存储、完整报价及执行链承接，再处理中央唯一账本可用性与具体GPU审批。cap226、旧16.5、A32/B36/S原结果和结算保持。

首次成功运维捕获：`reports/cara_budget_current_CPU_two_R4_operational_r2_20261031.json`。container ID `91bdcdc6a97c561548f40f32e82ca2f6df3ed71c03b2a3c8d9b99070f08b5f65`，CLI PID/start ticks `2240515/667464465`，worker `2240559/667464482`，boot ID `13495735-f30b-47a2-af0a-2496f5206a0b`，PID namespace inode `4026531836`。本次观测为running；后续仅按这些身份与原stage恢复。

## 已完成：只读原接受，不重跑

2026-10-31 01:17:53原容器exit0、无OOM；完整捕获为 `reports/cara_budget_current_CPU_two_R4_capture_r4_20261031.json`，独立接受为 `reports/cara_budget_current_CPU_two_R4_accepted_r1_20261031.json`。两种flow完整矩阵及134+3控制通过，实际GPU派发仍未接受。半程与终验均已删除，见 `reports/cara_budget_current_CPU_two_R4_check_cleanup_r1_20261031.json`。完整收尾见 `research/789_CARA_TWO_CARD_R4_CPU_ACCEPTED_AND_COMPLETE_COST_DRAFT_20261031.md`。
