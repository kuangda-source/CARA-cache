# H0 模式控制修复与独立 r2 卡

2026-10-03。r1/source18e692e 的 `H0 requires eval` 失败已封存并计费；0完整四臂、0原件，不能追认为互补性结果。独立r2/source4c1c3a8已退出0并独立审计，状态 `H0_LOCAL_COMPLEMENT_SCREEN_PASS_TWO_CFG_ONE_DEVELOPMENT_SCENE`。首次局部互补筛查2/2通过；没有视频质量、端到端收益或来源×寿命结果。

## 终态与局部正结果

[独立审计](../reports/wc_h0_eval_complement_r2_audit_20261003.json)、[摘要](../reports/wc_h0_eval_complement_r2_summary_20261003.json)、[runner](../reports/wc_h0_eval_complement_r2_runner_20261003.json)、[监督](../reports/wc_h0_eval_complement_r2_supervisor_20261003.json)：两臂各20更新/40CFG，共享eval模式与全部九门通过；step13/20各36组件逐项一致，observed进程内restore两处通过。call33/CFG0与call34/CFG1为事前selector选出的首次eligible full，历史真实full counters分别12/22和13/23；C在当前D前产生，当前D唯一部署，所有dense重复与实际full hidden/velocity逐位一致。

八文件/16张量raw SHA、finite/shape/各臂三次hot计时、source与共同mode控制、float64 NumPy独立误差复算全部通过。以下误差均相对**同状态当前D**，是relative RMSE，不是视频评分：

| call / CFG | C velocity误差 | matched-full velocity误差 | S velocity误差 | S postwarp residual误差 | D组+head中位耗时 | S组+head中位耗时 | D/S加速 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 33 / 0 | 29.8408% | 0.4665% | 0.9390% | 4.3493% | 3098.077ms | 2933.363ms | 1.05615× |
| 34 / 1 | 38.4000% | 0.4547% | 0.9450% | 4.2525% | 3105.830ms | 2939.572ms | 1.05656× |

C组+head仅81.379/81.543ms，但此刻强行复用的误差较大；官方WC本来就选择full。S在这些full位置相对C大幅降低当前velocity误差，同时比D少约5.3%的整组耗时（加速约1.056×）。两点均满足事前四筛查：S residual/velocity≤5%、S/C velocity≤0.75、D/S≥1.05。matched-full是含量化/路由的控制，不是真dense；它的耗时3172.991/3190.669ms高于D。其误差与S误差不能简单相减当独立可加损失。

这支持“有些时刻C不够准，而S提供介于C/D之间的准确性和成本”这个局部前提。整组速度只略高于1.05门，尚未证明稳定跨场景优势；前面104点算子1.219×不能替代此处整组成本，更不能充当端到端加速。两个CFG属于同一已曝光开发场景，不是两个独立场景；当前稀疏缓存没有被后续采样复用，寿命/最终视频/预算匹配策略均未验收。已有历史sparse残差缺失的完整H0范围仍未补齐。

实计708.4838515026495秒（0.196801069861847GPUh），累计5.05310433089345/12GPUh、34jobs，余额6.94689566910655h；无inflight。原supervisor2662009/timeout2662025/runner2662027全部退出，f1锁与GPU释放（24MiB、无compute）。所有失败及费用保留，预留已被实际费替代。

## 下一步决定

H1后续CPU接口已实际通过，成本/下一门见[78记录](78_WC_H1_FIXED_TRAJECTORY_CPU_AND_COST.md)，尚无H1 GPU或寿命结果。以下为H0终态时冻结的接续安排。

继续WorldCache，下一优先准备原[65设计](65_WC_HIERARCHICAL_PROVENANCE_LIFETIME_DESIGN.md)的H1来源×复用寿命CPU接口与具体成本卡，先1组、三来源dense/matched-full/S×1/2/4个同CFG有效solver步。H0局部正结果允许准备下一卡，不自动解锁GPU、分组动态策略、RV或训练。

下一必须先定义一致的复用算子和来源语义：S/matched-full只能进入approximate reference，不能成为true dense校准锚点；同轨未来probe可读、当前/未来shadow真值只评分。选择能够覆盖后续4步的分支点与尾段，冻结完整配对分母，另验固定轨迹局部诊断与真正分叉闭环的不同接口；r2只保存当前评分原件与状态哈希，不能当成持久化可重启全状态。下一身份/source/范围/成本及实际门另登记，禁止自动第三H0或以当前筛查补造寿命结论。以下部署与启动是历史快照。

## CPU 定位与控制修复

官方 loader 的 `on_train_start()` 做 dtype/compile 准备，没有随后调用 eval。[固定源码 meta 构造回执](../reports/wc_h0_native_mode_meta_cpu_20261003.json)用失败配置中的全部网络参数构造实际 `MinimalV1LVGDiT`：2,059,174,912参数、1173模块全部默认training=True，拓扑没有Dropout/BatchNorm/InstanceNorm。失败GPU没有存下具体mode vector，这个CPU观察不能倒推当时每个标志。

CPU进程禁止CUDA lazy init与Triton执行。TE RMSNorm默认设备与meta reset会尝试materialize CUDA，因此仅此CPU构造给它显式meta设备并跳过meta参数reset；保留实际类与mode默认值，没有模型权重或原生前向。source与package SHA、适配明细均在回执中，不能称无适配的GPU运行。

[实际修复门](../reports/wc_h0_eval_mode_cpu_gate_20261003.json)：1173默认训练标志→共同eval后0；所有模块的train方法均为原 `torch.nn.Module.train`，参数/buffer对象及版本未变。默认模式数据/buffer/RNG保持、危险自定义train拒绝、拓扑变化和后续mode漂移拒绝通过。五次默认模式toy setup经同一个生产adapter进入官方固定源码shadow控制，flow OFF/ON各两CFG四臂、逐位D重放、历史隔离、原件独立误差复算及非finite失败分母保持全部通过。CPU不证明GPU train/eval输出等价或方法收益。

修复保留 `H0ComplementProbe` 的严格eval guard，不修改r1脚本、配置、旧stage或回执。新runner在首次baseline之前显式建立共享eval，并在两臂开始和结束检查全mode/topology签名。它是有版本的推理模式适配，同时应用baseline/observed；r2只对这个共同eval条件下的官方WC与shadow比较负责，不声称与r1默认模式前缀逐位等价。

## 下一张独立卡

卡 `WC-H0-EVAL-COMPLEMENT-R2-20261003-A`、run `wc-h0-eval-complement-r2`，[配置](../configs/wc_h0_eval_complement_r2.json)、[执行依据](../manifests/wc_h0_eval_complement_r2_execution_20261003.json)。由既有人工继续指令及当前自主推进goal选出的常规技术修复卡，没有伪造新用户消息；r1单次卡已结束，新的identity独立保存失败历史。

科学范围完全沿r1：同一已曝光第二CAL场景、seed0、93帧432×768/guidance7；两臂各20 solver更新/40CFG，step13/20恢复与36组件、全部九门保留；call25..40每CFG首个有两份严格过去同CFG真实full历史且resume为真的官方full；C在当前D之前、D唯一路径、matched-full/S只做shadow；固定layers6/23/27 dense回退、sim0.1/cdf0.98、noPV；每臂1warmup+3repeat、2状态/8臂固定分母。缺失/失败不补点、不加call或调阈值。局部≤5%误差、S/C≤0.75、D/S整组成本≥1.05的事前筛查不变。

不得把r2当原r1重试记录或把新增eval适配藏起来；所有原始输出只用于此局部评分，未训练/无专家标签。无完整视频、端到端部署或寿命验收，H1/H2/RV/训练后置。

## 时间、预算与实际门

[成本](../reports/wc_h0_eval_complement_r2_cost_20261003.json)取r1实际加载113.853秒与r4旧40-call前缀放大229.938秒/臂的较保守组合，24 shadow组×5秒、C10秒、metadata/IO70秒、mode5秒，20%规划余量及30秒结算余量合964.475秒≤1200。完整S组真实成本仍未测；不是保证不超时。

最多一次1200秒全cost/1170child/kill5，无自动第三H0卡。当前4.856303261031603/12GPUh、33jobs，余7.143696738968397h，历史不重置；仅单昂贵任务。先冻结源码/payload、在实际环境补齐旧26项及新native模式/默认模式四臂门、source/assets/import/package；再fresh UUID/VRAM/compute/f1锁/无inflight/余额。启动结果与费用须独立审计后再下科学结论。

## 实际部署与唯一启动（非终态）

[CPU31部署](../reports/wc_h0_eval_complement_r2_deployment_20261003.json)：source4c1c3a81741d9dc7edfaf40f43cf997bd13dcb11，全部31项CPU与source/assets/import/package门通过，native默认1173→eval0，CUDA未初始化、预算未变，数据盘585781604352bytes空闲。源码在GPU前已同步私有GitHub。

[唯一启动](../reports/wc_h0_eval_complement_r2_launch_20261003.json)/[现场](../reports/wc_h0_eval_complement_r2_start_observation_20261003.json)：supervisor2662009/timeout2662025/runner2662027现场存活，模型加载和共享eval设置通过，baseline前缀在跑；fresh选定sm86 GPU24MiB/noapps，全局锁/无inflight/余额门通过。child起算1200秒最大截止北京时间15:49:09；预付1/3h使在途账本5.189636594364936/12h、第34job，结束按实际全wall替换预留。只跟踪同一identity，禁止重复提交和修改在跑source；live状态不构成模式或互补性GPU验收。
