# E1完整8显存诊断：唯一GPU提交与接续

2026-10-11。本轮“完整单次8h以内都允许”直接授权下，CPU全部验收及fresh监督准入后已唯一提交；预计2.044575084 GPUh，不再重复请批。目标保持active。

## 实际执行证据

[唯一启动回执](../reports/wc_e1_diag8_gpu_r1_launch_20261011.json)、[原句柄现场观察](../reports/wc_e1_diag8_gpu_r1_dispatch_live_observation_20261011.json)：方法source8a51232，selected配置34af67b63caf3b856819448155840b941f9ccc6aaca294aeec831dae9a8fba0b，监督4048795／后续CPU4048796／首臂runner4048882均存活。监督已fresh准入并登记第76次GPU任务、取得f1共享锁；四臂／全部8位置不变，后CPU只等待原监督。

目前第一臂ORIGINAL_COLD处于导入／加载准备，尚无完成路径或新视频科学结论；观察时GPU24MiB／尚无compute app不能解释为实际采样已完成。随后模型分配、检查点元数据、实际36输出及终态独立审计才回答显存问题。真实终态按原句柄回收，不重投或改在跑源。

[完整sampling CPU](../reports/wc_e1_diag8_sampling_cpu_r1_terminal_20261011_capture.json)16成功／12失败尝试、1008更新／888张量独立重演保持；[actual生产CPU](../reports/wc_e1_diag8_production_cpu_r1_terminal_20261011_capture.json)49.419121秒、两原PID已退出0消失，398原载荷、225输入源、四臂／真实校准与资产／guardrail、13合同／8准入／八故障分类控制及源身份保持。

## 研究问题与范围

原／CPU快照各比较冷启动Human阶段β1，与同一模型内AV28阶段β1→Human阶段W1→Human阶段β1，共四独立加载、8完整计划路径。全部原动作、真实输入、CFG、solver/RNG、完整physical与workspace/prefix reserve保持。已知容量保护后终止本臂进程，进入下一登记fresh臂；未知故障停止余下范围并保留失败和未开始槽，不继续使用异常状态。

元数据区分physical capture前、additional state前、restore/release后显存与唯一storage。终态CPU保留全部8位置，核对36guided/final数值、逐臂source语义、所有已写原件及93帧完整视频解码；完整对照存在才数值比较。没有新增人评、训练或终点LPIPS需求。短前序未复现不能宣称14路径生命周期或完整64已修复。

## 预算和接续

启动前已实结39.183807748／77.895246590、新48余额38.711438842。第76任务在途将全余额暂时预留，账本used字段77.895246590是预留而非已实耗或预算耗尽；按完整监督wall计费，包括导入、四次加载、失败、观察与四次清理。作用于本轮的8h约定保持，服务器全局旧4h字段未改；8h／余额计费保护独立实施，无旧任意秒数限制。

下一只跟踪上述原句柄，终态后自动全scope原件CPU，保留四模型加载和失败分母。按容量／生命周期与直接数值结果决定后续修复和原64补齐登记，不提前宣称P收益或GPU修复。E2完整76路径9.869732459 GPUh具体确认仍待、不拆卡，共享单GPU队列；A确认和P开发继续按v1.11设计。旧官方复现／W1负例／阶段A四CAL正结果与原64技术失败均保留。
