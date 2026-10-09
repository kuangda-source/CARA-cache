# 首个 RA 八路径完整工作点已执行（2026-10-10）

`WC-RA-FULL-VIDEO-COMPARISON-R1-20261010-A`／`wc-ra-full-video-comparison-r1`已按单次≤4 GPUh自主规则唯一派发。原WC／JOINT_NATIVE／RA六方法全路径与相同Common/Human seed3的两普通Native参考槽完整保留，合计8路径／288更新／576调用，未拆卡或删对照。当前进入真实方法输出阶段，终点视频和质量结果仍待。

## 执行条件与当前状态

生产CPU source `19d76e79d69b49db7dc16a15902494ea1685770e`、3866274／3866275用时35.243509秒；选定CPU source `45b08ce9a7f21b09f15264e42bbcc0c9ca81fe4a`、3866644／3866645用时32.451839秒，均退出0且消失。226完整载荷不变，实际Native类源／模型和安全管线资产、两请求、19范围拒绝，以及真实表加载和八区间阈值函数核对通过。实际首阈值`0.141488470197544`、表指纹`9ab1d77c303560823ed2f32f43b2982318cdd9835828a46da4835a1b95ea7d7a`与独立重建相同。[生产CPU原件](../reports/wc_ra_comparison_production_cpu_r1_terminal_20261010_capture.json)、[选定CPU原件](../reports/wc_ra_comparison_selected_cpu_r1_terminal_20261010_capture.json)保留。

本地选定器的包导入错误单独修复并保留：[修复记录](../reports/wc_ra_comparison_local_selection_import_repair_20261010.json)。新独立包导入入口不修改已验收的226生产载荷、完整实验范围或CPU结果，不是生产模型或研究方向失败。

[原GPU启动回执](../reports/wc_ra_comparison_r1_GPU_launch_20261010.json)绑定source `45b08ce9a7f21b09f15264e42bbcc0c9ca81fe4a`、相同226载荷、完整费用预测 **3.173496962 GPUh**。启动前fresh A6000 UUID、sm8.6、24MiB／无compute进程、共享锁、磁盘和账本准入通过。现场1791575842.679966：[只读进展](../reports/wc_ra_comparison_r1_live_progress_20261010.json)确认原GPU监督3866900、runner3866913、后CPU监督3866901存活，runner为INITIALIZING、目标GPU338MiB。无完整候选或收益验收，不重复提交或因观察等待重启。

## 预算与后续

启动前实际结算 **31.41828899188821／77.89524658965853 GPUh**，新增48窗口余额 **46.476957597770316 GPUh**；提交68→69，当前一个GPU在途。服务器将余额在途预留，因此used字段暂等于累计上限，状态明确为`RA_COMPARISON_INFLIGHT_REMAINING_RESERVED_NOT_ACTUAL_SPENT`。这不是实际花完；退出按含加载、运行、失败、写盘与清理的wall结算。本地预算仍为启动前结算快照。

只跟踪原卡及三句柄，不改冻结stage或分母。完成后后CPU实际重读六方法与所有接受Native参考的36个guided／latent、完整视频全93帧、实际动作、状态、条件噪声及来源文件；独立捕获原件、费用和GPU／锁释放，再统一CPU全帧LPIPS与逐帧正负分析。参考拒绝原样保留，不补选、不填零。此卡含诊断开销，实际wall是工程成本工作点，干净部署速度另按设计比较。

之后继续guided-W1、协调稀疏／部分MLP及来源感知组合，不要求各模块先独立稳定胜出。旧W1正负、稀疏条件、CFG机制、原失败和旧16路径／6.704 GPUh卡全部保留；旧卡仍超过4且未获具体批准。预算起点不重置，单次完整≤4 GPUh自主、>4具体确认，无非必要人工评审，goal active。
