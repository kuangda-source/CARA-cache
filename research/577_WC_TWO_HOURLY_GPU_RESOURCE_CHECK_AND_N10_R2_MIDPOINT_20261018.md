# GPU资源改为两小时一次，五模型R2半程全部记录exit0

2026-10-18。用户回复不知道GPU释放时间，要求每两个小时检查。**已创建 `worldcache-gpu` 两小时间隔的资源检查；占用状态不变时安静，有空闲可行动变化再继续主线。** 这不改变GPU预算、完整卡范围或已安排的科学验收时点。

资源检查每次只读两卡UUID／显存／利用率／计算进程、逐UUID锁及权威v2账本，不读取方法质量或速度partial，不干预其他账号任务。显存占满但利用率0不能当空闲。主线N09完整40优先，原失败stage的dispatch fence保持；新准入须fresh stage／source／真实生产CPU／完整报价／v2／UUID。后续整卡严格少于12 GPUh沿用自主规则；两小时检查不替代具体长卡的一次半程和预计结束后验收。

## N10修复R2半程

按原02:22仅一次[技术查收](../reports/wc_paper_N10_full_five_model_CPU_R2_midpoint_20261018_0222.json)及[独立技术接受](../reports/wc_paper_N10_full_five_model_CPU_R2_midpoint_independent_20261018.json)：sourcefb89a755／注册／worker源码和五分母匹配，原PID1688791已结束，五角色文件均存在且都记录exit0，bundle技术状态为 `N10_ALL_FIVE_REAL_MODEL_CPU_PROBES_ACCEPTED_NOT_VIDEO_SCORES`。

完整角色证明／输出张量身份尚未独立接受，因此还不能称新五模型全部接受。原 **02:30**完整原件查收保持，最早02:29:16.819221；半程自动化`worldcache-n10-cpu`已删除，最终`worldcache-n10-cpu-2`保留。原R1错误与1／5接受保留，当前正式质量分数仍0。

## 连续修正88已完成

[576完整结果](576_WC_CORRECTION_WINDOW_FULL88_CPU_ACCEPTED_AND_FULL24_PRODUCTION_NEXT_20261018.md)已独立接受88／88数值路径和三命令，原source57b4c19、1686源和runtime身份一致；核心257.9014秒、bundle332.7927秒，0CUDA／GPU／新视频。两个查收自动化均已结束删除。下一步接完整24真实生产入口／旧12端点与四预热控制／完整报价，新A3终点仍为空。

本次新增GPUh=0；累计cap226、最近实结110.869061155／预留0余115.130938845及origin历史不变，fresh账本准入为准。GPU正式测速不并发重CPU模型／评分；F/B关闭，无训练、人评或OMR。
