# N10固定权重R3终态与传输诊断

2026-10-16 15:50按原时点一次查收。**原R3已退出，14/204个范围完成后在第15段耗尽六次已登记请求尝试，完整资源未接受。** 这是后续自动质量评分的资源缺口；不改变N07主线或方法结论。

## 原任务与原件

原Mac PID19489／source`129577b94a5a91b38cf2b67baaa53de5a7963116`、stage`.sync/wc-N10-viclip-local-ranges-r3-20261016`的进程已不存在，原结果exit1。实际运行184.146546秒，22次HTTP尝试、8次失败，已提交117,440,512字节（112MiB）。

完整目标1710545812字节未形成，`local_resource_bytes_independently_accepted=false`。原partial SHA为`19bba4e2711199561cd59f93b3a65e85a087363cc79f1070dba890706d45a32f`；partial、逐段请求、错误与原注册均保留，不作为可加载权重。原R1/R2失败也保持，没有接续SCP或运行评分模型。

随后仅离线独立核对14份已接受范围的206／Content-Range／ETag／大小／body SHA、顺序与原partial逐字节一致，实际117440512字节及prefix SHA一致，原文件未改。它可作为后续独立恢复的前缀证据，仍不是完整权重。

最后请求范围`117440512–125829119`，curl退出35：`LibreSSL SSL_connect: SSL_ERROR_SYSCALL`，零字节。末次记录里的HTTP200来自代理CONNECT头，不是目标文件206响应；原worker因此正确拒绝，没有把它当完整下载。

原15:50资源自动化`p-acr-cpu`已暂停，避免重查已结束句柄；未修改负责N07半程／最终验收的`worldcache-26d`。

## 小范围区分测试

使用同一原文件、原revision与失败偏移，仅请求1MiB，不尝试另一模型：

|探测|真实观察|
|---|---|
| bundled Python3.12／OpenSSL3.5.8，经既有本机代理 | TLS `UNEXPECTED_EOF_WHILE_READING`，约5秒 |
| 同一OpenSSL，官方域名直连 | 同样TLS EOF，约5秒 |
| 同一固定repo／revision路径的镜像直连 | 同样TLS EOF，约5秒，未取得任何可接受镜像字节 |
| 原curl限定TLS1.2／HTTP1.1，经原代理 | curl35，约5秒，零字节 |

这些观察不支持“仅换成新TLS库即可修复”的解释，仍不能唯一定位代理节点、上游或本机连接环境。没有改变共享代理配置，也没有反复重新派发整份资源任务。后续须出现可用的小范围传输证据后，再选择独立修复版本和一次查收时点；完整原大小／SHA仍是资源验收依据。

## 主线与费用

本次0SSH、0GPU、0模型、0新质量分数、0服务器／账本写。N07原source`140d0a6`与完整180保持，今天21:30一次半程技术检查、明早05:30完整验收。N07→N08→N09/10、cap113和原origin保持；本次资源缺失不阻塞已授权的主线共同测试与重复测速。

原件：[15:50唯一查收](../reports/wc_paper_N10_ViCLIP_local_ranges_R3_collection_20261016_1550.json)、[原14段独立前缀审计](../reports/wc_paper_N10_R3_original_prefix_independent_audit_20261016.json)、[OpenSSL原代理](../reports/wc_paper_N10_OpenSSL_failed_offset_probe_20261016.json)、[官方直连](../reports/wc_paper_N10_transport_official_direct_probe_20261016.json)、[镜像直连](../reports/wc_paper_N10_transport_mirror_direct_probe_20261016.json)、[TLS1.2／HTTP1.1](../reports/wc_paper_N10_tls12_http11_transport_probe_20261016.json)。
