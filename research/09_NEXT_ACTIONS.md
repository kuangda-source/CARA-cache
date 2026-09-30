# Next actions — 自动成像终态，开发VQA资源准备

1. [成像结果](25_W1_IMAGING_RESULTS.md)：原8分母/7完整可比对、3升4降、mean delta +0.004254295，robot拒绝保留，无一致质量改善/标准语义物理/clean speed/独立确认。暂不加W2或判方法通过。
2. [MUSIQ终态审计](../reports/w1_imaging_r1_audit.json)/[重新计算汇总](../reports/w1_imaging_r1_summary.json)确认旧3PIDs退出/锁释放/GPU释放/source与15输入视频hash一致。累计3.612360697/4GPUh，余0.387639303h，无GPU在途。
3. [Qwen3-VL2B资源manifest](../manifests/w1_development_judge_assets.json)/[官方文件完整性](../manifests/w1_development_judge_integrity.json)固定公共revision/10文件约3.974GiB。CPU acquisition cap1200秒到项目hfhub，匿名官方端点，不写共享cache/不GPU；3 CPU测试通过。commit/push/hash部署CPU脚本/LinuxCPU后，仅启动一次outputs/w1-judge-assets-r1；launch receipt/原PIDs/日志必须归档，不据观察失败重复提交。
4. 下载终态确认父/子退出、完整文件SHA256/Git blob与manifest匹配，offline config/processor/model兼容；CPU准备不作VLM inference或质量结果。已有42原题hash输入保留。
5. 下阶段VQA是小模型开发评价，不是论文235B标准Joint。先冻结完整原8分母/原题/采帧/提示/解析与输入hash、估算成本，从原余量内有界提交；拒绝与parse/unknown保留，不改题或挑场景，不人评/付费/训练/扩额。
6. 仍需语义/物理/动作完成与clean重复配对/独立确认。若完整下一GPU任务超余额，先完成有界准备并提出具体资源方案，重大预算/方向决策交用户；每次结果/代码/文档同步GitHub。
