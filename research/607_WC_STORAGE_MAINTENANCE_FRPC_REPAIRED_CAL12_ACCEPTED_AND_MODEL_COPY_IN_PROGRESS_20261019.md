# 用户存储维护、FRP恢复与CAL12验收接续（2026-10-19）

截至18:46，FRP已恢复，原CAL12完整12路径及8正式视频93帧评分已经独立接受。用户授权的存储维护已单次启动：本人不完整Nano权重已删除，pip/uv缓存已清空并在数据盘重建；HF和Wan仍在复制与全文件SHA256校验，**尚未宣告迁移完成或实际总释放量**。BANK24等存储独立验收后继续，原算法、已验阶段与预算不变。

## 1. 授权与实际范围

用户直接授权修复FRP、删除本人Nano权重、在不影响当前实验的条件下重建pip/uv缓存，把HF和Wan迁数据盘并统一路径；补充同学用户名为wangshuai。没有修改同学的文件或权限，没有启动生成、训练或新GPU卡。

| 项目 | 原路径 | 数据盘统一目标 | 当前边界 |
|---|---|---|---|
| 本人Nano | `/home/gaokuangda/cosmos3_nano/models` | 删除 | 已确认删除，download脚本及记录保留 |
| pip缓存 | `/home/gaokuangda/.cache/pip` | `/home/gaokuangda/data/gkd/home_storage/cache/pip` | 已清空重建，旧路径软链接 |
| uv缓存 | `/home/gaokuangda/.cache/uv` | `/home/gaokuangda/data/gkd/home_storage/cache/uv` | 已清空重建，已装环境保留，旧路径软链接 |
| HF | `/home/gaokuangda/.cache/huggingface` | `/home/gaokuangda/data/gkd/home_storage/models/huggingface` | 复制/逐文件SHA校验中；通过后原子切换旧路径 |
| Wan | `/home/gaokuangda/da_str_assets` | `/home/gaokuangda/data/gkd/home_storage/models/wan` | 同上；不能提前认定已迁移 |

历史只读盘点：home系统盘实占约163.89GiB；Nano及pip/uv预计释放约73.97GiB，HF/Wan约79.96GiB可迁移，总减少预计约153.93GiB。以上为规划估计，真实减量以最终原件中的home allocated前后差及新容量为准。其他用户也会使用/释放磁盘，因此文件系统可用量变化不能全部归因于本次维护。

## 2. FRP恢复与实验保护

原任务自己的FRPC旧TCP会话失效；隔离新会话以原SSH主机密钥、账号、主机和GPU UUID确认同一服务器后，仅重连本人原入口。旧PID17525替换为35140，原gkd_minchen别名/33620保留，私有凭据和配置不变。临时探测客户端已关闭；其他任务FRPC未动，远端实验GPU/runner/post重启次数均为0。

小型脱敏证据：`reports/wc_storage_FRPC_primary_repair_sanitized_20261019.json`。私密配置和日志留本地ignored .sync，不入Git。

清理前已确认原CAL12三个句柄退出，无活跃pip/uv操作，相关环境无指向旧缓存的软链接或.pth依赖。维护保留已装uv/uvx及Python环境文件指纹，并在最终独立复核；删除的是缓存文件名，环境中既有硬链接不会因此被改写。仅在实验GPU空闲期维护，禁止维护未接受时启动BANK24。

## 3. 迁移执行与验收

唯一worker source SHA：`b1d31ba209812be164d7b75dcc24cbef78b93fa832e03db28f1771f12ca047d7`；PID2856956/start570111208，run_id b0bd9ec3c5e84301，18:36:48.565单次启动。运行时Python3.10，nice19/ionice低优先级，无CUDA、权重加载或账本写入。launch为`reports/wc_user_storage_maintenance_launch_20261019.json`。

原stage `.sync/storage-maintenance-20261019-r1` 保持，不重派或改源。HF/Wan先rsync保留完整目录及相对链接，再对源和目标全部普通文件计算SHA256，并逐项比较类型、模式与链接文本；一致后在原文件系统用RENAME_EXCHANGE切换目录/兼容软链接，无旧路径不可用窗口。项目hfhub的Predict2.5/Reason1原链接文字保留并校验新解析目标。通过前原模型目录保留；通过后才删除系统盘旧副本。私有逐文件清单不导出。

18:37准入快照确认Nano删除、两缓存重建，原worker处于COPY_HUGGINGFACE。此后未持续查询。已实际安排：

- 18:52一次技术半程（最早18:51:48.565），自动化worldcache；只看原身份/技术阶段/错误。
- 19:12一次完整独立验收（最早19:11:48.565），自动化worldcache-cal12-bank24；全部五动作、两模型SHA、旧路径同inode/数据盘、环境指纹、原进程退出和维护锁释放通过才解除BANK24互斥。

调度原件：`reports/wc_storage_maintenance_two_once_collections_20261019.json`。若未完按一次快照剩余阶段重新估时后结束，不循环监听；失败/未知保存，不重派破坏性操作。最终收件/离线接受由`scripts/capture_wc_storage_maintenance_r1.py`完成。本地兼容路径互斥为`.sync/storage_maintenance_20261019/maintenance-state.json`，当前ACTIVE_STORAGE_WORKER_DISPATCHED；只有COMPLETED_STORAGE_MIGRATION_VERIFIED且no_new_GPU_until_storage_acceptance=false才可准入BANK24。

## 4. Wangshuai的Nano权限

数据盘实际目录为`/home/gaokuangda/data/wangshuai/cosmos/models/Cosmos3-Nano`。当前账号已核对两个权重索引及全部10个不同的必需权重文件：均存在、可读，并实际打开读取1字节。无需改权限。未加载、复制或修改同学模型；部分私人迁移元数据目录不可读，保持不访问。

模型目录joint du为35,301,957,632字节，所检查的HF Nano缓存目录仅4,096字节；当前证据不支持将该HF目录算第二份完整权重。此为文件与权限检查，不替代完整模型运行/版本兼容性验证。脱敏原件：`reports/wc_wangshuai_Nano_read_access_20261019.json`。

## 5. CAL12恢复验收与后续

18:06连接UNKNOWN原件完整保留；FRP修复后沿原launch只读取一次新文件：`reports/wc_scout_CAL12_full12_terminal_recovered_collection_20261019_1830.json.gz`。独立接受为`reports/wc_scout_CAL12_full12_terminal_independent_acceptance_20261019.json`，status=SCOUT_COMPLETE_REGISTERED_PROTOCOL_ACCEPTED，12/12完成、8/8正式全部93帧，4warm控制、共同前20步和四场景同状态probe/inputhash均通过，零错误。原GPU/post退出、费用与自身UUID释放接受，实费0.9899122730769321GPUh。该收件快照pool实结116.825023108771/cap226、reserve0，之后准入必须fresh重查，不能当实时余额。

CAL12为四旧CAL探索，诊断秒数不当clean速度，不自动并入主稿。四CAL gate已保存`reports/wc_scout_CAL12_fourCAL_frozen_gate_20261019.json`；mu/中位秩阈值只来自CAL，较大z保留D，平局>=，DEV不拟合。

BANK24自身R2生命周期CPU三件套已接受，不重跑CPU。迁移独立接受后，用CAL12上述真实capture/acceptance和gate、fresh v2/UUID按ready手册仅一次启动原完整24（18正式+6warm，六DEV与六Native，forecast3.407222222/上限4.5GPUh）。已有fence/未知派发仅恢复原句柄；资源busy则每两小时一次，禁止循环。累计cap226、origin79.99637737158223及历史不变，严格整卡<12直接执行；F/B关闭，无训练/人评/付费VLM/OMR。

## 6. 18:52一次半程正常

实际18:52:31.737仅一次技术读取，原PID2856956/start570111208及source一致，处于HASH_DESTINATION_HUGGINGFACE，累计已哈希68,932,992,844字节（包含源/目标，不能当唯一迁移容量或整体完成百分比），无错误。Nano删除及两缓存重建完成；HF/Wan尚未作最终独立验收，维护互斥保持。原件wc_user_storage_maintenance_midpoint_20261019.json及独立技术核对wc_user_storage_maintenance_midpoint_technical_acceptance_20261019.json已保存。半程worldcache已删除；唯一19:12最终worldcache-cal12-bank24保持，不新增检查或GPU。

## 7. 19:12按时读取，HF已迁移；Wan最后哈希重估19:25

19:12:36.075一次原件捕获确认原PID/start/source不变，RUNNING/HASH_DESTINATION_WAN，无错误。HF的199项/103普通文件、51,651,996,220逻辑字节已完成源/目标全SHA和兼容路径切换；原件记录的full_SHA256_tree_match=true。Wan尚未最终接受，不能宣告整项完成，也不能解除BANK24互斥。原19:12回执wc_user_storage_maintenance_terminal_20261019.json保留，不作为终态送accept。

累计哈希150,150,987,601字节是两树源/目标之和；按已登记模型规模估计尚余约21.6GB目标哈希，另留原子路径切换和旧副本回收时间，改约19:25一次新查收（not-before1792409100）。只使用新wc_user_storage_maintenance_terminal_recheck_20261019_1925.json，原worker不改/不重派，不再次查询当前快照。独立重估原件wc_user_storage_maintenance_once_reestimate_20261019_1912.json。worldcache-cal12-bank24已实际更新为19:25；通过后接BANK24的授权、CPU/完整矩阵/冻结gate/预算保持。

## 8. 19:25完整独立接受：系统盘实际减少153.928GiB

19:25:35.543新原件确认worker已结束且维护锁释放，五动作全部完成，HF/Wan各自完整源/目标SHA通过；独立收件对四旧路径软链接、数据盘位置/同inode/可读、两私有清单摘要及全部目标元数据、受检运行文件指纹复核通过。126个模型普通文件全部完成复制校验；环境未重装，原项目模型别名保持。原19:12运行中快照不覆盖，私有逐文件清单不导出。

正式接受为reports/wc_user_storage_maintenance_independent_acceptance_20261019.json，status=COMPLETED_STORAGE_MIGRATION_VERIFIED；home实占175,980,699,648→10,701,676,544字节，即163.8948→9.9667GiB，实际减少165,279,023,104字节/153.9281GiB。该时刻系统盘可用192.4265GiB、数据盘1260.1984GiB，为全文件系统容量快照，不全部归因于本次维护。原worker19:18:36.086完成，全wall约2506.956秒，0新GPU费用；本地维护互斥已由独立接受解除。

19:26:40.496仅一次fresh资源查询发现两GPU被其他任务占满（PID2883539/2883540，48168/47822MiB，100%），自身锁free但无空闲卡。原BANK24 stage所有fence/launch/授权/log/输出不存在，未调用GPU派发器，0新GPU/预留。新资源自动化worldcache-bank24实际安排21:27，最早21:26:40.496；占用未变时按实际观测+2小时再约一次，禁止连续尝试。原worldcache-cal12-bank24本轮维护用途完成已删除。当前完整接续见608。
