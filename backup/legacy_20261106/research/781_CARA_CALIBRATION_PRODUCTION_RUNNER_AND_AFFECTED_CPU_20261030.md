# 781 — 14 GPUh 校准运行器与受影响采样 CPU 验证

本轮接通新的校准 producer 与原模型加载、精度、状态恢复和 sole-runner context 路径。独立 `BUDGET_RUN_SPEC_R1.json` 只定义拟议校准范围，源于原请求合同但使用新 scope；它不是启动批准或科学冻结。14 GPUh 版本为初始1＋SA30＋HC20，共51次双 FIT 查询，加10条预热/教师/控制，共112条完整路径。与 S 比较的是相同总预算上限，实际支出和查询数量分别报告。

## 实现

- `Calibration` 增加显式生产 context，绑定原 launch、完整40位源码、host、UUID、登记、profile、14 GPUh、51/112分母和全分辨率93帧 RGB；保留 CPU fixture 模式，混用拒绝。
- CPU 与生产共用原 `cara_fast_requests_r2.Requests` 路由。查询子策略仅派生该次请求清单，继承原 launch 身份。等价检查改为 Python、NumPy、Torch CPU 及已初始化 CUDA 的完整随机状态摘要。
- `run_cara_budget_calibration_r1.py` 沿用原 BF16/Wan FP32、28块模型、状态复位、参数版本检查和 CUDA 独占握手，不修改原 A32/B36 文件。它要求独立批准、整卡 CPU/报价、原中央预约、当前 guardian 和原 runner grant；重复入口被持久 intent 拒绝。
- 运行器只产出完整校准工件，不写科学冻结、不结算账本。完整终态验收与一次派发入口仍待连接。

## 验证边界

[本地回执](../reports/cara_budget_runner_local_CPU_r1_20261030.json)：27项通过、0跳过，包括全51查询/112路径的合成控制、存储边界和生产身份拒绝；生产运行器目前仅有元数据边界验证，未执行真实模型加载或 CUDA RNG。

[原完整 CPU 发布源复核](../reports/cara_budget_calibration_four_card_CPU_published_source_revalidation_r3_20261030.json)：继续使用 e31cc212836882e80f835bec0f0c9016a07b30af 的原224设计路径/102目标证据，无重跑，不能替代本轮新源验证。

本轮另登记[受影响路径 CPU 卡](../plans/cara_next_stage_20261028/mainline/r2/BUDGET_CALIBRATION_CPU_FRAGMENT_R2.json)：两种 flow 各18条完整设计路径/4次双 FIT 查询，并覆盖三类原失败/不重试与零生成恢复；含失败控制时每种 flow 共42次物理尝试。这是新增代码路径的 CPU 差量验证，不重命名为完整112条生产卡验收。GPU模型、CUDA RNG、整容器生产执行和双端整卡验收仍待。

## 原连接与本次唯一 CPU

第一次提交遇到 Windows 跳板连接重置，未取得远端启动回执。只读恢复先发现登记缺失；一次后续握手超时后，[精确检查](../reports/cara_budget_runner_four_card_CPU_absence_recovery_r2_20261030.json)确认原阶段目录和精确容器都不存在，才按同一登记源继续唯一提交。没有在 UNKNOWN 状态重派。

[实际 CPU 启动](../reports/cara_budget_runner_four_card_CPU_launch_r1_20261030.json)：four_card，stage `cara-budget-calibration-CPU-ada-r2-20261030`，CLI PID2249，登记 SHA `ad82aead3581b68062547fea946615171408c68e324c4d534d6a573ed80316ec`。1CPU/4GiB、零swap、network none、只读根、GPU隐藏；原启动约21:30:44（Asia/Shanghai）。终态以单独接受回执为准，不以提交成功视为通过。

本轮0新GPU、0预约、0中央账本变动。原62个 B36 执行/分析/导图源及 A32 冻结 SHA 均核对不变；S/Q文件和原运行保持。后续仍需完整结果验收、once入口、64GiB实际配额、双端受影响/整卡CPU与完整报价，再申请单次14GPUh启动。

## 本轮收尾时状态

[32项本地验证与原 CPU 待终态回执](../reports/cara_budget_runner_preparation_and_original_CPU_pending_r1_20261030.json)：27项 producer/存储/身份控制＋5项验收器元数据控制通过。原 CPU 容器曾实际确认 running、无OOM且资源一致；后续读取多次传输超时，因此当前终态**未知且未接受**，没有重新派发。1200秒工作 alarm 是已登记的上限，不把经过该时长当作正常完成证据。后续仅恢复原 stage、容器和登记 SHA。

[原跳板诊断](../reports/cara_budget_original_jump_transport_diagnosis_r2_20261030.json)：现有两卡和四卡均早已配置 ProxyJump；“Mac缺少服务器子网路由”不能解释这次跳转失败。Tailscale/TSMP/ICMP均曾收到回应，普通 SSH 间歇超时；任务私有 userspace TCP 配置曾使两层公钥认证完整成功并返回 `minchen-X11DAi-N`，后续仍出现拨号超时/502，故不能宣称已稳定恢复，也不能归因到具体 Clash 规则。旧 FRP 仍 KEX reset。全局 SSH、Clash、Tailscale 未改，服务器未装软件；用户已同意向跳板助手收集失败同期的只读 OpenSSH 与 Clash/TUN 日志。可用入口及仅恢复原S/Q的边界已按先前授权发送给S/Q对话。
