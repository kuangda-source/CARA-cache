# WorldCache后续计划：P-ACR与W3-MixTrend有界增强

2026-10-14。结合引用对话最新五轮、两份新材料与本地417/420/423/424结果修订。425时完成设计接入；随后按现有“依设计自主推进”的目标完成**E0 CPU只读审计与离线系数区分**，见[426](../research/426_WC_P_W3_E0_COMPLETE_ASYMMETRIC_ORACLE_AND_COEFFICIENT_RESULTS_20261014.md)。新GPU/模型前向/自动化仍0，旧停止GPU要求保持。原F/B本阶段结束，旧实验、失败、判据与冻结候选保持。

**最新实际入口：**E0已完成，PA单支执行器/CPU与W3因果标签准备待做。旧16状态上SourcePhase Pu系数held-prompt失真低37.2996%、4/4提示词、14/16点改善，证明条件性局部可行性；不是H1主动D、实际费用或终点收益。PA已预选12个H1状态；W3拟议8开发提示词×8标签，但具体资产/完整卡/forecast尚未冻结。

**2026-10-15进展：**[428](../research/428_WC_ACR_SOURCE_BOOKKEEPING_FIX_AND_W3_CAUSAL_PREPARATION_20261015.md)完整共享前缀80例与W3因果11项服务器CPU已接受，source f1b0da7/550源、43.01秒、原CPU句柄结束/账本不变。只付两次shallow、深算一支的原语已经实现，来源不刷新；修复源码精确的post-counter previous_output写入，旧失败保留。下一为完整H1父接口/非提交式恢复与原父等价，尚未接受此层或实际模型。开发系数和历史差分对照已准备，GPU仍0。

**最新完整父接口/生产范围：[429](../research/429_WC_P_ACR_FULL_H1_PARENT_CPU_AND_PRODUCTION_QUOTATION_NEXT_20261015.md)。** H1非提交式owner已实现，完整CPU32/48/528正在原R3验收；R1/R2合成age7支持拒绝保留，4项守卫通过，真实H1未改。02:14首次查收未结束，已有32个mock文件仅为进度；`p-acr-cpu`按02:20一次查收终态后暂停，不循环查询。后续生产报价建议另登记8父/12状态/每动作1预热＋3正式，共528真实pairs/1056CFG；新增CAD重复和报价CPU/完整forecast仍待，不能与本轮CPU额外528调用混淆。PA1.5GPUh仍只是原建议，不填成实际整卡费用。W3仍缺真实sigma/标签。详见[PA12完整范围](../research/p_w3_e0_20261014/PA12_Production_Controls_And_Price_Scope_20261015.md)。

## 1. 研究组织与执行顺序

**冻结A＋H1主干 → E0材料/决策边界审计 → P单边执行与W3时间趋势小探针 → 配对闭环 → 决定是否并入 → 正式论文五项补验。**

- **成熟主干：**CFG一致廉价读出A、真实动作校准及当前阶段部署。继续用已有证据写作。
- **新P：**只深算一条CFG分支，用其真实创新量补偿另一分支，研究有价值的中间精度动作。
- **新W3：**利用去噪更新的因果历史，直接预测动作的局部误差收益差，研究更好的分配。
- **F/B：**空间Haar/FFT、MLP覆盖率与Block残差复用全部归档，不新增实验或用新名称接续旧假设。

P/W3尚未并入论文主方法。允许组合效应，即使各自局部收益较小，也可在有可解释信号后做完整组合；不要求模块各自先达到任意显著百分比。当前不训练生成器/LoRA，不展开新的长期RL或大预测网络。

## 2. 直接复用的已完成证据

|证据|实际结果|本轮处理|
|---|---|---|
|420效率点|A_NO_P比同批WC节时13.72%、LPIPS失真低11.16%；比RA多2.09秒、失真低9.67%|冻结版本，作为有效低费用对照|
|417冻结确认|四新提示词×17/43，H1八视频LPIPS0.0530368、Native加速1.2681×|不重跑，不用于新候选的独立测试结论|
|420固定归因|MID与固定A正式终态/动作/RGB一致；预热144guided等价；同26D的A比plain均失真低3.5196%，3/4改善|归因已完成，读取原件，不再登记相同矩阵|
|420三λ|都26D/0P，只变A0/5/7；HIGH四场景全帧退化|保留敏感性，不能当宽费用前沿|
|423最终B|16全93帧，L2/C四状态均失真+0.8682%；P父C复放等价，D父A与首纯C不同|归档；沿用“物理CC与实际读出要分开”的检查经验|

完整支持文件：[417](../research/417_WC_FROZEN_CONFIRMATION_FULL50_RESULTS_AND_COST_CURVE_NEXT_20261013.md)、[420](../research/420_WC_FULL60_COST_CURVE_COMPLETE_RESULTS_AND_CONVERGENCE_20261014.md)、[423](../research/423_WC_B_FULL312_COMPLETE_ENDPOINT_RESULTS_AND_READOUT_BOUNDARY_20261014.md)、[424](../research/424_WC_FINAL_EXPERIMENT_CLOSURE_AND_PAPER_EVIDENCE_20261014.md)。已有速度与保真来自不同配置/批次，不能拼成同一个性能点。

H1中档参数fingerprint为`34ef948ed2a309e8b1cae4b72b780c14e21d63383fa1eadcdfc8803c3d5beef8`。H1、A_NO_P、原WC/RA、原配置与来源SHA均不覆盖。新策略另版本、另配置、另输出目录；理论成立、素材存在、CPU通过与视频有效分别记录。

## 3. E0：首先回答可改进空间与素材缺口

E0已完成0GPU，只读历史文件、核对原件身份；任何模型前向或新teacher均属于后续独立卡。已完成12条H1/432步独立J重构、28raw/336张量审计、16pi0状态的48oracle家族与预登记的系数LOPO，详细证据见426和三份E0报告。

### 3.1 决策原因与边界

输出H1每一实际更新的`protected`、`fallback_reason`、`legal_actions`、来源/年龄、`qhat/g/cost/J`、所选动作、次优动作及差值。保护、缺ρ/g、age越界、缺表回退和优化器主动D分别统计；**D31须读取实际reason，不能用步号猜原因**。

对合法C/A/D、同一来源报价、`0<r=qhat_A/qhat_C<1`，令`x=λg²qhat_C`，A胜过C、D的区间为

\[
\frac{c_A-c_C}{1-r}<x<\frac{c_D-c_A}{r}.
\]

这是一步代理边界。存在P、r≥1、零误差或支持缺失时，直接比较全部合法J，不套该区间。记录边界距离与跨提示词变化，不要求新策略必须产生不同序列。

### 3.2 素材审计

逐文件核对各分支C/A/D post-RF velocity、teacher、前置观测历史、来源/实际读出、噪声坐标、checkpoint和哈希；标`VERIFIED`、`METADATA_ONLY`、`MISSING`或`NOT_ON_H1_TRAJECTORY`。

|已有索引|已知范围|尚不能据此推定|
|---|---|---|
|source_phase16原件|16状态、192张量，历史CPU已读全候选/teacher|当前服务器文件存在、连续历史齐全、属于H1主动D状态|
|N1 natural12原件|12状态及分支误差相关统计|每步都有分支输出、可恢复完整运行状态|
|420 full60/417确认|完整终点、动作和评分；正式计时关闭研究复制|已保存每个D步的C/A/分支teacher张量|
|旧F16与B记录|可复用定义/元数据，原探索结果冻结|16点足以训练时间预测器；允许续跑旧F/B|

E0实际核验source_phase16/N1全部28文件和336张量；source_phase64候选Gram/MSE重算一致，原stage/runner/final身份通过。仍无H1逐步C/A/D真值、完整sigma或probe张量序列；原parent-vectors本轮未重读。中档每条17主动D（8–24）、8保护D、1缺支持D（31，age7）、5A、5C；主动评分最小分差0.0106976秒在A/C边界。PA具体12状态清单见[预选manifest](../manifests/wc_p_acr_h1_state_selection_e0_20261014.json)，不以同一步旧pi0代替新H1状态。

素材索引见[source_phase16配置](../configs/wc_source_phase16_full368_production_r1_20261012.json)、[捕获记录](../reports/wc_source_phase16_live_or_terminal_capture_20261012.json)、[N1记录](../reports/wc_math_n1_live_or_terminal_capture_20261012.json)。N1元数据明确有`NOT_SERIALIZED_CHECKPOINT_HASHES_ONLY`；哈希不能当可恢复快照。仅guided向量或标量MSE也不能恢复两个分支。不同轨迹的标签不能冒称同一H1状态。

### 3.3 数据分组

既有CAL用于探索/拟合；旧CONF可用于材料诊断，若进入新模型拟合则记为新版本的开发曝光。旧417对冻结H1的确认身份仍保留，但这些输入不能再次证明新Trend的独立泛化。

新`EXPL_DEV`拟议6–8个提示词，训练/验证按提示词分组，seed作为配对重测；正式`PAPER_TEST_RESERVED`成员在方法确定后冻结，并排除所有已曝光输入。当前提示词清单尚未选定，不提前创建“独立测试已冻结”的回执。标准化、PCA、系数、超参仅用训练组，禁止随机拆同视频步骤到train/test。

## 4. P-ACR：先测输出与费用，再谈来源刷新

### 4.1 数学与监督

对同一实际latent、条件、噪声时间与合法缓存，取实际A输出`bar_v_c,bar_v_u`和两支Dense真值。CFG固定为`8v_c−7v_u`，所有公式作用在相同post-RF velocity坐标。

\[
\Delta_c=v_c^D-\bar v_c,\quad
P_c=(v_c^D,\bar v_u+\eta\Delta_c),\quad
v_g^{P_c}=v_g^A+(8-7\eta)\Delta_c;
\]
\[
\Delta_u=v_u^D-\bar v_u,\quad
P_u=(\bar v_c+\zeta\Delta_u,v_u^D),\quad
v_g^{P_u}=v_g^A+(8\zeta-7)\Delta_u.
\]

令`e_b=bar_v_b−v_b^D`，N为guided张量元素数，q统一为平方误差和/N。离线oracle为

\[
\eta^*=\frac{\langle e_u,e_c\rangle}{\|e_c\|^2},\quad
q_{P_c}^*=\frac{49}{N}\|e_u-\eta^*e_c\|^2;
\qquad
\zeta^*=\frac{\langle e_c,e_u\rangle}{\|e_u\|^2},\quad
q_{P_u}^*=\frac{64}{N}\|e_c-\zeta^*e_u\|^2.
\]

非退化时，`(q_A−q_Pc*)/q_A=cos²(e_g^A,e_c)`。高跨支ρ并不保证创新方向能消除guided剩余误差；η*在8/7两侧都可能有收益，不能以系数的单侧大小筛选。没有创新方向或q_A=0时记录退化情形，不构造无意义比值。

历史系数误估的代价可精确写为

\[
q_{P_c}(\eta)=q_{P_c}^*+\frac{49}{N}\|e_c\|^2(\eta-\eta^*)^2,
\qquad
q_{P_u}(\zeta)=q_{P_u}^*+\frac{64}{N}\|e_u\|^2(\zeta-\zeta^*)^2.
\]

oracle严格离线，不读取当前被跳过分支真值作为在线输入。可部署首版使用训练开发组冻结系数；在线历史更新只能使用过去真实D及可取得的A读出，额外head/统计费用计入。引用讨论中的旧CC三个oracle改善0.52%–9.22%保持其历史身份，不当作新A基线/主动D状态的筛查结果。

### 4.2 状态与对照

先在E0核定的四CAL中预选12–16个状态：H1优化器主动D为主体，A/C位置与较差状态作对照。只按原动作/阶段/来源预选，不能用新终点选择点；强制保护D不视为可替代D。

离线比较C、实际A、双Dense、Pc/Pu的0与1固定系数、开发组冻结系数、oracle。再保留历史CFG差分对照。FasterCache已经利用同一步CFG冗余及历史输出差分，因此单边复用本身不作为原创；基于其思想的简化对照须标`FC_STYLE_HISTORY_DIFF`，不能称官方FasterCache复现。[FasterCache原文](https://arxiv.org/html/2410.19355v1)

PA-LOCAL真实算子探针建议8–12状态，先冻结完整名单与方向/重复/预热。双probe照常付费；分别执行单边deep、实际head/RF与另一侧A修正。随机/RNG、solver、缓存、真实D历史、所有buffer恢复，父输出/动作保持；不提交新的来源，不污染父轨迹。

### 4.3 报价和局部筛查

旧H1报价为C=0.16846秒，A_D=0.33811秒、A_P=0.50777秒，P0=6.17331秒、D=6.25420秒。这是**历史完整CFG对、双probe已付后的报价转移**，不是新clean profile。旧pi0的“C”还可能包括阶段A，必须与H1的普通C分别命名。

新Pc/Pu重新实测，计入A候选头、单支deep/head、跨支补偿、必要同步、维护与系数更新，不能把3.2秒或“快一半”填成测量。报价来源：[冻结H1参数](../manifests/wc_source_phase_absolute_h1_parameters_r1_20261013.json)。

在固定同状态、`c_A<c_P<c_D`、`q_D=0`、`0<q_P<q_A`下，P在某个正权重下严格优于A/D须满足

\[
q_P/q_A<(c_D-c_P)/(c_D-c_A).
\]

旧P0在D源A报价下约为1.367%；这个数不套到新P。对所有合法C/A/Pc/Pu/D报告真实费用—绝对guided MSE下包络及冻结λg²选择，不能用相对teacher RMSE代替q_P/q_A。局部包络不保证终点，也不描述更新后源寿命。

### 4.4 两种执行身份

- **ACR_READOUT：**真实单支计算改善当次velocity；不写真实D历史、不重置源年龄或风险，不承诺生成可复用hidden。可作为首轮闭环版本。
- **ACR_REFRESH：**需新增分支级状态契约，真实计算侧可登记D_c或D_u，另一侧保持旧/近似身份、出生误差与年龄；原联合来源假设须重新审计。第一轮不默认实现此版本。

缓存字段至少包含`true_D_c/u、working_c/u、source_id_c/u、age_c/u、birth_error_c/u、cached_hidden_exists、readout_version`。velocity修正不能反推合法hidden residual。η=8/7时当前guided可不变，若真实来源发生更新，未来状态价值仍须单独检验；输出与来源实验分开。

正交多组系数/双频带oracle可作为以后离线理论扩展；首轮只做全局标量与时间域模型，不新增空间FFT、旧F或Block/MLP稀疏实验。

## 5. W3-MixTrend：预测局部代理收益，检验实际选择

MixLinear原论文用分段时间趋势及低秩频谱建模长时间序列。此处借鉴局部/长期分解，首版用**时间域**模型，不能宣称已实现原MixLinear或其结果直接适用于36步去噪。[MixLinear原文](https://proceedings.iclr.cc/paper_files/paper/2026/file/7db2348b5bfeca620aa7327df815adcc-Paper-Conference.pdf)

### 5.1 标签与一致风险

同一合法状态的绝对guided MSE为q_C、q_A、q_D=0，定义

\[
y_{CA}=g_n^2(q_C-q_A),\qquad y_{AD}=g_n^2q_A;
\quad M_{CA}=\lambda y_{CA}-(c_A-c_C),\quad M_{AD}=\lambda y_{AD}-(c_D-c_A).
\]

它们是**传播加权的当前误差代理收益**，不是已经测得的最终LPIPS反事实价值。g是现有经验传播幅度，使用g²，不重复乘求解器步长。y_CA允许负数。

预测统一的q_A与差值，再重构q_C；非负修复后重新计算有效差值/J，保留修复率，不用互相矛盾的两独立margin作决策。T1/T2首版实现采用等价已加权坐标`r_A=g²q_A,delta_r=g²(q_C−q_A)`，修复r后直接`J=cost+λr`；不得重复乘g²。最终在原合法集合上比较全部J，不用逐级阈值替代完整argmin。

### 5.2 模型与时间坐标

|模型|内容|作用|
|---|---|---|
|T0|冻结H1来源×阶段表|原参考|
|T1|当前漂移/来源/时间＋Ridge，收益差监督|控制改标签与回归容量的贡献|
|T2|T1＋近期均值、EMA、相邻斜率/波动度、短段趋势|短历史增量|
|T3|T2＋小秩时间域长窗口线性分支|局部/长期互补|
|T4|低秩去噪历史时间频谱|独立后续备选，不列首轮自动执行|

窗口L=4/8/16仅为开发候选；使用真实sigma/log-SNR差、前缀mask、来源重置标记。同来源累积差`p_n−p_s`不能当相邻增量方向；若需方向，用真实相邻且坐标可比的p或固定低维sketch。历史时轴为36次去噪更新，不是93视频帧或H/W空间轴。

在线特征只来自当前已付probe与过去状态。禁止当前未算侧teacher、未来probe/动作、最终LPIPS或动作之后才产生的统计。受保护D步骤没有原前置观测时保留mask，不为了特征额外补算而不计费。

### 5.3 数据、选择和评价

旧16状态是π0轨迹上的来源/阶段标签，不能假定覆盖H1主动D边界或足以稳健训练新网络。W3-LABEL优先利用真实D前缀记录C/A候选；这些额外候选head、记录与独立teacher全部计入新卡。非D状态必要时非提交式teacher，保留不同来源/阶段/动作的覆盖，不只取D样本。E0后拟议8开发提示词×10/16/23/25/29/30/32/35八位置，总64标签、完整36步前置标量历史；实际成员、完整父控制/预热、teacher复用证明和总费用未冻结。先T1/T2，有增量再做T3，详见[数据规范](../research/p_w3_e0_20261014/W3_Trend_Label_And_Baseline_Spec.md)。

训练、标准化、系数/超参按提示词分组；参照保留同当前特征的T1与H1，防止把标签改变误当历史贡献。主指标为提示词等权的合法动作regret、边界误判及排序，辅以margin误差。regret在同λ/g/费用下由真实同状态标签重构，不是终点损失。

记录历史采集、模型预测、CPU/GPU搬运和控制全费用。局部预测更准或动作序列不同仅为中间信号，闭环看LPIPS—实际时间。支持/保护规则不放宽，UNKNOWN回退不伪造合法动作；D31若是缺支持，不靠新特征解除它。

## 6. S1：小范围配对闭环与必要桥接

首轮拟议4个EXPL_DEV提示词、一个固定seed；优先选未参与系数拟合的开发验证组。若模型选择已使用该组，它仍属开发，不称独立测试。候选系数/模型/λ在闭环前冻结。因原H1仍有旧P0候选，不能直接删P0再把差异归功于Trend。建议新增同域H1_CAD桥接：

|配置|目的|
|---|---|
|Native完整|本批匹配参考及主计时|
|H1_ORIGINAL|原冻结H1完整身份，含原合法P0|
|H1_CAD|仅将旧P0从实验集合排除的配对桥接|
|H1_CAD＋Trend|同C/A/D合法集合替换估计器|
|H1_CAD＋ACR|原估计器＋新可用中间动作|
|H1_CAD＋Trend＋ACR|组合交互|

这是**24正式＋12完整预热、共36路径的拟议完整卡**，尚未登记/生产CPU验收。比原建议增加H1_CAD桥接，用于排除改变合法集合的解释；若先前E0已有严格同输入桥接，也须在卡冻结前明确复用证据，不能跑后删格。完整费用若超S1建议3.5GPUh，先重新讨论整卡；不执行后缩范围。

首轮可使用ACR_READOUT，实际名与日志均保留readout-only；ACR_REFRESH只有来源接口/CPU/真实D身份通过后才能另登记。原P0不以新名字报价/更新。若仅一个模块有代表性信号，可在**新卡登记前**选择与问题相符的完整对照；不是缩拆已经登记卡。

每路径计入文本编码＋去噪＋VAE及算法维护/预测/单边计算；加载、预热、写盘、评分、取证另列。配对全部93帧，保留失败/拒绝/缺参照。逐提示词时间、LPIPS、C/A/Pc/Pu/D、主动D/保护D、来源年龄、后续成本和峰值显存全部报告。

组合有实际工作点可继续有限确认，独立效果小不自动淘汰；组合也没有端到端增量则停该轮配置并回到已有效A＋H1。具体配置失败、证据不足和方向否定分开，不以单项阈值作总否定。

## 7. 建议预算、卡状态与权限

|阶段|建议GPUh上限|当前状态|
|---|---:|---|
|E0现有资产/边界/数学审计|0|已完成；另有CAL系数LOPO CPU区分，GPU0|
|PA-LOCAL单边输出与真实报价|1.5|拟议状态/对照，名单、调用数、CPU、费用待冻结|
|W3-LABEL必要标签与前置历史|1.5|缺口待E0确定；不是必须用满|
|S1完整配对闭环|3.5|拟议36路径，依前两阶段与来源合法性决定|
|加载/补全/重复/工程修复预留|1.5|共享预留，不是独立自动实验卡|
|合计|**8.0**|建议整轮上限，非授权、非实际forecast或扣费|

每卡真实forecast需包括模型加载、完整父路径、全部预热/重复、teacher/恢复、保存、失败/清理和余量，不能只乘局部算子秒数。不得转用旧13.06GPUh P卡或原9.87GPUh E2的身份/权限。

最新E0服务器只读账本核验：累计79.996377372/cap104.971363333、余24.974985961，前后SHA一致、没有新扣费/预留。若以后为本轮预留8，算术余额为16.974985961，**不是实际扣费**。原新增48窗口不重置、单次严格>8GPUh确认规则保留；当前停止GPU未被8h建议或旧自主规则解除。

目前GPU卡均未选定、未批准、未启动，自动化不恢复。新的完整执行范围/CPU/forecast准备好后，执行权限另按用户直接指令核对；不在方案未具体化时提出开工确认。

## 8. 后续主线总安排

1. **现在：**文档/接续入口、E0及离线系数研究已完成；已有A/H1论文写作可继续。
2. **下一阶段：**CPU准备真实单支执行器与因果T1/T2标签/对照；PA与W3仅共用确定同状态可用标签，不重复teacher或重新跑旧F/B。
3. **有界开发：**完整PA-LOCAL、W3-LABEL各自CPU与费用具体化；经直接权限允许后串行上卡。CPU技术准备可并行，单GPU提交者不变。
4. **候选闭环：**同域参考、各模块与组合，取得实际完整视频/费用证据，保留负结果；一轮结束决定冻结增强或保持原版。
5. **正式论文补验：**强基线48正式＋24预热 → 同26D简单规则/读出 → 最终共同测试160正式＋20预热 → 最终三轮测速30正式＋10预热 → 部署/校准/自动质量；第二骨干另议。这些仍是设计模板，没有生产准备或新GPU授权。

新候选若修改算法/λ/训练素材，重新冻结后使用真正未参与探索的提示词。未完成的正式证据不会因8h增强完成自动取消，也不承诺现有余额覆盖全部模板与第二模型。旧E2-76批准未取得、旧P13h暂缓继续保持；不重问、拆卡或静默替换。

## 9. 下一次接续交付

E0三份交付已完成，位于`research/p_w3_e0_20261014/`：`E0_Decision_Margin_And_Asset_Audit.md`、`PA_Local_Oracle_Feasibility.md`、`W3_Trend_Label_And_Baseline_Spec.md`。PA状态范围已预选；两张新探针的完整父路径/重复/预热/生产CPU/完整forecast尚未完成，不把设计上限填作已验收执行卡。

统一记录`prompt/seed/split、model/sampler/dtype、repo/source/hash、parent_state、noise coordinate、source_c/u、actual_readout、legal_actions/reasons、pre_action_features、candidate_q/cost/J、oracle_only_flags、raw_identity、full_time、93frame_metrics、failures`。控制标签与线上输入分库存储，候选评估不得修改部署状态。

原始材料：[新实验计划](../research/sources/worldcache_p_w3_20261014/WorldCache_P_W3_Enhancement_Experiment_Plan_20261014.md)、[原接续文档](../research/sources/worldcache_p_w3_20261014/WorldCache_P_W3_Codex_Handoff_20261014.md)；本地修订说明见[425](../research/425_WC_P_W3_DESIGN_UPDATE_AND_NEXT_STEPS_20261014.md)。
