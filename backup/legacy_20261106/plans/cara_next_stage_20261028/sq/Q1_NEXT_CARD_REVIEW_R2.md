# 下一张 Q1-saved：修正后的完整审阅

2026-10-29。主机整段计费、失败收件、唯一启动与中央结算已接通，双端各 66 项完整 Linux CPU 控制及十类错误回执拒绝检查通过。双端新源包、原生 Python 入口、33 项资产的原完整摘要与本轮文件身份、空白私有输出盘均已核验。[完整机器审阅](../../../reports/cara_sq_q1_complete_review_r2_20261029.json) · [双端 CPU](../../../reports/cara_sq_q1_control_dual_cpu_accepted_r6_20261029.json)。准备完成；GPU 尚未批准、预约或启动。

执行源固定为 `a8dc60f53f62adbbecaab07d207f466ab1ca471e`，采用新的 `cara-sq-q1-saved-<host>-r2-20261029` stage、R2 profile 和两份 R2 报价。旧 f3 仍禁止启动，旧 stage、失败、CPU 阶段与旧审阅保留。原 RUN 与科学范围不变。

## 做什么与停止条件

固定 Shared25-C，使用两个已曝光 FIT 输入 AV28/human_199 在 22、23、25、33、34、35 的 12 个旧 B1 状态。96 正式 C pair、2 warm C、1 原 C 预检、12 D-hidden 控制，共 **111 pair / 222 head**；新增 deep、父轨迹和视频均为零。

原 C 与 D-hidden 输出仍须与旧 B1 `torch.equal`。首个原控制失败就停止后续 codec 和全部选择，保留原失败、已完成分母与整段费用；不改容差/精度、不换主机续跑、不自动重试。此前 CPU 原控制未过，实际 CUDA 数值门仍待本卡验证。

完整收集后，先证明所有原句柄/容器退出、锁与模式释放，唯一中央结算并独立接受终态，再用 2 CPU / 8 GiB / 最多 300 秒做完整 12 状态 LOPO。同字节报告 q_total、q_codec、交叉项、实际 packet 字节及编码/传输/读出时间；部分状态不选方向。零新视频，本卡不提供完整视频或部署总峰值节省结论，未来 S-END/Q-END 另行绑定 Fidelity-v2。

## 整卡报价与唯一时钟

| 主机 | 完整工程预测 | GPU 硬限 |
|---|---:|---:|
| RTX 6000 Ada | 112.610 分钟 | 2 GPUh |
| RTX A6000 | 57.658 分钟 | 1.25 GPUh |

两份报价包含完整 111 pair、加载/SHA/I/O、CPU codec、传输、原件审计、输出/释放及 25% 失败余量；R2 额外明确主机模式准入/恢复 100 秒及原容器收尾 60 秒。它们是工程预测，尚非实测 GPU 单价。[Ada R2](Q1_WHOLE_QUOTE_FOUR_CARD_R2.json) · [A6000 R2](Q1_WHOLE_QUOTE_TWO_CARD_R2.json)。

唯一账单从 host guardian 准入前的 monotonic 起点开始，直到绑定原容器关闭和模式恢复后结束，覆盖容器启动/退出；监督器时间仅作诊断。凭据、准入、未 exec、未创建容器、worker 早退和超时同样保留费用。UNKNOWN 或模式恢复失败继续保留原 envelope，仅恢复原件。释放余量为 180 秒，超过硬限的实际费用也不截断。

资源仍为一张 GPU、2 CPU（24/25）、16 GiB、私有输入逻辑副本 8 GiB、CUDA allocator fraction 0.5、1 GiB SSD 输出、48 MiB 异盘 journal、64 MiB 文件限额；idle 温度 <70°C，达到 90°C 即停止。真实 context 独占仍必须成立。

## 已有证据与费用

每端 51 核心＋15 wrapper 控制，含 14 个可枚举 allocation CPU 子进程及真实 Linux 监督器、自发布 handoff、凭据管道异常和 CPU 后处理。GPU/容器/温度与财务时间均为显式夹具，账本只在临时目录。[整段修订记录](Q1_FULL_ALLOCATION_R2.md)。

最终 R6 容器 A6000 44.712 秒、Ada 180.601 秒，均退出 0；worker 加已回收子进程 CPU 分别 32.338 / 52.486 秒。保留本轮 R4/R5 与 R6 共五个实际 CPU 容器，合计墙钟 565.109 秒、已测 worker/子进程 CPU 209.786 秒、分配 vCPU 上界 1130.218 秒；本地测试、主机拷贝/daemon、SSH 与 Git CPU 未完整计量。[完整 CPU 费用](../../../reports/cara_sq_q1_full_allocation_CPU_costs_r2_20261029.json)。新增 GPU 费用和中央写入均为零。

资产不重新复制或重扫：复用先前完整 33 项 SHA，只在本轮逐项检查 dev/inode/大小/mtime/ctime/HF link、原 runtime 与空白私有盘。[A6000 绑定](../../../reports/cara_sq_q1_two_card_prepared_inputs_reuse_r2_20261029.json) · [Ada 绑定](../../../reports/cara_sq_q1_four_card_prepared_inputs_reuse_r2_20261029.json)。变化即拒绝复用。

## 下一步

本轮只读检查显示双端旧 r1/新 r2 均无 GPU intent、容器或 Q1 中央预约；资产与源有效，当时 Ada 无合格空闲卡、A6000 有合格候选。中央快照 cap 226、已用 178.061565、旧未知责任 16.5、可用 31.438435 GPUh。[原句柄](../../../reports/cara_sq_q1_original_handles_prepared_r2_20261029.json) · [资源快照](../../../reports/cara_sq_q1_preflight_readonly_r2_20261029.json) · [中央快照](../../../reports/cara_sq_q1_budget_readonly_r2_20261029.json)。这些快照不替代派发时准入。

仍需用户对这一张 Q1 单独授权。批准后只选择一个主机，fresh 准入优先 Ada、否则 A6000，绑定对应已审阅 proof 与单个中央 envelope。实际 guardian 起点后安排一次预测半程与一次终态检查；不读取部分科学分数。此卡不授权 S、Q-END、新视频、预算扩容或重放。

等待期间继续补 S 的真实 RAM/存储边界、GPU 入口与整卡报价；108 真实标签仍为零。主线 F19/B36 独立推进，S/Q 各自有证据后才进入自己的完整视频闭环，组合实验最后进行。
