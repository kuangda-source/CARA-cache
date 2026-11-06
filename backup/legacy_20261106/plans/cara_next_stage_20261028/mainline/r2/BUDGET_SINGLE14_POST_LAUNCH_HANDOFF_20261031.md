# 单次14GPUh原运行：失败已关闭，禁止重派

先读 `research/795_CARA_SINGLE14_ORIGINAL_FAILED_SETTLED_AND_EXEC_HANDOFF_CPU_REPAIR_20261031.md` 和 `reports/cara_budget_single14_failed_settled_closeout_r1_20261031.json`。

唯一launch `2b8058a77c7248f181acffddd399c257`；run `cara-budget-calibration-14gpuh-r1-20261030`；原源 `8a4eb813e5122cc450d980be45d4c3816ad9b4ae`；stage `/data20t/gaokuangda/worldcache_workspace/.sync/cara-budget-calibration-GPU-a6000-r2-20261031`；GPU `GPU-cebf7119-cf03-23b9-e192-cd196332b704`；launch SHA `524487887300d0822cf36f05c1263c844fb2e172ea98b36212c9812834db06b8`。

实际 2026-10-31T16:00:22.729488+08:00 → 2026-10-31T16:00:31.064562+08:00，原8.335秒/0.002315298004800247GPUh已唯一结算。0/112路径，容器退出1、无OOM、四个原进程结束、锁释放、Default恢复。原结算恢复见 `reports/cara_budget_single14_central_settlement_recovery_r2_20261031.json`，不得重新预约、启动或结算。没有半程/终验自动化需要删除。不可调用完整科学接受/冻结器，因为原容器失败。

原guardian PID2364428/ticks672852558；CLI2364515/672852746；supervisor2364570/672852789；runner2364614/672852945；boot13495735-f30b-47a2-af0a-2496f5206a0b，namespace4026531836。原容器53a3c5ed9751abb2fb549271bd2093a021d00407ac22d6c6632a3017db5cb236。

根因是exec改变命令哈希，被误判为不同runner。候选本地修复经真实Linux exec的8项控制接受，但未组下一张整卡，不授予任何新GPU权限。保留原stage/source/日志及64GiB卷/48MiB journal，不能清零旧journal后重用单次身份。若继续，只做CPU准备和新卡可审阅范围/报价；再次14GPUh必须单独批准。

四卡仅原账本/句柄读取和本卡预约/结算获准；没有四卡实验许可或账本迁移许可。A32/B36/S/Q与原科学冻结保持。
