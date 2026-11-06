# 修复后的预算搜索强基线：新单次14GPUh审阅卡

目的仍是完成两条原FIT输入上的SA+HC搜索，得到一个19D缓存布局，作为S规则和F19的预算搜索强基线。只在两卡服务器的单张A6000运行；共同端点比较另行登记。本次不使用CHECK或最终确认集调参。

原卡已在进入生成前失败，0/112路径，8.335秒/0.002315298GPUh已唯一结算。此次是一个完整的新卡，不续跑或重放原launch。新run为 `cara-budget-calibration-14gpuh-r2-20261031`，launch_id `323ef0d5e8eb4a91a1c8a4ba47c24b18`，固定源 `33fc2263405baaa77f6dbcfdfdfabedb20f066bc`，阶段 `/data20t/gaokuangda/worldcache_workspace/.sync/cara-budget-calibration-GPU-a6000-r3-20261031`。旧源、容器、失败、64GiB卷及控制日志均保留。

完整范围保持112条：10条预热/Native教师/计时与allD控制，加51次双FIT查询的102条。51次包含Uniform19初始查询、30次SA提案和完整一轮20邻居HC。36更新中19D，search seed42、generation seed0；不缓存跳过重复查询，不失败重试，不冻结部分赢家。

工程预测 **13.03253066GPUh，硬限14GPUh**，包含加载、生成、工件、目标计算、生产端最终读回、停止与释放。与S使用相同14GPUh上限，不声称实耗相等。新卡的加载/GPU拷贝/共享盘最慢情况仍含估算余量；失败也按原guardian全段实耗结算。前一卡0.002315298GPUh为单独已结算成本，不抵扣本卡范围或掩盖在报价中。

执行修复已通过 **113项实际Linux CPU控制**：实际exec承接、篡改拒绝、新旧卡预算隔离、派发、监督器、失败结算和完整112路径结果恢复/一次冻结。原完整两种flow数值证据按未变源码复用，1184文件及12项runtime源对应上述发布版本。先前180秒CPU时限失败原件保留，新300秒CPU句柄于约202秒正常完成；该CPU限时调整没有改变GPU硬限。

新卡使用独立64GiB ext4卷及48MiB跨盘日志。真实1MiB落盘读回和清理通过，输出为空、日志全零；原完整93帧RGB IO组件及费用依据复用，未将新卷小探针称作完整RGB性能测量。实际模型/CUDA执行仍需启动后的原设备和独占核验，CPU通过不代表GPU实验成功。

本次请求批准：**这一张新卡的单次14GPUh，以及仅该新卡在原四卡中央账本的预算预约和最终实际费用结算**。四卡仍不运行实验，不迁移账本。cap226、旧16.5GPUh责任保持；最近已验证余额25.71345654GPUh已扣除旧责任，但不代替派发前实时核验。

批准后先核对新旧原句柄、源/runtime/资产、UUID、温度、显存、计算进程、模式/设备锁、40GiB无额外swap及44GiB宿主余量、独立存储和原账本，全部通过才唯一启动。实际起点后约6小时30分半程、13小时15分终验、14小时硬截止；提前结束时前移同一终验。成功失败都唯一结算并释放，只有完整112/51接受后才一次CPU汇总与冻结，不自动进入其他GPU卡。

[机器审阅卡](BUDGET_SUCCESSOR14GPUH_REVIEW_R1_20261031.json) · [完整CPU](../../../../reports/cara_budget_successor_whole_CPU_composed_r1_20261031.json) · [完整报价](../../../../reports/cara_budget_successor_whole_quote_r1_20261031.json) · [实际113项CPU接受](../../../../reports/cara_budget_successor_CPU_accepted_r2_20261031.json) · [新存储接受](../../../../reports/cara_budget_successor_storage_accepted_r1_20261031.json)
