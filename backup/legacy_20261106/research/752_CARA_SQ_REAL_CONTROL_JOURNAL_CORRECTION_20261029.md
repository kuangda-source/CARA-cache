# S/Q 真实控制日志修复与 Q1 就绪撤回

原 48 MiB `FixedJournal` 仅注册六个物理键。Q1/S 的 host allocation、pending release 和 supervisor diagnostic 使用额外逻辑键，原 CPU 存储替身接受任意键，漏过了这一生产故障。[实盘复现](../reports/cara_sq_original_control_journal_key_refusal_r1_20261029.json)。这会在原控制文件落盘前拒绝写入，影响释放与费用证据，不是数值方法失败。

因此撤回源 `a8dc60f53f62adbbecaab07d207f466ab1ca471e` 的 GPU 就绪状态；[R2 审阅](../plans/cara_next_stage_20261028/sq/Q1_NEXT_CARD_REVIEW_R2.md) 仅保留历史准备事实。双端原 r1/r2 无 intent、容器或中央 Q1 envelope，旧 stage 与全部原回执保持。[撤回](../reports/cara_sq_q1_readiness_withdrawn_control_journal_r1_20261029.json) · [原句柄](../reports/cara_sq_q1_original_handles_before_journal_fix_r1_20261029.json)。

修复只在独立 S/Q storage wrapper 中，将额外记录按名称封装到原 accounting 槽，并用独立跨进程锁覆盖完整读、合并、写过程。共享 journal 模块、48 MiB 格式、原六物理槽、原始 journal-first 落盘顺序不变。外来身份、非空损坏、未知键及超长记录保留原件并拒绝；不重建旧日志。

本地 12 项真实日志控制通过，含两个真实并发 CPU 子进程。新[完整 CPU 范围](../plans/cara_next_stage_20261028/sq/Q1_CONTROL_JOURNAL_CPU_R1.json) 在原 51 core＋15 wrapper 上增加 12 journal＋4 actual actor 控制，每端共 82 项、18 个枚举 allocation/journal CPU 子进程。双端 R2 完整 Linux 控制、原容器/CLI 全退出及各 12 类拒绝均已[独立接受](../reports/cara_sq_control_journal_dual_cpu_accepted_r2_20261029.json)。首次双端 R1 因新增 actor 测试夹具缺报价文件失败，原失败保留，修正只补齐夹具。GPU、容器状态、模式和挂载观测在 actor 测试中明确为夹具；不能称真实 GPU 释放验收。

新 Q1 采用 r3 stage/R3 profile，整卡报价增加 4 秒 journal 合并工程余量，硬限仍为 A6000 1.25、Ada 2 GPUh。保留两个已曝光 FIT 的 12 旧状态、111 pair/222 head、零新 deep/父路径/视频和首个原控制失败即停。未改变读出、codec、collection 或资产数值源。

双端新 Q1 r3 源、原生入口、原 33 项摘要与当前文件身份及空私有盘已绑定；完整审阅见 [Q1 R3](../plans/cara_next_stage_20261028/sq/Q1_NEXT_CARD_REVIEW_R3.md)。本轮四个原 CPU 容器合计 444.548 秒、分配 vCPU 上界 889.096 秒；[费用记录](../reports/cara_sq_control_journal_CPU_full_costs_r2_20261029.json) 保留未计量口径。接下来单独获得该 Q1 GPU 授权后再 fresh 准入与唯一派发。S 同步补完整 GPU 生命周期，真实 108 标签仍为零，14/17 GPUh 整卡报价仍是未冻结提案。S/Q 各自有用后才进入各自完整视频与最后组合，不继承主线权限。此次没有 GPU 提交、预约或中央账本写入。
