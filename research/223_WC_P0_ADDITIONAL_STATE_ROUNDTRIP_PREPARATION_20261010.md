# P0 新增状态恢复与真实整组准备（2026-10-10）

[222核心CPU结果](222_WC_P0_PARTIAL_MLP_CORE_IMPLEMENTATION_20261010.md)已证明真实gather路径执行了较少Linear行，同时保留当前gate和双CFG各自缓存。新增[ProjectionRoundtrip](../src/wcomr/partial_mlp_state.py)覆盖这些状态，作为下一轮实际同状态P0候选比较的必要接线；不是重新审查研究方向，也不要求P0单独赢过旧方法才允许组合。

覆盖内容是全部所选层×两CFG的未gate投影、逐token更新时间、D/P来源、context、参数版本与最后实际D、pair最后逻辑步、记录和poison。快照和每次恢复各自复制tensor，后续候选或主动破坏不能修改保存的原点；完整清单缺失或显式新增逻辑复制预算不足时，在分配前拒绝。恢复只在pair结束后执行，安装/参数变化不受该快照覆盖。普通部署失败仍poison；已经明确隔离的score-only故障，可在其完整外部状态恢复后撤回试算的poison和记录。

这里是**新增P0清单**，与既有WC/net、solver、latent、条件、RNG和buffer清单一起使用；不能把它称为完整Cosmos恢复。逻辑复制字节不等于峰值VRAM，old/live/saved/restored副本与attention workspace都需真实资源核算。哈希和恢复取证不纳入部署速度，但全部GPU研究过程计入既有账本。

[新CPU登记](../manifests/wc_p0_projection_state_cpu_r1_preregistration_20261010.json)保留原六正常pair、两完整安全回退和四拒绝等完整核心控制，另加两次真实原Block双CFG四层P试算、一次第二分支故障及四状态拒绝。直接修改所有缓存物理值、年龄、来源、context/D历史、records/逻辑步/poison，再核对每个tensor恢复；从同一原点重做P，要求输出逐值相同。权重/attention/输入仍为明确Toy CPU，不是实机视频或速度结论。旧核心source cf88776及原回执保持；新九载荷source772805a在独立目录实际CPU3.970380秒退出0，[原件及独立全量验收](../reports/wc_p0_projection_state_cpu_r1_terminal_20261010_capture.json)均通过，3891446／3891447现场消失。新增物理清单、主动破坏恢复、同原点重算逐值相同、失败恢复与四拒绝均通过；未修改原A运行源，GPU新增0、未拿锁／写账本。

[下一真实整组前瞻设计](../manifests/wc_p0_real_group_design_r1_20261010.json)已固定零基层4／10／16／22，按深层分散覆盖选择，未用尚不存在的P0误差挑层、未把attention排除层当MLP排除层。共同块128，预期真实31104 token下0.5／0.75实际活跃15488／23296，两CFG与随机／轮换配额严格相同。六模式保留DENSE原参考、DENSE+P0和四partial；真实shape、参数、完整父控制与整卡成本尚须运行源码核实，这份设计不是已选GPU卡。下一接原四CAL×两阶段真实整组：完整dense源、P当前gate正确性、两Linear真行数、两CFG误差交叉项、实际选择/读写/gather/scatter/attention与整组成本/峰值。完整真实卡再冻结精确对照与完整forecast；不静默删掉已登记的场景/控制，不重开104层搜索。随后尽早BASE-R＋P0、A＋P0与来源感知组合完整视频。

原guided-W1四CAL采集在1791585362现场仍跟踪3887240／3887253及后CPU3887241，AV28／Human各两父已完成、misc OFF完成／ON正在推进，AV51尚待。完整八父／八起点／64输出分支审计和共享α待；本卡不消费新的GPU额度。预算启动前结算32.674095027／77.895246590、48窗口余45.221151563；服务器在途预留不是实费。完整单次≤4GPUh自主、>4GPUh具体确认，goal active；没有非必要人评。
