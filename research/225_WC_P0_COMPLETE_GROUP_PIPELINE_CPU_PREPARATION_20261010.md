# P0 完整管线与整组候选 CPU 准备（2026-10-10）

本轮把已通过的真实 gather 核心接入原完整采样，而不是再扩大 attention 层搜索。父路径只执行原 D6 共同完整刷新／缓存；P0 诊断臂从同一已付浅层 probe 出发，执行全部深层 Block、当前 head 和原 RF 条件处理。零基层4、10、16、22缓存各CFG未gate投影，保留每层完整attention、当前调制与gate。共同128块的0.5／0.75配额分别与同配额随机选择对照，完整dense原参考／dense+P0保留。

[采集](../src/wcomr/partial_mlp_collection.py)在step12／30保存同原点的六模式和原输出，全部112 post-RF分支输出。actual D7／25是唯一实际P0来源，教师和试算P不写WC锚点。外部WC／net／solver／RNG／buffer与额外投影值／来源／年龄／context／记录分别实际恢复；当前条件与参数保持。复制字节按合并清单、双副本和显式workspace，在分配前核验；这不是总峰值保证。必要Linear行数hook只用于一次warmup，三次完整整组wall按轮换／逆序计时，包含掩码选择、CPU→GPU index、cache读写、gather／scatter、全部attention与head／RF。恢复与哈希在计时区间外，但真实GPU研究wall全部付费。该整组成本不是完整视频速度。

[管线](../src/wcomr/partial_mlp_sampling.py)仅替换原完整A batch四个显式collector／compiler／validator绑定、112输出数、collector运行上下文与退出清理；逆AST必须恢复原完整 sampler与guarded返回。卸载时恢复类原forward属性形态，避免临时bound method残留；此前core／state CPU原件仍保持，但不能代替本轮新字节验证。

[独立CPU登记](../manifests/wc_p0_group_sampling_cpu_r1_preregistration_20261010.json)包含209冻结载荷、实际原Block／GPT2全文与WC／RF／UniPC／condition／完整入口。明确ToyCPU权重／attention／prepare／decode／writer，512hidden tokens让两Linear实际执行512／256／384行。flow OFF/ON各完整四场景、采集OFF/ON，另最后父写出故障：共24执行父路径、864 solver／1728正常net；成功两批重读576guided、16latent、224诊断分支。全四场景／两个起点、两dense控制、十登记变异、两实际截断、最后写出恢复均保留。当前只有本地AST通过，实际服务器CPU尚待；未选新GPU卡、未拿GPU锁／写账本。失败则保留整卡原件，修复后新身份复核完整范围。

上一真实guided-W1全部验收见[224](224_WC_GUIDED_W1_REAL_CAL_RESULTS_AND_PHASE_REVISION_20261010.md)：全局W1 guided MSE改善27.76%、β=1改善29.65%，后期半强度更好；新阶段候选只在下一轮登记，原全局与全部负结果保持。下一P0 CPU通过后冻结真实四CAL×两起点／八父／八视频槽／112分支完整成本和生产资产卡，fresh资源准入；随后BASE-R＋A／P0及联合选择完整视频，非必要无人评。

权威终态结算33.19208302866151／77.89524658965853，追加48窗口余44.70316356099702 GPUh，71 GPU提交、无在途。单次完整forecast≤4GPUh自主，>4必须具体确认；不拆卡／缩分母规避，旧6.704055834／16路仍未批。goal保持active。

## R1原失败与完整R2

source6922b12的R1实际CPU35.990978秒退出1，3893885／3893886消失、无GPU／锁／账本写入。原完整scope和第一父失败原件已保存；夹具t_embedder直接expand整数timestep导致原Block的SiLU拒绝Long，在第一个父未完成时停止，并未运行部分成功批。修复仅使声明Toy时间嵌入像实际learned embedder输出浮点，并显式报告被原测试汇总断言覆盖的底层错误。独立R2注册212载荷，原全部场景／控制／24执行父／112输出每成功批不缩。真实CPU尚待，新P0 GPU仍未选。

飞书组会补入真实guided-W1结果、正负与P0下一步，完整回读revision43确认183旧块全保持、六新增块正文与链接相同；文档写入不是新实验。

## R2元数据夹具失败与R3

完整R2 source1cf2915实际CPU27.203472秒退出1，3895298／3895300消失、GPU0。底层原件明确首父的声明ToyVideoSize未接受T／H／W参数；这只在完整Block执行时暴露。改为已在核心CPU使用过的三字段dataclass元数据，声明Toy浮点时间嵌入按1000归一化，避免把整数噪声时间直接冒充learned embedding数值。原Block全文、生产MLP与采集算法保持；完整R3同样24父／全场景／全部故障与输出范围，实际CPU待。原R1／R2退出和全部原件保留，不从失败截取成功子集。
