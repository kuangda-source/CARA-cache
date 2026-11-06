# 连续修正完整24路径已准入：原句柄恢复与两次查收

**原Window24已于2026-10-19 12:28:22.733北京时间在GPU0准入，只有一次GPU派发；14:01做技术半程检查，15:48做完整验收。当前没有新的A3保真或速度结果。**

## 1. 原卡范围与来源保持

原source `a350ea9822e3443c3cd8f4c601673fc064d49684`，stage `.sync/wc-drop1-window24-production-cpu-r1-20261018`，run `wc-drop1-correction-window-cal4-full24-r1`。原1749源／五命令实际生产CPU已接受，没有重跑数值或生产CPU，也没有更换当前HEAD部署。

四个旧CAL×四臂S26-C、S25-C、S25-A1、S25-A3，共16正式＋8完整预热、24路径／864pairs／1728CFG／一次模型加载／零新teacher。A3沿原设计在21／22／23连续修正；旧12端点、完整预热36guided与共同前21步等价控制保持，不能用此次启动替代终态验收。

[本次fresh资源原件](../reports/wc_window24_fresh_resource_and_single_dispatch_preflight_20261019_0706.json)实际观察时间为12:25:39.023；原07:06心跳延后执行，不能将文件槽名当成实际观察时间。两卡当时显存320／24MiB、利用率0、没有compute进程、两UUID锁free。[独立准入前检查](../reports/wc_window24_resource_slot_0706_independent_idle_acceptance_20261019.json)接受完整卡余额和原stage没有任何派发标记，随后只派发一次原卡。

## 2. 启动回执异常及原任务恢复

原启动器已创建GPU派发fence和supervisor，但紧接着读取`/proc`的command时，脚本名校验触发AssertionError，尚未写启动回执、尚未创建CPU post。这个异常发生在原supervisor已派发之后，不能按“未启动”重新执行启动器；随后只读恢复确认其已完成GPU准入并启动runner。

[原unknown回执](../reports/wc_drop1_window24_full24_GPU_launch_20261019_1228.json)保留。一次[只读恢复快照](../reports/wc_window24_original_dispatch_identity_recovery_readonly_20261019.json.gz)确认：原launch_id、fence、授权、pool job与GPU锁一致，supervisor2639899及runner2640331已运行；没有post或GPU启动回执。该快照只读技术身份，没有读取科学partial。原进程当前command正确，说明最初的即时command观察没有稳定完成身份登记；不把它解释为模型或方法失败。

[独立恢复工具](../scripts/recover_wc_drop1_window24_dispatch_identity_r1.py)只恢复原句柄和缺失的操作回执，并补一次原已验CPU post watcher。它复核原授权／CPU／配置SHA、原PID/start_ticks和同一账本预留；已有post或回执即拒绝操作，使用独立post恢复fence。原GPU不重启、不再次派发，原采样、执行代码、配置、注册payload/runtime均未改。

[本地恢复控制](../reports/wc_window24_original_handle_metadata_recovery_local_controls_20261019.json)用真实恢复快照检查正确原句柄，并拒绝错误UUID、错误start_ticks、已有post、已有启动回执、原锁已释放五种情况；这六项只是操作恢复证据，不是新算法或视频验证。

[恢复后的启动回执](../reports/wc_drop1_window24_full24_recovered_GPU_launch_20261019.json)独立保存；原unknown没有覆盖。`started_unix`明确采用原supervisor实际GPU准入时间，同时保留原fence创建时间、恢复时间和恢复来源SHA，未把恢复时刻写成原启动时刻。唯一launch_id为`edae5828-637b-4823-b686-2ba0f8741a7c`。

## 3. 实际准入与费用边界

[一次准入收件](../reports/wc_drop1_window24_full24_original_admission_20261019.json.gz)及[独立接受](../reports/wc_drop1_window24_full24_independent_admission_acceptance_20261019.json)核对：

| 角色 | PID | start_ticks |
|---|---:|---:|
| 原GPU supervisor | 2639899 | 567894598 |
| 原GPU runner | 2640331 | 567900634 |
| 补齐的原CPU post watcher | 2641355 | 567912775 |

GPU0 UUID为`GPU-de9a5370-cd87-0f1c-a48e-288888777dd3`。原锁持有、完整24范围、原source／config／CPU／授权／输入绑定及4GPUh整卡预留均接受。另一张卡不并发启动CAL12或BANK24，上游完整接受的顺序保持。

完整预测3.064166667GPUh、计费上限4，沿原严格小于12GPUh的直接授权执行。权威v2实结仍114.02498439084846／cap226，完整预留4，可准入余额107.97501560915154，origin79.99637737158223和全部历史保留。**4是预留，不是实际费用；本卡实际GPU费用待原账单结算。**

## 4. 两次查收与既定接续

[实际自动化绑定](../reports/wc_drop1_window24_full24_two_once_collection_automations_20261019.json)：

| 查收 | 最早北京时间 | 安排 | 自动化 |
|---|---|---|---|
| 技术半程 | 14:00:18.733 | 14:01 | worldcache-window24 |
| 完整原件验收 | 15:47:13.733 | 15:48 | worldcache-window24-cal12 |

两者使用恢复后的唯一launch-ref，按原卡实际准入时刻与原预测公式计算。半程只核对技术状态；终态捕获一次后离线分析全部24分母、原件、等价控制、全部有效兼容正式93帧LPIPS、原GPU/post退出、真实全wall费用及本UUID释放。失败、拒绝和未到达保留，未完成则重新估时另约一次，不持续监听。

两次查收已实际创建并核对后，删除不再需要的`worldcache-gpu`两小时资源巡检。后续若下一卡等待资源，由上游collector恢复两小时检查，不能借删除巡检取消在途查收。

原24完整原件和费用按原协议接受后，按[就绪手册](../plans/WC_SCOUT_GPU_READY_CONTINUATION_20261019.md)直接接已验CAL12完整12（预测1.876666667／上限2.5），从四旧CAL冻结μ和中位秩阈值，再接BANK24完整24（预测3.407222222／上限4.5），X-R共享。新卡自己的R2生命周期CPU三件套已接受，不重跑准备，不借原卡通过标记。每卡重新fresh UUID／v2准入、半程／ETA各一次；未知派发不重放。

原N10全960已接受，不重查／重评；探索不自动并入主稿，F/B关闭，无训练、人评、付费VLM或OMR。当前所有新科学结果仍待真实终态验收。

## 5. 14:01技术半程已完成，原15:48终态不变

14:01:37.432一次[原任务半程回执](../reports/wc_drop1_window24_full24_midpoint_health_20261019.json.gz)确认：全部24分母中20完成、1运行、3未到达；21个已有runner记录不等于21个完成。原supervisor2639899／runner2640331／post2641355的PID/start_ticks和原注册绑定一致，原GPU0锁仍持有，GPU与supervisor错误标签为空。只读取技术状态，没有打开质量、逐帧、张量或方法时间比较。

[独立技术接受](../reports/wc_drop1_window24_full24_midpoint_independent_technical_acceptance_20261019.json)核对完整计数、原句柄／UUID／授权／4预留及池账相符；实结114.024984391／cap226、预留4、可准入107.975015609保持，本卡实际费用未知。没有新增GPU或CPU派发，没有改原stage。完整源／视频／费用终态接受未执行，不能用本次健康检查代替。

本次半程自动化`worldcache-window24`完成后已删除；原终态自动化`worldcache-window24-cal12`及15:48时间／原not-before／全部接受协议和后续CAL12接续保持不变。状态正常，无需人工动作，不追加巡检或提前读取科学结果。
