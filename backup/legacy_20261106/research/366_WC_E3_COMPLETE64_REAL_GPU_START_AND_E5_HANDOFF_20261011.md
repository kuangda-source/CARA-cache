# 完整 E3 补验已真实启动：64 位置、10 复用、54 新生成

**E5 完整验收后，已按用户准确批准启动唯一 E3 补验卡。** selected CPU 检查退出 0，现场准入通过，原 GPU supervisor、绑定自动 post CPU 与第一组模型均有实际存活句柄；本卡生成、评分和最终科学结果仍在进行。

## 完整范围与执行

卡为 `WC-E3-CURRENT-BIRTH-COMPLETE64-REUSE10-FRESH54-R1-20261011-A`，保留两种来源规则 × 四个 CAL 场景 × 八方法的 **64 位置**；复用 **10** 个已合格位置、新生成 **54** 条完整路径。共 **20** 次独立模型加载，每进程最多 **3** 路径；新生成部分为 **1944 次更新／3888 次 CFG 调用**。完整 forecast **12.377456422 GPUh**。

阶段目录 `.sync/wc-e3-complete64-selected-r1-20261011`，输出 `outputs/wc-e3-current-birth-complete64-reuse10-fresh54-r1`。source 为 `2e39cd31b593540130c08a394b92d9f5b5b5db42`，**449 方法源文件＋16 执行源文件**全部保持。selected 配置 SHA 为 `4ae93359ff2e0ec51fdcb3aa957ecdfcca4b6724119146354883ee3e367b57ba`，协议 SHA 为 `3ca6e941c45684e5853be9ad418dedc2194c48bb5e0ce69f000d6c7526291d72`，准确授权 SHA 为 `a3119dd46f1005a56abbd371880189622487f914b0fe9080250ca4ddf9f4c843`。

## 原始启动证据

selected driver `4163637` 与 CPU 子进程 `4163775` 均已结束、退出 0，实际 CPU 检查耗时 **86.129615 秒**；检查未提交 GPU、未改变账本。之后唯一原执行链为：

| 角色 | PID | 启动观察 |
|---|---:|---|
| GPU supervisor | 4163981 | 实际存活、命令绑定冻结 stage 与 source |
| 自动 post CPU supervisor | 4163982 | 实际存活、绑定原 GPU PID |
| 第一模型 E3_BLOCK_01 | 4164075 | 实际存活、首组计划 3 路径 |

fresh 准入 UUID `GPU-cebf7119-cf03-23b9-e192-cd196332b704`，RTX A6000、cc 8.6；准入时 24 MiB、无 compute app。独立启动观察时，目标 GPU 的实际 compute app 为原模型 PID `4164075`、**13074 MiB**。这证明实际执行已经开始，不替代完整路径或质量结果。

## 预算与后续

前一 E5 已独立验收，实费 **4.168024668 GPUh**，前实结累计 **46.076713614／77.895246590**，新增 48 窗口余 **31.818532976 GPUh**。E3 为累计第 **80** 次 GPU 作业。当前账本 `used=cap` 是本卡在途剩余预算预留，**不是已经消耗 77.895 GPUh**；原 supervisor 的 billed limit 为余下 31.818532976，旧 seconds deadline 关闭，最终仍按原完整单作业实际 wall 结算，累计 cap 不变。

只跟踪上述原句柄和原输出，不重复提交或修改冻结源。完成后由原绑定 post 自动读取全部位置、原件和有效兼容视频，并执行 93 帧 CPU 评分；独立终态验收与科学报告随后完成。技术失败、拒绝、部分和未开始位置均保留在 64 分母中。

E5 省算模块的输出保持证据留存，E3 沿自身已批准冻结实现执行。P 五读出完整 CPU 证据及 13.060019179 GPUh forecast 保留，自身 above8 批准未授，待 E3 结果和实结预算后再评估；E2 原问题保持。继续 WorldCache，不新增训练或人工评审。

来源：[唯一 selected pipeline 启动](../reports/wc_e3_complete64_selected_pipeline_r1_launch_20261011.json) · [独立真实启动观察及原回执](../reports/wc_e3_complete64_real_gpu_start_r1_20261011.json) · [E5 完整结果](365_WC_E5_COMPLETE24_REAL_HEAD_EQUIVALENCE_RESULTS_AND_E3_NEXT_20261011.md)。启动观察是明确时间点的快照，后续以实际原句柄、原件和终态回执为准。
