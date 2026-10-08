# WorldCache 组会汇报｜从缓存残差近似到同配额刷新调度（2026-10-09）

汇报日期：2026年10月9日（北京时间）。已完成的科学数据截至10月8日；10月9日获批的下一张同配额实验尚未执行。本报告覆盖当前 WorldCache 主线，OMR 与独立蒸馏专家项目已分开管理。

## 阶段结论：有明确正信号，研究问题已收敛，稳定端到端优势待确认

目标是在视频生成质量与行为保持要求下，减少重复计算，把有限的完整计算花在更有价值的位置。当前值得继续 WorldCache：官方缓存已在本地实现实际加速；W1 在部分场景改善了终点保真；W3 已发现同配额刷新位置的正例，以及刷新会改变后续计算需求的真实机制。新方法尚未证明跨场景、跨种子的稳定质量—速度优势。

| 方向 | 当前最有价值的证据 | 阶段判断 |
| --- | --- | --- |
| 官方 WorldCache | 三对接受视频的 Native/WC 耗时比 1.476–1.602× | 本地技术复现与实际加速成立 |
| W1 残差增量校准 | 7/8 内部误差改善；七个接受视频 4 改善/3 退化，平均 LPIPS 降低0.439% | 条件性机制与终点保真信号；全局标量方案不稳定 |
| 稀疏注意力/近似刷新 | 算子中位1.219×；整组约省5.33%，完整视频仅省0.29%/1.41% | 局部可行；当前配置净收益较弱且依赖位置与覆盖 |
| W3 刷新调度 | seed0 Human 单点刷新LPIPS改善2.808%、后缀full18→16；同配额46/48交换改善1.444% | 有真实位置/自适应反馈价值，推广性不足 |
| 最新 CFG 四组合 | seed2 CFG0刷新保真+0.515%，但full35→37；联合full仍35、保真−0.453% | 分支相互作用与质量成本取舍清楚；下一步同配额区分 |

本阶段的主要成果是把“缓存更准”“稀疏算得快”“刷新位置更好”拆成可独立验证的问题，减少用局部指标替代最终收益的风险。报告中的正例和负例均保留；没有因单项阈值否定整个方向。

## 研究目标与方法：怎么复用、怎么算、何时刷新

一次生成有两个时间轴：视频中的帧，以及生成算法中的去噪步骤。本研究的缓存主要利用相邻去噪步骤之间的冗余。每次去噪更新会调用两个 CFG 分支；本文 CFG0/CFG1 沿用代码槽位编号，一个分支动作不等于整次去噪更新。

$$
\min_{\pi}\;\mathbb{E}[D(V_{\pi},V_{\mathrm{Native}})]\quad\mathrm{s.t.}\quad\mathbb{E}[T_{\pi}]\le B
$$

上式是保真与预算的研究目标，不把 Native 当作绝对物理正确的真值。额外的成像、动作、语义和物理评价需单独确认。

| 方法层 | 具体做法 | 本阶段状态 |
| --- | --- | --- |
| W1：复用时近似得更准 | 冻结 full/cache 位置，利用当前浅层变化与过去真实 full anchors 修正深层 residual | 全局 scalar-recent 已实际验证 |
| W2：不同区域/层用不同近似 | 考虑时间、空间、通道或层分组 | 做了误差分布诊断；尚未新增分组网络/训练方法 |
| 稀疏刷新：需要算时减少注意力交互 | 在允许的深层用真实稀疏核；敏感层回退 dense，区分近似来源与真正 full anchor | 已做到整组、缓存寿命和完整视频验证 |
| W3：完整计算应放在哪里 | 同状态比较继续缓存 C 与完整刷新 D；再做每CFG配额固定的位置交换 | 当前主执行线，尚未训练收益 Head |

WorldCache 仍执行浅层 probe，再决定深层完整计算或缓存近似；原 warp、缓存历史与计数逻辑保留。稀疏关注单次计算内部的交互，缓存关注跨去噪步骤复用，两者可能互补，但必须看总开销和误差传播。尚未实施新的多模态注意力模块或删除 backbone 部件。

## 统一实验设置、对照和评价

| 项目 | 当前协议 |
| --- | --- |
| 平台 | Cosmos-Predict2.5-2B；单张 RTX A6000；已固定运行源、权重与解码路径 |
| 视频 | 768×432，93帧，16fps；匹配比较共享提示词、seed、初始噪声和生成/解码配置 |
| 采样 | UniPC/Karras：请求35步，实际36次更新/72次CFG；少步Native23请求对应24次更新/48次CFG |
| 基线 | Native完整采样、Native少步、WorldCache多阈值工作点，及每轮匹配的OFF/BASE控制 |
| 局部指标 | 同一个实际状态上的预测velocity与postwarp residual MSE/RMSE；teacher只评分、不写回部署 |
| 终点保真 | 完整93帧CPU FP32/Alex LPIPS；不裁剪、缩放或抽帧；补充RGB MSE/SSIM/92次帧间差分 |
| 其他质量 | MUSIQ成像代理、小模型抽帧开发VQA；保留分歧，不把它们当物理质量最终判决 |
| 成本 | 实际收费包含加载、失败、诊断、输出和释放；取证后缀wall单独报告，避免冒充部署测速 |

样本主要是已曝光开发集 CAL：W1 原8场景/seed0，后续稀疏与W3多集中 Common/Human；新seed是同提示词复验。93帧、104算子输入、72格诊断和严格重复都不等于相同数量的独立场景。尚无冻结未曝光 CONF 上的最终方法结论。

技术一致性与科研效果分开验收：先核对原始文件、动作、状态恢复、自己的CFG历史、solver/latent/RNG、解码与配置，再看质量与成本。安全管线拒绝样本保留在原分母，缺失不补零、不换样。

## 已执行实验总览：按研究问题归纳全部阶段

| 实验阶段 | 设计与覆盖 | 得到什么／对下一步的作用 |
| --- | --- | --- |
| F1技术基线 | 4场景 Native/WC，3对共同接受 | 确认官方缓存可实际省时，建立可运行基线 |
| W1-P0与scalar/shrink试验 | 同状态shadow、旧单AV四点、recent估计对照 | 确认不干扰原路径；旧四点负结果与收缩负结果保留 |
| W1-D CAL8机制 | 8场景×8依赖状态，比较official/scalar/shrink | scalar 7/8联合改善；选择简单增量校准进入生成 |
| W1固定位置完整生成 | 8候选，7接受/1拒绝；MUSIQ和开发VQA | 视频生成可运行，绝对质量代理混合 |
| W1补五个Native参考 | 21个Native/WC/W1视频，全93帧、14对LPIPS | 补齐七接受场景：4正3负，均值改善很小 |
| W1自身轨迹teacher | misc/AV51/AV28，12个同状态观测 | 两个终点负例仍局部改善，排除简单“只在旧轨迹有效”解释 |
| 稀疏R4全104点 | 4调用×26深层，312 dense/matched-full/sparse案例 | 局部加速与层差异；6/23/27保留dense |
| H0整组刷新 | 两CFG的D/MF/S真实deep组+head | 局部误差较低，整组省时约5.33% |
| H1来源与寿命 | D/MF/S来源×age1/2/4；扩至双CAL早晚72格 | 共同漂移比来源扰动大，单纯换来源不能解决复用寿命 |
| 固定/小层组/低频稀疏 | 四输出、六输出和来源位置匹配对照 | 限制full/cache反馈后仍有偏离；减层减频未形成稳定优势 |
| 稀疏位置与早晚2×2 | 固定原掩码，改变S刷新的位置与早/晚两组开关 | 早期额外S破坏更大；后期没有修复早期损失的证据 |
| 在线窗口与公平14输出 | 双CAL窗口23–27；Native35/23、WC0.04/0.06/0.08、stage | 窗口改善相对旧S方案的保真；公平基线下视频净收益仍弱 |
| W3-A同状态C/D | Common和Human，完整恢复后真实动作干预 | Human显示刷新改变终点和未来算量；Common验证原WC动作 |
| W3-B同配额四交换 | 2场景seed0、2父16后缀10视频，固定每CFG配额 | Human46/48正例1.444%；其余三对负结果 |
| D46跨seed与联合CFG | 同Human seed1/2，再同seed2的联合/单槽对照 | seed1 no-op、seed2单槽负例，不能把旧seed0正例当普遍规则 |
| 最新四细胞factorial | 同seed2新完整快照、1父10后缀6视频、四对比一交互 | CFG0小正例但增算，联合回收未来full但不优于BASE |
| 已有记录CPU诊断/下一卡 | 分析分支上下文；固定45/47与46/48四种交换 | 新卡核心与生产CPU均通过；10月9日已批准，文档完成后推进GPU |

实现、导入、状态桥和尾段约束的失败记录及费用均保留。修复后的独立卡只证明修复卡通过，不追认旧卡。组会关注上述科学阶段；逐次运行日志、旧判据与回执可从文末来源追溯。

## W1：浅层增量确实有信息，但终点收益依赖场景

### 方法与局部机制

$$
\hat r_t=r_s+\beta_t(p_t-p_s),\qquad\beta_t=\mathrm{clip}\!\left(\frac{\langle\Delta p,\Delta r\rangle}{\langle\Delta p,\Delta p\rangle+\lambda}\right)
$$

p为浅层probe，r为深层residual，s为上一真实full anchor。scalar-recent仅用过去最近一对full的增量估计beta；当前完整teacher只评价，不参与预测。保持原full/cache位置与原warp，从而把“近似器改进”与“刷新调度变化”分开。固定收缩对照也测试过，未得到同样收益。

CAL8中，7/8场景同时改善网络预测和postwarp residual；场景等权预测MSE降低24.08%，residual MSE降低10.63%。分时间/空间/通道看也有机制信号，尚不足以支持增加分组网络复杂度。

### 七个接受场景的最终保真

| 场景 | WC LPIPS | W1 LPIPS | 相对失真降低 | 改善/退化帧 |
| --- | --- | --- | --- | --- |
| AV28 | 0.389524 | 0.294265 | +24.46% | 93/0 |
| Common | 0.333153 | 0.306939 | +7.87% | 93/0 |
| Human | 0.424745 | 0.390806 | +7.99% | 93/0 |
| industry | 0.532712 | 0.544605 | −2.23% | 13/80 |
| misc | 0.493993 | 0.588302 | −19.09% | 0/93 |
| physics | 0.305083 | 0.278172 | +8.82% | 93/0 |
| AV51 | 0.394325 | 0.457839 | −16.11% | 0/93 |
| robot | 缺失 | W1输出被拒绝 | 不评分、不补样 | 缺失 |

七场景等权平均LPIPS为0.410505→0.408704，平均loss相对降低0.4388%；逐场景相对降低率的均值1.6721%是另一聚合，不能互换。四正三负与两例大退化说明配置有条件性价值，不能用两个原正例或中位数掩盖风险。此前MUSIQ为3升4降；开发VQA为6平1降，等场景−3.17个百分点。

### 自身状态诊断：关键反例仍存在

| 场景 | 自身状态预测MSE降低 | 自身状态residual MSE降低 | 已有终点LPIPS降低 |
| --- | --- | --- | --- |
| misc | +5.69% | +21.78% | −19.09% |
| AV51 | +49.06% | +48.37% | −16.11% |
| AV28 | +9.83% | +1.82% | +24.46% |

三场景在W1自身实际状态观测calls45/46、67/68，teacher不写回，新增生成与旧候选视频逐字节相同，复用已有终点评分。两个负例的局部预测平均误差仍改善，说明局部MSE不足以替代最终目标；具体误差方向、CFG更新及传播机制仍需区分。当前保留W1，不直接上分组MLP/LoRA。

依据：[W1 CAL8机制](https://github.com/kuangda-source/worldcache-omr-experiments/blob/5b9cb14/research/21_W1D_CAL8_RESULTS.md)；[七场景终点](https://github.com/kuangda-source/worldcache-omr-experiments/blob/5b9cb14/research/138_WC_W1_APPROVED_FIVE_REFERENCE_EXECUTION_AND_RESULTS.md)；[自身轨迹teacher](https://github.com/kuangda-source/worldcache-omr-experiments/blob/5b9cb14/research/141_WC_W1_OWN_STATE_APPROVED_EXECUTION_AND_RESULTS.md)

## 稀疏注意力：局部可行，兑现空间与适用位置有限

### 算子、整组与缓存寿命

104输入/312案例中，dense/sparse算子时间比中位1.218931×；相对误差≤5%为92/104、速度比≥1.1为76/104、两项同时满足64/104。层6、23、27在四输入上都超过原局部误差线，因此完整视频配置保留dense回退。104不是独立视频数。

整组deep+head两CFG热重放时间比约1.056×，平均省时5.33%，网络预测相对误差约0.94%。这比单算子加速小：MLP、未替换层、路由、同步与访存仍有成本。

H1用dense-held、matched-full、sparse三来源在age1/2/4重放：首局部18格、扩展早晚双CAL72格的“双字段≤5%”描述性筛查均未通过，dense-held同样失败。扩展中共同velocity漂移约7.25%–40.27%；稀疏来源本身约0.89%–1.73%。说明该范围中共同缓存预测漂移更大，不是稀疏独有的问题，也不能用这条局部线否定最终视频质量。

### 位置与完整视频

固定full/cache掩码、小层组、低频S和相同S次数的位置匹配均已尝试。Human早晚2×2中，仅增加早期两次S，相对官方WC的SSIM由约0.9276降到0.7449；晚期两次S影响较小且没有修复早期损失。该对照包含后续来源与轨迹传播，不能唯一归因于即时注意力误差。

将S限制在去噪窗口23–27后，在线候选相对早期全组S方案的保真明显改善。公平Native参考比较时，Common总流程省0.292%，Human省1.407%；相对Native的LPIPS分别恶化0.078%/0.332%。Common采样区间反而慢1.023秒，表明全流程微小快差不能全部归到注意力。

当前配置实际稀疏覆盖Common为6/35次full、Human为9/38次full，每次仅23个允许层；数量比例不等于时间比例。现阶段暂停扩大稀疏搜索，保留适用条件与开销问题，后续只有在明确省时空间的前提下再考虑组合。

依据：[104点算子](https://github.com/kuangda-source/worldcache-omr-experiments/blob/5b9cb14/research/75_WC_FULL104_R4_CARD_AND_RESULTS.md)；[来源寿命扩展](https://github.com/kuangda-source/worldcache-omr-experiments/blob/5b9cb14/research/80_WC_H1_GENERALIZATION_R1_CARD_AND_CPU.md)；[早晚位置factorial](https://github.com/kuangda-source/worldcache-omr-experiments/blob/5b9cb14/research/98_WC_TIMING_FACTORIAL_RESULTS_AND_EARLY_PROTECTION_NEXT.md)；[净成本分析](https://github.com/kuangda-source/worldcache-omr-experiments/blob/5b9cb14/research/134_WC_SPARSE_COST_CONDITIONS_EXPLORATORY_RESULTS.md)

## 公平基线：已有完整少步与调参WC对照

公平14输出批次包含两次额外D/D一致性控制与双CAL的六工作点。下表是该批固定顺序、各配置一次的完整pipeline计时，不能与早期F1时间跨批次拼接。Native35为视频参考，其零误差是定义。

| 场景 | 工作点 | pipeline秒 | full CFG | RGB MSE | SSIM |
| --- | --- | --- | --- | --- | --- |
| Common | Native35 | 321.262 | 72 | 0（定义） | 1（定义） |
| Common | Native23 | 239.265 | 48 | 0.030541 | 0.594418 |
| Common | WC0.04 | 235.158 | 43 | 0.031040 | 0.583404 |
| Common | WC0.06 | 208.204 | 35 | 0.035744 | 0.566834 |
| Common | WC0.08 | 198.832 | 32 | 0.045488 | 0.515345 |
| Common | WC0.06+稀疏窗口 | 207.597 | 35 | 0.035806 | 0.566432 |
| Human | Native35 | 324.248 | 72 | 0（定义） | 1（定义） |
| Human | Native23 | 241.233 | 48 | 0.091390 | 0.386620 |
| Human | WC0.04 | 237.867 | 44 | 0.047012 | 0.506084 |
| Human | WC0.06 | 217.791 | 38 | 0.058062 | 0.468119 |
| Human | WC0.08 | 199.115 | 32 | 0.058878 | 0.460812 |
| Human | WC0.06+稀疏窗口 | 214.727 | 38 | 0.058046 | 0.468038 |

直接少步是必须保留的强基线：Common中少步在略慢的时间点更接近Native，Human则部分WC工作点更好。没有统一获胜策略；新方法需面对质量—成本曲线，而不是只比默认WC或完整Native。未来部署测速还需重复与公平计时边界。

依据：[公平14输出完整结果](https://github.com/kuangda-source/worldcache-omr-experiments/blob/5b9cb14/research/107_WC_FAIR_CAL_RESULTS_AND_DIRECTION_GATE.md)

## W3：刷新有价值，但依赖位置、种子和CFG上下文

### 两种互补设计

$$
Y_q=L_C-L_D,\qquad Y_t=T_C-T_D
$$

自适应C/D实验从同一完整状态出发，仅改变当前动作，之后两臂使用相同的原WC策略函数。动作引起后续调用数变化是系统总效应的一部分，应完整计费。固定配额实验则保持每CFG完整计算数，只交换位置，回答相同预算下配置是否更好。两者都保留，不用后者单独否定前者。

### seed0：已有真实自适应正例与同配额正例

Human call46单点D刷新：LPIPS 0.424745→0.412819，失真降低2.808%；后缀full两CFG合计18→16。当前动作刷新缓存后，后续计算需求改变。这不是干净速度测量；Common原WC本来就选D，因此该点验证原动作，不算新策略贡献。

| 同配额交换／seed0 | 保持的CFG0/CFG1总配额 | LPIPS相对改善 | 改善/退化帧 |
| --- | --- | --- | --- |
| Common 47/49 | 18/17 | −3.134% | 1/92 |
| Common 48/50 | 18/17 | −9.629% | 0/93 |
| Human 61/63 | 20/18 | −57.343% | 0/93 |
| Human 46/48 | 20/18 | +1.444% | 65/28 |

只有Human46/48这次交换为正，支持位置价值存在；三个负例说明“提前刷新”本身不是可泛化规则。首次尾段约束不可行保留，后续R2只放开干预后原生建议必须相同的错误要求，保留实际固定尾掩码、70 reset和71/72完整计算。

### 新seed复验：旧单槽正例没有简单推广

| 同Human新seed | 原call46与动作 | BASE→REFRESH LPIPS | full总数 |
| --- | --- | --- | --- |
| seed1 | 原D，强制D为no-op | 0.357725→0.357725，持平 | 37→37 |
| seed2 | 原C，可干预 | 0.415138→0.427261，失真升2.920% | 35→36 |

no-op不算策略成功。旧seed0正例与新seed负例都保留；不能合并被选中的旧正例来声称独立确认。由此登记同seed2的新共享状态四组合，区分两CFG分支同时改变的效果。

### 最新四组合：小幅保真正例与计算取舍

| seed2当前动作 | LPIPS | 相对BASE保真改善 | 全程CFG0/CFG1 full | 严格未来47–72 full |
| --- | --- | --- | --- | --- |
| BASE C/C | 0.415138287 | — | 18/17，总35 | 8/7 |
| 仅CFG0 D/C | 0.412999369 | +0.5152% | 19/18，总37 | 8/8 |
| 仅CFG1 C/D | 0.427260689 | −2.9201% | 18/18，总36 | 8/7 |
| 联合 D/D | 0.417017531 | −0.4527% | 18/17，总35 | 7/6 |

完整1父、10后缀、6新视频、同一旧Native、五组严格重复及全93帧评分已完成。CFG0收益为71帧改善/22帧退化，并非每帧更好；当前多一次full后，未来还多一次，因此全程多两次计算。

联合相对CFG0少两次full，但保真退化0.973%；联合相对BASE当前加两次、未来省两次、全程仍35，却没有净保真优势。交互 L_CFG0+L_CFG1−L_BASE−L_PAIRED 为+0.00810424，说明效果不能简单相加；正交互不等于联合优于BASE。

CPU上下文诊断发现：两种CFG0上下文下，call46的已付浅层风险信号和D输出摘要完全相同，而当前缓存组件及下游质量成本效应不同。提示未来决策需要考虑历史上下文，但仅两个依赖条件不足以证明浅层proxy整体无效，不能立刻据此训练Head。

依据：[W3-A Human C/D](https://github.com/kuangda-source/worldcache-omr-experiments/blob/5b9cb14/research/129_WC_W3_HUMAN_APPROVED_EXECUTION_AND_RESULTS.md)；[W3-B同配额四交换](https://github.com/kuangda-source/worldcache-omr-experiments/blob/5b9cb14/research/147_WC_W3_TAIL_ALIGNED_APPROVED_EXECUTION_AND_RESULTS.md)；[D46新seed复验](https://github.com/kuangda-source/worldcache-omr-experiments/blob/5b9cb14/research/151_WC_W3_D46_FRESH_SEEDS_APPROVED_EXECUTION_AND_RESULTS.md)；[最新完整四组合](https://github.com/kuangda-source/worldcache-omr-experiments/blob/5b9cb14/research/158_WC_CFG_FACTORIAL_COMPLETE_RESULTS.md)；[上下文CPU诊断](https://github.com/kuangda-source/worldcache-omr-experiments/blob/5b9cb14/research/159_WC_CFG_CONTEXT_AND_MATCHED_MASK_CPU_RESULTS.md)

## 当前问题与研究判断

- 局部误差与最终目标不对齐：W1两个终点负例仍改善自身状态预测MSE。需要终点/传播视角，不能把局部MSE直接当刷新收益标签。
- 小样本与条件差异：主要为曝光CAL、少量seed；重复确定性与逐帧覆盖有工程价值，但不证明泛化。
- 计算量与速度分开：自适应干预改变未来full是有价值结果；同full数量也不保证同wall，取证耗时不能当清洁部署速度。
- 保真与绝对质量分开：LPIPS测接近Native；MUSIQ、开发VQA的混合表现继续保留，物理、语义、动作保持需补充证据。
- 稀疏净收益空间：覆盖率和非注意力成本限制收益，需要先解释省时来自何处，避免仅凭算子比叠模块。

继续WorldCache，当前主资源投入W3有限区分；W1保留条件性候选；稀疏暂缓扩大。这是依据正负证据调整具体配置优先级，不是把W1或稀疏方向判死。论文主张仍待建立，不能仅以“加稀疏/加一个Head”作为创新结论。

## 下一步：已批准的同配额CFG位置交换完整卡

本轮用户已于2026年10月9日直接批准完整单卡预计2.083 GPUh例外，先形成这份组会文档，再继续实验。卡名 WC-W3-CFG-BUDGET-MATCHED-R1-20261008-A，使用同Human seed2、旧匹配Native、新step22/call44完整快照。CPU完成不当作GPU结果。

| 细胞 | call45/46 当前 | call47/48 下一更新 | 全程各CFG完整次数 |
| --- | --- | --- | --- |
| BASE | C/C | D/D | 18/17，总35 |
| CFG0交换45/47 | D/C | C/D | 18/17，总35 |
| CFG1交换46/48 | C/D | D/C | 18/17，总35 |
| PAIRED双交换 | D/D | C/C | 18/17，总35 |

其余72调用掩码不变：固定原BASE的位置，所有细胞使用各自实际状态，自己的CFG历史合法且finite；原初始化、70 reset、71/72完整尾保留。新原WC父掩码必须与登记掩码一致；不一致则保留条件失败，不能静默换掩码。

完整范围不缩：1新WC父、10完整后缀（四细胞各两重复+OFF1/OFF2）、6新视频、1旧Native、4预定比较与1交互。核心CPU完成4父40后缀24模拟输出、5类回滚故障与104破坏拒绝；生产CPU301载荷、29依赖、guardrail和LPIPS资源均通过。

| 结果可能性 | 怎样解释 | 下一项低成本推进 |
| --- | --- | --- |
| CFG0改善在18/17固定配额下保留 | 支持此位置重分配价值；仍是单已曝光状态 | 冻结候选规则，优先小批新seed/场景复验，再谈独立CONF |
| CFG0改善消失或反向 | 原自适应收益可能依赖后续路由或增算，不能唯一归因 | 利用本批已有状态/动作/全帧记录区分条件，不立即加训练 |
| 联合位置交换优于BASE | 两CFG联合安排有价值候选 | 同时检查最差场景、帧段、真实成本，再有限复验 |
| 固定mask或缓存不可行 | 配置/可比性问题，不算质量失败 | 保留失败与费用，定位合法来源/状态/求解器接线后再登记修复 |

阶段二在这张卡结束后进行：先核对全部重复、实际mask、两个CFG配额、源/资源释放和真实费用，再全93帧评分、独立重算。随后只根据证据选择一项有限确认或区分实验。

阶段三在出现可复验的位置规律后：学习“刷新的终点质量收益与未来成本收益”，先线性/极小预测器，与年龄/时间/原WC启发式等强简单规则比较。监督从同状态反事实产生，避免把局部误差大小当风险真值。训练Head、LoRA、专家或缓存+稀疏组合均为条件后置，当前尚未解锁。重大方向与资源变化共同讨论，不额外引入非必要人工评审。

## 资源、可复现性与组会讨论点

本报告创建前实时服务器账本：累计使用23.702366/50 GPUh，余26.297634 GPUh，60次GPU提交记录（包括技术失败和诊断，不代表60个独立科学实验），无在途。单次超过2 GPUh先确认的规则保持；本次2.082740047 GPUh完整卡例外已获用户直接批准，来自保留旧费用预测并增加保守集成开销的规划，不是实测GPU时长。

文档完成并回读后，按已通过生产源进行同源selected CPU绑定，重新核对目标GPU/共享锁/账本/磁盘，再单次完整提交。GPU释放后自动CPU评分。旧正负结果、旧不可行判据和所有失败费用保留，运行代码不在执行期间改动。

- 组会问题一：W3是否应继续以“同预算终点收益”作为主要候选目标，同时保留自适应未来成本的另一条证据线？
- 组会问题二：若同配额信号保留，先做有限新seed复验再冻结可部署规则，避免当前样本上直接训练复杂Head。
- 组会问题三：是否把W1场景差异与稀疏阶段敏感性作为统一“计算价值”问题的支撑证据，先收敛一个主方法，而不是扩大模块组合？

可用于组会收尾的一句话：我们已经证明有些冗余计算可以省，也找到某些刷新位置会改善结果；下一步要证明，在同一计算配额下，能够稳定把计算安排到更值得的位置。

## 来源与完整阶段索引

依据：[F1官方缓存技术复现](https://github.com/kuangda-source/worldcache-omr-experiments/blob/5b9cb14/research/11_F1_R3_TECHNICAL_RESULTS.md)；[H0整组刷新](https://github.com/kuangda-source/worldcache-omr-experiments/blob/5b9cb14/research/77_WC_H0_MODE_REPAIR_AND_R2_CARD.md)；[固定刷新](https://github.com/kuangda-source/worldcache-omr-experiments/blob/5b9cb14/research/90_WC_FIXED_HUMAN_RESULTS_AND_SMALL_GROUP_NEXT.md)；[小层组与低频](https://github.com/kuangda-source/worldcache-omr-experiments/blob/5b9cb14/research/92_WC_SELECTIVE_HUMAN_RESULTS_AND_FORECAST_WINDOW_NEXT.md)；[相同S配额位置](https://github.com/kuangda-source/worldcache-omr-experiments/blob/5b9cb14/research/95_WC_FORECAST_PLACEMENT_RESULTS_AND_TIMING_FACTORIAL_NEXT.md)；[在线窗口四候选](https://github.com/kuangda-source/worldcache-omr-experiments/blob/5b9cb14/research/103_WC_ONLINE_STAGE_RESULTS_AND_FAIR_BASELINE_NEXT.md)；[下一完整卡CPU与费用](https://github.com/kuangda-source/worldcache-omr-experiments/blob/5b9cb14/research/160_WC_CFG_BUDGET_MATCHED_CORE_AND_PRODUCTION_CPU.md)；[下一轮v5.8设计](https://github.com/kuangda-source/worldcache-omr-experiments/blob/5b9cb14/plans/WORLD_CACHE_CFG_BUDGET_MATCHED_WINDOW_20261008.md)

以上链接绑定已存在的仓库版本5b9cb14，报告对应的原日志、逐帧loss、视频SHA、GPU实际费用与失败记录可从各阶段报告追溯。服务器视频与大张量不上传GitHub；本报告依据已完成原件与实时账本，不是文献综述或论文最终结果。

