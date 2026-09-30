# W1-S1 最近真实full-pair修订：仍无总体收益，发现跨进程视频复现差异

2026-09-30；源码99f554f；同AV工程场景/seed0/4calls15、16、37、38。只把scalar统计decay从0.9改为0；shrink预测不变。状态 **NO_GAIN_IN_SCOPE**，不推进当前两种公式的闭环，不据单场景四点否定整个缓存方向。

## 数值结果

| 配置 | velocity sum-MSE / official | postwarp residual sum-MSE / official | velocity改善点数 |
|---|---:|---:|---:|
| scalar默认decay0.9 | 2.531190 | 1.258734 | 2/4 |
| scalar最近pair decay0 | 2.354246 | 1.258812 | 2/4 |
| shrink固定控制 | 5.394980 | 2.316817 | 2/4 |

最近pair的velocity总MSE较默认约下降6.99%，但仍为官方2.35倍，残差总MSE基本不变；不能作为方法入围信号。beta确实改变（约0.307、0.079、−0.446、−1.832），当前真值未参与估计。新旧72个官方模型输出、缓存、full/skip、trace及采样完全一致；四点官方和shrink的所有数值评分逐值一致。因而同状态数值对比可信，单纯历史系数滞后不足以解释/解决初始无收益现象。

两次实机任务各自的off/on8项checks均通过，包含各自的视频SHA一致。最新supervisor/timeout/runner均退出，GPU释放，锁可获取，服务器产物重哈希匹配。

## 必须保留的复现问题

跨新进程的官方模型输出72/72哈希一致、缓存一致，但两个官方MP4的哈希不同；CPU PyAV完整解码证明93/93帧RGB哈希不同，尺寸均768×432、时间戳相同。8bit RGB MSE=31.026577，平均绝对差3.604356，最大绝对差94，约83.0%通道值不同。不是仅容器元数据差异；目前无法归因于sampler最终latent、VAE解码、安全处理、量化转换或编码中的哪一阶段。没有保存这些阶段的哈希，不补造原因。

该问题没有破坏每次任务内部的诊断无扰动验收，也未改变已核实的同状态数值控制；但它阻止跨进程视频复现一致性和后续质量/干净测速的归因。比较工具返回MATCHED_DENOISER_ONLY_RECENT_PAIR_CONTRAST，显式保留POST_MODEL_VIDEO_MISMATCH_UNRESOLVED。不宣称跨任务的视频相同或质量等价，不据候选数字归因解码后的视频变化。

## 成本与下一步

最近pair任务记账530.753305s /0.147431474GPUh；累计1.560151151/4GPUh，剩余2.439848849GPUh。采样显存峰值26734MiB。所有失败/加载/诊断都已计账，无在途任务。

停止无依据的第二次标量调参。最优先为[跨进程阶段哈希诊断准备卡](16_POST_MODEL_REPRODUCTION_GATE.md)：在相同官方输入/配置/seed的两个新进程中，记录最终sample latent、VAE raw视频、安全管线输入/输出、保存输入、编码文件与完整解码RGB，定位首个差异阶段；不关闭安全组件、不修改共享驱动、不要求人评。质量阶段等待此复现问题被解释或排除。数值方向后续按诊断决定F2或W1-D分组，不自动进入W2复杂方法。

额外非GPU数据清点：固定上游1,044个text-only提示词、7类别，无规范化后的完全重复prompt；JSON没有源视频/场景字段。CAL/DEV/CONF未冻结，必须先连接来源并做近模板分组，不能用唯一ID代替独立性。

证据：[最近pair原始记录](../reports/w1_s1_recent_r1.json)、[监督器终态](../reports/w1_s1_recent_r1_supervisor.json)、[数值摘要](../reports/w1_s1_recent_r1_summary.json)、[受限数值对比](../reports/w1_s1_recent_r1_contrast.json)、[完整解码核查](../reports/w1_s1_recent_r1_cross_decode.json)、[执行及产物审计](../reports/w1_s1_recent_r1_execution_audit.json)、[数据清点](../reports/dataset_inventory_20260930.json)、[账本](../reports/budget.json)。
