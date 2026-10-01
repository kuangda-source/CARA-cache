# WC-S0 官方缓存剩余成本与真实 QKV：冻结诊断范围

2026-10-01；接续 S1 真实内核，不重复 kernel-r1，不增加原 4 GPUh，不引入默认人评。

## 范围与证据用途

同一 resident Cosmos2B 模型，官方 WC、固定 CAL8 第一行 `av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632`、seed0、93帧/432×768、35请求步/36实际步/72 CFG调用/horizon70。保持原 eager、guardrails、offload、cache参数与已验收 decoder cuDNN policy。选择在新结果前固定，不因拒绝或观察换场景。

第一轮只 profile：CUDA events 包围 net inclusive、probe/deep self核心、self Q/K/V/output projection、cross核心、MLP、官方 optical-flow/warp/saliency 函数；同步wall记录原阶段。记录完整逐调用events；inclusive不能与子项相加。一次 cold 单场景的诊断profile不是clean速度确认，不能归因纯device kernel执行时间。

第二轮只capture：在实际 self `attn_op` 入口（Q/K norm和RoPE之后）采集调用1/2/71/72、层2/14/27，共12个QKV，保留实际CFG slot/counter、shape/dtype/stride、finite、原tensor bytes SHA和文件SHA。预期 `[1,31104,16,128]` BF16是待验证接口假设。复制到CPU后即落盘，不保留所有GPU张量；bulk `.pt` 留服务器ignored目录，Git只保留小回执。capture含CPUcopy/IO时间，不能当速度比较。

观察器不替换QKV/output，不调用额外model真值，不改cache/RNG或任何sparse policy。两轮原trace、blockcounts、sampling、latent witness/拒绝均保留；相同latent/trace支持只读观察一致性，不是人工视频质量或稀疏方法验收。官方拒绝不另行保存输出。

## 预算与依赖

余额1243.785096秒，唯一scope预约750秒、child timeout740秒、5秒kill和15秒准入余量，所有load/import/failure/IO/flush/release按单GPU监督wall结算；保留至少约493秒后续真实QKV候选误差门。fresh UUID/VRAM/compute PID、global `.sync/f1.lock`、existing cap4和任何inflight拒绝；只观察同identity，不重复launch。

执行前：完整checkpoint SHA、六runtime文件/源码补齐/采样器/outcome、项目依赖/输入/setup SHA匹配；实际Cosmos Torch的CPU观察器/预算门和validate-only先通过。模型加载后查实际28层/16heads/D128/minimal_a2a绑定。profile/capture分离的CPU契约测identity、cache计数、异常传播、nested events/恢复命名空间、call/CFG选取、互斥范围；这些仅实现证据。

## 决策

先根据 WC 后 deep self-attention 实测占比判断上限，再在真实QKV比较dense、同内核no-PV全块、数据驱动块选择；路由/packing成本必须包含。固定band上一轮误差很大，尚不接入视频或三档自由调度。该轮没有训练、付费评价或视频质量—时间方法结论。

## R1保留失败与R2修复

R1/source1824d1c，监督/timeout/runner PIDs2550284/2550298/2550300全部退出。缺少历史supervisor的PYTHONPATH导致实际import来自原生editable Cosmos，不是已固定runtime；在加载模型前`worldcache_utils` ImportError，无forward/capture/profile。独立失败审计payload/SHA/账本/释放通过，完整69.455333966762秒已计入现有额度，余1174.329762秒。不能把这个失败称生成结果。

修复明确sys.path runtime与两个package，supervisor恢复历史PYTHONPATH并validate后再准入；新增CPU-import-check，用CUDA hidden和lazy-init拒绝核对实际Inference/WC/minimal_v4/attention origin及SHA，不构造模型。R2使用新stage/launch身份，不覆盖或重跑R1；750秒范围/同一场景/原4h cap不变。CPU6控制仍通过，实际import-origin门待验收。

R2最初CPU full-import被TransformerEngine/Triton导入期autotune benchmarker的驱动探测拦住（0 active drivers），未GPU提交/未改账本。CPU-check增加仅导入期driver guard：提供返回拒绝执行函数的benchmarker factory，其他driver访问仍拒绝，进程退出即消失；真实GPU分支不做这些patch。这是guarded源码来源检查，不能当真实模型/内核parity。
