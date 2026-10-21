## 2026-10-21 四卡魔搭同字节Reason1短测更快，资源R2失败保留并接新来源

[626服务器实测](626_WC_FOUR_CARD_SERVER_MIRROR_ROUTE_COMPARISON_AND_FIXED_MODELSCOPE_WEIGHT_IDENTITY_20261021.md)：魔搭四个Reason1分片的元数据SHA256/大小与冻结NVIDIA精确一致；同一4MiB1.740秒、Mac代理11.843—12.416秒，两次16MiB1.106—1.164秒（13.74—14.47MiB/s），样本哈希交叉一致；短测不作完整稳速或全资源ETA。HF-Mirror首次4MiB3.787秒后429，直连HF两次20秒超时。另已只读确认原Mac R2 source7f79ceef/PID94749于18:23:48.385技术失败，8次SSLEOFError，原1,132,462,080字节partial及source/job保持；未重派或接受完整96件。旧r2半程已删，sha改约本日19:35一次故障/魔搭来源接续（不是新worker ETA）；新下载worker尚未启动，后续须独立源码/注册、断点绑定与真实launch半程/终态。两卡22:12四小时只读保持，0模型加载/CUDA/GPU/账本。

## 2026-10-21 公开两辅助模型全14已接受，独立资源检查关闭

[623完整收件](../research/623_WC_PUBLIC_ASSET_R1_TIMEOUT_AND_MISSING_ONLY_R2_RESUME_20261021.md)：17:25恢复槽延后，实际仅于17:55:23.834读取原R2 PID397742/start934875508/source88ebc004；原任务15:17:25.447结束、wall3353.677414秒，原进程和本人容器退出。Qwen3Guard与SigLIP全部14文件/5,034,332,532字节独立Git-blob/SHA256及尺寸全过、两命令0；13件复用，唯一注册SigLIP权重请求与完成，15项额外范围核对全过。R1失败与16:23收件UNKNOWN原件保留，不将旧超时认作下载失败；只接受公开两辅助模型文件。automation-2已完成删除，sha已补真实三件套及复用证明；96件生产模型R2 source7f79ceef/PID94749仍按10月22日00:43一次半程、07:43全SHA，两个时点已读回保持。完整Cosmos资源、LPIPS、完整推理CPU、新机scope CPU/报价/兼容及唯一v2准入仍待，BANK24→完整1624/具体12批准/cap226历史与两卡4小时只读保持。0CUDA/模型加载/科研GPU/账本写；本人85709 master/63606 FRPC继续供资源使用。 [原件](../reports/wc_four_card_public_model_assets_resume_R2_terminal_recovery_20261021_1725.json) / [独立全范围接受](../reports/wc_four_card_public_model_assets_resume_R2_full14_resume_scope_acceptance_20261021.json) / [检查关闭与接续读回](../reports/wc_four_card_public_model_assets_resume_R2_completed_handoff_and_schedules_20261021.json)。

## 2026-10-21 用户要求立即修复，独立模型续传R2已实际恢复

[625即时修复](625_WC_AUTHORIZED_MODEL_RELAY_IMMEDIATE_REPAIR_AND_MISSING_ONLY_R2_20261021.md)：用户“现在就开始修复”取代等待旧21:11才定位的安排，原R1失败已本地完整收件并离线不接受，原源/job/partial留存。新source7f79ceef通过11项实现控制并已GitHub发布，17:42:17.428单次启动外盘R2 PID94749；一次准入验原source/worker/legacy/manifest及句柄一致、复用全部86件，只请求注册10缺失，复制核对原385,875,968字节种子并已越过断点8MiB。4MiB/8次有界重试与脱敏错误已生效，模型只外盘、凭据只Mac。按首批分块观察将资源规划改14小时，原24小时wall不改：已实际约10月22日00:43一次技术半程（r2）、07:43一次全SHA（sha）；原8小时启动规划保留为历史，不当完成保证。公开R2原句柄恢复与两卡4小时只读保持；未称完整资源/生产CPU/GPU就绪，0CUDA/模型加载/科研GPU/账本写。 [实际新launch](../reports/wc_four_card_authorized_external_models_resume_R2_launch_20261021.json) / [准入与实际排程](../reports/wc_four_card_authorized_external_models_resume_R2_actual_schedules_20261021.json)。

## 2026-10-21 外盘96件中转技术失败留存，21:11完整查收保持

17:11计划半程实际于 **17:12:00.731** 仅一次本地捕获原外盘中转。source79c9d171、worker SHA d3556447、manifest SHA f59d04a1、原完整96文件/21,358,871,258字节身份全部一致，外盘仍挂载；原PID87082已不活，health技术终态为 `AUTHORIZED_MODEL_RELAY_FAILURE_RETAINED`。health记录 **13:43:47.627** 结束、wall2001.328秒，停在 `nvidia/Cosmos-Reason1-7B/model-00001-of-00004.safetensors` 的download-to-external-volume阶段，`RuntimeError`，技术partial385,875,968/4,968,243,304字节保留。

已有86个注册worker `REMOTE_FULL_HASH_PASS` 回执共 **141,176,513字节**，多数是小文件，不能用86/96推断主要权重完成比例。根据冻结源码与失败阶段，可定位到三次有界分块下载尝试耗尽；原catch只保存RuntimeError，无法进一步区分网络超时、HTTP错误、响应头不符合或短读。这里只读技术health与本地worker/manifest SHA，未读最终result内容、未查询最终远端模型、未运行accept；完整资源未接受，原job/partial/源不改、不重派。

[本次半程原件](../reports/wc_four_card_authorized_external_models_R1_midpoint_20261021.json)与[独立技术失败边界/实际排程读回](../reports/wc_four_card_authorized_external_models_R1_midpoint_technical_failure_boundary_20261021.json)。本半程 `wc4-model-relay-midpoint` 已完成删除；`sha` 的 **21:11** 完整查收保留，并补原失败收件后独立新R2只续传缺失件/安全partial、复用完整已验件和脱敏错误分类的接续；不提前读原result或复活原worker。原公开R2 **17:25** 收件恢复与两卡 **17:48** 四小时只读检查保持。本人SSH master仍供资源使用，不关闭；0CUDA/模型加载/科研GPU/账本写，BANK24→完整1624/具体12批准与全部新机准入前置保持。

## 2026-10-21 公开R2收件未知，17:25一次原句柄恢复

[623公开资源接续](623_WC_PUBLIC_ASSET_R1_TIMEOUT_AND_MISSING_ONLY_R2_RESUME_20261021.md)：16:23唯一终态收件在55秒内未返回JSON而超时，未取得原result/当前进程退出/全14哈希，状态保留UNKNOWN，不接受或重派。原件已保存，原worker/cache/两任务入口保持；只新建本地180秒有界收件器（不改原验收），automation-2已读回重约17:25一次恢复并使用新文件，sha21:11已补此接续。原96件17:11/21:11和两卡4小时17:48时点保持；没有第二次SSH、模型加载、科研CPU/GPU或账本写。 [回执与排程](../reports/wc_four_card_public_model_assets_resume_R2_terminal_unknown_boundary_20261021.json)。

## 2026-10-21 SigLIP独立R2半程健康，16:23完整验收保持

[623半程原件](623_WC_PUBLIC_ASSET_R1_TIMEOUT_AND_MISSING_ONLY_R2_RESUME_20261021.md)：原R2在14:53:07.942一次半程核对中PID/start/source及全部job文件SHA一致；13件已验文件已复用，仅请求注册SigLIP权重，技术字节4.217/5.034GB，无错误、尚无result。仅技术健康，不提前完整接受；半程siglip已完成删除，原automation-2的16:23全14收件、96件外盘中转17:11/21:11、两卡每4小时17:48只读检查均保持。0重启/重派、0模型加载/GPU/账本写，正常无可行动变化静默。

## 2026-10-21 公开模型R1超时留存，SigLIP缺失文件R2已单次续传

[623原件与续传](623_WC_PUBLIC_ASSET_R1_TIMEOUT_AND_MISSING_ONLY_R2_RESUME_20261021.md)：原公开14文件任务触及90分钟上限/TimeoutExpired，PID及自身容器退出；13件独立全SHA通过，唯一SigLIP权重缺，完整资源不接受。原job/result/partial保留，source88ebc004的新独立R2只请求注册缺失文件并复用已验件，14:21:31.718启动PID397742/start934875508；一次技术准入source/worker/manifest/文件一致、原进程活，尚无完整接受。新siglip已约14:52技术半程、automation-2已约16:23全14验收；本触发automation-3已删除。71,648字节新GitHub delta远端全SHA后已删外盘包；未重装基础/重下13件。原96件外盘中转PID87082的17:11/21:11、两卡只读4小时17:48均保持，sha已补R2真实接续，不代收。完整模型/推理/CUDA/新机scope CPU/报价/单一v2仍待，BANK24→1624和具体12批准/预算历史不变，0CUDA/模型加载/GPU/账本写。

## 2026-10-21 两卡改四小时只读检查，四卡接续原BANK24→1624→自动生成器

[622最新决策](622_WC_FOUR_HOUR_TWO_CARD_MONITOR_AND_FOUR_CARD_EXPERIMENT_QUEUE_20261021.md)与[完整后续清单](../plans/WC_FOUR_CARD_EXPERIMENT_QUEUE_20261021.md)：按最新直接人类要求，worldcache-bank24已实际改为14400秒一次，只读恢复状态/原句柄/权威账本，不在两卡自动启动新GPU；以13:47:14.270913实际人类连接测试为基准，下一17:48（最早17:47:14.270913），原15:27由本次改频取代。四卡成为后续实验目标主机，原14:08/17:11/21:11模型检查保留，21:11 collector已补新机生产CPU/完整报价/唯一v2交接后的接续。顺序：资源与新机门→完整BANK24及共享CPU诊断→已批12GPUh完整1624→PG-P1单预算闭环→PG-P2公平消融→PG-P3跨预算/模型再校准→PG-P4冻结后独立确认。原source/scope/gate/已验结果与cap226/origin历史保留；旧机报价不作Ada实测，新机CPU/模型/兼容/共同权威账本仍须分别通过。当前仅准备与安排变更，0新远端查询/CPU/GPU/账本写；正常未知/忙静默。

# 四卡资源补齐：公开模型下载在途，固定生产模型已接通只读授权

## 实际公开模型任务

复用已验env-r3、容器和runtime。source e8d1d4268967cc7683ef6a87f700d36257529ccc的公开任务于2026年10月21日12:37:05.773单次启动：PID389727/start934248913；原job wc-fourcard-public-model-assets-r1-20261021。两份固定snapshot为Qwen3Guard和SigLIP，14文件/5,034,332,532字节。2CPU/16GiB/隐藏GPU，0CUDA/模型加载/GPU/账本。

一次技术半程在原not-before之后已保存：原句柄/worker/manifest一致，仍在下载，没有最终result；已下载字节仅为技术进度，不是完整哈希接受。半程automation-2已删除，13:08计划收件实际13:09:30只捕获一次，原PID仍活/无result，已保存1,284,658,789技术字节的在途边界，不运行最终accept。原最长5400秒不改，automation-3已重新约14:08，新文件terminal_recheck_20261021_1408.json，不覆盖13:08原件；不循环或重派。

自己的SSH master只将服务器127.0.0.1:17897接到本机127.0.0.1:7897代理，模型直接落四卡数据盘。原c9项目不改；GitHub e8源码已转运到独立projects/wc-resource-preparation-e8d1d4268967-20261021，全部增量SHA接受后本机318,380字节临时bundle已删除。已验服务器base/runtime/wheel不重建。

## HF授权和外接硬盘

浏览器账号GaoKuangda已获Guardrail访问权限。在用户逐项批准后创建worldcache-fourcard-download-20261021，只允许三个NVIDIA仓库的读取，无写入、付费推理或管理权限。凭据只在本机0600文件；不传服务器、GitHub或回执。实际whoami200、固定Guardrail文件200、固定主权重206，匿名401的缺口已解决。

按最新直接要求，本机模型中转仅使用可写USB APFS外盘/Volumes/data（观察时余1268.552GiB）；Mac内盘余11.195GiB，不承载模型。96个注册生产文件/21,358,871,258字节（19.892GiB）的新中转worker以GitHub已发布source79c9d171，于13:10:26.252单次启动，PID87082，外盘job /Volumes/data/worldcache_resource_relay_20261021/nvidia-fixed-models-r1。每件先在外盘完整哈希，流式SSH传模型字节，再在服务器独立全文件哈希并建立原HF兼容路径；接受后删除对应外盘副本。HTTP跨主机重定向剥离Authorization，凭据不进入服务器。

## 固定模型与VAE内容身份

主权重固定15a82a2ec231bc318692aa0456a36537c806e7d4/post-trained，SHA256 565bbb2c9645737327983f4461e4d32627bba465b0a8dc26447edea144e1ff47。Guardrail保持d6d4bfa899a71454a700907664f3e88f503950cf。实际Reason1.1别名和Qwen tokenizer均指向Cosmos-Reason1-7B固定3210bec0495fdc7a8d3dbb8d58da5711eab4b423，共用同一组文件，不下载无关T5/旧Llama/Cosmos3-Nano。

原VAE revision6787e176dce74a101d922174a95dba29fa5f0c55现已认证实测元数据404。历史真实decoder_policy_r1_stage_b.json已记录tokenizer.pth为507,609,880字节/SHA256 38071ab59bd94681c686fa51d75a1968f64e470262043be31f7a094e442fd981；可访问的官方固定15a82a2e版本元数据给出完全相同大小和完整SHA。新配方明确分开下载来源与原目标revision，按已证明的字节身份建立可逆缓存兼容链接；不改runtime/冻结decoder策略，不把两个Git revision称作相同。

## 尚待接受

公开两模型尚未全哈希接受；96件生产文件已真实单次启动，原PID/lstart/脚本/manifest/source已核对，尚待全部远端SHA回执。首次本机捕获因Python launcher展开而误判活性，原回执保留，捕获器只修本地身份解析后已核对原进程活、无重启。17:11一次技术半程（最早17:10:26.252）由wc4-model-relay-midpoint负责；21:11一次完整验收（最早21:10:26.252、8小时规划）由sha负责，两个真实app安排均已读回。之后独立离线模型/推理导入、LPIPS评分资产、实际CUDA/驱动兼容、新机scope生产CPU/完整报价和共同权威v2还须分别接受。完整资源/GPU_dispatch_ready仍false，科学GPU未启动。原BANK24→完整1624、具体整卡12GPUh批准、原scope/source/CPU/gate和两卡资源任务均保持。

## 原件

- [公开任务launch](../reports/wc_four_card_public_model_assets_R1_launch_20261021.json)
- [公开任务准入](../reports/wc_four_card_public_model_assets_R1_admission_20261021.json)
- [一次技术半程](../reports/wc_four_card_public_model_assets_R1_midpoint_20261021.json)
- [两次收件安排](../reports/wc_four_card_public_model_assets_R1_collection_schedule_20261021.json)
- [浏览器授权后实际文件测试](../reports/wc_four_card_HF_browser_authorized_fixed_source_probe_20261021.json)
- [固定生产文件配方](../manifests/wc_four_card_frozen_production_assets_r1_20261021.json)
- [外盘中转安全控制](../reports/wc_four_card_authorized_external_relay_local_controls_20261021.json)
- [独立GitHub源码与转运SHA](../reports/wc_four_card_GitHub_resource_preparation_R4_source_transfer_20261021.json)

- [96件实际launch](../reports/wc_four_card_authorized_external_models_R1_launch_20261021.json)
- [原进程恢复核对](../reports/wc_four_card_authorized_external_models_R1_admission_recovered_20261021.json)
- [应用三项实际收件安排](../reports/wc_four_card_model_resource_actual_collection_schedules_20261021.json)
- [GitHub79源码实际转运与本机清理](../reports/wc_four_card_GitHub_authorized_model_relay_R1_source_transfer_20261021.json)
