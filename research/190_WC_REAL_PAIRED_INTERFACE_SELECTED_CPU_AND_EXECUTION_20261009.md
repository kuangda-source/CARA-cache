# 真实成对浅层接口：最终CPU验证与完整GPU执行

## 目标与当前发现

本轮检验 H-T58：在同一真实 Cosmos-Predict2.5-2B 状态上，把两个 CFG 分支的浅层观察放到共同决策之前，是否仍能按相同 CC（两分支复用）或 DD（两分支完整刷新）动作，恢复原始 conditional、unconditional 与 FP32 guided 输出及缓存状态。它是后续联合调度的实现对照，不是新的终点质量或速度实验。

前一完整 Common 实验已显示主 S22 的单槽刷新误差为 CC 的 13.728／13.252 倍，负交叉项抵消约 96.29% 的独立加权能量。第二个曝光场景重现这一机制；旧 Human 单槽正例、W1 与稀疏的正负结果保持。RA-CFGCache 已研究相关联合风险机制，因此不能把联合 CFG 或抵消现象单独作为算法创新。

## 完整实验设计

使用曝光 Common seed3 的原登记请求，固定 768×432、93 帧、16fps、guidance 7、35 请求步／36 实际 UniPC-Karras 更新。完成原生 WorldCache 观察 OFF／ON 两条完整父轨迹与两个视频，并在 ON 父轨迹的 S22 状态执行：CC／DD × 观察 OFF／ON × 原接口／成对接口 × 两次严格重复，共 **16 对局部 CFG 调用、32 次诊断 net、48 个真实 FP32 张量、8 组原／成对比较**。保留 1216 状态组件和全部父轨迹条件、求解器输出及视频。

末端 CPU 将重读全部 48 张量，直接比较分支与原 FP32 CFG 表达式、观察开关／顺序／重复、状态与层访问；两视频完整解码 93 帧，并核对原父 72 次 net／36 次 solver 与终点一致性。测量当前受观测与层钩子影响的 wall／显存，不能把它称为干净部署加速或未来节省。

范围不包含 S23、完整反事实后缀、全 36 步候选策略、终点收益或未来成本标签。它回答与旧五起点卡不同的问题，没有缩减或替代旧卡。曝光请求重用不作独立 CONF。

## 源绑定与实际CPU结果

冻结 156 载荷、原生资产与运行源，配置 SHA `2b06315553ae3371a2632cb005ea9d817fc63c1865223f76965c2aba1f53acb2`；GPU 执行源 `9f01274f55bfaa95dfc0a6016ff4fafca5d82e6d`。

生产 CPU 34.056518 秒通过；selected CPU **32.010701 秒**通过，原 PID 3445551／3445552 退出 0 且消失。原资产、完整请求、16 身份／范围拒绝、配置 binding 与原字节独立核对通过，CUDA 0、新 GPU 0、预算 SHA 未变。此前实际 batch 的完整 CPU／Toy 对照见报告 189；Toy 验证不等于 2B 结果。

## 唯一GPU实际执行

整卡 forecast **1.6487813757460874 GPUh**，包含完整三个教师来源、非嵌套局部与父轨迹最大耗时、加载、900 秒未测开销余量及整体 1.5 倍。它不是实费或严格上界。按既有累计 50 GPUh／完整单次 ≤2 GPUh 权限执行，没有新扩大权限。

现场 UUID `GPU-cebf7119-cf03-23b9-e192-cd196332b704`、A6000／sm8.6、24MiB／无 compute apps、共享锁、余额、磁盘均核对后，唯一启动 `wc-w3-real-paired-interface-r1`。原 GPU supervisor **3445779**、child **3445791**，绑定后 CPU **3445780** 均实际活；最初处于导入阶段，不能从 PID 或审批推定采样成功。独立新目录 `/home/gaokuangda/data/gkd/worldcache_omr/.sync/wc-real-paired-interface-selected-cpu-r1-20261009` 与新输出绑定，旧结果目录不改。

启动前实费 **29.027073214694138／50 GPUh**，64 历史 GPU 提交；本轮第 65 次在途。账本 `used_gpu_hours=50` 是剩余预算的原任务预留，**不是已经花费 50 GPUh**。终态按包含导入、加载、失败与写出的完整 wall 结算；原 2 GPUh 单次及累计限制保持。

## 下一步

只跟踪原句柄和冻结载荷，不复投或改运行源码。原 GPU 正常结束并释放后，绑定后 CPU 审计完整 16 对／48 张量／两视频；若失败，保留整个范围、失败位置和原件，再判断实现问题，不把子集称为成功。

若真实接口等价，继续登记正确的终点收益与未来成本对照，比较原生 WC、简单共同刷新与校准后的 RA 联合基线；不由接口成功直接升级为算法成功，不训练／扩大稀疏／引入人评。重大方向与超 2 GPUh 整卡仍共同讨论。

证据：`reports/wc_real_paired_interface_selected_cpu_r1_terminal_20261009_capture.json`、`reports/wc_real_paired_interface_r1_GPU_launch_20261009.json`、`reports/wc_real_paired_interface_r1_initial_live_20261009.json`。goal active，本轮真实完整 selected CPU、唯一 GPU 派发与跟踪是实际进展，暂无重要阻碍。

## 后续只读采样现场与飞书

最新只读现场 `reports/wc_real_paired_interface_r1_sampling_live_20261009.json` 确认原三个 PID 活、156 冻结载荷未变；真实模型加载 103.754713 秒、prompt guardrail 通过，日志首 OFF 父采样 **13／36**。该批 receipt 只在父起止／局部 pair 写出时保存，父起点快照 `parent_net_calls=0` 不是现场零计算；以原日志和句柄核对进度，不把未更新 checkpoint 判为停止。显存约 10,010MiB，目标唯一 compute PID 为原 child。完整两父／16 pair／48 张量／两全93与后CPU仍待，不评分子集。

组会飞书已用 CLI 更新并全回读 **revision20**：[组会报告](https://lcnssrlun9lz.feishu.cn/docx/HTSIdK0uLofCG5xUI1IcTKaCnAh)。21 节／20 表／4 公式／48 链接；旧其他149块逐块保留，新4块文字、链接与表格核对相同，两次写入成功且无 warnings。完整验证与原读写回执见 `reports/wc_group_meeting_feishu_paired_interface_verification_20261009.json` 与 `research/sources/worldcache_group_meeting_20261009/paired-interface-*`。

新增 `scripts/capture_wc_real_paired_interface_terminal.py` 为未加入冻结156载荷的本地只读终态捕获器：只读原句柄、全量原件／配置／预算，终态做独立JSON范围、状态／观察／artifact／视频和费用重建；不会再次派发GPU／CPU，也不会改服务器或加载第二份张量。AST与当前live返回路径已检查；其终态验证尚待原任务完整结束，不能报已经通过。
