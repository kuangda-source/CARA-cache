# W3 小卡直接批准、累计24 GPUh与真实执行（2026-10-05）

用户直接批准：`批准 WC-W3-SMALL-CD-R1-20261004-A，把累计 gpuh 限制提升到 24`。

## 当前阶段

累计24h迁移已在真实服务器的全局 f1 锁下完成；实际CPU7步骤、原32控制与增量16控制及102文件原件哈希通过（58.023秒，CUDA未初始化、账本不变）。唯一GPU卡正在执行，首场景step22快照与OFF1完整后缀/视频已产生，重复及C/D控制仍在运行。此处尚无新C/D收益结论。

## 预算与来源

- 上限13→24 GPUh；已用11.022315686839217h、45jobs不重置，无inflight。余额12.977684313160783h。
- 单次总上限3900秒、child3870秒、kill grace5秒不变。预付一次3900秒，结束按含加载、失败、写盘和释放的实际wall结算。
- [直接授权](../manifests/budget_authorization_20261005_wc_24gpuh.json)与[迁移回执](../reports/wc_w3_small_cd_budget24_migration_20261005.json)。
- [批准配置](../configs/wc_w3_small_cd_approved_r1_20261005.json)与[83文件部署清单](../manifests/wc_w3_small_cd_approved_r1_20261005.json)。原V1/V2、67文件核心、历史CPU阶段和原full RV0保持其原身份。原scope里的13h设计字段是历史，新增 execution_budget_authority 明确绑定24h与本卡，不能用历史草案支出24h。
- 唯一生产逻辑变化是 rv0_small_execution 的预算权威校验；科学核心、运行/监督/审计/读取/评分代码不变。原80文件实际CPU回执原件及所有非预算代码SHA仍绑定；新增预算适配拒绝旧权限、重置、费用超限、并发账本修改、扩大单卡与缩减科学分母。

## 固定科学分母与边界

两个曝光CAL场景 common_sense 与 human_199，seed0；step22状态、target calls45/46分别CFG槽0/1；每场景OFF1/OFF2/C_first/D_second/D_first/C_second。共2父、12完整后缀、8新视频，后缀运行14更新/28CFG至终点。规格768×432/93帧/16fps。

必须验证本次官方WC与历史WC编码桥，再复用两个历史Native35。GPU释放后CPU评价4个完整93帧Native-relative LPIPS，形成2个有符号 C−D 诊断。未来继续原自适应策略，因此两臂费用可能不同；负值、失败与分母保留，不称同预算位置调度、正式RV训练标签或物理质量通过。原8父/24后缀/18输出full RV0不在本卡范围；不开始Head、LoRA、专家训练或扩大稀疏搜索。

## 执行后回填

服务器CPU、唯一启动与首个OFF原件观察已回填；待原句柄终态后完成费用/来源/输出完整审计及全帧评分。后续位置交换卡由本次实际技术/成本和科学结果决定，累计预算增加不改变单卡范围。

## 原始启动句柄

冻结GPU source `c12a3cad2cefd3559d60a5256d74d802eb151bab`；supervisor2856696 / timeout2856713 / runner2856714。fresh selected UUID为 GPU-cebf7119-cf03-23b9-e192-cd196332b704，准入24MiB/noapps。输出目录 `/home/gaokuangda/data/gkd/worldcache_omr/outputs/wc-w3-small-cd-r1`。

[actual CPU](../reports/wc_w3_small_cd_budget24_actual_cpu_20261005.json) · [独立原件审计](../reports/wc_w3_small_cd_budget24_actual_cpu_audit_20261005.json) · [唯一启动](../reports/wc_w3_small_cd_launch_20261005.json) · [启动现场](../reports/wc_w3_small_cd_start_observation_20261005.json)。预算在途12.105649020172551/24h、46jobs，是3900秒预付；终态按实际全wall替换预付，尚非最终实费。

## 真实GPU检查点观察（进行中）

首个OFF1现已完成，下面保留此前快照观察的历史身份；最新结果见文末。

[原始检查点观察](../reports/wc_w3_small_cd_live_snapshot_20261005.json)：原runner2856714确认存活，首场景母轨迹到step22（44CFG），slot0/target45；真实Video2WorldCondition两槽位状态已捕获，首个OFF1完整后缀开始。逻辑张量复制2,828,989,246bytes，独占GPU快照存储2,319,184,538bytes；capture所需余量9,952,945,492bytes、当时GPU可用40,412,774,400bytes。该存储只含快照，不是总峰值显存；余量门通过不代表完整恢复控制或C/D终点已通过。当前无C/D评分，不据live改原任务或重提。

## 首个真实OFF后缀与实际成本（尚未整卡验收）

[首个OFF原件观察](../reports/wc_w3_small_cd_first_off_observation_20261005.json)：common_sense/slot0 的OFF1完成14更新/28CFG，完整调用按两槽位为8/7，parent_restored记录true；control wall318.15352621208876秒，解码/安全检查/编码38.81982713006437秒。531,916bytes视频原件重新读取SHA与冻结历史WC完全一致。

这是一个真实后缀/视频来源匹配观察；尚未完成OFF2、C/C、D/D与原母轨迹比较，不能代替整个parent历史桥或两场景因果验收。首次真实control成本明显高于名义单后缀代理，接近349.248秒压力代理；完整2父/12后缀/8输出仍可能触发单次3900秒限时。保持原任务与分母，不取消在跑工作、不延长上限、不根据预估重提。终态保存实际费用、完成/未完成矩阵，只有完整对应来源和控制通过的输出才解释评分。
