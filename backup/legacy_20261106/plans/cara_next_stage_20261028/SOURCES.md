# 来源与依据

查阅日期：2026-10-28。仓库固定观察commit：`7fde97459f65c835d7ae9c688986e603b7191f0a`；不代表服务器实时状态。

## 仓库事实来源

- [R1] DEV128完整接受：https://github.com/kuangda-source/CARA-cache/blob/7fde97459f65c835d7ae9c688986e603b7191f0a/research/716_CARA_DEV128_COMPLETE_ACCEPTANCE_AND_FROZEN_DECISION_20261027.md
- [R2] 原S设计：https://github.com/kuangda-source/CARA-cache/blob/7fde97459f65c835d7ae9c688986e603b7191f0a/plans/cara_cfg_mainline_20261027/01_CFG_Scheduling_Experiment.md
- [R3] 原Q设计：https://github.com/kuangda-source/CARA-cache/blob/7fde97459f65c835d7ae9c688986e603b7191f0a/plans/cara_cfg_mainline_20261027/02_CFG_Cache_Compression_Experiment.md
- [R4] 对计时、WC配置、已有实验的边界：本对话给出的721/722/734/738及实验记录；原文以仓库相应文件为准。本包没有据此推断新的GPU性能。
- [R5] WC73热停和保存账本：https://github.com/kuangda-source/CARA-cache/blob/7fde97459f65c835d7ae9c688986e603b7191f0a/research/736_CARA_WC73_THERMAL_STOP_AND_SETTLEMENT_20261028.md

## 本轮外部核对（不是本项目实验成绩）

- [P1] WorldCache: Content-Aware Caching for Accelerated Video World Models, v1；附录B计时为去噪开始至解码结束，含方法开销。https://arxiv.org/html/2603.22286v1
- [P2] BudCache: Budget-Constrained Step-Level Diffusion Caching；固定预算的离线策略搜索与时间网格对齐。https://arxiv.org/html/2606.13496v1
- [P3] CacheQuant: Comprehensively Accelerated Diffusion Models；缓存与量化联合设计先例。https://arxiv.org/html/2503.01323v1
- [P4] ERTACache: Error Rectification and Timesteps Adjustment for Efficient Diffusion；误差传播与轨迹校正近邻。https://arxiv.org/html/2508.21091v1
- [P5] Bell Labs, Predictive Quantizing Systems (Differential Pulse Code Modulation) for the Transmission of Television Signals；预测量化历史来源。https://www.nokia.com/bell-labs/publications-and-media/publications/predictive-quantizing-systems-differential-pulse-code-modulation-for-the-transmission-of-television-signals/
- [P6] AlignPred: Error-Controlled KV Cache Compression via Alignment and Predictive Coding，2026-10预印本；预测缓存编码近邻，压的是KV，不等同跨去噪残差。https://arxiv.org/abs/2610.17970
- [P7] SVDQuant: Absorbing Outliers by Low-Rank Components for 4-Bit Diffusion Models；量化/内核共同设计，不能把其速度直接外推到Cosmos。https://arxiv.org/html/2411.05007v1
- [P8] Align Your Steps，ICML2024；采样网格近邻，不等同特征缓存。https://proceedings.mlr.press/v235/sabour24a.html

本文中的Fast目标、S-FAST19、备用B-S/B-Q/B-E、预算分池和新评价层级均为本轮设计或数学推导，未被上述资料证明成功。文献存在相似思想不构成自动否决，但不得宣称其已有内容为本项目首创。
