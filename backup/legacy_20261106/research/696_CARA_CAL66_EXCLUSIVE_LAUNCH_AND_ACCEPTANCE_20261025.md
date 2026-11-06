# CAL66完整卡：实际独占启动与验收安排

2026-10-25用户明确授权一次完整66路径执行，单卡8GPUh、累计226GPUh与最终`min(257.7712338712067秒,0.8×fresh Native)`不变。四项CPU原件及完整报价独立重放通过后，于**18:19:39.856326 +08:00**单次派发。**GPU2原runner实际上下文独占已接受，当前运行；尚无科学结果。**

## 唯一任务与原件

- [实际启动](../reports/cara_CAL66_GPU_actual_launch_r1_20261025.json)：launch `54eeebc7-00bb-4951-96cf-e2f66a85e344`；run `cara-shared-cal66-ada-r1`。
- [不可变stage](../reports/cara_CAL66_GPU_stage_r1_20261025.json)：`/data20t/gaokuangda/worldcache_workspace/.sync/cara-shared66-full-ada-r1-20261025`，source `323bb2a10a0a255b0c3429b9c88a31b1d4fffade`，registration SHA `7757c54633416790f4e29cdeb2c72a49ab20d6c5a7c0b598da620d90e7c5d4ed`。复用完整接受生产源码，未改旧stage；新控制器源码 `cd43881b597b0dedbf5af3a2c80454893dc3eb0b`。
- [明确授权](../reports/cara_CAL66_explicit_GPU_authorization_20261025.json)、[完整CPU合并接受](../reports/cara_CAL66_complete_CPU_preparation_and_quote_20261025.json)、[派发控制器CPU](../reports/cara_CAL66_dispatch_controller_CPU_20261025.json)。新控制器4项检查覆盖原intent禁止重复、绑定CPU/质量原件/8GPUh报价、错误授权不访问服务器及远端模板。
- [GPU2实际独占与存储准入](../reports/cara_CAL66_GPU2_exclusive_storage_active_20261025.json)：UUID `GPU-ad5c68cd-890e-b4c1-d0b6-4d80c7d51018`，guardian PID1635177/start970864321，supervisor PID1635271/start970864964，runner PID1635470/start970865687/UID1000。唯一runner CUDA上下文、EXCLUSIVE_PROCESS、无MPS。原四句柄/容器正常，初期49样本最大间隔3.330秒；这只是监测前缀，不代表完整终态独占已接受。

## 完整范围、费用与保护

52QUALITY+6计时重复+6WARM+2历史桥接=66；4CAL、15身份/13正式角色、2296pairs/4592CFG/单load；原α和强基线保持。完整报价预计6.47845126GPUh，监督器8GPUh硬上限。正式评分在GPU释放和账本结算后执行：48组LPIPS/4464帧及52视频×3独立质量指标，共156位置；2CPU/8GiB/6小时，无第二评分进程。

[首次资源](../reports/cara_CAL66_fresh_resources_20261025.json)显示GPU0/1/3忙，GPU2空闲；随后[最终preflight](../reports/cara_CAL66_GPU2_preflight_20261025.json)通过。未触碰其他用户任务。新卡预约8GPUh后，used156.1354543951237、reserved24.5（含旧两卡未知责任16.5）、available45.3645456048763，累计226不变。预约不是实际费用，终态按单调时钟结算。

[私有容量恢复原件](../reports/cara_CAL66_private_storage_recovered_20261025.json)：32GiB真实预分配ext4输出卷，挂载本卡输出路径；跨盘`/data1/gaokuangda_cara_control/cal66-r1/control.journal`预分配48MiB。实际准入输出可用31.18GiB，host约1.16TiB；低水位/跨盘账单与监测持续启用。首次空卷格式化discard导致镜像块数不足，StorageGuard拒绝；没有GPU启动。只对同一新空卷补足真实分配，原失败保留，后续provision工具使用nodiscard；未修改20T共享文件系统保留比例。

五个[原始质量权重再次SHA校验](../reports/cara_CAL66_quality_weights_fresh_admission_20261025.json)通过；已接受模型stage、源码和2395文件依赖overlay已在preflight绑定核验。旧CPU准备原件的GPU_authorized=false保留为当时历史状态，不改写为本轮授权。

## 实际启动后的检查

[检查登记](../reports/cara_CAL66_actual_start_acceptance_schedule_20261025.json)：

- `cara-cal66`：10月25日21:35技术半程，最早21:34:01；只核对进程、UUID、独占、磁盘/跨盘日志、路径量和预算，不读取部分科学结果调参。完成后删除。
- `cara-cal66-2`：10月26日05:50完整验收。报价推算GPU采集结束约00:48，CPU含余量规划完成约05:31；原launch的01:03只是GPU收件预测，不是CPU完成保证。半程按实际技术节奏更新已有最终检查；未完复用原任务，不重派。
- GPU采集结束后自动停止原runner、核对释放、精确结算与释放lease，再进行GPU隐藏CPU评分。guardian在原容器结束后安全恢复模式；若外部进程进入则只记录延期，不驱逐他人。

控制器 `scripts/wc_four_card_cara_shared66_gpu_r1.py` 的capture和accept-gpu独立验收完整66、6重复数值、历史桥接、全部原始评分/权重与源码SHA、独占完整监测、费用/账本、磁盘/跨盘日志和原进程/容器/锁释放。历史桥接不相等仅禁止跨批合并，不伪造一致。失败原件与实际费用保留，科学接受与财务恢复分开。已有intent只recover原stage；不得再次prepare/launch。

完整接受后才按CAL66预登记比较与决策合同分析；不自动追加GPU、不根据部分结果改掩码或阈值。

## 启动后技术补充

18:26:11只读日志确认原runner仍在进行Cosmos导入/模型初始化，日志持续推进；无技术退出或OOM，尚未产生正式路径结果。[原技术日志](../reports/cara_CAL66_model_loading_technical_20261025.json)保留只读Matplotlib缓存回退和可选ffmpegcv提示；未改运行环境。预计时间仍按整卡报价，半程以实测节奏修正，不把初始化状态当作完成进度。
