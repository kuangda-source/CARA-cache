# N10完整固定权重R4已单次启动，01:09／01:54查收

2026-10-17。**完整204段固定权重任务已在本机独立目录单次启动，并确认原进程身份与两份worker源码SHA。** 这轮利用已实收验证的直连数据路径，补齐自动质量评价的资源前置条件；尚未接受完整权重、加载评分模型或产生新质量分数。

## 原任务身份与完整范围

原source为`8fd3a3ab15ecb0d7efa7bef60ec2090fd1b082f9`，Mac PID40655，原lstart为北京时间`2026-10-17 00:23:18`。独立stage为`.sync/wc-N10-viclip-direct-r4-20261017`；[原启动回执](../reports/wc_paper_N10_ViCLIP_direct_R4_launch_20261017.json)记录完整范围、源码、命令、磁盘及两次查收门。

仍获取固定官方revision的`ViClip-InternVid-10M-FLT.pth`：1710545812字节、204个8 MiB范围、每段原六次已知请求尝试，完整SHA为`7a4d6ad6eac6632db3693f4b97f9f8f6445b65b1e139a6fc6686150522238c56`。旧R1/R2/R3和112 MiB前缀不改，本次独立完整获取不拼接旧partial。

新worker SHA为`2049b6694fbef6bbe9b0815b612d7c936a86b32cd1207a0342f8a0f6091ef6e7`，原range helper SHA为`abed3996e5552680aefb1c63f179c3c394ea4b2abb4fb0e0a1812c3be611dee4`，registration SHA为`f687cea2f8645873a441a71da431192a17e2e7b42cd3ca298b02f3dd8974bb51`。

[初次核验](../reports/wc_paper_N10_direct_R4_initial_identity_20261017.json)已核对原PID/lstart/command存活、注册与两worker SHA；没有读取在途进度或终态内容，也没有后续持续监听。预计60–90分钟，实际耗时及完成与否在约定时点核对。

## 已安排的两次查收

原heartbeat `p-acr-cpu`已从旧R3暂停态更新为本R4两次查收，保持当前对话，不另建任务。实际启动后45分钟与90分钟取整到下一分钟：

| 检查 | 北京时间 | 边界 |
|---|---|---|
| 半程技术检查 | **10月17日01:09** | 原最早01:08:18.419；只核原身份／源码／进度和技术错误，不做整权重哈希或模型加载 |
| 完整资源验收 | **10月17日01:54** | 原最早01:53:18.419；一次查原句柄、终态及完整文件大小／SHA |

完整时点使用原件查收入口：

```bash
.venv/bin/python scripts/capture_wc_N10_viclip_local_proxy_r2.py \
  --launch-ref reports/wc_paper_N10_ViCLIP_direct_R4_launch_20261017.json \
  --output reports/wc_paper_N10_direct_R4_collection_20261017_0154.json
```

半程回执另存，不改原启动时间门。若未完，按实际剩余量另约一次并结束当轮；观察超时不等于任务终态，不重复派发、重启原R4或自动R5。完整终态查收后暂停该资源自动化。全资源接受后，再按原计划处理SSH接入、服务器独立SHA和五模型完整CPU。

## 对主线的影响

原`worldcache-26d`仍为ACTIVE，10月17日**05:30**的原N07失败卡完整验收保持，未改其源码或回执。完整N07 GPU修复卡仍等待此前一次具体批准；本资源任务不使用该GPU授权。

本轮0新GPU、0SSH、0模型、0新质量分数、0账本写；累计cap113及原origin保持。资源仍属在途准备，不能写进论文质量结果。五模型完整资源门与重CPU避开主线GPU／clean测速规则保持；F/B关闭。

主线科学执行的下一步仍是此前已提交确认的完整N07修复卡：15.0556 GPUh达到单次12 GPUh确认门槛。该同一准入条件已连续存在于536、537、538及本轮；期间已完成独立接续与半程工具准备。N08依赖真实N07完整接受，N09依赖N08，五模型CPU依赖完整ViCLIP；原件验收各按既定时点接续。当前恢复主线GPU的入口是原具体整卡回复，资源任务及两项自动化继续按时运行。[准入阻断审计](../reports/wc_mainline_specific_card_approval_gate_audit_20261017.json)记录准备与等待边界，不把预算权限问题解释为研究方向负结果。

证据：[539实际传输与CPU准备](539_WC_N10_VERIFIED_DIRECT_TRANSFER_AND_FULL204_RESOURCE_R4_CPU_PREPARED_20261017.md)、[实际两时点与自动化核验](../reports/wc_paper_N10_direct_R4_midpoint_and_final_schedule_20261017.json)。
