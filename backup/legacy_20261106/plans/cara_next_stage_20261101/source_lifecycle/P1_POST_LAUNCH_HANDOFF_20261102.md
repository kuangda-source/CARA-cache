# P1 原单次失败收尾（已释放、唯一结算，禁止重派）

原单次P1已于 **2026-11-02 20:40:28.311146 Asia/Shanghai** 失败退出，原因是第三个内部FIT查询目录先于request.json发布被消费者视为残缺。完整146语义未完成，仅38物理请求完成；未查看部分科学分数、未后评分或冻结。原进程/服务/锁已结束，Default恢复，实耗 **4.933201963873063 GPUh** 已唯一结算。见 [863完整故障记录](../../../research/863_CARA_P1_QUERY_PUBLICATION_RACE_FAILURE_AND_UNIQUE_SETTLEMENT_20261102.md)、[收尾原件](../../../reports/cara_v1_P1_original_failure_complete_acceptance_r1_20261102.json) 和 [关闭的检查清单](../../../reports/cara_v1_P1_acceptance_schedule_closed_r4_20261102.json)。

p1-quarter、p1-2、p1-3全部删除。不要继续轮询、prepare、dispatch、评分或再次收费；原单次批准已消耗，不授权重跑。下一步仅准备CPU发布原子性和RPC输出包装修复，新的GPU整卡另审。

以下保留原执行身份与原合同；原19GPUh硬截止属于已结束卡。

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

## 已完成的运维恢复与检查

原quarter实际capture、释放接受、operator恢复与原唯一结算都在863及原回执中。原/tmp中央缓存缺失后仅精确恢复同115源码，central-status回读原账本/预约未变，再由原settle完成费用。四卡只做本卡原中央事务，没有实验或迁移账本。当前cap250、used201.95503799855743、旧reserved16.5、available31.54496200144257。

原Tailscale入口按用户要求保持；没有改Clash、路由或服务。quarter/half/terminal均已删除，无自动下一卡。保留所有原失败、A32/B36/S/Q/旧搜索冻结、WC/RA FIT UNMATCHED、旧CAL/曝光CHECK及最终/备用16保护输入。

## 原终态、释放与费用已接受

`reports/cara_v1_P1_quarter_original_status_r1_20261102.json` 的原launch SHA和完整lifecycle由原financial_terminal核验，随后 `reports/cara_v1_P1_original_failure_central_settlement_r1_20261102.json` 的原settle/audit_settlement通过。不得再次收费或将未用19GPUh余额当重派许可。

## 原成功分支存档（本次失败禁止进入）

下列成功接受流程本次未执行；不得对本次失败工件调用released_artifacts、score dispatch或freeze。

完整GPU成功释放且唯一结算后，在原stage固定source调用wcomr.cara_source_lifecycle_p1_artifacts_r1.released_artifacts(capture,expected_launch_sha256,settlement)。它先验证release，再完整读取146/最多142物理、64标签、所有等价/RGB与原封存FIT。不得在此前查看部分科学分数。

用原internal-score-environment.json的torch_home/piq_site/weights_sha256调用wcomr.cara_source_lifecycle_p1_scores_r1.bind_post_scorer，随后原wcomr.cara_source_lifecycle_p1_score_dispatch_r1.dispatch(stage,packet,config,registration_sha256)仅派一次至多32新对。post-score-control/intent.json存在则只recover(stage)，不得重派。原bootstrap和固定CPU资源/截止/原PID-start ticks必须验证。完整52接受时已封存内部FIT原样复用，不重评旧指标或重选任何原FIT赢家。

之后原wcomr.cara_source_lifecycle_p1_report_r1.complete(stage)完整汇总输入等权结果/双时钟/93帧/实际校准费用，一次冻结原FIT计划；原分析seal消除只读观测时间变化，已有结果只接受相同原字节。使用原scripts/cara_source_lifecycle_p1_result_bundle_r1.py export --stage 原stage导出完整report/analysis/freeze原字节和SHA；取回原导出包后在本机按独立SHA render，不在服务器安装绘图库、不再评分。固定13角色52位置及FIT/曝光CHECK/四旧CAL分别解释，工程筛选不是论文成立线。更新canonical、研究记录及原件引用，精确提交推送；完整接受后删除终验和多余检查。
