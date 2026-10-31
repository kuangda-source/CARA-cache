# 新单次14GPUh执行交接（已实际唯一启动）

用户明确批准“批准新单次 14 GPUh 及该卡原账本预约、结算”。完整112路径/51次双FIT查询，预计13.03253065964414GPUh，硬限14；仅两卡原A6000，cap226、旧16.5责任保持。

run `cara-budget-calibration-14gpuh-r2-20261031`；launch `323ef0d5e8eb4a91a1c8a4ba47c24b18`；源 `33fc2263405baaa77f6dbcfdfdfabedb20f066bc`；stage `/data20t/gaokuangda/worldcache_workspace/.sync/cara-budget-calibration-GPU-a6000-r3-20261031`；GPU `GPU-cebf7119-cf03-23b9-e192-cd196332b704`。原卡2b8058a77c7248f181acffddd399c257失败结算，禁止重放。

源准备回执 reports/cara_budget_successor_source_prepared_r1_20261031.json；授权 BUDGET_SUCCESSOR14GPUH_USER_AUTHORIZATION_20261031.json；完整CPU/报价 reports/cara_budget_successor_whole_CPU_composed_r1_20261031.json 和 cara_budget_successor_whole_quote_r1_20261031.json。

准入使用 scripts/cara_budget_successor_admission_r1.py 原CPU-admission-r1句柄；未知只capture，不再launch。控制使用 scripts/cara_budget_successor_control_r1.py。中央源码先单独central-prepare；成功后按fresh refresh → reserve → dispatch顺序。连接未知先status/central-status恢复原记录，不盲重派或重复计费。

实际开始后补原guardian/CLI/supervisor/runner PID与start ticks、launchSHA、容器身份、独占上下文和原账本预约。仅运维路径计数，无部分科学分数；实际起点后6.5h半程、13.25h终验、14h硬截止。成功失败均取原终态并唯一结算实耗，所有进程结束/释放后才按原完整接受入口验收112/51并一次冻结；不自动进入其它GPU卡。

终态保存control status完整lifecycle；settle用原launch SHA/capture；未知只central-status恢复。完整结果用固定源 scripts/accept_cara_budget_complete_r1.py，原project/stage/capture/settlement和expected-launch-sha256，--freeze只一次；若失败不读部分赢家、不写科学冻结。保留原存储、容器、日志与失败。完成或真实失败收尾后删除多余自动检查。

实际guardian开始：2026-10-31T16:45:04.590671+08:00；硬截止：2026-11-01T06:45:04.590671+08:00。launch SHA `d7862675a7a046924371d17d1793c7921429d9089861cb21f47cc89c7eecd526`。实际启动接受：reports/cara_budget_successor_actual_start_accepted_r1_20261031.json；四原PID/start ticks均在该回执。runner独占CUDA已核验，启动读取时0/112，52C。

原启动排程：半程14h于10月31日23:16，终验14h-2于11月1日06:01（Asia/Shanghai）；清单 reports/cara_budget_successor_acceptance_schedule_r1_20261031.json。原账本缓存 /tmp/successor14-central-operator-52fh798c，控制器settle必须传 --operator-receipt reports/cara_budget_successor_central_operator_ready_r3_20261031.json。预约后余额11.713456542526245GPUh；不是未来fresh余额。

半程已于2026-10-31 23:24:49实际检查：104/112完成、105条已尝试，原四PID/start ticks存活，原runner独占CUDA，76C，容器23.49/40GiB且无额外swap，输出盘剩余28,436,410,368字节。中央本卡仍唯一预约14GPUh，cap226、旧16.5保持，本轮未写账本。仅按6.662542小时墙钟和剩余8条估计23:55完成，已将同一个14h-2终验前移到2026-11-01 00:10；这只是运维估算，实际硬截止06:45:04.590671不变。半程14h已删除。原运行仍活跃，未读取部分科学结果、未结算或冻结。详见 reports/cara_budget_successor_halfway_summary_r1_20261031.json 和 cara_budget_successor_halfway_check_cleanup_r1_20261031.json。

2026-11-01终验承接：原GPU于10月31日23:56:56.112259退出释放，完整112/112、退出0、四原句柄结束、锁释放及Default恢复。原guardian实耗7.197644817485577GPUh已中央唯一结算；原终态 reports/cara_budget_successor_final_capture_r1_20261101.json、结算 cara_budget_successor_final_settlement_r1_20261101.json、释放独立接受 cara_budget_successor_final_release_accepted_r1_20261101.json。不得重复结算或启动GPU。

完整CPU读者已于11月1日00:18:07唯一启动：stage `/data20t/gaokuangda/worldcache_workspace/.sync/cara-budget-successor-accept-CPU-a6000-r1-20261101`，容器同名加`-cpu`；容器PID2654005、reader PID2654036/start ticks675839119。2CPU/8GiB、零额外swap、network none、GPU隐藏，3600秒工作上限。首轮握手失败后，先明确stage/精确容器均不存在才执行首次CPU启动；原失败与缺席回执保留。最新原句柄 reports/cara_budget_successor_final_CPU_capture_r3_20261101.json；只运行 `python3 scripts/cara_budget_successor_accept_transport_r1.py capture --output 新回执.json`，禁止prepare或重复派CPU。

该CPU容器调用原GPU stage固定源的 `accept_cara_budget_complete_r1.py --freeze`，完整原RGB/生成工件/51查询通过后才一次冻结。00:20观察原reader仍活跃，未取最终分数。若成功，capture返回accepted/frozen/collection原始字节与SHA，保存并汇总即可，禁止重跑读者。若失败保留原终态、不得假定赢家接受。14h-2已调整为11月1日00:30继续恢复，完整接受或真实失败收尾后删除；半程14h已删除。汇总 reports/cara_budget_successor_GPU_settled_CPU_running_r1_20261101.json。

2026-11-01最终完成：原CPU于00:25:44.617394退出0，完整112路径/51查询已接受并一次冻结。原终态 reports/cara_budget_successor_final_CPU_capture_r4_20261101.json，原接受 cara_budget_successor_complete_accepted_r1_20261101.json；原冻结副本 BUDGET_SUCCESSOR14_FROZEN_MASK_R1_20261101.json，SHA f1e0b08b9dc31fd9cd3c02a80b01cbb874e9348003ec6aad3a5aa9f82d848c86。第39次HC查询选中19D，双FIT RGB MSE由0.04275328855降至0.02412058939（43.5819%）；仅是两个旧FIT的校准目标变化，尚无CHECK/新输入/LPIPS或部署时延结论。完整汇总 reports/cara_budget_successor_complete_summary_r1_20261101.json、research/817_CARA_BUDGET_SEARCH_COMPLETE_ACCEPTANCE_AND_FROZEN_WINNER_20261101.md。14h与14h-2均删除；不再捕获已完成句柄、重跑CPU读者或再次结算。后续只复用已接受原件；端点新卡仍需准备和独立批准。
