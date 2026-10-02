# wc-mid-coverage-r1：初始化检查位置错误，失败结算与CPU修正

2026-10-03；本卡唯一GPU提交已结束。结论：TECH_BLOCKED，未开始去噪前向、prefix、QKV或算子诊断，coverage实际为0/104、case0/312。不是中间刷新、状态恢复、稀疏数值或方法质量的负结果。第二GPU窗口由协调线程根据本次终态另行分配，本轮不自动r2，不采集专家残差。

## 终态、成本与释放

- run：`wc-mid-coverage-r1`；部署source `375261a8d4efa7bb7f9b330f526f114ac1c94b53`，独立stage/输出，原上游与runtime未改。
- supervisor退出码：1；runner错误：`ValueError: WC protocol differs`，模型构建后、首次generate之前触发。
- 监督2626531、timeout2626549、runner2626550现场均已不存在；global f1.lock可取得；所选A6000释放到24MiB/无compute。监控实际看到本runner。
- 全监督墙钟172.90053822286427秒，包括加载/失败/退出与释放；增量0.04802792728412897GPUh。预留1200秒按实际结算，累计3.959780495795162/12GPUh、29jobs，余8.040219504204838GPUh，无inflight。历史28jobs/已用未清零，未追加额度。
- [失败/释放审计](../reports/wc_mid_coverage_r1_audit_20261003.json)、[supervisor终态](../reports/wc_mid_coverage_r1_supervisor_20261003.json)、[runner原始回执](../reports/wc_mid_coverage_r1_runner_20261003.json)、[汇总](../reports/wc_mid_coverage_r1_summary_20261003.json)、[权威账本副本](../reports/budget.json)。审计核对部署payload与全部实际回执/成本/PID/锁/monitor；没有QKV可作raw复核，不把零样本审计写成覆盖通过。

## 原因与修正范围

runner误把`worldcache_num_steps==70`放在Inference初始化后。原冻结setup配置为35，原始运行回执也记录构建时35/probe_depth2。官方`video2world.py`在每次请求开始前执行`target_steps=num_steps*2`并重置cache，这之后才是70-call horizon。这个生命周期在此前9项CPU恢复/asset/import检查中未覆盖，是新增runner的检查位置错误；没有改变官方35请求步、36实际UniPC步、72CFG调用、70horizon合同。

修正只检查构建时与冻结setup一致，并在首次实际net.forward核验请求horizon/probe。新增官方请求重置源码hash `59aa9e236a5e7e26490f5cfcb94ab95ce911d9c38eba61dd8aef7d067e458a95`，独立CPU控制解析并实际执行该冻结源码的reset AST块：构建35时请求门拒绝，reset后70/计数与两路cache清空时通过；请求36或probe改变仍拒绝。没有为了通过检查改原上游、setup或硬设请求70。

本地9项针对性控制通过（原8+请求生命周期），实际Cosmos Torch2.7.1+cu128的新请求reset CPU控制通过，CUDA未初始化、账本不变。[新实际CPU回执](../reports/wc_mid_request_lifecycle_cpu_20261003.json)。这不是第二次GPU验收或新完整pipeline分叉验收。

原失败stage/source/config/logs保留不动；修正在当前仓库及独立CPU stage中准备，尚未部署新GPU窗口。此前完整资产/来源和UniPC恢复CPU回执保留原source，不把它们改标为修订runner的全新实机验收。

## 下一入口

先由唯一协调线程分配第二GPU卡；届时新identity/source/stage必须重新执行完整新配置/资产/实际接口门、fresh UUID/VRAM/compute/global锁以及12h余额检查。仍为call25/26、35/36×全26深层、匹配prefix与状态恢复的有界覆盖，不进入H0/H1或RV，不重复原r1。原r1失败成本与0覆盖保留在分母；不把修正CPU通过当研究进展正结果。
