# 最终共同测试生产CPU已启动，整卡与预算待具体批准

2026-10-16。**N05/N06完整接受后，已完成最终共同测试的实际输入、方法和费用冻结，并在独立服务器目录单次启动真实生产CPU。** 这一步验证实际Cosmos入口和完整180排程能否使用已冻结条件；尚未执行新GPU或产生最终测试视频。

## 当前原句柄

- source：`3138e03a088b03a8381f9df609cbd59b76433a05`；stage：`.sync/wc-paper-n07-production-cpu-r1-20261016`。
- CPU PID1111360 / start_ticks541937992，启动`2026-10-16T12:21:16.399570+08:00`。
- 全1724 payload / 157 overlay；注册SHA `660cbe19d2927112fcbf604ed6d551e9fe0e1137939b8d49f51a0b4aa17cf5e0`。
- 六命令：五组合同/完整batch/post/acceptance/dispatch控制，加真实Cosmos无权重CPU入口；CUDA和下载禁用，原99数值执行依赖复用952证明。
- 原完整8新prompt×2seed×10方法：160正式+20完整warm=180，6318pairs/12636CFG、一次加载、0新teacher；不拼接旧结果或缩减控制。

最早一次查收`2026-10-16T12:25:16.399570+08:00`，已将原worldcache-26d heartbeat更新为**12:27一次收**；N05旧任务不再查询。查收只运行原capture，再用同一个保存回执离线accept，核对全payload/原PID终态/六退出码/160typed参数/Native双seed与guardrail/数值源和无CUDA/账本写。若尚在运行，据剩余量另约一次并结束；禁止循环轮询。CPU失败保留原件与完整分母，必要修复用fresh版本。

## 科学进展和主线顺序

[496完整强基线](496_WC_N05_CORE66_COMPLETE_STRONG_BASELINES_AND_N07_N08_METHOD_FREEZE_20261016.md)已接受66/44视频4092帧，低费用A相对默认RA失真低9.6667%、主时间高1.0809%；高保真工作点与少步Native26耗时接近，参考失真更低。四个开发场景和每格一次计时的边界保持。

[497实际冻结](497_WC_N07_FROZEN_NEW_INPUTS_FULL180_ACTUAL_COST_AND_PRODUCTION_CPU_PREREG_20261016.md)已按先方法冻结、再fresh身份排除、后确定性选8组/seed17和43顺序完成，保留全部七个N05前沿点、两强前密简单对照及Native26。下一主线为N07最终共同确认→N08完整40平衡重复clean计时→N09实际部署费用/显存与N10自动质量。P/T1后排，F/B关闭，无训练、OMR或人工评审。

## CPU通过后的具体决策

N07整卡`WC-PAPER-N07-FROZEN-SHARED180-R1`完整预计及计费上限**15.055555556 GPUh**，达到需要直接批准的门槛；N08原完整40预计3.6275 GPUh，两卡合计18.683055556。原服务器累计cap仍104.97136333301378，origin79.99637737158223不变；12:05保存实结93.58182465745968，预留0，余11.389538675554107。**本轮没有修改cap、预留费用或派发GPU。**

配置中的累计cap113仅是明示的拟议审批对象，服务器尚未应用。建议CPU完整接受后，一次询问是否批准原完整180卡并将同一累计cap提高到113；这样按现快照可覆盖N07+N08预计费用，约余0.735119787GPUh。N09/N10实际费用另待核定，不能宣称后续全部工作已获预算。原窗口/used/历史不重置；未获直接回复不执行新GPU。

若批准，才更新原v2并按真实余额、UUID、原CPU/源码和完整价格绑定单次准入。未来长GPU首次查收按配置为启动后16小时；本次CPU自动化收完即暂停，后续GPU另约一次ETA。不用缩卡、删对手或重做调参绕过12门槛。

## 原件

- [原CPU launch](../reports/wc_paper_N07_actual_production_CPU_R1_launch_20261016.json) · SHA256 `d1d97e24cf88a15519ada6fdbe6e775af5f564dcaeb5f361768d59bebbc21d1c`。
- [实际N07配置](../configs/wc_paper_N07_frozen_shared_production_r1_20261016.json)。
- [完整180/40实际费用](../reports/wc_paper_N07_N08_actual_complete_cost_r1_20261016.json)。
