# RA 八路径对照的统一全93帧评分准备（2026-10-10）

## 当前实际派发与方法进展

新独立评分source `c40c0b8ac757f284d409fc11933a016281842b00`、10载荷已唯一CPU派发，见[原启动回执](../reports/wc_ra_comparison_score_cpu_r1_launch_20261010.json)。原评分监督3869952现场1791577157.8113587实际存活，状态`WAITING_ORIGINAL_GPU_AND_RAW_CPU_HANDLES`，尚未执行或验收LPIPS；等待原GPU3866900／3866913和raw CPU3866901正常退出，不重复评分、提交GPU或改原226载荷。

[同次只读现场记录](../reports/wc_ra_comparison_r1_methods_and_score_waiter_progress_20261010.json)显示Common WC／JOINT_NATIVE／RA均完整36步，实际完整分支调用38／36／24；Human WC完整36步、35完整分支调用，共同刷新开始，两Native槽仍待。Common RA中第14／21步是年龄超出当前校准格的保守DD，第26／31步是实际校准代理触发的DD；它并非仅依赖定周期回退。当前不能据调用数宣称保真或干净速度收益，也不在运行中改阈值。

新增[评分终态只读捕获](../scripts/capture_wc_ra_comparison_score_cpu_r1.py)将保留原CPU回执／日志／注册／逐帧原件，绑定已独立验收的整八路径原件及实际metric资源SHA。其本地独立重建使用全部93距离、严格递增PTS、场景均值／中位数、正负帧、分位数／连续区间及八槽实际费用；不再调用模型评分、不写账本、不把失败子集验收为整卡成功。GPU整卡捕获在先、完整评分捕获在后；如本地复核代码出错，先保留原件后修复复核，不重跑GPU或评分。

以下准备时刻的“派发尚待／Common RA开始”保留为历史快照。

[211完整GPU卡](211_WC_RA_EIGHT_PATH_GPU_EXECUTION_20261010.md)仍跟随原3866900／3866913／3866901运行。现场1791576487.468306确认原三句柄存活，Common WC与JOINT_NATIVE各完整36更新并保存视频，Common RA开始；Human三方法与两个Native参考尚未整批验收。目标GPU26220MiB，未重复提交、改冻结226载荷或提前报告收益。

## 完整评价设计

新独立CPU评价仅在原完整GPU与原全张量／视频CPU审计退出成功后开始。固定两场景×WC／JOINT_NATIVE／RA，最多六组匹配Native参考、每组完整93帧，最多558个实际帧距离。两个Native槽及六候选分母保持；参考拒绝保留原结果，只对所有可用的精确配对评分，不补选、不填零。不在原任务失败时自动接受或评分成功子集。

使用现有隔离的LPIPS0.1.4／alex／FP32 CPU资产，无缩放、裁剪或抽帧；reader复用当前GPU卡已绑定源，metric另绑定原隔离资源的实际CPU回执与源／包／backbone／线性权重SHA。新的只读[资源身份检查](../src/wcomr/lpips_resource_identity.py)保留全部包与预训练资源检查，去除“今天GPU提交数必须等于资源安装时”的旧预算耦合；不改原审计器、共享环境、GPU stage或预算。现场[身份核验](../reports/wc_ra_comparison_live_lpips_resource_identity_20261010.json)通过，未重新安装或下载模型。

[评分入口](../scripts/score_wc_ra_comparison_cpu_r1.py)将核对原配置／receipt、raw审计、所有接受视频的SHA与完整时间戳，统一计算所有可用方法—参考的全93LPIPS。输出逐场景均值、WC减候选的保真差、93帧改善／退化／持平数、三个连续31帧区间、type7分位数；独立单位是场景。场景等权均值和中位数同时保留正负，不用单阈值裁掉困难视频。

实际成本来自原八路径，记录完整分支调用数与含诊断的pipeline wall；保真改善与时间改善分开报告。可以描述本次同流程的质量—成本关系，不能宣称等预算或干净部署速度，不能把LPIPS保真当成语义、物理或CONF质量。

## 新控制与接续

[新增汇总CPU控制](../reports/wc_ra_comparison_score_summary_cpu_controls_20261010.json)检验一正一负场景导致均值负值仍保留、参考拒绝不替换、保真提高但时间变慢的分开记录，以及缺失矩阵、错来源、截帧、错均值、重复PTS、非有限值和负成本七类拒绝。只验证新增汇总代码，没有重跑已通过的完整采样Toy矩阵；不是实际视频分数。

[完整CPU评分登记](../manifests/wc_ra_comparison_score_cpu_r1_preregistration_20261010.json)固定输出分母、源文件SHA及原GPU身份。[独立监督入口](../scripts/supervise_wc_ra_comparison_score_cpu_r1.py)只跟踪原GPU和raw CPU句柄退出，再唯一执行全部可用配对；不占GPU、不写账本。当前源已准备，独立CPU派发与原件验收尚待。

原GPU终态须独立捕获原件、费用和释放；新评分结束后重建六组均值／逐帧统计与成本来源，再据结果推进guided-W1和协调稀疏／部分MLP，不把首工作点不占优当方向否定。单次>4GPUh具体确认、原48窗口与计费保持，非必要不增加人工评审，goal active。
