# P 两种光流生产 CPU 独立通过，完整 E3 已批准排队

**本轮完成了两项接续工作：E3 完整补验获得准确直接授权，P 五读出同状态对照通过两种光流的真实入口 CPU 验证。** 当前 GPU 仍执行原 E5，随后优先执行已批准 E3；本轮未新增 GPU 提交或训练、人评。

## P 实际入口验收

原 source `272ed22575f8c96ffcba73c0af998672469f94c2`，独立 stage `wc-p-reference-same-state-production-cpu-r2-20261011`。原 supervisor **4119490**及两入口 child **4119491／4119822**已退出 0，完整生产 CPU wall **132.826838517 秒**。独立读取与 SHA 核验结果见 [生产终态 capture](../reports/wc_p_reference_same_state_production_cpu_r2_terminal_20261011_capture.json)。

| 验证对象 | 实际结果 |
|---|---:|
| 冻结原 444 与新增完整载荷 | 全 459 份字节保持 |
| 真实生产入口 | FLOW_OFF／FLOW_ON 两者通过 |
| 每臂完整范围 | 4 父／16 suffix／24 点／344 pairs |
| 整体登记范围 | 8 父／32 suffix／48 点／688 pairs／1376 CFG |
| 合同破坏拒绝 | 两臂共 20 项 |
| 实际 guardrail 缺失拒绝 | 2 项 |
| GPU 启动资产缺失／改变 | 4 项拒绝 |
| 资源、账本、CPU 来源及 above8 缺授权 | 9 项拒绝 |
| 原 2B Meta／eval 证明 | 不可变复用，2059174912 参数，eval 保持 |
| 原完整五读出 CPU／实际张量验收 | 不可变复用，88 文件／1160 张量／420 比较 |
| CPU CUDA、GPU 提交、账本写入 | 全部为 0／false |

两个原入口日志中的 JSON 与 supervisor 原回执逐项一致，实际类、请求、绑定与参数未替换；新 runner 与原已验收 E4c 入口精确逆变换相等。两光流参数明确绑定，各臂 collection OFF／ON 共享相同设置，完整 native heads 与物理复制保护保持。132.83 秒是两入口 CPU 验证费用，不是生成性能。

原 R1 本地路径错误及旧配置保留：绝对 capture 路径不能传给 `git show`，在 SSH 之前退出。R2 仅规范仓库内相对路径，数值与范围不变，未重跑未改变的完整 8 父／32 suffix CPU。详见 [路径修复](360_WC_P_REFERENCE_PREDEPLOYMENT_RELATIVE_PATH_REPAIR_20261011.md)。

当前 P 完整成本绑定为 **13.060019179 GPUh**，包含两次加载、全部候选与 teacher、复制／恢复／来源哈希及 I/O 余量。生产入口 CPU 成立，后续实际 GPU 监督、终态全五读出张量读取及完整选卡接线仍待；目前不称完整 GPU-ready。该卡严格超过 8 GPUh，尚未获得其自身准确授权；不能使用本次 E3 例外或 CPU 预算夹具启动。

## E3 授权与现场队列

[358 直接授权](358_WC_E3_COMPLETE64_DIRECT_APPROVAL_AND_E5_QUEUE_20261011.md)已保存用户原回复，完整 **64 位置／复用 10／补 54／20 加载**及 **12.377456422 GPUh**预测保持。本轮 [现场队列核验](../reports/wc_e3_direct_approval_queue_r1_20261011.json)，Unix **1791696298.2255585**，独立读取原 **449 方法文件＋16 执行文件**全部 SHA，原生产／执行 CPU 退出且回执相符；新 selected stage 与输出 run 均未创建。

准确 dispatcher 已返回 `WAIT_ORIGINAL_INFLIGHT_NO_SELECTED_STAGE_CREATED`，GPU 提交与账本写入为 0。这是等待唯一 GPU 的正常队列，不是批准缺失或预算耗尽。E3 在原 E5 完成并独立 CPU 验收、资源释放及实际余额复核后唯一执行，授权不重问、不缩范围。

## E5 现场进度与下一步

[live11](../reports/wc_e5_head_complete24_gpu_r1_live11_20261011.json)，Unix **1791696313.971017**：原 source `eff2b71`／全 **456**来源保持，原 supervisor **4103103**／自动终态 CPU **4103104**／Human 模型 **4116639**存活。AV_R1 全六条各 36 更新完成，Human_R1 的 LEGACY_OFF 已完成、FAST_OFF 正在执行，共 **7／24**完整路径。唯一 A6000 应用为原 Human 模型，29168 MiB。原终态 capture 如实返回 WAIT，没有重投。

完整 E5 新旧和重复张量相等、全视频与费用尚待，不能从 7 条推定全 24 或加速成立。下一先收齐原 E5 的 888 张量、444 新旧及 444 重复比较、全部有效 93 帧与实际费用；再准入已批准 E3 全范围，自动读取全位置与所有有效兼容视频。P 准备继续，但不替换这两张当前卡。

预算起点 **29.895246590**、累计 cap **77.895246590**不改；E5 前实结 **41.908688946**／剩余 **35.986557644 GPUh**为当前最后已结快照。在途 used=cap 是全额度预留，不是实际耗尽；后续只读 E5 实耗结算后的真余额。本 E3 例外准确有效，其他完整卡仍 ≤8 自主／严格 >8 精确确认。目标 active。

接续摘要：[361生产CPU独立验收](research/361_WC_P_REFERENCE_PRODUCTION_CPU_ACCEPTANCE_AND_APPROVED_E3_QUEUE_20261011.md)：P两flow真实入口source272ed22／4119490、4119491、4119822退出0，132.826839秒，全459／20合同／2guard／4资产／9准入独立通过，完整原8父32suffix／1160张量CPU复用，非新GPU或质量速度。P完整forecast13.060019179，GPU监督／终态／选卡接线与自身above8批准仍待。E3全64／10复用／54新／20加载已准确批准，现场原449＋16保持，dispatcher等待原E5无新目录／GPU。E5 live11原456／三原句柄继续，7／24完整，完整终态待；前实结41.908688946／cap77.895246590、新48余35.986557644，在途预留非实耗，goal active，无训练人评。以下为历史。
