## 2026-10-21 两卡改四小时只读检查，四卡接续原BANK24→1624→自动生成器

[622最新决策](622_WC_FOUR_HOUR_TWO_CARD_MONITOR_AND_FOUR_CARD_EXPERIMENT_QUEUE_20261021.md)与[完整后续清单](../plans/WC_FOUR_CARD_EXPERIMENT_QUEUE_20261021.md)：按最新直接人类要求，worldcache-bank24已实际改为14400秒一次，只读恢复状态/原句柄/权威账本，不在两卡自动启动新GPU；以13:47:14.270913实际人类连接测试为基准，下一17:48（最早17:47:14.270913），原15:27由本次改频取代。四卡成为后续实验目标主机，原14:08/17:11/21:11模型检查保留，21:11 collector已补新机生产CPU/完整报价/唯一v2交接后的接续。顺序：资源与新机门→完整BANK24及共享CPU诊断→已批12GPUh完整1624→PG-P1单预算闭环→PG-P2公平消融→PG-P3跨预算/模型再校准→PG-P4冻结后独立确认。原source/scope/gate/已验结果与cap226/origin历史保留；旧机报价不作Ada实测，新机CPU/模型/兼容/共同权威账本仍须分别通过。当前仅准备与安排变更，0新远端查询/CPU/GPU/账本写；正常未知/忙静默。

## 2026-10-21 13:47 人工重启本机FRP后仍缺远端listener，15:27资源检查保持

按直接人类要求核对本任务原63302私有argv身份后，仅一次SIGTERM并按原完整配置重启；新本人客户端88068已登录、原33620 visitor监听成功，配置SHA前后一致。随后一次SSH连接测试仍认证前255；后续本人新日志已明确分类为远端转发listener不存在。结论限于远端FRP注册/转发链路不可用，不能据此判断整台GPU服务器宕机，也未从当前不可用入口执行远端frpc重启。原63302仅为历史进程，今后按current-owned-process.private.json核对88068，不查旧PID或自动重复重启。无其他FRPC/服务器任务改动，未取得GPU/锁/v2/原句柄，0CPU/GPU/账本写。此次人工连接测试不充fresh资源、不后移原15:27（最早15:26:06.991610）；BANK24/1624及四卡14:08/17:11/21:11资源检查和外盘模型准备均保持。

原件：[本人客户端重启与一次SSH](../reports/wc_two_card_owned_FRPC_human_restart_and_once_SSH_test_20261021.json)；[远端listener错误分类](../reports/wc_two_card_human_FRPC_restart_remote_listener_diagnosis_20261021.json)；[原15:27实际排程保持](../reports/wc_two_card_human_FRPC_restart_original_resource_schedule_preserved_20261021.json)。

## 2026-10-21 12:37资源槽延后13:26仍连接未知，下一15:27

原双卡12:37槽延后送达，实际仅于13:26:06.991610尝试一次资源SSH，认证前reset（exit255），没有当前GPU/显存/compute/UUID锁/v2/原句柄观察；不回填12:37或中间观察，最后成功仍10月20日16:05，不能据连接失败判断空闲、未派发或终态。本人FRPC63302的私有argv身份和33620监听仍一致，存储marker完整接受；无重启、追加CPU/其他SSH，0新CPU/GPU/账本写。原件与UNKNOWN边界保留，worldcache-bank24已读回改约15:27一次（最早15:26:06.991610，unix1792567566.99161）；本槽不重查、无可行动变化静默。原BANK24/source/CPU/gate和完整1624具体12批准/实际CPU/上游保持。四卡按621已实际公开模型下载及96件外盘中转，HF只读授权已通、token只Mac，14:08/17:11/21:11三原检查不改，本轮不查四卡或停其资源准备。

原件：[本槽一次连接回执](../reports/wc_scout_BANK24_fresh_resource_20261021_1237.json)；[离线边界核对](../reports/wc_scout_BANK24_resource_slot_1237_independent_unknown_acceptance_20261021.json)；[下一次15:27实际排程读回](../reports/wc_scout_BANK24_resource_slot_1237_once_reschedule_20261021.json)。

## 2026-10-21 10:36资源槽连接仍未知，下一12:37

原双卡本槽仅一次资源SSH于10:36:33.101639认证前reset（exit255），未取得当前GPU/显存/compute/UUID锁/v2/原句柄；最后成功资源仍10月20日16:05，不能据连接失败推断空闲、未派发或终态。本人FRPC63302的私有命令身份和33620监听核对一致；无重启、追加CPU或其他远端查询，0新CPU/GPU/账本写。原件与离线UNKNOWN边界已保留；worldcache-bank24已实际改约12:37一次（最早12:36:33.101639，unix1792557393.1016388），同槽不重查、状态无可行动变化静默。BANK24已验CPU/source/gate优先与完整1624具体12批准/实际CPU/上游前置保持；四卡618/619依赖组件和本机代理/清理/HF授权缺口保持，本轮不查四卡、不重建旧环境监控或本机大包。

原件：[本槽一次连接回执](../reports/wc_scout_BANK24_fresh_resource_20261021_1036.json)；[离线边界核对](../reports/wc_scout_BANK24_resource_slot_1036_independent_unknown_acceptance_20261021.json)；[下一次12:37实际排程读回](../reports/wc_scout_BANK24_resource_slot_1036_once_reschedule_20261021.json)。

## 2026-10-21 08:35资源槽连接仍未知，下一10:36

原双卡本槽仅一次资源SSH于08:35:28.540566认证前reset（exit255），未取得当前GPU/显存/compute/UUID锁/v2/原句柄；最后成功资源仍10月20日16:05，不能据连接失败推断空闲、未派发或终态。本人FRPC63302的私有命令身份和33620监听核对一致；无重启、追加CPU或其他远端查询，0新CPU/GPU/账本写。原件与离线UNKNOWN边界已保留；worldcache-bank24已实际改约10:36一次（最早10:35:28.540566，unix1792550128.540566），同槽不重查、状态无可行动变化静默。BANK24已验CPU/source/gate优先与完整1624具体12批准/实际CPU/上游前置保持；四卡618/619依赖组件和本机代理/清理/HF授权缺口保持，本轮不查四卡、不重建旧环境监控或本机大包。

原件：[本槽一次连接回执](../reports/wc_scout_BANK24_fresh_resource_20261021_0835.json)；[离线边界核对](../reports/wc_scout_BANK24_resource_slot_0835_independent_unknown_acceptance_20261021.json)；[下一次10:36实际排程读回](../reports/wc_scout_BANK24_resource_slot_0835_once_reschedule_20261021.json)。

## 2026-10-21 06:34资源槽连接仍未知，下一08:35

原双卡本槽仅一次资源SSH于06:34:40.516376认证前reset（exit255），未取得当前GPU/显存/compute/UUID锁/v2/原句柄；最后成功资源仍10月20日16:05，不能据连接失败推断空闲、未派发或终态。本人FRPC63302的私有命令身份和33620监听核对一致；无重启、追加CPU或其他远端查询，0新CPU/GPU/账本写。原件与离线UNKNOWN边界已保留；worldcache-bank24已实际改约08:35一次（最早08:34:40.516376，unix1792542880.516376），同槽不重查、状态无可行动变化静默。BANK24已验CPU/source/gate优先与完整1624具体12批准/实际CPU/上游前置保持；四卡618/619依赖组件和本机代理/清理/HF授权缺口保持，本轮不查四卡、不重建旧环境监控或本机大包。

原件：[本槽一次连接回执](../reports/wc_scout_BANK24_fresh_resource_20261021_0634.json)；[离线边界核对](../reports/wc_scout_BANK24_resource_slot_0634_independent_unknown_acceptance_20261021.json)；[下一次08:35实际排程读回](../reports/wc_scout_BANK24_resource_slot_0634_once_reschedule_20261021.json)。

## 2026-10-21 04:33资源槽连接仍未知，下一06:34

原双卡本槽仅一次资源SSH于04:33:39.099812认证前reset（exit255），未取得当前GPU/显存/compute/UUID锁/v2/原句柄；最后成功资源仍10月20日16:05，不能据连接失败推断空闲、未派发或终态。本人FRPC63302的私有命令身份和33620监听核对一致；无重启、追加CPU或其他远端查询，0新CPU/GPU/账本写。原件与离线UNKNOWN边界已保留；worldcache-bank24已实际改约06:34一次（最早06:33:39.099812，unix1792535619.099812），同槽不重查、状态无可行动变化静默。BANK24已验CPU/source/gate优先与完整1624具体12批准/实际CPU/上游前置保持；四卡618/619依赖组件和本机代理/清理/HF授权缺口保持，本轮不查四卡、不重建旧环境监控或本机大包。

原件：[本槽一次连接回执](../reports/wc_scout_BANK24_fresh_resource_20261021_0433.json)；[离线边界核对](../reports/wc_scout_BANK24_resource_slot_0433_independent_unknown_acceptance_20261021.json)；[下一次06:34实际排程读回](../reports/wc_scout_BANK24_resource_slot_0433_once_reschedule_20261021.json)。

## 2026-10-21 02:30资源槽实际02:32仍连接未知，下一04:33

原双卡本槽仅一次资源SSH于02:32:34.568812认证前reset（exit255），未取得当前GPU/显存/compute/UUID锁/v2/原句柄；最后成功资源仍10月20日16:05，不能据连接失败推断空闲、未派发或任务终态。本人FRPC63302的私有命令身份与原33620监听核对一致，未重启客户端/服务器、未追加CPU或其他远端查询，0新CPU/GPU/账本写。原件与离线UNKNOWN边界保留；worldcache-bank24已实际改约04:33一次（最早04:32:34.568812，unix1792528354.5688121），同槽不重查、无可行动变化静默。原BANK24冻结CPU/source/gate优先与完整1624具体12批准和实际CPU/上游前置保持；四卡618依赖组件已接受而完整推理/模型/GPU仍未接受，619本机代理/清理及HF授权缺口保持，本轮不查四卡或重建已完成环境监控。

原件：[本槽一次连接回执](../reports/wc_scout_BANK24_fresh_resource_20261021_0230.json)；[离线边界核对](../reports/wc_scout_BANK24_resource_slot_0230_independent_unknown_acceptance_20261021.json)；[下一次04:33实际排程读回](../reports/wc_scout_BANK24_resource_slot_0230_once_reschedule_20261021.json)。

## 2026-10-21 00:20资源槽实际00:29仍连接未知，下一02:30

原双卡仅一次资源SSH于00:29:28.540在认证前reset（exit255），没有当前GPU/锁/v2/原句柄观察；最后成功资源仍为10月20日16:05，不能据旧状态准入。本人FRPC63302和原33620监听仍在，本轮未重启或追加远端CPU查询，0新CPU/GPU/账本写。原件与离线UNKNOWN边界已保留，worldcache-bank24已读回确认改约02:30一次（最早02:29:28.540，unix1792520968.539606），同槽不重查、无可行动变化安静。原BANK24优先、已验CPU/gate及完整1624具体12批准/实际CPU/上游接受前置不变；四卡完整环境00:50/01:50两次查收独立保留，不迁移原scope。

原件：[本槽一次连接回执](../reports/wc_scout_BANK24_fresh_resource_20261021_0020.json)；[离线边界核对](../reports/wc_scout_BANK24_resource_slot_0020_independent_unknown_acceptance_20261021.json)；[下一次02:30实际排程读回](../reports/wc_scout_BANK24_resource_slot_0020_once_reschedule_20261021.json)。

## 2026-10-20 22:10槽实际22:19连接仍未知，下一10月21日00:20

一次原入口SSH仍认证前失败，未取得GPU/锁/v2/原stage。reports/wc_scout_BANK24_fresh_resource_20261020_2210.json及独立unknown边界已保存，最后成功观察仍16:05，旧余额不充fresh。原worldcache-bank24按实际22:19:50.876+7200秒重约00:20一次并回读，未追加CPU SSH或重复派发。已授权四卡CPU环境按615独立准备，原BANK24/已批完整12卡的source/证明/上游顺序保持，0本轮GPU/账本。以下为历史。

# 存储维护完整接受，BANK24就绪等待GPU（2026-10-19）

## 2026-10-20 20:44直接人类要求下的一次本人FRPC重启

用户直接要求“重启下 frp 试试呢”。原本人60782先验证PID命令与完整配置身份，再正常停止，以同一完整配置启动63302；配置SHA不变，新客户端登录和原33620监听均独立确认。一次原SSH测试20:44:40仍在认证前255，当前新日志提示远端原转发listener未注册，未执行服务器命令、未取得原stage/句柄或当前GPU/v2。原件[重启](../reports/wc_owned_FRPC_direct_human_restart_20261020_2043.json)和[原SSH一次测试](../reports/wc_owned_FRPC_restart_original_SSH_once_test_20261020_2044.json)保留。当前客户端PID为63302，私有PID/日志引用在ignored .sync/policy-assets-frpc-20261020/current-owned-process.private.json，旧60782及旧日志仅为历史。

没有动其他FRPC或服务器实验，无新CPU/GPU派发或账本写；未再循环重启。此为直接人类恢复探测，非新资源观察，原资源自动化22:10一次保持。其prompt已改为当前63302和新日志，具体上限12批准仍有效，原BANK24及新scope实际生产CPU前置未放宽。

## 最新：2026-10-20 20:09原20:08槽连接仍未知，下一22:10

本槽按原not-before后只执行一次轻量资源SSH；实际20:09:33.312568仍在认证前reset，未取得任何当前GPU/compute/逐UUID锁/v2/原任务句柄。原件[wc_scout_BANK24_fresh_resource_20261020_2008.json](../reports/wc_scout_BANK24_fresh_resource_20261020_2008.json)及独立[wc_scout_BANK24_resource_slot_2008_independent_unknown_acceptance_20261020.json](../reports/wc_scout_BANK24_resource_slot_2008_independent_unknown_acceptance_20261020.json)保留；这仅接受连接未知边界，不接受GPU资源、任务终态或任何价格/科学结果。最后成功快照仍为16:05，不能填成当前空闲/忙卡或余额。

本人60782客户端仍存活，有界日志继续显示远端原转发listener未注册；未重启客户端、其他FRPC或任何服务器任务。本槽没有追加新CPU SSH，0新GPU/账本写。原BANK24及新完整1624卡的实际服务器状态仍须恢复原句柄；完整12GPUh具体批准已记录，CPU及BANK24前置没有放宽。

按实际尝试+7200秒最早22:09:33.312568，向上取整22:10已通过app工具更新本资源自动化一次COUNT1并回读核实；无新通知事项、无循环监听。同槽原件已存在时仅离线读它，下一时点仍执行原BANK24优先及613已批完整卡的接续。以下为历史观察，旧“仅GPU占用”的表述不代表当前已连接。

**FRP修复与五项存储维护已完整接受；系统盘上本人home实占减少153.9281GiB。BANK24自身CPU、CAL12上游和四CAL门控均已接受，目前唯一阻碍是两张GPU被其他任务占满。没有新GPU派发或费用。**

## 实际完成与证据

- 本人不完整Cosmos3-Nano模型目录已删除，下载脚本/记录保留；同学wangshuai的Nano索引必需权重全部可读，未修改其文件或权限。
- pip/uv缓存已清空并在数据盘重建，HF/Wan的126个普通文件完成源/目标全SHA复制一致；四旧路径保留兼容软链接，实际数据集中在`/home/gaokuangda/data/gkd/home_storage`下的cache和models。原项目hfhub别名保持，受检Python/uv运行文件和环境配置指纹一致，环境未重装。
- home系统盘占用：163.894798279→9.966712952GiB，减少153.928085327GiB。新容量快照系统盘可用192.4265GiB、数据盘1260.1984GiB。
- 唯一worker b1d31ba2/run b0bd9ec3c5e84301已退出，维护锁释放；本地marker=COMPLETED_STORAGE_MIGRATION_VERIFIED，no_new_GPU_until_storage_acceptance=false。

最终原件：`reports/wc_user_storage_maintenance_terminal_recheck_20261019_1925.json`；独立接受：`reports/wc_user_storage_maintenance_independent_acceptance_20261019.json`。18:52半程和19:12运行中快照完整保留。复制清单留服务器私有目录，不进入Git。

## 新一次资源检查与余额

实际2026-10-19 19:26:40.496，`reports/wc_scout_BANK24_storage_accepted_fresh_resource_20261019_1926.json`：

| GPU | UUID尾部 | 显存MiB | 利用率 | compute PID | 自身UUID锁 |
|---|---|---:|---:|---:|---|
| 0 | 288888777dd3 | 48168/49140 | 100% | 2883539 | free |
| 1 | cd196332b704 | 47822/49140 | 100% | 2883540 | free |

锁free不代表GPU空闲。本项目当前0GPU任务/0预留，BANK24的fence/launch/授权/日志/输出全部不存在，未尝试派发。v2在该次快照实结116.825023108771/cap226，余109.174976891229，origin79.99637737158223及历史不变；准入时必须重新读取fresh账本。

资源自动化worldcache-bank24已实际创建，下一21:27，最早unix1792416400.4960527。每次忙卡依据实际观察+7200秒向上取整分钟更新下一次COUNT1，立即结束，不循环监听、不干预他人任务。原worldcache-cal12-bank24已删除，避免重复维护/查收。调度与依赖原件：`reports/wc_storage_complete_BANK24_busy_ordered_continuation_20261019.json`。

## 等空闲后的唯一完整卡

BANK24保持六DEV×D21/A21/NATIVE35，18正式+6完整预热=24，864pairs/1728CFG/一次加载/六Native。forecast3.407222222GPUh，整卡上限4.5<12，现有直接授权保持；不缩卡/拆卡、不重复已验CPU、不以当前HEAD替换冻结stage。

已接受CPU三件套：

- `reports/wc_scout_BANK24_GPU_lifecycle_CPU_R2_launch_20261018.json`
- `reports/wc_scout_BANK24_GPU_lifecycle_CPU_R2_collection_20261019.json.gz`
- `reports/wc_scout_BANK24_GPU_lifecycle_CPU_R2_independent_acceptance_20261019.json`

source2bd41dc8fa19f42353e03a7c78b7264b4b2695c6；stage `.sync/wc-scout-bank24-gpu-lifecycle-cpu-r2-20261018`；实际生成entry c1c95ce0/原1772依赖不变。上游CAL12已接受，直接使用`reports/wc_scout_CAL12_full12_terminal_recovered_collection_20261019_1830.json.gz`和`reports/wc_scout_CAL12_full12_terminal_independent_acceptance_20261019.json`，gate为`reports/wc_scout_CAL12_fourCAL_frozen_gate_20261019.json`，不得重新拟合DEV。

按ready手册调用launch_wc_scout_gpu_r1.py一次，目标唯一launch文件`reports/wc_scout_BANK24_full24_GPU_launch_20261019.json`；fresh空闲UUID/显存/compute/锁/v2余额及原stage无派发标记均满足才执行。已有fence/通信未知仅恢复原句柄，禁止删除标记重放。一次实际admission核对后按真实launch半程/ETA各约一次，并删除已无用途的资源巡检。

终态保存原件再离线analyze，完整24分母/所有拒绝失败/warm OFF-ON/同状态前20guided与probe/inputhash/全部有效兼容正式93帧/真实Native/owner与实际费用分别接受。X-R共享银行，仅执行原登记CPU方向/同D配额门控诊断，不把离线重组当在线闭环或clean速度，不自动并入主稿。F/B关闭，无训练/人评/付费VLM/OMR；原N10、Window24、CAL12不重查或重跑。

## 21:27资源占用未变，下一23:28

实际21:27:49.684只做一次资源查询，两UUID仍被原PID2883539/2883540占满，48170/47824MiB、100%；自身锁free，原BANK24所有派发标记与输出仍不存在，0新GPU/预留/费用，没有重跑CPU或存储。原件wc_scout_BANK24_fresh_resource_20261019_2127.json及独立核对wc_scout_BANK24_resource_slot_2127_independent_busy_acceptance_20261019.json保存。按origin加全部SETTLED原费用独立重建116.825023108771/cap226，余109.174976891229。worldcache-bank24已更新下一23:28，最早unix1792423669.6840827/23:27:49.684；不连续监听。

## 23:28资源占用未变，下一10月20日01:29

实际23:28:49.481仅一次资源查询，两GPU仍由原PID2883539/2883540占满（48170/47824MiB、100%），自身锁free、BANK24所有派发标记和输出不存在，未启动GPU或重跑准备。原件wc_scout_BANK24_fresh_resource_20261019_2328.json和独立核对wc_scout_BANK24_resource_slot_2328_independent_busy_acceptance_20261019.json保存。原账重建实结116.825023108771/cap226、预留0余109.174976891229，费用不变。下一not-before1792430929.4810946（10月20日01:28:49.481），worldcache-bank24已约01:29一次；不循环监听，609本地科学分析及原BANK24冻结scope/gate保持。

## 2026-10-20 01:30两GPU仍占用，BANK24未派发；下一03:31

原01:29槽实际01:30:40.464仅一次轻量资源快照：两GPU仍占满48170/47824MiB、100%，其他任务PID更新为3015457/3015458；自身两锁free、原BANK24全部派发标记和输出不存在，0本项目GPU/预留/新费用。v2逐原任务重建实结116.825023108771/cap226，余109.174976891229；源/CPU/存储/CAL12/gate不重跑。下一最早03:30:40.464（unix1792438240.4636245），worldcache-bank24已更新03:31一次，忙卡不变安静、不循环。v6新32路径仍是待实际生产CPU的草案，本轮不抢开新GPU。 原件`reports/wc_scout_BANK24_fresh_resource_20261020_0129.json`、独立核对`reports/wc_scout_BANK24_resource_slot_0129_independent_busy_acceptance_20261020.json`。

## 2026-10-20 03:31两GPU占用未变，BANK24未派发；下一05:32

实际03:31:53.348仅一次轻量资源快照：原其他任务PID3015457/3015458仍占满两GPU（48170/47824MiB、100%），自身两锁free，BANK24全部派发标记与输出不存在，0本项目GPU/预留/新费用。v2逐原任务重建实结116.825023108771/cap226，余109.174976891229；原CPU、存储、CAL12与gate不重跑。下一最早05:31:53.348（unix1792445513.3477428），worldcache-bank24已更新05:32一次；不循环监听、不问释放时间，v6首轮32路径仍须自己的实际生产CPU，不抢开新GPU。 原件`reports/wc_scout_BANK24_fresh_resource_20261020_0331.json`、独立核对`reports/wc_scout_BANK24_resource_slot_0331_independent_busy_acceptance_20261020.json`。

## 2026-10-20 05:32两GPU占用未变，BANK24未派发；下一07:33

实际05:32:52.004仅一次轻量资源快照：原其他任务PID3015457/3015458仍占满两GPU（48170/47824MiB、100%），自身两锁free，BANK24全部派发标记与输出不存在，0本项目GPU/预留/新费用。v2逐原任务重建实结116.825023108771/cap226，余109.174976891229；原CPU、存储、CAL12与gate不重跑。下一最早07:32:52.004（unix1792452772.0036604），worldcache-bank24已更新07:33一次；不循环监听、不问释放时间，v6首轮32路径仍须自己的实际生产CPU，不抢开新GPU。 原件`reports/wc_scout_BANK24_fresh_resource_20261020_0532.json`、独立核对`reports/wc_scout_BANK24_resource_slot_0532_independent_busy_acceptance_20261020.json`。

## 2026-10-20 14:00原07:33槽延后查收，两GPU仍占用；下一16:01

原07:33心跳延后送达，实际14:00:10.808仅一次当前资源快照，未补填中间观察：其他任务PID3015457/3015458仍占两GPU（48214/47826MiB，利用率5%/8%；显存未释放仍busy），自身两锁free，BANK24全部派发标记和输出不存在，0本项目GPU/预留/新费用。v2逐原任务重建实结116.825023108771/cap226，余109.174976891229。下一最早16:00:10.808（unix1792483210.8082192），worldcache-bank24已实际更新16:01一次；不循环监听，原CPU/存储/CAL12/gate与v6设计保持，v6首轮32路径仍须自己的实际生产CPU。

原件`reports/wc_scout_BANK24_fresh_resource_20261020_0733.json`及独立核对`reports/wc_scout_BANK24_resource_slot_0733_independent_busy_acceptance_20261020.json`保存。实际观察距原计划07:33已延后约6小时27分钟；本轮没有重复SSH、重跑CPU或派发GPU。按实际观察后至少7200秒安排下一次，不能据旧时刻循环追补查询。

## 2026-10-20 16:05两GPU占用未变，BANK24未派发；下一18:06

原16:01槽实际16:05:17.889仅一次轻量资源快照：原其他任务PID3015457/3015458仍占两GPU（48214/47826MiB、100%），自身两UUID锁free，BANK24全部派发标记与输出不存在，0本项目GPU/预留/新费用。v2逐原任务重建实结116.825023108771/cap226，余109.174976891229；原CPU、存储、CAL12与gate未重跑。下一最早18:05:17.889（unix1792490717.8894036），worldcache-bank24已实际更新18:06一次，不循环监听。最新611固定官方WC和612可复现策略生成器设计保持；人工32路径草案后置，新生成器22项CPU原型控制不代替真实生产CPU，本任务仍只接原BANK24。

原件`reports/wc_scout_BANK24_fresh_resource_20261020_1601.json`及独立核对`reports/wc_scout_BANK24_resource_slot_1601_independent_busy_acceptance_20261020.json`保存；原07:33槽实际14:00观察仍保留，本次没有回填中间观察。两次实际观察间隔超过7200秒；未读科学partial或方法时间。


## 2026-10-20 18:07原18:06槽连接未知，下一20:08

仅一次资源SSH尝试在认证前reset，未读取GPU/compute/锁/v2或原任务终态。最后成功原件仍为16:05，旧busy和旧余额不充当前准入。自己的完整TCP客户端60782可登录/监听33620，但远端原target listener未注册；不循环重连、不重启服务器任务或其他FRPC。原件wc_scout_BANK24_fresh_resource_20261020_1806.json及resource_slot_1806_independent_unknown_acceptance_20261020.json保留。实际18:07:33.450尝试后+7200秒，下一最早20:07:33.450，worldcache-bank24已实际约20:08一次。

最新直接人类613卡的CPU恢复已接入本资源任务与未来BANK24终态接续；BANK24仍原卡优先。新卡全1624标签/独立价格、14路径，预计9.918333333/上限12，本地完整Toy数值通过；实际生产CPU因认证前失败尚未启动，不能当GPU-ready或默认批准12。恢复后先原stage/launch只读，未知不得重派。全部旧CPU/存储/CAL12/gate不重查。
