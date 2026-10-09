# 首个 RA 完整视频工作点：八路径生产卡（2026-10-10）

已将[209真实校准与完整CPU结果](209_WC_REAL_RA_CALIBRATION_RESULTS_AND_MATCHED_REFERENCE_NEXT_20261010.md)落实为完整生产卡`WC-RA-FULL-VIDEO-COMPARISON-R1-20261010-A`／`wc-ra-full-video-comparison-r1`。本卡回答：本地真实相关性与传播先验驱动的共同刷新，能否在自身轨迹上改善终点保真和计算分配；同时比较简单共同刷新与原WC，随后接入guided-W1和协调部分刷新。

## 方法、对照和范围

Common/Human seed3各执行原WC、JOINT_NATIVE和RA三方法，合计六全36步候选；再执行相同请求的两个普通Native参考槽。整卡8路径、288求解器更新／576模型调用，最多8全93帧视频、288实际guided输出／8终点latent。参考拒绝保留在分母，不补选其他seed或把缺失指标填零。

RA使用六个实际校准观测重建的表，指纹`9ab1d77c303560823ed2f32f43b2982318cdd9835828a46da4835a1b95ea7d7a`；阈值`0.141488470197544`来自事前固定的八个完整D6区间paid联合风险中位数。生产CPU必须实际加载非Toy表并运行原阈值函数，与独立重建核对。各方法只付当前浅层probe，不在候选中运行teacher。

六方法执行器和两Native组合来源于已验收的source `b901432`完整32路径CPU，源逐字保持。真实Native引用固定类forward、关闭pipe与net缓存，每次执行全部深层；准备输入、第一步noise／latent／time和CFG条件与候选配对，前七步DD控制需直接相同。该卡是独立三方法比较，未接受或修改旧16路径／6.704 GPUh卡。

## 完整成本与执行规则

[完整费用预测](../reports/wc_ra_comparison_r1_complete_cost_forecast_20261010.json)绑定当前真实校准OFF父用时与此前完整父记录，采用925.025799秒／路径、620.284490秒慢加载、900秒状态恢复及新方法记录余量、480秒整卡向量写出和120秒清理，再乘1.2整卡余量：**3.173496962 GPUh**。两Native成本计入八条路径，没有删对照、切分整卡或按算法部分计费。此为来源绑定的经验预测，不是时间上界或旧秒数截止。

当前单次完整≤4 GPUh自主，>4具体确认；新卡预测在自主范围内。预算以已用29.895246590为新增48窗口起点，累计上限77.895246590保持；当前结算31.418288992、剩余46.476957598 GPUh、68次提交，无GPU在途。预计超出单次授权时按原规则保存部分结果和费用并安全停止自有任务，提出具体继续方案。

## 生产实现与验证状态

新生产合同、运行器、锁与计费监督、GPU后CPU全向量／视频审计、原件捕获以及选定／部署入口均已实现；[生产配置](../configs/wc_ra_comparison_production_r1_20261010.json)和[完整登记](../manifests/wc_ra_comparison_r1_preregistration_20261010.json)冻结226载荷。本地语法、整卡合同、全部载荷SHA核对通过。source `19d76e79d69b49db7dc16a15902494ea1685770e`已提交并推送，226载荷同步到独立`.sync/wc-ra-comparison-production-cpu-r1-20261010`。原生产CPU监督3866274／child3866275已退出0且消失，35.243509秒通过；实际非Toy表／八区间阈值函数、Native类入口及19范围拒绝通过，[完整CPU原件核验](../reports/wc_ra_comparison_production_cpu_r1_terminal_20261010_capture.json)保留。本地选定器将包内合同作为独立模块导入导致ImportError；改用独立[包导入选定入口](../scripts/select_wc_ra_comparison_r1_package.py)后完整选定成功，[原错误与修复记录](../reports/wc_ra_comparison_local_selection_import_repair_20261010.json)保留。生产226载荷和已通过CPU原件逐字不变。选定CPU和fresh GPU／锁／磁盘／预算准入仍待，尚未新GPU提交。

生产CPU检查19种改变范围／请求的拒绝、实际Native类forward源位置和非Toy表／八区间阈值函数。实际GPU完成后重读全部接受路径的36个FP32guided与latent、五处1216状态及完整93帧视频，核对实际动作／paid-before-deep访问、输入噪声／条件和文件来源。终点指标随后统一CPU全帧LPIPS，保留逐场景和全部帧正负分布，原有MUSIQ／VQA结果保持。

本卡保留必要诊断，pipeline wall用于实际成本和工作点分析，干净部署速度需后续轻量计时；首阈值不保证相同调用数或时间。首工作点正负均保留，必要时先检查目标和指标是否对齐，再登记有限的低成本区分修订，不用单项阈值否定RA或整个方向。未增加人工评审，goal active。

组会已通过飞书CLI追加真实校准与八路径CPU进展并完整回读revision40：175原块全部保留，新正文／样式／链接相符，[核验证明](../reports/wc_ra_calibration_complete_and_reference_cpu_feishu_verification_20261010.json)。
