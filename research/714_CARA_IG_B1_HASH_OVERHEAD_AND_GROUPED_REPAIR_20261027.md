# B1工程停止：重复全状态拷贝与哈希超过整卡成本假设

原B1唯一句柄`82bec7e7-c131-412a-b5e5-3e2069609ff9`已按原监督流程停止、释放GPU并恢复模式，实际[0.5827235015070377 GPUh结算](../reports/cara_IG_B1_engineering_central_settlement_20261027.json)。原源码、公式、alpha、样本、配置和原件均未修改。DEV128原CPU评分及中央12h责任、16.5h未知责任保持。

## 实测工程证据

第一条无观测父路径完整结束；第二条在第22/23状态诊断分别约478/497秒，保存两状态后仍未完成整条路径。剩余十状态按该速度已超过剩余阶段预算，还未计必须的72次保存状态重放。因此提前停止原尝试，而不是用部分结果宣告方法成功/失败。[终态回执](../reports/cara_IG_B1_engineering_terminal_20261027.json)保留非零子进程退出、原完整范围及实际账单；这些数据不构成完整12状态或质量验收。

非阻塞Python栈落在`tree_digest → state_components → CompleteStateRoundtrip.fingerprint → ScoutReadoutKernel.evaluate`的GPU到CPU内容拷贝处；GPU遥测显示仍有计算及PCIe发送。首次gdb快照超时，确认无调试器残留；随后有界原生栈与非阻塞Python快照完成。原完整运行计费包含诊断暂停/开销，因此不用于部署速度比较。见[Python栈](../reports/cara_IG_B1_nonblocking_python_stack_20261027.json)、[PCIe遥测](../reports/cara_IG_B1_GPU_transfer_diagnostic_20261027.json)。

## R2修复范围

同一状态下的六原读出与三增益读出共享完整物理快照，每个读出仍在前后恢复全部物理状态、复制私有输入并检查权重版本。原父路径外层的完整状态、owner和输入哈希验收保留；保存状态重放用显式组事务在组前后做完整哈希，禁止脱离事务使用。数值实现继续继承原`_evaluate`，投影、拟合、增益盒、lambda、alpha和样本均不改变。

本地对照覆盖两flow、六状态、六原标签和六增益，共144逐点比对；缓冲区/solver/RNG故障恢复、无外层事务拒绝通过。完整父路径与B1整卡CPU检查也通过；该证据仍是明确小权重CPU，不是修复后真实吞吐或科学结论。新源文件/入口将接受两台服务器复核后绑定独立R2卡，原尝试费用计入同一7GPUh探索上限；不能重复使用原R1启动意图或覆盖其记录。
