# 626 — 四卡服务器镜像实测与魔搭同字节Reason1来源

用户要求：“可以，帮我看一下在服务器上直接下镜像站的会不会快一点”。本次仅有界HTTP请求和内存样本，不落模型文件、不加载模型、不初始化CUDA、不占GPU或改账本。收到的模型片段合计48MiB；原96分母、runtime、科学stage和批准保持。

## 实际路由比较

同一四卡主机、同一固定Reason1首分片、同一1132462080断点。所有有效样本严格检查206、Content-Range/总大小、长度；成功路由4MiB样本SHA256相同。

| 路由 | 本次样本 | 结果 |
|---|---|---|
| 服务器直连HF-Mirror | 同一4MiB两次 | 首次3.787秒（1.056MiB/s），重测429；后续Predict/Guardrail镜像请求亦429 |
| 服务器直连HF | 同一4MiB两次 | 两次均到20秒上限，无有效数据 |
| 服务器经既有Mac代理到HF | 同一4MiB两次 | 12.416/11.843秒，0.322/0.338MiB/s |
| 服务器直连魔搭 | 同一4MiB | 1.740秒（2.299MiB/s），同样本比代理全wall快约6.97倍 |
| 服务器直连魔搭较大样本复测 | 同一16MiB两次 | 1.164/1.106秒，13.741/14.467MiB/s；完整样本SHA相同，前4MiB与HF参考相同 |

魔搭终点为 `cdn-lfs-cn-1.modelscope.cn`，不经Mac代理。HF-Mirror首次成功实际转到 `cas-bridge.xethub.hf.co`；镜像入口不证明全部数据来自国内。其429令当前不适合独占主源。

这些是短时、重复同段测试，可能受连接或缓存预热影响，不能外推16GB持续速度、整套模型加速倍数或完成时间。所有测速匿名，不把HF token或签名URL发往服务器/镜像。

## 四个大分片身份精确相同，整文件接受仍待

魔搭 `unsloth/Cosmos-Reason1-7B` 公开API的四个BF16大权重分片，其大小和完整SHA256元数据与冻结 `nvidia/Cosmos-Reason1-7B@3210bec0495fdc7a8d3dbb8d58da5711eab4b423` 全部一致，合计16,584,414,544字节。精确文件名/大小/SHA见[独立分析](../reports/wc_four_card_server_mirror_route_independent_analysis_20261021.json)。

魔搭master只是传输定位，与原NVIDIA Git revision分开登记；下载时仍须每件完整尺寸和SHA，完成后独立全文件重读再接入原HF缓存/别名。现在仅核对元数据和片段，未接受四件整文件、13件完整Reason1或96件完整生产资源。魔搭其余配置/分词器没有接受，不替换原文件。

本次测试的魔搭 `nvidia/Cosmos-Reason1-7B`、`nvidia/Cosmos-Predict2.5-2B`、`nvidia/Cosmos-Guardrail1` 命名空间返回404，仅说明这些具体入口未核实，不证明没有其他副本。

## 相邻发现：原Mac资源R2技术失败，1.13GB断点保留

原R2 source7f79ceef/PID94749已于 **18:23:48.385** 结束，wall2489.327896秒。原worker/manifest/legacy SHA一致、原PID退出；8次有界重试都在1132462080—1136656383范围记录 `URL_TRANSPORT_ERROR/SSLEOFError`，最终 `BOUNDED_RANGE_ATTEMPTS_EXHAUSTED`。它不证明权重损坏或科学失败，也不能唯一归因于代理、远端或永久故障；之后代理的两次样本都成功。

原source/job未修改或重放，原 **1,132,462,080字节** partial仍在外盘，未当完整文件接受。原86个worker小文件回执仅约141MB，不按86/96推算权重进度。本次只保存[技术失败与原件/断点边界](../reports/wc_four_card_authorized_external_models_resume_R2_user_route_probe_failure_boundary_20261021.json)，没有额外远端96全hash或新下载worker。

## 已安排的资源接续

沿用户已有“把资源准备完成/现在就开始修复”的授权，独立新version只续传仍缺的登记文件。优先让四卡从魔搭直接下载上述四个同字节Reason1权重，其余文件保留原授权来源、配置、HF兼容路径与96完整分母。可单次安全流式转移并完整prefix SHA绑定现存seed，避免重下已下载字节，不覆盖旧失败job/partial。每件完成后独立全SHA/大小通过才原子接入缓存；四件子集不等于96资源完成。新资源源码/注册/复用及有界退避控制仍须独立准备并GitHub发布。

旧R2已知技术终态，其 **10月22日00:43 r2半程已删除**；`sha` 从旧07:43改约 **10月21日19:35** 一次故障/新来源接续，并实际读回。19:35是资源恢复工作时点，不是新worker ETA。**本次没有启动新下载worker。** 后续每个真实新launch须一次admission、一次半程和预计结束查收。两卡22:12四小时只读定义保持。

公开辅助模型14文件已完整接受，不重下；完整生产资源、LPIPS、完整推理CPU、新机scope CPU/实际兼容/整卡报价与唯一权威v2仍待。测速不赋予科研GPU准入；BANK24→完整1624→生成器、具体12批准、cap226/origin79.99637737158223及费用历史保持。

## 原件与实现

- [三路4MiB原件](../reports/wc_four_card_server_anonymous_model_route_probe_r1_20261021.json)、[有界实现](../scripts/probe_wc_model_download_routes_r1.py)：source1be1367c执行前已发布。
- [魔搭文件身份及4MiB原件](../reports/wc_four_card_server_modelscope_fixed_identity_probe_r1_20261021.json)、[有界实现](../scripts/probe_wc_modelscope_asset_identity_r1.py)：sourcee064737f执行前已发布。
- [两次16MiB原件及公开源码内嵌](../reports/wc_four_card_server_modelscope_two16MiB_stability_20261021.json)。
- [7项独立范围/身份/样本核对](../reports/wc_four_card_server_mirror_route_independent_analysis_20261021.json)。
- [R2技术失败与断点](../reports/wc_four_card_authorized_external_models_resume_R2_user_route_probe_failure_boundary_20261021.json)。
- [实际恢复接续及其他检查保持](../reports/wc_four_card_server_mirror_probe_resource_repair_handoff_20261021.json)。

## 2026-10-21 完整96资源R3已启动，23:51半程／明晨03:51全件查收

[627 R3](627_WC_FIXED96_HYBRID_R3_SERVER_MODELSCOPE_AND_ORIGINAL_HF_RESOURCE_CONTINUATION_20261021.md)：原R2失败已完整本地收件并独立不接受，原源码/job及1,132,462,080字节断点保留。新GitHub source3d2dd5e1的R3于19:50:46.056单次启动Mac PID99269；19:51一次准入核对原server Docker PID527857/start936852533、source/worker/manifest及全部原96，16项全过，正接收原断点。四Reason1字节相同分片改server匿名魔搭、其余原HF缺失文件只Mac外盘；完整96/21,358,871,258字节分母、原HF revision/兼容路径保持。新实现14项控制通过，资源准入不是完整资产/生产CPU/GPU通过。2CPU16GiB/隐藏GPU，0模型加载/CUDA/科学GPU/账本写；server fresh数据盘352.642GiB，旧receiver不存在。已读回r3今晚23:51技术半程、r3-96-cpu于10月22日03:51完整全SHA；旧sha接续已删，两卡四小时只读22:12定义保持。完整资产接受后依次LPIPS/完整推理CPU/实际兼容/各scope新机CPU与报价/唯一权威v2交接，才接BANK24→已登记CPU诊断→完整1624，具体12批准及cap226/origin历史不变；科研54行不变。


## 2026-10-22 固定96全件接受；R4.1离线CPU资源04:17启动

[628实际接受与接续](628_WC_FIXED96_ACCEPTED_AND_LPIPS_OFFLINE_INFERENCE_CPU_R4_20261022.md)：原R3完整96件／21,358,871,258字节已一次终态收件并独立接受，23项全过：全文件哈希与HF兼容路径、四Reason镜像完整SHA与原断点绑定、原进程／容器／锁退出、新外盘副本清理均通过。公开14件已验原件复用，不重下；原R1/R2失败与1,132,462,080字节断点保留。首次新CPU预检错引旧回执文件名，在创建stage前退出，失败保留；独立R4.1 sourcee5eedef4于04:17:03.983单次启动PID615773/start939888734，fresh原R4 stage不存在、数据盘321.586GiB／主存56.358GiB，15项技术准入核对通过。正在服务器直下官方LPIPS，原env-r3和11runtime保持；随后110离线路径／Reason tokenizer、原受限推理入口、预训练LPIPS合成CPU验证。Cosmos权重0／CUDA0／真实评分0／科研GPU0／账本0；资源CPU不充新机scope生产CPU或GPU-ready。已读回r4-1-cpu于04:40一次半程、r4-1-cpu-2于05:05一次完整验收，旧r3-96-cpu已完成删除；两卡worldcache-bank24四小时只读06:16保持。本轮未查双卡或改权威v2，BANK24→既定CPU诊断→完整1624及其具体12批准、cap226/origin历史与54科研行保持。
