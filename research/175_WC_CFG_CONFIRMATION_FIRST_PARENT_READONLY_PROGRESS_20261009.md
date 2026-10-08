# 新种子机制复验：首条完整父轨迹已保存，第二条与全部动作对照继续

2026-10-09。Human seed3 的第一条 OFF 父轨迹已经完整结束并保存视频。新增测量记录在真实模型上可读取、可独立核对，这是本轮实际进展；还没有接受新种子的完整科学结果。

承接 [174 实际执行](174_WC_CFG_FRESH_SEED_PRODUCTION_CPU_AND_EXECUTION_20261009.md)，原卡 `WC-W3-CFG-MECHANISM-CONFIRMATION-R1-20261009-A` 与原运行 `wc-w3-cfg-mechanism-confirmation-r1` 继续。冻结源 `00b06e61f39bf3bd7f7f2696a70994a0d2ffc0e5`、77 个运行载荷及配置 SHA `7c2bb25419803231941277eb1bfe61f61f3bfa28a7af1f7d01e65c76ac0935a9` 不变。没有新增 GPU、改运行目录、重启或缩减范围。

## 已完成的只读核对

[只读工具](../scripts/capture_wc_cfg_confirmation_first_parent_cpu.py)通过 SSH 使用服务器标准库读取原件，不导入 Torch、不使用 CUDA、不部署到正在运行的77文件目录。[实际审计回执](../reports/wc_cfg_mechanism_confirmation_r1_first_parent_20261009_readonly_audit.json)记录观察 epoch `1791501896.6412547`，原 GPU supervisor/runner `3409913/3409924` 和释放后 CPU waiter `3409914` 均仍在运行。

- 第一条父轨迹 `COMPLETE_PARENT`，wall **866.375353 秒**；72 次网络输入/输出/deep/cache 和36次 solver、1216个最终组件已保存，flags 前后一致。
- 72 个实际网络条件见证与原输入摘要绑定，36 个 solver 原返回及解出下一 latent 的空间、shape、dtype、元素数绑定通过。
- 72 个空有效条件区域摘要、72 个全零条件 mask 摘要由标准库独立重建通过；实际 gt_frames 为 `torch.float32`。这只验证本条记录，不补写旧卡的有效条件信息。
- 视频文件 **903,485 bytes**，文件 SHA `18ada87fe0b29762d25ff78e6625787e73b7bba30d1a4695db264b8473cbd587` 已核对。路径为 `/home/gaokuangda/data/gkd/worldcache_omr/outputs/wc-w3-cfg-mechanism-confirmation-r1/diagnostic/human_199_seed3/OFF/human_199_seed3.mp4`。此阶段没有做完整93帧解码。
- 捕获原部分 runner receipt 的压缩原字节与 SHA，未下载大张量或视频；压缩副本已在本地独立解压核验。第二条 ON 父轨迹记录为 `STARTED`。

首次父轨迹未完成时，工具返回等待状态，没有保存接受结果。父完成后的本次核对不评分，也不把完整卡的成功子集当作终态接受。

## 仍待完成的内容

原完整两父、五起点×四动作×两重复、40对CFG/80次net、120张量、20重复、两个全93帧视频，以及224个条件/76个solver见证全部保持。第二条父轨迹、实际动作误差与自身历史、完整无扰动控制、有符号能量和全部费用，须在原GPU正常释放后由已绑定CPU程序一次完整核验。

已结算底数 **26.279085386/50 GPUh**；第63个提交在途账本的 `used=50` 是额度预留，不能当作实际花费。本条父 wall 不是整卡费用。单次2GPUh及累计50GPUh约定保持，终态按服务器原完整 wall 结算。

本轮属于实际采样与只读进展，没有新端点质量、速度、独立CONF或机制重现结论。[176 近期相关工作核对](176_WC_RA_CFGCACHE_OVERLAP_AND_NEXT_DESIGN_20261009.md)另外记录了新发现的创新点重叠；当前已批准复验继续，不据此取消或改写 H-T48 原主假设。

## 飞书更新后再次核对原句柄

[后续现场观察](../reports/wc_cfg_mechanism_confirmation_r1_post_literature_live_20261009.json)在服务器 epoch `1791502493.8795528` 确认三个原PID仍活，OFF完成、ON继续，日志21/36。绑定CPU仍等待原GPU释放。终态捕获工具也返回活句柄/不捕获终态，没有新提交；这不是执行阻塞。继续相同完整卡及既有释放后CPU程序，不把观察有效期或旧日志标记当作停止/重启理由。
