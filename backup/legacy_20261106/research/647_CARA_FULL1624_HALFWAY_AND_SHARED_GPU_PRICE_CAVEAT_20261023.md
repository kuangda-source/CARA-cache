# 完整1624半程：原任务正常推进，同卡外部进程影响动作价格解释

**2026-10-23 03:16:50（Asia/Shanghai）实际收件：10/14路径完成，1运行，3未到达，0失败。** 原supervisor、runner、容器和GPU UUID均匹配，UUID锁仍由原任务持有，日志末段未见错误。此次半程没有提交、停止或修改任何远端任务。

半程首次观测同时发现同一GPU上有另一个计算进程。03:18:57的只读身份检查确认：原runner PID811944/UID1000使用约16254 MiB；外部PID848535/UID1005使用约13408 MiB。**本批动作耗时不能直接作为独占GPU下的干净价格接受。** 这尚不等于数值标签或视频失败；这些仍由完整原件及Native/off/on控制独立验收。

## 原任务与实测进度

launch `37ab7e89-952b-4ddb-acde-5b20a0fc1295`；source `94fe08832b8feb92ae6235c5b569d615950cf491`；run `wc-policy-interval-assets-cal4-full1624-ada-r2`。原完整4CAL/1624正式格/14路径/2030总格/13020读出/单次加载及12GPUh上限不变。

- 原supervisor：PID811837/start946344871；runner：PID811944/start946345336；原容器运行中，未OOM。
- 当前`formal_2_COLLECT`：253/406格；已完成两条正式COLLECT和一条预热COLLECT。合计1065/1624正式格、1471/2030含预热格，只表示技术完成量，尚未全量接受。
- GPU3 UUID `GPU-d4868f0a-29df-9077-82db-77f7bf0f9934`，观测约29693 MiB、100%利用率；外部进程与原runner同UUID。
- 03:17:36资源补查：数据盘余240.40 GiB，MemAvailable约29.24 GiB，均高于原卡最低要求。
- 按监督器实际启动时间累计约5.0614小时GPU占用墙钟，上限内余约6.9386小时。仍未结算，不冒充终态实际费用。账本仍预留本卡12GPUh，旧两卡16.5GPUh未知责任预约保留。

按已完成正式COLLECT约73–74分钟及Native/control约6分钟推算，GPU段粗略还需约1.9小时，落在05:10附近；同卡竞争与输入差异会改变该估算，且不含CPU后处理。保持原08:26全程检查，不把预测结束时间写成完成事实。

## 动作价格验收边界

首次同UUID竞争证据为03:16:50；外部进程启动时间估计为10月22日23:25:44，但进程启动不等于首次使用GPU时间，不能据此断言此前每条价格试验均受竞争。

本卡按原范围继续，所有价格重复、数值、视频、控制和费用原件完整保留。终态时先分别接受来源、完整性和数值控制；价格标记为存在同卡竞争证据，不将控制通过或采集完成等同于干净延迟通过。PG-P1不得仅凭旧acceptor的`generator_input_ready`字段启动：需同时处理本记录的价格门槛，检查竞争影响；若需要独占条件补测，应另立明确的计时修复范围与报价，不重跑本卡、不改写已有原件。

没有触碰外部进程，也没有使用部分误差、视频或标签调参。当前共享α与两支独立α的消融建议不改变本卡冻结采集。

## 原件与后续检查

- [半程原始回执](../reports/wc_policy_assets_full1624_fourcard_GPU_halfway_20261023_0317.json)
- [资源及路径时长补查](../reports/wc_policy_assets_full1624_fourcard_GPU_halfway_resources_20261023_0318.json)
- [同UUID进程身份](../reports/wc_policy_assets_full1624_fourcard_GPU_halfway_compute_identity_20261023.json)
- [技术核对与价格门槛](../reports/wc_policy_assets_full1624_fourcard_GPU_halfway_technical_20261023.json)
- [原启动及完整范围](646_CARA_FULL1624_CPU_ACCEPTED_GPU_LAUNCH_20261022.md)

一次性半程自动化`cara-1624-gpu`已删除。原终态自动化`cara-bank24-2`继续绑定同一launch、10月23日08:26收件，并加入上述价格验收门槛；不新增重复终态任务。
