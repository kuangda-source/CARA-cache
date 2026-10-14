# W3启动失败修复R3 CPU与完整卡投入说明

2026-10-15，接续445。原数值72 CPU、生产R1/R2均已接受；新增“未创建child／child缺runner”完整失败分母处理已通过本地launch12/fullpost7，现只接这版代码的fresh真实生产R3 CPU。

source **047dcf181a3ab706002b2965e74b626e4648deea**，stage `.sync/wc-w3-label64-production-cpu-r3-20261015`，原CPU **860586**，于 **06:49:39.831 Asia/Shanghai**唯一派发。[原launch](../reports/wc_w3_label64_actual_production_CPU_r3_launch_20261015.json)。

预计5分钟；**next_check_not_before=2026-10-15 06:54:39.831（unix1792018479.831499）**，既有自动化“W3整卡CPU最终查收”安排 **06:56一次查收**。完整实际入口及scope4/fullpost7/launch12共23控制、原资源/八请求/18父64+8/864最大pairs、90合成原件、budget SHA/CUDA权重0均须核对。此前不SSH查看partial；未完按余量重估单次查收并结束，失败保留原件，终态完成暂停自动化。

本次不修改或重新查旧stage；没有GPU/模型权重/真实标签/拟合，不能称W3方法有效。scope、原H1和上游模型代码不变。

[完整投入说明](p_w3_e0_20261014/W3_Full864_Whole_Card_Decision_Spec_20261015.md)已列出全卡范围、目标、原件、费用和接续；R3 CPU与具体人类许可仍待。保守forecast11.645828GPUh、建议具体单次计费上限12，原余24.974986不重置；PA7.529994保持可选且原询问未回。全部CPU通过后仅提交该具体卡供人决定，不自动GPU，不恢复F/B或引入人评/训练/OMR。
