# E1完整CPU验收与E2第三轮接续

2026-10-11。**本轮最大的进展是：新附加CPU存储实现通过了原完整sampler范围，并经真实原件独立复核。** E2的新计时入口在flow OFF已经得到与旧sampler的数值等价信号，两个观察／拒绝处理接线问题已保留并修订，当前R3继续完整验收。没有新GPU视频、质量或clean速度结果。

## E1实际验收

- 原唯一stage `.sync/wc-e1-storage-full-sampler-cpu-r1-20261011`，sourced569caa；监督4040126／子4040127均exit0并消失，CPU全wall3017.693854秒。365冻结载荷和actual runtime hashes保持。
- 两来源规则×flow OFF／ON：128成功＋128末写出故障路径，实际9216 UniPC更新／18432正常CFG网络调用；全部原分母、semantic mutation、截断与末writer故障控制保持。
- 独立捕获实际重载 **4736 tensors**、16整组部分计算参照；原dense／OFF逐位相同，独立重演 **4032 策略决策**。
- 全部 **896 附加CPU存储roundtrip**确认原logical cap保持、serial physical／owned restore两guard、GPU owned storage为0；原physical snapshot建立前两-copy保护及完整reserve保持。原件252个Toy tensor文件／256个Toy JSON writer文件，不是真实视频。
- 本地原bytes、原source／历史文档身份、driver、SHA、故障控制与全量参数组合通过；未初始化CUDA、未写budget。原GPU失败／费用和14／1／49范围继续保留。

[原始终态与独立审计](../reports/wc_e1_storage_full_sampler_cpu_r1_terminal_20261011_capture.json)。这支持进入真实GPU容量区分，尚未证明原step12保护触发的根因、真实显存修复或P方法收益。

## E2实现与CPU状态

原72科学位置保持：四新提示词×seed17／43×五版本40确认，加两CAL×四方法×四平衡轮32计时。为真实计时等价额外加四AUDIT代表路径；总76、2736更新／5472CFG，全部费用入同张卡，不替代原72。

R1在RA双probe后把两个deep访问都标到最后prefix，观察动作失败。R2改为实际counter匹配最新prefix；其flow OFF完成76路径、原旧四方法36 guided／final逐位比较、16计时端点／动作等价和mutation／截断控制，随后在预期text guardrail拒绝控制抛原入口异常停止，flow ON未完成。两个原失败、stage和完整原件保持，不追认为全CPU通过或方向失败。

R3使用原pinned keep_going返回None机制，仅在单路径期间启用，完成及失败都恢复；不改变guardrail判定，其他异常仍传播。新加Native text／video拒绝，八拒绝控制，完整152成功与全部故障／parity／mutation／truncation保留。source5152d4b／213载荷、监督4043674／子4043675现场存活，原目录 `.sync/wc-e2-confirmation-timing-cpu-r3-20261011`；只跟踪这些句柄，不在跑目录改源或重投。完整CPU尚未验收；生产runner／contract当前只有syntax草拟，实际生产CPU及源资产门仍待。

[290首次登记](290_WC_E2_CLEAN_IMPLEMENTATION_AND_FULL76_CPU_PREREGISTRATION_20261011.md) · [291观察修订](291_WC_E2_R1_COUNTING_FAILURE_AND_R2_CPU_CARD_20261011.md) · [292拒绝修订](292_WC_E2_R2_FULL76_OFF_PASS_REFUSAL_FAILURE_AND_R3_20261011.md)。所有比较仍是明确Toy边界内的CPU接线，未运行真实2B方法／新视频／LPIPS或clean GPU计时。

## 费用与下步

实际预算仍 **39.183807748／77.895246590 GPUh**、75历史提交，新48余额 **38.711438842**，本轮新GPU0。用户“这次 gpuh 8h 以内都允许”已落实本轮E0—E5：完整单次forecast≤8自主、严格>8具体批准；不重置累计额度，不拆卡，不恢复旧秒数截止。

[E2完整费用预测](../reports/wc_e2_full76_whole_cost_r1_20261011.json)为 **9.869732459 GPUh**，沿用上一完整64的35%包络规则，以实测Native和A成本保守计全部76 Native及全部每步复用，不用未知clean节省下调。它不是速度结果或硬上界，原约8h容量分配不能当具体卡许可。当前不提前申请；先完成R3与生产准备，再提出可审阅的完整76卡确认。

下一跟踪R3终态／原件独立复核，落实actual十请求／原real prior／guardrail／source-assets的生产CPU；同时冻结E1冷启动失败方法与短前序的真实GPU区分卡和完整费用。A确认继续独立于P科学成功；≤8准入通过可直接推进，>8具体卡完成准备后询问。不引入人评，不改旧科学正负结果。
