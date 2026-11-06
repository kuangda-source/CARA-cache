# N10半程发现原CPU已终态，两项错误待完整原件定位

2026-10-18。[原五模型CPU半程](../reports/wc_paper_N10_full_five_model_CPU_R1_midpoint_20261018_0159.json)于01:59:35一次查收，[独立技术接受](../reports/wc_paper_N10_full_five_model_CPU_R1_midpoint_independent_20261018.json)核对source／注册／worker源码与完整五分母。原PID1679058已消失；五个角色文件均存在，bundle记录全部五项已尝试。

技术状态中DINO／AMT_S／RAFT_THINGS记录exit0，ViCLIP／MUSIQ_SPAQ记录exit1及ValueError，bundle为 `N10_CPU_MODEL_FAILURES_RETAINED_ALL_FIVE_DENOMINATOR`。半程未读取模型输出／全角色证明及完整traceback，不能据此独立接受前三项或确定后两项原因。

原**02:07完整原件查收**保持，最早02:06:49.761960；只收原句柄和完整五角色原件，再离线独立接受并定位修复。`worldcache-n10-cpu`半程自动化已删除，`worldcache-n10-cpu-2`最终查收保留。不提前执行最终collector，不重派原CPU、不换四模型或三模型子集；当前新质量分数仍0。

同时为后续N09进行[一次资源只读核对](../reports/wc_N09_next_card_fresh_GPU_readonly_20261018_0200.json)：原其他账号PID1615193／1615194仍占用GPU0约48,063MiB、GPU1约47,696MiB，无本项目在途预留或GPU子进程。0利用率不代表显存可用；不重放原失败fence或停止其他账号作业。CPU源准备继续，不把资源等待当方法失败。

完整88连续修正CPU链已准备（[571](571_WC_CORRECTION_WINDOW88_IMMUTABLE_CPU_CHAIN_READY_NOT_EXECUTED_20261018.md)），当前未派发；按已登记的资源等待顺序，在N10原终态完整查收后、无N09实际GPU测量时推进。真实生产和整卡报价仍待，新A3质量和时间为空。N12原18结果保持。

本次0新GPU／模型观察器加载／账本写；累计cap226、最近实结110.869061155及所有历史保留，strict<12整卡自主规则保持。F/B关闭，无训练、人评或OMR。
