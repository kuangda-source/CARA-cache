# 818 — 七角色端点卡范围更新与Euler-E0 CPU准备

依据用户11月1日交接文档更新队列，并按用户明确选择保留唯一**46物理路径、七角色、28逻辑位置**E1卡：新增F19-RiskSwap，加入F19-C同批时延；旧32草案保留且不执行。完整预计6.040147GPUh，建议硬限7.0，尚无GPU执行授权。

四项交付：

- [准备与原件复用](../plans/cara_next_stage_20261101/READINESS_AND_ASSET_REUSE.md)
- [39/46完整清单与逐项报价](../plans/cara_next_stage_20261101/ENDPOINT7_SCOPE_AND_QUOTE.md)
- [Euler源码、数值控制和协议缺口](../plans/cara_next_stage_20261101/EULER35_PROTOCOL_GAPS.md)
- [决策树、冻结门与保护TEST计划](../plans/cara_next_stage_20261101/DECISION_AND_FREEZE_GATE.md)

原预算冻结按原终态捕获字节核SHA后直接绑定；四个新增策略互异，BR/DIAG与F19三目标别名各只生成一次。两卡原16视频SHA现场吻合，目标A6000观察时45°C/24MiB/0%，磁盘约907.55GiB。维护四卡未访问，最后18.515812GPUh可用额只是结算快照，不能用作新卡准入。

原唯一CPU容器01:20:17启动、01:22:55退出0/无OOM。46生产路由小张量组合通过，另5计时OFF对照、10重复一致性、Native/allD一致性、失败完整分母及重派拒绝通过，耗时153.487秒。2个计划边界测试和7个旧执行回归测试通过。无权重、无CUDA，不证明视频质量。没有重跑旧114微型路径、搜索或原评分。

Euler-E0从现场固定源码确认视频CFG=8C−7U、速度方向和原36网格；隔离Euler原型35更新/70CFG、常速度解析轨迹、CFG手算轨迹及6个19D噪声坐标映射控制通过。完整Euler wrapper CPU与真实权重Native/allD仍未接受；论文未给精确sigma数组，新增35网格明确记作重建。

**仍未关闭：** 七角色生产入口、释放后工件/28位置评分及汇总图表接线、完整资产和独立存储生产包。旧25/32的整链证据不能自动覆盖新46；当前新执行入口明确拒绝GPU，防止以采集CPU接受替代派发资格。先补这些受影响接口，再提交唯一7GPUh卡和本卡原中央账本事务审批；不请求或启动Euler GPU。

[机器登记](../reports/cara_next_experiments_E1_Euler_preparation_r1_20261101.json) · [46 CPU终态接受](../reports/cara_endpoint7_CPU_accepted_r1_20261101.json) · [Euler CPU回执](../reports/cara_euler35_E0_CPU_acceptance_r1_20261101.json)。原A32冻结、B36/S/Q/预算搜索接受、WC/RA UNMATCHED和旧CAL范围不变。
