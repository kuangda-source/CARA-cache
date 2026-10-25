# CAL66 R2已绑定执行授权、CPU与磁盘；等待空闲GPU

用户本轮明确“按设计继续独占gpu 推进，估计时间并做好半程检查和全程验收”。这授权一次新的完整R2执行，替代上一轮“先不重跑”的准备状态；不扩大原α、强基线、66路径或预算。原R1失败与0.484958702187 GPUh精确结算继续保留。

**当前已完成R2准备，尚未提交GPU。** 21:20全卡快照显示四卡均有外部进程；21:25完整GPU3准入只剩 `GPU_BUSY`。没有改忙卡模式、驱逐进程或新增GPU预约。

## 唯一执行身份与CPU

| 项目 | 已登记值 |
|---|---|
| run | `cara-shared-cal66-ada-r2` |
| stage | `/data20t/gaokuangda/worldcache_workspace/.sync/cara-shared66-full-ada-r2-20261025` |
| source | `fec1656f99cb3e92bc70d92ea978ea6acb020451` |
| registration SHA | `48193714a15f219b33fd62a6f929ee8e7a5c17b1b6c3dfd9c7615318318c7561` |
| CPU proof SHA | `b3b02a0d195734c02c13eb7b0b780f17050b781daf5ef4049524e0ca2a81ed60` |
| stage-ref | [新stage原件](../reports/cara_CAL66_R2_GPU_stage_20261025.json) |
| 执行授权 | [原指令记录](../reports/cara_CAL66_R2_direct_execution_authorization_20261025.json)、[与stage绑定的授权](../reports/cara_CAL66_R2_bound_execution_authorization_20261025.json) |

新CPU容器于21:15:23.275271开始、21:18:06.930418退出0，程序墙钟160.507秒；1CPU/4GiB、GPU隐藏。复用已接受的真实冻结类60数值路径/66槽位预检，同时重新验证R2运行名、新报价、实际stage/runtime绑定、原监督/guardian的10种真实CPU子进程生命周期、6种存储/真实tmpfs ENOSPC情景及60项终态检查。142个既有执行文件SHA未变；两个身份/报价适配文件经过新CPU验证，不将旧CPU原件直接冒充新身份接受。

[完整CPU终态](../reports/cara_CAL66_R2_identity_CPU_complete_check_20261025.json)、[独立接受](../reports/cara_CAL66_R2_identity_CPU_accepted_20261025.json)。新本地6项身份/报价及反例检查通过，旧冻结入口10项检查保持；新监督CPU不加载完整Cosmos权重，不是视频质量或加速结论。旧历史桥接、释放后评分与真实质量模型资源再次按原SHA独立重放审核，不重跑GPU。

执行控制器仍为 `scripts/wc_four_card_cara_shared66_gpu_r1.py`，脚本名保留兼容，当前合同使用R2。`shared66_card` 保留原科学manifest的完整冻结SHA，只把运行身份与独立恢复报价分离绑定；终态接受器核验新报价，不能将旧R1启动或旧报价当新R2。此前stage均未改。

## 新空卷预留问题及修复

新R2独立32GiB输出卷、48MiB跨盘journal已配置。初次创建通过后，准入发现底层镜像分配量低于32GiB：先为34,210,852,864字节、随后34,175,201,280字节，镜像逻辑长度仍34,359,738,368。StorageGuard正确拒绝，没有放宽预留阈值。

该现象与延迟文件系统初始化经loop设备零化区域的机制相符，但没有追踪块层调用，故不声称已唯一归因。处理限于**新R2空卷**：确认无文件、无GPU意图/启动/授权文件、无账本任务后卸载，以 `lazy_itable_init=0,lazy_journal_init=0,nodiscard` 同步初始化，再完整预分配并重新挂载。没有修改原实验数据；新卷inode/device及已冻结storage合同均未改变。重新分配34,359,746,560字节，随后完整准入存储通过；未来每次准入及运行中仍持续检查。

[初建原件](../reports/cara_CAL66_R2_private_storage_20261025.json)、[首轮拒绝](../reports/cara_CAL66_R2_preflight_GPU3_20261025.json)、[诊断](../reports/cara_CAL66_R2_storage_allocation_diagnostic_20261025.json)、[空卷修复](../reports/cara_CAL66_R2_empty_storage_allocation_repair_20261025.json)、[修复后完整准入](../reports/cara_CAL66_R2_preflight_after_storage_repair_20261025.json)。后者实际21:25:20观察：输出卷可用31.18GiB、host约1.12TiB、MemAvailable约60GiB，质量依赖overlay通过；仅GPU_BUSY未通过。

## 预算、时间与自动接续

范围保持52正式+6重复+6warm+2桥接=66，2296pairs/4592CFG/单load。完整报价6.880951 GPUh，单卡硬上限8，累计226；最终部署上限仍 `min(257.7712338712067秒,.8freshNative)`。当前账本used156.620413、旧两卡责任reserved16.5、available52.879587。新8小时尚未预留。

只有原GPU释放、结算、锁释放后，才进行48组LPIPS/4464帧和52视频×3维度=156位置评分，2CPU/8GiB/上限6小时。

| 相对实际启动 | 规划 |
|---|---|
| +3小时27分 | 一次技术半程，只读状态、不调参 |
| +6小时53分 | 预计采集完成并释放GPU |
| +11小时36分 | 预计含CPU评分具备最终验收条件 |
| +约13小时 | 按评分6小时上限安排的保守检查点，不代表保证完成 |

已创建本聊天自动检查 **`cara-cal66-r2`**，每30分钟检查空闲卡准入。它先恢复同stage句柄，确认没有intent/launch才允许单次派发；已有intent或UNKNOWN只能恢复原句柄。busy保持等待，不反复通知。成功启动并核对真实硬独占后，将本检查改绑同launch作为最终验收，并新增最多一个实际启动时间绑定的半程检查。没有实际启动就不虚构半程/最终日期。

启动命令沿已绑授权使用 `preflight` → `launch-gpu --recovery-authorization reports/cara_CAL66_R2_bound_execution_authorization_20261025.json` → `capture --mode admission`；stage-ref固定为本记录所列。Git验证沿已验 `ssh.github.com:443` 临时 `GIT_SSH_COMMAND`，不改全局配置。prepare/provision已完成，不能再调用。最终收件仍由同控制器 `capture --mode terminal` 和 `accept-gpu` 独立核验；评分未完成不能重派GPU，科学分析只在完整接受后进行。

[原句柄核查](../reports/cara_CAL66_R2_original_handle_check_20261025.json)显示新stage暂无intent/launch/guardian/failure文件。[21:20四卡原件](../reports/cara_CAL66_R2_fresh_GPU_20261025_212030.json)保留；显存占用或进程存在时，即使利用率为0也不是空闲卡。
