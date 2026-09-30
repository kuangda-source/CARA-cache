# L0公共原生T2V单条件分支准备

2026-10-01；NATIVE_T2V_CONDITIONAL_SCOPE_CPU_VERIFIED_NOT_MODEL_OR_GPU_PARITY。

[版本化适配](../src/wcomr/wan_t2v_conditional.py)/[本地7检查](../reports/l0_native_conditional_local_cpu_20261001.json)/[Linux7与真实CPU scheduler](../reports/l0_native_conditional_linux_cpu_20261001.json)/[测试](../tests/test_wan_t2v_conditional.py)。仅T2V的scope adaptation：固定官方Wan源文件SHA/原method导入位置与签名校验；guide1直接conditional，guide!=1保留原negative与CFG运算顺序，finally恢复原method。不改原文件或i2v。真实DiT/text encoder/VAE和GPU parity尚未测试。

## 改动与参照

原官方wan/textimage2video.py来自commit42bf4cf、SHA228f2fabf23014ed41ec6b8cd713d5be7371bb558501c71a62a0258b491a877b；仅对完整t2v body的negative调用/CFG blend加入guide1直接cond、else原代码。检查原co_filename/firstline、唯一精确CFG AST、signature与scope恢复/嵌套拒绝，不拷贝或修改上游文件。

默认参数、同device Generator/seed/noise、文本正负嵌入、mask/seq_len/time扩展、UniPC、解码/输出/offload位置保留。各臂未来使用同一已验证的native入口和显式共同frames/resolution/fps/dtype/seed/offload设置：A原生guide5/50步，B CFG-only guide1/50步，C joint guide1/4步，LoRA缩放按冻结配方，不由samplerguide倒推。CPU检查仅32×32、5帧替身、t5_cpu=True/offload=False/rank0/无分布式，不是GPU offload或整任务就绪。

## CPU证据与数值边界

本地/Linux7同范围检查通过，不相加。完整原生T2V body配真实CPU UniPC、模型/T5/VAE替身：4步旧/适配guide5均8次调用，50步均100次，全部输入/扩展时间点及最终latent逐位相同；guide1分别4/50次，全conditional，三者第一noise相同。不是实机GPU DiT计数、计时或完整视频。

旧stock guide1执行negative+(cond-negative)，BF16舍入可能不等于cond。直接使用cond是明确的CFG-free计算契约，不能对guide1声称stock OFF/ON逐位不变。特意设negative=1000、cond=1.0078125的CPU替身，旧first flow0、新1.0078125；这是风险反例，不是实际视频变差证据。reference guide5保留原精度和运算顺序，没有悄悄强制FP32或变更原生参照。

## 尚未验收

尚未在服务器主runtime启用scope，仅隔离CPUstaging；新Git HEAD不是GPU source。后续完整两适配器资源验收/真实CPU全模型融合，再准备全新隔离官方native runtime包及模型加载/依赖审计，固定实际noise/task/条件接口，完成真实暖场parity/调用数与显存门。此scope不是I2V/control/自回归世界模型适配，原i2v未改变。

range-r3仍同handles/3600CPU/16MiB，不改在跑7source/协议。download终态后全7 SHA/实际600×2finite/825当前base header核验，才关闭owned临时forward并启动有界新CPU fusion。原4GPUh实际用3.6512467238638138，主线质量—时间无一致收益、新4GPUh决定仍待用户；不新增GPU/训练/付费/人评。
