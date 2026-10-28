# 下一张 Q1-saved 卡：完整审阅包

2026-10-29。本卡单独验证固定 Shared25-C 的同字节缓存表示，使用两个已曝光 FIT 输入的旧 B1 状态。以下完整范围保持为待申请草案：四卡原资产 CPU 尚在运行，终态接受前不提出 GPU 批准请求。尚未获得新的 GPU 授权。主线 B36 与 S 新父轨迹采集分别处理。

## 做什么、按什么停止

使用固定源码 `f3be7662175889c77e3719521fecb9c4d3be83af`，旧 AV28 / human_199 × 位置 22、23、25、33、34、35，共 12 状态。每状态八角色：原未压 C、FP32 M 变换回转 C、I/M 各三种固定 bit 组合。96 正式 pair，加两次 C warm、一对原 C 预检与 12 对 Dense-hidden 控制，总计 **111 pair / 222 次 head 读出**；新增 deep、父轨迹、视频均为零。[原完整范围](Q1_WHOLE_SCOPE_R1.json)及其分母保持。

原 C 和 Dense-hidden 输出必须与旧 B1 `torch.equal`。首个失败立即结束后续 codec，保留完整失败、原费用和已完成分母，不改容差/精度，不换主机续跑或重试。此前单状态 CPU 数值门未过；本卡的 CUDA 控制正用于检查真实执行后端是否能满足原门槛，尚不预设通过。

成功时 GPU 阶段只收集；全部句柄退出、独占锁释放、Default 恢复、中央结算及独立终态接受后，再以 2 CPU / 8 GiB / 最多 300 秒做完整 12 状态的 LOPO 和一套共享方向选择。未完整则不使用部分状态选方向。报告真实 packet 字节、q_total、q_codec、交叉项与编码/传输/实际读出分别计时；本卡不证明完整视频收益或部署缓存峰值节省。

## 一次单卡与整卡费用

| 已注册主机 | 完整工程预测 | GPU 硬限 | 选择规则 |
|---|---:|---:|---|
| 四卡 RTX 6000 Ada | 109.28 分钟 | 2 GPUh | fresh 准入时优先选择一张合格空闲卡 |
| 两卡 RTX A6000 | 54.33 分钟 | 1.25 GPUh | Ada 不合格时选择一张合格空闲卡 |

最多启动一个主机上的一张卡，共用一个中央 envelope；不能双端执行、卡中切换或失败自动重放。报价包括 SHA/I/O、仅三个原 head 张量加载、144 次窗口 pair 编解码、传输、全部 111 pair、审计、输出/释放与 25% 失败余量。每 pair 单价等仍为明确未实测的工程余量，不是已测 GPU 加速。[Ada 报价](Q1_WHOLE_QUOTE_FOUR_CARD_R1.json) · [A6000 报价](Q1_WHOLE_QUOTE_TWO_CARD_R1.json)。

GPU profile 固定为 2 CPU（24/25）/ 16 GiB、私有输入逻辑副本上限 8 GiB、CUDA allocator fraction 0.5、1 GiB 独立 SSD 输出和 48 MiB 异盘日志、64 MiB 文件限额。实际 context 独占必须成立；idle 温度低于 70°C，达到 90°C 或资源/独占/硬时限失败即停止并结算，不触碰其他任务。

## 已有准备与实际资产

两端 R3 各 45 项受影响 CPU 控制均通过，含五类真实 Linux 子进程生命周期；使用声明的 GPU/温度/临时账本夹具。两端源包、原生命令及独立私有存储已接受。[双端 CPU 回执](../../../reports/cara_sq_q1_control_dual_cpu_accepted_r3_20261029.json)；CPU 接受不等于 CUDA 数值、真实大张量峰值或科学结果通过。

两卡[33 项资产 SHA/实际身份](../../../reports/cara_sq_q1_two_card_asset_cpu_terminal_r1_20261029.json)已通过。四卡 [32 文件直传](../../../reports/cara_sq_b1_port_terminal_r2_20261029.json)已完成并[释放已知原句柄](../../../reports/cara_sq_b1_port_release_accepted_r2_20261029.json)；R1 + R2 共 38.99 分钟，仍在原两小时 envelope 内。四卡[原独立资产 CPU 扫描](../../../reports/cara_sq_q1_four_card_asset_cpu_launch_r1_20261029.json)运行中，尚未将复制接受升级为真实资产接受。两端实际源 SFTP/SSH CPU 未完整计量，目标已测 CPU、R1 片段与未计量项见[原费用记录](../../../reports/cara_sq_b1_port_cpu_costs_r2_20261029.json)。

原 Q1 manifest SHA 为 `5487f8db32d45a5d0f3304333bf362d9d6ec46fb3181c735d7267b78a6e398fa`；4.12 GB 权重 SHA 为 `565bbb2c9645737327983f4461e4d32627bba465b0a8dc26447edea144e1ff47`。机器可读审阅回执将绑定双端原件、CPU proof、源包、scope、profile 和两份整卡报价，批准后按 fresh 选中主机填入对应已审阅 proof SHA。

## 唯一启动和验收

本轮双端只读恢复均无 Q1 GPU intent/容器/中央预约。中央只读快照为 cap 226、已用 178.061565、保留 16.5、可用 31.438435 GPUh；[原账本快照](../../../reports/cara_sq_q1_budget_readonly_20261029_0210.json)只作审阅，提交前再次核验。

仅在用户明确批准本卡后，使用已 CPU 验证的唯一控制器进行双端原句柄恢复、源/运行时/资产身份与 fresh 独占/显存/温度/CPU/RAM/存储/余额准入；任何已存在 intent 都转恢复，不能重新提交。实际 GPU 开始后，以原起点安排一次预测半程检查和一次预测终态验收；半程只读身份、进度与资源，ETA 变化时更新原检查。完整释放与结算后另做 CPU 选择，失败按原合同收件。

此审阅包不授权 S 采集、Q-END 视频、预算扩容或重放。S 继续完成真实 RAM/存储边界、完整 GPU 入口和整卡报价；108 真实标签齐备后，按共同 19D 语法比较 CFG/DIAG/BR 掩码，符合条件才申请自身端点卡。
