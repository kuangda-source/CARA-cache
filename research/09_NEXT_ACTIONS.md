# Next actions — 官方10文件hash完整通过，VQA待部署/准入

1. CPU r4/source39993d1已exit0/633.154270秒、三PIDs退出/CPU锁释放/hash与账本不变。[10文件完整性](../reports/w1_judge_assets_r4_integrity.json)/[终态审计](../reports/w1_judge_assets_r4_audit.json)均通过，无partial，4255140312字节权重SHA256与官方LFS一致。未模型load/forward/评分；旧r1/r2/r3失败保留，不再下载。
2. commit/push本次资源回执/docs，按[runner卡](27_W1_VQA_RUNNER_PREPARATION.md)hash部署源码/问题/原prompt fixture，最终Linux25检查与完整资产复核。deploy助手只在原CPU/GPU全终态/锁可用时执行，不把CPU通过作实机forward。
3. fresh预算/global锁/GPU UUID/VRAM/apps准入，只提交唯一outputs/w1-vqa-r1；单batch900秒/一次离线BF16 SDPA加载/原8/42参考39接受候选题，robot3题拒绝保留。GPU已用3.612360697/4h，余0.387639303h，全部hash/load/失败/评分/flush计费，不保证900秒完成/不扩额。
4. 同handles只读观察，每题partial持久化，invalid继续/保留bounds，技术错停止。不得改在跑源码/协议、重问改提示、观察失败重复启动。终态后核验全PIDs/锁/GPU释放/monitor/source/模型视频原题hash/实际cost，原raw答案与原题重新汇总，partial不得写完整。
5. scalar CAL8仅机制、重放7接受1拒绝/MUSIQ3升4降无整体质量或clean速度收益。小2B/10采样帧不是235B标准Joint/完整动态物理真值或独立确认，暂不加W2。不要求非必要人评/训练/付费/自动扩额；关键预算/方向决策需形成具体方案后交用户。每次meaningful代码/回执/docs同步GitHub。
