# 742：A32已在A6000单次启动

用户明确要求“A32gpu 实验能跑就开始跑，其他的可以边跑边补”。A32于2026-10-28 22:17:40在两卡GPU1 A6000实际启动，32条、硬5GPUh。原runner独占上下文已确认。22:58运行检查为8/32完成、GPU利用率100%、88°C，原90°C热保护保持；没有接受完整GPU数值门、保真、速度或F19增益。[运行检查](../reports/cara_fast_A6000_startup_progress_r2_20261028.json)。实际模型加载与569个BF16参数对象已观测，原Wan FP32策略和无outer autocast保持。

A32的目的，是在F19正式比较前建立同设备、同生产入口的强基线：先验证计时/数值，再在两个FIT上有限校准WC、RA和少步Native，使其接近Native的T_DD除以1.5；完整验收及CPU评分后，冻结三种基线。A32本身不证明F19取胜，B36仍需后续独立授权。

## 原运行与资源

[唯一启动](../reports/cara_fast_A6000_GPU_actual_launch_r1_20261028.json) · [上下文/实际起点](../reports/cara_fast_A6000_context_start_confirmed_r1_20261028.json) · [原运行交接](../plans/cara_next_stage_20261028/mainline/r2/A32_POST_LAUNCH_HANDOFF.md)。launch `5a5ab53ebb604433ab83cea06e1ab412`，GPU源码`9eaa5eb3`，scope `d0ad38bc...9694fb4`。锁、EXCLUSIVE_PROCESS和原runner PID/start ticks共同绑定；实际容器2CPU/40GiB，无swap、无网、root只读，只有原runner可见CUDA。

Ada四卡新鲜观测均忙，选择A6000 GPU1，准入时24MiB、0%利用率、无compute apps，主机可用内存约46GiB。原保守48GiB/64GiB余量profile在启动前改为40GiB容器/44GiB主机余量门，双端R14各6项真实Linux控制通过；范围、alpha、输入、数值路径和5GPUh不变。[资源CPU接受](../reports/cara_fast_resource_CPU_acceptance_r4_20261028.json) · [post元数据链双端R15各11项接受](../reports/cara_fast_post_CPU_acceptance_r2_20261028.json)。CPU模拟GPU观测的边界保持，原旧Ada142根因未证明。

[独立存储](../reports/cara_fast_A6000_storage_r1_20261028.json)为用户SSD上32GiB全分配ext4 loop输出及独立HDD上48MiB预分配journal，4GiB输出低水位；没有放松共享盘规则。权重/VAE/guardrail重新哈希，实际英语punkt四文件和固定NLTK manifest重新核对。全语言扫描曾在未使用的挪威语词表发生XFS I/O等待；完整语言包复用此前接受记录，当前只复核实际英语资源。两卡项目的既有路径别名先resolve到物理目录后检查，无资源文件改写。该等待和一次中央回传断线均发生在GPU实际启动前；恢复原中央回执，没有重复预约或GPU提交。

[中央原预约](../reports/cara_fast_A6000_central_admission_r1_20261028.json)保持cap226、used175.8058597668662；reserved由16.5到21.5，available28.694140233133794，恰好一个A32 job。旧16.5未知责任全部保留，两卡旧副本没有计第二次费用。实际GPUh等待原终态wall bill，预约不是已花费。

## 检查与后续

[实际起点检查安排](../reports/cara_fast_A6000_acceptance_schedule_r1_20261028.json)：10月29日00:47一次半程、03:15一次终验，分别为同一对话heartbeat `a32`、`a32-2`。预计03:14:52结束，原硬限03:17:40，监督器保留180秒释放边界。半程仅运维计数；终验需要完整32条/原失败、三臂门、源/参数与原件、独占、热界、退出与锁释放及中央实际结算。成功或失败都保留真实费用，不重派。

通过终态后才以2CPU/8GiB、最多2小时做12对93帧Fidelity-v2 CPU评分并按冻结规则选WC/RA/Native-k。当前未选择赢家，未读取CHECK或保护输入；未启动B36。历史60行科学记录及旧停止决定保持。用户新主线授权阈值已记入AGENTS模板，不能据此拆卡、重试或放松原门槛。
