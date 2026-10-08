# 同状态CFG教师实验：生成进度与终态取证准备

2026-10-09。接续[168实际执行](168_WC_CFG_GUIDED_TEACHER_PRODUCTION_CPU_AND_EXECUTION_20261009.md)。本轮新增终态只读工具，并继续核对同一个在途任务；没有新增GPU提交、停止、重启或实验范围变化。

## 已确认的进展

[原句柄现场记录](../reports/wc_cfg_guided_teacher_terminal_preparation_and_live_progress_20261009.json)中，原supervisor3388748、runner3388760与释放后CPU等待3388749均仍存活，实际命令行对应冻结源e9f47f5。真实模型加载98.133秒，首条OFF父轨迹已进入采样，最新日志为26/36更新。这个数字来自运行日志；中途回执尚未写入完整父轨迹，所以不把它记为已验收的26个状态。

选择配置SHAfb5c4e43、在跑64文件以及后处理driver哈希仍等于派发时的原件。两完整父轨迹、两视频和5起点×4动作×2重复仍完整保留；尚无完整父视频、实际局部向量评分或新的科学结论。后续正常结束后才审计真实shape、1216组件、全部20重复、120张量与两视频完整93帧。

## 终态只读取证

新增[原件捕获](../scripts/capture_wc_cfg_guided_teacher_terminal.py)，只通过现有SSH读取原任务。它先确认原GPU、等待driver及其实际评分子进程全部退出，再核对冻结配置/64载荷/driver、源与绑定、共享锁释放、目标GPU进程释放和实际费用结算。原GPU或CPU失败时保留原终态与计划分母，不给成功子集评分。原始回执、评分、日志、监控和预算以压缩原字节及SHA保存；张量和视频留在服务器，不进入Git。

新增[本地标准库重建](../scripts/audit_wc_cfg_guided_teacher_terminal_cpu.py)，在已成功的真实终态取证之后独立检查两完整父轨迹一致性、1216组件、40对/20重复/120张量哈希和五起点、原一步形成的四个S23桥，重算8/−7有符号能量、相对局部MSE与实际费用。全部实际张量已由绑定服务器CPU评分器独立读取重建；本地工具没有重读这些张量，不能替代其证据。

两个工具本机AST与compile通过。实际调用捕获工具时，三个原句柄仍活，因此返回`ORIGINAL_HANDLES_STILL_LIVE_NO_TERMINAL_CAPTURE`与exit2；没有生成终态原件、结论或新增提交。**真实终态捕获和独立终态CPU审计尚未执行。** 这些工具未部署到在跑源目录。

## 费用与下一步

实际结算底数24.908110354/50GPUh、61个历史job保持；第62job在途服务器used50是剩余额度预留，不是已用完预算。新卡完整保守预测1.692834708GPUh仍保持，不作为运行截止。

继续跟踪原三个句柄；正常释放后，已绑定CPUdriver自动完成全范围审计与局部评分，再运行本轮只读取证和独立重建，依据五个状态各自的结果讨论误差抵消与后续历史。局部DD是同状态teacher，不提供终点质量、物理质量或正式RV标签。本轮有实际审计工具准备和原任务生成进度，整体研究goal继续active；不扩训练、稀疏、OMR/DRE或人评。

## 接续进展：OFF完整对照已保存，ON生成继续

[首条完整对照只读核对](../reports/wc_cfg_guided_teacher_OFF_complete_partial_readonly_audit_20261009.json)确认原任务OFF父轨迹已`COMPLETE_PARENT`：72输入/输出/深层计数/缓存摘要、36solver更新、1216最终组件完整记录，flags恢复，真实full按CFG为18/17。实际视频991462字节，SHA2e96e1dd与当前回执及旧BASE实际文件三方相同。完整OFF原记录以[压缩原件](../reports/wc_cfg_guided_teacher_OFF_parent_partial_native_20261009.gz)保存，其SHA和字节数已独立核对。

这个证据确认了当前OFF完整输出与旧BASE相同；没有追认历史跨卡全状态一致，也没有通过当前OFF/ON无扰动验收。ON已通过提示词guardrail并开始实际采样，原GPU3388748/3388760和等待CPU3388749继续存活。源e9f47f5、配置、64文件和driver仍未变化，无新增GPU、停止或重启。

两条父轨迹只完成1条、两个新视频只完成1个；五状态40对/20重复、真实快照显存、局部有符号误差、ON父最终一致性、全93解码、终态实费仍待。先继续原ON轨迹，不提前给局部解释或质量结论。上一轮为工具准备progress与verified wait，本轮为首完整父原件核对progress和原活句柄verified wait，goal保持active，未满足complete/blocked条件。底数24.908110354/50GPUh和第62job在途预留保持。

## 接续进展：真实共享起点与首嵌套状态已开始采集

[共享起点原件核对](../reports/wc_cfg_guided_teacher_shared_origin_partial_readonly_audit_20261009.json)及[该时刻原GPU回执](../reports/wc_cfg_guided_teacher_shared_origin_partial_native_20261009.gz)确认：ON实际已到S22，前44模型调用的输入、输出、深层计数与缓存摘要及前22solver输出均与当前OFF精确相同。五起点原范围完整建立，原三个PID仍在运行，64载荷/配置/driver不变。

首S22真实快照的logical copy约2.829GB，要求GPU headroom9.953GB，捕获前实际free34.534GB；owned GPU快照2.319GB。第一个`S23_after_CC`嵌套状态也通过实际捕获准入，要求9.953GB/实际free34.530GB，owned GPU快照2.319GB。这里只验证了这两个真实准入，不是所有五起点通过，也不是进程总显存峰值。原记录中首CC按原求解器一步复用已测速度、calls45/46、deep0/0，其child latent与首S23起点相同，桥的字段已在本地从保存的原回执独立核对。

该时刻已写出两个局部CFG张量文件，实际文件大小/SHA与原回执相同，三个分量的记录形状均为`[1,16,24,54,96]`。首S22 `CC_first`仍因其嵌套分支在执行而标STARTED；首S23 `CC_first`完成、`CC_second`在执行。没有加载张量评分，没有把两个文件计为两组严格重复或完整40对验收。

下一继续全部原5×4×2采集、父S22恢复和剩余生成，GPU释放后才运行已绑定的原始张量重建与全范围评分。当前仍1/2父、1/2视频完成，全部重复、局部抵消解释、完整ON一致性和终态实费待。本轮是实际共享起点及首嵌套采集原件核对progress和原任务verified wait；总体goal active，无重要阻碍，不增加新GPU/训练/人评。

## 接续进展：第一个完整S23的四动作重复原件一致

[首完整S23原件重建](../reports/wc_cfg_guided_teacher_first_S23_complete_partial_readonly_audit_20261009.json)与[现场原GPU回执](../reports/wc_cfg_guided_teacher_first_S23_complete_partial_native_20261009.gz)确认`S23_after_CC`已完成8个CFG对、四个严格重复组。独立逐组比较原记录：1216起止组件/指纹、输入、条件、两个网络输出、缓存、求解器配置、动作事件与三个输出张量的记录哈希全部一致，两次均恢复各自起点。各动作实际calls47/48，C为0深层/D为26深层，paid probe与真实full历史/age均重建；八个实际张量文件大小/SHA及记录形状、dtype匹配。首S22已测速度按原一步产生的S23 latent与全部八个起点相同。

这是**一个起点的原记录和文件一致性核对**，只占完整五起点/20重复组中的4组；没有加载实际张量内容、重建CFG算式或提前计算MSE。全范围实际张量读取、全部五个起点的有符号误差评分、完整OFF/ON一致性和两视频全93解码仍等待原GPU释放后的绑定CPU。DD误差为零由teacher定义，不作为结果。

原3388748/3388760/3388749继续存活，source e9f47f5及64载荷/配置/driver保持。S22余格与其他三个S23仍按原完整范围推进，无新提交/停止/重启，不缩范围。费用底数和在途预留不变；上一轮共享起点原件核对progress，本轮首完整起点四重复原件核对progress与verified wait，goal active，无重要阻碍，不设complete/blocked或扩训练/人评。
