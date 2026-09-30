# 下一步：局部解码确定性策略与状态核验

2026-09-30；IMPLEMENTED_CPU_CHECKED_NOT_GPU_RUN。进入依据：同版本两个新进程的latent/decode输入严格相同，decode输出首先不同。具体内部原因未知。

先给现有阶段runner增加解码器运行态见证：真实tokenizer参数/buffer/normalization scale hash、training/dtype/cache设置、实际VAE checkpoint文件hash及调用时flags。参数只读取；不记录bulk tensor到Git。尽量直接固定latent复放，须先证明复放接口与原model.decode一致；若无法低成本证明，沿用已经验证的两新进程完整官方生成，不引入未经核验的tokenizer-only替代。

最小修复候选为只在原`model.decode`调用内部使用cuDNN benchmark=false/deterministic=true的局部context，TF32及denoiser全部保持原值，正常返回/异常均恢复flags。这是一个明确版本化的解码策略干预，不能叫作已确认根因。不得修改共享源码、模型权重或安全检查；不自动降精度或吞掉不支持的确定性报错。

CPU先查context在正常/异常情况下恢复全局设置、输入/output对象/RNG不改变，真实模型decoder状态与源码见证齐全后再提交。两个全新进程串行、原AV/seed0/36点72CFG/WC70，共享监督上限900秒/0.25GPUh，从当前2.176782231h余额扣除，不扩大预算。每次提交重核预算/锁/GPU实际准入。

验收：两个latent/decode输入及原72net输出与旧轨迹严格相同；decoder参数/状态见证相同；decode输出、guardrail、save和93帧解码严格相同。通过只能说本工程样本在所测策略下复现，不能声称全数据集确定性、质量提升或新方法有效。未通过按首个差异与状态证据继续缩小区间，不做无依据参数扫描；不要求人工评审。

## 实现准备

现有记录只保留latent hash，不能直接复放。为保持入口一致，选已验证的两新进程完整生成。decoder_policy.py仅局部cuDNN策略，正常/异常均恢复flags；stage runner在解码前后hash实际tokenizer参数/buffers/normalization、缓存与设置，并现场流式重算VAE checkpoint SHA核对content-addressed blob。CPU针对性22项通过。注意：状态观测与局部策略相对旧门同时变化，若通过只能称局部工程复现解决，不能独立证明benchmark为根因。
