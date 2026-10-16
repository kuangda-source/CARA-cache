# 固定评分权重：本机截断已保留，精确HTTP分段修复通过CPU检查

2026-10-16。**已定位第二次获取失败为长响应提前结束，改用已验证的精确HTTP范围读取同一固定权重。** 13项小文件/句柄控制通过；真实新分段任务尚待本提交后单次派发。N07主线及明早05:30查收保持。

## 14:00原件查收

原本机R2/PID18318已终态，实际收到78094879字节，用时166.582074秒；HTTP200声明1710545812字节，但响应提前结束，原worker按大小/全SHA拒绝并保留`.part`。原partial SHA为`23a9d7ec9a920190d9adc954288ce02dbea8cfd7a0dcdae95a3e655a7f853037`。查收后只离线分析该原回执，没有重查或重派原任务；原14:00资源自动化已暂停。

原服务器R1的0字节超时、R2本机截断及所有源码/注册/结果均保持。当前仍没有完整权重、实际五模型CPU结果或新视频质量分数。

## 分段传输的真实网络证据

|实际请求|结果|
|---|---|
|urllib，同URL，0—1048575|HTTP206、完整1MiB、Content-Range正确，与R2第一MiB相同|
|urllib，同URL，8388608—9437183|TLS EOF错误，原错误保留|
|系统curl8.7.1，同URL，8388608—9437183|HTTP206、完整1MiB、Content-Range正确，与R2同偏移字节相同|

成功请求的对象ETag一致，但ETag不是模型全SHA。仍固定HF revision`83290ee59b4e2c0a4d198857edbc79dd186b8d44`的`ViClip-InternVid-10M-FLT.pth`，精确1710545812字节、最终SHA`7a4d6ad6eac6632db3693f4b97f9f8f6445b65b1e139a6fc6686150522238c56`。不替换模型或改指标。

## 新独立R3修复

[分段worker](../scripts/fetch_wc_N10_viclip_ranges_r1.py)通过系统curl和原本机代理逐段获取8MiB。每段核对最终HTTP206、精确Content-Range、长度、对象ETag和未压缩编码；失败响应、头和错误原件保留，已明确终态的HTTP请求最多六次尝试。单次任务不重启，不复用未经本次传输验收的旧78MB数据。

只将完整校验的段按原偏移顺序组装到新`.part`。所有段到齐后仍需精确总大小与完整SHA，才rename为正式权重。逐段请求不是缩小评价或分拆GPU卡；其用途是避免单个1.71GB长响应被中途截断。资源获取没有GPU记账。

[新启动入口](../scripts/launch_wc_N10_viclip_ranges_r1.py)在原R1/R2都已真实终态查收、原R2 partial仍保持哈希、两个真实范围探测通过、源码已提交和磁盘空间通过后，才建立fresh本机stage`.sync/wc-N10-viclip-local-ranges-r3-20261016`。预计60—90分钟，原最早查收为启动后90分钟；实际时刻和原PID由单次launch回执给出，不持续监听。

查收沿用[原本机工具](../scripts/capture_wc_N10_viclip_local_proxy_r2.py)的完整字节接口，兼容原worker及新range worker；增加段进度和同PID nice执行变化识别。完整接受后才使用508已准备的独立SCP；重模型CPU继续避开N07/N08。

## CPU验证及边界

九项分段控制以小型真实字节文件和mock curl检查：顺序组装、短响应重试不重复/漏字节、错误偏移、错误ETag、忽略Range的HTTP200、最终全SHA、源码不符、原stage不重派、代理/重定向后最终响应头。四项查收控制检查原/新worker兼容、独立SHA、nice执行/PID、ETA前不查和外来worker拒绝。

查收测试首次因Mac临时目录`/var`与`/private/var`别名不一致失败，原三项assert失败记录保留；只规范化测试ROOT，未放宽生产路径门槛。13项最终通过不代表真实分段下载已完成。

本轮只有公开资源探测、小文件CPU和只读原件；没有查询N07科学partial、派GPU、写服务器或预算。原累计cap113、已结算与N07完整预留保持；F/B、训练、OMR、人评没有新增。

## 原件

- [原本机R2终态回执](../reports/wc_paper_N10_ViCLIP_local_proxy_R2_collection_20261016_1400.json)。
- [起始范围探测](../reports/wc_paper_N10_same_pin_HTTP_range_probe_20261016.json)、[非零偏移TLS错误](../reports/wc_paper_N10_same_pin_HTTP_nonzero_range_probe_20261016.json)、[curl非零范围成功](../reports/wc_paper_N10_curl_nonzero_range_transport_probe_20261016.json)。
- [完整13项CPU与源码SHA](../reports/wc_paper_N10_range_download_and_capture_CPU_preparation_20261016.json)、[原查收测试别名失败](../reports/wc_paper_N10_range_collector_fixture_R1_failure_20261016.json)。
