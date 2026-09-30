## 最新接续 — 2026-10-01：固定scalar重放终态，自动成像评价准备

source31a797d的`w1-replay-r1`已终态，原supervisor2471255/timeout2471260/runner2471262全部退出、锁可用、GPU1 24MiB/noapps；424监控点无观察到其他compute，所有9接受artifact/source hash核验通过。official14项/scalar OFF-ON18项全真；原8场景72call/frozen schedule/past-anchor技术通过，295scalar预测/0fallback、57自然与冻结判据差异。候选7接受、robot_054 VIDEO_REJECTED（官方WC8接受），拒绝保留原8分母，不能补跑或安全绕过。总结是FROZEN_REPLAY_TECH_PASS_QUALITY_UNASSESSED，非全视频接受/方法质量收益。

7可比视频对都有像素差异、6/7帧间RGB变化较小，两个AV更明显；不能判更稳或动作消失。带hash/首shadow/顺序加载时间不作clean测速。CAL8 scalar机制信号保持，尚无语义/物理、整体质量、干净速度或独立确认结果；暂不加W2。

监督2177.784138秒，累计3.59998488161299/4GPUh，余0.40001511838701h，无在途。下一独立MUSIQ成像维度评价已本地实现，17项CPU检查和Linux四种几何的官方Resize精确预处理对照通过，已有权重离线CPU加载/forward通过；冻结终态reference/candidate/checkpoint/source哈希，原8分母/7接受对、全部93帧，cap600秒从原余额扣除。尚未部署/未GPU评分；下一步源码同步后LinuxCPU与freshGPU/预算/锁准入，仅提交一次`outputs/w1-imaging-r1`。

Qwen3-VL2B/8B只有processor/tokenizer/config无权重，标准大judge/环境不就绪；原42条VQA问题已hash绑定取回，但未评分。MUSIQ只回答成像维度，不能替代语义/物理/Joint或通过整体质量门。不要求人评，不训练/付费/扩额。

证据：[重放结果](../../research/24_W1_FIXED_REPLAY_RESULTS.md)、[完整汇总](../../reports/w1_replay_r1_summary.json)、[审计](../../reports/w1_replay_r1_audit.json)、[成像评价卡](../../research/23_W1_IMAGING_EVALUATION.md)；终态后才部署下一source，原运行source31a身份保持。未来预算/质量/clean计时资源不足时形成具体方案再交用户重大决策。

## 以下为历史快照

## 最新接续 — 2026-10-01 00:29:13 北京时间：scalar固定重放实机运行，两门通过

GitHub/source `31a797d363a6ebdcf7d8443f84f7d0a0bb073797` 已部署，archive/source hash匹配，Linux63项CPU检查通过。新任务 `outputs/w1-replay-r1` 已于2026-10-01 00:16启动；supervisor2471255、timeout/PGID2471260、runner2471262均live，GPU1仅观察到此runner。继续同一任务，不部署新代码或重复启动。

首AV official重放对原CAL8 OFF全部14项严格检查全真；scalar OFF/ON全部18项检查全真、8个shadow点，两个候选输出均ACCEPTED。首候选计入原8成员，当前第二个common场景scalar OFF生成，完成1/8；全批和终态审计未完成。首候选完整93帧对WC RGB MSE975.370840、MAE18.228840、PSNR18.239106dB；相邻帧RGB MAE候选2.274710、WC4.391376。像素距离/较小帧间变化不证明正确性、质量或物理改善；带hash/诊断时间也不作干净测速。

启动前结算2.995044843356/4GPUh；观察时另有0.218519319h在途，未计入旧ledger。单batch总cap3000秒不变，所有加载/诊断/失败/flush计费，不能用旧余额准入第二任务。无新增预算、训练、付费评分或人评。原CAL8 scalar MECHANISM_ONLY结论及misc恶化保留。

证据：[部署](../../reports/w1_replay_r1_deployment_20261001.json)、[启动](../../reports/w1_replay_r1_launch_20261001.json)、[实时快照](../../reports/w1_replay_r1_live_observation.json)。下一步只读观察原handles；终态后验证PIDs退出/锁/GPU归属/源码与产物hash，归档原始runner/supervisor/audit并更新实际wall账本；用hash绑定CAL8 reference重新验证summary。失败/拒绝保留，不补样本或自动重跑。完整通过仍只证明固定schedule候选技术可运行，质量/clean计时/独立确认未完成。

## 以下为历史快照

## 最新接续 — 2026-10-01：fixed replay runner本地实现/CPU通过，待部署

原CAL8终态、scalar MECHANISM_ONLY和预算2.995044843/4h保持。已实现scripts/run_w1_replay.py、supervise_f1.py --w1-replay（单batch cap3000秒），以及replay_results/video_difference/summary CLI。19项本地针对性CPU检查通过；[回执](../../reports/w1_replay_local_cpu_20261001.json)。与旧CPU模块24项范围有重叠，不叠加计数。原manifest固定参数/样本/trace/reference hash未改；metadata初始NOT_IMPLEMENTED标签是冻结时历史，当前以此快照和后续运行回执为准。

runner先hash绑定完整CAL8/reference screen并重新计算screen、校验setup/input/runtime/scheduler/VAE；首AV official replay严格复现旧OFF，scalar OFF/ON output/cache/decoder/video及额外calibrator结束状态和controller记录一致，ON真值只评分。余7仅scalar OFF；每sample用自身状态，有限模型输出/固定独立blockcounts/实际controller past anchors/peak memory记录，完整93RGB对旧WC距离与temporal variation描述（非质量）。拒绝/异常保留；SIGTERM尽可能写TECH_BLOCKED，所有真实墙钟计费。无新GPU运行。

下一步：commit/hash部署并Linux CPU gates；重新核验旧PIDs/锁/预算、全部reference视频hash、GPU1 UUID/VRAM/apps，只启动新唯一outputs/w1-replay-r1一次。前门失败立即停止，不能据观察超时重复提交或改在跑代码。上限3000从余1.004955157h扣除，无扩额/训练/付费/人评。部署与launch receipt/PIDs/logs、总体docs和预算需同步GitHub。

## 以下为历史快照

## 最新接续 — 2026-09-30：CAL8终态，scalar机制信号，固定重放准备

w1d-cal8-r1（部署源62f1c0d）完整终态：8/8场景、每样本8点/17项OFF-ON检查全真；16接受视频重新hash匹配，原supervisor2461004/timeout2461009/runner2461011均退出，exit0/无stop reason，锁可用、GPU1 24MiB/noapps，699监控点无观察到其他compute。原始runner/supervisor/audit/summary/analysis/figure已归档reports/w1d_cal8_r1_*；旧live与partial文件都是历史，不得重启旧任务。

冻结screen MECHANISM_ONLY_CAL8：scalar7/8联合velocity/postwarp改善，等样本均值比0.759184683/0.893679139，0fallback；misc两指标恶化保留。shrink0/8 velocity改善，均值1.306201721，本CAL8收缩线不送闭环。8样本皆有内部排序反转，共40 dependent point-mode对比；组上scalar均7/8改善，暂不加W2。没有视频质量/干净速度/独立确认正结果。旧AV四工程点负结果保留原范围；CAL是开发数据。详细[结果](../../research/21_W1D_CAL8_RESULTS.md)。

本批监督3590.173902秒/0.997270528h，累计2.995044843355815/4h，余1.004955156644185h，无在途成本。下一固定schedule scalar-recent闭环最多3000秒/0.833333h，仍原budget内。CPU模块fixed_replay.py及24项针对性检查通过，协议已冻结完整8原trace/hash/参数；[准备卡](../../research/22_W1_REPLAY_PREPARATION.md)、[manifest](../../manifests/w1_fixed_replay_protocol.json)、[CPU回执](../../reports/w1_fixed_replay_cpu_20260930.json)。runner/监督模式尚未实现、未Linux部署、未CUDA/生成测试，不能称候选已经跑过。

下一步自主实现有监督runner：firstAV新official fixed replay对旧OFF严格复现，再scalar OFF/ON自身parity，通过后原其余7scalar OFF；共10generation，firstcandidateOFF计入8成员。自己当前latent/probe/full anchors，shadow truth只评分，不回放旧latent。不择优/替换misc；拒绝保留，技术异常停止。预算forecast2224.619秒+30%=2892.004秒，cap3000；提交前重新核验旧handles/锁/余额/GPU/source/hash/LinuxCPU。尚无第二任务/额外预算/训练/付费评分/人评。代码与docs推送后的新HEAD不改变旧source62运行身份。

## 以下为历史快照

## 最新接续 — 2026-09-30 23:09：5/8技术通过，分布分析就绪

原w1d-cal8-r1任务持续运行；supervisor2461004/timeout2461009/runner2461011均live，source62f1c0d保持。前5个样本各8诊断点、17项OFF/ON检查全真；第6个physics_045 OFF生成。当前[实时进程/GPU快照](../../reports/w1d_cal8_r1_live_observation.json)更新；22:48的runner/partial summary文件仍只归档前2样本，不是最新/终态。启动前结算1.997774315h，23:09在途0.668417069h额外，batch6000秒/原总4h cap不变，无第二任务。

已完成只读分布分析src/wcomr/w1d_analysis.py与CLI scripts/analyze_w1d_cal.py，严格校验每个分区非空/不重叠/完整覆盖、候选坐标匹配、group MSE与reference energy能重建整体值；按样本等权汇总，零官方误差比留空。scripts/plot_w1d_cal.py输出同状态散点/排序反转计数/velocity时间空间通道图，显示dependent/latent坐标范围，不把组当独立样本。11项针对性CPU检查通过，真实部分回执CLI与私有部分图检查通过；[CPU回执](../../reports/w1d_analysis_cpu_20260930.json)。仅本地代码，未部署到正在跑的job，无新科学结论或额外GPU成本。

终态归档/审计后执行原screen与新descriptive analysis；plot依赖可用pip install -e '.[analysis]'安装到本地环境。所有partial显式NO_DECISION。接续原PIDs，不重启/改公式/增加样本。没有重要问题时按协议自行收尾和评估下一有界任务。

## 以下为历史快照

## 最新核验 — 2026-09-30 22:48：CAL8 W1-D运行，2/8技术通过

源`62f1c0d03ab7d789a7e5a86235e2d27cf920825c`，部署archive/源码hash一致，Linux44项CPU检查通过。已真实启动`outputs/w1d-cal8-r1`，GPU1 UUID GPU-cebf7119-cf03-23b9-e192-cd196332b704；supervisor2461004、timeout/PGID2461009、runner2461011 live。22:48只读观察：前两个AV/common样本各8点、四pair完整、ACCEPTED、17项OFF/ON检查全真；第三个human_199 OFF在跑。各样本点先按OFF trace冻结，truth只评分，局部decode flags恢复。此为非终态快照，不是全批成功。

本批一次加载8off/on，上限6000秒/1.666667GPUh，所有成本从原4h cap扣除。启动前已结算1.9977743149465987h，观察时在途另计0.32540379007657366h；旧ledger余额未包含在途，不能用来准入新任务。仍只有此昂贵任务；原FRPC/SSH可用，无需重新建隧道或索取凭证。勿修改部署源码、重启或另起作业。

证据：[部署](../../reports/w1d_cal8_r1_deployment_20260930.json)、[启动](../../reports/w1d_cal8_r1_launch_20260930.json)、[进程/GPU/日志](../../reports/w1d_cal8_r1_live_observation.json)、[真实runner部分快照](../../reports/w1d_cal8_r1_live_runner_snapshot.json)、[部分汇总](../../reports/w1d_cal8_r1_live_partial_summary.json)、[协议/进展](../../research/20_CAL_AND_W1D_PREPARATION.md)。部分scalar等样本velocity/postwarp误差比0.666140/0.820278；shrink1.132306/1.057422，无fallback。LIVE_PARTIAL_NO_DECISION：不据前两样本调公式、判全批成败或进入候选闭环，无质量/干净加速/独立确认结论。旧四工程点NO_GAIN_IN_SCOPE仍是旧范围，不向CAL扩张。

下一步：只读查原handles直至终态；原PIDs退出与锁释放、GPU监控归属/源码/视频哈希核验后归档runner/supervisor/audit及实际wall账本。完整8PAIR_PARITY_PASS才按固定screen汇总；部分/失败保留，不能补样本或重启凑全。随后按机制证据与实际余额自主推进；预算扩张/训练/重大方向决策再交用户。当前无需人评/训练/付费评分。Git只同步代码/小回执/文档；后续本地文档commit不改变此源62f1c0d运行身份。

## 以下为历史记录

## 最新核验 — 2026-09-30：局部解码策略复现通过，CAL已冻结

源33f080b decoder-policy-r1两个fresh进程均exit0；72net/trace/cache/latent匹配旧官方参考。decoder实际参数/buffers/normalization及运行设置相同；cuDNN benchmark=false/deterministic=true只在decode内部、TF32保持原值、离开后恢复；decode/guardrail/save/MP4/全部93帧RGB与PTS严格相同。结论LOCAL_DECODE_POLICY_REPRODUCTION_PASS，仅本工程样本/所测策略，不是独立根因证明、质量、新方法或干净耗时收益。

最新审计：supervisor2456556、child2456561/2457589、runner2456563/2457591均退出；锁可用，GPU1 24MiB/noapps，无在途任务。预算1.9977743149465987/4h，剩余2.0022256850534013。旧scalar/shrink四点NO_GAIN_IN_SCOPE不变。详见research/19_DECODER_POLICY_RESULTS.md和reports/decoder_policy_r1*.json。

官方基准1044条reference_video/image_name元数据全部连接固定prompt，0缺失/不符；reference+TFIDF0.85形成1043组，原recording/session独立性未证。CAL24及首批8在新生成前按固定hash/配额冻结，排除4工程组；DEV/CONF未冻结。见manifests/cal_v1.json。下一轮research/20_CAL_AND_W1D_PREPARATION.md：CAL前8稀疏同状态/布局明确的时间空间通道诊断，三公式冻结、所有路径共用新解码策略、off/on验证、安全拒绝保留分母。提议单batch6000秒/1.666667h，从现有余额扣除，尚未实现/启动；提交前重核资源/锁/预算/源码。不要补人评或追加GPU预算。

## 以下为历史记录

## 最新核验 — 2026-09-30：差异已定位decode输出

同源fa042d3 stage-r2两新进程均exit0，净监督634.230530秒。72net输出/cache/trace/采样/runtime identity相同，sample与decode输入hash相同，decode_output首先不同。两个guardrail各自输入输出相同；93帧完整RGB全部hash不同、时间戳相同。根因仍UNKNOWN，decoder实际权重/状态hash和局部确定性策略待验。见research/17_DECODE_INTERVAL_RESULTS.md及18_DECODER_POLICY_GATE.md。

最新终态审计：supervisor2453240及两child2453245/2454606与runner2453247/2454608均退出；锁可用，GPU1 24MiB/noapps，无在途任务。预算1.82321776939763/4h、剩余2.17678223060237。r1输出目录问题导致首见证成功而第二child显式取消，原失败/费用保留，勿误写两进程通过。下一轮卡PREPARED_NOT_IMPLEMENTED_NOT_RUN，不能当运行许可或实时准入；提交重核预算/锁/GPU，保护共享源码。数值候选仍NO_GAIN_IN_SCOPE，不推进闭环/不要求人评。

## 以下为历史记录

# Latest — recent-pair negative; cross-process post-model reproduction next

AllGPUtasks terminal. Recentrevision source99f554f,supervisor2447006/timeout2447012/runner2447014gone;8within-runoff/oncheckspass,artifactsrehashmatch,lockfree,GPU1released24MiB/noapps. Budget1.560151151220004/4h,remaining2.439848848779996. No currentjob.

Defaultscalar/shrinkvelocitysum-MSEratio2.531/5.395;recentdecay0scalar2.354,shrinkunchanged5.395,both2/4improve.NO_GAIN_IN_SCOPEallversions,notmethodwide rejection. Do notenterclosedlooporcontinueuninformedscalarparamchanges. Detailedresearch/15_W1_S1_RECENT_RESULTS.md,raw/summary/contrast/audit/crossdecode receiptsunderreports/w1_s1_recent_r1*.json.

Importantreproductiongap:cross-runall72officialoutputhashes/finalcache/trace/inputs/samplingand4pointofficial+shrinkmetricsexactlyequal,butMP4hashesand93/93decodedRGBframesdiffer;CPUdecodingMSE31.026577/MAE3.604356,max94. Notmerelymetadata. Within-processoff/onvideohashmatchesineachrun; numericcontrastvalidONLYatmodelstatelevel. Firstdifferencefinalsample/VAE/guardrail/save/codecUNKNOWNbecauseintermediatehashesmissing. Do notguesscauseorclaimvideo/qualityequivalence.

Next implementresearch/16_POST_MODEL_REPRODUCTION_GATE.md:readonlystagewrappers(samplefinal,decodeinput/output,guardrailinput/output,saveinput,encoded/decoded),twofreshofficialprocessesserialunderone<=900s/0.25hjob,existinglock/admission/conflictstop/budget. Noactivationyet. Observebeforealteringdeterminismflags;sharedruntime/sourceuntouched. Afterreproductionexplanation,chooseF2orW1-DlocaldiagnosticbeforeW2. No humanreview,training,paidscoring,extra budget. Datasetinventory1044fixedtext2worldpromptscounted;CALnotfrozen/source-link+neartemplatespending;4engineeringsamplesexcludedconfirmation.

## Historical snapshots

# Latest — single recent-pair revision live

Source99f554f,archive65a4c0225a7925a6ee182bb291e33f71141e6e02fc5b1b20bfbdbb5b60ed9de1verified,16local/16LinuxCPUchecks pass. outputs/w1-s1-recent-r1 launchedonce <=900s,supervisor2447006/timeout2447012/runner2447014verifiedlive,offgenerating. NewadmissionGPU1 24MiB/noapps;actualprojectcacheenvverified. Do notmodifyrunningcode/submitsecondjob. BudgetsettledBEFORErevision1.4127196775542366/4h,inflightadditional.

Revisiononlydecay0latesttruefullpairvsdefault0.9;original AV/seed0/4calls15,16,37,38/72calls/WC70/warpunchanged,shrinkunchangedcontrol. Newprotocolmanifests/w1_same_state_recent_protocol.json. Onterminalcollectw1-same-state.json,supervisor,budget,process/lock/GPU/video-hash audit;runlocal summarize_w1_same_state.py,thencompare official72hashes/config andshrinkmetrics withr2. EarlierdefaultsNO_GAIN_IN_SCOPE scalar2.531/shrink5.395velocityMSEratio,2/4improve;do notlaunchclosedloopfromdefaults. Onefixedrevisiononly,noparameterscan. Quality/candidatevideos/independentCALnotestablished. Humanannotationnotrequired.

## Historical snapshots

# Latest — W1-S1 r2 terminal, default no-gain; recent-pair revision prepared

Source7e5bc10,r2exit0,8checks pass; originalPIDsabsent/lockavailable/GPU1released24MiB/noapps. AllvideoSHA256rehashmatch. Sameofficial4selectedstates:scalarvelocitysum-MSEratio2.531189803,shrink5.394980328,both2/4improve;no fallback.DefaultNO_GAIN_IN_SCOPE,notmethodwide rejection;earlier15/16improve,middle37/38worsen. Officialvideosonly,nocandidateclosedloop/qualityclaim.

Budget1.4127196775542366/4h,remaining2.5872803224457632h. Nextonefixedrevision:decay0latesttruefullpairbeta,allotherprotocolunchanged;shrinkcontrolunchanged. manifests/w1_same_state_recent_protocol.json and supervise_f1.py --w1-same-state --w1-recent-calibration. Localtargeted16CPUtests pass. Needsourcecommit/hash deployment/freshadmission thenuniqueoutputs/w1-s1-recent-r1 <=900s. No secondrevisionwithoutnewmechanismevidence. Reportresearch/14_W1_S1_INITIAL_RESULTS.md andr2raw/summary/auditreceipts. Humanannotationnotrequired. Priorcacheinitfailurearchived/charged,explicitcachefixretained.

## Historical snapshots

# Latest — W1-S1 r2 generating; inspect this identity

Source7e5bc10,matchingarchive f40c3e9d669128d54c041410e142852cc4f467d927db5fdafe0051c042d40de7. r2supervisor2444752/timeout2444757/runner2444759live,outputs/w1-s1-r2,max900s. Cachepathprojecthfhub verifiedinactualprocess;offgenerating. Prior r1 failedinit0generated after75.011195s becausecacheenvomitted;fixedin supervisor and6local+6Linuxsubprocesschecks pass. AlloldPIDs verifiedgone;newadmission24MiB/noapps. SettledbudgetBEFOREr2 1.266033649245898/4h,ongoingcostextra. No secondjob orrunning-sourceedit.

Afterterminal: take w1-same-state.json,supervisor.json,budget andGPU/process/lock/video-hash receipts; run local scripts/summarize_w1_same_state.py. Local7receipt-summarychecks pass;thatcodeisnotdeployedtor2. Triadscoredonexactofficialtrajectory withtruepastfullanchorsandpinnedcandidate-specificwarp;currenttruthscoreonly. Need72output/cache/video/traceoff-onparitybeforemechanismclaim. Manualannotationnotrequired. Candidateclosed-loop/independentCAL/quality/cleanspeedremainpending evenonparitypass.

## Historical snapshots

# Latest — W1-S1 r1 initialization failure archived; cache fix ready

r1 sourcef43e0a1 supervisor2443666/timeout2443671 exited1 after75.011195s,0generatedruns. MissingHF_HUB_CACHE causedofflineGuardrail1 path to default incompletecache. Actual authorized projectassets remainready. Fixedsupervisor nowsetsHF_HUB_CACHE=project/hfhub;6local subprocesschecks pass. Budget1.266033649245898/4h. Do not retryr1 or overwrite outputs; nextverifygonePIDs/lock/projectcache,deployfixedsource,launchr2<=900s once. prior19LinuxCPUchecks validatedsame-stateimplementation;noGPUdiagnosticresultyet.

## Historical snapshots

# Latest — W1-S1 implementation ready for deployment gate

Same-state3candidate diagnostics implemented.58localCPUtests pass; protocol manifests/w1_same_state_protocol.json freezes4engineeringcalls anddefaults. check_w1_parity.py --same-state does newversionoff/on invariance; supervise_f1.py --w1-same-state enforcesonejob/900s, globalprojectlock/admission/conflictstop/budget. Next verify LinuxCPUtests andmatchingarchive under lock, then freshlyadmitGPU1 andlaunch w1-s1-r1 once. NOT_GPU_RUN atthissnapshot. Priorbudget1.245197206/4h; needremote recheck. Do not rerun F1/W1-P0. No humanannotation gate.

## Prior recovery snapshots

# Latest — W1-P0 terminal verified; W1-S1 preparation next

2026-09-30 18:52 北京时间实时恢复核验。GitHub/local 源码恢复基点 `75c66bd`，运行部署源为 `d98f447`。W1-P0 supervisor2439296 / timeout2439301已退出，exit0，无 stop reason。原始回执已取回，所有7项checks通过；72次输出、38full/34skip、trace、最终缓存和视频哈希严格一致，4个诊断点数值有限。两份远端视频重新哈希匹配。结果仅限官方WC、单个AV工程样本，不是候选收益。

累计1.2451972062057919/4GPUh，剩余2.754802793794208h。共享监督锁观察时可获取，无项目生成脚本活跃；GPU1 UUID GPU-cebf7119-cf03-23b9-e192-cd196332b704，24MiB/no compute apps。提交前重核，不视为持续资源保留。数据盘约677GiB可用，根盘约13GiB可用，新增文件用数据盘。

继续使用既有终端侧FRPC项目visitor后SSH，私有连接信息在ignored configs/hosts.local.json。本次已实际登录，不需重复建隧道或索取凭证。共享FRP不改动。另一台历史称四卡A6000的机器实际为RTX6000Ada，本次未重核，当前无需切换服务器。

下一任务：research/13_W1_S1_PREPARATION.md，状态PREPARED_NOT_IMPLEMENTED_NOT_RUN。实现官方同一轨迹的三近似器独立评分；现有scalar/shrink forward会改变部署，不能直接用于同状态三臂。先CPU因果性及状态检查，再新版本实机无扰动验收，准备<=900s/0.25GPUh有监督任务；本次恢复没有新增GPU运行。人工语义标注不是W1门槛。报告research/12_W1_P0_TERMINAL_RESULTS.md和reports/w1_p0_r1_{summary,recovery_audit}.json为此次结果依据。

F1 r3仍为终态：Native3接受/1拒绝，WC4接受；三组E2E比1.476–1.602。暂无新方法正结果或质量等价结论。仅继续WorldCache主线，不扩预算/训练/付费评分。代码、回执和总文档须同步GitHub，视频及秘密不入Git。

## Historical handoff snapshots (superseded by the terminal recovery above)

# Latest — W1-P0 r1 running; F1 terminal retained

Official shadow off/on parity gate launched once in outputs/w1-p0-r1, source d98f447, verified supervisor2439296 / timeout child2439301. Fresh GPU1 admission24MiB/no compute apps. Local49tests andLinux13CPU/fake-GPU tests pass; source archive hash matches. Hard bound900s, charged to original4GPUh cap. Settled BEFORE gate1.09256762723128h; in-flight cost extra. Check reports/w1_p0_r1_launch_20260930.json and live process/terminal receipt before any action. Do not modify deployed source during run.

Gate compares sameAV/seed officialWC off/on:72output hashes, deployment counts/trace, finalcache and video hashes; selectedshadowcalls15,16,37,38. A pass would validate only this engineering sample/official path, not scalar/shrink candidates or quality. Full-video review of F1 remains pending. No second expensive job.

## Prior context (historical process status)

# Latest — F1 r3 terminal, paired timing available, quality pending

Supervisor and both children verified absent; GPU1 released (24MiB, no compute apps). Both arms exit0: Native3accepted/1VIDEO_REJECTED(physics), WC4accepted. All4cases attempted per arm. Seven accepted videos locally hash/full93-frame decode pass; full-video quality review still pending.

All terminal receipts now reports/f1_smoke_r3_{native,worldcache,supervisor}.json. summarize_f1.py passed matched actual setup/input/protocol checks; reports/f1_smoke_r3_summary.json has3accepted pairs. E2E ratios AV1.475529(cold),common1.601593,robot~1.600; no aggregate/no quality-equivalent claim. Execution monitor audit reports/f1_smoke_r3_execution_audit.json. Cost1.09256762723128/4GPUh settled, remaining2.90743237276872h; no live task.

Next: read research/11_F1_R3_TECHNICAL_RESULTS.md; review complete videos; build bounded W1 parity runner, then real-model diagnostics off/on invariance, state/VRAM/cost gate before CAL experiments. Local shadow prototype/tests not yet deployed or CUDA validated. Do not rerun F1 from stale earlier notes. Keep exact approved sampler72calls/WC70horizon. No direction switch or training now.

## Historical snapshots (not current process status)

# Latest — r3 Native terminal, WorldCache live

Native r3 attempted all4:3accepted (AV/common/robot),1VIDEO_REJECTED (physics); exit0 means outcomes recorded, not whole-batch pass. Supervisor measured1322.461758s. Terminal Native receipt is reports/f1_smoke_r3_native.json. Settled budget now0.8406482060750325/4GPUh, with ongoing WC cost additional.

Supervisor2431971 is still live; current WorldCache timeout child2435496 was verified live after fresh admission. Remote outputs/f1-smoke-r3/worldcache. Snapshot reports/f1_smoke_r3_worldcache_start.json is NOT terminal. No paired ratios yet. Inspect same process and receipts; do not restart or change deployed source57c8660. Local W1 preparation has not been deployed.

## Earlier snapshots (superseded for live status)

# Latest — F1 r3 live, inspect before any restart

R3 supervisor2431971 and initial Native timeout child2431976 launched after fresh admission (GPU1 24MiB, no compute apps). Remote outputs/f1-smoke-r3, source57c8660. 32 local tests, 11 Linux CPU/fake-GPU tests pass; source archive hash matched. Outcome protocol v1 uses official keep_going, records rejects without saving rejected outputs, attempts all frozen cases; same model/sampler/WC settings. Charged BEFORE launch0.4732977178361681/4GPUh; current in-flight cost is additional and not yet settled. Read reports/f1_smoke_r3_launch_20260930.json. Do not alter deployed source during run.

## Prior r2 evidence and protocol context

User chose current-code technical comparison first on2026-09-30. No protocol decision remains pending. Four Native/WC pairs, same frozen inputs/seed/93frames/432x768, UniPC/Karras35requested36actual72CFGcalls. Preserve original WC70-call horizon and record counter resets; not paperEuler reproduction. No prototype installed in F1.

F1 r2 deployed source4814657 with matching archive SHA e6229786e3ffcf1152cbd04dc3ab298ebb480902b278b61d84abed6a4c91bdb2. Local29tests pass, Linux8measurement/protocol/supervisor tests pass. Runner validates exact schedule, source hash, actual counts, and persists diagnostics before assertions. Per-call trace measures actual deep execution and WC counters identically in both arms.

TERMINAL remote root /home/gaokuangda/data/gkd/worldcache_omr, output outputs/f1-smoke-r2. Supervisor2427723 FAILED; Native timeout child2427728 exit1 after1042.542395s. Two Native samples completed; physics_001 rejected by video guardrail. No WC arm. Preserve failure denominator and inspect continuation handling; no safety bypass. Local terminal receipts: reports/f1_smoke_r2_supervisor.json and reports/f1_smoke_r2_native.json.

Budget now0.4732977178361681/4GPUh; remote reports/budget.json authoritative. R1 partial output is not reused for paired timing. No paired speed/quality result, no full-video quality review yet.

Access: two-card TCP SSH localhost33621 usergaokuangda, identity ~/.ssh/id_ed25519, HostKeyAlias=[localhost]:33620, StrictHostKeyChecking=yes. Task FRP .sync/frp_tcp; do not duplicate/shared FRP changes. Four-card login recovered (actual4RTX6000Ada), prepared two-card used. Runtime isolated; shared environment/source/cache unchanged. Projecthfhub links core caches read-only and holds all new safety assets.

All assets hash-verified, core load and full safety-pipeline compatibility passed. Guardrail access nowHTTP200. No more readiness probes needed. Currentcore adaptation: missing model dirs supplied from pinnedNVIDIA source, exact-hash registration adapter skips unrelated14B training example. Botharms share it, eager and matched offloading retained.

Latest user request: integrate latest discussion into current plans. Both plans now v1.1. Add W1-D downstream error diagnostics, non-GPU L0 audit, L1 Wan5B native/CFG-only/four-step+CFG baseline only after F1 and reserving F2/W1 budget (up to2GPUh FROM existing4h cap); J6/X3/J5-P conditional later. Read source manifest and research/09_NEXT_ACTIONS.md. No GPU job launched by this plan edit. User requests every meaningful change pushed to private GitHub; exclude weights/videos/tensors/secrets.

Cross-device entry: user requested a PhysCache-style project experiment document. `EXPERIMENT_REPORT.md` now provides the stable Chinese overview, result/evidence tables, failure history, synchronization protocol and next-dialogue prompt. Read/update it with the queue and handoff. Documentation-only update; no new runtime observation or GPU launch.

Outcome continuation prepared: r2 PIDs verified absent. Official inference keep_going returns no video for a rejected sample; new observer records text/video decisions unchanged, keeps failure denominator and permits attempting remaining original cases. Unknown errors still abort. Fresh r3 planned for both arms with same sampler/source/model. 32 local CPU tests pass. Inspect new launch receipt before any further launch; this note alone is not a launch.

Read-only continuation observation at Unix1790761244.9133024: supervisor2431971 and child2431976 live, Native GENERATING first AV sample, model load74.685959s, zero completed outcomes. New local summary CLI/tests are not deployed into the running job. After terminal receipts, archive both arms and supervisor under reports/f1_smoke_r3_{native,worldcache,supervisor}.json and run scripts/summarize_f1.py as documented in EXPERIMENT_REPORT.md. Summary is receipt evidence only; artifact integrity, GPU exclusivity and full-video review remain separate.

Latest verified r3 progress: first Native AV accepted, next common scene generating. First video copied to ignored reports/private/r3/native-av.mp4 and hash/full93-frame decode verified locally (receipt reports/f1_smoke_r3_first_native_decode.json). E2E314.462688s/denoise256.631392s;72full/0skip. This is not a paired speed or full-video quality result. Running server source remains unchanged.

W1-D preparation is local only: src/wcomr/shadow_metrics.py scores distinct residual/velocity errors and explicit-axis groups without model/cache access. Four CPU tests cover ranking reversal under an anisotropic synthetic map, read-only/RNG invariance, zero-reference and invalid values. This is not a real shadow runner or a WorldCache quality result. Do not deploy during F1.

W1 local preparation advanced: shadow_forward.py implements hash-gated sparse same-call deep-tail truth for official/scalar/shrink. begin_request(identity) mandatory; direct deep blocks+head only, RNG/buffer restoration; measurement.py ignores shadow-active hooks.48 local tests pass including pinned-forward toy output/cache/anchor parity and random/buffer restoration. Not deployed to F1 and not real-model validated. Need a bounded W1 runner plus real-model output parity/cost gate before experiments. Latest live r3 observation: Native two accepted, physics generating; retain original process identity.

Latest live progression: Native r3 physics_001 was VIDEO_REJECTED (72full/0skip), no physics mp4 exists, and original robot_000 now generating. Explicit evidence: reports/f1_smoke_r3_rejection_continuation.json (timestamp, source receipt hash and live ps included). Two Native accepted plus one rejected; not a whole-batch pass. Keep same supervisor2431971; WorldCache will follow only when Native arm exits successfully with all outcomes recorded.

Latest WC observation: firstAV accepted; common now generating, supervisor2431971/child2435496 verified live. FirstAV72calls/38full/34skip, counter reset atcall71 matches frozen policy. Actualsetup/provenance compared with Native and matched. E2E213.118537s/denoise152.435226s are raw single-sample observations, no whole-batch/quality-equivalent speed claim. Snapshot reports/f1_smoke_r3_worldcache_first_snapshot.json is NOT terminal. All3accepted Native videos locally hash/full-decode pass (native_integrity receipt).

W1-P0 ready to deploy: check_w1_parity.py runs original officialWC forward then shadow instrumented same model/seed AV, calls15/16/37/38, compares72output hashes, counts/trace, final cache hash and video hash. --w1-parity supervisor launches one bounded900s task, charged to originalbudget.49CPUtests pass. No GPU launch implied by this note; inspect any w1-p0-r1 launch receipt before acting. Full-video quality remains pending, no candidate efficacy test yet.

Review UI deliverable: ignored reports/private/r3/review.html generated by scripts/build_f1_review.py; local server127.0.0.1:8765 (execsession39197), IAB tab2 marked deliverable. All7videos ready/duration5.8125/noerrors;firstpair playback ended, no quality fields filled. User/nextagent can replay full videos and export observations. This is explicitly nonblind engineering review, not final quality evidence. If server exits, reopen local HTML or serve that directory locally. W1-P0 latest live check still off pass generating32/36, no completedruns/errors yet.

LATEST USER SCOPE CORRECTION: Manual semantic review is NOT an F1/W1 gate. Original F1 covers generation/spec/cache/VRAM/time; final-quality human comparison appears later in plan section4.4. Prior repeated full-video-review-pending notes are a quality-claim limitation, not a blocker. Do not require user annotation or recreate PhysCache evaluation workflow. Continue running W1-P0 and numerical diagnostics; the review page is optional. No stop/restart of current job implied.
