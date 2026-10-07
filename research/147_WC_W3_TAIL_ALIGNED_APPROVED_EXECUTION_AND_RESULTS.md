# W3-B 尾段执行约束对齐 R2：批准、执行与结果

日期：2026-10-07（Asia/Shanghai）。本报告随同一个原运行的实际进度更新，当前科学结果尚未完成。

## 当前状态

完整卡 `WC-W3-PLACEMENT-TAIL-ALIGNED-R2-20261007-A` 已获本轮直接批准，唯一运行 `wc-w3-placement-tail-aligned-r2` 已启动，正在初始化。尚无新终点保真、速度或在线调度结论。恢复与固定配额的原 R1 对照结果继续保留；原 R1 第70调用停止的不可行结果和费用不改。

## 批准与执行身份

- 本轮直接“允许”：thread `01a0f1eb-7894-7ed0-a186-d010111e14b1`，turn `01a115a3-fbef-77c1-9d5f-8f817b389fee`，user message `01a115a3-fc36-7350-8aad-bbf2d3eb2ae9`。原件见 [直接答复](../reports/wc_w3_placement_tail_v2_direct_approval_source_20261007.json)，对应此前已提报的新R2整卡例外，不重用已执行R1的批准。
- 完整范围保持：两个已曝光 CAL 场景、seed 0、2 条父轨迹、16 个完整后缀、10 个视频、4 对交换、6 个匹配 Native 的全93帧 LPIPS 损失；Common 配额18/17、Human20/18，各 CFG 分支分别固定。
- 规划名义2.156980347 GPUh、压力2.596709750 GPUh，均为费用代理，未当作硬截止。旧秒数限制取消，累计24 GPUh、全部失败/加载/清理费用和共享资源保护保持。
- 实际代码 source `e4642726754bba73b28c622856bafc3edc33508b`，与通过生产 CPU 的源一致；当前文档提交不替代实际源码身份。
- 执行目录 `.sync/wc-w3-placement-tail-approved-r1-20261007`，GPU UUID `GPU-cebf7119-cf03-23b9-e192-cd196332b704`。只新增直接授权并替换执行配置，保留通过 CPU 的源；原核心模型 fixture 和生产合同测试不重复。
- [执行配置](../configs/wc_w3_placement_tail_v2_approved_r1_20261007.json)及[文件/批准绑定](../manifests/wc_w3_placement_tail_v2_approved_r1_20261007.json)覆盖169份文件。原生产CPU原件SHA `1892b772325409a72ab5752202b89f82ee41e6b3b5d77f792f3582dbb2033567` 保持。

## 实际验证与启动

执行配置实际服务器 CPU 准入验证用时 **12.0568797588 秒**，exit 0，新增授权、原生产CPU、168份原源及9份上游源的闭包通过，账本未变。原件见 [服务器回执](../reports/wc_w3_placement_tail_v2_selected_preflight_native_20261007.json)，SHA `2ab6fa10f496be2683fe52189f80946e61a1daf128069b90961e8858df5e5475`；独立核对见 [审计](../reports/wc_w3_placement_tail_v2_selected_preflight_audit_20261007.json)。这仍属于 CPU 准入，不是视频方法收益。

[唯一启动记录](../reports/wc_w3_placement_tail_v2_launch_20261007.json)记录 supervisor **3040329**。现场读取确认该句柄及 runner **3040347** 均存活，cmdline 的 stage/run/source 与获批卡一致。启动时目标GPU24MiB、无计算应用；随后原 runner 正在初始化，尚无新视频。后续只跟踪这两个原进程，不因观察超时重启或修改在跑源码。

首次GPU现场确认见 [原运行观测](../reports/wc_w3_placement_tail_v2_initial_live_20261007.json)：模型加载 **86.6626909915 秒**，`CUDA_initialized=true`，实际网络为 `MinimalV1LVGDiT`，目标GPU计算PID **3040347**、显存24450MiB，与原runner一致；Common父轨迹已进入STARTED。尚无完整后缀、新视频或终点收益，这不是科学验收。

启动前实际已结算 **14.3563403569/24 GPUh**、50 jobs；新任务为第51次。服务器为保护累计预算先预留全部剩余 **9.6436596431 GPUh**，`used_gpu_hours=24` 的在途记录表示预留，并非实际已花完；结束按完整实际wall结算并退回差额。CPU评分在GPU释放后执行。

## 当前实验所回答的问题

R2 只改变原R1的尾段附加条件：69/70保留冻结的实际动作，记录原生建议与计划的差异；不再要求干预后的原生建议也相同。前缀、原生初始化/reset、71/72完整计算、缓存合法性、自己的CFG历史、有限性、年龄、不可变计划、全部重复对照和配额仍约束执行。

完整调用次数相同并不代表实际时间相同；本批为离线固定动作的位置干预，不能宣称形成了在线路由或单步刷新收益训练标签。通过CPU或进程健康也不证明真实四对交换可行。每对交换的正、负和不可行结果均按原分母保存，不补换场景/seed，也不缩减对照绕过2h门槛。

## 后续验收

先核对原进程终态、实际费用、GPU/锁释放和全部原件/源码SHA，再验证2父/16后缀/10输出、重复轨迹、每CFG配额及全部冻结动作。通过完整科学验收后，对6个新候选执行匹配Native的全93帧CPU FP32 LPIPS，报告4对signed交换，联合真实费用解释收益与适用条件。若发生负结果或不可行，先区分实现、监督目标和指标对齐问题，保留旧判据，下一新假设先登记；不自动加入训练、稀疏扩大搜索或人工评审。
