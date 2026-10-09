# Guided-W1 格点核心与部分 MLP 接入映射（2026-10-10）

按现有三模块首窗口推进了两个实际准备项：共享输出系数的选择代码已实现并通过新增 CPU 控制；服务器真实固定源码已读出，部分 MLP 的缓存边界和内存数量级已定位。没有修改正在运行的 RA 对照、拟合真实系数、部署新读出或产生 A/B 视频结果。

## A：先实现已登记的共享格点

[新核心](../src/wcomr/cfg_guided_w1_grid.py)选择首版已登记的 α∈{0,0.5,1}，两 CFG 分支使用同一个 α，不同时新增连续拟合、分支参数或正则强度。令旧读出的 guided 误差为 e₀=8(v_c⁰−v_cᶠ)−7(v_u⁰−v_uᶠ)，更新为 q=8(v_c¹−v_c⁰)−7(v_u¹−v_u⁰)，每个合法同状态样本的目标为 mean(e₀²)+2α mean(e₀q)+α² mean(q²)。先汇总直接合成的 guided 向量，再取矩；先场景内平均、再场景等权平均。重复状态拒绝；无数据／无有效更新和格点平局保留更小 α。

[CPU 登记](../manifests/wc_mf_a_guided_grid_cpu_r1_preregistration_20261010.json)在执行前固定这版选择与控制。[实际控制结果](../reports/wc_mf_a_guided_grid_cpu_controls_20261010.json)包含：两分支误差各自改善但 guided 误差恶化时选择 α=0；另一个耦合例子选择 α=0.5；同一场景四状态不改变两个场景的等权地位；缺失／零更新回退；四种无效矩或重复拒绝。它们是标量 CPU 控制，不是真实 CAL 信号或视频收益。代码没有接收可证明 teacher 来源的原件，因此输出明确标记同状态 teacher 来源尚未证明。

实际接入仍要保留原近似、β=1、原 W1、共享 α 四个对照。现在的 PaidProbe 只有 drift 标量，不能从中重建浅层向量；须增加独立、固定源码下的真实 probe／过去 D-anchor／读出接线。当前 dense teacher 只用于离线合法状态监督，不刷新部署 anchor。α=0 不应免费计算第二 head；α=0.5 的双 head／warp 和读写费用都要计入。真实四 CAL 场景×两个合法状态的完整采集卡将在接线完成后另行绑定范围、源码和完整费用，不把当前六方法两参考替换成 A 卡。

## B：实际源码确定了可替换边界

[服务器只读 AST 映射](../reports/wc_mf_ab_actual_source_map_20261010.json)记录三个原文件的实际 SHA、方法边界与关键调用；没有导入 Torch、运行模型或写 GPU stage。MinimalV1LVGDiT 继承 MinimalV4 的 MiniTrainDIT。当前 Block 中 MLP 的顺序是：当前 LayerNorm 与 timestep scale/shift → GPT2FeedForward 的 Linear/GELU/Linear → **当前 gate 乘投影结果** → residual 相加。

因此 P0 应在 `self.mlp(normalized_x)` 处执行：gather 活跃 token 后真正运行两次 Linear，scatter 投影结果，非活跃位置读本分支的投影后、gate 前缓存，再由原 Block 施加当前 gate。缓存已经乘过旧 gate 的结果会混入过去 modulation；完整 GEMM 后再 mask 也不是部分计算。这一版保留全 token attention、两 CFG 自身内容和共用位置集合，D 更新可靠全层来源，P/S 保存近似来源与非活跃位置年龄；来源变化纳入恢复和计费。

旧 meta 构造记录与当前两个网络文件 SHA 相同：28层、宽度2048、spatial patch2／temporal patch1。用当前 latent24×54×96推算 hidden24×27×48，即31104 tokens；这是按已保存构造参数的条件估计，尚未重新构造或实测峰值。BF16 的一个完整 MLP 投影缓存约121.5MiB，四层×两分支约0.949GiB，八层约1.898GiB；实际若为 FP32 则翻倍，额外 clone、gather/scatter、mask、attention workspace另计。先4–8层、比例0.5／0.75的既定容量与实测设计保持，具体层集在运行前确定。attention敏感层6／23／27的旧证据不能扩成 MLP 禁用名单。

FinalLayer 自带 LayerNorm、当前调制和 Linear；warp/head 不能假设对 hidden 系数线性。因此 A 首版仍按已经登记的速度输出融合，而不是把 hidden 融合冒充同一种共享 α。

## 接续与边界

原 RA 八路径仍优先完成、全量审计和统一全93评分；Native 已有一个接受参考，另一个在原句柄生成。下一将本核心接到四场景合法状态的真实输出，再开发 P0 与协调 sparse，尽早按既定 A/B/AB/ABC 方法完成视频；不要求 A/B 先分别稳定胜出。当前不是新策略已有效、真实 sparse/partial MLP 已运行或已开始训练。原 W1 正负、稀疏条件、首窗口与当前 48 GPUh账目保留；单次完整≤4GPUh自主、>4具体确认，无额外人工评审。
