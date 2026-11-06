# E5 完整采样 CPU 省算验收与真实24入口

2026-10-11。原 R6 source `ac0282350a2c807f321fde070cb8541e921d7f47` 的 supervisor4099331／sampler4099333退出0，2138.910203秒；复用的原 Meta4094620亦已消失。原434文件与账本SHA保持，没有重复 sampler、Meta、GPU提交或训练。

## 已取得的结果

[独立原件验收](../reports/wc_e5_complete_sampling_cpu_r6_terminal_20261011_capture.json)完整重读24个 `.pt` 的888个有限FP32张量，444项新旧直接 `torch.equal` 全部相等，96次物理与自有状态扰动恢复通过。包括flow OFF／ON、固定与当前出生两族、OFF／阶段W1／阶段β=1、新旧两版本，864更新／1728CFG。条件、solver、RNG、实际动作、真D统计与P来源／投影历史一致；跨版本只规范化各自合法且全程稳定的opaque owner对象ID，原R5失败保留。

| 完整 CPU 调度族 | 模式 | 原实际 native head | 新实际 native head | 省掉调用 |
|---|---|---:|---:|---:|
| 固定 | OFF | 72 | 72 | 0 |
| 固定 | 阶段W1／β=1，各自 | 100 | 82 | 18 |
| 当前出生 | OFF | 72 | 72 | 0 |
| 当前出生 | 阶段W1／β=1，各自 | 128 | 94 | 34 |

上述各行在两个flow均观察到；实际叶子Python调用事件、来源记录与R4统计三方一致。固定／当前出生的候选模式分别少18%／26.5625%的**head次数**，不能解释为整模型省时。原生2B Meta合同继续精确复用：AdaLN LoRA、Wan FP32、native unpatchify、原NO_REENTRANT选择性checkpoint及七wrapper变异拒绝。`previous_output`记账差异保持公开，各自恢复通过，未声称跨版本所有物理缓存同字节。

Toy权重、attention、prepare／unpatchify、条件与decoder／writer边界仍在；没有真实新视频或clean端到端耗时结论。

## 已准备的真实完整卡

[347事前设计](347_WC_E5_COMPLETE24_ACTUAL_ENTRY_AND_COST_PREREGISTRATION_20261011.md)与[新生产CPU登记](../manifests/wc_e5_head_complete24_production_cpu_r1_preregistration_20261011.json)绑定完整24路径／四次独立加载、两个已曝光CAL、OFF／W1／β、新旧与反向顺序重复。456文件继承原R6的434字节，加入新实际入口、监督／读取代码、完整CPU原始回执和四监督CPU fixture代码；本地四fixture已有独立结果，服务器实际入口仍待；GPU选卡为false。

下一步在独立服务器stage做实际runtime全部四入口、13合同拒绝、四无guardrail拒绝、四启动资产拒绝、八准入拒绝及四监督生命周期CPU检查。通过并独立捕获原回执后，fresh资源／锁／账本／磁盘验收，整卡预计5.126846282GPUh，按用户本次≤8GPUh直接授权执行；不拆完整范围。结束自动唯一CPU读取888真实张量、12配对和12同版本顺序重复、全部有效视频93帧，拒绝／部分／未开始位置和费用保留。

当前41.908688946／77.895246590GPUh，新48余35.986557644，78次历史提交、无GPU在途。E2／E3原完整above8问题仍待，不重问或替换；P工作参考数学组件旧结果保留，实际cache／两flow／完整恢复未完成。继续WorldCache与已登记E5开发，未新增人工评审、训练或OMR。
