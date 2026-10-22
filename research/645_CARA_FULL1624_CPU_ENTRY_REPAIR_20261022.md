# 完整1624 CPU生产入口修复与原卡接续

2026-10-22 21:36终态收件确认原CPU R1于21:33:46退出1，未OOM，GPU提交为0。原完整数值检查通过：28条CPU路径、4060个重载格、26040次读出试验；实际CPU总耗时950.807秒。随后生产入口在构造Cosmos `SetupArguments` 时因缺少必填的 `output_dir` 失败。失败原件和独立失败接受均保留，不把数值通过记为完整生产通过。

修复只在可逆四卡适配层补显式 `stage/CPU-production-output`，原科学源码、四CAL请求、1624正式格、14完整路径、2030总格、13020GPU读出试验和已批12GPUh不变。生产边界检查提前到数值检查之前；三条完整CPU命令均保留。R2使用独立stage与物理run，原R1目录/失败日志不修改。13项适配检查通过，R6包包含修复；新完整CPU尚待实际启动和独立接受。

失败验收器现在对原身份/GPU隐藏且已退出的失败容器写出明确 `production_CPU_accepted=false`；成功仍须原完整数值、生产入口和实际FD/父进程/锁证明全部通过。

- 原终态：`reports/wc_policy_assets_full1624_fourcard_CPU_terminal_20261022_2136.json`
- 独立失败接受：`reports/wc_policy_assets_full1624_fourcard_CPU_r1_failure_accepted_20261022.json`
- 错误原件与原文件哈希：`reports/wc_policy_assets_full1624_fourcard_CPU_r1_failure_diagnosis_20261022.json`
- 新完整包：`manifests/wc_policy_assets_fourcard_full1624_package_r6_20261022.json`

BANK24已接受的六DEV结论保持644：A修正改善同状态误差；冻结z门控仍需加强，不能依据新DEV拟合阈值。完整1624将提供自动生成器所需的真实区间标签和动作价格，当前入口故障不改变这两项科学判断。
