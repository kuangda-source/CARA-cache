# 稀疏刷新动作 P：记录核查与轻量探索设计

日期：2026-11-05。仓库 CARA-cache origin/main `5e762e38`（只读）；基线 /workspace/WorldCache。下文中“估”表示我自己的推算，不是记录里的实测值。其余数字都给了出处。

## 1. 记录核查（TASK 1）

### 1.1 CFG 分支稀疏：用户记忆准确

| 测试 | 内容 | 关键数字 | 出处 |
|---|---|---|---|
| H-T45/48/52 同状态 | 只刷新一支（DC/CD），与 CC、DD 对比 guided MSE | 被刷新那支的误差精确为0。guided MSE 在 S22 处是 CC 的 8.53×/9.39×（Human s2）、12.20×/12.09×（Human s3）、13.73×/13.25×（Common s3）。两支误差 cos 0.945–0.963，交叉项抵消 94.4–96.3% | research/170, 180, 187 |
| 预算匹配终点 | 固定掩码，每支18/17次 full | CFG0 −4.02%、CFG1 −13.39%（LPIPS 变差），PAIRED +0.12% | research/164 |
| B1 保存张量 CPU | 直接混合，即 cond-D/uncond-C | 12/12 变差，为 CC 的 24.2×/32.7× | plans/cara_next_stage_20261103/f19_zero_gpu/REAL_B1_RESULTS_R2.md |
| B1 δ-hold | 只算 cond 支，uncond 取 c−δ，δ 为最近真 DD 的 c−u | 局部 hold/C 为 0.088（隔1步）和 0.113（隔2步），全部更好。对 δ 做线性外推反而差 4.7× | 同上 |
| F19-delta4 完整视频 | D10/14/18/21 只算 cond 支 + δ-hold + light C | 1.969× 提速，LPIPS **0.415019**（F19-A1+lightC 为 0.227395），质量门未过。结论是“本轮不采用CFG单支刷新” | research/874 |

机制：实现中 guided 输出为 v=8c−7u（research/170；plans/cara_cfg_mainline_20261027/01 @`91988f9b`）。误差能量为 64‖e_c‖²+49‖e_u‖²−112⟨e_c,e_u⟩。两支同龄复用时误差高度相关，交叉项把误差抵消掉了。单支刷新让这一支误差归零，同时也破坏了抵消，所以 guided 误差变大。这是去相关造成的，不只是“乘以 w 放大”。

**新发现（代码核查，零 GPU）：F19-delta4 的终点失败很可能来自后续步的缓存污染，而不是 P 步本身。**
- WorldCache 的 full 路径每跑一次 net，就无条件写入 `residual_cache[current_idx]`（worldcache_utils.py L527–531）。
- 在 δ-hold 步，cond 支跑的是真 D，会写入新残差；uncond 支走 light C，残差留在上一个 DD（src/wcomr/cara_f19_speed190_sampling_r1.py L92–97、L117）。
- F19 的布局是 `DDDDDDDDADADADADADADDCCDCCDCCDCCCCCD`（CAL35_MANIFEST_R1.json），P 位置是 10/14/18/21，紧接着的 11/15/19 是 A，22/23 是 C。这些步读到的都是“cond 新、uncond 旧”的混龄缓存，也就是上表中 8–33× 的那种 DC 状态。
- B1 只测了 P 步本身的输出，没测后续步（REAL_B1_RESULTS_R2.md）。research/874 也说“不足以唯一归因”。
- 结论：δ-hold 这种 CFG 分支 P 还没有被干净地否定。**直接混合 DC/CD 已被排除。**

### 1.2 其它已试的部分刷新

| 方案 | 实测 | 结论 | 出处 |
|---|---|---|---|
| P0 / ROTATION_050：在第4/10/16/22层，对50% token 只做 MLP，attention 仍为全量 | 省时 **1.29%**（P0 约1%，M8 八层约2%）。局部误差比 C 低 83–92% | 误差好但省不了时间。实测费用下 DP 永远不选它（0 个 P），H1 掩码中 0PP | research/262, 264, 418；plans/WORLD_CACHE_A_CONFIRMATION_AND_P_RECOVERY_20261011.md |
| L2：第13、19两整层复用旧 block 残差 | 省 **7.1%**（每 pair 约0.47s）。rRMSE 11–38% | 终点 4 状态平均比 C_REPLAY 差 +0.87%，Dense 速度也差 +0.52%，没有一致改善。未并入主线 | research/418, 414, 423 |
| F 频域/浅层特征（RAW/Haar/FFT） | 预测误差更准，但动作选择没变好 | 不是 P | research/418 |
| Q2 部分 query 更新 | **未实现** | — | research/418 §3.3 |
| A（浅层 probe+校正） | 生成器不选 | 相当于“只刷浅层”的 block 子集，已经无效 | 主线背景；METHOD_DESIGN_CARA_CURRENT_20261105.md |

费用规律：Cosmos-2B 有 28 个 block，hidden 2048（net.py L83–85），token 数 24×27×48=31104（research/418 L32）。self-attention 是全 3D 注意力。按 FLOPs 估算，每层 self-attn 约占 68%，MLP 约18%（估）。
- 用这个 FLOPs 模型复算：P0 为 4/28×50%×18%≈1.3%，对上实测 1.29%。L2 为 2/28=7.14%，对上实测 7.1%。
- 所以**真实墙钟费用 ≈ 所跑的 (block × token × 分支) 比例**，只省 MLP 没有意义。

## 2. 候选 P 评估（TASK 2）

D pair 为 6.8595s（research/874）。CFG 是两次串行 net 调用（`cnt%2`，worldcache_utils）。

| 候选 | c_P/c_D | 实现量 | 主要风险 | 判断 |
|---|---|---|---|---|
| **P_δ-sync**：只算 cond 支 + δ-hold，并同步缓存（见 2.1） | ≈0.5（估，单支约3.43s，需实测） | 小：在现有 SpeedReadout 上加一个钩子，并放开 PARTIAL_UPDATES/age≤2 的冻结限制 | δ 龄增大后变差（B1 只测了龄1–2）；有 F19 终点失败的前科 | **首选** |
| **P_k block 子集**：现跑 k 层，其余 28−k 层用最近 D 的逐层残差 | ≈k/28（L2 已验证线性） | 中：需要逐层残差缓存，k=14 时约 3.6GB（估：14×2支×127MB） | 只跳2层误差就已达 11–38%，终点无改善（423）。浅层子集≈A，已无效 | 备选，只做局部探针 |
| token/区域子集（运动 token） | ≈ρ（估）。前提是 attention 也只算 query 子集 | 大：需要 gather query、3D RoPE 子集、全层 K/V 或 hidden 缓存（约7GB 以上） | 驾驶场景有自车运动，背景在 latent 中并不静止。Q2 从未实现 | 本轮不做 |
| CFG 直接混合 DC/CD | 0.5 | — | 已被 170/180/187/164/B1 否定 | 排除 |

### 2.1 P_δ-sync 定义

在 P 步 p，令 r_c、r_u 为两支的 full-stack residual，Δr=r_c^DD−r_u^DD 取自最近一次真 DD。
- **cond 支**：跑真 D，输出为 c_p，并写入 r_c←r_c^p。
- **uncond 支**：不跑。输出取 c_p−δ_DD（与现有代码一致）。新增一步：**写回 r_u←r_c^p−Δr**，让后续 C/A 读到的两支缓存同龄，保持误差相关。
- 对照 P_δ-raw：就是现有行为，不做写回。
- δ 和 Δr 只在真 DD 时刷新，并限定 δ 龄 ≤ a_max。

## 3. 漂移模型扩展（部分重置）

现有生成器的误差为 e_C(t)=s(t)·drift(t, t_D)，DP 在 T≈7.51+6.81nD+0.85nA 的预算下运行（主线背景；参数见 METHOD_DESIGN_CARA_CURRENT_20261105.md）。加入 P 后：

- 费用：T += c_P·nP，其中 c_P 取实测值（预期约3.4s）。
- P 是“带出生误差的锚点”：
  - P 步本身：e_P(p)=s(p)·κ(a)·drift(p, t_D)。a 为 δ 龄（或 1−k/28），κ 由探针拟合，B1 先验为 κ(1)≈0.09，κ(2)≈0.11。
  - P 之后的 C：e(t)=s(t)·[drift(t,p)+κ(a)·drift(p,t_D)]，即部分重置。κ=0 时退化为 D，κ=1 时退化为 C。
- DP 状态从 (t, t_D) 扩成 (t, t_D, t_P)，规模为 36³，CPU 上可以忽略。约束为 a≤a_max，且不允许连续 P。

## 4. 实验

### 4.1 零 GPU（先做）

1. 代码层面复核缓存污染：确认 CARA 编译后的 WC 源码（SpeedOwner 中 WC_PATH 的 AST 变换）同样在 cond-D 后写入 `residual_cache[0]`。再写一个 CPU 夹具，断言 P 步后 C 步读到的两支残差出生步不同（raw）或相同（sync）。
2. 查 B1 包里是否存有 P 之后一步的两支残差和 teacher。如果有，用 CPU 直接比较 raw 与 sync 在后一步的 guided MSE。如果没有，记为缺口。
3. 在 DP 中加入 P，参数用 κ=0.1/0.3/0.5 和 c_P=3.4s，离线生成 R18C 预算（≤132.98s，取自 g17 预注册）下的掩码，确定 GPU 卡用到的固定位置。κ=0.5 仍被选中才有意义。

### 4.2 GPU 探针（≤1 GPUh，估约0.8）

**S1 单状态计时与局部误差（估约0.15 GPUh，含加载）**
- 选 1 个已曝光输入，在 R18C 轨迹的尾部（step 29）处测：D、C、P_δ（a=3）、P_k（k=14、20），每个 1 次预热 + 3 次计时。
- 局部指标为对同状态 D 的 guided MSE。
- 再在 step 30 测 raw 与 sync 两种后续 C 的误差。

**S2 终点（12 段视频 × 约195s ≈ 0.65 GPUh；T_request 参考 F17 的 195.8s，research/874）**
- 使用 4 个已曝光输入，与已有 Native 和 R18C 分数比较（R18C 均值 Alex 0.239914，取自 reports/cara_avslc_minitest_r1_20261105/COMPLETE_RESULTS.md）。三个臂：
  - (b) R18C + P_δ-sync，放在 C29、C32（δ 来自 D26，龄 3/6，加约6.9s）；
  - (b0) 与 b 相同但用 raw，用来检验污染假设；
  - (c) 等费用 R18C：D22 换成 P22、P24（δ 来自 D19，龄 3/5，费用差约 0）。
- P_k 本轮只做局部测试，不出视频。

### 4.3 Go/No-go

**Go**（全部满足）：
1. 实测 c_P ≤ 0.55·c_D；
2. (b) 均值 Alex 低于 R18C，且 ≥3/4 输入改善；每秒改善不低于“加一个 D”的参考值，即 (0.270181−0.239914)/(130.2536−123.3756) ≈ 0.0044 Alex/s（G17_CALL→R18C，布局不同，只作量级参考）；
3. 或 (c) 在 ≤ R18C 的时间下均值 Alex 不劣于 R18C，且 ≥3/4 输入改善。

满足后拟合 κ(a)，正式接入 DP。

**No-go**：
- (b) 与 (b0) 都劣于 R18C → 说明 δ-hold 在完整视频上本身就不成立，CFG 分支 P 彻底关闭。
- S1 中 P_k 的局部误差不明显低于 C（例如 k=20 时 MSE 仍 > 0.5×C），或 P_k 费用偏离线性 >10% → block 子集也关闭。

**机理判读**：sync ≪ raw 说明污染假设成立，F19-delta4 的失败需要改写归因。
