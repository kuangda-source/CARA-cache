# P单支共享前缀与W3因果接口：CPU准备

2026-10-15。接续[426离线结果](426_WC_P_W3_E0_COMPLETE_ASYMMETRIC_ORACLE_AND_COEFFICIENT_RESULTS_20261014.md)，继续接口准备，**无新GPU或实际模型teacher**。

## 新P当前实现

`ACRReadoutExecutor`使用现有DC/CD配对执行器：两支当前shallow只付一次，缓存A读出从同一前缀产生，只有选定支继续真实deep及RF；另一支不运行deep。共用前缀、源精确cache/flow/head及RF转换，单支结果按冻结标量创新量补偿。

计算侧的临时WC深层来源不会保留：恢复该侧为C兼容的原residual/probe/windows/previous-output，普通C的current-input/probe bookkeeping推进；物理deep/skip次数仍按实际计算统计。真D和工作bank只读，不重置源年龄，不生成新hidden来源。native70末尾清空保持。此为独立ACR_READOUT原语，不是已接入完整H1/CAD控制器。

完整CPU范围为两flow×五位置（12/23/29/30/35）×两方向×四系数，共80例；对照独立C/A/D源函数，检查两个shallow/一个deep、A与真实单支D及最终补偿、C兼容缓存、银行/RNG/条件不变、cycle70。

本地R1因vendor两个文件版本不匹配止步；R2因源码准备进程未完成就引用新目录止步；R3因本地缺diffusers止步。三份失败回执保留，均未到算法数值结论。已有八份固定服务器源码CPU只读取回且SHA一致，未放宽源码门。下一在独立服务器CPU stage复用既有生产依赖运行完整范围，不修改共享环境。

## W3当前实现

`Observation`只接受当前paid统计/来源/年龄/真实sigma/g及支持标记，teacher标签是分离类型；严格前缀/提示词/seed/reset，T1有13个当前特征，T2加入真实因果窗口4共27维。不同σ缺失与整数timestep不互换，age7/D31不通过新预测扩域。

小Ridge直接输出`r_A=g²q_A`和`r_C−r_A=g²(q_C−q_A)`，等价于现有规范中的统一q与差值坐标。先修复rA/rC非负，再重算J和margin；**J=cost+λr，不第二次乘g²**。差值允许负，保护/原支持缺失走D。按整提示词拟合与训练组标准化，不从held标签构造线上特征。

本地11必要检查通过：未来不改旧特征、跨组/乱序拒绝、reset计数、teacher字段隔离、D31支持、同状态身份、g²仅一次、负差值/修复、缺σ、held隔离和模型schema。全部训练/标签为合成接口数据；没有真实W3预测、regret或视频收益。

## 仍待完成

先完整P原语CPU/服务器依赖验证，再接入非提交式完整H1父状态恢复、原父36输出/终态对照与PA12状态/报价入口；W3接采集/数据原件与真实T1/T2标签评价。对应完整scope/forecast/生产入口还未封口，不将建议1.5GPUh当准入。

P/W3没有并入冻结主线。F/B不恢复，人评/训练生成器/OMR不新增；原GPU停止要求、余额及48窗口不变。

范围：[CPU预登记](../manifests/wc_p_acr_w3_cpu_interface_prereg_20261015.json)。代码：[P](../src/wcomr/p_acr_readout_r1.py)、[W3](../src/wcomr/w3_causal_trend_r1.py)；W3本地证据：[11检查回执](../reports/wc_w3_causal_trend_local_cpu_r1_20261015.json)。
