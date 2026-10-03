# 同S预算下的缓存来源位置：离线下界、CPU接线与六输出提案

2026-10-04。沿[92人物六输出结果](92_WC_SELECTIVE_HUMAN_RESULTS_AND_FORECAST_WINDOW_NEXT.md)继续：低频S把算子减半却仍有26次cache读取近似来源。本轮先固定计算数量研究位置，不训练、不扩样；[机器摘要](../reports/wc_forecast_placement_summary_20261004.json)。当前仅源码与CPU，无新GPU、视频或质量结论。

## 在相同S预算下，可以改变多少后续复用

[精确CPU来源分析](../reports/wc_forecast_placement_source_cpu_20261004.json)使用已审计六输出原件，raw SHA a752a19587552ca4842a3dec0683bbf42891a3a774c4987ca104c58cc0364265。先逐call复现原full/small/cadenced三种实际来源组合；三者都38次deep/34次cache、26次读取S来源。

固定human_199/seed0曝光官方38-deep掩码、warm14/native70/尾两dense、相同23个S层和CFG配额6/5（合计11次S、253算子、27次D）。每个CFG分支的来源窗口独立，所以可分别穷举；首次S固定的两分支共588种组合，不限制首次的共1176种。主目标最小化“至少读取一个S来源的cache调用数”，次目标最小化S来源读取次数，再按序号字典序决定平局。没有按视频误差或质量选择位置，没有新增GPU搜索。

| 离线方案 | 首次S call（CFG0/1） | S次数/算子 | 读取S的cache调用 | S来源读取次数 | 最大同CFG复用年龄 |
|---|---|---:|---:|---:|---:|
| 已实测legacy SD | 23/24 | 11/253 | 26 | 26 | 8 |
| 保持首次S的最小值 | 23/24 | 11/253 | 15 | 16 | 8 |
| 放开首次S的最小值 | 45/48 | 11/253 | 2 | 3 | 2 |

首次匹配的S calls：23/24/45/47/48/49/50/51/52/53/54；自由位置为45/47/48/49/50/51/52/53/54/55/58。自由位置只有call56与62的cache读取S来源；8个S来源没有被后续cache使用，但仍影响当步速度场与latent。年龄以同CFG有效调用计，不是视频帧。两种方案的深层次数、S次数、S层数一致，只是名义计算量匹配；实际wall仍须测量。

这把下一问题从“不断降低稀疏比例”收紧为：同样花11次S，是否可以减少其后续缓存影响？连续两次真D可让原生预测窗口的最后两个来源都成为D；交替S/D未必做到。true-D metadata与native residual window是不同结构，不能只改标签或清空元数据冒充刷新。

这些下界利用了**已经曝光的未来full/cache掩码**，是oracle机制对照，不是线上策略。自由位置同时改变首次S噪声区间；首次匹配也改变其余S时刻，不能单独识别缓存寿命的因果贡献。来源数减少不代表视频更好，D也只在自身轨迹上为真，不会恢复官方latent；必须用完整视频判定。本轮不是[68刷新价值](68_WC_COUNTERFACTUAL_REFRESH_VALUE_DESIGN.md)的有符号收益标签。

## 当前接口与实际CPU证据

[policy](../src/wcomr/selective_refresh_policy.py)新增不可变SparsePlacementPolicy，两组明确、排序的正整数eligible序号；选择只读取当前分支已发生的计数。位置如何产生仍依赖曝光未来轨迹，不能因执行时只读计数就声称online。原周期策略默认to_dict和选择逻辑保持，adapter显式传CFG，counter随call70清空和snapshot恢复。

[六输出核心](../src/wcomr/selective_output.py)增加明确forecast_placement比较；默认layer_cadence旧路径保持。新比较拒绝错层/错配额/超界位置或缺首次匹配；先严格D/D，再固定D→legacy SD→首次匹配→最小来源位置。候选均须实际满足相同分支S配额，不足paid-probe/合法历史不能静默补S；历史D或legacy SD不复现则在新变体之前止步，六分母保持。

[实际CPU r1](../reports/wc_forecast_placement_sampling_cpu_r1_20261004.json)126.129秒，旧14控制与首版新8控制通过。针对mock decoder可能饱和，新增旧legacy采样返回/解码/guardrail/写入前实际张量指纹比较；[当前r2](../reports/wc_forecast_placement_sampling_cpu_r2_20261004.json)64.907秒，新8控制通过。只改check_forecast_placement_cpu.py一叶，r1旧14不执行此叶；[独立原件与源码审计](../reports/wc_forecast_placement_sampling_cpu_audit_20261004.json)绑定两份服务器原件、当前35份依赖及r2覆盖，不用旧CPU追认改后的测试。

flow OFF/ON均真实走固定原生函数体的36 solver/72 CFG/每臂一次prepare/六臂；D/D九门与完整pipeline、三D一致、legacy实际张量指纹、指定CFG位置/真实D隔离/预测来源、计数恢复与换策略拒绝、70失效和尾dense通过。D/D掩码不一致、legacy SHA不匹配、第一新变体kernel NaN均止步，保留先前文件和六分母，hooks/modes/buffers清理通过。这里用ToyNet、CPU S输出stand-in与mock writer，CPU计划来自toy trace，不是人物真实核或视频。

[19项纯policy/source控制](../reports/wc_forecast_placement_policy_cpu_20261004.json)拒绝CFG混淆、布尔/重复/乱序/非正序号、可变slots、周期混用、未来引用、错误来源种类/CFG/reset及不完整记录；[实际controller8项preflight拒绝](../reports/wc_forecast_placement_preflight_cpu_20261004.json)在任何phase准备前拒绝错S配额/超界/错首次/错层、把oracle传给旧比较、未知比较、错误SHA和已存在身份。后者只是早期范围控制，不是GPU资产或资源准入。Torch2.7.1+cu128禁止CUDA且未初始化，两轮及preflight账本均保持，GPU新增0。

## 六输出提案与完整成本

[具体提案](../manifests/wc_forecast_placement_human_proposal_20261004.json)/[位置清单](../manifests/wc_forecast_placement_draft_20261004.json)。拟独立WC-FORECAST-PLACEMENT-HUMAN-R1-20261004-A/wc-forecast-placement-human-r1，仅同一曝光human_199/seed0，93帧768×432/16fps、35请求/36实际UniPC、72 CFG、固定38-deep。S参数0.1/0.98/no-PV，6/23/27继续D，三个候选各253算子，不添当前/未来deep truth。固定D与旧4d0f…82fb一致；legacy SD必须复现7caed…119b，才进入两新位置。

[完整cost提案](../reports/wc_forecast_placement_cost_proposal_20261004.json)沿已实测保守D/D381.751秒×2、light214.335秒再加10%×4、加载95.916秒与bookkeeping75秒，乘1.2再加30秒结算，共2282.988秒。拟2400秒全cost/2370child/kill5；不是挤进或重复原104点1800秒身份。加载/失败/必要来源与选择/核/decoder/guardrail/write/flush/释放计入；D/D观察wall不进部署比较，首次S保留。四测量各一次，不提供重复速度或CONF。

当前累计8.215651676683272/12GPUh、40jobs，余3.7843483233167277GPUh，无inflight；没有卡选择、source冻结、GPU部署或reservation。下一完成独立runner/scope/监督器与完整payload，再实际CPU原件和对应源/旧视频/prepare/native-meta/资产/import/package/条件门、fresh GPU/锁/账本/磁盘准入，仅在这些门后另行单次提交。

实际终态须独立验证六视频完整解码、38共同动作、实际分支6/5 S与253算子、每个policy的来源组合与真D/70清理、历史D/legacy SHA、全费用与原进程/锁/GPU释放；再比较同官方参考PSNR/SSIM/temporal/帧差量。若连低来源复用的oracle位置也没有可取的保真—耗时表现，不扩样或叠加学习模块，回到近似误差与基本计算价值。若只自由位置有效，优先检验噪声时间/位置敏感性，不能把收益全归因于cache来源。Native/少步/调过WC前沿、语义物理/CONF仍缺，科学goal active。
