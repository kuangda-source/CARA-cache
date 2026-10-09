# P0 部分MLP投影核心实现（2026-10-10）

[部分MLP核心](../src/wcomr/partial_mlp.py)已按[原B2设计](../plans/WORLD_CACHE_MULTI_FIDELITY_FIRST_WINDOW_20261009.md)实现。只拦截所选层的MLP.forward，保留原Block全部attention、当前LayerNorm／scale／shift及投影后的当前gate；P在两次真正Linear前gather活跃token，inactive读取本CFG自己的投影后、gate前缓存。没有全GEMM后遮罩来伪装节省，没有把partial来源当WorldCache D锚点或RA零风险来源。

每层两分支各自缓存未gate的projection、逐token更新时间／D或P来源、最后实际D及context／parameter版本；两CFG共用选择向量。空活跃集合不执行Linear，全活跃或D保持原MLP形状直接执行。冷缓存／context／shape／dtype／device／参数不兼容时完整MLP回退，P回退仍标P来源、不观察新的D。score-only教师显式只读，不写缓存；pair只有两个分支及所有所选层完成才提交，第二分支失败恢复原缓存引用并poison，保留已支付失败操作记录。

首版选择为0.5／0.75配额的轮换与独立本地generator随机块，按实际latent token数而非93帧划分；tail块统一不进入第一配额使随机／轮换实际token预算相同，真实31104 tokens可整除128。记录实际density，选择／CPU索引验证／GPU传输、gather／scatter、projection clone和逐tokenmetadata及attention全部属于成本，不宣称当前净加速。四层／八层缓存约0.949／1.898GiB仅是BF16 projection条件估计，新增元数据和事务old/new／clone也须实测。

[CPU登记](../manifests/wc_p0_projection_core_cpu_r1_preregistration_20261010.json)直接编译实际固定minimal_v4原Block与GPT2FeedForward完整类体，Toy CPU权重／attention／输入明确声明。使用独立完整dense Block与当前gate补偿作参考；两Linear输入hook验证真执行16／8／12／0／16／16行，不能只靠输出接近放行full GEMM blend。六正常双CFG四层pair，加两冷／不兼容P的完整回退pair；D／全活跃逐值相同、partial输出参考、source-age／本分支缓存、当前gate、完整attention、global RNG／参数、四拒绝与第二分支失败回滚／poison均登记。

本地AST／compile通过，实际服务器CPU尚待；不是Cosmos完整模型、真实attention、视频收益或GPU性能。GPU新增0，没有改动在跑的guided-W1冻结237载荷。下一完整CPU成功后，冻结实际层集合并准备已有四CAL×两阶段范围的真实正确性调试与必要干净整组计时，再尽早接BASE-R＋P0／A＋P0与来源感知组合；不重开每层搜索、不要求单模块先稳定获胜，不增加非必要人工评审。

原guided-W1四CAL作业3887240／3887253与后CPU3887241仍现场活，正在第一AV28父采样，尚无完整结果。71提交、启动前结算32.674095026904／77.89524658965853，48窗口余45.22115156275453GPUh；服务器余量预留不是实费。本次CPU不获取GPU锁、不写账本。完整单次≤4自主、>4具体确认，goal active。原W1正负／稀疏局限／RA两工作点与其保真负帧保持。
