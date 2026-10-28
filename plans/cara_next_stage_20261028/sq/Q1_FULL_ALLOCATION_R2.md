# Q1 整段计费修订与整卡 CPU 验收

2026-10-29。旧 f3 准备因主机计费缺口撤回，原源、stage、回执和科学范围保持。此修订接入已双端接受的主机 allocation 组件，覆盖 guardian、监督器、原件捕获、中央结算和一次 handoff；当前仍无新 GPU 权限。

guardian 在模式准入前持有唯一 monotonic 起点，在绑定的原容器终态及模式恢复后结束。`Q1-billing.json` 只由主机写入，包含完整起止时钟与释放见证；监督器写独立 diagnostic 文件，不能结算或覆盖主机账单。监督器 hard deadline、半程与全程检查均沿用主机起点，连续独占监控的尾部间隔则相对于监督器自身诊断区间校验。

财务验收不要求成功的科学收集。凭据丢失、准入失败、明确未 exec、Docker 未创建、worker 提前退出和超时，都保留完整主机费用；只有原容器终态、全部原句柄与释放可证明时才结算。UNKNOWN 或恢复失败保持 envelope，不推断未启动、不改费用、不换主机重派。成功的技术/科学验收仍另需原数值门、全部实际调用分母、独占/温度与释放控制。

子 guardian 在读取凭据前自写 PID/start ticks 启动回执；父控制器先消耗一次 handoff，凭据或早退异常只转原句柄恢复。启动前恢复双端旧 r1 和修正 r2 的全部 intent/container，中央仍只有同一个 RUN/envelope。新执行 stage 为 `cara-sq-q1-saved-<host>-r2-20261029`，不修改旧 stage。

新 stage 可按原注册/资产/存储 SHA，复用已经完整接受的 33 项资产 digest 和从未使用的私有输出；须 fresh 核对所有文件 dev/inode/大小/mtime/ctime、HF link、原 pinned runtime、输出为空及私有盘。任一变化就拒绝复用。此步骤无需重新复制大张量或重扫 21 GB，不授予 GPU 权限。

执行 profile 和完整报价分别版本化为 R2。主机模式准入/恢复额外预留 100 秒、原容器收尾额外 60 秒，并继续完整 25% 失败余量；工程预测为 A6000 57.658 分钟、Ada 112.610 分钟，均未实测。GPU 硬限仍为 1.25/2；guardian 释放余量显式为 180 秒。111 pair/222 head、12 旧状态、原 `torch.equal` 数值门、零新增 deep/父轨迹/视频及 CPU 后处理范围均不变。旧 R1 profile、报价和旧审阅均保留。

[R4 受影响 CPU 范围](Q1_ALLOCATION_CPU_R4.json)为 51 项核心和 14 项控制器测试；包括 14 个可枚举 allocation CPU 子进程及原监督器/自发布 handoff/后处理 CLI 的实际 Linux 控制。GPU/容器/温度观察均为显式夹具，账本为临时文件。资源沿用 2 CPU / 8 GiB / 1800 秒、隐藏 GPU、无网络、只写独立 stage。双端完成后由独立解析器核验源、容器实际退出、CLI 退出、资源、原字节、65 项完整分母、14 个子进程终态及十类错误回执拒绝，再准备新 GPU stage 并出具完整审阅。

R4 接续审查另发现：父控制器若把凭据管道错误追加到返回的 launch，会改变原子 guardian 回执的字节，导致随后按 SHA 恢复失败。修正后错误只写独立 diagnostic，返回的原 launch 字节保持；新增一次实际 Linux 早退子进程和显式 BrokenPipe 控制。[R5 CPU 范围](Q1_ALLOCATION_CPU_R5.json)为 51+15 共 66 项，其余分母/资源不变；只在同端原 R4 确定退出后使用新的 R5 stage，不改运行中的 R4。R4 原成本/收件全部保留，最终执行准备绑定修正后的 R5 源与完整双端 proof。
