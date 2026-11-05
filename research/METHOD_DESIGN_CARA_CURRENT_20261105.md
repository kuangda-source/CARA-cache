# CARA-Cache 当前主方法设计（2026-11-05）

> 给外部审阅者（如 GPT）的自洽摘要：机制、计时、布局生成、已测结果与开放问题。数字一律摘自仓库报告；找不到的数字宁缺毋滥。评价口径以用户最新确认为准。

## 1. 问题与目标

**问题。** 在 Cosmos 视频/世界模型推理中，默认每个去噪步做完整引导更新（Native，36 步实际 updates / 35 requested）。完整路径慢：CAL35 上 Native35 平均 `T_DD ≈ 252.66 s`（去噪＋decode）。目标是在**可接受感知质量**下显著加速。

**评价口径（用户确认，2026-11-05）。**

| 保留 | 作废 / 降级 |
|---|---|
| 同 `T_DD` 预算下的加速比（相对同批或锚点 Native） | D/A 位置与某个手搜布局的重合门 |
| 相对同一 Native 视频的配对 LPIPS（Alex 0.1，全 93 帧） | 用位置重叠代替 outcome |
| F17 仅作手搜参照点，不作“金标准方法” | 事后时间插值、换 mask 来凑预算 |

当前 fast tier 工作点是手搜得到的 **F17-A2 + light C**（约 **1.92×**，见 §4）。原理生成布局（G17 等）的目标是：在相近 `T_DD` 下，配对 LPIPS 不劣于或优于 F17。投稿会议未定；基线对照（Native-k / RA / LeMiCa / TeaCache / MagCache / WC）与 Fidelity-v2、FINAL final16 仍在路线图上，尚未全部冻结到本摘要。

## 2. 方法核心：动作、语法与计时

### 2.1 三种逐步动作

每一步（1-based，`mask[t−1]`）属于：

| 动作 | 含义（实现语义） | 相对成本（量级） |
|---|---|---|
| **D** | 完整 Dense 计算；刷新可复用的残差/状态 | 最贵 |
| **A** | 校正（Correction），带标量 `α∈(0,1]`；保留当前浅层信息 | 介于 D 与 C |
| **C** | 缓存复用（Cache readout） | 最便宜；**light C** 更便宜 |

**light C 定义（F17/F19 族沿用）：** 读出 = 当前 embedding ＋ 最近一次真实 D 残差；跳过当前浅层探针、OSI/光流/显著性。A 仍保留当前浅层信息。末步 36 在现有工作点中仍为完整 D。`partial_updates` 在当前正式臂上为空。

代码入口（相对仓库根）：

- 间隔语法与 layout 编译：`src/wcomr/policy_generator_r1/interval_grammar.py`
- 生产采样：`src/wcomr/policy_generator_r1/production_sampling.py`
- F19/F17 请求与计时绑定：`src/wcomr/cara_f19_speed190_requests_r1.py`（及 companion sampling / `paper_latency_r1.py`）

Interval grammar 把 horizon、受保护的 Dense 集合、最大 source age、最少 A/C 锚点等编成可哈希的 Profile，再展开为逐步 D/A/C 与 α，与运行时验收分离。

### 2.2 计时模型（CAL35 四参数）

论文主时钟是 **`T_DD`**（完整去噪＋decode）。计费/报价另用 **`T_request`**。对 CAL35 四个已测 clean 均值（NATIVE35 / F19_A1 / F19_A1_LIGHT_C / F17_A2_LIGHT_C）做精确插值，得到边际秒：

| 参数 | 值（秒） |
|---|---:|
| shared | 70.735 |
| D | 6.772 |
| A | 0.994 |
| original_C | 0.638 |

light C 在报价里按 **C 边际 = 0** 计入（相对 original C 的差额已由 F19_A1 vs F19_A1_LIGHT_C 标定）。单请求价约：

`T_request ≈ shared + n_D·D + n_A·A + (0 if light_C else n_C·original_C)`。

工程报价再乘中心系数 1.1，并加模型加载/释放各 600 s；工程范围为 −10% / ＋20%。共同质量预算常用 **mean `T_DD` ≤ 132.98 s**（F17 附近快档）。

CAL35 实测锚点（四旧 CAL 均值）：

| 角色 | `T_DD` (s) | 速度比 vs Native | `T_request` (s) | mean Alex |
|---|---:|---:|---:|---:|
| Native35 | 252.657 | 1.000× | 314.536 | — |
| F19-A1 | 149.361 | ~1.69× | 212.389 | ~0.231（历史） |
| F19-A1 + light C | 142.079 | 1.778× | 205.372 | 0.227 |
| **F17-A2 + light C** | **131.653** | **1.919×** | 195.803 | **0.238** |

## 3. 布局生成原理

### 3.1 误差单元：`s(t)·Δv`

单步内容敏感度 `s(t)` 来自 Native vs 局部 guided-C 扰动（sensitivity8：八输入 × 偶数步 8…34 的 latent MSE 比）。漂移 `drift(t)` 为自上次 D 以来的 `Δv` 累积。逐步误差大致：

`e_t = s(t)·drift(t)·[A: (1−κ_A·α) 或带 age 修正]·[light C: β_L]·…`

再经 `log LPIPS = b_group + γ·log E` 连到实测 LPIPS。组截距按 batch:input 分开（H 与 A6000 不可 bit 级混比）。

### 3.2 模型族与当前拟合结论

| 模型 | 要点 | 状态（摘自 principle_fit / principle_refit） |
|---|---|---|
| M0 | 加性 s·drift | LOLO paired ~0.92–0.94；粗结构强、近优区分弱 |
| M1 | run 内 κ_run^(age−1)，κ_run≈0.81 | 误差不在 C/A run 内指数爆炸 |
| M5f | σ^g 倾斜，g≈2.72，κ_A≈0.26 | 旧数据 headline 最优；近优布局 paired 仅 ~0.55；**严重高估长 A 尾** |
| **M0A** | M0 ＋ A-age 罚项：`A因子 = max(0,1−κα) + ρ·α·(age−1)`，ρ≈**0.185** | 唯一在前瞻（不含 G）上把 G19 判为 4/4 最差的模型 |

**β_L（light C 相对代价）仍不确定：** 全量拟合 ≈ **0.514**（倾向 light C），去掉 G 布局后 ≈ **1.115**（短 age 时 A 更好）。这直接决定生成器在“多放 A”还是“多放 light C / 多换一个 D”之间摇摆。

Refit 后（258 点）M0A 再生布局的共同趋势：不再出现超长 A run / A 尾巴；D 在 8–27 间隔放置。全量拟合甚至倾向 0 个 A、把预算换成第 18 个 D。

### 3.3 flat_opt：最优面很“平”，模型却未过 outcome 门

对 6,906,900 个 17D 布局穷举（模型预测）：绝对意义下最优并不平——2% 带内仅 4–24 个、5% 带内 17–298 个；但近优集合在结构上仍多样（与自身最优的自由 D 重叠中位约 5–7/9，与 F17 仅约 3–6/9）。**位置重叠是差代理。**

同时模型未通过 outcome 校验：预测的 F17−F19 排序与实测 Spearman 约 0 到 −0.8，且把 N3 排成最小/次小异常而非 outlier。因此模型最优布局本身不可直接信任，需 GPU 实测。

## 4. 关键实验与结果

### 4.1 工作点与对照（CAL / confirm）

| 实验 | 结论摘要 | 报告 |
|---|---|---|
| CAL35 / F19 族 | F17-A2+lightC：**1.919×**，`T_DD` 131.653 s，Alex **0.238**；均值质量门通过 | [874](874_CARA_F19_SPEED190_CAL35_COMPLETE_RESULTS_20261104.md) · [CAL 分析](../reports/cara_f19_speed190_complete_r1_20261103/) |
| F17 confirm4 | 同批速度 **1.919511×**，`T_DD` 131.701 s，mean Alex 0.236；**原非配对 n=4 非劣未证实**（p=0.300），定性为功效/不确定，不写成方法失败 | [sensitivity8 COMPLETE](../reports/cara_sensitivity8_resume_r3_20261105/COMPLETE_RESULTS.md) |
| Shared25-C | 较早 CAL 冻结主候选（DEV128 完整请求约 246.7 s / 1.27× 量级）；现为独立确认规划项，非当前 fast tier | [702](702_CARA_CAL66_A6000_COMPLETE_RESULTS_AND_FROZEN_SHARED25_C_20261026.md) 等 |

F17 mask（1-based 定义）：`DDDDDDDDADADADADADADDAADAACCCCCCCCCD` → **17D / 10A / 9C**；A25/26 的 α=0.5，其余 A 为 1。

逐输入 F17−F19 配对 Alex 差（confirm 四新输入）：+0.0067 / +0.0039 / **+0.0707（N3）** / +0.0050。N3 是突出 outlier。

### 4.2 sensitivity8（s(t) 与 Δv）

八输入 Native + 112 个 single-C 点收齐；累计实际约 **228.35 GPUh**（本 resume r3 结算 7.57 GPUh）。固定 s·Δv 重建的 D/A 位置重叠门**未通过**（中位 5/9、6/10），该门已被用户废止。完整 s(t) 表与 `native_delta_v.csv` 见报告。

### 4.3 G17 mini-test（原理生成 vs F17）

预注册主终点：G17 vs 同批 F17-A2+lightC，四输入等权 ΔAlex；共同预算 mean `T_DD`≤132.98 s。**科学结论：INCONCLUSIVE。**

| 量 | 值 |
|---|---|
| mean ΔAlex (G17−F17) | **−0.021834**（负＝G17 更好） |
| 95% 描述性 CI（4⁴ bootstrap） | **[−0.052514, +0.008846]**（跨 0） |
| 方向 | 2 改善 / 2 退化 |
| mean Alex | G17 0.276 vs F17 0.298 |
| mean `T_DD` | G17 132.60 / F17 131.75 / tail 132.56（均 ≤132.98） |

逐输入 Δ(G17−F17)：O1 +0.0002，O3 **−0.0584**，N1 **−0.0466**，N3 +0.0175。

G17 mask：`DDDDDDDDDDDDDADADAADAAAAAAACCCCCCCCD`（17/11/8）。G17-tail（D13↔A27 交换）相对 G17 mean +0.004，无一致收益。

**N3 +0.071 路径分解（指定顺序，非独立主效应）：** light C 贡献约 +0.022；丢掉 D27/D30 合计约 +0.053；late A 反而略改善。故 N3 同时有 light-C 内容敏感性与 tail-D 损失。

**G19 / G22：** 更慢，不适用 132.98 快档。G19 四输入均退化（mean Δ vs F17 +0.055）；G22 平均略好但慢（Δ −0.006，CI 跨 0）。M5f 预测排序 G22&lt;G19&lt;G17&lt;F17；实测 mean 排序 **G17 &lt; G22 &lt; F17 &lt; G19**——时间预测准，质量排序不可靠。

报告：[G17 COMPLETE_RESULTS](../reports/cara_g17_minitest_nonfast_r1_20261105/COMPLETE_RESULTS.md)

### 4.4 零 GPU 拟合 / 穷举

| 产物 | 要点 |
|---|---|
| [principle_fit](../reports/cara_principle_fit_20261105/report.md) | 346 点；M5f 等；近优区分弱；N3 无模型可解释 |
| [flat_opt](../reports/cara_flat_opt_20261105/report.md) | 690 万 17D 穷举；最优面相对“平”但结构多样；模型未过 outcome |
| [principle_refit](../reports/cara_principle_refit_20261105/report.md) | +24 G 点 → M0A（ρ=0.185）；β_L 分歧；再生 mask 去掉长 A |

## 5. 正在进行：AVSLC 小测（定 β_L）

**目的。** 固定 G17 的 D 集合，只改 21–35 的 A / light C，并加上 refit 再生的 R18C / R17A，用实测区分 M0A 全量（β_L≈0.51）与去 G（β_L≈1.12）两套冻结预测。

| arm | mask 摘要 | D/A/C | 预测 `T_DD` (s) |
|---|---|---|---:|
| G17_CALL | 中后段全 light C | 17/0/19 | 123.28 |
| G17_A21_24 | 21–24 一带 A，其后 C | 17/8/11 | 130.08 |
| R18C | refit 全量倾向的 18D+C | 18/0/18 | 130.09 |
| R17A | 近 F17+D27 的 17D+A | 17/11/8 | 132.63 |

输入：O1/O3/N1/N3；F17/G17 LPIPS/`T_DD` 复用上一卡（同协议 H 批）。主终点：G17_CALL、R18C 对 F17 的配对 ratio 与两套冻结预测的 MAE（描述性，不重拟合）。预注册报价中心约 **1.389 GPUh**，硬限 1.5。

预注册：[plans/cara_next_stage_20261105/avslc_minitest/PREREGISTRATION.md](../plans/cara_next_stage_20261105/avslc_minitest/PREREGISTRATION.md)

**结果状态（本文撰写时）：** `reports/cara_avslc_minitest_r1_20261105/COMPLETE_RESULTS.md` **尚不存在 → 结果待验收。**

## 6. 开放问题 / 想讨论的点

1. **β_L**：light C 与短 age A 谁更值？AVSLC 直接回答；决定下一轮生成器偏好。
2. **长 A run**：旧数据最大 A-age≈5；G19/G22 外推到 13–15 失败。线性 ρ 是否过度惩罚 age 6–7？
3. **近优布局区分力弱**：headline Spearman 高主要来自“灾难早期 C vs 其余”；competitive 带内 M5f 仅 ~0.55。如何在近 F17 的布局间可靠排序？
4. **n=4 功效**：F17 非劣与 G17 CI 均跨关键决策阈值；是否需要更大确认集或不同终点？
5. **N3 机制**：light-C 敏感性 vs 丢掉 tail D；是否需要内容条件策略（何时禁用 light C）？
6. **基线冻结**：Native-k / RA / LeMiCa / TeaCache / MagCache / WC、Fidelity-v2、FINAL final16——与 CARA 同 `T_DD` 口径对齐的进度与优先级。
7. **投稿会议未定**：方法叙事（手搜 F17 vs 原理生成 vs 二者结合）与实验完备度如何匹配目标 venue？
8. **模型信任边界**：时间模型可用；质量模型在粗结构外不可单独决策——是否改为“生成候选 + 小卡实测”的闭环，而非相信单次最优？

## 7. 文件索引

### 方法与状态

| 文件 | 内容 |
|---|---|
| [本文件](METHOD_DESIGN_CARA_CURRENT_20261105.md) | 当前主方法设计（对外讨论用） |
| [02_CURRENT_STATE.md](02_CURRENT_STATE.md) | 仓库当前状态与规则 |
| [09_NEXT_ACTIONS.md](09_NEXT_ACTIONS.md) | 下一步动作 |
| [858 映射与无标签几何](858_CARA_V1_METHOD_MAPPING_AND_LABEL_FREE_DESIGN_GEOMETRY_20261102.md) | 早期方法映射 |
| [874 F19/F17 完整接受](874_CARA_F19_SPEED190_CAL35_COMPLETE_RESULTS_20261104.md) | CAL35 工作点 |
| [memory/handoffs/LATEST.md](../memory/handoffs/LATEST.md) | 交接快照 |

### 关键结果报告

| 报告 | URL 路径 |
|---|---|
| G17 minitest | [`reports/cara_g17_minitest_nonfast_r1_20261105/COMPLETE_RESULTS.md`](../reports/cara_g17_minitest_nonfast_r1_20261105/COMPLETE_RESULTS.md) |
| principle_fit | [`reports/cara_principle_fit_20261105/report.md`](../reports/cara_principle_fit_20261105/report.md) |
| flat_opt | [`reports/cara_flat_opt_20261105/report.md`](../reports/cara_flat_opt_20261105/report.md) |
| sensitivity8 r3 | [`reports/cara_sensitivity8_resume_r3_20261105/COMPLETE_RESULTS.md`](../reports/cara_sensitivity8_resume_r3_20261105/COMPLETE_RESULTS.md) |
| principle_refit 归档 | [`reports/cara_principle_refit_20261105/`](../reports/cara_principle_refit_20261105/) |
| AVSLC（若已验收） | `reports/cara_avslc_minitest_r1_20261105/COMPLETE_RESULTS.md` |

### 计划与代码

- `plans/cara_next_stage_20261105/principle_refit_report.md`
- `plans/cara_next_stage_20261105/avslc_minitest/PREREGISTRATION.md`
- `plans/cara_next_stage_20261105/g17_minitest/PREREGISTRATION.md`
- `src/wcomr/policy_generator_r1/interval_grammar.py`
- `src/wcomr/policy_generator_r1/production_sampling.py`
- `src/wcomr/cara_f19_speed190_requests_r1.py`

---

*文档日期：2026-11-05（Asia/Shanghai）。仅汇总已入库事实；AVSLC 验收后请更新 §5 并替换“结果待验收”。*
