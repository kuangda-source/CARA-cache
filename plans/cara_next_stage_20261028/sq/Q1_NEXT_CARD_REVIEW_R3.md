# Q1-saved R3：真实日志修复后的独立实验卡

双端完整真实日志 CPU、新 r3 源、原生入口和 33 项输入的当前身份绑定均已接受。用户已明确批准这一次 Q1 单卡；当前等待完整主机与物理准入，尚无 Q1 预约或派发。[直接批准](Q1_GPU_APPROVAL_R1_20261029.json) · [准入等待](../../../reports/cara_sq_q1_approved_waiting_admission_r1_20261029.json) · [完整机器审阅](../../../reports/cara_sq_q1_complete_review_r3_20261029.json)。旧 R2 就绪状态已[撤回](../../../reports/cara_sq_q1_readiness_withdrawn_control_journal_r1_20261029.json)：生产日志不接受释放记录使用的额外键。修复保持共享 48 MiB 日志格式，在独立 S/Q wrapper 的 accounting 槽中保存命名记录，并以跨进程锁保护读改写。原 r1/r2 GPU stage、失败和回执保持。新执行源为 `cd368922cbc70d610aaece6d1a71069fa45a3ecd`，使用 GPU r3 stage/R3 profile。

## 要回答的问题

固定 Shared25-C，在两个已曝光 FIT 输入 AV28/human_199 的 12 个旧 B1 状态上，比较同字节 codec 的真实 C 读出误差、实际 packet 字节和完整编码/传输/读出耗时。96 正式 C＋2 warm C＋1 原 C＋12 D-hidden，共 **111 pair / 222 head**；新增 deep、父路径和视频均为零。读出、collection、codec、子图和资产数值源与原 R6 接受源逐项保持。

原 C 与 D-hidden 必须先与旧 B1 `torch.equal`。首个原控制失败即停止后续 codec 和全部选择，保留失败、分母与原费用；不调容差、精度、不换主机续跑或自动重试。真实 CUDA 数值门仍未通过，CPU 控制不能替代。

完整 GPU 收集后，先证明原容器/进程、context、锁和模式全部释放，唯一中央结算并独立接受终态，再用 2 CPU / 8 GiB / 最多 300 秒对完整 12 状态做两个 prompt 留一选择。同字节报告 q_total、q_codec、交叉项及字节/时间；不从部分状态选方向。本卡没有完整视频或部署总峰值改善结论。Q1 有用后才准备独立的 Q-END。

## 完整资源与工程报价

| 主机 | 整卡工程预测 | GPU 硬限 |
|---|---:|---:|
| RTX 6000 Ada | 112.700 分钟 | 2 GPUh |
| RTX A6000 | 57.750 分钟 | 1.25 GPUh |

[Ada R3](Q1_WHOLE_QUOTE_FOUR_CARD_R3.json) · [A6000 R3](Q1_WHOLE_QUOTE_TWO_CARD_R3.json)。报价包括完整 111 pair、加载/SHA/I/O、CPU codec、传输、原件审计、模式/容器收尾、4 秒日志合并工程余量和 25% 失败余量；仍是工程预测，未接受真实 GPU 单价。硬限不变，不为适配阈值拆卡。

资源为一张 GPU、2 CPU（24/25）、16 GiB RAM、8 GiB 私有输入逻辑上限、CUDA allocator fraction 0.5、1 GiB 私有 SSD 输出、48 MiB 异盘 journal、64 MiB 文件限额；idle 温度 <70°C，达到 90°C 停止。完整报价、真实 context 独占与派发时 fresh UUID/VRAM/apps/locks/磁盘/内存/资金均须成立。

唯一费用时钟从 host guardian 准入前开始，到原容器关闭并恢复模式后结束；监督器时间仅作诊断，失败费用不丢失或截断。UNKNOWN 仅恢复原句柄并保留 envelope。实际唯一启动后按原 guardian 起点安排一次预测半程与一次终态检查，不读取部分科学分数。

## CPU 证据与下一步

每端原 51 core＋15 wrapper＋12 真实日志＋4 真实 actor 持久化控制共 82 项全部通过；18 个枚举 allocation/journal CPU 子进程、原容器和 CLI 均已退出，每端 12 类错误回执拒绝通过。[双端接受](../../../reports/cara_sq_control_journal_dual_cpu_accepted_r2_20261029.json)。日志为真实完整 48 MiB 文件，GPU/容器/模式/挂载观测明确为夹具，只有临时测试账本。首次双端 CPU 尝试因 actor 测试夹具缺少报价文件退出，原失败保留；修正只补齐夹具，不更改生产或数值源。

最终 A6000/Ada CPU 容器分别 46.671/105.662 秒，退出 0；本轮含两次保留失败的四个原 CPU 容器合计 444.548 秒，分配 vCPU 上界 889.096 秒，成功两次已测 worker＋回收子进程 CPU 94.425 秒。失败 worker、cgroup 总 CPU 和本地/传输/Git CPU 未完整计量。Ada 在预测半程点之前已完成，名为 half 的原捕获实际是终态，未据此声称半程运行观察。[完整 CPU 费用](../../../reports/cara_sq_control_journal_CPU_full_costs_r2_20261029.json)。

准备时已[恢复双端 r1/r2/r3 原句柄](../../../reports/cara_sq_q1_original_handles_prepared_r3_20261029.json)：没有 intent、GPU 容器或中央 Q1 envelope。原 33 项完整摘要复用前重新核对文件身份和空私有盘，未重复制或重扫输入。收到直接批准后的新检查仍无 Q1 原件：Ada 无合格空闲卡，A6000 虽有物理候选，但主线 B36 持有该主机的中央预约，原 guardian 和容器已只读确认在运行。按每主机一个所属 GPU job 的约定等待，不叠加、释放或修改 B36。已建立本对话 15 分钟准入监控 `q1`；状态不变静默。完整准入成立后使用本次已有批准，优先 fresh 合格 Ada，否则 A6000，只派发一次，再从实际起点安排半程与全程验收。此卡不授权 S、Q-END、新视频、重放或预算扩容。

S 独立继续准备完整执行入口，真实 108 标签仍为零；其 14/17 GPUh 报价是未冻结提案。各自局部验证有用后进入各自完整视频，两者分别成立后才做最终布局×codec 组合；主线 F19/B36 的范围、权限和预算保持独立。
