# 139｜W1 自身轨迹同状态诊断：核心接线与服务器 CPU 验证

2026-10-06。**下一轮自身轨迹诊断的核心已接线，实际服务器 CPU 检查通过。**它使后续能够在 W1 当前状态上比较官方近似、W1 近似和完整 teacher；本轮没有加载实际模型、生成视频或产生新科学标签。原[138 七场景终点结果](138_WC_W1_APPROVED_FIVE_REFERENCE_EXECUTION_AND_RESULTS.md)和[v4.1 科学设计](../plans/WORLD_CACHE_POST_REFERENCE_WINDOW_20261006.md)不改。

## 本轮的具体进展

上一 goal 轮完成获批五参考、全帧评分及真实结算，属于 progress。本轮依据[下一轮登记](../manifests/wc_post_reference_hypotheses_r1_20261006.json)，实现必要核心并完成 CPU 原件验证，同样属于 progress；不是等待一个已退出的 GPU 进程，也没有把未执行设计当作结果。

三个场景仍为 misc/AV51 负例和 AV28 正对照，seed0、旧 scalar 参数、旧 fixed mask 不变。原真实 trace 核对：calls45/46/67/68 在三个 mask 中均为 skip，未移动观测点或缩减范围。

[own_state_shadow.py](../src/wcomr/own_state_shadow.py)复用 `FixedReplay` 的实际部署校准器，在原 scalar 替换前捕获官方 prewarp hidden，替换后捕获 W1 prewarp hidden；两个副本只在四个登记点创建。官方对照使用这条 W1 轨迹的 cache 和原源码提取的 warp，W1 端直接使用实际部署的 postwarp hidden/velocity，没有用旧 OFF 轨迹冒充当前对照，也没有重复计算/更新 W1 校准。

完整 teacher 从同一浅层 probe 直接运行剩余 block 和原 final layer。当前 teacher 不调用第二个 cache forward，不回写 anchor、cache、latent、solver history 或后续动作。诊断恢复 RNG、注册 buffers 和 shadow marker，并检查部署 cache/anchor/记录的结构与可用版本；该廉价检查不冒充完整内容哈希，未来实际运行仍须逐调用输出、cache/校准终态、视频与旧 shadow OFF 的不干扰性桥。

每对 CFG 保存当前输入和 timestep 的哈希，两分支必须相同；条件文本分支不要求相同。配对失败、选到 full 位置、缺失登记观测、非有限误差均记录技术问题，不接受较小子集或临时换点。分别记录 prewarp residual、postwarp residual 和 velocity 的 signed 误差；没有新增质量阈值或 3/3 必须改善判据。

## 实际 CPU 检查与修复

R1/source `a1e7926`、独立 `.sync/wc-w1-own-state-core-cpu-r1-20261006`、13 文件；实际 CPU **exit1/6.965765 秒**。Toy 从 BCTHW 转到 BTHWD 后保留了非连续步幅，官方 Gamma 的 `.view` 拒绝该输入。失败发生于 CPU 夹具，原始[失败回执](../reports/wc_w1_own_state_core_actual_cpu_r1_20261006.json)和服务器 stage 保留；没有修改官方源码、核心算法或旧结果。

R2/source `b138422`、独立 `.sync/wc-w1-own-state-core-cpu-r2-20261006`、13 文件；只给 Toy 的嵌入布局和 unpatchify 转置添加 `.contiguous()`，核心模块原字节保持。实际 CPU **exit0/6.137902 秒**，[原回执](../reports/wc_w1_own_state_core_actual_cpu_r2_20261006.json)，原件 SHA `063d2f0826134f739a231659b88c00a9c279e2a92355a8e7df95d2490efcbc70`。

[CPU 检查源](../scripts/check_w1_own_state_core_cpu.py)执行真实 pinned forward 的 AST，使用小型 CPU block 与原真实 mask，而非重新实现 cache 公式。八个配对 fixture 覆盖：

- 原三个 mask × flow OFF/ON，候选自己的 36 次反馈更新、72 调用；shadow OFF/ON 的全部输出、trace、full/skip 计数、最终 cache/anchor 与 RNG 一致。
- 四个登记点的官方近似，在当前候选 cache/input 上用独立 official fork 计算；full teacher 用独立完整 block stack 计算。两种近似的 velocity MSE 均与独立计算一致。
- 额外随机/注册 buffer 夹具验证恢复；`torch.inference_mode` 夹具覆盖无 tensor version 的实际常见上下文。
- 五类不完整/错序/重复/full/越界观测点拒绝；CFG 两分支实际输入不一致拒绝。
- teacher 异常时恢复 RNG/buffer/marker，不产生完整诊断记录或接受标签。

上述是 CPU 接线与不干扰控制，不是实际 Cosmos 网络、GPU bf16 计算或视频 parity。Toy 有 3 个 block、probe depth1；它不能证明实际 28 层网络的误差、显存或速度。

## 独立原件与执行边界

[独立服务器原件审计](../reports/wc_w1_own_state_core_actual_cpu_audit_r2_20261006.json)核对 **189 项原生 SHA**、两阶段原日志/回执、R1/R2 原四个 CPU 句柄退出。确认两 payload 仅 CPU checker 的布局修复不同、诊断核心保持；旧五参考 GPU stage 的 160 文件原字节保持，runtime pinned WorldCache 源保持。

R1 supervisor/child `2969423/2969424`，R2 `2969650/2969651` 均已退出。CPU 子进程 `CUDA_VISIBLE_DEVICES=''` 且禁止 CUDA lazy init；检查确认 CUDA 未初始化。审计器不导入 Torch 或查询 GPU。真实模型运行、新视频、科学 teacher 标签、新 GPU 提交均 **0**。

项目账本前后字节不变：**13.504302792/24 GPUh**、48 jobs、无 inflight，SHA `8d868f727159804f2a6131ffb337c77e992de966a065367c68feed1e331fcdc9`。W3-B 单独授权与新输出仍不存在，旧问题已提报、不重复问，不把本轮自动续接当作该卡批准。

## 下一必要工作

保持 W3-B 原完整卡优先，待其具体答复后按原已通过生产 CPU 的 source 执行。W1 诊断接下来要完成实际生成入口、旧请求/setup/输出身份桥、同 solver 状态观测绑定、监督限时与计费、全卡失败记录和目标对齐汇总，并进行对应实际 CPU 验证与费用估计；复用未受影响的已通过核心，不重复本轮相同 fixture。

三场景诊断仍只是登记设计；纸面 1800 秒不是实际费用上界或 GPU 批准。必要生产准备完成后才形成具体可审阅卡。总体研究目标仍 active，核心 CPU 通过不等于新机制或终点收益；旧 W1 的 4 改善/3 退化、MUSIQ/VQA 分歧、拒绝与失败费用保留，不新增非必要人评或训练。
