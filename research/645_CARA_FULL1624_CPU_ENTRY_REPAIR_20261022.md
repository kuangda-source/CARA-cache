# 完整1624 CPU生产入口修复与原卡接续

2026-10-22 21:36终态收件确认原CPU R1于21:33:46退出1，未OOM，GPU提交为0。原完整数值检查通过：28条CPU路径、4060个重载格、26040次读出试验；实际CPU总耗时950.807秒。随后生产入口在构造Cosmos `SetupArguments` 时因缺少必填的 `output_dir` 失败。失败原件和独立失败接受均保留，不把数值通过记为完整生产通过。

修复只在可逆四卡适配层补显式 `stage/CPU-production-output`，原科学源码、四CAL请求、1624正式格、14完整路径、2030总格、13020GPU读出试验和已批12GPUh不变。生产边界检查提前到数值检查之前；三条完整CPU命令均保留。R2使用独立stage与物理run，原R1目录/失败日志不修改。13项适配检查通过，R6包包含修复；新完整CPU尚待实际启动和独立接受。

失败验收器现在对原身份/GPU隐藏且已退出的失败容器写出明确 `production_CPU_accepted=false`；成功仍须原完整数值、生产入口和实际FD/父进程/锁证明全部通过。

- 原终态：`reports/wc_policy_assets_full1624_fourcard_CPU_terminal_20261022_2136.json`
- 独立失败接受：`reports/wc_policy_assets_full1624_fourcard_CPU_r1_failure_accepted_20261022.json`
- 错误原件与原文件哈希：`reports/wc_policy_assets_full1624_fourcard_CPU_r1_failure_diagnosis_20261022.json`
- 新完整包：`manifests/wc_policy_assets_fourcard_full1624_package_r6_20261022.json`

BANK24已接受的六DEV结论保持644：A修正改善同状态误差；冻结z门控仍需加强，不能依据新DEV拟合阈值。完整1624将提供自动生成器所需的真实区间标签和动作价格，当前入口故障不改变这两项科学判断。

## R2实际启动与检查安排

source `94fe08832b8feb92ae6235c5b569d615950cf491` 已推送并读回GitHub同SHA。R2实际启动时间 `2026-10-22T21:47:16.094202+08:00`，PID793286/start946189945，容器PID793333；原R1四项原件SHA不变。启动后31秒GPU隐藏/只读容器正常，生产proof尚未落盘。launch原件 `reports/wc_policy_assets_full1624_fourcard_CPU_r2_launch_20261022.json`。

21:55（最早21:54:46）技术半程 `cara-1624-r2-cpu`；22:06（最早22:05:16）完整验收复用 `cara-bank24-2`，实际返回时间均已绑定。完整CPU通过后继续原12GPUh整卡及新GPU实际半程/全程安排；当前无新GPU提交。

21:49:55实际观察：R2真实Cosmos生产入口已通过，4请求/12拒绝控制、C/RF逆变换及容器FD/父进程/锁/GPU隐藏证明齐全；当前继续完整数值CPU，尚未整体接受，日志无错误。生产proof原件见reports/wc_policy_assets_full1624_fourcard_CPU_r2_production_boundary_20261022.json。

## R2实际技术半程

实际2026-10-22T21:55:39.368011+08:00半程收件：原PID/start与容器PID匹配，GPU隐藏/只读、无OOM/日志错误；生产proof与21:49:55原件SHA相同。数值报告与完整bundle尚未落盘，仍运行；目录清单仅记物理文件，不能当作已验收路径。一次半程cara-1624-r2-cpu已删除，原cara-bank24-2保持22:06完整验收，scope和GPU准入不变。半程原件 reports/wc_policy_assets_full1624_fourcard_CPU_r2_halfway_20261022_2155.json；技术核对 reports/wc_policy_assets_full1624_fourcard_CPU_r2_halfway_checked_20261022.json。
