# 666 — 无损去重归档释放空间，接续 PG-P2 组合 CPU

## 归档完成

在UID1000自己的已结束CARA输出内，完成452个完全相同的旧张量去重归档，共释放重复存储 **12,852,656,704 bytes（约11.97GiB）**。原路径仍然存在、SHA与字节保持相同；只读SHA对象与原路径通过硬链接共享内容。**这是同盘去重归档，不是异地备份**，不合并warm/正式角色、独立运行或费用。

- 442个 warm1624 interval/teacher 张量与 formal_0 同输入原件逐字节相同。
- 10个已接受的重复 all36-guided 张量与对应 Native 原件逐字节相同。
- BANK24原始诊断张量仅盘点，未改动；全部视频、最终latent、正式1624区间、Native参照、标签/价格、JSON回执、环境模型缓存均保持。
- 归档前核查账号、已结束容器、无本人进程打开及当前SHA；先建立归档对象，再原子替换重复文件路径。归档后核查452套路径/对象同inode且只读，并实际恢复一个独立副本验证SHA。
- 共享盘可用从33,704,222,720增至46,424,584,192 bytes。其净变化包含共享盘并发写入，不将差额归因给某一任务。

原件清单和恢复入口：

- `reports/cara_exact_duplicate_archive_plan_20261023.json`
- `reports/cara_exact_duplicate_archive_verified_20261023.json`
- `reports/cara_exact_duplicate_archive_committed_20261023.json`
- `reports/cara_archive_restore_and_P1_protection_verified_20261023.json`
- `plans/cara_policy_generator_20261020/COLD_ARCHIVE_RESTORE_R1_20261023.md`

远端归档目录 `/data20t/gaokuangda/worldcache_workspace/.sync/cara-cold-archive-20261023` 保留SHA对象、原元数据、逐文件提交日志及恢复说明引用。不要直接改写只读硬链接；需要编辑时复制为独立inode并校验SHA后使用新目录。

初次只读18GiB哈希超过160秒包装时限，失败回执保留；恢复核查未产生归档控制目录，后续仅延长只读核验时限。原小包FRP传输测试8MiB约3.2秒；既有LAN备用连接在12秒连接超时后未使用。最终未搬运大包、未触碰其他用户文件或进程。

## P1 保护

归档后实际核查：原runner **1148184/start954343237** 和原容器仍运行；P1全部登记payload SHA未改变；registration仍为 `31cc191345c36e31ed6dbad4109c859ffa0594da3ce87590beff46f1e774d4f7`。未修改P1源码/config/输入/输出/费用/GPU模式。没有使用部分质量结果；半程00:52、终态05:32保持。

## 新组合 CPU 原句柄

资源门槛恢复后，单次启动新P2组合CPU：

- launch：`reports/cara_PG_P2_combination_CPU_launch_r2_20261023.json`
- source：`43bb75f5d79d8d73d04217bf3c210bb6baa183d4`
- stage：`/data20t/gaokuangda/worldcache_workspace/.sync/cara-pg-p2-CPU-combination-r2-20261023`
- registration：`5da92668fffb25c4f9ac54fc5c9b8d85deb79e714b0acbabdfb2b09fc5736ca8`
- wrapper PID1166560/start955181257；实际启动 **2026-10-23 22:45:49.218019 Asia/Shanghai**。
- 准入磁盘46,021,423,104 bytes，MemAvailable53,741,879,296 bytes；固定镜像、只读root、GPU设备为空、1CPU/4GiB。没有GPU提交或权威账本写入。

原容器于 **2026-10-23 22:54:33.964578 Asia/Shanghai** 退出0，实际 **22:54:52.291542** 完整收件。复用原终态回执，不重复采集或重派：

- 完整终态：`reports/cara_PG_P2_combination_CPU_check_r2_20261023_05.json`
- 独立接受：`reports/cara_PG_P2_combination_CPU_accepted_r2_20261023.json`
- 接受状态：`PG_P2_COMPLETE_PRODUCTION_COMBINATION_CPU_ACCEPTED_P1_BINDING_AND_BUDGET_PENDING`。
- 48条完整采样CPU路径、72实际请求；真实93帧432×768 CPU LPIPS；六类实际CPU子进程监督/guardian生命周期；32项完整分母、评分失败、原件身份及终态结算组合检查全部通过。组合检查用时520.29秒。
- 采样调用固定生产请求/guardrail/scheduler/WC实现，但使用小CPU权重及声明的toy attention/decoder，没有加载真实Cosmos生成权重。LPIPS加载实际固定权重，输入为合成93帧视频。
- 全518路径/346组评分/1600质量位置及生命周期账本为合成控制。五项独立质量模型未实际加载；本次验收不证明真实模型质量、最终预算或新卡硬件独占。
- `production_CPU_accepted=true`、`full_GPU_lifecycle_CPU_accepted=true`；`final_P1_bindings_accepted=false`、`GPU_dispatch_ready=false`、`GPU_submissions=0`。最终P2 runner/capture/真实质量模型资源须在P1绑定后的实际manifest上核验。

旧R4采样CPU、665本地75/接受器15控制和资源不足失败原件保留。未来P1绑定脚本仍使用R4原入口CPU回执，新组合接受作为附加前提；不把不同接受器的回执直接互换。

## 后续约束

最终P2范围和预算仍等P1完整结果及策略物理去重后确定，本轮不重新报价、不申请或预留GPU预算。组合CPU通过只能说明实现和退出/评分/原件检查通过，不是自动策略、视频质量或速度结果。
