# 完整五模型CPU原件已查收，连续修正88数值CPU已运行

2026-10-18。**本轮把评价器问题定位到了具体的接口描述和隔离事件，连续修正的真实数值检查也已接上。** 没有新GPU、视频或质量分数；原N12完整三臂结果保持。

## N10完整原件：1／5独立接受，错误全部保留

02:07仅一次[完整查收](../reports/wc_paper_N10_full_five_model_CPU_R1_collection_20261018_0207.json.gz)确认原source `cd88370`、244payload和五项原件均在，原CPU已结束；[独立接受](../reports/wc_paper_N10_full_five_model_CPU_R1_independent_acceptance_20261018.json)仅接受 **RAFT_THINGS**。五角色全部尝试，CPU总131.4854秒。

| 角色 | 原进程 | 独立核对发现 |
|---|---:|---|
| DINO | exit0 | 官方保持宽高比Resize实际为2×3×224×398；验收表误写224×224，故尚未接受 |
| AMT_S | exit0 | 实际源码路径含`utils/../networks`，文件SHA对应已注册源码，但未规范化路径导致身份核对失败 |
| RAFT_THINGS | exit0 | 实际模型、权重、FP32 CPU输出与身份全部独立接受 |
| ViCLIP | exit1 | `Missing real weight load or forbidden CUDA/network activity`；事件中一次`NETWORK_OR_DOWNLOAD_BLOCKED` |
| MUSIQ_SPAQ | exit1 | 同一保护检查报错，事件中也有一次联网／下载被拦截记录 |

后三项原件包含的含义严格区分：实际模型运行返回、独立身份接受和正式视频评分不是同一结论。原件不改写；后续修正将保持官方预处理、原权重和五分母，规范实际身份描述，并先定位两次被拦截调用的来源，保留网络禁止条件。

旧[54项相关本地控制](../reports/wc_N10_original_constructor54_before_actual_failure_repair_20261018.json)仍全部通过，说明原合成接口夹具未覆盖此次真实运行差别，不能用54项替代实际五模型。原两个CPU查收自动化均已完成并删除，R1不重派／不重复查。

## 连续修正完整88已单次派发

已按[CPU顺序补充](../plans/WC_DROP1_WINDOW88_CPU_RESOURCE_WAIT_ORDER_20261018.md)在N10原终态查收后、无本项目GPU运行时接上：[原launch](../reports/wc_drop1_window88_actual_CPU_R1_launch_20261018.json)。

- source `57b4c19fc475795ccfbd90590c4d8d569949df75`；独立stage `.sync/wc-drop1-window88-cpu-r1-20261018`，1686个实际payload／12新overlay。
- 原PID **1685865**／start_ticks **555536543**；注册SHA `5aee8f86d5487f4099d514c516ff1e39ceb3cea407e934d5d8a99dfb17e1fc2d`。
- 两flow×四原CAL×四方法×audit／lean的64条完整36更新路径，加24条原三臂audit控制，共88；另8项新控制和4项原回归。原N12stage及核心源码不改。
- 完整修正窗口21–23、原21单次修正和25D／26D基线均保留；不调alpha／beta或删除位置，不新增教师或P。

实际启动 **02:07:41.912177**。半程最早02:13:41.912177，安排 **02:14**；完整最早02:19:41.912177，安排 **02:20**。两个一次性自动化 `worldcache-88cpu`／`worldcache-88cpu-2` 已创建。到时各一次收原句柄和原件；未完仅依据该次剩余量重估一次，不持续监听或重派。

全部88和三命令接受后才算数值CPU通过；它仍不是完整24的真实生产CPU、GPU或93帧视频结果。生产入口、旧12端点和四预热控制、完整报价及准入继续独立准备，A3结果与时间保持空。

## 资源和接续

N09完整40真实生产CPU已接受；最近一次只读资源快照仍为原其他账号占满两GPU，本项目无GPU预留／子进程。没有恢复失败fence或改动他人任务。N09实际GPU测量保持优先，期间不并发重模型CPU或评分。

同一cap226、最近实结110.869061155／预留0余115.130938845，origin与历史不变，本轮0GPUh。strict<12整卡自主、一次半程及预计结束后验收规则保持。F/B关闭，无训练、人评、付费VLM或OMR。
