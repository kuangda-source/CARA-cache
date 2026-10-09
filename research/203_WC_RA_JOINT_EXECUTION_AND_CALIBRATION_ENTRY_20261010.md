# RA联合执行接线与本地校准入口（2026-10-10）

在MF-00原完整GPU任务执行期间，新增[联合执行接线](../src/wcomr/cfg_ra_joint_execution.py)：现有成对执行器负责两支真实模型计算，小控制器负责选择；两支完成后才commit共同锚点和区间风险。保留既有protected warmup、新周期与counter尾部规则，失败或不匹配则丢弃执行器和控制器，不假装完成刷新。冻结的MF-00 stage与旧全部源码不修改。

[协议CPU结果](../reports/wc_ra_joint_execution_cpu_20261010.json)通过两个36步过程、浅层先付费再选择、第二分支失败/错误counter/混合动作/错误protected等四类失败控制。该项使用独立分支协议fixture，不是Torch、Toy模型、真实Cosmos或视频收益。

下一新增[实际源码完整求解器CPU卡](../manifests/wc_ra_joint_full_sampler_cpu_r1_preregistration_20261010.json)，仅补受影响的RA接线：两flow各原forced-DD、成对RA全DD、成对RA复用三完整路径，共6路径/216solver/432net。全DD检查36实际guided及终点latent直接相同；复用检查7个warmup DD、28个CC、尾部新周期DD、两prefix先于深层、各层实际访问、条件/RNG和36步controller commit。合成表明确标为fixture，不载入Cosmos候选。原16路矩阵不重跑，无GPU/费用账本写入。

该新CPU卡已实际完成，见[启动](../reports/wc_ra_joint_full_sampler_cpu_r1_launch_20261010.json)及[原件验收](../reports/wc_ra_joint_full_sampler_cpu_r1_terminal_20261010_capture.json)。source 55e10e1，145载荷，3633025/3633026退出0且消失，driver109.295320秒、core19.339928秒；六完整路径/216solver/432net全通过，两flow的全DD实际36 guided和终点latent逐张量相同，复用实际两浅层先付费、深层跳过与28 CC一致。预算SHA前后相同，CUDA未初始化，GPU提交0。这提升到实际WC/RF/UniPC源码配合Toy权重/attention的接线证据，仍非真实2B、校准RA或视频效果。

真实RA本地校准仍待。已有逐分支/混合锚点teacher不能直接当共享锚点表；当前MF-00原生政策与成对native政策等价，也不能代替共同C/D自身轨迹。拟用小CAL共同策略创建一致锚点，真实同状态CC/DD获取post-denoise误差相关性；少量同状态单次复用干预后保持完整UniPC历史、共同DD续推到终点，校准传播gain。表的聚合、阶段/年龄插值、缺表回退、预登记起点和完整GPU费用须在下一执行卡冻结；不凭缺失交叉项补造统计，也不把rho=0/g=1叫合理校准BASE-R。

完成必要接口、RA接线和校准后尽早接联合W1、协调稀疏/部分MLP与来源感知选择完整视频。A/B不要求先各自稳定胜出，保留组合和关键消融；不增加非必要人评。当前本文是实现与校准准备，尚非RA模型策略或方法效果结果。
