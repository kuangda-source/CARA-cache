# N10固定ViCLIP完整权重已独立接受，资源自动化收尾

2026-10-17。**此前缺失的本地ViCLIP完整权重已经补齐。** 在原01:54约定时点只查收一次，完整1710545812字节及独立全文件SHA均与固定官方revision一致。这解除自动质量评价的一项资源阻碍；服务器接入、五模型实际CPU和正式评分仍待后续主线执行。

## 已核实的结果

| 核对项 | 实际结果 |
|---|---|
| 固定对象 | `OpenGVLab/VBench_Used_Models` revision `83290ee59b4e2c0a4d198857edbc79dd186b8d44` 的 `ViClip-InternVid-10M-FLT.pth` |
| 完整大小 | **1710545812字节**，约1.71GB |
| 全文件独立SHA-256 | `7a4d6ad6eac6632db3693f4b97f9f8f6445b65b1e139a6fc6686150522238c56` |
| 范围完整性 | **204／204段**，204次HTTP尝试，失败0 |
| 实际获取耗时 | **2596.803543秒，约43分17秒** |
| worker完成时间 | `2026-10-17T01:06:35.253012+08:00`，北京时间 |
| 原约定查收 | `2026-10-17T01:54:50.864235+08:00`，北京时间，原进程已终态 |
| 接受范围 | 本机完整权重字节；服务器资源与模型运行仍未接受 |

原source `8fd3a3ab15ecb0d7efa7bef60ec2090fd1b082f9`、PID40655／原lstart与stage身份由原启动和初次核验绑定；最终collector核对registration与两worker源码SHA，独立读取完整目标文件计算SHA。验收采用完整文件，不以writer的prefix摘要或退出码单独替代。

[原启动](../reports/wc_paper_N10_ViCLIP_direct_R4_launch_20261017.json) → [半程技术快照](../reports/wc_paper_N10_direct_R4_midpoint_health_20261017.json) → [一次最终查收](../reports/wc_paper_N10_direct_R4_collection_20261017_0154.json) → [独立资源接受](../reports/wc_paper_N10_direct_R4_independent_resource_acceptance_20261017.json)。

完整本机文件仍保存在`.sync/wc-N10-viclip-direct-r4-20261017/ViClip-InternVid-10M-FLT.pth`，不提交Git。旧R1／R2／R3全部失败记录及112MiB前缀保持；本次R4独立获取整份，不拼接旧partial，不改变系统代理或TLS校验。

## 对后续主线的影响

| 工作 | 截至本轮的状态 |
|---|---|
| 本机完整固定ViCLIP字节 | **已独立接受** |
| SSH／SCP接入服务器及服务器独立SHA | 待后续主线接续；本轮未执行 |
| 原完整五模型实际CPU构造与接口验收 | 待资源接入并避开N07 GPU／N08 clean计时执行 |
| 冻结N07全体正式输出的自动质量评分 | 待N07完整接受及五模型前置条件，仍为0新分数 |

已准备的原资源relay和五模型完整CPU入口可继续复用；不改成四模型子集。正式质量实验仍保留N07全输入、拒绝失败缺失和完整注册分母，结果栏留空。资源下载成功不改变已冻结方法、超参数或论文终点结论。

## 自动化与任务边界

`p-acr-cpu`已经**暂停**，本资源任务收尾完成，不再次检查原PID、重启或自动R5。[实际设置回执](../reports/wc_paper_N10_direct_R4_terminal_automation_pause_20261017.json)同时核对两项N07自动化保持ACTIVE：原失败R1仍05:30验收，新完整修复R2仍09:24半程／17:24完整验收。本轮不读取N07科学partial或查询它的服务器进度。

本轮0新GPU、0SSH／SCP、0模型加载、0新质量分数、0服务器账本写。cap113与原origin保持，v2费用及预留沿用N07原准入快照，没有把资源验收当新的预算查收。F/B保持关闭；后续仅沿既定N07→N08→N09／N10主线接续。
