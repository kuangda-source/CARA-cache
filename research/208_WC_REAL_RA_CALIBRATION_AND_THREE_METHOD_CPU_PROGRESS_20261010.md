# 真实 RA 校准与三方法完整对照入口（2026-10-10）

真实 Cosmos RA 校准已唯一提交并正常推进；下一轮原 WorldCache、共同刷新、校准 RA 的完整对照入口已实现，完整生产循环 CPU 验证通过。当前工作正从接口与校准进入方法输出，随后接入 guided 目标 W1 与协调部分刷新。

## 真实校准已执行

生产资产 CPU `3767622/3767623` 用时824.593157413秒，绑定选定 CPU `3790000/3790006` 用时171.778118941秒，均退出0且原句柄消失；193载荷、真实固定运行源／资产／两请求及19范围拒绝全部验证，CPU无GPU提交或账本写入。[生产验证](../reports/wc_ra_calibration_production_cpu_r1_terminal_20261010_capture.json)和[选定验证](../reports/wc_ra_calibration_selected_cpu_r1_terminal_20261010_capture.json)均保留native原字节。

`WC-RA-COARSE-CAL-R1-20261010-A`／`wc-ra-coarse-cal-r1` 已按[完整登记](../manifests/wc_ra_calibration_r1_preregistration_20261010.json)和预测3.552744294GPUh自主派发一次：[启动回执](../reports/wc_ra_calibration_r1_GPU_launch_20261010.json)。冻结source `abdef6e533b7ee36fcfb1a9b4f530c3ec562c902`，193载荷；原GPU监督3801976、runner3802258、后CPU监督3801977继续跟踪，不复投或改源。完整范围4父／4全93视频／6同状态起点／12完整子／312solver／624net，未缩分母。

现场1791573064.093168时原三句柄均活：Common的OFF/ON完整36步和全部13／23／33起点的六子臂完成；Human OFF完整36步完成、ON开始。runner顶层仍为INITIALIZING，实际子路径已在计算，不能仅凭顶层字符串判定没有启动。全批与GPU后CPU重读尚未结束，真实表尚未验收。

启动前已结算30.52959376334963／累计77.89524658965853GPUh，窗口剩余47.365652826308896；提交67→68。服务器将该余额在途预留，账本used字段暂等于累计上限，其状态明确是`CFG_TEACHER_INFLIGHT_REMAINING_RESERVED_NOT_ACTUAL_SPENT`，不是已花完。退出按实际加载／运行／失败／写盘／清理wall结算；本地结算快照保持启动前值，不能拿预留计作实费。

## 三方法完整对照入口与 CPU 结果

source `1cceba2042550638340a0ceb1cf55482c483a8ed`、172载荷，独立[CPU登记](../manifests/wc_ra_baseline_sampling_cpu_r1_preregistration_20261010.json)和[启动](../reports/wc_ra_baseline_sampling_cpu_r1_launch_20261010.json)。原3827360／3827361退出0且消失；实际驱动975.891748476秒、核心63.346962478秒。

| 方法 | 实际决策 |
|---|---|
| WC | 原生逐分支策略，保持其全部合法动作 |
| JOINT_NATIVE | 两支当前实际paid probe只要一支要求完整计算，就双支DD；两支都允许缓存才CC |
| RA | 先支付当前两支浅层，再用校准相关性与传播gain选择共同CC/DD，沿自身轨迹运行 |

首个RA阈值规则预先固定为：采集父共同D6轨迹中，每场景四个完整六步区间累计paid联合风险，共八个观测区间取中位数。使用实际已审计校准表与paid特征；CPU仅用实际Toy校准原件，真实部署必须换成此批真实Cosmos表。阈值不根据候选终点质量挑选，也不宣称自动匹配实际耗时或完整调用数；后续必要的有限工作点调整以实测成本为依据。

- 两flow × 成功／最后RA向量写出失败：完整24执行路径、864solver／1728net；成功场景12路径。
- 实际重读432guided／12latent；三方法前七步DD张量直接相同；同输入／条件／RNG、paid-before-deep、实际深层访问、全部36步策略历史与五状态检查点验证。
- 12语义破坏拒绝、2最后方法真实文件截断拒绝、2最后写出失败控制保留；22Toy向量原件现场大小／SHA绑定。
- 原本地复核错误为对最后写出失败行读取尚未产生的success-only `all_modules_eval` 字段。原错误证明与native数据全保留；[独立修复复核](../reports/wc_ra_baseline_sampling_cpu_r1_terminal_20261010_retained_independent_audit.json)仅区别成功行和已验证完整失败行，仍核对失败行的36更新／动作／历史、全状态恢复和原错误。没有重跑CPU／GPU、改变生产源或接受子集。

## 下一步

1. 原真实校准完整结束后，GPU释放，再重读16向量原件、144父guided／4父latent／48子张量、四视频全93帧及OFF/ON一致性，重建来源绑定表；独立捕获21文件路径／大小／SHA和费用结算。
2. 由完整真实表与父D6 paid历史初始化首个RA阈值，冻结同输入的WC／共同刷新／RA六完整路径与匹配原生参考评价卡；按完整成本预测、实际源资产CPU和现场资源准入执行，完整≤4GPUh自主，>4具体确认。
3. 进入guided目标W1、协调稀疏／部分MLP与来源感知组合，尽早生成组合候选完整视频，不要求各模块先独立稳定胜出，不把长期Q标签或预测器训练作为开始方法开发的门槛。

原正负结果、旧判据、全部失败与旧16路径／6.704055834卡保持；旧卡仍超过4GPUh且未获具体批准。以上CPU与校准不是新策略质量／速度结果；当前只新增必要自动检查，不引入非必要人工评审。goal active，正常推进。

组会飞书已通过CLI追加并完整回读revision39：174个原块保留，新增正文／样式／链接全相符，[回读证明](../reports/wc_ra_real_run_and_baseline_cpu_feishu_verification_20261010.json)。汇报包括真实校准执行、三方法完整CPU与修复边界、首阈值规则、在途预留和下一步组合开发。
