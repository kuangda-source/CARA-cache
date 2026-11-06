# 原P0第20步准入与启动承接

**已由实际启动承接覆盖：** 原卡已于2026-11-02 01:24:19.536402+08实际开始。此文件保留启动前准备/连接等待快照；所有后续操作改读[原运行与验收交接](P0_POINT20_POST_LAUNCH_HANDOFF_20261102.md)，不得再次预约或dispatch。

用户已选择先补P0、完整P1另审预算，且2026-11-02明确允许“本卡原账本读取、预约与结算”。小于2GPUh沿用既有自主推进规则。以下是唯一新卡，不继承或重放原M1。

- run：`cara-source-lifecycle-P0-point20-full14-r1-20261101`
- 预登记launch：`94ad4122aab5401b834643a84868d417`，不可另造或迁移。
- source：`3263bdfe0eb93fa7c93daefd34ce892855a5a4b3`
- stage：`/data20t/gaokuangda/worldcache_workspace/.sync/cara-source-lifecycle-P0-point20-GPU-a6000-full14-r1-20261101`
- registration SHA：`d5df9d66c521bd0ffba6ae190f395c0daac22f79dc72f1ecbf3a9033b306b9f8`
- scope SHA：`0b61ea4937e71724ad1c781a3adca36a3839a4d8e3212a971747a0579da5a766`
- two_card原A6000：`GPU-cebf7119-cf03-23b9-e192-cd196332b704`
- 完整14路径/512pair/8新评分；预计1.6047625014886833、硬限1.95GPUh，6420秒主工作、600秒释放余量，90°C；cap226和旧16.5责任不变。

整卡准备见[机器回执](../../../reports/cara_v1_P0_point20_complete_preparation_r1_20261101.json)。原新CPU退出0：77控制、28条loaded tiny完整请求、8对93帧合成评分、2Native桥接；原存储进程退出、16GiB卷和48MiB journal接受。不得再prepare这些已完成CPU、卷或GPU源码。

最终授权为[P0_POINT20_AUTHORIZATION_R1.json](P0_POINT20_AUTHORIZATION_R1.json)，草稿不能派发。`scripts/cara_source_lifecycle_p0_control_r1.py`负责bind/admit/refresh/central-prepare/central-status/reserve/dispatch/status/settle。四卡仅本卡原中央账本事务，不做实验，不迁移或重置账本。新intent或连接UNKNOWN时只用status/central恢复，不得新建dispatch、reserve、prepare或重启；已有事务仅恢复原件。原operator缓存按本卡launch分隔；中央源码必须仍与原CPU和GPU注册哈希相同。

先恢复原句柄、完成实际资产/运行时/UUID/VRAM/应用/锁/温度/存储/内存/独占及中央余额核验，再新鲜refresh→原中央reserve→唯一dispatch。需要新的fresh回执时另存，不覆盖旧回执。成功/失败均以原guardian全段单调时钟实耗唯一结算；网络UNKNOWN先恢复原事务，不能重复收费。

实际开始接受文件固定使用 `reports/cara_v1_P0_point20_actual_start_accepted_r1_20261101.json`（日期为冻结卡标识，实际时间必须记录真实日期）。开始后才创建一次半程和一次终验，按实际guardian开始推算；运维检查仅14分母计数、句柄、温度、资源、独占及账本，不读部分科学分数。无变化或不可行动保持安静，完成后删除一次性检查。

原GPU完整退出、释放和实耗结算后，固定源码的释放读者先检查四个全latent/93RGB角控制、两份原第8步Native桥接，再仅派一次8对CPU评分。用 `scripts/cara_source_lifecycle_p0_accept_transport_r1.py artifacts/score/capture`；CPU已启动只capture，不重复评分。最终原终态和原结算文件使用 `reports/cara_v1_P0_point20_final_original_r1_20261101.json` 与 `reports/cara_v1_P0_point20_final_settlement_r1_20261101.json`，与入口固定绑定。

全8接受后用 `scripts/analyze_cara_source_lifecycle_p0_complete_r1.py`完整合并原第8步八行与新第20步八行，保留W_C/W_D及读出、交互、总收益、完整93帧和直接消费者历史。原M1不重评分、冻结或结算。P0不等于V1规划器确立；P1的完整预算仍单独审阅，不自动下一卡。


## 2026-11-02实时承接：连接待恢复，无GPU派发

[原准入等待回执](../../../reports/cara_v1_P0_point20_admission_transport_wait_r1_20261102.json)：授权已绑定；central-prepare返回UNKNOWN，之后仅central-recover，尚未读回原operator状态。两卡admit/原status均因跳板握手失败；未调用reserve或dispatch，因此未预约、未开始、未计新GPU费用，也未创建实际开始检查。原Windows IPv4/IPv6 TCP22均超时；原FRP四卡账本入口在握手前重置，未由此读取GPU状态。已请求恢复原Windows通路，无须重新申请本卡预算或账本许可。

本地仅传输等待时间适配为 `scripts/cara_source_lifecycle_p0_control_r2.py`（原TWO/CENTRAL RPC字节逐值保持；本任务独立private SSH配置、目标ConnectTimeout60秒）。原GPUstage、source3263bdfe、授权与硬限均未改。恢复后只调用该入口central-recover/status；未确认原operator缓存缺席前不要再次central-prepare，存在部分缓存时只恢复原相同哈希字节。查明无GPU intent/容器后再恢复fresh准入。任何既有预约/派发只能恢复原事务，不新造launch。
