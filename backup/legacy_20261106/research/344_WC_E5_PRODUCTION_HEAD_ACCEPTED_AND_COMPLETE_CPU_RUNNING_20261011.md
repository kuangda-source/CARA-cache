# E5生产head合同通过，完整数值验证实际运行（2026-10-11）

**最大的新进展是：已把省算原型接到真实生产head配置和原生checkpoint调用合同，并得到独立Meta验收结果。** AdaLN LoRA／Wan FP32、native unpatchify、原生NO_REENTRANT wrapper、子层eps拒绝和七wrapper动态拒绝通过；2B2059174912参数仅Meta、没有权重前向。此前普通head的222等价和15／18次head节省证据保留，但尚不能换算生产速度。

完整24路径CPU现已实际运行：原CPU source1185a47／4095672及4095678存活，429来源字节与预算hash核对保持。Unix1791687631.535时，flow OFF／固定族的LEGACY_OFF、FAST_OFF、LEGACY_W1_ONE_PHASE、FAST_W1_ONE_PHASE四路径写出并标完整，LEGACY_BETA1_ONE_PHASE进行中。它们尚未经过本卡全部444项独立验收，不能用四个写出文件报整卡成功。

## 已完成接线与遇到的问题

生产head外层有SAC CheckpointWrapper；初版只识别FinalLayer，已修为同时校验根包装与内层原生叶子，并保留真实调用。嵌套函数指纹的类上下文差异也已修复，保持所有code_consts与flags严格比较。Meta与完整sampler的CPU导入图分开，sampler复用原已验收actual-source import-only驱动，临时元数据helpers恢复后才执行测试。成功Meta组件按原PID／result／全部426源码hash精确复用。

R1–R4原失败、未开始路径分母、原log和回执全部保留；这些是实现／导入问题，尚未产生否定省算数值等价的实验结论。当前数值实现仍为R4不可变源码，R5只修导入与监督接线，没有换控制器、A目标或缩成smoke。

## 接下来要验收的证据

两flow×固定／current-birth两族×OFF／W1_ONE_PHASE／BETA1_ONE_PHASE×新旧：24完整36步UniPC路径，864更新／1728 CFG，24文件888张量、444直接逐元素比较、96完整physical与owned扰动恢复。实际native leaf Python调用事件、head选择记录和读出成本必须一致。全范围完成后，另次CPU只读原件校验sha、内容、D/P来源／年龄、solver／RNG／条件和全部返回值，不重跑sampler；独立入口`scripts/capture_wc_e5_complete_sampling_cpu_r5.py`已准备。

本卡仍是小权重／Toy attention／条件／prepare／unpatchify／decode／writer下的完整求解器接线证据，不是真实视频、速度或方法质量结论。CPU全部通过后才冻结完整真实旧／新等价与同边界费用卡；加载、搬运、记录、失败费用照常记账，实际单卡预测≤8GPUh自主，严格>8准确整卡确认。

## 原科学GPU与预算

原E4c source6a5910c／4075406／4075494及唯一终态CPU等待器4079033现场存活，399在途字节保持、f1锁busy、指定GPU唯一app4075494。AV28 OFF／ON、Human OFF三个父路径完整；Human ON进行中，完整4父／4事件／16suffix／24同状态teacher继续按原范围完成。全24终态仍优先，随后才实施已登记H-P-W1-WORKING-REFERENCE区分；不提前凭首六点改变本卡。

前settled40.313761639725／cap77.895246589659，新48余37.581484949934；当前used=cap是唯一原E4c在途保守预留、并非费用已经耗尽。78提交，本轮新GPU0，CPU不写账本。E2全76／9.869732459、E3全64／12.377456422原准确批准待，不拆或重问。无训练／人工评审，目标active。

现场证据：`reports/wc_e5_complete_sampling_cpu_r5_and_original_e4c_live_20261011.json`；Meta独立原件及失败链见[343](343_WC_E5_NATIVE_META_COMPONENT_ACCEPTANCE_AND_IMPORT_ADAPTER_REPAIR_20261011.md)。
