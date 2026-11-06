# 固定ViCLIP资源：原204范围R3已派发，15:50一次查收

2026-10-16。**已按510通过的分段方案派发一个新的本机资源任务。** 它获取与前两次完全相同的固定权重，不占GPU、不加载模型；N07原完整180及明早05:30验收保持。

|原任务项|实际值|
|---|---|
|本机stage|`.sync/wc-N10-viclip-local-ranges-r3-20261016`|
|source|`129577b94a5a91b38cf2b67baaa53de5a7963116`|
|原Mac PID/lstart|19489 / `Fri Oct 16 14:15:26 2026`|
|实际单次启动|2026-10-16 14:15:26.652263，北京时间|
|分段|204个范围，常规8MiB，末段保留精确余数|
|worker SHA|`abed3996e5552680aefb1c63f179c3c394ea4b2abb4fb0e0a1812c3be611dee4`|
|registration SHA|`95bd9af74f860ae413b886c84de2bbb114fedd2bee05815d93925ff80df45c32`|
|预计|60—90分钟|
|原最早查收|2026-10-16 15:45:26.652263，北京时间|
|安排一次查收|**2026-10-16 15:50，北京时间**|

启动前已确认原R1/R2终态、旧78,094,879字节partial的完整SHA保持、两个实际HTTP206范围/对象相同、13项CPU通过、执行源码已提交，以及本机13.7317GB可用空间。原R2没有重派，旧partial不被本任务拼接或覆盖。

仍固定HF revision`83290ee59b4e2c0a4d198857edbc79dd186b8d44`的`ViClip-InternVid-10M-FLT.pth`，1710545812字节、全SHA`7a4d6ad6eac6632db3693f4b97f9f8f6445b65b1e139a6fc6686150522238c56`。每个HTTP请求明确结束后可按原六尝试规则重取同一段；失败请求原件保持，不将连接未知当成另一次任务启动理由。

到ETA后只查原Mac PID/启动时间/worker和注册，读取原result或段进度；任务仍活跃则按剩余字节、失败尝试及实际耗时重估，另约一次后结束。完整资源只有原result退出0、全大小/SHA和collector独立读取全target一致才接受。204段不是204次模型或视频实验。

完整本机资源接受后，可用508已准备的原SCP入口传往独立服务器目录，并在该传输的ETA后收原件。模型CPU和960位置质量评分仍待真实主线空档、完整模型/资源验证与费用；资源取得不充作质量结果。

本次未查询N07、写服务器或账本；cap113、原origin和已结费用不变，N07预留仍按原监督终态结算。重模型CPU避开N07/N08，F/B关闭、无训练/OMR/人评。

原件：[R3单次启动回执](../reports/wc_paper_N10_ViCLIP_local_ranges_R3_launch_20261016.json)、[510失败与修复](510_WC_N10_LOCAL_TRUNCATION_RETAINED_EXACT_HTTP_RANGES_CPU_REPAIR_20261016.md)、[508服务器接入](508_WC_N10_ORIGINAL_SCP_PINNED_RESOURCE_RELAY_CPU_READY_NO_GPU_INTERFERENCE_20261016.md)。
