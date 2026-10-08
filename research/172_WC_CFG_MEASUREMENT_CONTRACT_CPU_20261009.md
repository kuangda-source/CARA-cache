# CFG测量契约：代码已接入，完整CPU验证待执行

2026-10-09。上一轮完成真实教师、CPU联结和组会飞书，属于实际progress。本轮继续[H-T47](../plans/WORLD_CACHE_CFG_MEASUREMENT_CPU_20261009.md)的低成本记录修订；整体goal active，科学目标未完成，尚无新GPU或模型效果结果。

## 修订解决什么

旧pre45记录的是经过denoise的net输入，新教师捕获的是采样器latent；原solver返回整体与解出的latent摘要也不能直接比较。现明确保留四个测量位置与dtype/shape/device/SHA，不更改旧结果或原记录。gt_frames跨卡摘要不同，新增全量和实际二值条件mask有效区域的独立记录，帮助下轮分辨差异发生在有效条件还是未使用区域；不能反推旧未保存的有效值。

[新模块](../src/wcomr/cfg_teacher_measurement.py)不改变输入、RNG或策略，记录采样起点、实际net输入、post-denoise速度、solver原返回及原循环解出的下一latent。mask需有限、二值且可广播到实际gt_frames；零mask显式记录零个有效元素。原主体输入/输出/动作/状态、40对/20重复和两父无扰动仍保持，新增记录绑定和重复完整性检查。

## CPU完整范围与边界

[预登记](../manifests/wc_cfg_measurement_cpu_preregistration_20261009.json)与[完整载荷](../manifests/wc_cfg_measurement_collector_cpu_r1_preregistration_20261009.json)绑定H-T45/H-T46原结果SHA及44个文件。先提交/推送，然后仅向独立CPU目录同步，旧真实r1终态目录封存不改。

保留flow OFF/ON两组完整Toy集成：4完整父/10起点/80速度对/40重复组/240原张量，原六类失败回滚；增加测量空间/有效区域/dtype/零mask/非法mask/无输入与RNG消耗控制，以及三类记录证据破坏拒绝。独立重建读取全部240CPU张量，并核对448个实际net条件见证与152个solver空间见证。核心CPU成功回执不等于整个控制进程完成，后续独立审计exit0后才形成完整终态。

实际Cosmos采样循环、denoise/CFG、冻结条件和UniPC仍由固定源加载；权重/注意力/编码/解码/writer为Toy夹具。CPU不能提供真实gt_frames跨卡等价、模型质量、GPU显存、端到端收益或新种子确认。当前仅AST/compile与source diff通过，实际CPU及独立原始张量重建尚未运行。

## 接续与资源

服务器原GPU/CPU全部退出、锁可取、无登记在途，实时账本26.279085386/50GPUh、62提交，余23.720914614GPUh；本轮CPU不写账本、不占GPU。不增加训练、稀疏/OMR/DRE或人评。

完整CPU通过后才准备有限未曝光身份卡：确认身份确实未执行、冻结完整控制/重复/历史、生产CPU和实际资源绑定、核算整卡保守成本。下一GPU未选择/派发，单次≤2GPUh在50h内自主、>2GPUh具体确认，不能删范围或拆控制规避。
