# F/B探索材料接收、CPU代数复核与E0资产清点

2026-10-13。本轮将用户提供的新思路登记为独立探索，未启用主线模块、未提交F/B GPU、未写服务器预算。当前主线见[406](406_WC_MAINLINE_AND_ISOLATED_EXPLORATION_MAP_20261013.md)，详细[探索设计](../plans/WORLD_CACHE_SPECTRAL_BLOCK_ISOLATED_EXPLORATION_20261013.md)。

## 1. 材料与版本

读取了引用对话 `6abf4581-4ec8-83e8-8990-3efe11053cf4` 最新三轮，最新轮 `e46cf37a-60b7-4086-848e-6cf2db04bd9f` 明确频率信息与部分Block可先轻量探索，成立再并入。对话/附件是研究建议，执行授权以用户直接指示及当前预算规则为准。

六份输入在[原样副本目录](sources/worldcache_spectral_block_probe_20261013/README.md)保留，包含完整数学、实验、接续与CPU脚本/作者结果；[接收清单](../manifests/wc_spectral_block_exploration_intake_20261013.json)记录各原始路径、字节数、SHA256和逐字节一致。原包未修改。

新增设计明确修订：附件以380为事实截点，旧N2的A=0不能覆盖当前403；“按成本缩减”只适用于具体卡冻结前，冻结后不能删对照/重复；6GPUh是规划，不是实测费用、追加预算或已执行结果。

独立设计复核另修正两处归因：F-Haar/FFT保留已有raw/RA和元数据再加新特征；P_OFF桥接的F仅在D来源合法C/A位置作用，P来源继续A关闭。若将来开启P源一致A，需共享同一读出/动作集的raw对照，不能把增加读出能力算成频谱收益。

## 2. CPU数学复核

状态：**CPU_ALGEBRA_PASS_WITH_BACKEND_WARNINGS**。

审阅脚本后只import并调用`run()`，未调用会覆写附件JSON的`__main__`。Apple Python3.9.6、NumPy2.0.2；三次原始断言均通过且所有数值有限。主要检查包括Parseval、Haar能量、相位丢失反例、不同滤波器诱导距离、CFG交叉项、fresh-KV活跃attention行、stale-KV保守界和旧hidden覆盖反例。

|检查|本地观测|
|---|---:|
|Parseval/Haar相对误差|0 / 0|
|CFG二次式相对误差|2.068e−16|
|fresh-KV活跃行最大误差|1.665e−16|
|stale-KV误差 / 保守界|0.118802 / 1.404851|
|独立einsum活跃行误差|0|
|matmul与einsum最大差|1.249e−16|

原脚本matmul出现可重复divide/overflow/invalid RuntimeWarning，原因尚未定位；结果有限及einsum吻合不意味着可以删除警告。原作者JSON与本地结果有浮点末位差异，所以逐JSON相等为false，不能误解为断言失败。[原复核](../reports/worldcache_spectral_block_math_review_20261013.json)与[警告及独立复核](../reports/worldcache_spectral_block_math_review_20261013_followup.json)均保留。

这些只是合成代数证据，不是实际Cosmos、完整GPUkernel、端到端成本或视频结果。真实rFFT权重/奇偶网格、padding/位置编码、低精度、张量来源时钟仍待隔离实现时检查。

## 3. E0已知资产与缺口

本轮仅本地源码、manifest和已保存回执清点，未下载bulk、未重新SSH核验16个原件存续。区分“已有验收回执”“运行时代码支持”和“本轮远端重新核验”。

|资产|可用内容|不能从中恢复的内容|
|---|---|---|
|392 source-phase16|16自然父轨迹状态的C、旧D参考A、融合A、新P、同状态D双分支速度，latent/timestep及来源元数据/哈希|当前/来源浅层原张量、逐层完整残差|
|396 suffix8|四自然C状态的C/A后缀guided序列、终态、动作、视频|各步浅层频谱、可离线重启的完整层缓存快照|
|400 teacher-first|设计保存同状态teacher c/u速度、latent/noise/timestep和后缀首C速度|不是浅层特征或逐层历史；整卡仍在途|
|P0运行时缓存|层4/10/16/22的分CFG ungated MLP projection、token更新时间/来源与真实D时间|MLP projection不等于完整Block residual；不能直接用于L2/Q2|

16点均从自然P_OFF父轨迹预先选，原动作 **14C＋2P**。Human晚P step26、AV51晚P step26原动作P；396/400的AV51是自然C step27，不能混用标签。依据[选择清单](../manifests/wc_source_phase_natural16_selection_r1_20261012.json)及[392](392_WC_SOURCE_PHASE16_COMPLETE_POSITIVE_RESULTS_AND_CONSEQUENCE_NEXT_20261012.md)。

源码位置：

- [source_phase16_calibration_r1.py](../src/wcomr/source_phase16_calibration_r1.py)的payload仅写五种双分支输出、actual_latent、timestep，共12张量；已保存终态回执登记16原件各约87.6MB，路径位于服务器，本地不存在不是原件丢失。
- [pi0_readout_suffix8_r1.py](../src/wcomr/pi0_readout_suffix8_r1.py)与[teacher_first_velocity_alignment_r1.py](../src/wcomr/teacher_first_velocity_alignment_r1.py)定义后缀和teacher的实际保存范围；进程内DiagnosticSnapshot及fingerprint不等于完整状态已落盘。
- [cfg_paired_probe_forward.py](../src/wcomr/cfg_paired_probe_forward.py)的PaidProbe导出delta_x/delta_y/threshold等标量。真正test_x在昂贵深层前可获得，但需新隔离observer，不能从标量还原。
- [partial_mlp.py](../src/wcomr/partial_mlp.py)定义P0状态，[partial_mlp_production.py](../src/wcomr/partial_mlp_production.py)绑定probe `[B,T,H,W,D]=[1,24,27,48,2048]` 和latent `[1,16,24,54,96]`。旧配置形状可用于起点，具体patchification、padding、位置编码须在新入口核实，不能把两套轴混用。

因此下一步是**补必要资产，不重做已完成teacher矩阵**：F观察器记录预动作固定通道及current/last-probe/working-source/true-D身份；父轨迹重放保持后复用旧标签。B-M8为新层建立合法过去projection，B-L2/Q2建立各自真实残差历史并计费。两条都不允许用当前teacher充当旧来源。

## 4. 数据和主线保护

探索开发先旧CAL，视频桥接另取探索专用新提示词。排除全部CAL、原E2保留提示词和[CONF四新组](../manifests/wc_source_conditional_confirmation_inputs_r1_20261013.json)，即AV46fe9718、Human125、misc2711212、robot043，不能仅换seed复用CONF。新探索split尚未选定，不能声称已有未见评估。

400原teacher任务source4b18478/665保持；本轮先观察2/4父组完成，随后最后一次只读capture确认4/4生成结束、GPU监督和runner退出、kernel释放，原post仍live，状态为`TEACHER_FIRST_RAW_AND_FRAME_CPU_RUNNING`。原件/全93帧终态验收仍待，未据生成结束提前解释结果。405独立确认e48ba58/684最终CPU已通过但GPU未启动；候选fingerprint34ef948e及全部冻结绑定不变。待原post完整验收后按原卡串行。

本轮[文档与冻结验证](../reports/wc_spectral_block_design_validation_20261013.json)核对27个本地链接、六份原材料及10个确认冻结文件均通过；主线src/config/scripts/tests/vendor零改动。观察进度回执变化不是方法改动。

探索预算只登记约6GPUh规划，实际F/B卡仍待完整范围与实测费用；本轮GPU提交新增0、预算未改。原400 GPU成本已按原卡结算，累计69.349719229/cap104.971363333、余35.621644104；CPU终态待，费用不归入F/B。新数学和方案不等于新的论文结果。
