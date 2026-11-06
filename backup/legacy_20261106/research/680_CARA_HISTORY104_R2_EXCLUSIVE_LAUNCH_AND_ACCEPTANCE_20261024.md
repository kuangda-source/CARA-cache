# 680 — 完整104 R2硬独占启动与验收安排

用户在恢复准备完成后明确授权启动新的完整104卡。原失败R1仍保留，旧72路径不拼接、不评分、不用于调参；旧费用按非精确的保守重建值5.48GPUh结算，新卡独立预约。

## 实际身份与准入

- 实际启动：2026-10-24 13:41:30.911624 +08:00。
- launch：`eee11fe8-c801-4e11-9e53-15b5a6040863`；run：`cara-history-boundary104-cal4-ada-r2`。
- source：`159aaa76ddecc78864b40fa669a32029a3a4a6e4`；stage：`/data20t/gaokuangda/worldcache_workspace/.sync/cara-history104-full-ada-r2-20261024`。
- GPU3：`GPU-d4868f0a-29df-9077-82db-77f7bf0f9934`，从空闲Default经正常sudo改为Exclusive_Process；无MPS，不触碰GPU0其他用户任务。
- guardian：1280430/start960555427；supervisor：1280495/start960555633；唯一CUDA runner：1280552/start960555843/UID1000。
- 已核对真实context-ready/granted、容器、原句柄、UUID项目锁和账本。首次持续独占前缀51样本、49个已授权上下文样本、0违规、最大间隔2.394秒；这不是完整终态独占接受。
- 最新技术观察为MODEL_LOADING、0/104、0失败。未分析任何部分视频或计时。

## 空间和费用保护

启动前20T盘普通用户可用1423425597440字节（约1.29TiB），内存可用约81.58GiB。独立32GiB ext4镜像已实体预分配并挂载到本卡输出目录，初始可用33484972032字节（约31.18GiB）。跨盘`/data1/gaokuangda_cara_control/history104-r2/control.journal`为48MiB预分配双槽日志；启动后实际supervisor/guardian/telemetry记录已落盘。输出低水位4GiB、主卷低水位128MiB、挂载/设备/inode身份检查持续生效。账单在终态生成，不以运行中空billing槽冒充账单。

本卡forecast **11.423207068397064 GPUh**，硬上限 **11.9 GPUh**；累计 **226 GPUh**、部署 **257.7712338712067秒**与既定Native相对约束不变。预约后used140.60066151587193、reserved28.4（包含旧两卡未知责任16.5和本卡11.9）、available56.99933848412807 GPUh。旧失败费用不重复结算。

## 固定范围与检查时间

4CAL、10角色、80正式+20warm+4诊断，共104路径、3744pairs/7488CFG、单load；历史alpha、S24/S25/S26/shared布局、两轮反序交错和诊断范围保持。GPU释放、结算和锁释放后进行72组/6696帧CPU LPIPS（最多1.5h、2CPU）。完整终态前不做科学解释或调参。

所有时间为Asia/Shanghai：

| 检查 | 安排 |
|---|---|
| 技术半程 | 10月24日19:25；实际起点推算最早19:24:12；automation `cara104-r2` |
| GPU阶段预计完成 | 10月25日01:06:54（估算，不是完成证明） |
| GPU预算上限对应时间 | 约10月25日01:35:31，以实际单调钟监督为准 |
| 最终验收 | 10月25日03:10；覆盖释放后最多1.5h CPU评分；automation `cara104-r2-2` |

只创建以上一个半程和一个最终检查。实际提前结束可以提前收件；若评分仍运行，复用原检查，不重派GPU。UNKNOWN仅恢复原stage句柄。失败保留原件、日志和真实费用，不能将财务恢复当作科学接受。完整接受后按673/674分析历史强基线、24/25D预算边界与计时模型，不直接放宽预算或派P2。

## 唯一原件入口

- [实际launch](../reports/cara_history104_recovery_GPU_actual_launch_r2_20261024.json)
- [新明确授权](../reports/cara_history104_recovery_direct_user_GPU_authorization_20261024.json)
- [fresh准入](../reports/cara_history104_recovery_GPU3_preflight_20261024.json)
- [完整恢复CPU接受](../reports/cara_history104_storage_combination_CPU_accepted_r2_20261024.json)
- [真实独占接受](../reports/cara_history104_recovery_GPU3_exclusive_active_r2_20261024.json)
- [实际存储与日志](../reports/cara_history104_recovery_active_storage_journal_20261024.json)
- [连续独占前缀](../reports/cara_history104_recovery_exclusive_monitor_prefix_20261024.json)
- [最新技术收件](../reports/cara_history104_recovery_GPU_model_loading_r2_20261024.json)
- [完整报价](../manifests/cara_history104_recovery_full104_quote_r2_20261024.json)

终态命令：`.venv/bin/python scripts/wc_four_card_cara_history104_gpu_r1.py capture --launch-ref reports/cara_history104_recovery_GPU_actual_launch_r2_20261024.json --mode terminal --output <新唯一回执>`，完整退出后`accept-gpu --capture <终态> --output <新接受>`。原stage和launch不替换、不重新prepare或launch。
