# Next actions — W1-S1 default no-gain; one recent-pair revision

1. F1、W1-P0、W1-S1 r2都已终态；不重启旧身份。r2 output/cache/video/trace等8checks通过，四点scalar/shrink velocity sum-MSE比2.531/5.395，默认候选不进入闭环；详见research/14_W1_S1_INITIAL_RESULTS.md。
2. 只实施一次有机制依据的scalar修订：decay固定0（最近真实full-pair），其他参数/工程样本/四点/官方部署轨迹/warp不变，shrink作为不变控制。修订协议manifests/w1_same_state_recent_protocol.json。源码测试/部署哈希/新鲜准入后运行w1-s1-recent-r1，单个监督任务<=900s/0.25GPUh。不是参数扫描；若仍无优势不重复调同一公式。
3. 账本1.412719678/4GPUh，余额2.587280322h。每次提交前查远端进程/全项目锁/预算/GPU UUID/VRAM/compute apps。一次一个昂贵任务，无第二作业、无在跑源码变更。
4. 人工语义标注不阻塞W1。只有机制候选信号后才进入候选专用parity、固定schedule闭环和独立CAL/DEV；工程四点不是独立确认，当前没有候选生成视频/质量结论。
5. 同步实验报告/原始失败/数值/成本/交接到私有GitHub；不扩预算、不训练、不付费评分、不无依据切换方向。L0非GPU资源核对可穿插；当前不抢跑Wan/OMR。
