# N09完整40路径部署测量入口准备

2026-10-16。**五个冻结工作点、两旧CAL、三种诊断模式的完整40路径运行入口已接通，26项本地CPU控制通过。** 它将用于组件／生命周期费用和逐请求显存测量；真实Cosmos生产CPU、实际报价／部署、GPU测量与终态接受尚待完成。

## 本轮完成

新增 [`runtime_profile40_execution_r1.py`](../src/wcomr/runtime_profile40_execution_r1.py)、[`runtime_profile40_production_r1.py`](../src/wcomr/runtime_profile40_production_r1.py) 和 [`run_wc_paper_N09_runtime_profile40_r1.py`](../scripts/run_wc_paper_N09_runtime_profile40_r1.py)。直接调用原冻结执行器与原观察器，没有改动四份已接受的核心源码。

原509范围完整保持：十个scene×method组，每组一条完整预热＋ORIGINAL_AUDIT／PROFILE_AUDIT／PROFILE_LEAN三条正式诊断路径；总40路径、1440 pairs、一次加载、零teacher。五个方法仍为NATIVE35、WC_HALF、RA_DEFAULT、A_NO_P、TABLE_PHASE_H1，原提示词／seed0／步数／规格不变。

每次先恢复模型／求解器／RNG与shared eval，再观察完整请求。原取证与预热只读请求边界显存，不安装组件hook；另外20条启用原组件观察器。GPU路径在模型驻留后对当前可见`cuda:0`同步、reset peak，记录allocated／reserved与各自峰值及起始基线；CPU控制保留不可用为null。

原取证、带观察器取证均保存36个实际guided输出；轻量模式只关闭研究guided副本，算法维护保持。所有完整结果仍保存终态、动作、A/source history与视频原件。张量和标量profile在请求计时结束后归档，失败／拒绝／未到达位置保留，不补样。三种模式的时间有不同观察设置，不作为三次重复clean计时；组件区间为inclusive，不能相加冒充端到端总时间。

生产合同绑定原N07/N08接受与原capture，离线重新调用原独立接受器并匹配shared config、方法冻结与N08协议。已接受完整102观察器证据通过原capture SHA及四份当前源码逐项复用；原完整952数值／物理资产仍由原shared validator核对。没有重复102或952矩阵。

实际运行入口按原生产方式检查guardrail、固定Native类、28块、后端、eval、原CPU结果、UUID锁、source/config与v2整卡预留；提供两原输入的实际生产CPU入口，但本轮没有在服务器执行它。GPU卡仍须实际CPU接受、完整费用与fresh预算准入；等于或超过12GPUh需具体整卡批准。

## 验证层级

26项为5生产合同、8执行／归档、7观察器生命周期与6原重复测速接线控制，全部通过。覆盖40原顺序／三模式、20个profile路径、十个原输入变体、36步取证模式、原CPU张量归档、完整失败分母、source/seed/报价错误拒绝、原主线接受重新绑定、exact12批准规则。另用`python -S --help`确认新CLI可解析；这不是实际Cosmos依赖导入。

推理／视频／CUDA观察及原GPU接受为明确替身；小型真实CPU张量只验证归档。原四份观察器／数值源码SHA与509登记一致。当前没有新完整Toy数值采样、实际Cosmos CPU、原模型前向、真实GPU组件费用、显存或质量结果。

R1的21项、R2的25项、R3/R4的26项回执均保留；R4补入原CPU无CUDA／无权重、完整十输入／40矩阵与两guardrail控制的核对，绑定当前全部五份新源码。

## 余项与主线

本40路径还需实际配置／整卡报价、生产CPU部署与单次GPU监督、完整原件／guided／RGB／owner释放及费用接受。N09另两个问题——同一已支付双probe下的C/A/P0/D动作价格、可复现标定采集配方的实际成本——继续单列，不能由本40路径代答。

N07原source`140d0a6`／180路径、今天21:30半程检查与明早05:30验收保持。顺序仍N07→N08→N09/10；同一cap113、原origin与严格<12自主规则保持。本轮0SSH、0新GPU、0服务器／账本写。517的固定权重连接缺口仍保留，未启动新下载／评分或更改资源自动化。F/B关闭，无训练、OMR或人评。

原件：[最终26项CPU](../reports/wc_paper_N09_runtime40_production_entry_related_CPU_R4_20261016.json)、[21项执行与原四源码核对](../reports/wc_paper_N09_runtime40_execution_CPU_R1_20261016.json)、[25项中间控制](../reports/wc_paper_N09_runtime40_production_entry_related_CPU_R2_20261016.json)、[509原完整范围](509_WC_N09_FROZEN_RUNTIME_PROFILE40_SCOPE_AND_REMAINING_ACTION_CALIBRATION_COSTS_20261016.md)。
