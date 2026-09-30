# Next actions — r3连接中断终态，runner CPU通过，准备r4续传

1. r3/source202e21d实际exit1/IncompleteRead/1153.880144秒，三PIDs退出/CPU锁释放/hash与预算不变，2890MiB保留。[终态审计](../reports/w1_judge_assets_r3_audit.json)。commit/push后新唯一outputs/w1-judge-assets-r4，同镜像/固定revision/官方hash/cache/cap3600CPU-only。保留旧失败，不能因观察超时或状态旧文件重启。
2. 继续同r4 handles至终态，不改在跑文件；终态核验PIDs/CPU lock/source并归档原receipt/wall。exit0后verify_public_assets.py逐文件官方Git/LFS digest，部分字节不冒充齐备。GPU账本保持3.612360697/4h、余0.387639303h，无GPU在途。
3. [VQA runner准备卡](27_W1_VQA_RUNNER_PREPARATION.md)：已实现/本地25+Linux25同范围CPU通过，全部15真实视频timestamped输入与42原题通过，实际runner拒绝不完整权重。尚未模型load/forward/评分。原8/42参考39候选/单题/10帧/严格raw解析/拒绝保留，运行时安装源hash已锁定。
4. 完整资产后部署source/hash，Linux最终检查+fresh预算/锁/GPU UUID/apps准入；只提交唯一outputs/w1-vqa-r1、单batch900秒/一次load/所有原题，从原余额扣除，全部失败/加载/评分/flush计费。不保证900秒完整，不扩额。每题partial持久化，未知技术异常停止，invalid保留继续。
5. 完整GPU终态后核验原PIDs/锁/GPU释放、source/模型/15视频与原题hash、monitor/实际预算，用summarize_w1_vqa.py重算原raw/coverage/拒绝/metadata/token证据。小2B不是235B标准Joint/独立确认。scalar机制、MUSIQ混合结果仍无整体/物理质量或clean速度收益，暂不加W2；标准评价/clean配对/独立确认资源不足时先具体方案再交用户。不引入非必要人评/付费/训练。每次代码/回执/docs同步GitHub。
