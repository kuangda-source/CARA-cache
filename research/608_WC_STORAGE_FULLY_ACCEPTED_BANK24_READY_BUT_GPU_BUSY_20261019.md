# 存储维护完整接受，BANK24就绪等待GPU（2026-10-19）

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
