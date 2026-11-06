# F19-A1 → 1.9×：三项零 GPU 探索

2026-11-03。授权范围为用户指定的成本拆解、保存 B1 张量的差分保持诊断、16–17D 布局准备。**真实B1补测现已完成，见[R2完整结果](REAL_B1_RESULTS_R2.md)：12状态、10组保持差分、24组单支混用和4组外推；保持差分10/10低于同目标C及A，直接混用和当前外推不优先。** 两轮GPU提交/新增GPUh/账本访问均为0，没有模型推理或旧视频重评分。下文保留首轮成本/布局与原连接失败记录，原缺口由R2补齐；局部结果不构成GPU准入或F19终点验证。

## 1. C 步成本：总账能核对，绝对单步成本尚不能唯一识别

复用 [B36完整原分析](../../../reports/cara_fast_B36_complete_analysis_r1_20261029.json)，保持原输入内重复均值、四旧CAL输入等权、完整93帧与双时钟口径。主目标为T_DD，完整请求保留独立口径。

| 已接受角色 | T_DD/秒 | Alex LPIPS |
|---|---:|---:|
| Native35，实际36更新 | 252.812242 | 0 |
| Shared25-C | 185.805542 | 0.062266 |
| F19-C | 148.447718 | 0.249365 |
| F19-A1 | 149.482379 | 0.231499 |

1.9×对应133.059075秒，需要再省16.423304秒。Shared25-C与F19-C之间每次D→C的经验差价为6.226304秒；Native与F19-C给出6.139090秒，两者不完全相同。用前两条固定布局拟合后，Native残差为−1.482643秒，因此这只是筛选用的近似成本模型。

`T = B + nD*d + (36−nD)*c`只能识别`d−c`和`B+36c`，不能把解码/固定开销B与C绝对成本c分开。将B强设为0得到的c=0.837443秒只是一个假设，不能称为实测“每C约1秒”。F19-A1实际为 **19D＋6A＋11C**，17个非D不能都按纯C优化；A1相对C整条路径增加1.034661秒，经验上约0.172444秒/A。

另复用[N09原组件回执汇总](../../../reports/wc_paper_N09_full40_complete_results_analysis_20261018.json)的10条PROFILE_LEAN观察。旧配置两层浅层块、两CFG支合计平均0.479215秒/更新；主输出头约0.0034秒/支，solver约0.002秒/更新，VAE约6.36秒/请求。它们属于旧配置的诊断计时，嵌套区间不能相加，不能移植成F19的实测组件价格。按该浅层价格类比，11个纯C去掉探针约省5.271369秒，仍差11.151936秒。即便将11个C从假定1秒降到0.3秒，也只有7.7秒；“省约10秒”需要同时改变A路径或其他组件。

源码核对：固定mask仍支付浅层块、漂移/显著性和日志/标量读取；C的OSI和光流读出继续依赖当前probe。**不能只因为刷新决策固定，就把probe删掉后仍称为同一个WC-C读出。** Flow开关也会改变返回张量。可先尝试的两个窄优化是关闭仅用于决策的saliency，以及避免纯C在`prewarp`克隆后立即丢弃的临时张量；后一项只完成源码定位，没有修改生产实现。

已新增 [profile_policy_owner](../../../src/wcomr/cara_f19_profile_r1.py)，在已构造的owner上记录D/A/C配对、浅/深层、saliency、OSI、光流、warp、输出头、读出和solver区间；记录实际更新号。原始WC源码与原执行入口不变。CPU计时只验证接线；真实F19的漂移/残差代数/内存搬运余项及GPU组件时间仍为空。该模块可附着到未来新卡的诊断路径，不能混入clean均值。

```python
with profile_policy_owner(owner, scheduler, device='cpu') as diagnostic:
    # Existing owner.pair / scheduler.step loop, unchanged.
    ...
# diagnostic.summary: inclusive diagnostic spans, not clean latency.
```

## 2. CFG差分保持：首轮准备记录，真实补测已由R2完成

实际源码采用`v = c + 7(c−u) = 8c−7u`。仅刷新条件支、保持过去差分`δs=cs−us`时，`v_hat=ct+7δs`，误差恰为`7(δs−δt)`，MSE放大系数49。若改为刷新无条件支，则系数为8；不能把两种操作混用，也不能使用描述中的7.5。

[离线分析器](../../../src/wcomr/cara_f19_zero_gpu_r1.py)读取原B1 manifest与每个state/anchor的完整SHA/字节数，检查同request/model/parent、实际更新号、原same-state/head/RF控制、FP32两支输出；只在CPU计算。逐对输出差分漂移MSE、引导MSE、相对RMSE、最大误差及相同目标状态原WC-C误差。没有阈值调参或endpoint推理。

B1只有两曝光输入、每输入22/23/25/33/34/35这6个状态。可以形成的真实更新间隔如下：

| lag | 每个输入的源→目标 | 两输入比较数 |
|---|---|---:|
| 1 | 22→23、33→34、34→35 | 6 |
| 2 | 23→25、33→35 | 4 |

这是 **Shared25-C父轨迹上的跨时刻shadow-D平滑性诊断**，过去shadow输出并非该父轨迹上真正部署的刷新。它既不覆盖拟替换的F19中段D，也不验证单支刷新后两支不对称缓存、UniPC历史及完整自由运行；B1局部误差即使较小，也不能直接证明LPIPS≤0.27或完整单支部署可行。

首轮产物中的真实B1误差值均为`null`，该历史产物不覆盖写。首轮本机只有tiny夹具；原双卡服务器三个已有通路分别发生banner超时、目标22端口关闭、banner超时，保留 [r1](../../../reports/cara_f19_zero_gpu_b1_manifest_readonly_r1_20261103.json)、[r2](../../../reports/cara_f19_zero_gpu_b1_manifest_readonly_r2_20261103.json)、[r3](../../../reports/cara_f19_zero_gpu_b1_manifest_readonly_r3_20261103.json)。随后依用户新指示恢复服务器并完成[R2真实CPU补测](REAL_B1_RESULTS_R2.md)，全局网络/SSH配置和原实验保持。

连接恢复并取得原保存资产后，可在CPU运行：

```bash
CUDA_VISIBLE_DEVICES='' PYTHONPATH=src .venv/bin/python scripts/cara_f19_zero_gpu_r1.py \
  --output-directory reports/cara_f19_zero_gpu_B1_followup_r1 \
  --b1-assets /absolute/path/to/original/B1/assets
```

分析器默认要求原manifest SHA `5487f8db32d45a5d0f3304333bf362d9d6ec46fb3181c735d7267b78a6e398fa`；R2已完成真实字节复核及新引导坐标诊断。结果由原两支张量直接计算，首轮及R2各自保留来源和分母。

## 3. 三组候选布局：先保存，不按未知LPIPS选赢家

原F19的D为`1–8,10,12,14,16,18,20,21,24,27,30,36`；A为`9,11,13,15,17,19`，alpha=1。原最大非D年龄5。三组均保留D8–D16、初始1–7与周期重置D36。

| 候选 | 相对F19删除D | 剩余D | 原A中仍合法的age1数量 | 最大非D年龄 | 仿射T_DD估计/秒 | 实测LPIPS |
|---|---|---:|---:|---:|---:|---|
| F17_TAIL | 27,30 | 17 | 6 | 11 | 137.030 | 未运行 |
| F17_MIDDLE_TAIL | 18,30 | 17 | 5 | 8 | 136.857 | 未运行 |
| F16_TAIL | 24,27,30 | 16 | 6 | 14 | 130.803 | 未运行 |

每组保存四个合法变体：保留原A中仍为age1的位置、每区间age1、每区间age1+2、全纯C。A2表示在年龄1和2连续使用同一修正算子，不是更换修正公式；保持原阶段alpha（25前1，25起0.5）。删除D18后A19已为age3，因此不能把它继续称为原A1；该变体将A19改为C，其余变体可明确在17/18补A。全部 **12个结构候选** 由原interval grammar编译，未改变旧冻结。所有真实时延/LPIPS字段均为空。

17D保留原6次A的近似成本137.030秒，离目标约3.971秒，因而“17D＋轻量C”值得优先拆解；F16虽在估算中约1.933×，但14步老缓存是实质质量风险，不能从时间估计推断LPIPS。P0只在Uniform19、两个旧FIT的8/20位置检验写入价值，不是F19的D27/D30删除标签，也没有建立“8–16所有写入都高价值”的逐位置证据。历史D33观察不能直接当成当前F19删除实验。

## CPU验证、产物和剩余边界

[最终CPU回执](../../../reports/cara_f19_zero_gpu_r1_20261103/CPU_controls_r2.json)：7项控制全部通过；原WC/RF/UniPC的 **18条完整36更新小权重CPU路径**，含三组布局的保留A1/A2变体、F19原布局、saliency OFF及计时器ON，均覆盖flow OFF/ON。A2实际进入原生产PolicyOwner，无回退、完整更新计数正确。计时器ON/OFF逐步guided、最终latent、完整cache/buffer/solver摘要精确一致；固定F19的saliency OFF/ON逐步guided与latent精确一致。这是4层tiny权重的数值和接线控制，没有实际Cosmos权重、VAE或新视频质量结果。

计时器实际捕获19个D、6个A、11个C，144次浅层块、84次输出头（含12个额外A头）、34次OSI；flow ON捕获46次光流、92次warp，其中A额外支付候选warp。完整调用数保存在回执；CPU耗时不用于GPU速度预测。B1分析器通过合成12状态/10比较的真实文件I/O、SHA拒绝、跨输入隔离和CFG代数控制，真实B1比较仍为0。

机器产物：[时延审计](../../../reports/cara_f19_zero_gpu_r1_20261103/timing.json)、[完整候选/逐步来源/alpha](../../../reports/cara_f19_zero_gpu_r1_20261103/candidate_layouts.json)、[B1缺口记录](../../../reports/cara_f19_zero_gpu_r1_20261103/B1_delta_hold.json)、[输入与源码绑定](../../../reports/cara_f19_zero_gpu_r1_20261103/receipt.json)。[测试源码](../../../tests/test_cara_f19_zero_gpu_r1.py)与[CLI](../../../scripts/cara_f19_zero_gpu_r1.py)可复核。

用户提出的LPIPS≤0.27可继续作为下一张卡的候选目标；它相对真实F19-A1的0.231499是约+16.63%，不是1.1倍。三项原质量门也没有因本次CPU探索而被清除。本次没有注册或报价新GPU卡，没有验证“剩余19GPUh”；未来整卡范围、完整费用与fresh准入另定。本分支不改正在准备的C1、旧P1/P0终态、原冻结或保护输入。
