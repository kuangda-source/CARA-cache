# BANK24 四卡独立重跑与半程、全程验收

2026-10-22 用户明确要求继续后续实验，并为长程实验安排估时、半程与全程验收。本轮沿原 BANK24 科学卡执行：6 个冻结 DEV，D21/A21/NATIVE35 三方法，18 条正式路径和 6 条完整预热路径，864 普通 pairs、1728 CFG calls、一次模型加载、6 条新 Native。四 CAL 固定 gate 不变，DEV 不参与拟合。

## 接入修复与完整生产 CPU

NLTK 修复复用已接受的 75 件物理资源、原模型和依赖。生产运行的 NLTK_DATA 明确绑定物理路径，派发与 supervisor 在 GPU 前核对完整资源哈希。原 15:46 启动在 NLTK 软链接解析处停止的记录、0.075736525161 GPUh 实费及原输出全部保留。

新 attempt 使用独立 output 与 stage，原科学配置保持字节不变。原 scientific ID 为 `wc-scout-dev6-paired-native-full24-r1`，本次 execution ID 为 `wc-scout-dev6-paired-native-full24-ada-r2`。原 R1 控制工具保留，新增 R2 执行器与 R4 native transport。

首个新 CPU R3 在 fixture 启动前暴露私有 Python 的原始二进制缺少 host GLIBC。R4 子进程改为通过已验证的 Python wrapper 启动；保留 R3 失败原件，没有 GPU 费用。source `d0d4b11861adace3f291a751b7da62f8e31914e8` 的 R4 完整生产 CPU 于 16:50:31 单次运行，实际 26.35 秒完成；17:02 收取完整终态后，35 项独立验收全部通过。本地相关 75 项回归、3 项独立 attempt 测试与 8 项 NLTK 控制通过。

- [实际 CPU launch](../reports/wc_four_card_BANK24_full_execution_tools_CPU_R4_actual_launch_20261022.json)
- [完整 CPU 原件](../reports/wc_four_card_BANK24_full_execution_tools_CPU_R4_terminal_20261022.json)
- [35 项独立接受](../reports/wc_four_card_BANK24_full_execution_tools_CPU_R4_independent_acceptance_20261022.json)

CPU 证据和研究判断已通过 `fc7cba54` 发布 GitHub；CPU 接受绑定的生产代码仍是 d0d4b118，后续文档提交不改变运行源码。

## 实际 GPU 句柄与长程安排

- 实际提交：2026-10-22 **17:03:16.061365 Asia/Shanghai**。
- launch ID：`e14a3299-3bd9-44f0-8843-bccecaa70365`。
- GPU1：`GPU-19d4d100-f845-018d-ec30-def1553c01f5`，RTX 6000 Ada。
- stage：`/data20t/gaokuangda/worldcache_workspace/.sync/wc-bank24-fourcard-full-execution-r3-20261022`。
- supervisor：PID 707273 / start_ticks 944485942；post watcher PID 707274 / 同 start_ticks。
- 整卡规划：6.974166667 GPUh，约 6 小时 58 分；上限 8.75 GPUh。该值为保守估计，尚非本卡 Ada 实测结论。
- 预计完成：10 月 23 日 **00:01:43**；最终实际时间以完整回执为准。

| 检查 | 已登记本地时间 | 内容 |
|---|---|---|
| 半程，`cara-bank24` | 10 月 22 日 **20:33** | 原进程、容器、日志错误、完成量、显存、磁盘、锁与费用；按实测进度更新剩余时间 |
| 全程，`cara-bank24-2` | 10 月 23 日 **00:17** | 原完整 24 路、视频/评分/失败分母、冻结身份、真实时间费用、进程和锁释放、独立重算及后续接续 |

两项均为当前聊天的一次 heartbeat，已从实际 automation.toml 读回 ACTIVE、时间和唯一 launch 绑定。半程不早于 20:32:30.061365，终态不早于 00:16:43.061365。按真正送达的时点记录；若仍运行则据实测剩余量更新原检查一次，不重派或反复紧密查询。

[实际 GPU launch](../reports/wc_four_card_BANK24_full24_GPU_retry2_actual_launch_20261022.json) · [自动化定义与读回](../reports/wc_four_card_BANK24_GPU_retry2_acceptance_schedule_20261022.json)

17:06:40.309243 实际 admission 确认原 supervisor/post/inner/runner 和容器均活、compute PID707498、显存 21066 MiB、UUID 锁持有；新预留 8.75 GPUh。池 used 116.900759633932、reserved 25.25（旧未知责任预约 16.5 + 本轮 8.75）、available 83.849240366068；原失败实费保留。9 项离线准入核对通过。[技术原件](../reports/wc_four_card_BANK24_full24_GPU_retry2_admission_20261022.json) · [准入核对](../reports/wc_four_card_BANK24_GPU_retry2_admission_acceptance_20261022.json)。科学结果须待全卡完整原件及独立验收；实验主表不因 CPU 通过或 GPU 启动增加接受行。

17:08:49 一次有界技术日志核对进一步确认：17:07:21 原生产入口已 **Passed guardrail on prompt**，随后实际进入视频采样，首条完整预热路径已到 9/36 steps。此前 NLTK 故障点已在真实 GPU 路径上通过；本记录不读取视频或中间质量。[实际启动日志](../reports/wc_four_card_BANK24_GPU_retry2_guardrail_and_sampling_startup_20261022.json)。

## 验收后的推进顺序

1. BANK24 全量原件与实费接受后，完成既定同 D 配额和 X-R 离线 CPU 诊断。
2. 推进原完整 1624 区间标签/独立动作价格卡：4 CAL、1624 正式格、14 完整路径，保留已有具体 12 GPUh 批准；先完成该卡自己的四卡生产 CPU、整卡报价与共同账本准入。
3. PG-P1 单预算生成闭环，PG-P2 同信息/候选数/校准费用下的归因消融，PG-P3 第二预算与第二模型/设置重校准，PG-P4 冻结后新 TEST。各卡全范围估时后串行执行，每张长卡安排半程与全程验收；已授权范围内继续推进。

[面向 CVPR 的贡献判断与实验优先级](638_CARA_CVPR_CONTRIBUTION_AND_EXPERIMENT_PRIORITIES_20261022.md)：核心是把连续修正的已证实价值，转成相同实测时间与可比校准机会下优于强简单前密方案的自动生成策略。

## 20:36实际半程更新

原24位置已全部报告完成，GPU结束18:54:06、实费1.845248657494GPUh；原GPU/CPU post/容器退出及锁释放。半程已完成删除，00:17全程保持。[642技术原件与后续](642_WC_BANK24_HALFWAY_EARLY_COMPLETION_20261022.md)。
