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
