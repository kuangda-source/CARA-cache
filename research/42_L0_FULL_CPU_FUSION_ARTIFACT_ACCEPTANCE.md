# L0两臂融合产物完整CPU验收

2026-10-01；FULL_CPU_FUSION_ARTIFACTS_PASS_NOT_MODEL_TASK_GPU_READY。

真实两臂CPU融合与独立fresh audit均终态通过：fusion1960.417015秒/peakRSS30.8287GiB，audit663.896945秒；18原输入融合前后及fresh官方digest一致，6输出shard/1650实际tensor全finite与dtype/shape/字节digest通过，1050未目标weight原字节不变，两臂各300目标实际bytes_changed。所有原fusion/审计6PIDs退出/CPU锁释放/source与GPU账本不变。仍未实际模型/T5/VAE加载或任务/GPU就绪。

[原fusion全runner](../reports/l0_cpu_fusion_r1_runner.json)/[原监督](../reports/l0_cpu_fusion_r1_supervisor.json)/[独立全产物审计](../reports/l0_cpu_fusion_r1_artifact_audit_20261001.json)/[最后同process观察](../reports/l0_cpu_fusion_audit_r1_live_observation.json)。独立audit source dbe863c/SHAa9caec6f，与原fusion sourcec69e492分别固定，没有把新文档HEAD当旧实机运行版本。local全runner/监督JSON bytes的SHA与独立auditor实际读取的原receipt SHA相同。

两配方新目录位于服务器 `l0-fused-models-r1/cfg_only`、`l0-fused-models-r1/few_step_cfg`，原输入未覆写。CFG权重1.0；few-step1.0后CFG0.5。每臂825/300target/525untargeted/3shard，独立矩阵公式记录全有限且最大abs误差0.0（仅本次CPU融合数值），实际saved tensor重读及未目标基座字节核验通过。索引/config与原基座语义/字节分别一致，VAE/T5/tokenizer明确引用原官方hash验证资产。不能据此称实际native模型构造/加载或GPU行为通过。

## 隔离环境下一门

本项目empty virtualenv `.sync/l0-native-env-r1` 已创建，仍未安装任何runtime包。当前offline索引cache无法解析Torch2.4.1+cu121；不称版本不可得或环境不兼容。

[官方二进制源与传输预检](../manifests/l0_native_binary_sources_20261001.json)：三PyTorch wheel从官方索引得到精确SHA256；索引提供download-r2 host实际GET返回403，原官方download.pytorch.org同文件路径精确206/64KiB ZIP prefix通过。保存原index URL和新download_url，保持官方expected SHA不变。实际大小Torch798979686、Torchvision7073837、Torchaudio3411156字节；只是前缀/metadata，不是full payload SHA或安装。

Flash2.7.4.post1的cu12/torch2.4/cxx11abiFALSE/cp311官方asset ID/size已锁，但官方未发布digest；记UNKNOWN。未来从官方asset取得payload后冻结实际SHA，不称官方SHA验证；实际Torch CPP ABI必须在安装后CPU读取确认。

下一CPU-only获取四个binary/全payload检查、完整PyPI resolved依赖锁/独立env安装、唯一600秒持久回执的native runtime probe（必传--environment-lock，当前新版未执行）。不修改共享环境、不要在新model-dir再重复注入LoRA；完整DiT/T5/VAE加载与实际条件任务门仍待。原WorldCache成本/质量结论不变，未新GPU；新4GPUh clean50与L1额度不能混用，预算决定仍待。
