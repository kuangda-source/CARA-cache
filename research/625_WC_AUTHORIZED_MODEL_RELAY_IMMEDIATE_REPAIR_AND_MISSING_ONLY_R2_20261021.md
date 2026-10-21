# 625 — 固定模型中转立即修复与独立缺失续传R2

用户在技术半程发现失败后直接要求“现在就开始修复”，因此现在收齐原失败记录并准备新版本，不再等待原21:11时点才开始修复。原R1 worker、manifest、失败result、86件回执与外盘partial保持；不是重启原任务。

原R1在下载Reason1首个4,968,243,304字节分片时退出，最后完整断点385,875,968字节。固定源码说明三次有界分块尝试耗尽，但原catch未保留底层异常；不能从RuntimeError倒推出具体HTTP错误或服务器故障。对同一固定文件/断点的新一次1MiB诊断已返回206、精确Content-Range/长度且实际收到完整1MiB；当前权限和该请求链路可用，不能据此复原先前故障原因。

新独立R2使用4MiB分块、每块最多8次尝试、90秒socket timeout和2秒起始/30秒封顶指数退避，每次刷新同一冻结对象的请求nonce。严格校验状态、Range、长度和完整对象hash；失败块回滚到已提交断点，保留现存数据。错误只记录分类、HTTP状态、字节范围和时长，不写token、签名URL或原始异常文本。跨域重定向仍移除Authorization。

原96文件/21,358,871,258字节与原固定revision、原HF兼容路径/VAE内容别名不变；先在服务器重新核对完整现存件，只允许登记的10个缺失文件发起下载，不重下已验86件。外盘新job复制并核对原partial作续传种子，原失败job不覆盖。模型临时文件只落 `/Volumes/data`；凭据只在Mac受限文件内，模型每件远端完整hash通过后删除新中转副本。资源任务仍为0CUDA/模型加载/GPU/账本，不代表新机生产CPU或实验就绪。

11项本地实现控制通过：后缀续传、短读回滚、错误Range/长度拒绝、HTTP分类与脱敏、401有界停止、小完整文件200兼容、坏种子完整hash拒绝、超时保留断点、跨域凭据剥离、现存blob及别名核对。原R1完整失败已在用户立即修复授权下本地收件并离线不接受；旧collector的无条件public辅助模型flag另保留raw并离线纠正，不借其他scope标记接受。

本次先发布精确R2源码和配方，再单次实际启动；只有实际launch和一次准入后才记录PID、source和新的半程/ETA安排。8小时仍是初始资源规划，原24小时资源wall上限不变，均非GPU价格。原两卡四小时只读、公开SigLIP任务及BANK24→完整1624/具体12批准/共同预算历史保持。实际续传与排程以下方新回执为准。

- [11项本地控制](../reports/wc_four_card_model_relay_resume_R2_local_controls_20261021.json)
- [同一断点有界请求诊断](../reports/wc_four_card_authorized_relay_R2_bounded_range_diagnostic_20261021.json)
- [原失败即时收件](../reports/wc_four_card_authorized_external_models_R1_human_immediate_repair_failure_capture_20261021.json)
- [原失败独立不接受及scope纠正](../reports/wc_four_card_authorized_external_models_R1_human_immediate_repair_independent_nonacceptance_20261021.json)
- [独立R2配方](../manifests/wc_four_card_frozen_model_relay_resume_r2_20261021.json)
- [独立R2实现](../scripts/relay_wc_four_card_frozen_models_resume_r2.py)

## 实际新R2启动、准入和排程

新source **7f79ceef2e382f12814816ba6ec4955df52a1bad** 已推送CARA-cache；实际 **17:42:17.428** 单次启动，PID **94749**，新job `/Volumes/data/worldcache_resource_relay_20261021/nvidia-fixed-models-resume-r2`。worker SHA `9e1529de5ee89bc1326e73d05888dc667f88ec9bbd826dc60c16954b190b0826`、manifest SHA `63a98f351e53ab7e0d5c64baac5551363119a3fe85b7a4eba0daf4539f7694ce`、原receiver/helper SHA `d3556447a46934ab26fd1db7811faad4b37112b7934416b98b2cc54542a64950` 均已按一次实际准入核对。完整原86件复用，当前只请求登记缺失；新种子与旧385,875,968字节partial完整SHA一致，准入已观察推进8,388,608字节，证明恢复了实际下载，不是仅提交计划。新执行器在Mac，精确执行源码已GitHub发布；服务器字节接收器仍用原已验不变代码，未修改原c9/e8/88科学或资源stage。

首批4MiB块全wall8.229秒/响应头3.821秒，只有单块观察，不能当稳定带宽。按剩余下载、上传与哈希余量将初始8小时规划保守改14小时，原启动回执不重写、原24小时资源上限不变。已实际读回 **2026-10-22 00:43** 技术半程（r2）和 **07:43** 全件查收（sha）；旧R1的21:11收件由本次直接立即修复授权取代，不再另查原失败任务。若届时仍运行只依据保存快照重估一次，不循环。公开SigLIP原自动化和两卡每4小时只读保持。

- [新实际launch](../reports/wc_four_card_authorized_external_models_resume_R2_launch_20261021.json)
- [一次实际准入](../reports/wc_four_card_authorized_external_models_resume_R2_admission_20261021.json) / [独立技术准入](../reports/wc_four_card_authorized_external_models_resume_R2_independent_admission_20261021.json)
- [资源规划修正](../reports/wc_four_card_authorized_external_models_resume_R2_collection_plan_20261021.json) / [实际排程读回](../reports/wc_four_card_authorized_external_models_resume_R2_actual_schedules_20261021.json)

## 公开两辅助模型已独立完整接受

[623实际原句柄恢复](623_WC_PUBLIC_ASSET_R1_TIMEOUT_AND_MISSING_ONLY_R2_RESUME_20261021.md)于17:55只捕获一次原公开R2：14文件/5,034,332,532字节全哈希、两命令0、退出与13件复用/唯一SigLIP请求均独立通过。automation-2已完成删除，sha07:43已补真实三件套及复用检查。本625的生产96件R2 scope/source/PID94749、00:43半程与07:43全SHA不变；公开文件接受不替代自身生产资产/完整推理CPU或GPU准入。

## 最新服务器镜像实测与资源失败接续

[626服务器实测](626_WC_FOUR_CARD_SERVER_MIRROR_ROUTE_COMPARISON_AND_FIXED_MODELSCOPE_WEIGHT_IDENTITY_20261021.md)：魔搭四个Reason1分片的元数据SHA256/大小与冻结NVIDIA精确一致；同一4MiB1.740秒、Mac代理11.843—12.416秒，两次16MiB1.106—1.164秒（13.74—14.47MiB/s），样本哈希交叉一致；短测不作完整稳速或全资源ETA。HF-Mirror首次4MiB3.787秒后429，直连HF两次20秒超时。另已只读确认原Mac R2 source7f79ceef/PID94749于18:23:48.385技术失败，8次SSLEOFError，原1,132,462,080字节partial及source/job保持；未重派或接受完整96件。旧r2半程已删，sha改约本日19:35一次故障/魔搭来源接续（不是新worker ETA）；新下载worker尚未启动，后续须独立源码/注册、断点绑定与真实launch半程/终态。两卡22:12四小时只读保持，0模型加载/CUDA/GPU/账本。

原先00:43/07:43为已失败R2的历史安排，不再作为新资源任务时点。公开14文件完整接受和科学卡所有门槛保持。

## 2026-10-21 完整96资源R3已启动，23:51半程／明晨03:51全件查收

[627 R3](627_WC_FIXED96_HYBRID_R3_SERVER_MODELSCOPE_AND_ORIGINAL_HF_RESOURCE_CONTINUATION_20261021.md)：原R2失败已完整本地收件并独立不接受，原源码/job及1,132,462,080字节断点保留。新GitHub source3d2dd5e1的R3于19:50:46.056单次启动Mac PID99269；19:51一次准入核对原server Docker PID527857/start936852533、source/worker/manifest及全部原96，16项全过，正接收原断点。四Reason1字节相同分片改server匿名魔搭、其余原HF缺失文件只Mac外盘；完整96/21,358,871,258字节分母、原HF revision/兼容路径保持。新实现14项控制通过，资源准入不是完整资产/生产CPU/GPU通过。2CPU16GiB/隐藏GPU，0模型加载/CUDA/科学GPU/账本写；server fresh数据盘352.642GiB，旧receiver不存在。已读回r3今晚23:51技术半程、r3-96-cpu于10月22日03:51完整全SHA；旧sha接续已删，两卡四小时只读22:12定义保持。完整资产接受后依次LPIPS/完整推理CPU/实际兼容/各scope新机CPU与报价/唯一权威v2交接，才接BANK24→已登记CPU诊断→完整1624，具体12批准及cap226/origin历史不变；科研54行不变。
