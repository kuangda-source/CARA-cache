# S 实际 CLI 与完整矩阵的本地 CPU 组合

[本轮回执](../../../reports/cara_sq_s_cli_composition_local_r5_20261030.json)记录了在 Darwin arm64 上分别使用 two_card、four_card 配置的检查。每种配置执行两个 flow、每个 flow 完整十角色；合计40条小张量路径。它不是两台 Linux 服务器的验收。

实际执行链为 `run_cara_sq_s_r2.run → sq_s_model_entry_r1.execute → run_matrix → check_result → 原文件重读审计`。每个矩阵只调用一次加载替身并清理一次，原 CLI 的第二次调用在加载前被拒绝。四个矩阵合计3744次 head、2208次 deep block、432项资源检查；每个矩阵保留108行、8个 raw、24个独立 anchor，并通过完整 OFF/ON 控制。

每个矩阵审计140个行/张量文件的字节和 SHA；其中8个 raw 各重读4个 anchor 引用，形成40次张量读取、32个独立张量文件。四个矩阵合计160次读取、128个独立张量文件。早期开发检查把文件审计数与张量读取数混在一起，失败回执已保留，最终统计按原审计器的读取语义核对。

CPU 适配集中在检查器中：授权/锁/上下文、存储监控、checkpoint 元数据、环境/注册、权重加载、微型权重及注意力/条件/尺寸/解码/写出、CUDA遥测，以及原接口明确提供的 CPU_fixture 边界。WC/RF 使用原 SHA 的函数 AST 和显式 CPU 全局绑定；这里没有验证完整上游模块的原生导入。原请求对象及432×768参数保留，测试在调用原采样器时显式改用8×2×8×8 latent。原生产 CLI 没有新增 CPU 开关。

保留原条件时间步0.1后，CPU两帧时间嵌入为 `[1,2,8]`。新 [CPU资源合同](S_MODEL_ENTRY_CPU_RESOURCE_CONTRACT_R5.json)由旧 CPU 合同另存，仅修改两个时间嵌入形状；其他字段、类型及上限完全相同。旧 CPU 合同与真实 `[1,24,2048]` 合同保持，38个生产关键文件的 SHA 全部未变。

[缓存边界检查](../../../reports/cara_sq_s_config_cache_boundaries_local_r5_20261030.json)另外执行了15个既有加载边界控制和原 Cosmos 参数解析。缓存命中使用59字节的合成元数据，原 HF 只读查找成功；空缓存离线拒绝，socket出站被阻止。该检查不验证真实 checkpoint 字节，也不加载权重。旧 Python3.9 的语法失败及旧下载钩子拦截缓存查找的失败均另存。

本地隔离环境为 Python3.12.14、Torch2.7.1、diffusers0.35.2；完整版本与源码 SHA 在回执中。每个进程设置2个 Torch 线程，本地未验证 Linux 容器 CPU/RAM 限额或真实分配生命周期。

下一步是把这一组合接入完整 Linux CPU 入口，核对真实缓存解析、完整上游导入及原 guardian/worker/lease/清理链，再形成双端 CPU 证据和整卡报价。S 资源优先保持；本轮计算服务器查询、GPU提交、中央账本写入和新自动检查均为0。S 真实标签和视频仍为0。
