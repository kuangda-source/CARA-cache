# P 同状态完整 CPU 的原函数命名空间修复

R2 已通过源码片段匹配，但导入时暴露了另一处包装器适配问题。原函数由 `torch.no_grad` 包装，直接使用包装器的 `__globals__` 不包含原模块的 `torch`；动态重建装饰函数因此报 `NameError`。原 supervisor 4113332／child 4113333 均已退出，CPU wall **30.914753241 秒**、exit 1、0 完整父路径／0 张量文件，444 源码及原失败保持，见 [R2 原始记录](../reports/wc_p_reference_same_state_cpu_r2_failure_20261011.json)。它仍是导入实现问题，不能判为算法负结果。

R3 显式使用 `inspect.unwrap` 获取原函数的命名空间，并核对其中 `torch` 与当前模块对象相同。数值公式、teacher、五候选及最终旧 D-scalar 部署均不变。新的独立目录 `wc-p-reference-same-state-cpu-r3-20261011` 保留 444 来源、两 flow 完整 8 父／32 suffix／48 同状态点、688 pairs／1376 CFG、88 文件／1160 张量、420 直接比较／26 合同拒绝／2 截断拒绝。语法和全部新来源哈希通过，实际 CPU 尚未验收。

独立 terminal capture 已准备：只在原 CPU 句柄均退出后读取全部 88 文件，独立重建五读出的 FP32 CFG 差向量／FP64 MSE归约，保留每点全部候选并验证 D 来源两组逐元素相等、240 次候选恢复、全部自然父／suffix 严格等价；不运行模型、不下载、不初始化 CUDA、不写账本。Toy 结果只用于实现验收。

原 E5 live6 核对 456 来源未改、三原句柄存活，AV_R1 五条路径已各完成 36 次更新，FAST_BETA1 仍待。完整 24 路与自动终态 CPU 继续。P 同状态 CPU 修复不改 E5，不提交新 GPU。累计预算／本轮单卡 ≤8 GPUh 自主规则保持；E2／E3 严格 >8 的原完整卡确认仍待，不重问或拆卡。

接续摘要：[356原函数绑定修复](research/356_WC_P_REFERENCE_SAME_STATE_UNWRAPPED_GLOBALS_REPAIR_20261011.md)：CPU R2/sourcecf02589在no_grad包装器globals处导入失败，30.914753秒／0父／0张量，444原来源保持。R3仅unwrap原命名空间并严格核对torch，五读出数值／两flow完整8父32suffix48点688pairs／1160张量不改；完整CPU和独立实读待。E5 live6原三句柄／456保持，AV_R1五完整路径，全24仍待；前实结41.908688946／cap77.895246590、新48余35.986557644，在途预留非实耗。≤8整卡自主／严格>8具体确认，E2/E3原问待，无训练人评，goal active。以下为历史。
