# N10半程确认评分进程已终态，22:43完整科学验收保持

2026-10-18。**一次半程检查确认原N10评分进程已结束，child exit0，GPU0与逐UUID锁释放；完整质量分数与原账单尚未验收。** 本轮没有打开质量journal、metric-results或方法比较，没有新GPU、CPU重模型任务或重派。

## 实际检查与原身份

原20:01半程心跳到达后，按真实时钟核对最早unix1792324815.8404052，实际只读SSH快照时间为 **20:02:22.754288+08:00**。原launch／source d10e9926／registration SHA及原CPU授权绑定与准入回执一致；原supervisor2077516/start561087236、child2077521/start561087296身份保持，当前原进程均已消失，没有PID复用或其他句柄被当作原任务。

监督状态为`N10_FULL960_ORIGINAL_GPU_TERMINAL_NOT_QUALITY_ACCEPTANCE`，runner状态为`N10_FULL960_FINISHED_FAILURES_RETAINED`，原child退出码0。只读错误标签为空，自身GPU0无compute进程、锁可取。原160／960、五模型／19对比及原全部分母没有更改。

## 终态名称不能代替评分计数

**`FINISHED_FAILURES_RETAINED`是原worker正常完成路径固定写入的状态名称，并不自动表示本卡确有评分失败。** 本轮仅对照与原271源CPU registration一致的本地worker源码确认这一语义；没有提取其中的metric_status_counts、all_ready_positions_scored或原分数。

因此，此时既不报告全部645评分成功，也不把该名称解释成失败结论。有效分数、缺失／失败原因、MUSIQ全93帧、19对比和提示词分组统计均由22:43原完整收件及离线接受决定。

## 账本观察与科研接受分开

原v2任务已标记SETTLED，记录本卡 **0.38650610486769843 GPUh**，累计 **114.02498439084846／226 GPUh**，预留0、可用 **111.97501560915154 GPUh**；原origin及历史保持，完整上限6.25没有改变。

上述是半程允许读取的账本技术状态，**原billing／supervisor全wall及逐项科学原件尚未独立接受**，不提前宣布完整财务协议或质量范围通过。GPU与锁释放也不替代全960分母的完整验收。

## 接续

- 本次单次半程自动化`worldcache-n10-960`已完成并删除。
- 原完整验收`worldcache-n10-960-2`保持ACTIVE，**今天22:43**，最早unix1792334562.8404052；使用原launch进行一次终态捕获，之后仅离线核对。
- 原最终／资源自动化未改，不提前读科学结果、不持续监听、不自动重新评分。
- 连续修正完整24仍只有实际报价3.064166667／上限4，真实新stage生产CPU及GPU／A3视频待。即使本卡资源已释放，本次半程不抢开下一卡；F/B保持关闭，无训练、人评、付费VLM或OMR。

## 原件

- [一次半程原件](../reports/wc_paper_N10_full960_midpoint_health_20261018.json.gz)
- [本地独立技术核对](../reports/wc_paper_N10_full960_midpoint_independent_technical_check_20261018.json)
- [原派发与两时点](592_WC_N10_FULL960_GPU_ADMITTED_AFTER_N09_AND_TWO_COLLECTION_TIMES_20261018.md)
