# N10资源传输修复：保留服务器超时，经本机既有网络获取同一固定权重

2026-10-16。**自动质量评价所需的固定ViCLIP权重已改从本机既有网络路径获取，N07主线按原方案运行。** 本轮是CPU资源准备，没有新增GPU、模型运行或视频质量分数。

## 原服务器请求的实际结果

13:17按ETA一次查收原source`3c7767f`、PID1113019/start542082643，进程已经终态。请求在取得正文前超时，120.428369秒，收到0字节、没有part。原result和失败身份保持，原stage不覆盖、不重派。该结果是资源传输失败，并非ViCLIP模型、评价指标或研究方向的失败。

本机对同一固定URL的HEAD使用已有`127.0.0.1:7897`代理，3.475406秒返回HTTP200，Content-Length为1710545812，最终主机为`us.aws.cdn.hf.co`。此观察证明存在可用的请求路径，不代表已取得完整资源。

## 独立本机R2

只获取`OpenGVLab/VBench_Used_Models`的revision`83290ee59b4e2c0a4d198857edbc79dd186b8d44`，文件`ViClip-InternVid-10M-FLT.pth`：

- 固定大小1710545812字节。
- 固定SHA256：`7a4d6ad6eac6632db3693f4b97f9f8f6445b65b1e139a6fc6686150522238c56`。
- worker仍为已验证的原资源获取代码，SHA`d8602f2174d46035e838ba38101671b79c20ab9d04e7cc70fd3be7fb0de13ac4`，Git源`5d7ef36ab58579ee6e8100d3d822e2c5426cffb7`。
- 独立本机stage：`.sync/wc-N10-viclip-local-proxy-r2-20261016`。
- 原本机PID18318，lstart`Fri Oct 16 13:28:28 2026`；13:28:28.373032单次派发。
- 注册SHA：`5e9174c2f49839ac11621021fa8070653985e52a70c00c757df128f5166df67c`。
- 预估15—30分钟；最早13:58:28.373032，**安排14:00一次查收**。

复用当前代理，不改全局网络设置。下载显式空CUDA可见集、低优先级、标准库流式写part并全SHA/大小一致才rename；失败part保留。启动前本机可用13.4564GB，满足三倍权重大小的空间检查。未修改N07原源、句柄、预算或服务器资源目录。

新的本地查收入口在原ETA前直接拒绝，不查询进程/文件；该边界已实测。到时只读原Mac PID/lstart/command、注册/worker、result/part，并在终态后独立读取完整target SHA。local accepted不代表服务器接收或模型CPU通过。

## 后续接线

本机原件完整接受后，通过既有SSH传往fresh服务器资源目录，先part、独立完整SHA后rename；保留本机原件和原R1失败。若传输本身较长，单次派发后另约ETA查收，不重复上传或持续监听。

[505五模型CPU链](505_WC_N10_COMPLETE_FIVE_MODEL_CPU_BATCH_STAGING_AND_INDEPENDENT_ACCEPTANCE_READY_20261016.md)已完成完整五角色bundle、固定源码/资源部署与原件独立验收，15项合成控制通过；真实模型CPU尚未执行。部署器见登记GPU活动即defer，优先[506的N07生成](506_WC_N07_FULL180_HUMAN_APPROVED_CAP113_GPU_ADMITTED_AND_0530_COLLECTION_20261016.md)和其后N08 clean测速。取得权重不代替五模型运行，也不代替最终160视频/960指标位置评价。

## 原件

- [原服务器终态资源回执](../reports/wc_paper_N10_ViCLIP_resource_R1_collection_20261016_1317.json)。
- [本机同URL HEAD](../reports/wc_paper_N10_local_ViCLIP_HEAD_route_probe_20261016.json)。
- [本机R2单次启动](../reports/wc_paper_N10_ViCLIP_local_proxy_R2_launch_20261016.json)。
- [ETA前拒绝控制](../reports/wc_paper_N10_local_proxy_R2_collector_preETA_boundary_20261016.json)。
- [本机原句柄一次查收工具](../scripts/capture_wc_N10_viclip_local_proxy_r2.py)。
