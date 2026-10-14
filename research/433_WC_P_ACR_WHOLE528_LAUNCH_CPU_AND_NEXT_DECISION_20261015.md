# P-ACR 完整卡启动接线、CPU 封口与后续投入

2026-10-15，接续[432 真实生产入口](432_WC_P_ACR_REAL_PRODUCTION_ENTRY_CPU_AND_FULL_POST_INTERFACE_20261015.md)。本轮完成完整 PA528 的单次启动、项目锁下的余额与设备准入、实际费用结算、原句柄保留及 CPU post 接线；**本地控制及服务器R2实际入口／启动CPU已经接受，原进程结束；没有新GPU许可或提交。**

## 科学问题和固定范围

在四个已有 CAL/seed0 上复放冻结 H1，每个场景保留普通父和诊断父，共 8 完整路径。每场景固定三点：step12/23 两个可优化 D，加 step29 的 A 或 step30 的 C 边界。五动作 C/A/D/Pc/Pu 各一次预热、三次正式，12×5×4=240 次诊断，加 8×36=288 次原父更新，共 **528 pairs／1056 CFG、一次加载**。原 gamma、系数和输入不变；同状态 teacher 不用于当前系数拟合。

它回答：单支真实深算及另一支创新量补偿能否在 H1 的真实可改位置取得有用的误差—费用折中。读出单支 D 不提交新锚点，父路径恢复后仍走原 H1；原父视频的评分用于诊断无扰动检查，不能作为新 P 的闭环结果。

## 启动接线与本地控制

- 新许可绑定完整卡、528 范围、保守 forecast、源版本、配置 SHA 和接受的生产 CPU SHA；旧 48 窗口或 ≤8 规则不能解除当前停止新 GPU 的要求。
- 准入在项目锁下检查实际账本、fresh UUID、A6000/8.6、显存和计算进程。失败不启动模型、不预留或改账本；运行后整卡实际单卡时间结算。
- 默认启动脚本只显示本地方案，SSH/GPU 为零。实际提交保留原 supervisor，再派 post；超时、未知 claim 或 post 派发失败不重复启动原 GPU。
- 自动 post 仅在原 supervisor／child 结束后读取所有原件与全分母；拒绝／缺失／失败保留。外部查收按 ETA 一次进行，服务器预算监督独立维护。

本地 21 项控制通过：合同5、完整 post5、启动11；缺许可的实际入口在导入 native 前拒绝。测试只有假句柄和临时 CPU 夹具，没有 SSH、模型或预算写入。[本地回执](../reports/wc_p_acr_local12_launch_controls_and_early_refusal_cpu_20261015.json)。

## 服务器 CPU 登记与权限（登记内容，结果见下节）

R2 独立目录 `.sync/wc-p-acr-local12-production-cpu-r2-20261015`，原 R1/0dce0a0 及所有数值证据保持。R2 只重验实际入口／资源身份与新增启动控制，CUDA／权重禁止，预计约 5 分钟后一次查收。不执行 528 次真实模型调用或 GPU post。

整卡保守 forecast **7.529994179 GPUh**；原建议 PA1.5 和增强整轮8不是新的实测费用。即使小于单次8，也仍需用户恢复这张具体新 GPU 卡；不把它自动提交，不缩或拆控制。原窗口最后实结79.996377372／cap104.971363333、余24.974985961保持，CPU前后账本SHA须一致。

## 下一步安排

先接受本卡实际启动层 CPU，交付完整范围与投入决定。W3 缺真实连续 sigma／同 H1 C/A/D 标签，保留 T0/T1/T2/T3 的因果收益差比较；不要用当前 PA12 代替拟议8提示词×8状态的泛化标签。P 有实际局部价值之后，才登记 readout 闭环及合法 source refresh，不能把 velocity 直接当 hidden 来源。

论文正式待补：调优 WC/RA 与少步 Native／修正近邻、同26D简单调度、真正冻结共同测试、重复 clean latency／质量与来源成本、第二模型。旧固定归因和冻结确认不重复；F/B 结束，新探索不自动并入。

## R2一次查收结果（04:24北京时间）

独立stage/source **715cae725423bfef8a5a243a0729b80d9c68f5cb**、**1574文件**逐份一致，原CPU **853632**终态／进程结束；完整实际入口与新增11启动控制、5post控制通过。实际bundle **109.252579秒**（生产109.164634），CUDA／权重／GPU为零、预算SHA前后一致。原R1与完整数值CPU结果保持。

[独立接受](../reports/wc_p_acr_local12_production_launch_cpu_r2_independent_acceptance_20261015.json)、[一次原终态](../reports/wc_p_acr_local12_production_launch_cpu_r2_collection_20261015_0424.json.gz)。生产CPU SHA为`d59d68094fb7f5ca990df696f60bf97ba2daa02b823a6dec2af247efe593ada1`，绑定原configuration de64913f与registration46ed9e44；仅实际入口／资源／指令控制，不是528模型执行或全部20原件／93帧评分。

04:25独立只读资源快照：账本79.99637737158223／104.97136333301378，余24.974985961431557，无inflight、项目锁空闲、无计算进程；A6000两卡显存332／24MiB。预算SHA与CPU一致。[快照](../reports/wc_p_acr_post_CPU_resource_budget_readonly_20261015_0425.json)。该快照不代替未来GPU启动的fresh准入。

当前完整卡已经可以具体审查，下一是投入与恢复新GPU的共同决定。新许可必须明确PA528完整卡、源715cae7／config／CPU SHA和实际单卡额度；尚无该许可，不提交GPU。最终后续总路线见[研究路线](../plans/WORLD_CACHE_RESEARCH_ROADMAP_20261015.md)。
