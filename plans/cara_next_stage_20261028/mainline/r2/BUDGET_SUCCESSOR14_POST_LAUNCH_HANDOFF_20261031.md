# 新单次14GPUh执行交接（已批准，尚待实际启动）

用户明确批准“批准新单次 14 GPUh 及该卡原账本预约、结算”。完整112路径/51次双FIT查询，预计13.03253065964414GPUh，硬限14；仅两卡原A6000，cap226、旧16.5责任保持。

run `cara-budget-calibration-14gpuh-r2-20261031`；launch `323ef0d5e8eb4a91a1c8a4ba47c24b18`；源 `33fc2263405baaa77f6dbcfdfdfabedb20f066bc`；stage `/data20t/gaokuangda/worldcache_workspace/.sync/cara-budget-calibration-GPU-a6000-r3-20261031`；GPU `GPU-cebf7119-cf03-23b9-e192-cd196332b704`。原卡2b8058a77c7248f181acffddd399c257失败结算，禁止重放。

源准备回执 reports/cara_budget_successor_source_prepared_r1_20261031.json；授权 BUDGET_SUCCESSOR14GPUH_USER_AUTHORIZATION_20261031.json；完整CPU/报价 reports/cara_budget_successor_whole_CPU_composed_r1_20261031.json 和 cara_budget_successor_whole_quote_r1_20261031.json。

准入使用 scripts/cara_budget_successor_admission_r1.py 原CPU-admission-r1句柄；未知只capture，不再launch。控制使用 scripts/cara_budget_successor_control_r1.py。中央源码先单独central-prepare；成功后按fresh refresh → reserve → dispatch顺序。连接未知先status/central-status恢复原记录，不盲重派或重复计费。

实际开始后补原guardian/CLI/supervisor/runner PID与start ticks、launchSHA、容器身份、独占上下文和原账本预约。仅运维路径计数，无部分科学分数；实际起点后6.5h半程、13.25h终验、14h硬截止。成功失败均取原终态并唯一结算实耗，所有进程结束/释放后才按原完整接受入口验收112/51并一次冻结；不自动进入其它GPU卡。

终态保存control status完整lifecycle；settle用原launch SHA/capture；未知只central-status恢复。完整结果用固定源 scripts/accept_cara_budget_complete_r1.py，原project/stage/capture/settlement和expected-launch-sha256，--freeze只一次；若失败不读部分赢家、不写科学冻结。保留原存储、容器、日志与失败。完成或真实失败收尾后删除多余自动检查。
