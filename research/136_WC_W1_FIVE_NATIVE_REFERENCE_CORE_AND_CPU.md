# 136｜W1 五原生参考的完整生成核心与 CPU 准备

2026-10-06；源冻结阶段：CORE_AND_LOCAL_SCOPE_READY / ACTUAL_SERVER_CPU_NEXT / NO_NEW_GPU_AUTHORIZATION。

## 目的和完整范围

按[确认窗口 v4.0](../plans/WORLD_CACHE_CONFIRMATION_WINDOW_20261006.md)，补原 CAL 接受输出中五个缺失 Native35 参考；原五索引0/3/4/5/7，不重跑旧 WC/W1，不换原拒绝 robot，原8/7/1分母及两既有匹配参考保持。上一轮已更新设计并完成自适应动作/成本和参考清单，是实质进展；本轮继续准备独立生成能力，不重复旧B CPU。

新增[作用域](../src/wcomr/w1_native_reference_scope.py)、[完整生成核心](../src/wcomr/w1_native_reference_sampling.py)和[CPU 检查入口](../scripts/check_w1_native_reference_core_cpu.py)。[CPU草案配置](../configs/wc_w1_native_reference_core_r1_draft_20261006.json)/[冻结清单](../manifests/wc_w1_native_reference_core_cpu_r1_20261006.json)继承原B CPU146份闭包中的136旧文件，只新增10份；旧CPU/GPU源和stage不改。继承闭包仅复用源码/资产证明，不继承任何卡的GPU授权。

核心会绑定官方类 `MinimalV1LVGDiT.forward`，同时关闭 pipe/net cache flag，防止实例上保留旧替换 forward。每参考正常调用完整生成、真实 prepare一次、36更新/72CFG、所有深层均执行，沿用net.eval和原解码cuDNN策略、guardrail。按原请求识别text/video拒绝，不保存被拒视频；技术异常保留原观测、五参考分母及部分输出。finally恢复forward/开关/钩子；采样后核对backend和参数版本。只记录输出文件/规格链及SHA，全93帧解码和CPU LPIPS在GPU释放后执行，不把诊断wall当部署速度。

## 已完成与待验证

[本机作用域回执](../reports/wc_w1_native_reference_scope_local_cpu_r1_20261006.json)通过，16个损坏scope拒绝，包括减五为四、换拒绝robot、改prompt/seed/grid/权重或视频、丢两既有参考、把预算当GPUauthority。首个本机校验把归档path/sha256字段误当legacy video_path/video_sha256，已在源冻结前修正；错误保留在回执，不是方法负结果。

本机无Torch，未装新依赖，未执行生成fixture或声称实际模型验证。下一用现有服务器Torch2.7.1+cu128，在独立CPU目录测试两完整五参考批次（全接受；text/video拒绝保留），旧实例patch不得执行、完整block/solver/probe计数和出错清理；另核对真实Native类源码/forward identity和实际Pydantic原8请求及仅两项setup变更。仅加载微型CPU夹具，不加载backbone权重；模拟编码文件明确不是视频/codec证据。

## 执行边界与接续

当前GPU未选、authority空、生成supervisor未接线；新卡仅3600秒候选草案，未预付/执行/生成真实参考。当前累计仍12.99974633233337/24GPUh、47jobs无inflight，root账本SHA保留。W3-B 9600秒具体范围仍待回复，不重复提问、不重启旧卡。

CPU核心通过后还需独立生产CLI/监督限时/预算预付与实费结算、终态审计和全帧评分的具体卡绑定，以及实际生产CPU门；不能用本核心CPU通过代替。W1独立范围确认也不能由B批准自动获得。两者保持完整计划优先级，训练/W2/稀疏扫描/非必要人评后置。
