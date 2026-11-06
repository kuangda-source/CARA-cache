# 782 — 原校准 CPU 差量接受与完整结果验收器

[原四卡 CPU 接受](../reports/cara_budget_runner_four_card_CPU_accepted_r1_20261030.json)已完成。恢复的是781的唯一容器和登记；GPU未启动，CPU未重跑。原容器21:30:44开始、21:38:12退出0且无OOM；1CPU/4GiB、零swap、网络关闭、只读根和GPU隐藏均与原登记一致。完整证明经源码 `2d9332a687655474bf87cc4e2b5918cf08466e5a` 验证。

## 原 CPU 的实际覆盖

- 两种 flow 各18条完整设计路径、4次双 FIT 查询；包含失败控制后各42次物理尝试，共78条成功路径和6次明确注入的失败。
- 原采样代码的 Native/allD、时间开关、Python/NumPy/Torch CPU随机状态与93帧小张量RGB等价；原结果恢复不再生成，写出失败、第二FIT拒绝和策略回退均不重试。
- 27项校准/存储/运行器身份控制及3项原spec控制通过。CPU进程235.07885秒、worker墙钟429.48828秒；这些时间不计作GPUh或模型推理性能。
- 原完整112范围仍由e31发布源的原224条设计路径证据提供；本次差量不改称新源的双端整卡验收。原fixture通用footer中的“No sparse candidate”不定义本次范围：本次专用body实际执行并检查了19D策略和SEARCH_CANDIDATE，范围以专用checks及绑定源码为准。

[原捕获R7](../reports/cara_budget_runner_four_card_CPU_capture_r7_20261030.json)通过同一任务私有userspace SSH跳板、压缩只读传输取回。它保留原launch/registration/worker/proof字节身份；观察失联并未改变实验终态。此次取回成功不代表跳板间歇故障根因已查明，Windows同期日志仍待；不再轮询已接受的原CPU来刷新状态。

## 完整验收与一次冻结

新增 `cara_budget_complete_r1.py` 和生产CLI `accept_cara_budget_complete_r1.py`。它们先复核原guardian实测账单、中央唯一结算、全部原句柄结束、原容器退出0、锁/设备释放和模式恢复；在这些条件通过前，不打开collection、RGB、query return或候选分数。

通过释放门后，才核对原launch/context、reader/producer源码、运行器终态与精度，逐条检查112个完整物理尝试，无额外空目录/未完成路径。每条36更新、固定D预算、RNG摘要和时间字段受检；原RGB和生成工件哈希、Native/allD和时间开关等价、51次确定性查询及完整均值MSE通过原回读路径复核，不能执行新请求。

只有完整初始1＋SA30＋HC20均接受，才在该新run的输出目录创建 `calibration-frozen-mask.json`。已有相同内容只读复用，冲突拒绝且不覆盖；不写A32原冻结、不写中央账本、不授予新GPU。输出选择范围明确为两个旧CAL的FIT、seed0，不声称收敛或端点质量/时延收益。CPU夹具仅能写带CPU前缀的测试冻结；生产CLI拒绝CPU夹具。

[本地R2验证](../reports/cara_budget_complete_reader_local_CPU_r2_20261030.json)：11项、0跳过，完整51查询/112路径、93帧2×2合成RGB；包含正常一次冻结、零生成重复读取、活/未结算/未恢复/失败分配的提前拒绝、来源/计数/RNG/时间/工件/查询损坏与冲突冻结拒绝。使用真实生命周期审计和临时测试账本，stage模型/批准元数据明确mock；不是实际GPU结果或双端整卡CPU接受。R1的10项本地历史回执保留。

## 剩余整卡工作

完整派发once入口、64GiB实际非稀疏专用存储、双端整卡CPU和完整报价仍待；源码组件实现不等于整卡绑定通过。报价还必须包括 producer 完成搜索后的全量RGB/生成工件再读取与MSE复核时间，它发生在GPU清理释放前；这里新增的释放后科学验收CPU时间与GPU账单分开。继续沿用完整51查询/112路径设计，不以部分最佳候选代替完整接受。

用户仅选择14GPUh公平预算设计，尚未批准实际启动。当前0新GPU、0预约、0中央账本变更；226上限、旧16.5责任、原62个B36源和A32冻结保持。S/Q原运行与本对话范围分开。
