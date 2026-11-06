# N10完整960评分的监督与实际费用准备

2026-10-16。**原完整评分worker已接独立监督进程、逐UUID锁、原v2整卡预留及实际费用结算；13项本地CPU控制通过。** 没有启动真实评分GPU、载入原模型或取得新质量分数。

新增 [`supervise_wc_paper_N10_full960_r1.py`](../scripts/supervise_wc_paper_N10_full960_r1.py)，并扩展516入口的原CPU证明／授权核对。生产CPU结果绑定实际worker SHA、source注册、config、原输入指纹和完整960范围；只有原生产CPU进程已退出且原退出回执成功，才能进入原UUID准入。源码注册与配置文件SHA分开绑定。

父监督只派发一个原完整评分子进程，传递自己实际持有的UUID锁；费用使用同一v2累计窗口和原origin，按完整wall加法结算。严格小于12GPUh使用既有自主规则；等于或超过12必须持有该完整卡的具体人类批准，继续复用原`ApprovedCardBudgetPool`，没有新预算窗口。

原五模型CPU证明与实际输入仍由原worker验证。另一主线任务存在活动预留时，评分不能进入。子进程失败、创建失败或中断均保留全范围和原日志，监督只停止自己拥有的进程组，不自动重派。费用、退出与GPU释放不替代科研接受；评分账单明确不形成生成延迟结论。

## 验证与剩余工作

13项是新增5监督控制＋8受影响入口控制，使用真实临时UUID文件锁／原v2账本实现，显卡、子进程、CPU证明与批准内容为明确合成夹具。验证单次子进程、180秒合成wall的加法实结、创建失败仍记费和释放、原主线／CPU在途拒绝、错误source／worker／报价拒绝，以及完整12GPUh具体批准通路。没有访问真实服务器、原GPU或真实账本。

仍待：原固定资源完整接受、真实五模型CPU、N07最终原件绑定、实际完整配置与报价、独立CPU部署／单次GPU派发、原事件与终态原件查收及独立科研接受。当前监督代码准备不能当成生产卡已验收或已执行。未来实际长卡仍按真实启动／估时安排半程与终态两次离散查收。

本轮资源R3已按时查收，失败及连接层区分证据见[517](517_WC_N10_RESOURCE_R3_TERMINAL_TLS_FAILURE_AND_SCOPED_TRANSPORT_DIAGNOSIS_20261016.md)。N07今天21:30／明早05:30、主线N07→N08→N09/10、同一cap113／origin保持。F/B关闭，无训练、OMR或人评。

原件：[13项本地CPU](../reports/wc_paper_N10_full960_supervisor_CPU_R1_20261016.json)、[516评分worker](516_WC_N10_COMPLETE960_SCORING_WORKER_AND_ORIGINAL_ADMISSION_CPU_PREPARATION_20261016.md)。
