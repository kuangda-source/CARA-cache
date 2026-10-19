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
