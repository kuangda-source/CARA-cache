# P-ACR完整报价20的audit/quiet CPU准备与查收

2026-10-15。**上一层完整H1父接口已经接受；本轮推进五动作的完整重复、计时顺序与关闭取证的等价控制。** **03:01原CPU823795终态与完整数值scope独立接受：48路径/96状态/1920额外试次，全程954.5665秒，预算SHA不变；p-acr-cpu已暂停。** 无新GPU或真实报价。下述派发和等待段保留历史。原A/H1、417/420/423/424科学结果与真实H1参数保持。

## 已验收的入口

[429](429_WC_P_ACR_FULL_H1_PARENT_CPU_AND_PRODUCTION_QUOTATION_NEXT_20261015.md)：source6ef228e/1532，原CPU817370已结束，全程370.9358秒，原32完整CPU路径/48固定状态/528额外pairs/1680总pairs、全部恢复与36输出/动作/终态/mock视频接受。原p-acr-cpu查收已暂停后复用于本轮不同CPU句柄，原任务不再查询。

## 本轮实现与完整范围

新独立`p_acr_profile20_owner_r1.py`复用已接受的物理/owned快照和普通H1继续部分，仅扩展诊断循环。五动作C/A/D/Pc/Pu各一次完整预热＋三次正式计时；正式正序→反序→正序，每次从同一状态恢复。全部CAD和单支重复输出逐项相等，Pc/Pu仍基于实际A读出与当前选中支的真实D，历史差分只读过去普通DD。

两个报价观察模式：audit完整记录实际head与Linear；quiet只临时关闭8个Linear预观察hook和1个head观察hook，真实MLP forward、mask、缓存、来源及读出保留。禁用未知或算法hook，不把没观察到的head记成0；quiet记录None，并与audit全部候选payload及普通父36输出对照。安装的hook身份/顺序与MLP forward在每次报价后恢复。

|注册范围|数量|
|---|---:|
|两flow×四Toy提示词×两合成来源情形×普通/audit/quiet父|48完整CPU路径|
|实际普通父更新|1728 pairs|
|诊断状态|96|
|五动作1预热3正式|20 pairs/状态|
|额外预热/正式|480 / 1440 pairs|
|全部额外 / 全部模型pairs|1920 / 3648|
|对应CFG调用|7296|
|physical＋owned串行恢复|1920次|

这些均为CPU夹具的分母，真实生产报价的拟议8父/12点/528pairs另有身份，不混合。

## 防止遗漏算法成本

当前单支执行器每次构造仍编译/绑定源代码。因此记录`action_preparation_seconds`，并将其加到`charged_action_seconds=full_pair_seconds+action_preparation_seconds`。pair计时包含两个probe、实际A heads、单支deep/head、RF、补偿和必要算法维护；恢复、哈希、输出CPU副本及写盘在pair计时外。没有实现摊销前，不把单次构造费用从算法报价中删除。

新增CPU断言保留全部正反序与重复，对audit逐次核对：C/D各2head，D源A4/P源A6，单支D源5/P源7；C/A无深层Linear、D16条、单支8条。quiet关闭恰9个纯观察hook，候选数据与audit仍应逐项一致。实际是否通过等待完整结果，不把声明当验证。

## 唯一CPU提交与预计时间

source **8f0971583b2121e214c9976a906e41adabebed7a**、本地完整packet **1538个文件**，独立stage `.sync/wc-p-acr-profile20-cpu-r1-20261015`，原CPU **823795**，02:35:17单次提交。原CPU32数值341.48秒；本轮3648pairs与1920恢复比上一层多，估计15–25分钟，按25分钟保守，于**03:01北京时间**一次查收（最早03:00:17.199、unix1792004417.199）。p-acr-cpu已更新为只查此原句柄。期间不持续查询或重复派发。

使用`capture_wc_p_acr_profile20_cpu_r1.py --launch-ref reports/wc_p_acr_profile20_cpu_r1_launch_20261015.json --output 新.json.gz`；到时接受全部48路径/96状态/1920试次、audit/quiet/父36等价、实际计数/计时口径、源hash、原进程终态和预算SHA。未结束就按剩余工作量再估时、安排一次查收并结束该轮；失败保留原件和完整分母，不缩卡或放宽真实校准域。

## 后续设计

新层接受后，接真实PA12输入/冻结系数、完整输出审计、CPU生产入口和包括全部父路径/加载/恢复/I/O的forecast。原PA1.5GPUh只作建议，不拿CPU成本或当前packet准备替代实际报价。

W3继续缺真实sigma/连续pre-action观测与同H1 C/A/D标签。12个旧CAL点不能代替8开发提示词×8位置；T1/T2标签与历史贡献分别比较，局部regret后再闭环。新P/W3没有自动合入论文主线；五项正式补验和已有A/H1写作继续保持。

现阶段新GPU停止，F/B已结束、旧P13h暂缓/E2具体审批未取得、不新增人评/训练/OMR。原48窗口最后核验余24.974985961不重置，本轮GPU0/不扣费。严格>8GPUh确认规则不解除停止GPU的指令。

证据：[CPU预登记](../manifests/wc_p_acr_profile20_cpu_prereg_20261015.json)、[唯一提交](../reports/wc_p_acr_profile20_cpu_r1_launch_20261015.json)、[上一层独立接受](../reports/wc_p_acr_full_h1_parent_cpu_r3_independent_acceptance_20261015.json)、[真实生产拟议范围](p_w3_e0_20261014/PA12_Production_Controls_And_Price_Scope_20261015.md)。

## 最终接受（03:01）

原source8f09715/1538文件一致，原823795已结束；两flow各24完整路径、48状态、960额外试次，合计48/96/1920/3648pairs/7296CFG。全部五动作预热/3正式正反序、20serial恢复、普通父36输出/动作/终态、audit与quiet候选payload等价通过；audit的D/P实际head与Linear计数及quiet关闭恰9个观察hook均独立核对。构造费用加计等式通过，数值925.0455秒、全bundle954.5665秒，预算SHA不变/GPU0。

证据：[原终态](../reports/wc_p_acr_profile20_cpu_r1_collection_20261015_0301.json.gz)、[独立完整scope接受](../reports/wc_p_acr_profile20_cpu_r1_independent_acceptance_20261015.json)。仅Toy接口/计时控制，不代表真实PA12资源、报价或新方法端点。最新实际输入与完整费用见[431](431_WC_P_ACR_ACTUAL12_INPUTS_AND_FULL_COST_PREPARATION_20261015.md)。
