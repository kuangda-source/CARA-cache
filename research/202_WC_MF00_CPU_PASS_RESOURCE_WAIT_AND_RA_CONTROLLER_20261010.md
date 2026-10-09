# MF-00 CPU通过、生产准入与RA控制器首版（2026-10-10）

本轮完成MF-00实际batch的完整CPU验收、真实生产源资产与选定配置检查，并开始本地RA联合控制器的软件实现。**目前新增GPU提交为0；不是接口GPU通过或新方法质量/速度结果。**

## 必要接口CPU与完整卡

[实际batch独立验收](../reports/wc_mf00_interface_sampling_cpu_r1_terminal_20261010_capture.json)：原3603520/3603521终态退出0并消失，703.069631秒，含之前的页读取等待。两flow×成功/最后写出故障共16完整Toy路径、576solver/1152net；成功8路径重读288guided/8latent，24记录破坏、2截断及2最后写出故障控制全部通过，账本SHA未变。该时间是CPU耗时，不计GPUh。

[真实生产CPU](../reports/wc_mf00_interface_production_cpu_r1_terminal_20261010_capture.json)47.613180秒，[选定同源CPU](../reports/wc_mf00_interface_selected_cpu_r1_terminal_20261010_capture.json)33.461055秒；四原PID3613089/3613090/3614406/3614407均终态退出0消失。164载荷与真实checkpoint、guardrail、请求、实际源、预算授权通过，全部15范围/请求变更拒绝。两配置除声明动态字段外绑定相同，CUDA未初始化。

[独立整卡登记](../manifests/wc_mf00_interface_r1_preregistration_20261010.json)和[选定配置](../configs/wc_mf00_interface_selected_r1_20261010.json)：Common/Human seed3，各原WC与成对接口全OFF一次，4完整路径/4视频/144 guided/4latent，完整预测**1.707952637 GPUh**。不是旧16路卡的通过，也不提供ON/重复证据；旧登记、全部源码、判据和结果保留。

## 两次提交前观察

首次默认系统Python3.8.10在`str.removesuffix`处失败，发生在授权/源验证阶段；未建立输出/后CPU目录、未预留预算或启动GPU，见[原失败与回读](../reports/wc_mf00_interface_r1_first_dispatch_failure_20261010.json)。修正仅让远端准入和GPU监督使用已经生产CPU验收的同一`.venv/bin/python`，两处精确替换并逆向恢复原源；冻结164载荷、原启动器和完整范围不修改，见[调度源证明](../reports/wc_mf00_interface_pinned_dispatch_source_20261010.json)。

使用正确环境后已到达现场显存准入，但A6000被其他实际存活PID3601834占用，现场显存约44890MiB。本卡未派发，原输出和后CPU目录不存在、无本项目在途，账本29.895246589658527/77.89524658965853 GPUh、65提交保持。该项是共享资源等待，不是方法或实验配置失败；不终止其他任务。只有现场实际进程消失、显存和共享锁允许时，再显式复验同一完整卡并唯一提交；不因观察超时重启任务。

## RA联合控制器软件进展

[独立控制器](../src/wcomr/cfg_ra_joint_control.py)实现paid-probe `WC_PAID_DELTA_Y`联合C/D选择：真实Cosmos权重8/−7、共享dense anchor、按逻辑36步索引的rho和传播gain、区间风险累积、先评分后实际执行完成才commit。缺表/无来源/非法统计回退D；混合动作或失败不能更新共同anchor，控制器失效后丢弃。评分本身不改变部署历史，不运行teacher或偷用深层统计。

数学与调度参考[已捕获官方Di代理](sources/ra_cfgcache_20261009/wan-di_proxy.py.readonly.txt)和[官方共同控制/commit](sources/ra_cfgcache_20261009/models/wan/racfgcache_utils/__init__.py)，固定revision e17d6a74。WC probe定义与Wan Di定义分开标记，公开Wan表和传播参数不载入。能量用等价非负形式`(8 ec−7 eu)^2＋112 ec eu(1−rho)`计算，属于相同CFG几何的数值实现，不宣称交叉项原创。

[CPU验证](../reports/wc_ra_joint_controller_cpu_20261010.json)含1000组独立直接向量比较、强抵消边界、协议/分支拒绝、36步counter跨周期、评分无状态副作用、失败与混合动作不写假anchor。这是合成数学/状态机证据，**没有生成Cosmos校准表，没有在模型中安装或运行RA策略**。当前新增控制器不改正在准备的MF-00冻结stage。

下一完成必要真实接口并取证，同时准备共享anchor自身轨迹、同状态单次复用干预与正确UniPC续推的极小Cosmos CAL包；完成rho/gain后才能叫BASE-R。随后推进guided目标W1、协调mask/部分MLP及组合完整视频。非必要不增加人工评审。
