## 2026-10-03 完整六输出首卡终态：真实闭环通过，人物保真差异待解决

[83 完整卡](research/83_WC_FULL_OUTPUT_R1_CARD.md)/[完整摘要](reports/wc_full_output_r1_summary_20261003.json)：冻结source b3ed6b084b5e7bad5a242bd9a934a0d502e1ef6c唯一run退出0，六phase均36更新/72CFG、六mp4/93完整解码；D/D九门和五处实际restore/最终pipeline、source/assets/import/package/来源/费用/释放独立审计通过。两曝光CAL各19次S CFG/437个真实注意力算子、29次后续cache读取approximate；合计874算子，不是仅局部算子测试。

相对官方WC，common PSNR24.9893dB/luma SSIM0.90118/motion帧差比0.98596；human PSNR17.4794dB/SSIM0.70541/motion比0.95216，人物保真差异明显更大。common两轨deep35/35，human38/35、9次full/cache选择改变；第一输出SHA分歧均call23，human第一次schedule分歧call46。哈希不能做因果归因；编码代理不是原生full/语义/物理接受，两CAL不是CONF。debug wall common359.8905/389.6099秒、human381.7509/386.8368秒含不同restore/ledger/hash/prepare工作，不报净E2E收益。

实费2442.346019768156秒=0.678429450GPUh，累计6.733473505896205/12h、37jobs，余5.266526494103795h，无inflight；原三PIDs2687791/2687807/2687809与f1锁/GPU释放（24MiB/noapps），1144次monitor峰值26966MiB。6000预付已按实际结算，原104点单次1800授权/H0/H1历史保持，不重启。

下一按[84 CPU与测量方案](research/84_WC_VIDEO_GATE_AND_CLEAN_TIMING_NEXT.md)先用现有回执核查轨迹/成本并准备轻量部署路径，将人物保真和adaptive schedule反馈作为当前缺口；不扩样/叠学习器/训练/新增人评。下一GPU卡尚未选定，需新的具体范围、实测成本、source及实际门/fresh准入；goal继续，当前无质量—时间前沿或论文接受结论。完整原回执采用无损gzip归档并校验解压SHA，视频/权重/张量不入Git。以下为历史。

## 2026-10-03 第一个完整WC/S配对已独立CPU审计，第二场景原任务继续

[83 完整卡](research/83_WC_FULL_OUTPUT_R1_CARD.md)的common配对两路径均36更新/72CFG和35次deep，真实S在19次CFG刷新中执行437个注意力算子，29次后续cache读取approximate来源；来源/CFG/group/epoch/call70失效/两尾部dense与6/23/27回退、两视频768×432/16fps/93完整解码独立通过。first-pair自动编码指标为PSNR24.9893dB/luma SSIM0.90118/帧差motion比0.98596；是相对官方WC的描述性开发诊断，不是原生full/语义/物理质量接受。

首场景debug wall为官方359.8905/S389.6099秒，包含恢复/ledger/哈希与prepare工作差异，既不能据此认定净加速，也不能把局部算子加速当E2E结果。现场1791035289.041415共4/6mp4，第二human_199原run正在生成；原3PIDs/source不变，6000预付和累计12h、6全分母保持。先完成原卡、终态source/assets/cost/release和六视频独立审计及自动指标，再决定clean E2E/强基线范围；不重提本卡或自动训练/新增人评。以下均为历史。

## 2026-10-03 完整六输出首卡在跑：D/D独立原件审计通过，3/6视频

[83 固定卡](research/83_WC_FULL_OUTPUT_R1_CARD.md)的冻结 source b3ed6b084b5e7bad5a242bd9a934a0d502e1ef6c 在 actual CPU11/19/3、prepare/metadata/native-meta buffers/source/assets/import/package 与 fresh资源/锁/账本门通过后唯一提交。现场1791034920.0072188确认 supervisor2687791/child2687807/runner2687809均live；D/D两臂36更新/72CFG、九门/五处restore/最终pipeline通过。独立CPU再从原回执重算九项/五项与来源、两mp4字节SHA相同/768×432/16fps/93完整解码通过；自动指标DD对照MSE0/SSIM1/temporal0，静止退化、缺帧、多帧与缺结构门拒绝控制通过。

当前三个mp4为D/D两对照加common配对官方WC，common的S候选正在生成，尚无完整候选或质量结论。只跟踪原run/输出目录，不修改冻结stage/payload、不重复提交；终态独立审计6分母、源码/原件/真实核/来源/93帧和费用/释放。此前已结算6.055044055960606/12GPUh、36jobs；预付6000秒=1.666666667h，含预留7.7217107226272725/12h、37jobs，实际费用待终态结算。child1791033603.3447514起算最大北京时间23:00:03.344751；任一输出缺失或技术异常即止，不自动第二卡/训练/新增人评。debug wall无净E2E归因；单次104点≤1800授权已完成并消耗，以下为历史。

## 2026-10-03 完整六输出首卡：实际部署全部门通过，待唯一现场提交

[83 固定卡](research/83_WC_FULL_OUTPUT_R1_CARD.md)：冻结source b3ed6b084b5e7bad5a242bd9a934a0d502e1ef6c在新deploy2 stage实际完整CPU11/19/3控制、官方prepare/样本metadata、native-meta mode/buffers、全部source/assets/import/package通过，CUDA未初始化、账本保持；原缺依赖准备失败stage/34f2d86保留。源代码已同步GitHub，6输出/6000全cost/5970child/全局锁/累计12h范围不变；尚无本卡GPU费用或视频。

下一仅fresh UUID/VRAM/compute/无inflight/余额/锁/磁盘后提交wc-full-output-r1一次；DD原官方与dense adapter不通过即止，不重启旧任务/自动第二卡，不删分母。当前6.055044055960606/12GPUh、36jobs保持。实际核执行/视频/clean E2E/独立CONF仍待结果；以下为历史。

## 2026-10-03 独立完整六输出首卡：CPU组合通过，实际部署门待验证

[83 独立卡](research/83_WC_FULL_OUTPUT_R1_CARD.md)选定WC-FULL-OUTPUT-R1-20261003-A/wc-full-output-r1：先common官方无adapter与dense adapter完整D/D九门/最终pipeline严格等价，再common/human两个曝光CAL的WC/S四输出；合计六phase/六文件。native九门与额外provenance签名单独记录，恢复仍检查完整sidecar。初步实际CPU229.492秒通过完整11条D/D、19条刷新与flow OFF/ON六生成组合、解码失败和scope/预算拒绝，禁止CUDA/无权重/真实VAE；r5 source及51组件旧口径封存，新口径native50+单独来源签名。

完整成本5732.4秒，独立6000全cost/5970child/kill5；依累计12h及自主goal选定，不复用原r4单次授权。当前尚未新GPU/预付；先冻结source/payload与GitHub同步，再actual完整CPU/官方prepare/metadata/native-meta buffers/source/assets/import/package及fresh资源/锁/账本/磁盘。现累计6.055044055960606/12h、36jobs保持。含hash/深拷贝/同步/共享prepare，debug wall不作净E2E加速结论；不自动第二卡/训练/新增人评。以下为历史。

## 2026-10-03 完整采样与简单 S/D 刷新 CPU 接线

[82 当前证据与下一步](research/82_WC_COMPLETE_SAMPLING_AND_REFRESH_CPU.md)：新增完整官方采样核心，35 请求/36 实际更新/72 CFG 到最终返回，保持原生 horizon70/call70 清空及最后两次 warm full。五检查点13/21/33/35/36含 buffers/modes/RNG/UniPC 与实际恢复 latent；D/D严格九门和完整 pipeline 控制通过。CPU r1夹具 stride失败保持，r2 77.964秒通过；r3 178.700秒通过全部旧11条控制与17条 D/D provenance、实际 D/S 接线和失败控制。r4 122.205秒通过新增 model/group 拒绝；清理闭包绑定修正后的r5 122.224秒、19条刷新控制及当前source独立CPU审计通过；全部hook/模式/buffers/forward恢复。每轮原SHA保持，较早CPU不追认后来文件。

S确实进入后续 cache/solver/最终 latent；native forecast window 与 true-dense metadata 分开，S不进入真D历史，call70同时失效两CFG来源。官方OSI用完整probe差分，无deep目标在线校准。此为禁止CUDA、无真实权重的toy接线控制，mock decoder/writer不是视频；生产fallback6/23/27/真实稀疏核尚未闭环验证。严格九门只用于D/D，候选D/S允许输出与自适应轨迹改变。

本阶段GPU费用0，累计6.055044055960606/12h、36jobs，余5.944955944039394h，无新GPU卡。下一具体化官方WC/简单WC+S完整输出诊断的source/成本/实际部署门，再fresh准入；调试哈希/深拷贝wall不作净加速结论，不追加H2/RV/训练/人评。直接授权的r4完整104点已终态且单次授权消耗，不重跑。以下为历史快照。

## 2026-10-03 H1早晚双CAL终态：完整72格原件审计通过，CPU来源扰动分解完成

[80完整卡](research/80_WC_H1_GENERALIZATION_R1_CARD_AND_CPU.md)：source77111262a02931e01f2ca2253c2ec585e6b0852b实际CPU35后唯一run退出0；两场景各两前缀33更新/66CFG、全部九门、step13/21/33各36组件与进程内restore通过。24来源/72格/120原件240张量和96组独立float64误差、参考语义/费用/释放全部审计通过。早step12/晚step25为预登记选择，两个曝光CAL不是CONF。

S来源velocity误差0.8935%–1.7341%，D/S整组+head热耗时比1.05601–1.14293×；human早期S residual7.2962%/7.5772%超过局部5%，来源不是处处安全。未来双字段5%描述性筛查0/72（D/MF/S各0/24），dense-held velocity漂移7.2466%–40.2694%；不是视频接受门或安全寿命结论。CPU来源扰动与交叉项分解177.791秒通过：S−D velocity0.5436%–2.1606%，绝对扰动/来源0.3388–1.8274×，随场景/阶段变化且交叉项可抵消。下一仅CPU完整采样与简单S/D闭环接口准备，不自动H2/RV/训练或新增人评。

实费2717.978329秒（0.754993980h），累计6.055044055960606/12GPUh、36jobs，余5.944955944039394h，无inflight。原PIDs2674427/2674442/2674444/f1锁/GPU已释放（24MiB/noapps），1273次monitor峰值27332MiB；CPU不新增GPU费用。以下在跑/预付/旧授权文字均为历史。

下一科学缺口及CPU范围见[81完整采样准备](research/81_WC_H1_DECISION_AND_CLOSED_LOOP_CPU_PLAN.md)；先D/D完整尾部与restore等价，再明确approximate reference，不再机械追加局部窗口。下一GPU卡未选定。

## 2026-10-03 H1早晚双CAL批次CPU通过，独立6000秒卡待实际部署

[80独立卡](research/80_WC_H1_GENERALIZATION_R1_CARD_AND_CPU.md)：保持H1中间点终态，现CPU同一生产batch在同net/solver/Inference处理两请求，flow OFF/ON各完整72格/120raw；四request各33更新/66CFG/九门与step13/21/33各36组件/restore、age3实际刷新但held参考不覆盖通过。第二请求晚期nonfinite/条件变化/无paired-full保留全24/72分母与第一请求36格，挂钩恢复；实际Torch2.7.1+cu128，禁止CUDA，无真实权重/前向。r1前缀CPU56.275秒、r2批次CPU80.447秒各自source保留。

common与human_199都是曝光CAL；早[8,12]/晚[25,29]从新官方baseline按最早双CFG true-full/已付probe/两过去同CFG历史选点，不用候选误差、缺点不补选。完整成本5151.663秒，不缩矩阵挤进旧1800/4800；自主goal/累计12h队列选定独立WC-H1-GENERALIZATION-R1-20261003-A，单次6000全cost/5970child/kill5，非旧窗口复用。当前尚未新GPU/预付，5.300050075675308/12h、35jobs保持。先source/payload提交、完整实际官方prepare/UniPC下一更新13/21/33/native-meta/assets/import/双样本绑定门，再fresh资源/锁/无inflight/余额/协调槽位；不自动第二泛化/H2/RV/训练，不新增人评。以下状态为历史。


## 2026-10-03 H1首卡终态：完整18格审计通过，共同漂移占主导

[79真实结果](research/79_WC_H1_LOCAL_LIFETIME_R1_CARD_AND_RESULTS.md)：source e59b588退出0，actual CPU34、两前缀21更新/42CFG、全部九门、step13/21各36组件/restore、6来源/18格/30原件60张量及独立float64误差/费用/释放通过。age1/2 held-D预测匹配部署cache，age4 D teacher匹配部署full。S来源velocity约0.94%，整组+head省5.53%/5.84%；后续S−D预测差值1.03%–1.44%，绝对来源扰动放大1.10–1.56×，dense-held共同误差11.16%–31.58%，局部双字段5%筛查0/18（D也未过）。一个已曝光CAL/两相关CFG的固定轨迹诊断，无连续安全寿命、闭环、视频或端到端收益。

全wall889.004681秒，累计5.300050075675308/12GPUh、35jobs，余6.699949924324692h，无inflight，三PIDs2668463/2668479/2668481与f1锁/GPU释放；原失败/单次r4历史保留。继续WC，暂缓复杂来源H2/训练；下一CPU准备早/晚及另一CAL的有限泛化诊断选择规则/配对/成本，简单S/D及age基线优先。下一GPU须另具体card/source/完整实际门与fresh准入，本r1单次已消耗，不自动再投H1/H2/RV；非必要不新增人评。以下状态为历史。

## 2026-10-03 H1生产核心CPU通过，独立首卡待完整实际部署门

[79独立卡](research/79_WC_H1_LOCAL_LIFETIME_R1_CARD_AND_RESULTS.md)：同一生产前缀核心在禁止CUDA的实际环境中通过两组21更新/42CFG、九门与step13/21各36组件、18格/30raw和全部挂钩恢复；条件变化/非finite失败分母保持。原源码/来源六控制与四组分支矩阵再通过，未GPU。

既有自主goal/累计12h队列选定WC-H1-LOCAL-LIFETIME-R1-20261003-A；另计startup/import后的1414.365秒包络保留，最多一次1800全cost/1770child，不复用r4单次授权。另冻source/payload，先官方prepare/实际UniPC下一更新/native meta共同mode/assets/import完整门，再fresh资源/锁/无inflight/余额。6来源/18格不缩、S/MF不是真dense、只固定轨迹无闭环/视频。5.05310433089345/12h、34jobs不变；不自动第二H1/H2/RV/训练。以下状态为历史。

## 2026-10-03 H1 CPU接口通过，完整18格成本草案待独立执行卡

[78接口与成本](research/78_WC_H1_FIXED_TRAJECTORY_CPU_AND_COST.md)：六项来源控制、flow OFF/ON×两种未来分支四组42-call/18格配对、失败分母与30 raw roundtrip通过；禁止CUDA、无权重，r1/r2 CPU夹具失败保留，r3通过。共同官方Gamma+warp，held来源不随中间部署刷新更新，S/MF不是true dense锚点。没有真实寿命、闭环或视频结果。

保留第二已曝光CAL/step17两CFG、三来源×1/2/4、先1个deep组的草案；完整成本包络1354.365秒，不能按1200秒准入。1800仅候选下一独立卡，不复用r4已消耗单次授权；先单独runner/九门与恢复集成/实际source-assets-import-package，再新卡及fresh准入。累计5.05310433089345/12GPUh、34jobs不变，新增GPU费用0。H0/r4终态及失败历史保持，非必要不新增人评。以下条目为历史。

## 2026-10-03 H0独立r2终态：局部互补筛查2/2通过，费用/释放已审计

[完整结果](research/77_WC_H0_MODE_REPAIR_AND_R2_CARD.md)：source4c1c3a8退出0，实际CPU31/shared-eval后两臂各20更新/40CFG、九门/step13&20各36组件/进程内restore/D逐位重放全部通过；八原件16张量/source/独立float64误差/重复计时/费用/资源释放审计通过。call33/34两CFG中，C velocity RMSE29.84%/38.40%，S0.939%/0.945%，S residual4.349%/4.253%，D/S整组+head1.05615/1.05656×（耗时降低约5.3%）；固定四项筛查2/2通过。是单个已曝光CAL的局部机制正结果，无候选视频、端到端收益或稀疏来源寿命，旧r1模式失败保持。

实计708.4838515026495秒，累计5.05310433089345/12GPUh、34jobs，余6.94689566910655h，无inflight；三PIDs2662009/2662025/2662027退出，f1锁/GPU释放（24MiB/noapps）。继续WC，下一优先CPU准备既定H1三来源×1/2/4步（先1组）接口/配对/来源语义/具体成本；S/MF不是true dense锚，当前评分原件/状态哈希不是可重启全状态。另冻结下一卡，不自动第三H0/H1GPU/H2/RV/训练，非必要不新增人评。以下在跑/预留/旧授权文字为历史。

## 2026-10-03 H0独立r2 actual CPU31通过，唯一诊断在跑

[部署/单次启动](research/77_WC_H0_MODE_REPAIR_AND_R2_CARD.md)：source4c1c3a8的CPU31/默认1173→eval0/全部资产/source/import/package通过，CUDA未初始化、旧费用不变；唯一wc-h0-eval-complement-r2 fresh准入后启动，supervisor2662009/timeout2662025/runner2662027存活，模型加载和共享eval设置通过，baseline前缀在跑。共用eval适配事前显式冻结，不删shadow guard，旧r1失败保持。两CFG/四臂/step13&20/九门仍待实际结果。

1200秒全cost/1170child/kill5，child起算最大截止北京时间15:49:09。预付1/3h，账本在途5.189636594364936h/34jobs；原已结算4.856303261031603h/33jobs，实际费尚未定。只跟踪原句柄，source/payload不变、不重复提交，完成后独立source/模式/原件误差/成本/释放审计；不据初始化报方法或视频收益，不自动第三H0/H1/H2/RV/训练。以下条目为历史。

## 2026-10-03 H0实际CPU模式修复通过，独立r2具体卡待完整部署门

[CPU修复/独立r2卡](research/77_WC_H0_MODE_REPAIR_AND_R2_CARD.md)：固定原类meta网络1173默认training标志，共享eval后0；禁止CUDA/权重/前向，全部train方法为nn.Module.train，参数/buffer对象及版本未变；默认模式toy经实际adapter的四臂与失败分母控制通过。保留严格shadow eval guard和原r1失败，不追认其完整九门/互补性。r2共同eval适配显式应用两臂，不主张与r1默认模式输出等价。

自主goal选定新WC-H0-EVAL-COMPLEMENT-R2-20261003-A/wc-h0-eval-complement-r2具体修复卡，原场景/selector/回退/阈值/2状态8臂/step13&20及全部九门不变，964.475秒规划包络≤1200秒。当前未r2 GPU；先新source/payload及实际旧26+新模式/源码/资产/import/package门，再fresh GPU/全局锁/无inflight/余额，只此一次，不自动第三H0/H1/H2/RV/训练。累计4.856303261031603/12h、33jobs，余7.143696738968397h保持。以下状态为历史。

## 2026-10-03 H0首卡技术停止，费用/释放已审计，继续CPU模式定位

[终态与下一步](research/76_WC_H0_COMPLEMENT_R1_CARD_AND_RESULTS.md)：唯一wc-h0-complement-r1/source18e692e退出1，baseline20更新/40CFG，observed在首个eligible full call33触发新增 `H0 requires eval` 检查。完整四臂0、原件0，2状态/8臂分母保留，完整九门未完成；不是互补性负结果。CPU26的toy显式eval，未覆盖实际官方网络模式，先核查实际固定源码/构建与mode-sensitive路径，再无CUDA修复控制，不直接改原模型mode或重提r1。source/stage/失败回执封存，H1/H2/RV/训练后置。

全wall523.4742335593328秒已实计，累计4.856303261031603/12GPUh、33jobs，余7.143696738968397h，无inflight；原三PIDs/f1锁/指定GPU均已释放（24MiB/noapps）。另一GPU卡须新identity/source、具体范围/成本与完整实际门，不自动第二卡。以下在跑及旧预算文字为历史快照。

## 2026-10-03 H0首卡实际CPU26通过，唯一诊断已启动

[实际部署](reports/wc_h0_complement_r1_deployment_20261003.json)：冻结source18e692ebb0f23a6ed832e0d7ff74ec3a6acc0ca9，actual CPU26/C分支/完整四臂/原件误差/step13&20/source/assets/import/package全部通过，CUDA未初始化、原账本不变；源码已推送。唯一wc-h0-complement-r1 fresh准入并启动，[启动](reports/wc_h0_complement_r1_launch_20261003.json)/[现场](reports/wc_h0_complement_r1_start_observation_20261003.json)supervisor2657420/timeout2657436/runner2657438存活，初始化非终态。原GPU24MiB/noapps，child起算最多1200秒截止北京时间15:08:40，已预付1/3GPUh（在途5.044227085042899h、第33job），结束按实际全wall结算；已用4.710893751709566h/32job历史保留。只跟踪原句柄，不改在跑source或重提，不据live报互补性/视频收益。H1/H2/RV/训练后置。

## 2026-10-03 H0首卡：CPU门通过，实际部署准入待验证

用户2026-10-03 06:00:14UTC继续自主推进常规步骤、06:07:41再确认继续实验。H0首卡冻结第二CAL场景/两CFG四臂、6/23/27 dense回退与0.1/0.98，C严格过去同轨历史、真实D唯一路径；CPU原源码/完整shadow/失败分母/原件误差门通过。1200秒总cost/1170child，951.369秒规划包络含余量。当前未GPU启动，必须冻结source、actual assets/import及fresh UUID/VRAM/compute/f1锁/12h余额门；不重启r4/自动H1/H2/RV/训练。used4.710893751709566h/32jobs保留，原件不入Git。 [具体冻结卡](research/76_WC_H0_COMPLEMENT_R1_CARD_AND_RESULTS.md)。以下r4/旧授权条目为历史快照。

# WorldCache experiment rules

## 当前补验终态 — 2026-10-03

直接授权的唯一wc-mid-full-r4已执行并独立审计：104QKV/312case及九门/step13&18通过。实计1153.547616秒，累计4.710893751709566/12GPUh、32jobs，无inflight，PIDs/锁/GPU已释放。该单次授权已消耗，不重启同run或自动新增r5/H0/H1/RV；[75完整结果与下一卡边界](research/75_WC_FULL104_R4_CARD_AND_RESULTS.md)。以下准备授权为历史。

## 当前直接补验授权 — 2026-10-03

用户当前直接授权七份文件、CPU及门通过后的唯一wc-mid-full-r4≤1800秒/现累计12GPUh，见[独立卡](research/75_WC_FULL104_R4_CARD_AND_RESULTS.md)。旧1200秒及无r4约束保留其历史身份；本卡不授予自动下一窗。原已用4.390463858430222h/31jobs不变，必须actual CPU/source/assets及fresh GPU/锁/预算门。

## 最新执行授权 — 2026-10-03

[各项目累计12GPUh与恢复后队列](research/BUDGET_AUTHORIZATION_20261003.md)取代此前仅文档及旧预算限制；保留已用与历史账目，单昂贵任务，GPU优先WC。WC已用3.9117525685110333GPUh、28jobs保持，当前余额8.088247431488967GPUh。先中间刷新/全26深层覆盖准备和无扰动诊断，再H0互补性、H1来源×寿命；W1/replay已完成不重跑，RV后置。旧new4h/clean50不自动转为新队列。新runner须按明确12h权威账本校验，不能重新执行硬编码4h的旧launch。 下述2026-10-02原包适配/仅文档条目为当时快照。

- Read `EXPERIMENT_REPORT.md`, `research/02_CURRENT_STATE.md`, `research/09_NEXT_ACTIONS.md`, and `memory/handoffs/LATEST.md` before continuing. Follow the supplied plans in `plans/`; do not restart unrelated historical projects.
- User authorized experiment work on the two-card and four-card A6000 servers on 2026-09-29. Select using fresh GPU UUID, VRAM and compute-process observations. No stopping others' jobs, changing shared drivers, or treating idle utilization as admission.
- First batch: F0 and F1 (4 scenes, 1 seed, Native and official WC), one expensive job at a time. Self-imposed first-batch stop cap: 4 GPU hours including load, failure, diagnostics and flush. This is a conservative execution limit under the current user instruction, not an assertion that the plan itself grants GPU permission. Propose F2/W1 GPU scope from measured costs before expansion; no training or paid scoring in this batch.
- Keep upstream pinned and unmodified. Experimental runtime adaptations must be separately identified, versioned, and shared by both comparison paths where appropriate.
- True anchors are full computations within the current request, CFG branch and model/expert. Current shadow truth never updates deployed state. Reset on requests and model/condition changes. Fail safe on nonfinite inputs or insufficient anchors.
- Synthetic/CPU tests are implementation evidence only; no generated video or quality/latency claim without real receipts. Record UNKNOWN and TECH_BLOCKED honestly.
- User requests that every meaningful code/config/result change be committed and synchronized to the private GitHub repository `kuangda-source/worldcache-omr-experiments` before reporting completion. Keep code, plans, tests, manifests, summaries and small receipts in Git. Never commit credentials, machine connection secrets, weights, bulk tensors, or videos. Record artifact paths/hashes instead. Do not force-push or overwrite unrelated changes.
- A GitHub connector atomic tree/commit/ref update may be used when local Git credentials are unavailable. Verify the resulting commit and file tree; preserve remote README and parent history. Record local-to-remote mapping under ignored `.sync/`.

- Maintain `EXPERIMENT_REPORT.md` as the stable cross-device experiment overview. After meaningful experiment changes, update its evidence-bound results/decisions plus next actions and handoff in the same sync. Follow its Git conflict and single GPU submitter protocol; Git synchronization is not a distributed runtime lock.

- This repository is WorldCache-only. OMR plans, Wan/LongLive support preparation and future OMR edits belong to private kuangda-source/omr-experiments. Do not switch this queue to OMR; finish existing frozen WC work first. Shared legacy wcomr package/project identifiers and historical deployed paths are retained for compatibility.
