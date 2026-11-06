# ACR来源记账修复与W3因果准备

2026-10-15，接续427。P80/W3-11服务器CPU独立运行，完整范围保持；无GPU、新teacher、模型权重或新预算扣费。

**01:24按预计时间一次查收R3，完整80 P用例＋11 W3检查接受。** source `f1b0da7`、550文件SHA一致，CPU全程43.0118秒，pid797604结束，预算SHA前后一致。本地另从完整矩阵/来源/动作/数值/计数/复位独立验收，未把CPU通过当实际模型或加速。下述修复与派发保留历史。

## 已定位的实际实现问题

R1在Anchor哈希校验止步，修复为实际张量/统计字段。R2进入数值测试后，**当前A、单支Dense与补偿输出已通过，但C兼容缓存检查失败**。重新读固定WC发现：它在分支计数器和native70清空之后，还会把最后head保存到`previous_output`。共享前缀的新执行器最初漏了这个写入，导致当前输出对了、以后读取的来源状态却不一致。

R3从同一固定源码抽取该post-counter写入：未计算deep的一侧保存当前C head；深算侧恢复C兼容旧残差/窗口后也保存当前C head，cycle70之后仍按源代码写入。保留物理1次deep/1次skip统计，避免误写新D或新P来源。算法修复不是放宽缓存检查。R1/R2原stage、结果和失败不覆盖。

## W3当前准备与尚缺素材

服务器与本地11因果/标签/支持/加权检查通过；独立高精度fsum重建小Ridge正规方程与实现权重相差约2e-16，输出有限。全部拟合数据为合成CPU夹具，不是实际W3收益。

四条真实中档H1的144步已通过新接口复放；保留D31支持回退、来源重置和原timestep标识，缺sigma不伪填、更不拿这些前缀训练真实模型。仍缺H1同状态C/A/D标签与真实sigma记录。

## 下轮PA的开发控制

- 新P的D/P0×早/晚四格、Pc/Pu两方向系数已用全部旧CAL16冻结，fingerprint `a195c62903f58e4bb0d6800a4aa93175472607b44a7b4ae8f2a2d58e607df6cb`。不在看到PA当前teacher后重拟合。
- `FC_STYLE_HISTORY_DIFF`简化历史差分对照已实现，只能由过去真实部署DD建立；影子DD、PP、C或ACR不能推进该历史。三个必要检查通过。不是官方FasterCache复现。
- 来源保持为ACR_READOUT，首轮无ACR_REFRESH；旧P0来源系数不被冒称为新ACR来源校准。

## 当前CPU查收

R3唯一CPU提交：source `f1b0da77946e8e0c24e943f32cab16e216e95cb0`、pid797604，stage `.sync/wc-p-acr-w3-shared-prefix-cpu-r3-20261015`，01:19:01北京时间。原R2全程序实测5.64秒但只到第一失败点；完整80预计约1–3分钟，保守于**01:24:01**一次查收原句柄。该估时以实际CPU测试量修订，不持续监听。

查收后完整80原语结果、W3-11、代码SHA、原进程结束与预算SHA一并接受；若仍在运行，按原句柄再估时，不重复启动。原语通过后仍需完整H1父轨迹的非提交式诊断与恢复/等价控制、实际PA12位置、完整报价/生产封口，不能直接GPU或称新方法已经有效。

## 当前下一步

1. 原语CPU已接受，接到冻结H1的独立诊断owner：同实际父状态、原C/A/D、单支动作全部非提交式，完整cache/控制器/solver/RNG与原父36输出/终态等价。
2. 接预选PA12状态、冻结开发系数、历史差分及全部正式/预热重复；报价包括A读出、两个probe、单支deep/head/RF、补偿与实际维护。CPU生产入口、完整scope/forecast仍待。
3. W3单独接采集真实sigma与同状态标签，当前/历史的T1/T2同分组比较；144旧前缀仅作接口材料检查，不拟合无标签真实预测器。

首轮仍ACR_READOUT、P/W3不合入主线，不恢复F/B或旧GPU自动化；这轮模型GPU0、账本0，无在途本轮CPU。未完成的整卡/正文补验保持，不因原语通过跳过。

证据：[R2原件](../reports/wc_p_acr_w3_cpu_bundle_r2_collection_20261015_0115.json.gz)、[R3派发](../reports/wc_p_acr_w3_cpu_bundle_r3_launch_20261015.json)、[144前缀](../reports/wc_w3_existing_h1_causal_prefix_replay_cpu_20261015.json)、[开发系数](../manifests/wc_p_acr_development_source_phase_coefficients_r1_20261015.json)、[Ridge独立数值](../reports/wc_w3_normal_equation_reference_cpu_20261015.json)。

完整接受：[R3查收](../reports/wc_p_acr_w3_cpu_bundle_r3_collection_20261015_0124.json.gz)、[独立矩阵/身份验收](../reports/wc_p_acr_w3_cpu_bundle_r3_independent_acceptance_20261015.json)。
