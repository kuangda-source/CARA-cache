# 730｜COMMON_LONG6 R2进程扫描竞态修复与完整重启

2026-10-27用户明确“修复一下然后重新启动”。沿原完整6路径，2warm+2OFF+2ON、12状态84读出、228pairs456CFG、186额外head pairs、一次load；原α、六强对照、最终部署预算和累计226保持，IG暂停。旧R1失败完整保留，精确0.9401914451307514GPUh已中央结算；不拼接旧4路径。

## 修复及验证

只将MPS `/proc/*/comm`扫描中的`ProcessLookupError`纳入已消失进程处理，与原FileNotFoundError一致。权限不足仍返回未知MPS并拒绝准入；EIO仍抛错；真实MPS、GPU PID身份未知仍拒绝。未更改GPU身份、刷新决策、模型数值或独占要求。

5项真实observe函数CPU故障测试覆盖ESRCH/ENOENT重复观察通过、权限失败、其他I/O失败、MPS拒绝、GPU未知身份拒绝。R2独立run、stage、卷、跨盘日志、子账本job和中央包，不覆盖R1。监督、评分、终态和财务R2模块保持科学合同，增加观察器源SHA与故障测试到CPU接受闭包。

初次R6 CPU包装漏掉重命名后的数值测试文件，双端在加载前退出；失败回执保留，无GPU。补齐文件并新增本地包装存在检查后，R7执行完整组合验证。其结果绑定后才允许派发。

## 授权与完整报价

[授权报价](../reports/cara_common_long6_R2_authorization_and_quote_20261027.json)：仍预计2.608114273192671GPUh、硬3GPUh；费用包含一次加载、全部warm/formal、shadow/teacher/head、保存/解码/清理，GPU释放后CPU2核8GiB最多1h重算评分。中央准入须证明旧R1已精确结算且无另一自有昂贵任务运行，保留16.5未知责任。报价和预算不因修复放宽。

实际新launch与检查时间以本文件后续追加及docs/project_status.json为准。CPU通过不是GPU或科学接受；有intent后只能原句柄recover，禁止再launch。

## R7双端完整通过及实际启动

两卡与四卡R7均完整退出0并独立接受，各12路径/24状态/168评分、4生命周期、6存储边界、2财务终态测试和新增5竞态测试全部通过。见[两卡接受](../reports/cara_common_long_combination_two_card_CPU_accepted_r7_20261027.json)、[四卡接受](../reports/cara_common_long_combination_four_card_CPU_accepted_r7_20261027.json)。原R1保存的部分状态不分析、不拼接；R2是完整工程重跑，不把重复采样计作额外独立证据。

- 唯一[launch-ref](../reports/cara_common_long6_A6000_launch_R2_20261027.json)：`71904d09-63b2-40c1-80de-0ae5da68c477`。
- source：`0fa5c4710f110be85417e7727790b3a564b4ebd3`；run `cara-common-long-newstates6-r2`。
- stage：`/data20t/gaokuangda/worldcache_workspace/.sync/cara-common-long6-a6000-r2-20261027`，[stage-ref](../reports/cara_common_long6_A6000_stage_R2_20261027.json)。
- GPU1：`GPU-cebf7119-cf03-23b9-e192-cd196332b704`。guardian333442/start639775827；supervisor333514/start639775973；runner333562/start639776151/UID1004。
- 实际20:07:34.756670 +08派发，20:07:42.722938确认唯一真实CUDA上下文。

[准入观察](../reports/cara_common_long6_A6000_admission_R2_verified_20261027.json)：模型加载中，39独占样本0违规，最大间隔2.232秒；独立卷约31.2GiB可用，跨盘日志正常。新32GiB卷与`/home/gaokuangda/cara_control/common-long6-r2/control.journal`48MiB日志已真实绑定，不覆盖R1。

[中央实际准入](../reports/cara_common_long6_A6000_R2_central_admission_confirmed_20261027.json)：used173.20596615932914/reserved19.5/available33.29403384067086/cap226。R2唯一3GPUh外部包与两卡子账本同一笔费用，旧16.5未知责任保留。

## 自动检查与原句柄接续

北京时间10月27日21:27半程（`cara-r2`）、23:50终态（`cara-r2-2`）。预测22:44采集完成、GPU释放后最多1h CPU评分，约23:44可收件；预测不是保证。3h硬GPU上限约23:08，CPU最迟可能跨到10月28日00:08，届时按实际状态调整同一检查。

控制器改用`python scripts/wc_two_card_common_long6_gpu_r2.py`：

- `capture --launch-ref reports/cara_common_long6_A6000_launch_R2_20261027.json --mode halfway --output 新原件`只观察技术状态；容器和PID终态优先于可能停留的旧health。
- UNKNOWN：`recover --stage-ref reports/cara_common_long6_A6000_stage_R2_20261027.json --output 新原件`；已有intent，不再prepare/launch。
- 完整退出：`capture --launch-ref 原启动 --mode terminal --output 新完整回执`，再`settle-central --capture 新完整回执 --output 新中央结算`和`accept --capture 新完整回执 --central-settlement 新中央结算 --output 新独立接受`。

核对所有原身份和SHA、6路径84评分、OFF/ON全36/final/video、原α、双时钟诊断、独占全程与结算间隔、单调费用及中央幂等结算、锁/容器/句柄退出和安全恢复Default。失败保留原件费用，不自动重跑；完整科学接受前不调整方法、不启动E2或IG。

后续启动观察：84独占样本0违规，仍为模型加载、0失败，原runner活跃；见[启动状态](../reports/cara_common_long6_A6000_R2_startup_status_20261027.json)。不以工程启动宣称读出收益。

## 21:27实际技术半程

[原半程回执](../reports/cara_common_long6_A6000_R2_halfway_20261027_2127.json)实际观察21:27:25.254394（1793107645.254394），5/6完成、1运行、0失败。原guardian、supervisor、runner及容器仍运行，2209独占样本无违规，最大间隔2.285秒；私有输出卷32331718656字节可用，存储保护未报错，日志无错误。尚无GPU账单或CPU终态，不作科学接受。按启动墙钟计算距3h硬上限约100分钟，仅作技术余量，不替代单调账单。

半程一次自动化cara-r2已删除；23:50终态cara-r2-2继续绑定同launch。保持原采集约22:44及释放后最多1h CPU评分的保守安排，本次不凭单个完成计数重估各阶段速度。不读取部分分数，不调参，不重派。

## Terminal acceptance (23:50 scheduled check)

[Terminal receipt](../reports/cara_common_long6_A6000_R2_terminal_20261027_2350.json), [central settlement](../reports/cara_common_long6_A6000_R2_central_settlement_20261027_2350.json), and [independent acceptance](../reports/cara_common_long6_A6000_R2_accepted_20261027_2350.json). Original GPU billing ended at 21:44:47.004238 +08; CPU postprocessing exited 0 at 21:45:13.215702. These are original end times, not this check's observation time.

All 6 paths / 12 states / 84 readouts passed. OFF/ON all-36/final/video parity, original alpha, matrix, source/assets and both diagnostic clocks passed. All 2690 exclusivity observations passed; original guardian/supervisor/runner/post/container exited, UUID lock released, and guardian restored Default while idle. Storage and cross-disk journal checks passed.

Exact monotonic bill: 5829.267072642222 seconds = 1.6192408535117284 GPUh, below 3h. Central envelope settled once. Central snapshot: used175.8058597668662 / reserved16.5 / available33.694140233133794 / cap226. Other jobs account for their own pool changes; old R1 cost and uncertainty reserve remain.

Status: TECHNICAL_FINANCIAL_ACCEPTED_PENDING_FROZEN_ANALYSIS. No claim of candidate benefit, j1 promotion or closed-loop video quality. Frozen scientific analysis remains next; no E2/IG or new GPU dispatch. One-time terminal automation cara-r2-2 deleted.
