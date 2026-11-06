# W3 联合CFG刷新区分：H-T38（CPU准备后执行）

2026-10-08，在D46新seed结果和[152条件分析](../research/152_WC_W3_D46_EXISTING_CONDITION_CPU_RESULTS.md)曝光后提出；独立下一轮，保留原实验、正负结果、判据与费用。只继续WorldCache/W3，不训练Head/LoRA、不搜索额外位置、稀疏或引入人评。

## 问题和假设

seed0旧正例在step23的CFG0本来已D，D46把本步变为D/D；seed2原来C/C，D46只变为C/D并使终点LPIPS退化2.9201%。年龄和生成状态同时不同，现有记录不能证明CFG误差抵消。**在同一seed2、同一step23、同一快照上，联合D45/D46能否优于单D46，并且是否优于原C/C？** 这是有限干预，不将年龄1/2拟合成规则。

冻结生成器和原WC近似器。三个实验臂：BASE不干预、SINGLE只强制call46完整计算、PAIRED只强制calls45和46完整计算；两CFG都是同一个solver update。之后各臂恢复同一个原生自适应策略，禁止回放固定父掩码或用未来teacher挑动作。PAIRED是两当前调用干预，不能冒充单动作RV标签。

## 完整范围

`WC-W3-PAIRED-CFG-R1-20261008-A`，独立run `wc-w3-paired-cfg-r1`，复用seed2原请求与匹配Native参考。模型、dense/eager、guidance7、768×432/93帧/16fps、35请求/36 UniPC-Karras更新/72CFG、guardrails及源绑定与已完成D46 R3保持。

- 1条新原WC父，在step22/call44的完整状态分叉；8条完整14-update/28-call后缀：OFF1、OFF2、BASE_first、SINGLE_second、PAIRED_first、PAIRED_second、SINGLE_first、BASE_second。
- 5段新视频：WC父、OFF1、BASE_first、SINGLE_first、PAIRED_first。旧匹配seed2 Native是第6段评分/审计视频；不新增Native生成。需要登记该旧参考、旧BASE/SINGLE编码、原runner/score及请求的确切SHA。
- 四组严格重复、BASE/OFF与新父轨迹和旧BASE原件的真实输入/输出/缓存/求解器/终态一致；编码字节桥也一致。SINGLE重现旧D46全后缀及编码字节。任何桥失败先定位实现/资源，保留费用，不把不同配置比较为新科学结果。
- 两个当前动作从同一个pre45状态、同一个call45模型输入出发；SINGLE和PAIRED的call46模型输入必须相同，均只使用合法自身CFG历史、付费probe且当前年龄合法。两臂call45输出和pre46网络缓存可以因干预不同，不能错误地要求整个pre46状态相同。记录差异并检查其来自唯一已声明动作。
- 实际D45/D46计数必须分别核对。call45和46之间没有solver latent更新；所有剩余calls47–72按自身状态native建议，保留70reset及71/72强制D、拒绝/有限性/完整恢复/两CFG历史。
- 全部接口检查、严格重复、异常恢复、实际生产延迟导入/源码资产/绑定与真实入口CPU检查先通过；新输出和run不能复用本轮已消耗身份。原解码/guardrail/编码流程与全93帧CPU FP32 Alex LPIPS保持，不改旧评分源或原件。

## 两个主要比较与解释

先报告PAIRED相对BASE的总效果，再报告PAIRED相对SINGLE的增量效果：终点signed LPIPS、三等份逐帧差值及完整分布、每CFG全程完整调用、当前45/46额外完整次数、严格未来47–72节省、两重复诊断wall。恢复/哈希等开销完整计费；本卡不证明干净端到端加速，也不是固定配额实验。

如果PAIRED只比SINGLE好而仍输给BASE，属于修复单槽退化，不能报新方法净收益。如果PAIRED超过BASE，则保留成本条件后再考虑独立seed/场景确认；同一已曝光seed上的新臂不算独立CONF。若PAIRED也退化，说明本点联合操作没有解决问题，不能据此否定整个W3。任何结果都不能单独证明CFG误差抵消，因为尚未获得同状态数值误差分解。

## 费用与执行约定

完整成本从最新两seed实计全流程折算，并增加两条最慢后缀、单进程模型加载差额、120秒准备及20%余量/30秒释放。计算和原件SHA见登记清单；旧Native虽然复用，估算仍保留半张原卡中的Native开销以保守覆盖实现不确定性，不能把它说成将新增Native。

当前累计21.127299587/24GPUh，余2.872700413h，无在途。完整预测不超过2GPUh才按用户已有自主约定执行；不得删重复或拆臂压到门槛下。实际费用全计，旧秒数deadline不恢复，累计24h保持。CPU检查或完整成本不满足时先修复/汇报，不能把CPU准备报GPU收益。
