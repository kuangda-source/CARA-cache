# M2：把读写机制接成可执行的估值方法

**优先级更新：本路线现归V2，后置，不阻塞V1。** 用户最新选择[来源生命周期感知V1](../source_lifecycle/README.md)作为近期自动规划主交付；先完成其完整视频证据，再做一次有界终点响应增强，之后才决定完整伴随。本文的既有CPU与原科学结果保留，不据此启动新的伴随GPU。

2026-11-01。当前是实现与实验设计承接，GPU范围和整卡费用尚未冻结。M1原launch7949388215944eb98c7f64f21e8e1dd1已经完整接受、释放和唯一结算，双检查删除；其b930df4b源、14分母和1.95GPUh边界保持，不再派发或评分。本安排依据完整M1机制结果推进。

[835当前接受](../../../research/835_CARA_M2_VAE_LINUX_AND_REAL_ALEX_TERMINAL_VJP_20261101.md)：缓存转移、小模型伴随、原Wan2.1小权重解码分别通过实际Linux CPU；真实固定Alex权重在合成93×64×64视频上的流式输入VJP与整图值/梯度逐值一致，两档方向差分误差低于0.04%。两个新增原CPU已退出0。真实Cosmos/VAE权重、生产93帧显存、完整状态来源映射与硬交换仍待；新增GPU/中央事务为0。

## 要验证的方法

固定原Cosmos、35请求/36更新UniPC、CFG7（实际算术顺序为c+7(c−u)）、纯C读出和19D预算。从确定性Uniform19起点，在候选自身轨迹上对z=(latent,完整UniPC历史,两分支完整cache)求终点离散伴随，用同父状态的硬D/C转移差给出有符号read/write价值，再提出至多两个合法交换计划。完整硬FIT终点评价决定是否接受；没有改善就保留原计划。

主对照保持三个：原S的局部q、同一终点伴随的read-only、完整read+write。三者使用相同起点、同FIT/seed、同合法语法和相同硬候选额度。不能把另一个局部误差指标当作read-only伴随消融，也不在CFG传播后重复加64C+49U−112K。

## 当前已经实现的组件

`cara_read_write_transition_r1.py`提供独立校准转移，不修改生产no_grad执行器。WC仅把原阈值谓词替换为外部硬C/D；RF仅把原net调用接到显式参数/buffer执行，条件处理与FP32算术保留。缓存列表/字典结构独立，原会原地累加的漂移标量保留梯度地clone；特征张量不detach。每个module buffer由显式状态承接，临时前向不污染原模型。

覆盖原OSI、flow/warp、C工作状态更新、三个物理窗口槽和70-call cycle reset。当前只支持alpha=0的纯C/D；A校准器不进入该受限算子的数值依赖。接入生产父状态时仍须携带真实D来源step/sigma及owner离散出处，不能从“最后两个来源”推断只保存两个物理槽。

[本地R4接受](../../../reports/cara_read_write_transition_CPU_component_r4_20261101.json)包含五项检查：两种flow的完整36硬前向/全部WC字段/buffer逐值等价；C非恒等工作状态；当前输入和缓存残差的方向有限差分；实际UniPC+WC/RF36步小模型整图梯度；冻结/eval/未就绪C/inference-mode拒绝。R2保留UniPC测试模块未注册的接线失败，后续只修复测试注册，没有改原求解器。

本地使用固定源码函数体、CPU依赖namespace、小权重和合成latent损失。它证明真实WC递推的计算接线，尚未证明真实Cosmos权重VJP、VAE/视频Alex反向或完整伴随。两卡下一次GPU隐藏CPU验证只替换为实际Linux WC/RF导入与globals；仍使用小权重。该CPU运行独立1核/4GiB/零额外swap/无网络/无GPU，8GiB宿主余量门不通过就不派发，不借用M1的24、25核。

## 按依赖完成的实现

1. **固定槽和真实来源映射。** 用三个物理residual/probe槽、validity和两个CFG分支表达实际缓存，保留original reset。局部连续导数固定step/index/source身份；来源更新由精确硬转移/合法性负责，不对离散步号插值。验证D/C动作后到固定连续坐标的映射，不能把None当作未声明的零向量。
2. **真实模型单转移VJP。** 保持参数冻结/eval，核对真实WC/RF硬输出、buffer和状态与生产入口一致；对latent、probe/residual缓存和UniPC历史分别做多方向/多epsilon有限差分，记录实现分支和clamp边界。需要非零VJP和合理误差，不能仅以程序可backward接受。
3. **真实视频终点梯度。** 复用原同输入Native；拟合目标为同93帧/同尺度的未编码浮点VAE视频Alex LPIPS，按输入等权、帧等权。原VAE含时间耦合时，不能把单帧独立decode冒充原decoder；先验证前向等价再分块/重算。正式完整视频评分仍是硬候选接受依据，浮点目标与编码评分边界分别记录。
4. **完整离散伴随。** 对实际F的VJP传播，保留latent、所有UniPC预测/last_sample、缓存读写/移位和buffer依赖。可CPU存储检查点与分段重算，但整卡报价必须包含反向/重算/传输/释放；48GiB能否承载真实模型尚待实测。不把Euler、identity Jacobian、cache detach或latent MSE静默替换进主方法。
5. **同轨迹价值与硬行动。** 在候选自己的z_k支付同状态另一硬动作，计算g_read与g_write。有限D/C差是提案分数，不能解释为硬收益定理。固定radius1/2提案器只输出合法、保持K的至多两个不同计划；三个估值器额度相同，重复计划只生成一次并保留共享身份。

## 最小实验与判读

M1完整接受后，先判断写作用是否可辨识，再冻结M2实际完整卡。起点与样本不从M1分数重选。首轮维持原两FIT/seed0；不新增CHECK曝光或读取保护TEST。M2先做一轮行动验证：三个估值器各至多两个新计划，每个计划必须完整两FIT；同批Native/parent、导数检查、影子D/C、完整视频、控制及释放全部列入总范围和费用，不能只报至多12条候选视频的生成费用。

分开回答两件事：数值导数能否通过有限差分；提出的有限swap是否真改善正式终点。再看full相对同伴随read-only是否有可辨认增量，报告逐输入与等权均值，不设置机械5%门。若full/read-only相同或反复预测反向，优先检查状态坐标/符号/线性近似范围，不能把额外参数搜到的配方当作伴随机制证据。

仅信号与实现均支持时再进入M3：最多3轮、每轮2新候选；每次接受后在新轨迹重算价值，再冻结共享计划到开发留出。固定K和实测T_DD/T_request分别报告，不能宣称同K即时间匹配。

## 执行与财务边界

真实GPU桥接和M2整卡仍需完整生产CPU、固定源、资产/显存/私有存储、全段费用及fresh准入。M1的四卡原账本许可只覆盖M1；后续卡不继承。继续遵守两卡执行、cap226、旧16.5和<2自主/2–4说明后推进/>4单独批准的整卡规则，不拆卡规避阈值。当前M2新增GPU与账本事务均为0。

## 19:56实现增量

固定源码缓存转移已由[两卡原CPU终态](../../../reports/cara_read_write_transition_Linux_CPU_accepted_r1_20261101.json)接受五项，44.91秒、容器退出0。另已实现`cara_read_write_adjoint_r1.py`的完整状态余向量/VJP与read/write硬动作差收缩；[本地五项](../../../reports/cara_read_write_adjoint_CPU_component_r2_20261101.json)覆盖36步重算伴随对整图梯度、两幅度辅助方向差分、D起点符号、重置后零write和错位拒绝。原FP32小read方向的精度失败单列保留，未改原RF算术。当前状态坐标保留实际原窗口拓扑；合法内点C/D要求全部已占槽路径对齐，仅原漂移标量的literal0 reset显式对齐。全局固定槽/validity/source-sigma映射与真实GPU资源仍是未完成项。

## 20:08原Linux伴随接受与下一道关

[原伴随CPU](../../../reports/cara_read_write_adjoint_Linux_CPU_accepted_r1_20261101.json)已退出0，实际导入下五项通过，33.805秒；首次网络未知经stage/容器明确不存在后才进入同一stage首次实际准备，原证据见833。现在两段CPU均结束，只恢复原件。

[VAE源码审计](../../../reports/cara_read_write_vae_backward_source_audit_r1_20261101.json)明确上游外层model与WanVAE两处no_grad、Wan2.1跨时间特征缓存和原normalization/dtype依赖。尚未绑定本卡实际tokenizer类，也没有decode前向等价、真实权重VJP或93帧峰值证明；先实现保留时间缓存的独立校准适配，再完整核验与报价，不假定逐帧独立decode成立。

## M1完整机制信号与VAE组件

[834完整接受](../../../research/834_CARA_M1_COMPLETE_READ_WRITE_MECHANISM_AND_M2_CONTINUATION_20261101.md)支持继续M2：固定点写项2/2同向、平均Alex相对00降低19.51%，read降低2.02%，joint降低19.24%，正交互保留。不从本点手选新计划或修改三估值器/等候选预算；固定K方法收益仍由M2完整硬swap判断。

`cara_read_write_vae_r1.py`已实现source-bound私有Wan2.1解码包装，保留原normalization/dtype与时间缓存，要求原未包装接口、非parallel/benchmark、冻结eval且codec无buffer；仅去掉已核对no_grad装饰。三项本地CPU在小权重下通过一帧/93帧硬前向等价、调用者缓存保持、跨时间VJP/方向有限差分和模式拒绝。源码/hash见[原接受R3](../../../reports/cara_read_write_vae_CPU_component_r3_20261101.json)，R1/R2 CPU namespace缺项保留。实际部署backend身份、真实权重前向/VJP和93帧显存尚未接受；不得据此派GPU。
