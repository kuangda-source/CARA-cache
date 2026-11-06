# E5早期输出head省算原型与受影响CPU验证（2026-10-11）

已将334登记的H-EARLY-HEAD-ELISION写成独立原型。旧W1、P、RA和当前E4c的399来源字节不改；新实现只在早期CC、α=1且该CFG分支已有合法候选时省掉原head／unpatchify，原候选head仍实际执行。DD、PP、晚期α=.5、OFF和无候选fallback保留原路径。

源码衍生插入经过两层逆AST核对：旧collection的全部原检查先执行，新增条件可还原为原相邻head／unpatchify两语句。RF、Flow Warp、深层循环、缓存更新、双probe调度与原calibrator均沿用原体。新版本拒绝有状态buffer／head hooks／改参数／换head或unpatchify、非法候选。原版本不宣称支持这些新增合同。

`previous_output`在省算分支会记录所选候选；跨版本明确允许且记录这一字段差异，不声称完整旧状态相同。每个安装版本内部的完整物理与owned状态仍必须严格恢复。真D历史、P工作源／投影缓存、实际输出、条件、RNG和其余物理字段都要求等价。

CPU范围：两Flow×OFF／阶段W1／阶段β=1×旧／新，12条完整36更新／72CFG直接rollout；实际重读37张量／对，共222直接比较；step12／26完整物理和owned恢复共24次；另7个动态head拒绝、4个真实paired分支故障尝试，原36步分母和已完成前缀保留，不能修复／续跑poisoned分支。W1显式注册单边候选缺失和双边fallback；晚期融合、P／D及C-after-P覆盖。

执行固定native FinalLayer、28个native Block／MLP的CPU小权重；attention、条件／prepare／unpatchify和latent更新为明确Toy边界。此卡仅验证受影响实现与状态合同，不是实际Cosmos／UniPC全程、视频质量或速度结果。无新GPU、训练或人工评审。源码／manifest先提交再同步独立CPU目录，真实GPU等价与同边界费用卡在CPU通过后另行冻结。

当前E4c仍用原4075406／4075494及CPU等待器4079033；首窗6／24点已读，其余完整原4父／16suffix／24teacher不改或重投。8GPUh以内整卡自主权限保持；E2／9.8697和E3／12.3775原整卡准确批准待，不拆卡或重复问。预算结算以原监督终态与现场账本为准。
