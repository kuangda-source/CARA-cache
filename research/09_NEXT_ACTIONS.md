# Next actions — judge镜像续传与VQA输入准备

1. GPU阶段均终态：固定重放8技术轨迹/7接受1robot拒绝，MUSIQ3升4降/mean delta+0.004254295，无整体/物理质量或clean速度正结果，暂不加W2。原GPU累计3.612360697/4h、余0.387639303h，无在途。
2. CPU r1直连失败、r2代理下载timeout exit124均终态/PIDs退出/锁释放，r2保留750MiB，downloader旧RUNNING文件不能当live。归档[r1](../reports/w1_judge_assets_r1_audit.json)/[r2](../reports/w1_judge_assets_r2_audit.json)与原failed receipts；代理已在r2结束后停止，共享隧道/代理不改。
3. [resume资源manifest](../manifests/w1_development_judge_assets_resume.json)与[官方hash manifest](../manifests/w1_development_judge_integrity.json)：同10文件/固定revision，匿名镜像已同revision/8MiB prefix验证并测吞吐；CPU-only cap3600秒，不扩GPU cap。commit/push/source hash/LinuxCPU后唯一outputs/w1-judge-assets-r3，复用部分cache，不改旧协议或观察失败重复提交。
4. 续传终态后确认全PIDs退出/CPU锁/source，逐文件Git/LFS完整digest通过，再offline model/processor兼容，cleanup任务owned helpers。部分字节/CPUprocessor通过不代替权重完整性或VLM forward。
5. [开发VQA卡](26_W1_DEVELOPMENT_VQA_PREPARATION.md)/[输入协议](../manifests/w1_development_vqa_protocol.json)：原8/42原题、同single-question提示/输入、requested2fps实际10帧，严格YES/NO/invalid bounds，robot拒绝不插补；本地7CPU和真实Linux config/processor/video输入通过，未VLM forward。实现/检查runner并成本准入后拟单batch900秒/all原8/所有原题/一次load，从原余量扣除。
6. 小2B是开发代理，不是235B标准Joint/质量通过。仍需标准语义/物理、clean重复配对/独立确认；GPU预算不足时先形成具体方案再交用户，不引入非必要人评/付费/训练/自动扩额。代码/回执/docs每次同步GitHub。
