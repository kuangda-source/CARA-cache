# 从未来掩码诊断到在线阶段规则：CPU通过，完整成本已具体化

2026-10-04。承接[98四组合实测](98_WC_TIMING_FACTORIAL_RESULTS_AND_EARLY_PROTECTION_NEXT.md)，新增简单、无训练的阶段选择器。当前仅CPU接线和成本草案通过，**尚未选择/冻结下一GPU执行卡、提交GPU或预付费用**。历史104点、四组合及失败原件均不重跑或覆盖。

## 方法与对照

[纯策略](../src/wcomr/stage_refresh_policy.py)/[适配器](../src/wcomr/stage_refresh.py)只读取当前实际去噪step及过去同CFG窗口内eligible刷新计数。继承固定原生WC注入：**不替换skip predicate，不读取未来掩码、当前/未来deep truth或四组合位置表**。阶段窗口23–27含端点；早期和窗口之后的官方full用D，官方cache仍按原生判定执行。若S改变latent，后续官方skip决定可以随之变化，不能声称固定38deep或复现oracle轨迹。

窗口23–27由曝光human四组合结果提出，是CAL调参，不是独立确认。CFG call与视频帧不同；此规则不声称动作/物理关键时刻都发生在该去噪窗口。

23个S层保持2..27且排除6/23/27，probe2、sim0.1/cdf0.98/no-PV，warm、至少两个过去真D、已付probe及非finite拒绝保持。S仅写近似原生forecast来源，不能写true-dense历史；counter/CFG/请求/model/condition与native70清空、尾两次warm full保持。

比较窗口内每个eligible full用S，与每CFG第一次eligible后隔一次用S。频率计数仅在窗口内递增，原生周期reset后归零；不能把早期D的eligible次数计入新窗口相位，也不能强行增加full来凑S配额。实际S次数未知，上限每候选10/6，可能为0；不同频率不是等成本前沿。

[八输出核心](../src/wcomr/stage_output.py)/[草案](../manifests/wc_stage_window_draft_20261004.json)：

1. 第一CAL先官方WC与S关闭的阶段适配器，严格fresh-prepare D/D九门、五状态和完整pipeline止步。
2. 两个曝光CAL各生成官方自适应WC、窗口every1、窗口every2，共六测量。保持同seed、入口RNG、模型、条件、采样和完整93帧输出；每臂真实prepare一次、必要selector/provenance/kernel/decode/guardrail/write计入wall。
3. 历史D桥若声明两CAL的SHA，必须在每请求首个S候选前检查，失败保留已有输出、八分母且停止下一请求。技术失败不改配置或替换输入补跑。

这是两个CAL的当前接口草案，单次顺序测量用于技术/保真诊断，不接受稳定加速；后续重复计时、强基线和独立确认另计预算。

## 实际CPU证据

[实际r1回执](../reports/wc_stage_window_sampling_cpu_r1_20261004.json)，114.439167秒，Torch2.7.1+cu128，CUDA明确禁止。旧light入口15控制、新八输出10控制（flow OFF/ON各5）及纯策略4组通过；[独立原件/source审计](../reports/wc_stage_window_sampling_cpu_audit_20261004.json)绑定服务器原件SHA、28份当前依赖、5份固定官方源与现场账本，预算未变。

新10控制包括完整八输出、历史D桥完整复现、D/D解码不一致、第二请求最后S候选kernel NaN及错误历史D桥在任何S前止步。每种失败保留全八分母和前序产物；九门/完整pipeline、36更新72CFG/prepare1、当前窗口/逐CFG频率、真D隔离、实际counter snapshot/restore及负数/过大/bool计数拒绝、native70清空/尾dense和hook/forward/buffer清理通过。

[测试](../tests/check_stage_output_cpu.py)为明确验证cadence，在toy中强制窗口内多个原生full点。CPU窗口every1为10 S、every2为6 S；**不是上一human oracle的9/11，也不是实际自适应轨迹次数或反馈验证**。Toy net、条件、归一化、CPU稀疏输出替身、mock decoder/writer不是权重、实际稀疏核或视频。没有CPU质量/速度结论，旧actual CPU不被追认覆盖后来新文件。

## 完整成本与公平基线

[可重算的规划脚本](../scripts/plan_wc_stage_frontier_cost_cpu.py)/[机器成本草案](../reports/wc_stage_frontier_cost_draft_20261004.json)绑定历史成本、实际结算与F1原件。保持保守DD/full代理381.750898秒、light235.768257、加载95.915549及bookkeeping75秒，20%包络与30秒释放。历史接受Native最大314.462688秒只作成本参考，不证明当前共享eval与历史Native输出等价。

自适应S可以触发更多full，四个S测量均用full代理；Native少步不按步数线性折扣，低/高阈值WC也用full代理。不能沿用38固定deep的单次212秒当新卡保证。全部成本包括加载、首次kernel、选择/来源、prepare、采样、解码/guardrail/write、失败与退出flush。

| 条件阶段，均未选卡 | 完整输出与控制 | 完整规划秒 | 拟独立上限秒 |
|---|---|---:|---:|
| 在线阶段窗口/频率，两曝光CAL | 2 D/D + 每CAL的WC/window/cadence，共8 | 3549.549 | 3600 |
| 公平CAL前沿，两CAL | 2 D/D + 每CAL六工作点，共14 | 6298.155 | 6300 |
| 新独立CONF | 2 D/D + Native/少步/selected WC/selected stage，共6 | 2808.526 | 3000 |

公平CAL六工作点必须明确保留：**Native完整35请求/36实际、Native少步23请求（实际scheduler长度须实测）、WC阈值0.04/0.06/0.08、CAL选定的stage候选**。共同Cosmos2.5-2B、prompt/首帧条件、seed/初始噪声、guidance7、93帧432×768/16fps、精度/共享模式/卸载与完整pipeline。少步与阈值是明确干预变量，不能把不匹配配置当同状态误差；Native/fewer-step新完整入口和CPU/GPU parity尚未实现，不得以本阶段固定35的CPU代替。

后续CONF必须冻结新输入/seed和不再调参的策略；既有两曝光CAL及24-CAL开发成员不改叫CONF。两个CAL/一个CONF仅为有界推进方案，不替代原24-CAL与更完整独立研究计划。自动语义/物理评价和更大CONF成本仍须单独测量，不当作免费或默认人评。

当前已结算 **9.136838727254782/12 GPUh，42jobs**，余 **2.8631612727452183h = 10307.380582秒**，无inflight。三拟上限合计12900秒，计15秒余额门超 **2607.619418秒**；不能同时为三卡准入或删掉强基线/CONF挤预算。第一独立卡单独可容纳，前两拟上限9900秒也可容纳；未来第三卡必须在前序按实费替换预付后重新算余量，不保证当前就能全部完成。若实际费用仍不能容纳后续完整矩阵，应报告资源缺口，不把少量通过改定义为质量—时间前沿完成。

## 下一步

先把八输出草案具体化为独立scope/runner/监督器、历史D/CPU原件/source/assets/package/prepare/native-meta/sample条件的实际部署门和终态独立审计；冻结source并同步GitHub，再fresh UUID/sm86/VRAM/compute/磁盘/f1锁/12h账本后，仅选择并提交该独立卡一次。当前没有GPU提交、下一卡选择或预付。

只有真实在线候选取得可用保真/成本信号后，继续完整Native/少步/调过WC前沿入口；曝光human固定掩码的0.928 SSIM不当作新阶段规则的预期结果或接受门。若在线反馈损坏保真或S必要开销抵消收益，保留失败/负结果并审查23层S候选，不先训练Trust/RV或叠模块。不新增人评、训练或paid scoring。科学goal active。
