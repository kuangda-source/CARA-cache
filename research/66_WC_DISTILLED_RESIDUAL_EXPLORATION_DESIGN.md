# WC-D：可预测缓存残差与条件专家蒸馏的初期探索

日期：2026-10-02（北京时间）；版本：v0.1；总计划：v1.4 条件分支；状态：**DESIGN_ONLY / PROPOSED**。本次交付为方案与实验卡，尚未采集新标签、拟合学生、训练门控或运行 GPU。

讨论来源：[蒸馏专家化方法探讨](chatgpt-conversation://6abe8c6d-4ad8-83e8-b04e-b5b45c7274b0)。已读取完整两轮，采用第二轮对可预测性、直接先例与计算粒度的修正。对话是研究输入；一手资料核对层级见[来源清单](../manifests/plan_update_sources_distillation_20261002.json)。

**接续约束：先完成当前冻结工作及审计，再选择是否分配一个 WC-D 窗口。** [WC-S](55_WC_SPARSE_COMPUTE_COMPRESSION_DESIGN.md)和[WC-H](65_WC_HIERARCHICAL_PROVENANCE_LIFETIME_DESIGN.md)保留原顺序；WC-D 不要求稀疏内核先成功，也不自动替换主线。复用同状态 shadow、实际 CFG/采样器接口和资产，不重跑 F0/F1。首批执行说明见[WC-D首窗口卡](../plans/CODEX_FIRST_WINDOW_WC_DISTILLED_RESIDUAL_20261002.md)。

## 1. 研究问题与预期交付

主问题：**在实际 WorldCache 可跳过的深层计算中，能否用已经可获得的廉价状态预测一部分缓存误差，并把这种纠正换成更少完整计算；相同阶段与缓存年龄内，是否仍需要可识别的不同纠正规律？**

证据顺序：残差结构 → 廉价可预测性 → 单纠正器闭环 → 双专家互补与可路由性 → 同质量真实提速。首轮不预设“运动专家”“物理专家”，不训练多个完整小 Cosmos，不同时加入稀疏注意力、少步蒸馏、量化或 OMR。

首阶段最小交付是一个能回答“继续单纠正器、进入双专家、改善观测、还是暂停当前位置”的结果包。PCA 高解释率、低训练损失或 oracle 路由胜出，均不能单独支持论文或部署结论。

## 2. 已有证据与直接先例

当前仓库已完成 W1 同状态/固定 schedule 诊断及 S0/S1 成本、实际 QKV 对照。CAL8 只有机制信号，视频代理评价未一致改善；QKV 四组合没有全输入统一可用配置。**这些结果没有验证 WC-D 的可预测性或专家化。** QKV 和 W1 聚合误差也不是完整蒸馏数据集，需要先审计是否保存了同状态目标与因果特征。

| 一手工作 | 已覆盖的内容 | 本计划的必要对照 / 边界 |
|---|---|---|
| [DisCa](https://arxiv.org/html/2602.05449v2)，§3.3 | 轻量预测器结合缓存、当前输入和时间/条件预测昂贵模型输出 | 单预测器必须使用同样充分的廉价信息；“蒸馏+缓存”不是新点 |
| [LESA](https://arxiv.org/html/2602.20497v1)，§3 | 按阶段配置专家，并进行真实特征引导与闭环自回归训练 | 加入 time-conditioned single 与 stage-only 双专家；闭环训练不是独立新意 |
| [OnlineCache](https://arxiv.org/abs/2607.29398)，摘要 | 联合学习动态缓存策略与纠错器 | cache/correct/full 路由本身不是新点；不默认复现整套 RL |
| [LinCa](https://arxiv.org/abs/2608.17973)及[官方仓库](https://github.com/QHR69/LinCa) | 可学习可逆分解、分量匹配预测阶数 | 分解与恢复已有先例；可逆映射不保证预测无误差 |
| [SVD-Cache](https://arxiv.org/abs/2601.07396)，摘要 | 区分主要子空间和振荡低能量分量 | 文中正交残余不是本项目的缓存预测误差；低能量不等于易预测 |
| [WorldCache](https://arxiv.org/abs/2603.22286)与固定实现 | 内容感知缓存与完整深层刷新 | 用真实可跳过的计算组做部署单位，不能假设 token 精确重算可独立执行 |

目前潜在差异只是待证假设：**同阶段、同年龄内的条件纠正规律，以及由廉价信息预测的纠正收益/风险，是否超过充分条件化的单学生和阶段专家。** 只有结果成立后再收敛贡献；没有“无人做过”或预期加速倍数的承诺。移植版方法需标为 adaptation，不能称官方 Cosmos 复现。

## 3. 数学对象、作用位置与信息边界

### 3.1 在真实接口定义标签

第一版复用 `same_state.py` / `shadow_forward.py` 的深层整体 skip 位置。固定 WorldCache commit `60a486df6d2e6d2aa3c21815895aac157a88e95d` 和 `manifests/upstream.json` 的模块 SHA；实际 hook 必须再次逐 hash 审计。

令 h_n 为当前同 CFG 分支、前两层 probe 完成后的输入；Y_n 为从该输入执行余下深层得到、进入 final_layer 之前的 hidden；P_n 为同一状态上官方 WC 完成外推与 flow-warp 后、同一插入位置的预测 hidden。标签为：

$$R_n=Y_n-P_n,\qquad \widehat Y_n=P_n+G(S_n).$$

这里 R 是**缓存预测误差**，不等于 upstream 的 `residual_cache = hidden - ori_x`。第一版纠正在原 warp **之后**加入，不把 post-warp 标签拿去训练 pre-warp 纠正器；不删除现有 warp。不把当前 Native 轨迹的 Y 减去另一条学生轨迹的 P。

Shadow 从同一 h_n 重算深层，仅为标签/评分；不得更新部署历史、anchor、WC 判据、solver history 或 RNG。请求、条件、模型/expert、CFG 分支变化要 reset；缓存 counter 的历史 70-call 周期照旧记录。纠正输出属于 approximate state，不升级 true full anchor。

### 3.2 可压缩与可预测分开

对给定廉价信息 S 的平方误差有精确分解：

$$\mathbb E\|R-g(S)\|^2=\mathbb E\operatorname{tr}\operatorname{Cov}(R\mid S)+\mathbb E\|\mathbb E[R\mid S]-g(S)\|^2.$$

减去已知 P(S) 不改变条件协方差。条件期望与协方差用于解释信息不足和模型不足，**有限数据上的拟合失败不能证明 Bayes 不可预测**。

以训练集拟合通道基 U∈R^{2048×q}，UᵀU=I；令 μ 为训练集残差均值：

$$G(S)=\mu+Ua_\psi(Z(S)),$$
$$\|R-\mu-Ua_\psi\|^2=\|(I-UU^\top)(R-\mu)\|^2+\|U^\top(R-\mu)-a_\psi\|^2.$$

第一项衡量子空间表达能力，第二项衡量系数预测；两项都在未用于拟合 U/μ 的场景上测。真实系数 Uᵀ(R−μ) 是 **ORACLE_DIAGNOSTIC**，不允许进入部署输入。额外报告 μ-only，防止把平均偏置收益误认为复杂结构。

线性基线解带偏置、训练集标准化后的 ridge regression；按场景/轨迹等权，实际用线性求解而非显式求逆。均值项与零纠正也参与 CAL 选择；若均值易伤害则使用 μ=0 的候选。神经网络不作为首个前置条件。

### 3.3 输入表与廉价成本

| 输入组 | 可用信息 | 首版实现 / 限制 |
|---|---|---|
| Z-H 历史 | 最近两个同分支真实 anchor 的 probe/输出摘要与差分 | 不足两个 anchor 时 full；只用真实刷新样本建立 anchor |
| Z-T 时序 | τ、τ²、实际 Δτ、分支有效 age、anchor gap、phase | 全部学生含时间；跨 CFG 调用不冒充本分支一步 |
| Z-X 当前 | 当前 probe、probe−anchor probe、ori_x−anchor input 的固定16维通道投影 | 三组共48维；probe 是官方已支付的两层，投影/读写仍收费 |
| Z-P 主体 | 当前 P、最近两个 true residual 的固定16维投影 | 与 Z-X 同一个固定正交随机矩阵；合计48维，矩阵seed17事前冻结 |
| Z-G 位置/全局 | 归一化 t/h/w 坐标、已有全局漂移/运动摘要、缓存身份 | 仅使用 skip 判定前已存在或明确计费的统计；文本条件由已条件化的 probe 隐含携带 |

历史组的固定投影只取true anchor时保存的probe/输出/输入；当前Z-X/Z-P在历史-only消融中全部移除。比较历史+时间、历史+时间+当前输入、完整上述输入；模型维度由 schema 确定，固定投影不从测试数据学习。无当前深层 attention entropy、真实残差范数、当前教师系数、未来帧、最终评分或部署时新算的 dense QKV。新增条件池化若必要，作为一次单独观测消融，不能暗改第一版。

该模型按 token 预测共享通道基系数，但**整次深层 skip 仅执行一个纠正模型**。不做 token 级昂贵路由。全局 gate 使用廉价池化统计；全 token 投影/恢复的 O(Ndq)、approximate state 和额外 anchor 输入内存均计入成本。

## 4. 数据、划分与采集设计

### 4.1 两层规模，先小后大

| 集合 | 建议规模 | 用途 / 约束 |
|---|---:|---|
| TECH/CAL8 | 已消耗8场景，seed0 | 接口、储存与成本 smoke；不能作独立泛化证据 |
| FIT | 新24场景，seed0 | 拟合 U/μ、特征归一化、学生；四任务域尽量各6 |
| CAL | 新8场景，seed0 | q/模型/正则/阈值/成本权重选择；四域尽量各2 |
| CONF | 新8场景，seed0/1 | 冻结后确认与域间失败审查；四域尽量各2 |

40个新场景是目标容量，不是首窗口必须全跑。D0先核对 PAI-Bench 现有输入和历史使用表，再按 `SHA256(source_scene_id + "WC-D-v0.1")` 排序、域内分配，产出 frozen split manifest。近重复首帧/同原视频/同场景动作变体作为同一 source_scene 分组；所有 seed、token 和步骤跟随该组，不跨 FIT/CAL/CONF。确切 IDs、prompt/input SHA 与使用状态在 D1 前冻结，未完成清单不得 launch。

首个标注批次仅 FIT 前8（每域2），CAL先4（每域1）；其余在成本与初步可预测性有信号后补齐。初始小 CAL 反复使用会消耗开发资格，不能随后包装成 CONF。CONF 接触结果后若回调方法，该集转 DEV，并另立确认集。

### 4.2 固定协议与采样

沿用当前 Cosmos-Predict2.5-2B、BF16、93帧、432×768、16fps、guidance7、实际 FlowUniPC/Karras：请求35步，36时间点/72 CFG calls。不是论文 Euler 复现。各臂同 source、权重、seed、输入、offload 与 guardrail；不因拒绝换成有利输入。新分辨率/长度留 D6。

沿官方 WC 轨迹，在实际 solver 执行序号的早/中/晚三等分内，每分支按出现次序选前两个**非强制首尾、满足两个真 anchor 的实际 skip**：目标每轨迹≤12个带 shadow 标签的 calls。无合格 skip 则如实记缺口，不强行制造 skip；若缺某阶段，另建更强缓存强度的诊断卡并记录协议变化。shadow 全 token 算 Y；每个 call 用固定seed29在24×27×48网格分层抽2048 token存 R 和输入，不按残差大小抽好样本。

离线选型采用抽样 token，但入围后的 D3/D5 对所有 token 计算误差/输出，并单列大残差与空间边界失败。不能把采样 token 结果直接外推成整 hidden/视频质量。完整 native reference 仅在配对闭环评价需要时生成。

### 4.3 数据回执与规模

每条记录至少有 source_scene/request、input SHA、source/model SHA、solver index/τ、WC counter/cycle、CFG branch、true anchor IDs/τ/age、scope/post-warp 标签定义、P/Y 来源、token indices、dtype/shape、Z字段及可用时刻、采集 wall、拒绝/异常、文件SHA。教师目标进入独立标签目录；部署输入构建器不能读取该目录。

真实 hidden 每个张量约31104×2048×2=121.5MiB。完整 Y/P/probe 不逐 call 全存；2048-token BF16 R约8MiB，P/Y只对固定校验 token和≤2个接口 smoke calls保留。按40轨迹×12call估算，R抽样约3.75GiB，特征约0.1–0.3GiB；先申请≤10GiB标签存储软额度，另计视频和闭环状态快照。完整双分支 hidden驻留、额外历史输入可能增加数百MiB显存，D0用实测峰值决定；磁盘容量与GPU准入分开报告。

大张量、权重、视频和连接信息均留 ignored outputs/cache，Git只存 manifest、hash、小汇总和卡；哈希不替代可访问资产。

## 5. 初期实验卡与依赖

所有卡当前为 PROPOSED，不是已批准/已完成。每次执行从卡复制并冻结 run_id、parent、source/config/data hash、真实预算与timeout、唯一主要改动、控制、输出目录、失败语义；实现提交与采样器合同检查后才由唯一 GPU submitter提交。建议额度见第9节，不构成执行授权。

### D0 — WC-D0-INTERFACE（parent：W1 same-state / S0）

**问题：** post-warp同状态标签和廉价输入在真实skip位置能否严格隔离？只做CPU准备与旧资产审计，建议CPU≤2h、GPU0。读固定源码、现有同状态 hook、CAL8 manifest和历史使用；列可复用/缺失的 tensor，不重新生成视频。

必须检查：零纠正回到原输出；predictions先于truth；开启诊断不改skip trace、输出、历史、RNG；两CFG/reset/counter边界；标签目录对部署不可见；finite/shape失败使full或报错，不能隐式继续；还原完整 UniPC history而非仅latent。拟定 split/token schema、成本估计与存储需求，先验证准确性再开发GPU collector。

输出：`outputs/wc-d0-interface/<run_id>/`；Git汇总 `reports/wc_d0_interface.json` + `manifests/wc_d_split.json`/`wc_d_label_protocol.json`（尚未创建）。只有CPU证据则标 CPU_CONTRACT_ONLY；真实无扰动结果须 D1 paired smoke后才写 VERIFIED。

### D1 — WC-D1-LABEL（parent：D0）

**唯一变化：** 添加受限shadow标签采集，不部署学生。先1个TECH轨迹observer OFF/ON配对smoke验证原输出/trace（确定性协议下hash），再 FIT前8+CAL前4，≤12 labels/轨迹。shadow成本、load、失败、flush全部收费；时间超额时以未完成批次收尾，不自动减少预注册域覆盖后宣称完成。

建议GPU cap4h，含smoke与采集；执行前按D0实测估计缩成可覆盖的有界卡。输出 `outputs/wc-d1-label/<run_id>/`、`reports/wc_d1_label_summary.json`，列missing阶段/CFG、接口对等与磁盘实存。标签或无扰动不成立即 TECH_BLOCKED，不进入拟合/部署。

### D2 — WC-D2-PREDICT（parent：D1）

**主问题：** 残差低秩是否转化为廉价预测？默认compact CPU离线拟合，不加载teacher、不改主干；预计CPU≤4h，若改GPU训练须单列额度与范围。训练集场景等权streaming covariance/SVD；比较q∈{16,32,64}。

对照：零纠正、μ-only、已有scalar/shrink、同输入低秩线性、time-conditioned小MLP、oracle projection；另做同容量直接预测Y的低秩学生，检验残差参数化的有限容量收益。直接Y学生分别拟合其train-only基，不用弱输入人为削弱对照。

线性λ∈{1e−4,1e−2,1}（Z仅FIT标准化），每输入组3×3个有限拟合；MLP仅在最佳线性仍存在明显可预测缺口时，隐藏128、SiLU、输出q，AdamW lr1e−3/wd1e−4，最多20epochs，FIT trajectory等权batch，CAL early stopping patience3，初始化seed{17,29}。q和输入组合先由线性CAL选，MLP不重新全组合扫。真实mean/subspace oracle分开记，损失都在原2048维R上算。

输出 `reports/wc_d2_predictability.json`：η、rank谱/重建、系数误差、各域/phase×age×CFG、害处率、消融、总/激活参数、拟合cost。最佳模型在独立场景上有预测信号才进入D3；投影好而预测差只支持改善观测/函数的一次修订，不自动增专家。

### D3 — WC-D3-FIXED（parent：D2）

**唯一主要变化：** 在官方WC同一冻结full/skip schedule加入最佳单纠正器。先CAL4配对 Native / WC-replay / WC-replay+G 三臂，随后条件成立补CAL8。固定schedule来自独立官方WC预运行：先看控制轨迹，不能以候选结果选调用；候选漂移后仍按相同同分支索引执行，并保存实际trace。

不开动态gate，不减少full；按此设计只能首先检验质量与稳定性，不宣称比WC更快。保留最简单有效μ/linear对照；MLP只有明显离线优于linear才加入。必要的clip/scale只在CAL选择{0,0.5,1}，必须计为方法参数，所有模型给同等选择额度。

全token、合成CFG后的velocity、每步latent与Native偏移、最终视频保真/代理质量/运动/闪烁/任务响应均记录；同schedule局部误差改善而最终退化→MECHANISM_ONLY。output：`outputs/wc-d3-fixed/<run_id>/` + `reports/wc_d3_closed_loop.json`。建议GPU4h单窗口，按实测分批；不隐去guardrail拒绝。

### D4 — WC-D4-SPECIALIZE（parent：D2；部署依赖D3）

**主问题：** 相同phase/age内专家是否互补且可辨认？可以先在D1标签上做离线诊断，只有D3单纠正器可用才部署；默认CPU≤4h，不新增教师采集。K固定2，不命名功能，q/特征沿D2冻结。

两专家共享U和同架构小系数头；stage-only双头按实际36个solver执行点的前18/后18分配，均获得充分时间/age信息；条件双专家初始化用每个FIT call的标签系数池化摘要k-means（seed17），最多5次误差软分配/头更新；软分配以whole-call聚合误差生成，同call所有token共享分配权重，温度按FIT误差尺度固定，CAL不反复改簇数。FIT内按场景做out-of-fold专家误差，训练gate时使用这些误差生成soft targets，避免用训练内拟合优势制造路由规律。若OOF各折头/簇身份无法对齐，退回固定FIT-head/train-gate分组协议并记录代价，不拼错误标签。

gate为池化Z→隐藏32→2输出，只依赖廉价信息；推理先选一个头再执行，不跑两个头挑最低真误差。第一版头仅ridge时用weighted solve；不直接套用EM的理论保证。部署按整skip call选择，oracle损失必须也按整个call聚合后取min，**不能token级oracle对比call级gate**。

对照同时包含：充分条件化single（匹配每次激活成本）、较大single（匹配两头+gate总参数）、stage-only two-head、conditional two-head、whole-call oracle；报告真实latency/驻留显存/训练成本。若总参数匹配single达到同等收益，不能只凭小single对照声称功能专家化。

报告同phase×age层内交叉优势、专家使用率/塌缩、L_single/L_oracle/L_gate、router regret与gain capture；oracle包含真值，只作离线上界。output：`reports/wc_d4_specialization.json`。只有learned gate实获超出stage-only/single的收益才考虑双专家D5，否则保留单纠正器。

### D5 — WC-D5-FRONTIER（parent：D3；双专家另需D4）

**主问题：** 纠正收益能否换成更少完整计算？先CAL有限扫WC阈值{0.75,1,1.25,1.5}×当前阈值，对WC与WC+single/G各给相等额度。保持原必要dense/reset/首尾位置；不能凭缩减full次数推断同质量。入围后冻结≤2个重叠实际时间工作点；新增动态cache/correct/full只作为条件扩展，不同时改scheduler网格。

如要学gate，离线预测各动作的误差/纠正收益与风险；标签 $b_k=\|R\|^2-\|R-G_k\|^2$，而非仅真实残差大小。采用CAL校准的保守风险上界/经验分位数，未经独立校验不称质量保证；nonfinite/OOD/不够anchor/超age时full。gate、投影、恢复、搬运、同步全部计费。

配对比较Native、调优WC、WC+最佳single、条件入围双专家；若相关可学习缓存的代码/模型不兼容，至少做stage-only和充分条件化single，并将跨论文性能排序标未知。每配置2warmup/3clean repeats，预固定交错顺序；诊断关闭、同硬件/offload/输入，冷启动单列。time-matched容差±5%，quality-matched判据见第8节；没有重叠点不宣称曲线支配。

CAL通过后冻结全部参数，在CONF8×2seeds上确认，先pilot允许小批次筛查但不改CONF定义。output：`reports/wc_d5_frontier.json` + 所有video/trace/hash回执。建议GPU≤8h，按实际成本申请，超过上限拆成明确未完成窗口；不以省略强基线保证做完。

### D6 — WC-D6-ONPOLICY（parent：D3/D5，条件修订）

只在离线成功、闭环失败或age外推退化的明确诊断下展开：用FIT学生实际访问状态采同状态shadow标签，最多一次聚合/重拟合；所有on-policy状态保持在原split组，不能从CONF取训练标签。教师不刷新学生缓存，影子开销列训练预算；参考[DAgger](https://proceedings.mlr.press/v15/ross11a.html)的分布覆盖思想，不声称其保证直接适用于扩散。

修订后先CAL复验，CONF若已使用则需新确认样本。随后选不同缓存强度或一个官方支持的更长长度验证范围，不能一次同时更换模型/任务/长度。建议GPU≤4h另立scope；output：`reports/wc_d6_distribution_shift.json`。一次针对性修订仍无闭环或净成本收益，则暂停当前分支，保留假设边界。

## 6. 指标与初筛门

$$\eta=1-\frac{\sum_{\mathrm{heldout}}\|R-\widehat R\|^2}{\sum_{\mathrm{heldout}}\|R\|^2},\quad L=\mathbb E\|R-\widehat R\|^2.$$

η可为负，不能截断。同时报告energy-weighted aggregate与scene等权η、绝对MSE、cosine/幅度、逐call harm率；分母接近0者依训练冻结epsilon单列，不删坏样本。置信区间按source_scene bootstrap，不按token/frame独立计数；小pilot只筛查趋势。

以下数值是**本项目建议的筛查阈值**，不是理论定理或文献验证；执行卡冻结后若修改，先版本化并在新数据上评估。

| 门 | 建议标准 | 不通过的解释与处理 |
|---|---|---|
| 表达能力 | q≤64在新场景捕获≥80%原残差能量（均值单列） | 不是自动失败；若单全局基差，最多一次phase/age局部基诊断 |
| 廉价预测 | CAL scene等权η≥0.20，且胜最强简单对照，至少3/4域有正方向 | 进入单纠正器闭环；不足为INCONCLUSIVE/NO_GAIN_IN_SCOPE，非Bayes不可能 |
| 单纠正器稳定 | 大部分场景全token/velocity误差改善，最终质量无一致退化 | 内部好而视频坏标MECHANISM_ONLY，优先D6或影响权重诊断 |
| 专家必要性 | learned gate损失比最佳single与stage-only低≥10%，至少两种init同向；各专家≥10%calls，存在同phase/age交叉优势 | 塌缩/一头通吃保留single；使用均匀不等于专家化 |
| 可路由 | $\rho=(L_{single}-L_{gate})/(L_{single}-L_{oracle})\ge0.5$，oracle gap为正且超过噪声 | oracle好/gate差先改善廉价观测，不增K；gap≈0则ρ记NA |
| 净计算 | CAL匹配质量下端到端中位节省≥10%，paired区间方向支持且高于计时噪声 | 仅FLOPs/full次数降低不入围；CONF仍只有限范围确认 |

完整数学链允许一项失败即停在该项；阈值有信号但小样本区间过宽标INCONCLUSIVE，有预算才补最有信息的样本。不能为了通过将80%解释率升级成硬创新条件。

## 7. 下游误差与成本分析

同CFG两个分支分别拟合/评分，并报告真实guidance融合后的velocity误差；guidance7可能放大分支误差。实际final_layer/UniPC下游敏感性只能通过同状态输出、下一solver更新和闭环来测，不能用普通Euler一阶界代替当前多步采样器结论。full fallback只消除当前近似误差，不能回滚已偏离的latent。

若现有完整深层比例f₀，新方案f，完整成本c_F、缓存c_C、探针/路由增量c_R、纠正器平均成本Σp_kc_k，则简化模型的必要成本条件为：

$$(f_0-f)(c_F-c_C)>c_R+\sum_k p_kc_k.$$

同schedule f=f₀ 时新增纠正通常增加时间；它的用途是先证明质量收益，再寻找少full的工作点。实际最终判定用干净端到端wall，不用固定成本公式代替测量。q=32的通道恢复单call约4.08GFLOPs（2Ndq），还要叠加输入投影、读写和launch，不能凭少参数称“零成本”。

一次性准备/标签/训练与部署分别计账，并报告 $N_{break-even}=C_{prepare}/(T_{WC}-T_{new})$ 的同单位估算；若分母≤0则无部署摊销点。跨GPU准备成本先按GPU·s报告，再用明确价格/设备换算，不能混加CPU秒和GPU秒。

## 8. 最终质量与证据等级

沿用固定开发VQA/MUSIQ及video差异口径，记录其repeat/content controls；这些代理不是物理金标准或235B官方Joint。逐scene报告修复/破坏、Native保真、清晰度、时序闪烁、运动幅度、条件/任务完成及guardrail拒绝。运动降低可能抬高稳定性分数，必须单列，不凭“更平滑”判成功。

CAL的初筛质量容差建议：scene等权VQA下降不超过2pp、MUSIQ相对下降不超过2%，任务完成率/拒绝率无明显恶化；同时报告置信区间，波动过大则判INCONCLUSIVE。这只是筛选工作点的经验容差，**8场景不能证明2pp正式非劣**。无法确认任务/运动保持时状态QUALITY_UNVERIFIED，不升级确认。

CONF看结果前根据CAL配对方差登记主指标、非劣界、所需样本与功效；若CONF8不足，结果只PROMISING/INCONCLUSIVE，需要新预算补独立样本，不把“无显著差异”当等价。正式论文需要更充分样本、最接近可学习缓存对照与第二设置，另行规划。人工完整视频审核可在关键歧义处提议，当前不自动启用人工标注/付费judge。

状态沿用TECH_BLOCKED、INCONCLUSIVE、MECHANISM_ONLY、PROMISING、CONFIRMED_IN_SCOPE、NO_GAIN_IN_SCOPE、NEEDS_REVIEW。独立数据支持局部范围才用CONFIRMED_IN_SCOPE；不得写普遍物理提升或通用专家原语。

## 9. 资源与预算窗口

仓库`reports/budget.json`当前记录3.9117525685110333/4GPUh、28jobs，余额317.690753秒；是文件快照，未本次实机核验准入/进程。该余额不是蒸馏额度，原新4GPUh/clean50提案也不转成WC-D授权。本次用户授权设计并上传GitHub，未请求启动实验。

| 窗口 | 建议上限 | 核心交付 | 状态 |
|---|---:|---|---|
| A：D0 | CPU2h / GPU0 | 接口/资产/split/token schema/成本卡 | PROPOSED，仅计划 |
| B：D1+D2 | GPU4h + CPU4h | 小标签集、低秩与可预测性、单学生候选 | 未拨款；CPU拟合也须单列研究范围 |
| C：D3 | GPU4h | 固定schedule闭环，单纠正器是否真有用 | 依赖B信号，未拨款 |
| D：D4 | CPU4h / GPU0优先 | 双专家与stage/single公平离线比较 | 依赖B，部署依赖C；未启动 |
| E：D5 | GPU8h | 至多2预算点、clean repeats、条件CONF | 依赖C/D与成本，未拨款 |
| 修订：D6 | GPU4h | 一次学生状态覆盖/长度诊断 | 条件节点另决策，不计入默认首轮 |

B+C+E累计建议16GPUh，与当前/历史额度不相加；不是保证该上限能完成40场景。每窗口先用实测 $H=G(Nt_{gen}+Jt_{shadow}+t_{load}+t_{eval}+t_{failure})/3600$ 校准；多臂/多seed逐项累加。预留25%机动费用用于提案，执行实际全计，timeout不省略load/失败。剩余不足则交付部分结果与缺口，不自动续预算。

有效工作日安排：D0约1日；D1+D2约1–3日；D3约1–2日；D4按D2/D3结果条件展开；D5另1–3日加评测。GPU排队/资源故障不作为科学失败，不承诺日历一周完成。

## 10. 决策与首阶段结果模板

| 观察 | 结论边界 | 下一步 |
|---|---|---|
| 投影与预测均好，single闭环好 | 支持低成本条件纠正，尚未证明MoE必要 | D5单学生frontier；D4作条件诊断 |
| 投影好、预测差 | 低维可表示，当前信息/函数未识别 | 一次廉价当前观测修订，停止增K |
| 同phase/age双头oracle好、gate差 | 有离线互补，部署不可识别 | 检查观测/路由regret；不称专家成功 |
| gate赢小single但不赢大single/stage-only | 容量或阶段分段可解释收益 | 保留更简单强基线，收窄贡献 |
| 离线好、闭环坏 | 分布漂移/下游影响待诊断 | D6一次有依据修订，不能靠频繁full掩盖成本 |
| 视频更好、同质量不更快 | 质量候选，非额外加速 | 查投影/恢复/阈值与摊销；保留有限用途 |
| 单纠正器充分解决问题 | 单模型就是最小有效方法 | 冻结single，不强行追原MoE叙事 |
| 修订后仍无真实收益 | 当前底座/位置/窗口NO_GAIN_IN_SCOPE | 暂停WC-D，继续已有证据支持的WC-S/H |

结果包统一写：卡/parent/source/config/data、完成/缺失、主假设与唯一改变、对照与调参费、η/分解/专家损失、全token/velocity/视频/quality-time、失败与全部样本、真实成本/显存/磁盘、状态、支持/否定范围、一个下一步及所需新资源。没有运行则所有结果栏UNKNOWN。

## 11. 本次交付与下一入口

本次为DESIGN_ONLY：完整讨论读取、一手近邻核对、D0–D6卡与指标/预算/停止规则、现有总览/队列/交接同步。没有新GPU、学生拟合、标签资产、自动化任务或实验结果。

**最有信息的首个实验是 D1→D2：先测“oracle投影能解释多少”与“廉价输入真正能恢复多少”的差，再决定投入闭环或专家。** 当前主线完成审计后才申请此分支的具体执行窗口；每次先核实是否已有等价数据，避免重复采集。

补充数学背景：[POD/DEIM](https://epubs.siam.org/doi/10.1137/090766498)说明低维表示还需低成本求值；本方案不假设少量真实残差可免费测得。本文公式除标明引用的思想外为研究对象定义/基本代数分解与提案，均非新理论贡献。
