# 828 — 读写干预走通真实Linux模块与完整14请求采集

本轮继续[827采用的可解释主方法路线](827_CARA_READ_WRITE_FRAMEWORK_ADOPTED_AND_M0_M1_CPU_PROGRESS_20261101.md)。推进从本地组件到了两卡真实Linux模块、实际冻结参数类与完整M1采集矩阵。仍无新的GPU科学结果。

## 已完成的实际验证

- **原模块组件接受。** 两卡GPU隐藏容器正常退出/0；20项状态/导数控制、flow OFF/ON八条后缀，以及12条完整受保护请求均通过。实际WC/RF模块globals与原函数来源已验证，耗时65.68秒。[原R2接受](../reports/cara_read_write_Linux_CPU_accepted_r2_20261101.json)。R1因真实`apply_worldcache`重绑forward后未恢复调用方绑定而被外层验证器拒绝，原终态/失败保留；修复CPU夹具恢复后使用新R2容器，没有重启R1。
- **完整矩阵接受。** 从两旧FIT构造14请求：八个四格输出、两个Uniform19、两个独立D8控制、两个新Native；合计504次solver更新、512次实际paired调用/1024CFG分支。两卡真实模块和实际`InferenceArguments`下，完整矩阵两轮共28条小张量请求通过，耗时77.96秒，原容器exited/0。[完整14 Linux接受](../reports/cara_read_write_collection14_Linux_CPU_accepted_r1_20261101.json)。本地可变夹具曾被原冻结参数验证器拒绝，原失败保留；本地改用明确冻结替身，Linux使用实际原类。
- **数据完整性接线。** 每个正式请求走原guardrail、原完整sampler、解码和writer；四格同父状态精确一致，00/11与独立C/D8的最终latent及模拟RGB一致。检查完整solver历史归属、整包cache/来源、实际额外计算、无fallback、完整分母与禁止重复请求。没有计算真实视频保真分数。

## 执行范围如何变化

原同父八后缀科学问题和第8更新选点保持。共享前缀实现需要混合格同时物化两个完整GPU状态；新实现先在同父pre-solver状态分别支付C/D，选择返回的读出和整包写入，随后由原UniPC自然更新全部历史。每输出重复前缀，科学调用242→296，额外54次明确计费。

完整14卡另包含四个等价控制和两个新Native，共512次paired调用。它更容易直接复用完整受保护生成/评分与已有生命周期；没有缩减科学八格或改成局部代理。见[执行R2](../plans/cara_next_stage_20261101/read_write/M1_FULL14_EXECUTION_R2.md)与[冻结manifest](../plans/cara_next_stage_20261101/read_write/M1_FULL14_MANIFEST_R2.json)。这些干预仍是诊断动作，不是免费可部署动作或19D新方法。

## 费用与资源

[整卡报价草案](../plans/cara_next_stage_20261101/read_write/M1_FULL14_WHOLE_QUOTE_DRAFT_R2.json)预计**1.6047625 GPUh，拟硬限1.95 GPUh**：原E1完整FIT请求实测上界、新Dense、15%波动、700秒加载/设置、600秒新增快照开销与600秒停止释放余量。快照项尚未生产实测，报价仍是草案，不是准入或耗费。

两卡只读快照：原GPU空闲、24MiB/0%、46°C、Default；MemAvailable为56,878,841,856字节；系统盘余66,930,909,184字节，约62GiB。新方案保留独立16GiB卷，不能直接套用旧64GiB卷及80GiB空闲门，也不删除旧结果腾空间。该[资源快照](../reports/cara_read_write_two_card_preliminary_resources_r1_20261101.json)不替代派发时fresh准入；未完整重算模型资产SHA，四卡未访问。

## 下一直接任务

1. 对完整14卡接入新runner、prospective16GiB配置、原guardian/supervisor与单次派发/结算接口；复用未变的原生命周期控制，单独验受影响绑定。
2. 完整终态、释放、唯一费用结算之后，再接受两组00/C与11/D8的真实latent/93RGB等价，CPU一次评分完整八对，输出读/写/交互的逐输入及等权结果。
3. 将完整报价、资源与原中央账本边界组合为新卡准入。按用户小于2GPUh规则推进；不把旧卡的单次账本授权或本次CPU接受当作新资金/执行凭证。

本轮GPU提交/账本写入均为0。原A32/B36/S/Q/搜索/E1、WC/RA FIT UNMATCHED与旧CAL/CHECK范围不变，保护TEST未使用。当前仍未建立真实Cosmos VJP或主方法；M1先回答读写机制，之后再推进同伴随read-only/full的有限行动检验。
