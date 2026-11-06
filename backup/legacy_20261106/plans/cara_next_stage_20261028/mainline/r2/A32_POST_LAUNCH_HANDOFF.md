# A32 原运行与验收交接

用户已明确批准单次 A32。2026-10-28 **22:17:40 Asia/Shanghai** 实际启动，32条、硬5 GPUh；不得在任一主机重派，也不自动启动 B36。

**最新：A32完整链已接受并一次冻结，两个检查均已删除。** GPU00:33结束、CPU01:01:26退出0；真实12对评分接受后已生成 `A32_FROZEN_BASELINES.json`。WC_T006/RA_T1保留UNMATCHED，Native22为MATCHED。见 `research/745_CARA_A32_COMPLETE_FIT_SCORES_AND_FROZEN_BASELINES_20261029.md`。以下CPU启动/检查与原GPU身份保留为历史记录，不再派发任何原任务。

验收过程中复用的原回执：

- 原terminal：`reports/cara_fast_A6000_terminal_20261029_0050.json`
- 原中央settlement：`reports/cara_fast_A6000_central_settlement_20261029_0052.json`
- 原release接受：`reports/cara_fast_A6000_release_accepted_20261029_0053.json`
- 原12对manifest：`reports/cara_fast_A6000_score_manifest_20261029_0053.json`
- 原CPU启动：`reports/cara_fast_A6000_CPU_score_launch_20261029_0056.json`
- CPU状态：`reports/cara_fast_A6000_CPU_score_status_20261029_0058.json`（当时仍运行，不含分数）

GPU原32/32、3559观测、最大gap4.715004秒/最高88°C与全部原件哈希通过；实际**2.2557055054700728 GPUh**已中央唯一结算，cap226、旧16.5责任保持。不要重新派发GPU、终态读取器或CPU评分，也不要重新创建一个settlement快照来替换原文件：manifest绑定原release/settlement摘要。

CPU于2026-10-29 **00:55:16** 单次启动，2CPU/8GiB、cores26,27、禁swap、无GPU、原件/source只读，2小时上限。原容器`cara-fast-cal-a32-a6000-r2-20261028-A-score-cpu`，manifest SHA `7937a4895626d1555864bf30b78b3ee33f345e870ed53e84af93f3be2d33c767`。现有`A-score-CPU-intent.json`和`A-score-CPU-launch.json`位于原GPUstage，恢复原CPU句柄，禁止重试。

最终评分原捕获为 `reports/cara_fast_A6000_CPU_scores_terminal_20261029_0107.json`，独立接受为 `reports/cara_fast_A6000_CPU_scores_accepted_20261029_0108.json`，实际冻结为 `plans/cara_next_stage_20261028/mainline/r2/A32_FROZEN_BASELINES.json`，已在真实六原件上核对的B承接为 `A32_TO_B36_BOUND_HANDOFF.json`。冻结文件已存在，只能验证，绝不覆盖。B36仍待独立授权，不重开任何A32读取/评分进程。

- run：`cara-fast-cal-a32-r2-20261028`
- launch：`5a5ab53ebb604433ab83cea06e1ab412`
- 源码：`9eaa5eb30c5509810c99a55002b51d6b71da1ef6`；准入操作器后续仅修正真实路径和实际英语资源复核，`4cfc16ce`，未改GPU运行源。
- 主机：`two_card_lan`，经 `four_card` 现有密钥跳转。
- UUID：`GPU-cebf7119-cf03-23b9-e192-cd196332b704`，A6000 GPU1。
- 项目：`/data20t/gaokuangda/worldcache_workspace`
- 原stage：项目下 `.sync/cara-fast-cal-a32-a6000-r2-20261028`
- 容器：`cara-fast-cal-a32-a6000-r2-20261028-gpu`
- guardian：PID735035 / start_ticks649196172；supervisor：735091 / 649196297；runner：735135 / 649196413、UID1004。
- 注册SHA：`5d6576288a42d1b3bfbcf2b87bd1c06f5b1eafa130d823817f685789593a9a8c`。

实际句柄必须同时核对PID与start ticks，UNKNOWN只恢复原件。中央已唯一预约5 GPUh；cap226、旧16.5未知责任保持。两卡本地账本是旧副本，不授予费用。原输出在独立32GiB SSD loop，跨盘48MiB journal；40GiB/2CPU、无swap容器，主机可用内存门44GiB。EXCLUSIVE_PROCESS和确切原runner上下文已确认；90°C热保护不改。

## 两次检查

按原 supervisor `started_unix=1793197060.4785576`：

| 项目 | 北京时间 | 自动化 |
|---|---|---|
| 半程 | 2026-10-29 00:47 | `a32`，一次 |
| 预计结束 / 最终检查 | 2026-10-29 03:14:52 / 03:15 | `a32-2`，一次 |
| 原硬限 | 2026-10-29 03:17:40 | 原监督器执行，提前180秒进入释放边界 |

半程仅原句柄、完成计数、GPU独占、温度、资源和账本，禁止查看或公布部分科学分数。若终验时仍运行，将同一检查移到硬限后恢复原件，不改变监督器。完成后删除对应一次自动化；若提前失败，保留失败/实际费用，取消多余检查，不重试GPU。

## 可用命令与源

本地仓库：`/Users/kuangda_gao/Documents/世界模型加速实验/worldcache_omr`。既有transport为 `scripts/cara_two_card_transport_r1.py` 的 `ssh/four_ssh`，秘密只走既有0600读取器和stdin，不打印或入Git。不要再调用 dispatch 脚本的 prepare/reserve/launch。

运行检查可用 `scripts/cara_fast_a32_dispatch_r2.py status --output <新的reports路径>`；只允许读取原运行。终态捕获用：

```sh
python3 scripts/capture_cara_fast_terminal_r2.py --launch reports/cara_fast_A6000_GPU_actual_launch_r1_20261028.json --output reports/cara_fast_A6000_terminal_<唯一时间>.json
```

捕获器绑定原source/launch字节，GPU仍活跃时只返回运维信息。真正结束后才启动其一次CPU原件读取，1CPU/1GiB、最长900秒、最多32GiB原件扫描；超时恢复原 `A-terminal-capture-intent.json`、PID/start ticks、结果，不重开读者。所有原进程/容器/锁退出才可结算。当前GPU如被其他用户合法占用，不否认本卡过去已释放；不要干预新用户。

### 1. 无论技术成功或失败，结算原实际费用

使用原 `src/wcomr/cara_fast_terminal_r2.py` 的 `settle_original`，在 **four_card中央主机** 对原RUN结算，读取捕获的真实wall bill，不估算、不写两卡旧副本、不新增第二个job。

四卡已有通过R15的元数据CPU stage：`/data20t/gaokuangda/worldcache_workspace/.sync/cara-fast-CPU-ada-r15-20261028`。它包含与实际GPU准入一致的三个post模块、`scripts/postprocess_cara_fast_r2.py`、原协议/RUN_SPEC及四卡hostname绑定。先比对实际GPU registration中的相关SHA；只向新的 `A32-post-inputs/` 写捕获副本，不编辑已验证source，不重启旧CPU容器。

可在该stage的同一固定Python3.10 CPU环境中运行 `postprocess_cara_fast_r2.py settle --capture <捕获文件> --project /data20t/gaokuangda/worldcache_workspace --output <唯一结算回执>`。若用新容器，只开放CPU、固定原image、无网、root只读，挂载必要的中央reports和原预算锁供该原函数原子结算；不得暴露CUDA。记录中央before/after和bill SHA，保留其他jobs与16.5旧未知责任。发生断线先读原中央ledger和该结算回执；`Pool.settle`原费用幂等，禁止再reserve。

### 2. 技术接受和基线评分

`postprocess_cara_fast_r2.py release --capture ... --settlement ... --output ...` 会验证完整32分母、真实三臂门、原源码/参数、数值与时钟、干净Native、独占/热界、原件SHA、释放、guardian恢复和已接受中央账单。失败卡只记失败与费用，不能进入评分、冻结或B36。

成功时，用同脚本 `manifest --capture ... --settlement ... --output ...` 派生**恰好12对FIT**，包括两个新干净Native锚点；不访问CHECK、不加阈值搜索、不从部分结果选。将完全相同的manifest字节放在原两卡项目 `outputs/cara-fast-cal-a32-r2-20261028/A-score-CPU/manifest.json`，核对SHA及内嵌manifest_path。

同脚本 `score-command --project <原项目> --stage <原GPUstage> --manifest <原manifest> --output <新命令回执>` 只生成已通过R15检查的无GPU命令：原source/视频只读、评分目录可写、2CPU/8GiB、无网、固定原image、最大2小时。它不自动启动，必须在上述实际终态/释放/结算接受后才执行。

真正启动CPU评分前检查原容器名 `<原stage名>-A-score-cpu`、scores与唯一intent是否存在。若有任何已有句柄，恢复它；没有才以x/fsync写 `A-score-CPU-intent.json`，绑定launch/manifest/命令/source SHA，然后单次Popen，保存PID/start ticks、容器、日志和实际开始。不能因连接超时再启动，也不重评旧批次。原worker用alarm7200秒和2线程限制；评分进程不初始化CUDA。

CPU退出后用 `capture_cara_fast_terminal_r2.py --launch <原launch> --score-manifest <同字节manifest本地副本> --output <新捕获>`。活跃/未知CPU只给运维状态。`postprocess_cara_fast_r2.py accept-scores` 必须接受12/12、93帧、92时序对、原模型/实际保存参数、原Alex和PIQ版本/权重、完整曲线与汇总、正确cgroup及真实CPU容器退出，再用 `freeze` 重新验证全部原链并一次冻结WC/RA/Native-k。按冻结规则无法匹配目标时保留UNMATCHED，不扩网格；这仍不授予B36。

### 3. 完成后

B36核心执行承接已在独立CPU夹具中双端接受，见 [B36_CPU_HANDOFF_R1.md](B36_CPU_HANDOFF_R1.md) 和 `reports/cara_fast_B36_CPU_acceptance_r1_20261029.json`。A32真实六份终态/评分/冻结原件生成后，可交给 `cara_fast_b36_r1.read_handoff` / `bind_handoff` 验证；CPU夹具冻结文件不可用于实际B。仍不自动启动GPU或B36。

更新 `docs/project_status.json` 的 `fast_A32_execution_20261028`、WORKSTREAMS的运行指针和742后续研究记录，按生成器统一更新导航。若已结束，生成器运行展示也要改成终态；不得让旧RUNNING快照继续冒充实时状态。保留原历史60行科学结果和所有失败；A32完整接受后才新增相应科学事实。提交精确owned路径，推送private origin；不发送其他对话或外部消息。B36预计A6000约5.02GPUh、建议硬5.5，超过4GPUh，向用户解释目的并等独立授权。
