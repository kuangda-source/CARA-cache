# 730｜COMMON_LONG6 R2进程扫描竞态修复与完整重启

2026-10-27用户明确“修复一下然后重新启动”。沿原完整6路径，2warm+2OFF+2ON、12状态84读出、228pairs456CFG、186额外head pairs、一次load；原α、六强对照、最终部署预算和累计226保持，IG暂停。旧R1失败完整保留，精确0.9401914451307514GPUh已中央结算；不拼接旧4路径。

## 修复及验证

只将MPS `/proc/*/comm`扫描中的`ProcessLookupError`纳入已消失进程处理，与原FileNotFoundError一致。权限不足仍返回未知MPS并拒绝准入；EIO仍抛错；真实MPS、GPU PID身份未知仍拒绝。未更改GPU身份、刷新决策、模型数值或独占要求。

5项真实observe函数CPU故障测试覆盖ESRCH/ENOENT重复观察通过、权限失败、其他I/O失败、MPS拒绝、GPU未知身份拒绝。R2独立run、stage、卷、跨盘日志、子账本job和中央包，不覆盖R1。监督、评分、终态和财务R2模块保持科学合同，增加观察器源SHA与故障测试到CPU接受闭包。

初次R6 CPU包装漏掉重命名后的数值测试文件，双端在加载前退出；失败回执保留，无GPU。补齐文件并新增本地包装存在检查后，R7执行完整组合验证。其结果绑定后才允许派发。

## 授权与完整报价

[授权报价](../reports/cara_common_long6_R2_authorization_and_quote_20261027.json)：仍预计2.608114273192671GPUh、硬3GPUh；费用包含一次加载、全部warm/formal、shadow/teacher/head、保存/解码/清理，GPU释放后CPU2核8GiB最多1h重算评分。中央准入须证明旧R1已精确结算且无另一自有昂贵任务运行，保留16.5未知责任。报价和预算不因修复放宽。

实际新launch与检查时间以本文件后续追加及docs/project_status.json为准。CPU通过不是GPU或科学接受；有intent后只能原句柄recover，禁止再launch。
