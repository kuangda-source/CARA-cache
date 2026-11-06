# N07完整180路径已获批准并启动：新输入、双seed与十方法共同测试

2026-10-16。**冻结的最终共同测试已经在单张A6000上准入运行。** 本卡用八个新提示词、两个seed和十个事前冻结方法，检验GCR修正读出、CPA高保真工作点与强基线、简单前密策略的共同表现。N05与N06的开发结果已完整接受；N07结果尚未产生。

## 授权与预算

用户针对原完整询问明确回复：“批准完整180卡，累计上限提高到113 GPUh”。因此本次获批的是同一累计窗口的113 GPUh上限及完整15.055555556 GPUh卡，已用费用、origin与全部历史作业保持。

|财务项|准入时GPUh|
|---|---:|
|原累计上限|104.971363333|
|获批后累计上限|113.000000000|
|原窗口origin|79.996377372|
|已结算实际费用|93.581824657|
|本卡完整预留|15.055555556|
|预留后可准入余额|4.362619787|

预留由原v2账本按任务加入，实际费用在原任务终态后替换预留。不是从现在新增113 GPUh，也没有重置48窗口。后续N08完整40路径预计3.6275 GPUh，按当前快照可覆盖；其后约余0.7351 GPUh只是两张报价的算术余量，N09/N10未知真实GPU费用尚未确认。

原“严格少于12 GPUh自主执行”规则继续适用于后续完整卡。N07超过12，使用本次具体整卡批准；不缩小或分拆矩阵。

## 已冻结的完整范围

八个新prompt各执行seed17、43，共16请求。十方法为：

`NATIVE35 / NATIVE26 / WC_HALF / RA_HALF / RA_DEFAULT / RA_DOUBLE / A_NO_P / TABLE_PHASE_H1 / FRONT_DENSE_C / FRONT_DENSE_A`。

正式160路径＋完整预热20路径，共180路径、6318次guided更新对/12636次CFG调用、一次模型加载、零在线teacher。原提示词、negative、guidance、768×432/93帧规格与全部方法工作点保持冻结。Native26实际27次更新，Native35及缓存方法为36次更新。

运行源仍是通过六命令真实生产CPU的`140d0a6af7d5be16d1b191ab3a8e68ffe83d0007`，1725份payload哈希一致。当前后续N10工具提交不替代该原运行源。原配置内“待批准”等字段保留冻结时历史，实际新授权通过独立原件绑定，不修改已验收stage。

所有可配对正式视频采用同prompt、同seed的Native35参考，执行93帧CPU LPIPS；拒绝、坏视频、技术失败和缺失保留原分母。统计先在prompt/seed内配对，再按prompt分组，不把视频帧当独立样本。N07每格一次计时；稳定clean倍数由后续N08重复测试回答。

## 原任务身份与查收

|项|原值|
|---|---|
|卡/run|`WC-PAPER-N07-FROZEN-SHARED180-R1` / `wc-paper-n07-frozen-shared180-r1`|
|stage|`.sync/wc-paper-n07-production-cpu-r2-20261016`|
|GPU|GPU0，`GPU-de9a5370-cd87-0f1c-a48e-288888777dd3`|
|launch id|`798d9047-62e7-4a25-8112-5ab8910226fa`|
|supervisor|1115797 / start542326777|
|runner|1115898 / start542330755|
|CPU post watcher|1115798 / start542326783|
|实际准入|2026-10-16 13:26:43.956410，北京时间|
|原最早终态查收|2026-10-17 05:26:04.252106，北京时间|
|安排的一次查收|**2026-10-17 05:30，北京时间**|

原配置SHA为`9de3e5b9c2ce0377888e1244aa77043b42d4f92f0d9cea498c13c59e3aeafd0c`，注册SHA为`ebf9703a7babd41d4a8b6cf473427e2a66c5a5a689ff92fd094048c496f304f4`，生产CPU证明SHA为`bc2516964d0ab3f8271992caf316a5ab3eccb64a5ebab19d4a5688a341c3a0fa`。

启动后第一个快照发生在supervisor校验源期间，仅有派发、尚未预留；随后一个延后准入快照确认原三句柄、UUID锁、完整预留与实际child。两份均保留。没有读取正式科学partial或持续监听。之后按原ETA一次收取终态、完整180分母、CPU审计/评分、账单及自身资源释放；若CPU post仍未完成，按剩余工作量另约一次后结束，不重复派发。

## 接续优先级

1. 接受本完整卡的全部适用原件、视频、评分、费用与资源释放，并报告各prompt/seed结果、失败和条件。
2. 完成N08九命令实际生产CPU及原完整40路径重复clean测速，五角色保持开发阶段同次冻结，不能依据N07重新挑测速对手。
3. 补N09真实部署开销和N10固定指标质量评价。N10五模型完整CPU链已在[505](505_WC_N10_COMPLETE_FIVE_MODEL_CPU_BATCH_STAGING_AND_INDEPENDENT_ACCEPTANCE_READY_20261016.md)准备，真实模型尚未运行；资源传输按[507](507_WC_N10_SERVER_RESOURCE_TIMEOUT_RETAINED_LOCAL_PROXY_DOWNLOAD_AND_MAINLINE_PRIORITY_20261016.md)推进，重模型CPU避开主线生成和clean计时。

P/T1增强后排，F/B保持关闭，不增加训练、OMR或人评。近邻Cosmos忠实适配与第二骨干仍是明确待讨论范围，不由本卡自动补齐。

## 技术记录与原件

累计上限独立helper首次被系统Python3.8调用，在`Path.is_relative_to`处失败，尚未写预算；原失败回执保留。随后用已有generation Python3.10执行同一Git绑定helper，成功增加cap，逐项断言origin、jobs、已用和预留保持。未修改采样/数值代码，未重复派GPU。

- [人类cap批准原件](../reports/wc_paper_N07_cap113_direct_human_approval_20261016.json)与[整卡启动授权](../reports/wc_paper_N07_full180_direct_human_launch_authority_20261016.json)。
- [fresh资源](../reports/wc_paper_N07_human_approved_fresh_admission_resources_20261016.json)、[cap首次失败](../reports/wc_paper_N07_cap113_server_extension_receipt_20261016.json)、[实际cap扩展](../reports/wc_paper_N07_cap113_server_extension_R2_receipt_20261016.json)。
- [单次派发](../reports/wc_paper_N07_frozen_shared180_GPU_launch_20261016.json)、[初始快照](../reports/wc_paper_N07_frozen_shared180_GPU_admission_20261016.json.gz)、[实际准入快照](../reports/wc_paper_N07_frozen_shared180_GPU_admitted_20261016.json.gz)、[离线独立准入接受](../reports/wc_paper_N07_full180_independent_admission_acceptance_20261016.json)。
