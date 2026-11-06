# 831 — M2固定源码缓存转移与导数CPU接线

M2开始具备可执行的校准转移：原WC/RF算术保留，缓存与buffer显式传入、传出，保留C写入及梯度。五项本地CPU检查通过；尚未验证真实Cosmos权重或视频终点伴随。M1原GPU继续运行，未读取部分科学结果。

[组件R4原接受](../reports/cara_read_write_transition_CPU_component_r4_20261101.json)与[准备汇总](../reports/cara_read_write_M2_transition_preparation_r1_20261101.json)记录：

- flow关闭/开启分别完整36更新、72CFG分支，输出/全部WC字段/buffer与独立固定源码硬执行逐值一致；每个输入状态和原模型均未污染。
- C确实更新previous input/internal等工作状态，后续C保留对当前输入和缓存残差的VJP。两组方向有限差分误差分别约1.39e-6和1.57e-6，实际方向值约0.00864和0.02862，不以近零方向冒充通过。
- 接上原完整UniPC历史后，36步小模型轨迹梯度与有限差分相差约6.88e-9。损失明确为合成latent MSE，不是视频LPIPS。
- 原70-call cycle reset、冻结/eval、未就绪C与inference-mode边界覆盖。R1四项旧通过、R2测试模块注册接线失败和R3修复五项通过原件均保留；最终R4绑定新增Linux参考接口及完整源码SHA。

[原M1状态R6](../reports/cara_read_write_goal_original_status_r6_20261101.json)于19:20:29回读4/14完成、1运行、9未到达、0技术失败。原四进程PID/start ticks存活，原A6000独占且88°C，90°C保护保持。它是运维计数，未读取部分T_DD、LPIPS或曲线。源b930df4b、硬1.95GPUh、20:36:24停止释放及20:46:24硬截止保持，19:38半程/20:28终验仍由同一检查承接。

[M2具体实现和硬行动安排](../plans/cara_next_stage_20261101/read_write/M2_ADJOINT_IMPLEMENTATION_AND_HARD_ACTION_PLAN_R1.md)固定三个估值器：原S局部q、同伴随read-only、完整read+write；相同起点/候选额度、完整硬FIT接受、每次接受重算轨迹价值。下一个实现关是实际Linux导入/namespace、固定槽与来源映射、真实模型VJP及同93帧VAE/Alex终点。当前整卡范围/全段费用尚未冻结，未新增GPU或账本事务，M1许可不延伸到后续卡。
