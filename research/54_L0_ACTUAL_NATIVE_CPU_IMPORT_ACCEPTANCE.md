# L0 实际原生CPU导入与接口验收

2026-10-01。状态：NATIVE_CPU_GUARDED_PROBE_TERMINAL_PASS_NOT_MODEL_GPU。

原生probe-r1/source0da2b73已exit0/CPU20.307796秒，独立终态审计通过；actual Torch/Torch._C/Flash Python与extension origins/SHA、CPPABI false、pinned60完整Wan import（明确仅T5默认设备CPU guard）通过，825meta结构对实际base headers一致、真实tokenizer512与conditional scope签名/恢复通过。原3PIDs退出/环境锁释放，native60/installed93/source与GPU账本未变、CUDA未初始化。没有实际DiT/T5/VAE权重load、forward、完整任务或GPU parity。

[launch](../reports/l0_native_runtime_probe_r1_launch_20261001.json)/[完整终态](../reports/l0_native_runtime_probe_r1_terminal_audit_20261001.json)/[独立安装验收](53_L0_LOCAL93_INSTALL_ACCEPTANCE.md)。实际torch2.4.1+cu121/CPPABI false；所有compiled/Python模块来源在新env，真实hash见probe。guard只在这个CPU probe进程，将唯一attested T5 class-body默认设备查询替换CPU并finally恢复；T5构造默认因此改变，不能称unmodified native/GPU兼容证明。

825张量全meta/shape/key符合真实baseheaders；实际512 tokenizer有10个有效token，输出hash保存。没有加载DiT/T5/VAE权重或进行模型forward。93包原锁不含setuptools，此次actual import没有pkg_resources错误，不作预防性补包或改变图。

下一CPU门：先准备实际component load验证，逐臂串行加载原生DiT/base、CFG-only、few-step+CFG，显式CPU T5/VAE参数加载；检查实际keys/dtype/finite/serialized对应与CPU资源准入、阶段/PID/exit/source/预算回执。官方WanTI2V构造器硬编码CUDA，不能以直接构造加device_id冒充CPU全任务；component CPU门与真正GPU任务/内核验收分开。全weights CPU程序尚未实现/执行，不重跑已通过import/meta探针。

本次没有新GPU结果。累计仍3.6512467238638138/4GPUh（剩1255.511794秒），新4GPUh clean50提议未答；L1也不能自动扩额/挑子集运行，无新增人评/训练/付费。
