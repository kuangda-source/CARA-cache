# WC-S1：固定完整源码与隔离 CPU 构建

日期：2026-10-01。当前状态：完整upstream两扩展已CPU构建并fresh审计通过，无PV wrapper本地/实际Cosmos Torch的同3项CPU契约通过；动态导入/真实内核/吞吐仍未验收。

固定 upstream commit `ae5b629ebb41e41f86b3ea2ab5a3283f13ac151a` 的完整80文件已获取，17,306,415源字节、16,597,007压缩字节。每个文件均匹配官方Git blob SHA及本地SHA256，11个S0选定源文件完全一致；无submodule。大图片/源码/压缩包只在ignored staging，Git只保存[完整来源锁](../manifests/wc_s1_sparge_full_source_lock_20261001.json)。

[实际构建资源清单](../reports/wc_s1_build_inventory_20261001.json)确认Cosmos Torch2.7.1+cu128、setuptools79/packaging25/ninja1.13、g++9.4、CUDA12.2均在。默认shell ninja1.10与Python包ninja1.13不同，实际构建PATH优先原venv/bin。预检可用内存约55.5GiB/磁盘约624.7GiB；提交前再次核对，不当作GPU准入。

[获取程序](../scripts/acquire_wc_sparge_source.py)不执行源码；[构建监督](../scripts/build_wc_sparge.py)与[CPU入口](../scripts/wc_sparge_build_entry.py)以独立源码/输出目录构建，复用已有Torch与ABI，只读原环境、不pip install。固定CUDA_HOME12.2、sm86、CUDA_VISIBLE_DEVICES空、MAX_JOBS2、900秒cap；upstream nvcc每任务threads8也保留，不声称总共只有2CPU线程。entry明确禁止GPU枚举和lazy init，只有cpp_extension的availability查询返回false以避开驱动查询。guard是单进程构建适配，不修改upstream或模型运行时。

只运行upstream `setup.py build_ext`，保留其完整目标和自带generated instantiation；build前后对原80文件fresh hash，不把生成的CUDA源当作upstream修改。两扩展artifact SHA和log/PID/终态独立记录；编译成功也不等于安装、导入、ABI动态链接、真实kernel或质量收益。

本地[3个有意义的负控制](../tests/test_wc_sparse_build_controls.py)通过：源文件hash漂移时不产生child、超过900秒拒绝、GPU可见时在Torch导入前拒绝。[验证回执](../reports/wc_s1_build_preparation_validation_20261001.json)是CPU门检查，非编译证据。准备同步后才部署/唯一启动新CPU身份；无新GPU预算。

下一步：实际完整tree部署/逐hash验收、同范围Linux CPU控制检查、提交有界upstream构建并跟随同PID/receipt到终态。若失败先根据实际编译日志处理，不丢弃失败、不重跑旧identity或声称部分目标是完整构建。no-PV wrapper与dense/full-QK/sparse-QK控制继续依据[S0审计](56_WC_S0_SOURCE_SHAPE_AND_KERNEL_AUDIT.md)准备；GPU profile/运行仍另有范围门。

## 实际构建与终态

准备source `8047b15c7577b0f35323f8a31a7c60530d94b4fb`已同步后唯一部署并逐文件hash核对，服务器同3CPU构建门通过。[部署](../reports/wc_s1_source_deployment_20261001.json)。build-r1实际PID2538227/entry2538229已运行到exit0，CPU648.948283秒，输出两个完整上游扩展，而非删目标后的部分构建：[launch](../reports/wc_s1_build_r1_launch_20261001.json)、[终态](../reports/wc_s1_build_r1_terminal_20261001.json)。

- `_qattn`：26,576,128字节，SHA256 `601ad33950cd9d6033720fdb338c15eca84768da18efad00452357366c05f14f`。
- `_fused`：13,687,936字节，SHA256 `ad0ab3a6718c453d9c3185be386800a681fafbd86bfc532b3543c46bbaad1669`。

R2独立fresh审计确认原80文件未变、两binary完整SHA与sm86 CUDA images通过；build/entry/wrapper CPU PID均退出、CPU构建锁释放、runtime及GPU账本未变。六个Python源码原字节复制到独立build/lib，与两binary组成8文件package；未安装到Cosmos或import扩展。[完整审计](../reports/wc_s1_build_r1_fresh_audit_20261001.json)。R1审计误用了SSH system Python3.8，于Torch package metadata步骤失败，发生在package assembly之前；改用明确Cosmos Python3.10的新R2审计，不重编译。[失败记录](../reports/wc_s1_build_audit_r1_technical_failure_20261001.json)。

编译guard记录CUDA未初始化。日志保留CUDA12.2/Torch12.8 minor mismatch、Sage2++未开启、g++版本范围未定义及fused FP8 MeanScaleKernel的`block_sum_val`警告，不把编译通过说成无警告或动态ABI通过。当前no-PV路径是INT8 QK/FP16 V，并不调用该FP8 V转换；真实kernel finite/数值仍需验收，不凭源码排除所有影响。实际Cosmos Torch C++ ABI=true，不能与L0 Wan Torch2.4.1/ABI=false的独立环境混用binary。

## 无 PV wrapper 的实际 CPU 契约

[实验模块](../src/wcomr/sparge_no_pv.py)已实现显式NHD self-attention输入与boolean `128×64` block mask、inference/finite/非空query-row检查、HND contiguous packing、INT8 QK量化接口、FP16 V、PV-mode0低层binding以及原projection所需的`[B,N,2048]`输出展平。初版严格限制B1/H16/D128/N整除128、真实调用仅sm86；不做silent padding或CP>1适配。deep层路由、context-parallel setter以及actual QKV hook仍待模型接入，不能因该函数存在称WS方法实现完成。

本地[3个契约测试](../tests/test_wc_sparge_no_pv.py)通过；实际Cosmos Torch2.7.1+cu128下相同3项也通过，CUDA始终未初始化，没有import Sparge扩展或执行Triton/kernel。[服务器回执](../reports/wc_s1_no_pv_wrapper_cpu_20261001.json)。positive使用CPU spy binding核对布局/12参数/no threshold，不证明实际CUDA结果。input/output finite和mask row检查带来的同步、packing/quant/LUT/展平，全部保留在首轮净时间中。

当前无在途CPU/GPU作业；GPU账本仍3.6512467238638138/4GPUh、余1255.511794秒。本轮没有新增GPU消耗或人评。旧source获取/deploy/build launch不得重跑；只复用已验收的staging artifacts。

下一步：对8文件package做guarded动态导入/ABI与no-PV binding验收，准备有界GPU数值/计时runner。S0实际QKV与WC成本profile仍未测；在现有余额内事前固定具体scope/cap，或如确需额外预算再提出重要决定，不能自动批准原新4GPUh/全部clean50。有限微基准不是端到端加速或质量收益；S1净收益门之后才四臂/模块替换。
