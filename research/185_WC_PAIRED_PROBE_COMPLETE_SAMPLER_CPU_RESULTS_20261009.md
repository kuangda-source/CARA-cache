# 完整36步成对接口CPU通过：同动作缓存、求解器和终点latent一致

2026-10-09。**这轮把成对浅层probe接进了原Video2World条件构造／CFG velocity和完整UniPC采样，并完成24组全程同动作对照。** 48条Toy父采样的逐步输出、缓存、求解器和最终latent一致；已有接口证据不再只停留在单个CFG pair。首次尾部控制不一致失败保留，原Common科学确认继续，新增GPU0。

## 目标、方法与完整设计

[H-T55预登记](../plans/WORLD_CACHE_PAIRED_PROBE_FULL_SAMPLER_CPU_20261009.md)保留实际RF velocity的条件构造和原FP32 `cond + 7*(cond-uncond)`，只将相邻两次denoise赋值替换成一个成对executor调用。逆AST必须完整还原原函数；DataType、NUM_CONDITIONAL_FRAMES_KEY、parallel_state来自实际RF模块，只有成对调用helper为明确的新绑定。WC和denoise仍使用H-T54原实际模块编译器与原绑定检查，上游源不修改。

完整Text2World采样函数体和实际UniPC保持：35请求、36更新、72分支、70的WC周期与最后0／1。按flow OFF／ON × 恒CC／恒DD／交替CC-DD × 显式观察OFF／ON × 两重复，固定相同动作对照原顺序与成对顺序。warmup、68／69尾部DD和reset保护两路径相同，并核对真实4层访问增量；不是原生阈值策略有效性实验。

第22次更新在两条路径均实际破坏并恢复完整状态／条件，从恢复latent继续到第36步。五检查点为13、21、33、35、36。生成网络／attention、CPU噪声与normalize／broadcast、条件类构造均为声明Toy，latent为1×2048×2×8×8，不是实际2B输出。

| 全范围控制 | R2实际结果 |
| --- | --- |
| 原H-T54：8主／2初始化／16失败／2源 | **28行全保留并重新执行通过** |
| 原顺序／成对完整比较 | **24／24**，48条36步／72分支父采样 |
| 成功全程更新／分支调用 | 1,728次solver／3,456次net（旧控制和故障另计） |
| 最终latent | 24组实际`torch.equal`，全通过 |
| 每路径36个velocity及36个solver返回 | 全摘要一致 |
| 五检查点／最终WC、buffers、eval、solver、seed generator和全局RNG | 全一致；Toy每检查点50组件，不能称真实2B的1216组件 |
| 第22步完整roundtrip并继续 | 48条父路径均通过，条件保持类／身份／值 |
| 观察ON的72分支输入与net输出 | 每分支对应一致，中间时序差异保留 |
| 观察OFF／ON与两重复 | 每flow／每schedule均相同 |
| 新完整采样故障 | **8／8**预期拒绝，计划36步／失败位置保留 |

新故障是step23 selector异常、最后solver异常、forward绑定改变、视频条件构造异常，各两flow；分别在22、35、0、0次完成更新后拒绝并弃用副本，不声称任意真实模型完整回滚。共60结果行，不能以部分通过验收。

## 首次失败与修正的价值

R1 source `382a91dd66e69dd35186c0a5e980806fed938a6d`，3435897／3435898退出1，driver **36.894822秒**。首次恒CC的全36步最终latent断言失败，原[失败字节／日志／登记](../reports/wc_cfg_paired_probe_full_sampler_cpu_r1_terminal_20261009_capture_and_independent_audit.json)已保存。

控制臂强制CC原函数只替换阈值，并不会自动跟随成对executor的双分支尾部DD保护。因此R1比较了尾部不同动作。R2只让原顺序控制显式使用相同保护，补上每一步的真实浅深层访问核对（DD各2、CC浅2／深0）；24组范围、重复、两flow、观察、尾部、roundtrip和故障均没有删除。它提醒后续真实模型比较必须核对实际动作，不能只凭计划或日志标签声称同预算。

R2 source `ed15c5e430227a456b8f2513eb420bb4f49656b8`，独立`.sync/wc-cfg-paired-probe-full-sampler-cpu-r2-20261009`，3436864／3436865退出exit0。完整driver **170.060323秒**，fixture **141.947319秒**，68载荷／8runtime源与账本原字节不变；CUDA未初始化、权重／下载／Triton执行禁止，GPU提交0。

[原字节捕获及独立完整核对](../reports/wc_cfg_paired_probe_full_sampler_cpu_r2_terminal_20261009_capture_and_independent_audit.json)验证全部24组合、36步、动作实际层访问、五组件集合、恢复继续、分支观察、跨重复／观察开关以及8新／16旧失败。服务器完成真实Torch比较；本地为完整原件／分组／SHA审计，没有第二次张量加载。

R2原件`limits`继承通用fixture的历史pipeline说明，需要明确更正：**本卡新范围执行到最终latent，没有执行decode／writer／视频；velocity不是完全未改，而是上述两个赋值的已核对变换。** 原字节不改，本地函数仅更正这段说明（不改采样／控制行为），[元数据更正的逆AST核对](../reports/wc_cfg_paired_probe_full_sampler_cpu_r2_limits_metadata_erratum_20261009.json)通过，下一卡须绑定其新SHA；不能把历史默认说明当成完整pipeline验收，也不将该说明改动报成新CPU执行。

## 当前科学任务与下一步

[原Common现场](../reports/wc_other_scene_cfg_confirmation_r1_full_sampler_cpu_r2_progress_corrected_20261009.json)确认GPU3426296／3426308和后CPU3426297真实存活，source c243d30／95载荷不变。OFF已保存完整父视频，ON在S22及自身S23动作对照中：观察时27／40 pair登记完成但全量仍待，不加载在途教师评分或报跨场景科学成功。前两个进度快照读错teacher嵌套／pair状态导致0计数，保留并由这次原句柄、明确嵌套和完整状态值更正，不将旧0解释成实验停滞。

继续原Common全部40对、两父、两93帧视频和后CPU完整审计／费用结算。然后准备真实2B同动作接口／显存／观察开关成本卡，真实GPU范围及完整费用须另登记；CPU耗时不能换算GPU速度。原生WC、简单共同刷新和正确校准RA联合基线，最终动作收益与未来真实成本标签仍待。没有Head／LoRA、新风险策略或论文新方法优势。

实费底数**27.644682758／50GPUh**，第64 Common在途`used50`仅预留，终态全wall结算。整张新GPU预测>2GPUh时在完整CPU和具体可审阅成本准备后确认，不缩拆范围或重新消费旧单次身份；不扩稀疏／OMR／DRE／人评。goal active，本轮实际完整采样CPU与verified wait是进展。飞书revision15保持科学成果，接口CPU不另冒充论文结果追加。
