# L0完整原生源码与隔离运行检查准备

2026-10-01；SOURCE60_VERIFIED_CPU_RUNTIME_PROBE_PREPARED_NOT_ENV_MODEL_GPU_READY。

## 已完成与证据边界

官方 `Wan-Video/Wan2.2@42bf4cfaa384bc21833865abc2f9e6c0e67233dc` 的全部 `wan/` 文件和 `generate.py`、`requirements.txt`、`LICENSE.txt`（60文件/731323字节）从固定Git对象取得，每个Git blob和SHA256一致，部署到本项目独立新目录 `.sync/l0-native-official-42bf4cf-r1`。不是复制带未提交修改的历史工作区；没有改动上游文件。不包含无关examples/media资产。

[完整源码锁](../manifests/l0_native_runtime_source_20261001.json)/[实机全60部署核验](../reports/l0_native_runtime_source_deployment_r1_20261001.json)。导入时生成的Python cache不算上游源码修改。

一次在既有参考环境的只读full-package import观察45秒超时，随后原进程2503544仍处于D磁盘等待；没有重复导入。后续元数据观察确认该PID已消失，但没有保留下游导入结果/退出回执，因此结果仍UNKNOWN，不把观察超时、PID消失或历史环境称为import PASS。当前CPU融合任务仍在实机运行；不同时进行另一份大环境/模型拷贝。

## 环境约束

官方固定Wan要求 Transformers `>=4.49.0,<=4.51.3`。Cosmos现有4.57.1超出此范围，不能直接当本原生管线兼容环境。当前参考环境版本元数据为Python3.11.15/torch2.4.1+cu121/torchvision0.19.1+cu121/Transformers4.51.3/diffusers0.37.1/safetensors0.7.0/flash-attn2.7.4.post1；官方requirements每条版本元数据都满足。它是候选依赖快照，不是新隔离环境或完整import证明。

[实时参考依赖元数据](../reports/l0_native_reference_env_metadata_20261001.json)。源码包顶层还直接导入S2V/Animate模块，`decord`等传递导入不能凭requirements列表忽略；需实际完整import检验。后续在本项目新环境固定依赖，缺项只修新环境，不更新共享Cosmos/Wan环境。LongLive原wrapper推荐环境与当前选定的共同native Wan管线分开记录，不能据native元数据声称原wrapper通过。

## 后续有持久回执的CPU检查

新程序 [probe_l0_native_runtime.py](../scripts/probe_l0_native_runtime.py)已准备并通过语法检查，**尚未实际执行**。必须使用明确的新virtualenv，CUDA可见性为空、模型访问offline，外部GNU timeout最多600秒，新receipt身份。先保存实际PID/阶段，再校验源码/依赖/模块来源，最后保存失败或成功，不因SSH观察超时重启。

检查范围：完整原生Wan包import、meta设备构造真实WanModel与基座825 keys/shapes比较、真实本地UMT5 tokenizer编码、实际导入WanTI2V条件分支scope构造/签名/恢复、全部源码未改和CUDA未初始化。meta不是加载权重；tokenizer不是T5编码器；method构造不是T2V采样。完整DiT/T5/VAE载入、实际条件任务、GPU调用/显存/输出parity均另有后续门。

下一步：先核同fusion-r1三PIDs/固定source/CPU锁至终态并验收两臂全部产物，再新隔离环境及唯一bounded CPU probe。旧reference PID已消失，不重跑无持久回执的旧helper。CPU程序运行前sync/hash部署新probe和`wcomr.wan_t2v_conditional`，不能改正在跑的fusion stage7文件或其deployment。

GPU账本不变3.6512467238638138/4h；新4GPUh提议仅为WorldCache原8/50 clean计时，尚未批准，也不自动授予L1。L1原2h提议来自同4h余额，当前不足；资源齐备后仍排队，不新增训练/付费/人评。
