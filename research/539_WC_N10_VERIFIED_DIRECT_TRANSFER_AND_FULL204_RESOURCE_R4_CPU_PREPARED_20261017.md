# N10固定权重：直连数据路径已验证，完整R4准备完成

2026-10-17。**此前失败偏移上的直连1 MiB已经通过HTTP206、精确范围、原ETag与实际文件大小检查。** 已据此准备同一固定版本的独立完整资源任务，35项本地CPU检查和三个冷CLI通过。当前只是资源获取准备，尚未取得完整权重或新的质量分数。

## 新的实际传输证据

原R3在14/204段、117440512字节处因TLS失败终止，[517](517_WC_N10_RESOURCE_R3_TERMINAL_TLS_FAILURE_AND_SCOPED_TRANSPORT_DIAGNOSIS_20261016.md)及旧partial保持。

00:00的一轮四个有界HEAD请求确认：官方根地址、固定权重地址经原代理可达，固定权重直连也可达，TLS证书校验保持。随后原代理在失败偏移的1 MiB GET仍于6秒连接超时；HEAD可达不能据此认为完整数据路径已经正常。

00:04按原15秒连接时限做两项区分：直连`117440512–118489087`在6.085秒收到完整1048576字节，HTTP206、`Content-Range: bytes 117440512-118489087/1710545812`及原ETag全部匹配，body SHA为`9d0004c062deb9a56d77a2b32ee0d24bf4b7e69f17c9d1a5ead774e9cd7261db`。另一个代理首字节对照在302重定向正文阶段触发1字节大小限制，未到实际对象传输，不能据它判断代理数据路径是否可用。

这些观察支持采用已实测成功的直连请求，不唯一解释先前TLS失败原因，也不保证随后204段全部成功。

## 完整R4与原件边界

独立目录拟为`.sync/wc-N10-viclip-direct-r4-20261017`。仍获取官方repo `OpenGVLab/VBench_Used_Models`的固定revision `83290ee59b4e2c0a4d198857edbc79dd186b8d44`，完整1710545812字节、204个8 MiB范围、每段最多六次原已登记尝试，最终SHA仍为`7a4d6ad6eac6632db3693f4b97f9f8f6445b65b1e139a6fc6686150522238c56`。

旧112 MiB前缀与全部失败、请求和注册原件保留。本轮在新目录从头获取同一完整文件，旧partial不进入模型加载，也不覆盖旧任务。

[新执行器](../scripts/fetch_wc_N10_viclip_direct_r2.py)从原range worker精确派生，仅修改两处curl传输选项：显式忽略用户curl配置，使用请求私有直连／禁用环境代理，并设90秒单请求上限。TLS证书校验、原URL、完整范围、ETag、大小、六次尝试、顺序写入和整文件SHA全部保持，逆变换／AST相等控制通过。全大小／SHA验收后才发布`.pth`目标。

[单次启动入口](../scripts/launch_wc_N10_viclip_direct_r2.py)要求原R3终态、真实直连probe与原body哈希、Git已提交源码和全文件磁盘余量，创建新目录一次派发；[原查收工具](../scripts/capture_wc_N10_viclip_local_proxy_r2.py)显式识别新执行器，同时核对它和原range helper两个源码SHA。不得因观察超时重派。

## CPU验证与执行顺序

35项CPU包含原完整字节／错误范围／短响应／错误ETag／整SHA失败控制，新增直连参数、精确派生、变更源码拒绝、真实非零probe门与新查收身份控制，以及原本地查收／服务器接入控制。传输、进程和字节对象为明确替身，不是完整1.71GB下载。三个CLI冷启动均退出0。

源码同步后可按现有资源准备授权启动一次完整R4；预计60–90分钟，实际启动后45分钟技术检查、90分钟完整验收，时点从真实回执计算。半程只核原PID/lstart/command、注册和技术进度；最终才独立核全文件字节／SHA。未完按剩余量重新估时另约一次，不持续轮询。

完整资源实际接受后才进入原SSH传输及服务器独立SHA验收，然后是五模型完整CPU探针和正式评分准备。五模型资源前置条件保持，不缩成四模型评分。重模型CPU继续避开主线GPU与clean测速。

本准备轮0SSH、0新GPU、0模型、0新质量分数及0账本写。N07完整修复卡仍待原具体确认；累计113 GPUh、原预算窗口与严格少于12 GPUh自主规则保持，原N07的10月17日05:30验收单独保留。F/B关闭。

证据：[四HEAD](../reports/wc_paper_N10_bounded_HEAD_transport_diagnosis_20261017_000030.json)、[原代理偏移失败](../reports/wc_paper_N10_failed_offset_one_MiB_probe_20261017_000204.json)、[直连实际非零数据与对照](../reports/wc_paper_N10_paired_GET_transport_diagnosis_20261017_000406.json)、[35项CPU](../reports/wc_paper_N10_direct_resource_R4_CPU_preparation_20261017.json)、[三个冷CLI](../reports/wc_paper_N10_direct_resource_cold_CLI_20261017.json)。
