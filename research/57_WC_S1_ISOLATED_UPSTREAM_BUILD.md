# WC-S1：固定完整源码与隔离 CPU 构建

日期：2026-10-01。当前状态：完整源码/CPU构建程序已准备，实际编译尚未提交；不是内核或吞吐验收。

固定 upstream commit `ae5b629ebb41e41f86b3ea2ab5a3283f13ac151a` 的完整80文件已获取，17,306,415源字节、16,597,007压缩字节。每个文件均匹配官方Git blob SHA及本地SHA256，11个S0选定源文件完全一致；无submodule。大图片/源码/压缩包只在ignored staging，Git只保存[完整来源锁](../manifests/wc_s1_sparge_full_source_lock_20261001.json)。

[实际构建资源清单](../reports/wc_s1_build_inventory_20261001.json)确认Cosmos Torch2.7.1+cu128、setuptools79/packaging25/ninja1.13、g++9.4、CUDA12.2均在。默认shell ninja1.10与Python包ninja1.13不同，实际构建PATH优先原venv/bin。预检可用内存约55.5GiB/磁盘约624.7GiB；提交前再次核对，不当作GPU准入。

[获取程序](../scripts/acquire_wc_sparge_source.py)不执行源码；[构建监督](../scripts/build_wc_sparge.py)与[CPU入口](../scripts/wc_sparge_build_entry.py)以独立源码/输出目录构建，复用已有Torch与ABI，只读原环境、不pip install。固定CUDA_HOME12.2、sm86、CUDA_VISIBLE_DEVICES空、MAX_JOBS2、900秒cap；upstream nvcc每任务threads8也保留，不声称总共只有2CPU线程。entry明确禁止GPU枚举和lazy init，只有cpp_extension的availability查询返回false以避开驱动查询。guard是单进程构建适配，不修改upstream或模型运行时。

只运行upstream `setup.py build_ext`，保留其完整目标和自带generated instantiation；build前后对原80文件fresh hash，不把生成的CUDA源当作upstream修改。两扩展artifact SHA和log/PID/终态独立记录；编译成功也不等于安装、导入、ABI动态链接、真实kernel或质量收益。

本地[3个有意义的负控制](../tests/test_wc_sparse_build_controls.py)通过：源文件hash漂移时不产生child、超过900秒拒绝、GPU可见时在Torch导入前拒绝。[验证回执](../reports/wc_s1_build_preparation_validation_20261001.json)是CPU门检查，非编译证据。准备同步后才部署/唯一启动新CPU身份；无新GPU预算。

下一步：实际完整tree部署/逐hash验收、同范围Linux CPU控制检查、提交有界upstream构建并跟随同PID/receipt到终态。若失败先根据实际编译日志处理，不丢弃失败、不重跑旧identity或声称部分目标是完整构建。no-PV wrapper与dense/full-QK/sparse-QK控制继续依据[S0审计](56_WC_S0_SOURCE_SHAPE_AND_KERNEL_AUDIT.md)准备；GPU profile/运行仍另有范围门。
