# H1 独立首卡终态：来源扰动有温和增长，共同缓存漂移占主导

2026-10-03。唯一 `wc-h1-local-lifetime-r1` 正常exit0，状态 `H1_FIXED_TRAJECTORY_LOCAL18_AUDITED_DESCRIPTIVE_ONLY`，source `e59b5880df5a57118a6fdce5df1716b7a972f05a`。6/6来源臂、18/18来源×age格、30文件/60张量完整，全部九门和独立CPU误差复算通过。**这是一张已曝光CAL上的固定轨迹局部诊断，尚未证明安全寿命、视频质量或端到端收益。** 原r4/H0/H1 CPU失败回执保持。

## 实际部署、运行与独立审计

[完整部署回执](../reports/wc_h1_lifetime_r1_deployment_20261003.json)记录实际34组CPU/source/assets/import/package/native-meta/样本序列化门通过，CUDA未初始化；stage的69份payload加mid-config共70个文件通过SHA核对。[启动](../reports/wc_h1_lifetime_r1_launch_20261003.json)后只跟踪这一组handles，无重提或运行中修订。

[runner](../reports/wc_h1_lifetime_r1_runner_20261003.json)两前缀各21 solver更新/42CFG，20 full/22 cache；请求35仍保留36步完整网格和70CFG horizon。全部九项input/output/trace/block counts/state/sampling/named inputs/conditions/field signatures精确相等，step13/21各36组件相等，observed两处进程内restore通过并从13继续到21。共享eval两臂均1173 training标志归零，普通nn.Module.train且参数/buffer对象版本未变。该前缀的219.462/518.815秒含不同诊断负担，不能作部署速度比。

[独立审计](../reports/wc_h1_lifetime_r1_audit_20261003.json)验证冻结source、同CFG/条件、来源身份、true-dense过去计数、预测先于当前teacher、teacher两次逐位一致、held reference未变及全部分母。30个原件60张量的whole/raw SHA、shape/dtype/finite通过；24行×两字段的MSE/reference energy/relative MSE/RMSE/cosine用CPU float64复算，与GPU fp32记录一致（relative2e-6/absolute1e-9）。这是技术验收，不能替代质量评测。

[追加CPU部署哈希核对](../reports/wc_h1_lifetime_r1_deployed_velocity_cpu_20261003.json)：age1/2四次cache的held-dense预测，按原float32张量重建tree SHA，均等于实际官方部署输出；age4两次full的当前D teacher同样匹配部署输出。age4的旧参考预测并未部署，也不能说官方缓存连续复用了4步。

## 来源时的三臂结果

D是原算子，MF是候选后端全块，S是固定稀疏策略（6/23/27 dense回退，0.1/0.98/noPV）。两来源点step17/call33、34仍为官方full，严格过去true-full计数分别[12,22]、[13,23]。每臂1warmup+3repeat，以下为热重复中位，包含完整deep组2..27与head。

| CFG / call | D / MF / S 组+head ms | MF / S residual RMSE | MF / S velocity RMSE | D/S |
|---|---|---|---|---|
| 0 / 33 | 3103.487 / 3173.966 / 2931.983 | 2.2259% / 4.3493% | 0.4665% / 0.9390% | 1.05849× |
| 1 / 34 | 3126.290 / 3195.925 / 2943.667 | 2.1024% / 4.2525% | 0.4547% / 0.9450% | 1.06204× |

S来源的局部residual/velocity均低于描述性5%线；D/S约1.0585/1.0620×，组+head耗时降低5.53%/5.84%。这不是视频或总去噪加速。MF本身已有后端误差，不把S相对D的全部误差归因稀疏mask。

## 全部18格结果

以下每行含三个来源，完整18格保留。[完整JSON](../reports/wc_h1_lifetime_r1_summary_20261003.json)和runner保留原MSE、reference energy、方向余弦及有符号差值。

| CFG | age / step / call | 官方动作 | D / MF / S velocity RMSE | D / MF / S residual RMSE | S−D velocity pp |
|---|---|---|---|---|---|
| 0 | 1 / 18 / 35 | cache | 11.1645% / 11.1763% / 11.3165% | 24.3568% / 24.4095% / 24.8795% | 0.1519 |
| 0 | 2 / 19 / 37 | cache | 16.1128% / 16.1251% / 16.2907% | 34.1045% / 34.1511% / 34.5775% | 0.1779 |
| 0 | 4 / 21 / 41 | full | 25.7680% / 25.7755% / 25.9373% | 53.9159% / 53.9423% / 54.3030% | 0.1693 |
| 1 | 1 / 18 / 36 | cache | 13.6086% / 13.6377% / 13.7610% | 29.0374% / 29.1151% / 29.5470% | 0.1524 |
| 1 | 2 / 19 / 38 | cache | 19.9538% / 19.9843% / 20.1424% | 40.8561% / 40.9258% / 41.3651% | 0.1886 |
| 1 | 4 / 21 / 42 | full | 31.5805% / 31.6077% / 31.7619% | 63.9253% / 63.9789% / 64.3993% | 0.1813 |

描述性“双字段均≤5%”为0/18，dense-held也0/6。这不构成稀疏方法特有的失败判据，也不能由局部误差否定官方WC的最终视频质量；没有一臂获得这条局部线下的安全寿命。age1/2是官方实际cache，age4是强制保留step17参考的私有诊断，官方已full。此次范围内误差随1/2/4增大，但不据三个K推出普遍单调性或连续安全期限。

## CPU来源扰动分解：区分总误差与来源差值

总RMSE的S−D仅0.152–0.189个百分点，并不等于S与D预测的差值范数。[独立分析脚本](../scripts/analyze_wc_h1_source_delta.py)与[原件分析回执](../reports/wc_h1_source_delta_cpu_20261003.json)在CPU禁止CUDA、重新核验原件SHA后，逐字段float64验证恒等式：

`MSE(S,T) = MSE(D,T) + MSE(S,D) + 2 mean((D−T)·(S−D))`。

这是输出空间恒等式，不假设Gamma+flow预测器线性；附加分析是事后描述，不改变冻结5%筛查。归一化差值为`||S−D||/||当前teacher||`，绝对放大倍数为未来`||S−D||`除以来源时`||S−D||`，分母不同，分别报告。

| CFG | age | S−D velocity 归一化差值范数 | 相比来源时绝对差值范数倍数 | 与dense误差方向余弦 |
|---|---|---|---|---|
| 0 | 1 | 1.0328% | 1.1032× | 0.1019 |
| 1 | 1 | 1.0387% | 1.1021× | 0.1094 |
| 0 | 2 | 1.2347% | 1.3277× | 0.1066 |
| 1 | 2 | 1.2148% | 1.2976× | 0.1255 |
| 0 | 4 | 1.4390% | 1.5633× | 0.0901 |
| 1 | 4 | 1.3945% | 1.5054× | 0.1083 |

velocity来源扰动从原始约0.94%变为未来1.03%–1.44%，绝对范数放大1.10–1.56×；相较之下共同dense-held误差为11.16%–31.58%。MF−D未来差值也有0.51%–0.71%。S扰动与dense漂移方向余弦约0.09–0.13，轻微同向；总RMSE差距小不能解释为来源误差消失。深层residual的S−D差值为4.64%–7.38%，绝对范数放大1.09–1.76×；共同dense-held residual误差24.36%–63.93%，residual扰动与共同误差接近正交或轻微抵消，不能只看velocity就宣称内部误差可忽略。当前只能说该点来源偏差温和增长、共同预测漂移更大，不能作统计交互或来源不重要的全局结论。

## 费用、释放和接续决策

[supervisor](../reports/wc_h1_lifetime_r1_supervisor_20261003.json)全wall889.004681秒，即0.246945745GPUh，低于1800秒硬上限及1414.365秒规划包络；加载、初始化、诊断、IO和释放都计入。0.5h启动预付已按实费结算。累计5.300050075675308/12GPUh，35jobs，余6.699949924324692h；旧失败费用未删除，无inflight。PIDs2668463/2668479/2668481退出、f1锁可获取；417个监控点只观察到本runner，峰值24912MiB，释放后24MiB/noapps。

**继续WorldCache，但暂不推进H2来源感知分组路由或训练。** 这张首卡没有支持“来源决定可用寿命”的差异：三来源在同一局部筛查下均未达标，来源扰动小于共同漂移。保留简单S/D与age基线，下一先CPU准备预登记早/晚时段及未用于本次选参的CAL场景的有限诊断范围、选择规则和真实成本，检查这一现象是否泛化；不是独立最终确认。不能用总误差高直接跳到RV/Trust Head，刷新价值仍需要同状态、同后续规则、同预算的反事实收益证据。

另一GPU窗口须另一个具体identity/source/card与实际CPU/source/assets/import、fresh UUID/VRAM/compute/锁/无inflight/余额门；本r1授权已消耗，不重启或自动补点。不取消既有冻结工作，非必要不新增人评；早/中/晚、独立场景、闭环、视频和真实质量–时间边界仍待完成。

---

## 以下为执行前冻结卡与CPU快照（历史）

# H1 独立首卡：固定轨迹来源×1/2/4步

2026-10-03。当前状态 `PRODUCTION_CORE_CPU_PASS_PENDING_FULL_ACTUAL_DEPLOYMENT_NO_GPU`。延续[78接口/成本](78_WC_H1_FIXED_TRAJECTORY_CPU_AND_COST.md)；保留r4/H0和H1 CPU r1/r2失败及全部账目。主目标仍是提高调优WorldCache的质量–时间边界，当前局部诊断不等于目标完成。

## 冻结卡与执行依据

卡 `WC-H1-LOCAL-LIFETIME-R1-20261003-A`、run `wc-h1-local-lifetime-r1`，[配置](../configs/wc_h1_lifetime_r1.json)、[执行依据](../manifests/wc_h1_lifetime_r1_execution_20261003.json)、[成本](../reports/wc_h1_lifetime_r1_cost_20261003.json)。当前自主实验goal与既有[累计12GPUh/队列授权](BUDGET_AUTHORIZATION_20261003.md)支持完成常规准备后选择这张独立卡；不是新增人工消息，也不复用已完成104点r4的单次1800秒授权。H0筛查本身不直接启动下一GPU。

最多一次1800秒全cost、1770秒child、kill-after5秒；在78草案上另计50秒startup/import余量，保守规划包络1414.365秒，不缩矩阵以挤进1200。单昂贵任务，共享f1锁；load、首用/JIT、失败、诊断、IO与释放观察全部计费。已用5.05310433089345/12GPUh、34jobs不清零，无新GPU费用；启动时重新读实际账本，余额须容纳1800+15秒结算余量。没有自动第二H1、H2、RV或训练。

## 完整科学范围

一个已曝光第二CAL场景 `common_sense_6487f37f-ef57-49ca-afdc-d898922b5191`、seed0、93帧432×768/guidance7，Cosmos2.5-2B/eager/minimal_a2a，共同eval与原官方WC配置。完整UniPC-Karras网格仍请求35、实际36更新/70CFG horizon；baseline/observed各前21更新/42CFG。step13/21各36组件与进程内restore、全部九项输入/输出/状态/condition gates保留；13恢复后实际继续到21，不是独立可重启整管线接口。

step17/call33、34作为固定来源点，必须仍为有已付probe及两份严格过去同CFG真实full历史的官方full，失败不补选。一个deep组2..27；dense/matched-full/S只在这一状态生成参考，固定6/23/27原dense回退、0.1/0.98/noPV、各1warmup+3repeat。未来age1/2/4对应calls35/36、37/38、41/42，共6来源臂、18来源×age格、30raw文件。全部分母保持，失败不删、不另选K/场景/CFG。

三来源使用相同过去真实dense `(R_p,P_p)`、同一当前真实浅层 `P_s`，只改变新深层参考。私有Gamma+warp窗口 `[R_p,R_s^source] / [P_p,P_s]` 冻结至age4，中间官方刷新不改变held reference。matched-full/S始终approximate，不进入部署缓存或真dense校准器；未来读取相同官方轨迹输入/probe，不复用注意力mask。三种预测及raw先完成，之后才有当前D teacher；teacher重复两次逐位相等，原轨迹恰为full时再与其实际deep逐位相等。只有官方路径参与采样更新。

每个来源保存request/model/condition/CFG/group/step/call、过去true dense counter、快照SHA/版本、固定policy。新增实际cross-attention条件指纹按CFG核对；条件改变在复用与teacher前失败。完整报告每格MSE/reference energy/relative RMSE/方向余弦与有符号S−D、MF−D差。5%是描述性局部保真筛查，dense-held自身漂移同报；不预设单调，不从三个K推出连续安全寿命、最终质量或统计交互。两CFG是相关开发数据，早/中/晚与独立场景及完整闭环均未完成。

## 生产执行与实际CPU控制

[run_wc_h1_lifetime.py](../scripts/run_wc_h1_lifetime.py)调用独立的[同一生产前缀核心](../src/wcomr/h1_prefix.py)；真实入口不提供toy/kernel override。CPU用stand-in Inference/prepare/reset、Toy模块与合成kernel验证该核心，实际官方WC函数和UniPC源码均按固定SHA读取，不能当真实模型前向结果。

[实际CPU回执](../reports/wc_h1_prefix_cpu_r1_20261003.json)：32.689秒、Torch2.7.1+cu128、禁止CUDA lazy init，账本不变。flow OFF/ON两组各两臂21更新/42CFG，全部九门、step13/21各36组件、shared prepared batch/full RNG、buffer增量、18格与30raw通过；原件/重放要求沿78控制。非finite来源与当前CFG条件改变两种失败保持6/18分母，未生成未来truth/补点，所有model/net/scheduler/prepare挂钩恢复。六项reference控制与四组完整固定源码分支矩阵再验证通过；scope/cost/budget分别拒绝10/2/6种篡改。

本轮H1 condition guard的源码已更新，旧78 CPU r3保留其旧版本；当前回执记录新源码哈希。H0脚本与stage未修改。纯CPU core还不代替真实官方prepare/reset与实际模型九门；下一完整部署需补官方prepare CPU控制、真实UniPC在13/21恢复后的下一更新、固定原类meta共享eval、完整资产/包/source/import和sample metadata序列化检查，CUDA必须仍未初始化。

## 唯一启动与独立验收门

先提交/推送source、配置与具体卡；只在新stage验证全部payload，实际CPU及assets/import/native mode gates通过，再fresh UUID/VRAM/compute、全局锁、无inflight和预算。指定旧GPU只是候选，现场不满足则不争抢。输出run identity与scope绑定，旧stage/out/launch存在时只检查，不重复提交。

终态后独立核对source/同条件/九门/状态/来源语义、30文件60张量SHA/finite/shape、CPU float64误差复算与完整6/18分母，再核对实费/监督exit/PIDs/锁/GPU释放。技术门通过与局部寿命证据分别报告；范围不足不追认闭环、视频、H2或论文贡献。结果区待真实回执，不写预测结论。
