# N10完整资源已在服务器接受，完整五模型CPU已启动

2026-10-18。**自动质量评价的最后一项权重资源已接通：原ViCLIP完整1.71GB文件在服务器独立全SHA接受，随后完整五模型CPU已单次派发。** 本次没有新GPU、视频或质量分数。连续修正四臂的代码准备保持[569](569_WC_N10_MIDPOINT_REESTIMATE_AND_CORRECTION_WINDOW88_LOCAL_PREPARATION_20261018.md)，不以准备工作替代实验结果。

## 原资源完整收尾

原SCP按重估后的01:50仅查收一次：[原件](../reports/wc_paper_N10_original_SCP_R1_collection_20261018_0150.json)与[离线独立接受](../reports/wc_paper_N10_original_SCP_R1_independent_acceptance_20261018.json)确认原Mac worker已结束，远端正式文件为1,710,545,812字节，独立全文件SHA为 `7a4d6ad6eac6632db3693f4b97f9f8f6445b65b1e139a6fc6686150522238c56`。原producer记录与此次独立读取一致；单次传送和远端校验约2559.04秒，原失败资源与partial均保留。

半程一次、最终一次均已完成，`worldcache-n10-scp`及`worldcache-n10-scp-2`已删除。没有重复SCP、改TLS、模型加载或账本写入。

## 当前完整CPU范围与身份

[实际launch](../reports/wc_paper_N10_full_five_model_CPU_R1_launch_20261018.json)绑定source `cd8837082d7cfc43ad889019b1c06587aed06a0d`，独立stage `.sync/wc-N10-models-cpu-r1-20261018`，244个实际payload；原PID **1679058**／start_ticks **555441328**。原注册SHA为 `261802e05507bb5691c3bc5fa15dd3956395132a48352510cfef7ab26dc6fa56`。

完整角色为 **DINO、AMT_S、RAFT_THINGS、ViCLIP、MUSIQ_SPAQ**。各角色独立进程，使用固定官方权重和源码、FP32／eval／CPU两线程／离线模式；五项都须尝试，任何失败或缺失如实保留。测试输入为合成张量，不读取正式视频，不产生论文质量分数。

本机打包再次遇到111个原文件iCloud占位，已只请求同一原文件恢复；同一launcher继续完成原SHA核对与派发，没有重复启动。资源文件接受与模型接口CPU接受分开。

## 两个查收时点

实际启动 **01:51:49.761960**（unix1792259509.7619598）。

| 检查 | 最早时刻 | 已安排时刻 | 范围 |
|---|---|---|---|
| 技术半程 | 01:59:19.761960 | **01:59:30** | 原PID/start/注册/worker源码、五分母和技术错误；不提前最终验收 |
| 完整查收 | 02:06:49.761960 | **02:07** | 原句柄、244源、全部五角色原件与独立CPU接受 |

对应一次性自动化 `worldcache-n10-cpu`／`worldcache-n10-cpu-2` 已创建。[半程观察器](../scripts/capture_wc_N10_models_cpu_health_r1.py)及[四项本地门槛控制](../reports/wc_N10_models_cpu_midpoint_local_safety_controls_20261018.json)不触发模型或SSH。到时仅一次查询；如仍运行，根据原件剩余角色重估一次并结束当轮，不循环监听。各检查完成后删除对应自动化。

最终仅使用 `capture_wc_N10_models_cpu_r1.py` 和离线 `accept_wc_N10_models_cpu_r1.py`。全部五项通过后，才能绑定实际正式评分身份、完整960位置及整卡成本。当前645待评分、155视频不可用、160静态N/A保持，所有新质量结果为空。

## 其他主线与预算

N09完整40真实生产CPU已接受，原GPU准入因其他账号占满两卡而失败，0子GPU／0费用。原失败fence不重放，不停止他人进程。N09实际GPU测量期间不并发重模型CPU或评分。

连续修正完整24仍为16正式＋8warm／864pairs；本地12项、完整88入口已准备，实际88／真实生产／整卡报价／新GPU仍待，不自动把新A3并入主线结论。可以在N09无实际GPU的资源等待期间准备，原完整40优先级保持。

同一累计cap **226 GPUh**，最近接受快照实结 **110.869061155**、预留0、余 **115.130938845**；origin和所有历史账不变。本轮0新GPUh。严格少于12 GPUh整卡自主规则、半程及预计结束一次查收保持。F/B关闭，无生成器训练、人评、付费VLM或OMR。
