# WC-S0：实际 checkpoint 元数据、源码与稀疏接口审计

日期：2026-10-01。状态：CPU_SOURCE_METADATA_PASS；S0 GPU 成本 profile、S1 构建/内核/质量均未通过。延续[计算压缩设计](55_WC_SPARSE_COMPUTE_COMPRESSION_DESIGN.md)，不扩充 GPU 账本。

## 本轮完成的证据

重新验证既有 SSH 路线，实际服务器上执行 CPU checkpoint 元数据核对。R1 在读取权重前因 Python 3.10 没有 `hashlib.file_digest` 退出，9.249026 秒；改为流式 SHA 后用新身份 R2 完成，19.648997 秒。保留两个原始回执，不重跑旧身份。

R2 对当前 Cosmos-Predict2.5-2B 的 4,118,575,006 字节 checkpoint 完整流式计算 SHA256：`565bbb2c9645737327983f4461e4d32627bba465b0a8dc26447edea144e1ff47`。`torch.load(map_location='meta', mmap=True, weights_only=True)` 读取 689 个 tensor，设备全部为 meta；没有物化权重、构造模型或 forward。这个 SHA 是本次实际文件身份，不声称额外核对了官方 LFS digest。

28 层 self/cross-attention 的 336 个投影/归一化权重形状核对通过：self-attention Q/K/V/output 为 `[2048,2048]`；cross-attention K/V 为 `[2048,1024]`；Q/K norm 为 `[128]`。原回执字段 `parameter_elements=2059175652` 实际累加所有 tensor 元素，包含 buffer/extra state，**不是**可训练参数数；不能与历史模型 parameters=2059174912 直接作差推断架构错误。

终态独立读取确认 R1/R2 PID 均退出、本地/远端回执字节一致、当前六个 runtime 源码 SHA 与本地一致、checkpoint size/mtime 未变。R2 CUDA 初始化前后均 false；本轮 GPU 账本 SHA 未变，仍 `3.6512467238638138/4 GPUh`，余 `1255.511794` 秒。只读硬件清单不是 GPU 准入。

证据：[R1](../reports/wc_s0_checkpoint_metadata_r1_20261001.json)、[R2](../reports/wc_s0_checkpoint_metadata_r2_20261001.json)、[终态审计](../reports/wc_s0_cpu_terminal_audit_20261001.json)。本次未安装候选、改运行时或提交 GPU。

## 形状与接入边界

| 项目 | 已有证据及限制 |
|---|---|
| 实际 hidden/residual layout | CAL8 原始回执 `/cases/0/on/shadow_records/0/candidates/official/prewarp_residual/layout/shape` 为 `[1,24,27,48,2048]` |
| 配置/权重 | 2048 channels、16 heads、28 blocks，head dimension 128；checkpoint 与 runtime/config 相符 |
| 推导 QKV | NHD `[1,31104,16,128]`，31104=24×27×48；尚未直接 hook 实际 QKV，dtype/stride/contiguous 仍需运行核对 |
| 当前后端 | `minimal_a2a`，历史 Native 配置 CP=1；不是默认假设的 Torch SDPA |
| 接入位置 | `Attention.compute_qkv` 后的核心 `attn_op`；保留 QKV、RMSNorm、自注意力 RoPE、output projection/dropout |
| 输出契约 | 当前 MinimalA2AAttnOp 将 `[B,S,H,D]` 展平为 `[B,S,H*D]`；候选 NHD 输出也须展平后接原 projection |
| 范围 | zero-based layers 2..27 的 deep self-attention；probe 0/1 和所有 cross-attention 保持 dense |
| CP | 初版仅 CP=1；保留 context-parallel setter 接口，CP>1 明确拒绝，不能绕过通信直接本地 sparse |

当前 attention 文件 `compute_attention` 的注释写四维输出，但实际 operator 返回已展平输出，以可执行源码为准。不得使用另一个较新 Cosmos 版本的 attention 实现替代当前锁定版本。

## SpargeAttn 的实际接口与混杂

选取官方固定 commit `ae5b629ebb41e41f86b3ea2ab5a3283f13ac151a`，11 个相关 Python/CUDA/header/binding 文件逐 SHA 固定：[清单](../manifests/wc_s0_sparge_source_lock_20261001.json)。这是选定文件审计，不是完整构建树、安装或内核验收。

公开 `block_sparse_sage2_attn_cuda` 接收显式 `mask_id`，支持 NHD/HND，但内部 NHD 转 HND 后 contiguous，Ampere 的 Q/K 量化 INT8、V 转 FP16。BF16 Q 分支用 `empty_like(q)` 分配输出，不能仅凭未使用的 `output_dtype` 默认值认定输出 FP16。必须核对实际输出 dtype 和误差，打包/量化/LUT 开销纳入净时间。

A6000 sm86 路径使用 Q/K blocks `128×64`，当前推导 mask 为 `[1,16,243,486]`。map 要求四维 contiguous；LUT 为 int32，共 7,558,272 字节，valid-block-count 为 int32，共 15,552 字节。mask 本身可用何种 dtype/边界处理须 S1 验证，不用上游内部 map dtype 推断所有入口。noncausal 保留率直接用实际保留块/总块计算，公开 `return_sparsity` 的三角分母不用于这个双向 mask。

**关键修正：全 QK mask 仍会 PV 跳过。** 公开 API 默认 `pvthreshd=50`，Ampere 调用 `...with_pv_threshold`，CUDA dispatch PV mode=1；kernel 根据 `local_max_diff + pv_threshold > 0` 决定 PV 计算。因此“full-mask 对 dense”并不能单独隔离量化混杂。

已确认同一 upstream `_qattn` binding 导出 `qk_int8_sv_f16_accum_f16_block_sparse_attn_inst_buf`，对应 PV mode=0 的独立入口。S1 初轮改为：

1. 当前优化 dense 后端。
2. 同量化/布局/打包的 full-QK、**PV 跳过关闭**。
3. 同量化/布局/打包的 sparse-QK、**PV 跳过关闭**。
4. 仅在需要时增加相同 QK mask 下 PV 开/关，分别解释贡献。

初版 wrapper 应调用现有 no-PV binding；不靠巨大阈值声称严格关闭 PV，也不改 pinned upstream。full/sparse 两臂共享量化、scale、packing、输出契约和关闭 PV 设置。以上是源码接入依据，尚无数值或速度证据。

## 构建资源与下一步

实际 Cosmos 环境为 Python 3.10.19、Torch 2.7.1+cu128、TE 2.8.0+cu128.torch27、Flash 2.6.3+cu128.torch27、Triton 3.3.1；没有 SpargeAttn/SageAttention 安装。默认 PATH 的 `nvcc` 为 10.1；只读清单另发现 `/usr/local/cuda-12.2/bin/nvcc`，`/usr/local/cuda` 指向该版本，另有 11.7。

12.2 满足 upstream Ampere 最低 CUDA12.0 条件；不满足 Sage2++ 的 12.8 条件，也不证明与现有 Torch/cu128 extension 的构建/ABI 兼容。下一非 GPU 步骤：取得固定完整构建树，建立隔离 staging 环境，以明确 CUDA_HOME12.2/TORCH_CUDA_ARCH_LIST8.6 做有界 CPU 编译尝试，不修改原 Cosmos 环境/共享驱动，不导入 GPU extension 或自动 CUDA 枚举；失败保留完整回执。具体编译操作尚未提交。

S0 成本方案继续量化 WC 后 probe/deep attention、QKV/output、MLP、flow/warp、统计和访存开销，不拿 Native attention 占比代替 WC 剩余瓶颈。源码的 unused `warped_state` 保留为单独等价性/成本候选，当前没有删除或加速结论。

S0 GPU profile 和 S1 实际 QKV hook、finite/输出误差、带路由净时间需要明确有界 GPU 范围与 fresh 准入。原 clean50/新4GPUh 仍是未批准提案，不自动把全部任务加入新窗口。通过 S1 后才解锁四臂、模块替换或三档调度；不提前引入人工评审。

## 审计程序验证

[CPU 审计程序](../scripts/audit_wc_sparse_interfaces.py)只使用标准库，校验实际回执、预算/source hash、28 层权重、历史 layout 和 AST 接口。真实输入通过；源码修改、终态后回执修改、fixture attestation 下不兼容权重形状三个负控制均拒绝。[输出](../reports/wc_s0_source_shape_audit_20261001.json)、[验证](../reports/wc_s0_interface_audit_validation_20261001.json)。这是证据完整性验证，不是 sparse 方法正确性或模型 parity。
