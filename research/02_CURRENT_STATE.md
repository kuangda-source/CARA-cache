## 最新控制准备 — 2026-10-01：原8/42x3已冻结/实现/CPU通过，尚未控制GPU

原VQA/source1f326b5已终态、6平1misc降/robot拒绝，累计3.629295697609584/4GPUh、余1334.535秒，无GPU在途。新控制协议在看原方法代理后/任何控制答案前冻结，非盲：原8/42参考题x matched_repeat/blank/cyclic mismatch，共126答案，同judge/原prompt/输入采样/generation不改；对照只计相对原回答的改变/无correct或quality label。

runner及单300秒控制监督模式已实现，本地/Linux35同范围检查通过；24真实CPU输入（8视频x3条件/每条件首道原题）通过，matched sampled tensor与旧run一致、blank全零、cyclic无固定点且tensor改变，CUDA未初始化/未load/未126答案。下一Git同步/hash部署/Linux最终CPU/fresh锁预算GPU准入唯一controls-r1；不改旧结果/调提示/自动扩额，不人评/训练/付费。重复稳定或内容响应即使通过也不证明物理正确性；原模型proxy没有质量—时间正结果，暂不加W2/生成。

证据：[控制准备卡](../research/29_W1_VQA_INPUT_CONTROLS_PREPARATION.md)、[35项Linux检查](../reports/w1_vqa_controls_linux_cpu_20261001.json)、[24真实输入](../reports/w1_vqa_controls_input_cpu_20261001.json)、[原VQA结果](../research/28_W1_DEVELOPMENT_VQA_RESULTS.md)。旧实机source1f326b5身份不变，当前控制尚未部署/提交。

## 以下为历史快照

## 最新终态 — 2026-10-01 02:56:53 北京时间：开发VQA原8/81答案完整，6平1降，下一judge输入敏感性诊断

w1-vqa-r1/source1f326b5已exit0/无stop reason，监督60.966001秒；supervisor2485687/timeout2485695/runner2485697全退出/global锁释放/GPU1 24MiB/noapps，12monitor点无观察到foreign compute，peak4972MiB。模型离线BF16/SDPA load成功/无missing或mismatch，eval/inference_mode，42参考+39候选原单题完整，81raw token CPU重新decode一致/全部strict有效。原8分母/7可比/robot VIDEO_REJECTED保留，拒绝3题不插补；全部15视频/模型10文件/原题/运行时与源码hash重新通过。

开发judge场景差：6平/1降misc，scene等权mean delta -0.031746031746031744（-3.174603pp）；misc6/9到4/9，只有Q1空间关系与Q9时序两答案YES→NO/原标签YES，其他37可比题同答。参考26/42、接受场景参考23/39/候选21/39仅开发分数；原标签32YES/10NO，常YES32/42只是偏置诊断，不能当视频真值或否定judge。小2B/10帧未有有效性金标准，因此分类DEVELOPMENT_VQA_NO_GAIN_IN_PROXY，不作物理变差/非劣/最终方法否定或235B标准Joint。

GPU实际累计3.629295697609584/4h、余0.370704302390416h（1334.535秒），无在途。结合MUSIQ3升4降/robot拒绝，当前不扩大scalar/W2/生成批次，继续补评价可信度。官方固定数据revision根目录只有condition_image/vqa/metadata，未提供本次8场景对应gold视频；不冒充生成WC视频是gold。下一准备同judge原8/42题的matched repeat/black video/cyclic mismatch三种输入对照，最多300秒从原余额扣除，不改原prompt/模型或原方法结果、不要求人评/付费/训练/扩额。诊断只判断输入敏感性/重复稳定，不是物理正确性金标准；控制分数尚未生成。

证据：[VQA结果](../research/28_W1_DEVELOPMENT_VQA_RESULTS.md)、[raw runner](../reports/w1_vqa_r1_runner.json)、[原题重算汇总](../reports/w1_vqa_r1_summary.json)、[终态审计](../reports/w1_vqa_r1_audit.json)。旧source1f326b5不因新文档HEAD而变化；下一控制GPU尚未提交，需实现/CPU/source同步/fresh锁与预算/准入。

## 以下为历史快照

## 最新资源验收 — 2026-10-01 02:46:45 北京时间：CPU r4终态，官方10文件完整hash通过，待有界VQA部署

r4/source39993d1 exit0/633.154270秒，supervisor2484509/timeout2484510/downloader2484511全退出、CPU锁释放/source一致/GPU账本不变。固定revision的全部10文件逐文件官方Git blob/SHA256通过，包括4255140312字节model.safetensors，权重LFS SHA256 7de1838c87a5349b016c26a1c3f7d2bc400a3d485f95ef39a7059ffd734977a0，无partial；资源下载完整/hash验收成立。未load模型/forward/评分，不能据此称质量或GPU运行通过。

VQA runner/900秒模式/原raw完整汇总代码及本地/Linux25CPU、全部15真实输入/42原题检查已通过。下一同步本次资源回执、hash部署源码并最终LinuxCPU；核验剩余预算/global锁/GPU UUID/VRAM/apps，只提交唯一outputs/w1-vqa-r1，原8/42参考39候选/robot3题拒绝保留。同10帧固定输入/逐题原提示/strict invalid bounds/一次离线BF16 SDPA加载/每题partial回执；任何技术错保留失败，不能择优重问或静默补题。

GPU累计3.612360697322422/4h、余0.387639302677578h，无GPU在途；单900秒包括hash/load/失败/评分/flush，从原余额扣除，未实测完整成本，不扩额。scalar仅机制/MUSIQ3升4降与拒绝保持，尚无整体/物理质量或clean速度收益，暂不加W2；小2B不是235B标准Joint/独立确认。不人评/训练/付费。

证据：[官方10文件完整性](../reports/w1_judge_assets_r4_integrity.json)、[r4终态审计](../reports/w1_judge_assets_r4_audit.json)、[runner准备卡](../research/27_W1_VQA_RUNNER_PREPARATION.md)。CPU旧source39993d1保持，后续文档HEAD不冒充未来实机VQA source。

## 以下为历史快照

## 最新运行核验 — 2026-10-01 02:38:45 北京时间：CPU r4/source39993d1续传live，VQA runner CPU通过

r3终态/旧3PIDs退出/CPU锁释放后，新唯一outputs/w1-judge-assets-r4已启动。CPU部署source39993d1/hash一致，Linux4 acquisition检查通过；supervisor2484509/timeout2484510/downloader2484511本次proc核实live，CUDA为空/无代理/CPU锁持有。相同匿名镜像/revision/官方hash/cache/cap3600CPU-only，partial3030384640增至3439329280字节（3280MiB），未完整/hash验收/load/VLM forward。不是重复r3、不改旧失败或在跑源。

VQA GPU runner/900秒监督/原raw终态汇总已实现，本地25与Linux25 CPU、15真实视频输入/42原题hash/count通过；实际runner拒绝部分权重，未forward。部署/准入助手只已准备，尚未调用，不改正在跑CPU文件。继续同r4 handles至终态，完整10文件官方digest/模型源锁核验后，才部署并fresh预算/锁/GPU准入单个w1-vqa-r1。终态前不重复提交/变更源；观察失败不作任务终态。

GPU累计3.612360697322422/4h、余0.387639302677578h、无GPU在途，账本与启动前相同。scalar CAL8仅机制、固定重放7接受1robot拒绝、MUSIQ3升4降保持，尚无整体/物理质量或clean速度收益，暂不加W2；小2B开发judge不等于标准235B/Joint/独立确认。不引入非必要人评/训练/付费或自动扩额。

证据：[r4启动](../reports/w1_judge_assets_r4_launch_20261001.json)、[live观察](../reports/w1_judge_assets_r4_live_observation.json)、[runner准备卡](../research/27_W1_VQA_RUNNER_PREPARATION.md)、[r3终态](../reports/w1_judge_assets_r3_audit.json)。后续文档HEAD不改变CPU部署source39993d1身份。

## 以下为历史快照

## 最新接续 — 2026-10-01 02:24:30 北京时间：r3连接中断终态，VQA runner CPU通过，准备r4续传

r3/source202e21d实际exit1/1153.880144秒，IncompleteRead连接中断；supervisor2481616/timeout2481618/downloader2481619全退出/CPU锁释放/source hash一致/GPU账本未变，保留3030384640字节（2890MiB）。不是cap超时/人工取消，旧RUNNING快照已被终态覆盖。下一同匿名镜像/固定revision/官方hash/cache/cap3600秒CPU-only的新唯一r4，复用既有字节，不改r3输出/协议或扩GPU额度。

已实现scripts/run_w1_vqa.py与supervise_f1 --w1-vqa：单900秒/all8/42参考39接受候选题，一次离线BF16/SDPA模型加载，严格逐题原提示/贪心/原始tokens与答案/每题持久化，parse invalid继续，技术异常停止且保留部分覆盖。scripts/summarize_w1_vqa.py重新计算原题/原答案、检查原视频/采样元数据/coverage/rejection/token数，partial不得汇总成完整结果。模型/processor/vision utility的真实CPU安装hash/version已另锁定，不改初始VQA输入manifest。

本地25及Linux隔离staging25 CPU检查通过（不相加计数）；全部15接受视频原文件hash、实际10帧元数据/processor与42题hash/count真实CPU通过，CUDA未初始化；实际runner在部分权重时也已拒绝，未import torch/load/forward。当前只是实现与CPU证据，不是GPU load/评分/质量通过。GPU累计3.612360697322422/4h、余0.387639302677578h、无在途；scalar机制/MUSIQ混合结果保持，暂不加W2，不要求人评/付费/训练/自动扩额。

证据：[r3终态审计](../reports/w1_judge_assets_r3_audit.json)、[runner准备卡](../research/27_W1_VQA_RUNNER_PREPARATION.md)、[Linux25检查](../reports/w1_vqa_runner_linux_cpu_20261001.json)、[全部15输入](../reports/w1_vqa_all_inputs_cpu_20261001.json)。下一完整下载/hash后才可部署并fresh预算/锁/GPU准入。当前r4尚未启动，未来文档HEAD不改变旧CPU source202e21d。

## 以下为历史快照

## 最新恢复核验 — 2026-10-01 02:01:45 北京时间：judge CPU镜像续传r3 live

已fetch GitHub main并核对本地/远端同为202e21d，SSH实测成功，共享FRPC未改/未重复启动；原r1/r2和GPU任务均已退出。新唯一`outputs/w1-judge-assets-r3`部署source202e21d，文件SHA256一致，Linux4项CPU acquisition检查通过。supervisor2481616/timeout2481618/downloader2481619三个PIDs本次真实ps/proc核实存活，CUDA为空、无代理环境，CPU锁由本任务持有。匿名公共镜像/固定revision/同官方hash/cache，cap3600秒；权重partial由786432000增至891289600字节（850MiB），仍未完整/未验收，未加载权重/未VLM forward/未GPU评分。

继续观察同一handles，不改在跑CPU源码/manifest、不重复提交；终态后核验PIDs退出/锁/source、逐文件官方Git/LFS digest，再实现并检查GPU runner。原8/42题/10采样帧输入和parser已CPU准备，完整小模型结果仍仅开发代理，不是235B标准Joint或独立确认。robot拒绝保留，不要求人评/训练/付费或自动扩额。

GPU1本次24MiB/no compute apps，所有GPU阶段终态；账本与启动前相同，累计3.612360697322422/4GPUh、余0.387639302677578h。scalar CAL8仅机制信号，固定重放7接受1拒绝、MUSIQ3升4降，无整体/物理质量或clean speed正结果，暂不加W2。此后文档HEAD不改变实机source202e21d身份。

证据：[唯一启动](../reports/w1_judge_assets_r3_launch_20261001.json)、[live观察](../reports/w1_judge_assets_r3_live_observation.json)、[开发准备卡](../research/26_W1_DEVELOPMENT_VQA_PREPARATION.md)。

## 以下为历史快照

## 最新接续 — 2026-10-01：CPU r1失败/r2超时终态，准备镜像续传；VQA输入CPU通过

r1直连Hub metadata失败exit1/261.483689秒；r2代理下载真实有进度，1190.036513秒后timeout exit124，786432000字节/750MiB保留。原r2 supervisor2478913/timeout2478914/downloader2478915全退出/CPU lock释放、source哈希一致、GPU账本未变；downloader状态文件仍RUNNING是超时后的旧文件，不是live。任务专用SSH代理在终态后停止，不改共享FRPC/系统代理。不是观察超时导致重复提交，也未主动取消r2。

已验证匿名公共镜像同一revision metadata、8MiB HTTP206范围和既有权重prefix一致，测得5.489秒；不是完整权重验收。新r3相同10文件/官方Git-LFS哈希/cache，CPU-only cap3600秒因实测吞吐加余量；原4GPUh不扩，当前r3未启动，需先同步source/LinuxCPU/唯一launch并保留旧失败。完整下载后核验每个文件digest，再offline load/有界评分，不据部分字节冒充资源齐备。

VQA原8/42题输入/提示/严格parser协议已准备，本地7项CPU检查通过，真实Linux仅AutoConfig/Processor/视频输入成功，CUDA未初始化、模型权重未加载/无VLM forward。保持原单题提示，groundtruth/方法标签不入prompt；requested2fps实际10帧0到92/完整source93帧16fps，显式metadata。原32YES/10NO，invalid保留bounds，robot3题拒绝不插补。GPU runner尚未实现；下一拟cap900秒需完整权重/hash/代码/CPU/新预算锁GPU准入后方能提交。小2B只是开发judge，不是235B标准Joint/独立确认。

固定重放8技术轨迹/7接受1robot拒绝、MUSIQ3升4降保持，未有整体/物理质量或clean速度正结果；暂不加W2。累计3.612360697322422/4GPUh、余0.387639302677578h，无GPU在途。不人评/训练/付费/自动扩额；有界工程恢复继续，重大科学或GPU预算决策交用户。

证据：[开发VQA卡](../research/26_W1_DEVELOPMENT_VQA_PREPARATION.md)、[r1审计](../reports/w1_judge_assets_r1_audit.json)、[r2审计](../reports/w1_judge_assets_r2_audit.json)、[输入协议](../manifests/w1_development_vqa_protocol.json)。

## 以下为历史快照

## 最新运行核验 — 2026-10-01 01:16:40 北京时间：开发judge CPU资源下载在跑

已部署CPU source `d0faa4b`，上传文件hash匹配、Linux3项CPU检查通过；唯一`outputs/w1-judge-assets-r1`已启动。supervisor2478298、timeout/PGID2478299、downloader2478300三PIDs本次ps核验live，CUDA为空/gpu_workload_started=false。固定官方Qwen3-VL2B revision/10文件/匿名端点/项目hfhub，cap1200秒；观察时completed为空、未看到incomplete对象，仍RUNNING，不能称模型已下载或可评分。source/launch/budget证据已归档。

下一继续同一handles与日志；观察超时不代表任务退出，不重复提交。终态后查父子退出/CPU lock释放、完整文件SHA256/Git blob与manifest一致，再offline config/processor兼容及有界GPU方案；小judge只开发评价，不是235B标准Joint或独立确认。当前无VQA GPU评分/额外budget/人评/训练/付费。

固定重放8轨迹技术通过/7视频接受1robot拒绝，MUSIQ3升4降/mean delta+0.004254295，整体/物理质量与clean速度未证，暂不加W2。所有GPU任务已释放，累计3.612360697322422/4GPUh、余0.387639302677578h，无GPU在途；CPU下载不作GPU计费或运行结果。下一实际GPU提交仍需fresh预算/锁/GPU准入。

证据：[CPU启动](../reports/w1_judge_assets_r1_launch_20261001.json)、[只读进程快照](../reports/w1_judge_assets_r1_live_observation.json)、[已完成成像结果](../research/25_W1_IMAGING_RESULTS.md)。

## 以下为历史快照

## 最新接续 — 2026-10-01：自动成像评价终态，下一开发VQA资源准备

MUSIQ `w1-imaging-r1` sourcea51e3e4已终态：原8分母/7接受视频对全部93帧评分，robot VIDEO_REJECTED保留；3升4降，按可比场景等权mean delta +0.004254295（MUSIQ原始+0.425429518），industry单项较大，其他混合。没有预设非劣界限或独立确认，不能据小正均值称质量收益。原frame scores/均值/配对差/覆盖已重新计算。标准语义/物理/动作完成/整体质量与clean速度仍未评估，暂不加W2。

supervisor2477084/timeout2477091/runner2477093全退出，exit0/无stop reason；锁可用，GPU1 24MiB/noapps，9监控点无观察到其他compute，peak586MiB；source及15输入视频hash匹配。监督44.552937秒，累计3.612360697322/4GPUh，余0.387639302678h，无在途GPU任务。此评价是单成像维度/固定本地pyiqa，非完整标准benchmark/Joint复现。

下一已具体准备：官方公共Qwen3-VL2B revision89644892e4d85e24eaac8bacfd4f463576704203及10个inference文件/Git-LFS hash冻结，约3.974GiB；CPU下载到项目独立hfhub，cap1200秒，匿名官方端点、不写共享cache。小模型仅开发VQA judge，不能替代235B标准judge或独立确认。原42条VQA题已取回hash绑定。新CPU监督器单identity/flock/timeout/exit receipt/env CUDA为空，3项针对性CPU检查通过；当前下载尚未启动。先commit/push、hash部署CPU文件并Linux检查，唯一outputs/w1-judge-assets-r1；下一查同handles至终态，再完整hash/offline config/processor/load资源检查。尚无新VQA GPU评分。

固定重放结果仍8轨迹技术通过/7接受1robot拒绝/295scalar预测0fallback；CAL8只是机制信号。自动GPU VQA必须完整原8分母/所有原题、同模型/固定视频输入与评分协议、有界预算/fresh准入后才提交，不能用小模型单维度判最终方法成功。不扩预算/训练/付费/人评，重大资源/方向决策再交用户。

证据：[成像结果](../research/25_W1_IMAGING_RESULTS.md)、[重新计算汇总](../reports/w1_imaging_r1_summary.json)、[终态审计](../reports/w1_imaging_r1_audit.json)、[开发judge资源manifest](../manifests/w1_development_judge_assets.json)；后续文档HEAD不等于过去实机source。

## 以下为历史快照

## 最新接续 — 2026-10-01：固定scalar重放终态，自动成像评价准备

source31a797d的`w1-replay-r1`已终态，原supervisor2471255/timeout2471260/runner2471262全部退出、锁可用、GPU1 24MiB/noapps；424监控点无观察到其他compute，所有9接受artifact/source hash核验通过。official14项/scalar OFF-ON18项全真；原8场景72call/frozen schedule/past-anchor技术通过，295scalar预测/0fallback、57自然与冻结判据差异。候选7接受、robot_054 VIDEO_REJECTED（官方WC8接受），拒绝保留原8分母，不能补跑或安全绕过。总结是FROZEN_REPLAY_TECH_PASS_QUALITY_UNASSESSED，非全视频接受/方法质量收益。

7可比视频对都有像素差异、6/7帧间RGB变化较小，两个AV更明显；不能判更稳或动作消失。带hash/首shadow/顺序加载时间不作clean测速。CAL8 scalar机制信号保持，尚无语义/物理、整体质量、干净速度或独立确认结果；暂不加W2。

监督2177.784138秒，累计3.59998488161299/4GPUh，余0.40001511838701h，无在途。下一独立MUSIQ成像维度评价已本地实现，17项CPU检查和Linux四种几何的官方Resize精确预处理对照通过，已有权重离线CPU加载/forward通过；冻结终态reference/candidate/checkpoint/source哈希，原8分母/7接受对、全部93帧，cap600秒从原余额扣除。尚未部署/未GPU评分；下一步源码同步后LinuxCPU与freshGPU/预算/锁准入，仅提交一次`outputs/w1-imaging-r1`。

Qwen3-VL2B/8B只有processor/tokenizer/config无权重，标准大judge/环境不就绪；原42条VQA问题已hash绑定取回，但未评分。MUSIQ只回答成像维度，不能替代语义/物理/Joint或通过整体质量门。不要求人评，不训练/付费/扩额。

证据：[重放结果](../research/24_W1_FIXED_REPLAY_RESULTS.md)、[完整汇总](../reports/w1_replay_r1_summary.json)、[审计](../reports/w1_replay_r1_audit.json)、[成像评价卡](../research/23_W1_IMAGING_EVALUATION.md)；终态后才部署下一source，原运行source31a身份保持。未来预算/质量/clean计时资源不足时形成具体方案再交用户重大决策。

## 以下为历史快照

## 最新接续 — 2026-10-01 00:29:13 北京时间：scalar固定重放实机运行，两门通过

GitHub/source `31a797d363a6ebdcf7d8443f84f7d0a0bb073797` 已部署，archive/source hash匹配，Linux63项CPU检查通过。新任务 `outputs/w1-replay-r1` 已于2026-10-01 00:16启动；supervisor2471255、timeout/PGID2471260、runner2471262均live，GPU1仅观察到此runner。继续同一任务，不部署新代码或重复启动。

首AV official重放对原CAL8 OFF全部14项严格检查全真；scalar OFF/ON全部18项检查全真、8个shadow点，两个候选输出均ACCEPTED。首候选计入原8成员，当前第二个common场景scalar OFF生成，完成1/8；全批和终态审计未完成。首候选完整93帧对WC RGB MSE975.370840、MAE18.228840、PSNR18.239106dB；相邻帧RGB MAE候选2.274710、WC4.391376。像素距离/较小帧间变化不证明正确性、质量或物理改善；带hash/诊断时间也不作干净测速。

启动前结算2.995044843356/4GPUh；观察时另有0.218519319h在途，未计入旧ledger。单batch总cap3000秒不变，所有加载/诊断/失败/flush计费，不能用旧余额准入第二任务。无新增预算、训练、付费评分或人评。原CAL8 scalar MECHANISM_ONLY结论及misc恶化保留。

证据：[部署](../reports/w1_replay_r1_deployment_20261001.json)、[启动](../reports/w1_replay_r1_launch_20261001.json)、[实时快照](../reports/w1_replay_r1_live_observation.json)。下一步只读观察原handles；终态后验证PIDs退出/锁/GPU归属/源码与产物hash，归档原始runner/supervisor/audit并更新实际wall账本；用hash绑定CAL8 reference重新验证summary。失败/拒绝保留，不补样本或自动重跑。完整通过仍只证明固定schedule候选技术可运行，质量/clean计时/独立确认未完成。

## 以下为历史快照

## 最新接续 — 2026-10-01：fixed replay runner本地实现/CPU通过，待部署

原CAL8终态、scalar MECHANISM_ONLY和预算2.995044843/4h保持。已实现scripts/run_w1_replay.py、supervise_f1.py --w1-replay（单batch cap3000秒），以及replay_results/video_difference/summary CLI。19项本地针对性CPU检查通过；[回执](../reports/w1_replay_local_cpu_20261001.json)。与旧CPU模块24项范围有重叠，不叠加计数。原manifest固定参数/样本/trace/reference hash未改；metadata初始NOT_IMPLEMENTED标签是冻结时历史，当前以此快照和后续运行回执为准。

runner先hash绑定完整CAL8/reference screen并重新计算screen、校验setup/input/runtime/scheduler/VAE；首AV official replay严格复现旧OFF，scalar OFF/ON output/cache/decoder/video及额外calibrator结束状态和controller记录一致，ON真值只评分。余7仅scalar OFF；每sample用自身状态，有限模型输出/固定独立blockcounts/实际controller past anchors/peak memory记录，完整93RGB对旧WC距离与temporal variation描述（非质量）。拒绝/异常保留；SIGTERM尽可能写TECH_BLOCKED，所有真实墙钟计费。无新GPU运行。

下一步：commit/hash部署并Linux CPU gates；重新核验旧PIDs/锁/预算、全部reference视频hash、GPU1 UUID/VRAM/apps，只启动新唯一outputs/w1-replay-r1一次。前门失败立即停止，不能据观察超时重复提交或改在跑代码。上限3000从余1.004955157h扣除，无扩额/训练/付费/人评。部署与launch receipt/PIDs/logs、总体docs和预算需同步GitHub。

## 以下为历史快照

## 最新接续 — 2026-09-30：CAL8终态，scalar机制信号，固定重放准备

w1d-cal8-r1（部署源62f1c0d）完整终态：8/8场景、每样本8点/17项OFF-ON检查全真；16接受视频重新hash匹配，原supervisor2461004/timeout2461009/runner2461011均退出，exit0/无stop reason，锁可用、GPU1 24MiB/noapps，699监控点无观察到其他compute。原始runner/supervisor/audit/summary/analysis/figure已归档reports/w1d_cal8_r1_*；旧live与partial文件都是历史，不得重启旧任务。

冻结screen MECHANISM_ONLY_CAL8：scalar7/8联合velocity/postwarp改善，等样本均值比0.759184683/0.893679139，0fallback；misc两指标恶化保留。shrink0/8 velocity改善，均值1.306201721，本CAL8收缩线不送闭环。8样本皆有内部排序反转，共40 dependent point-mode对比；组上scalar均7/8改善，暂不加W2。没有视频质量/干净速度/独立确认正结果。旧AV四工程点负结果保留原范围；CAL是开发数据。详细[结果](21_W1D_CAL8_RESULTS.md)。

本批监督3590.173902秒/0.997270528h，累计2.995044843355815/4h，余1.004955156644185h，无在途成本。下一固定schedule scalar-recent闭环最多3000秒/0.833333h，仍原budget内。CPU模块fixed_replay.py及24项针对性检查通过，协议已冻结完整8原trace/hash/参数；[准备卡](22_W1_REPLAY_PREPARATION.md)、[manifest](../manifests/w1_fixed_replay_protocol.json)、[CPU回执](../reports/w1_fixed_replay_cpu_20260930.json)。runner/监督模式尚未实现、未Linux部署、未CUDA/生成测试，不能称候选已经跑过。

下一步自主实现有监督runner：firstAV新official fixed replay对旧OFF严格复现，再scalar OFF/ON自身parity，通过后原其余7scalar OFF；共10generation，firstcandidateOFF计入8成员。自己当前latent/probe/full anchors，shadow truth只评分，不回放旧latent。不择优/替换misc；拒绝保留，技术异常停止。预算forecast2224.619秒+30%=2892.004秒，cap3000；提交前重新核验旧handles/锁/余额/GPU/source/hash/LinuxCPU。尚无第二任务/额外预算/训练/付费评分/人评。代码与docs推送后的新HEAD不改变旧source62运行身份。

## 以下为历史快照

## 最新接续 — 2026-09-30 23:09：5/8技术通过，分布分析就绪

原w1d-cal8-r1任务持续运行；supervisor2461004/timeout2461009/runner2461011均live，source62f1c0d保持。前5个样本各8诊断点、17项OFF/ON检查全真；第6个physics_045 OFF生成。当前[实时进程/GPU快照](../reports/w1d_cal8_r1_live_observation.json)更新；22:48的runner/partial summary文件仍只归档前2样本，不是最新/终态。启动前结算1.997774315h，23:09在途0.668417069h额外，batch6000秒/原总4h cap不变，无第二任务。

已完成只读分布分析src/wcomr/w1d_analysis.py与CLI scripts/analyze_w1d_cal.py，严格校验每个分区非空/不重叠/完整覆盖、候选坐标匹配、group MSE与reference energy能重建整体值；按样本等权汇总，零官方误差比留空。scripts/plot_w1d_cal.py输出同状态散点/排序反转计数/velocity时间空间通道图，显示dependent/latent坐标范围，不把组当独立样本。11项针对性CPU检查通过，真实部分回执CLI与私有部分图检查通过；[CPU回执](../reports/w1d_analysis_cpu_20260930.json)。仅本地代码，未部署到正在跑的job，无新科学结论或额外GPU成本。

终态归档/审计后执行原screen与新descriptive analysis；plot依赖可用pip install -e '.[analysis]'安装到本地环境。所有partial显式NO_DECISION。接续原PIDs，不重启/改公式/增加样本。没有重要问题时按协议自行收尾和评估下一有界任务。

## 以下为历史快照

## 最新核验 — 2026-09-30 22:48：CAL8 W1-D运行，2/8技术通过

源`62f1c0d03ab7d789a7e5a86235e2d27cf920825c`，部署archive/源码hash一致，Linux44项CPU检查通过。已真实启动`outputs/w1d-cal8-r1`，GPU1 UUID GPU-cebf7119-cf03-23b9-e192-cd196332b704；supervisor2461004、timeout/PGID2461009、runner2461011 live。22:48只读观察：前两个AV/common样本各8点、四pair完整、ACCEPTED、17项OFF/ON检查全真；第三个human_199 OFF在跑。各样本点先按OFF trace冻结，truth只评分，局部decode flags恢复。此为非终态快照，不是全批成功。

本批一次加载8off/on，上限6000秒/1.666667GPUh，所有成本从原4h cap扣除。启动前已结算1.9977743149465987h，观察时在途另计0.32540379007657366h；旧ledger余额未包含在途，不能用来准入新任务。仍只有此昂贵任务；原FRPC/SSH可用，无需重新建隧道或索取凭证。勿修改部署源码、重启或另起作业。

证据：[部署](../reports/w1d_cal8_r1_deployment_20260930.json)、[启动](../reports/w1d_cal8_r1_launch_20260930.json)、[进程/GPU/日志](../reports/w1d_cal8_r1_live_observation.json)、[真实runner部分快照](../reports/w1d_cal8_r1_live_runner_snapshot.json)、[部分汇总](../reports/w1d_cal8_r1_live_partial_summary.json)、[协议/进展](20_CAL_AND_W1D_PREPARATION.md)。部分scalar等样本velocity/postwarp误差比0.666140/0.820278；shrink1.132306/1.057422，无fallback。LIVE_PARTIAL_NO_DECISION：不据前两样本调公式、判全批成败或进入候选闭环，无质量/干净加速/独立确认结论。旧四工程点NO_GAIN_IN_SCOPE仍是旧范围，不向CAL扩张。

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

# Current state — 2026-09-29

Earlier sections below include historical observations; the final reviewed section and current receipts supersede them.

## Scientific status

No GPU-generated sample or measured quality/time result from this project yet. Continue WorldCache F0/F1, conditional on the remaining safety assets and full forward readiness. Core construction and weight loading have passed. OMR resource availability is not established; the project page release section still says Coming soon.

## Implemented and checked

- Pinned official WorldCache commit and cache-module SHA256.
- Pure residual calibrator: only earlier true full-compute anchors; request/model/CFG isolation; finite and shape fallback; bounded scalar coefficient; actual-anchor-gap shrinkage.
- Narrow source hook preserves the official decision/warp path and injects only the approximate residual. CPU toy tests include reset, branch isolation, and all-full behavior.
- Stateless shadow scorer exists. A real-model shadow forward/trace runner is NOT implemented; therefore no fixed-schedule shadow claim.
- 25 CPU tests passed on macOS Python 3.9 / torch 2.8.0. Separately, the complete Linux inference entry point imported successfully with one GPU visible; no model instantiation or video generation yet. See reports/linux_import_gpu*.json.

## Resources / dependencies

- Two-card server: 2 A6000 49140 MiB, driver 570.133.20. Observed VRAM 336/24 MiB and no compute apps. Must recheck immediately before launch.
- Data disk approximately 682 GiB free; root only 13 GiB free. New files and any downloads must use data disk.
- Existing Cosmos checkout has torch 2.7.1+cu128 in its venv and cached Predict2.5-2B post-trained checkpoint, tokenizer, Reason1-7B. Preserve shared checkout, environment and caches.
- Existing checkout is a locally modified research version; it cannot be assumed to be the official baseline.
- Four-card SSH recovered using the historical local authentication path. Fresh BatchMode key-only login had incorrectly excluded that path. Actual hardware is RTX 6000 Ada, not A6000; GPUs 2/3 were idle, 0/1 occupied. Driver 550.67 and glibc 2.31; retain the existing two-card runtime as current F1 candidate. FRP is already running; do not launch a duplicate shared tunnel.
- Pinned WorldCache tree lacks model source directories referenced by its inference configuration. Need a separately pinned, documented source completion shared across both baseline paths. Do not silently substitute the locally modified model.
- Guardrail1 cache snapshot currently contains only README; inspect complete safety dependencies before inference. No safety/access bypass.

## First-batch scope

User explicitly authorized the two/four A6000 resources. Start with F0 and four-scene, one-seed Native/official-WC technical smoke. One expensive job at a time, at most 4 GPU hours including failure/loading. Recheck UUID/VRAM/processes and retain PID, log, outputs and exit status. F2/W1 GPU scope follows measured F1 cost. No training or paid evaluation.

## Linux runtime probe update

Missing model directories were copied into an isolated candidate runtime from pinned NVIDIA revision a2c298b0a3df3778b973fe65e9e58877b292d8a7. No existing WorldCache source file was overwritten. Complete directory/file hashes are in manifests/runtime_completion.json. This source completion is a documented adaptation, not an untouched official checkout.

Initial use of installed cosmos-cuda 1.3.1 failed against source cosmos-oss 1.4.0. Using both workspace source packages at 1.4.0 resolved that mismatch. CPU-only import then failed because Triton requires an active CUDA driver. After fresh admission (GPU 1: 24 MiB, zero compute processes), a bounded GPU-visible import passed with exit 0. Supervisor wall time 44.876 seconds, charged 0.012466 GPU hours conservatively. GPU video jobs remain zero.

Read-only reuse of the existing Python environment remains a compatibility candidate: torch 2.7.1+cu128 differs from upstream's 2.7.0 lock, glibc is 2.31 rather than documented >=2.35. Import success does not prove model-load or numerical/latency equivalence. Full assets and model loading are still gates.

Direct Hugging Face and the old forwarded proxy endpoint both failed a bounded connection test. A task-scoped SSH proxy is being checked for asset acquisition. Missing safety assets are not disabled.

## Historical first acquisition failure (superseded by official access check below)

Auxiliary download reached the mirror but failed with GatedRepoError HTTP 403 for a Cosmos-Guardrail1 blocklist file. Durable receipt: reports/auxiliary_download_20260929.json. No auxiliary snapshot completed; download exited. This establishes failure of the attempted access path, not a universal claim about the user's account permissions. Official authenticated access is not yet verified. No GPU generation is running.

Asked for an already authorized Guardrail1 directory or authorized HF login on the server. Do not remove the guardrails to evade this dependency. Downloader now defaults to anonymous requests and permits explicit authenticated access only to https://huggingface.co. No token should be pasted into chat or Git. Public Qwen/SigLIP acquisition remains pending, as the first required dependency failed.

## Four-card authentication recovery

Historical session evidence identified an automated interactive authentication path. Reusing it established a live SSH session; the user did not need to provide a password. No credentials were printed or stored in Git. A live multiplexed connection is temporary, so a later missing control socket is not evidence that authentication requires new user input. See reports/four_card_recovery_20260929.json. Guardrail1 access remains the only known external asset blocker for the current two-card F1 candidate.

## Autonomous continuation — authenticated access and F1 execution tooling

The previous turn made progress by restoring four-card authentication and obtaining a fresh GPU inventory. This continuation verified the actual existing two-card HF login against the official huggingface.co endpoint; access to the Guardrail1 blocklist file still returns HTTP 403 GatedRepo. This supersedes the earlier uncertainty about a mirror-only failure. No credential was logged or saved locally. Receipt: reports/guardrail_official_auth_20260929.json. Human action is needed to authorize that account/model or provide an authorized asset path.

Independent progress: F1 case-set runner, bounded serial supervisor, matched eager/offload profile, stage timers, independent full/skip counters, output format/hash receipts, and process/budget handling are implemented. 22 CPU tests pass, including real subprocess tests for serial execution/accounting, budget stop and duplicate-lock rejection. Fake GPU executable tests do not constitute GPU supervision validation. On Linux, the actual Cosmos configuration classes accept all four inputs and confirm only output_dir and worldcache_enabled differ between arms. Whole runner/model load/generation remain NOT_RUN.

Public Qwen/SigLIP acquisition is being attempted separately from gated Guardrail1. Inspect the durable public-download launch/child/exit records on the two-card server before retrying or reporting completion. No additional GPU hours consumed.

## Resource acquisition continuation

A separate, project-scoped TCP visitor was established with a different local port, using the existing server authorization and verified host key. Original shared FRP and other visitors were not stopped or changed. Its config is private, mode 0600, outside Git; local metadata is in ignored configs/hosts.local.json. Several live SSH operations now succeed through it. This is observed connectivity recovery, not a long-term stability guarantee.

After confirming the previous public-download launch/child/exit files were all absent, the public-only acquisition was started once. Supervisor PID 2361014 and downloader PID 2361016 were verified live; receipt reports RUNNING on Qwen3Guard. It is bounded to 1200 seconds and uses no GPU. Guardrail1 was excluded only from this acquisition queue because it is separately blocked; it remains required by the inference runner. Inspect current receipts rather than relying on this snapshot.

F1 source snapshot 08560c9 was deployed to the two-card project directory, with matching local/remote archive SHA256. Scripts compile on Linux and the 17 selected calibration/measurement/subprocess tests pass in its torch 2.7.1 environment. They use no GPU; the supervisor tests substitute nvidia-smi and timeout. This is not a real-model run. See reports/f1_deployment_20260929.json.

Load-only progress: core probe r1 terminated with exit 1 after 41.03 process seconds, before any parameter-loading call. It exposed an unrelated 14B training-example checkpoint download during config registration. GPU budget is now 0.023864 hours before r2, still no generated video. A hash-checked registration adapter was tested and deployed identically for both F1 arms; load-only r2 supervisor 2362849 is now running. It has a 420-second upper bound and never generates. Inspect its actual terminal receipt before another probe.

## Reviewed core-model loading and public assets

R2 exited 0 after 113.16 supervised process seconds. The tokenizer (194 keys), Reason1 encoder (729 keys) and MinimalV1LVGDiT (689 keys) state loads all returned zero missing and unexpected keys. The 2,059,174,912-parameter, 28-block network resides in bfloat16 on the admitted GPU. Torch peak allocated memory was 23.423 GiB. This validates construction/weight compatibility, not forward kernels, complete safety pipeline, video generation or a scientific quality-time result. Core probe processes have exited and the GPU was released. Total charged GPU time is 0.055297 hours.

Qwen3Guard public files (7 files) match SHA256/Git-blob hashes obtained from the official pinned HF tree. Its offline config/tokenizer are accepted by transformers 4.57.1 and resolve Qwen3ForCausalLM. It has not yet been model-load/inference tested. Two new hash-integrity tests passed in addition to the existing 25-test run.

Public acquisition r1 hit its independent 1200-second deadline (exit 124) while SigLIP was incomplete. Both old processes were confirmed absent. Only SigLIP was resumed with the same cache and a 3600-second bound; supervisor PID 2364279. No repeated download of the verified Qwen snapshot. Guardrail1 remains required and blocked by official authenticated HTTP 403.

The project HF cache now links the existing immutable core model directories; same-directory identity was checked. Shared cache contents and credentials were not modified. Set HF_HUB_CACHE to the project hfhub for full F1 so newly acquired safety assets and existing core checkpoints resolve together.

## Public Qwen component forward check

The pinned Qwen3Guard component completed offline CPU loading and deterministic generation in 12.03s on the existing Linux environment. A benign red-ball prompt produced `Safety: Safe / Categories: None`. No GPU was visible or used. Receipt: reports/qwen_forward_20260929.json. This establishes component load/forward compatibility only; Guardrail1 access still blocks full safety-pipeline validation and F1 generation. SigLIP supervisor 2364279 was verified live, with 2,527,068,160 bytes downloaded at the latest observation.

## Public dependencies ready; external access blocks F1

SigLIP resume ended with exit 0 after 1451.57s. All 7 files match the official pinned metadata. CPU loading and image encoding passed in 8.60s with finite nonzero features [1,1152]. Both public safety components are now locally usable, but this does not validate the complete safety pipeline. The final official authenticated Guardrail1 check at 09:47:50 UTC still returned 403 GatedRepo. This same blocker has persisted for more than three goal turns; with independent asset work complete, the goal is blocked pending authorized weights/access. No video has been generated, no scientific claim is established, and GPU cost remains 0.055297 h.

## Guardrail access restored and F1 launched

User granted model access. Server-token official HEAD returned HTTP 200. All 81 Guardrail files passed official pinned hashes. Full text/video/face safety compatibility probe exited 0 in 43.84 supervised seconds. F1 smoke r1 launched on admitted GPU1: supervisor 2370231, Native child 2370237. Four scenes per arm, Native then official WC, offline project cache, remaining shared 4h budget. Results and actual videos are pending; the earlier external blocker is resolved.

## F1 scheduler discrepancy (latest)

First Native video passed safety and format validation, but the job failed the CFG-count assertion. Exact hook counts were not saved; native progress log shows36 iterations and CPU schedule probe independently confirms35 requested ->36 actual UniPC/Karras steps. This differs from paper35Euler and WC counter horizon70. GPU is released; cumulative cost0.183703h. One Native-only video, no WC result or quality claim. User protocol decision pending; see research/10_SAMPLER_PROTOCOL_DECISION.md.

## Current-code protocol approved; F1 r2 live —2026-09-30

User selected current-code comparison. Frozen runtime protocol records exact36-point UniPC/Karras time grid,72CFGcalls and unchangedWC70-call horizon. Local29tests/Linux8relevant CPU tests pass; source4814657 deployment hashes match. F1r2 supervisor2427723, initialNative child2427728, admitted GPU1. FourNative thenfourWC, fresh paired outputs; results pending.

## F1 r2 terminal; latest plan v1.1 — 2026-09-30

This supersedes the live snapshot above. Remote supervisor2427723 exited FAILED; Native timeout child2427728 exited1 after1042.542395s. Two Native sample receipts exist; physics_001 was blocked by output video safety. WC did not start. Local copies: reports/f1_smoke_r2_supervisor.json and reports/f1_smoke_r2_native.json. Charged total0.4732977178361681/4GPUh. No complete paired result or visual-quality claim.

The latest discussion and QuantWM attachment are integrated into both maintained plans: W1-D downstream diagnostics, bounded L0/L1 Wan5B baseline, conditional J6/X3/J5-P. Source manifest records paper/README checks, attachment hash and pending adapter validation. Current F1 protocol is unchanged. The plan edit launches no GPU job. Next actions prioritize failure review and completion of the existing comparison before new experiments.

## F1 r3 launched after outcome recording fix — 2026-09-30

R2 PIDs verified absent. Official keep_going=True permits rejection recording without saving rejected outputs; new observation wrapper preserves filter return values and rejects unexplained missing outputs. 32 local tests and11 Linux CPU/fake-GPU tests passed. Source57c8660 archive matched. Supervisor2431971/Native child2431976 verified live on freshly admitted GPU1. outputs/f1-smoke-r3; before-run budget0.4732977178361681/4GPUh. No paired result yet. Do not change running code or restart from stale status.

## R3 first Native artifact integrity verified

AV completed and common started. Local copy matches receipt hash; full93-frame decoding passes,768x432,monotonic0–5.75s timestamps. E2E314.462688s, denoising256.631392s,72full/0skip. See reports/f1_smoke_r3_first_native_decode.json. No paired result or visual-quality conclusion; no source change on the live server.

## R3 rejection continuation verified on real generation

Physics output was rejected with72full/0skip, no rejected mp4 exists, original robot scene started with supervisor/child live. See reports/f1_smoke_r3_rejection_continuation.json. This validates the outcome-continuation implementation, not quality or paired acceleration.

## R3 Native complete; WorldCache live

Native all4attempted,3accepted/1video-rejected; exit0 after1322.461758 supervised seconds. reports/f1_smoke_r3_native.json is terminal. Settled budget0.8406482060750325/4GPUh. Supervisor2431971 now runs verified-live WC child2435496; start snapshot is reports/f1_smoke_r3_worldcache_start.json. No paired result; no changes to running source.

## First real WC output and Native artifact checks

WC firstAV accepted with72calls/38full/34skip; call71counter reset observed. Input, runtime setup and protocol provenance match Native. WC common scene now generating. First-sample raw E2E213.118537s/denoise152.435226s; no complete-batch or quality conclusion. Three accepted Native videos hash-match and fully decode locally.

## R3 terminal closeout

Both arms exited0, supervisor/children absent, GPU released. Native3accepted/1rejected; WC4accepted. Three accepted-pair E2E ratios1.476–1.602 with matched setup;7artifacts hash/full-decode pass, quality review pending. Budget1.09256762723128/4GPUh settled. See research/11_F1_R3_TECHNICAL_RESULTS.md and execution audit. Continue baseline review and bounded W1 parity gate, not another F1 launch.

## W1-P0 parity gate live

Source d98f447 deployed with matching archive.49local/13LinuxCPUtests pass. Supervisor2439296/child2439301 verified live after24MiB/no-app GPU admission; outputs/w1-p0-r1,900s maximum. Settled cost before gate1.09256762723128/4GPUh. No real parity result yet and F1qualityreview remains pending.

## User scope correction

Manual semantic review was prematurely emphasized; it is not required by original F1 smoke scope and must not block W1. Continue parity and numerical diagnostics. Optional review UI is not a prerequisite; quality-equivalence still requires appropriate later evidence.

## W1-P0 terminal recovered; next candidate diagnostic prepared — 2026-09-30

Live FRPC/SSH connection succeeded. W1-P0 r1 exited0; all7parity checks pass on officialWC AV/seed0.72forward hashes,38full/34skip counts/trace,finalcache andvideo hashes match off/on; calls15/16/37/38 finite. Both artifacts independently rehashed remotely. Old PIDs absent, no project generation processes, supervisor lock available; GPU1 24MiB/no compute apps at18:52Beijing. Source files/protocol hashes match local. No new GPU job.

Budget settled1.2451972062057919/4GPUh,remaining2.754802793794208h. reports/w1_p0_r1{,_supervisor,_summary,_recovery_audit}.json archive evidence; research/12_W1_P0_TERMINAL_RESULTS.md separates implementation acceptance from candidate efficacy. Next research/13_W1_S1_PREPARATION.md is PREPARED_NOT_IMPLEMENTED_NOT_RUN: isolated three approximators on the same official state, <=900s proposed from remainingbudget only after implementation/invariance gates. Current scalar/shrink deployment hooks are not a same-state three-arm diagnostic. Manualsemanticreview remains optional, not a W1gate.

## W1-S1 implemented and CPU checked

SameStateProbe retains official deployed output, scores3approximators at fixedcalls, preserves pinnedcandidate-specificwarp and pre/postwarp distinction, resets realfullanchor trackers on request/cycle/model/expert.58localtests pass, including random state preservation, spatialflow matching to actualcandidatefirstskip, expertfallback and boundedserialsupervision. New --w1-same-state mode caps one off/on job900s under remainingbudget. Not yet LinuxCPUchecked/deployed/GPUrun.

W1-S1 r1初始化失败，未生成：启动环境缺少HF_HUB_CACHE，默认offline缓存无Guardrail1 blocklist目录。监督耗时75.011195s/0.020836443GPUh已结算；当前累计1.266033649/4GPUh。已把项目hfhub路径固定到监督器，6项本地真实子进程测试确认缓存环境，准备核验旧进程/锁后运行不同身份r2。保留[失败回执](../reports/w1_s1_r1_failure_summary.json)。

## W1-S1 r2 live after explicit cache fix

Source7e5bc10 archive matched,6LinuxsupervisorCPUchecks passed afterprior19same-statechecks. Previousr1 PIDs absent,lockavailable;GPU1admitted24MiB/noapps. supervisor2444752/child2444757/runner2444759live,actualprojectHF_HUB_CACHEverified,offgenerating. Settled1.266033649h BEFOREr2;inflightadditional. Do notmodifydeployedsource orsubmitsecondjob. Localreceipt-only summarytool preparedwith7tests,notdeployed. Resultsremainpending.

## W1-S1 r2 terminal and initial mechanism decision

Bothmodes exit0,8paritychecks pass; originalPIDsabsent/lockavailable/GPUreleased,artifactsrehashmatch. Fourpoints scalarvelocitysum-MSEratio2.531189803,shrink5.394980328,both2/4improve,nofallback;defaultNO_GAIN_IN_SCOPE. Earlier15/16improve,midtrajectory37/38worsen. See research/14_W1_S1_INITIAL_RESULTS.md. Cost1.4127196775542366/4h settled. Onefixedrevisiondecay0recentfullpairplanned <=900s;notyetlaunched. Noquality/closed-loopgain.

## Recent-full-pair revision live

Source99f554f archivehashmatches,16local/16Linuxchecks pass. FreshGPU1 24MiB/noapps,oldPIDsabsent/lockavailable; supervisor2447006/timeout2447012/runner2447014live,outputs/w1-s1-recent-r1<=900s. Decay0only,shrinkcontrol/sampling/4callsunchanged. Budget1.412719677hBEFORErevision;additionalinflight. Collectcurrentidentity,notstaler2status;nohumanannotationgate.

## Recent-pair terminal; post-model artifact mismatch found

Source99f554f revisionexit0,8checks pass; oldPIDsabsent/lockfree/GPU1released24MiB/noapps,artifactsrehashmatch. Recentvelocitysum-MSEratio2.354245909,shrink5.394980328,both2/4improve: NO_GAIN_IN_SCOPE. Exact72officialoutputs/cache/trace/samplingandall4official+shrinkscoresequalacrossruns;recentvsdefaultscalarvelocityMSEratio0.930094577stillnoadmissionsignal. CrossprocessMP4hashANDall93decodedRGBframesdiffer(MSE31.026577,MAE3.604356); notmetadataonly, firstdifferencesamplingfinal/VAE/guardrail/save/codecstageUNKNOWN. NumericalcontrastscopedMATCHED_DENOISER_ONLY,notvideo/qualityreproduction. Budget1.560151151220004/4hsettled,remaining2.439848848779996. Nextresearch/16_POST_MODEL_REPRODUCTION_GATE.md: readonlystagehashobservationsintwonewprocesses,<=900sproposed,noGPUstartyet. Noadditionalscalarrevisionorhumanannotation.

## 最新终态 — 2026-10-01：输入控制原8/126完整审计，关键下一窗口待决定

w1-vqa-controls-r1/source72c9e24 exit0，supervisor2488580/timeout2488585/runner2488587全部退出，global锁释放/GPU1 24MiB/noapps。126raw/token一致、24输入重算、8视频/模型10文件/源码安装锁通过，本地原题再次重算一致。matched42/42原答案一致；blank和cyclic各14/42改变、三条件都0invalid。判定REPEAT_STABLE_AND_RESPONDS_TO_CONTENT_NOT_PHYSICAL_VALIDITY，不是物理准确/标准Joint/方法通过；部分场景不变应保留。

本轮计费79.02369451522827秒；累计3.6512467238638138/4GPUh，余0.3487532761361862h/1255.511794秒，无在途。原VQA6平1misc降、MUSIQ3升4降、robot拒绝/CAL8仅机制均保持，当前无质量—时间收益。不再重复输入控制/调prompt，不自动加W2/OMR或训练/人评/付费。

[结果](../research/30_W1_VQA_INPUT_CONTROLS_RESULTS.md)/[完整审计](../reports/w1_vqa_controls_r1_audit.json)/[本地重算](../reports/w1_vqa_controls_r1_local_recompute.json)。[下一窗口成本方案](../research/31_W1_NEXT_WINDOW_COST_AND_DECISION.md)：原8×两臂旧诊断约3141.247秒，非clean下界；当前余额不足以稳妥提交完整批次。新4GPUh提议用于原8×两臂×3重复clean成本门（非独立质量确认），或先CPU核对替代资源；预算/方向待用户决定，尚未实现或新GPU提交。不以挑好子集替代原8。旧实机source72c9e24保持，后续文档HEAD不是新的实机运行。

## 以下为历史快照

## 最新准备 — 2026-10-01：完整配对计时runner实现/CPU48通过，未GPU

原8×两臂×3次重复的50尝试计划（48计时+2预热）已冻结/实现，禁用计时内逐call/pipeline tensor hash/shadow/dump，保留算法与安全管线开销，artifact检查/持久化在计时外且总wall仍计账。两次预热必须post-timer逐93帧RGB核对旧各臂首场景，真实门未执行。partial/拒绝/暖场不变性/预算处理有完整CPU覆盖；本地及Linux48同范围通过，CUDA未初始化。

实际Linux新runner validate-only与固定runtime/source/原输入/raw通过；真实未批准4h账本被拒绝且未模型import/生成。新代码只在独立CPUstaging，旧runtime source72c9e24/PIDs全退出/锁GPU释放，主ledger未变3.6512467238638138/4h。下一新增4GPUh窗口仍待用户决定；不部署/提交GPU或以CPU称clean实机/质量通过，不要求人评。

[准备卡](../research/32_W1_CLEAN_TIMING_CPU_PREPARATION.md)/[冻结协议](../manifests/w1_clean_timing_protocol.json)/[Linux检查](../reports/w1_clean_timing_linux_cpu_20261001.json)。预算决定后才更新授权/ledger、sync/hash部署/fresh准入唯一clean-timing-r1；不要重跑旧controls。

## 以下为历史快照

## 最新资源进展 — 2026-10-01：L0部分核验完成，CPU真实资产/结构证据

历史Wan5B11文件/34201521169字节按新锁定官方revision全hash通过，CPU207.093538秒/原PIDs退出/无GPU成本；现有独立Wan入口3文件与官方42bf4cf逐hash相同，不继承历史PhysCache结果。LongLive代码fb16a879与Wan5B CFG/few-step两release已锁；两600tensor headers各300 A-B目标在实际base825tensor上全部key/shape/rank/alpha-r/index结构匹配。本地/Linux16CPU与tiny官方merge算术通过，尚未有完整adapter payload/真实5B融合/前向/GPU就绪。

[资源审计](../research/33_L0_WAN_LONGLIVE_OMR_RESOURCE_AUDIT.md)/[base完整hash](../reports/l0_wan5b_asset_integrity_20261001.json)/[结构重放](../reports/l0_lora_header_structural_audit_20261001.json)。OMR官方release实查仍Coming soon，公开资源BLOCKED，不自动切主线。环境版本不同，后续隔离准备；下一CPU锁定两适配器共1.802GiB下载/全SHA、真实融合/任务接口验收可独立推进。GPU账本不变3.6512467238638138/4h；原8/50计时CPU准备已齐，新4GPUh仍待用户决定。

## 以下为历史快照

## 最新CPU资源获取 — 2026-10-01：L0两适配器r1实际live，非GPU

资源核验/协议/source68afc3e同步后，唯一outputs/l0-adapter-assets-r1已启动。匿名官方HF、固定两release、独立project cache、cap3600 CPU-only；supervisor2493078/timeout2493079/downloader2493080本次proc核实live、CPU获取锁持有、CUDA空/source与协议hash一致。CFG partial73400320字节（70MiB），3小JSON已到位；few-step尚未开始，未完整payload/SHA/真实5B融合或前向。

接续[launch](../reports/l0_adapter_assets_r1_launch_20261001.json)/[live观察](../reports/l0_adapter_assets_r1_live_observation.json)，使用同3 handles至终态，不因观察超时重启，不改在跑3份CPU获取/验证source或manifest。当前专用临时loopback转发是本任务拥有的SSH进程，本机身份记录在ignored .sync/l0-owned-forward.json，直到CPU终态保持；共享FRPC/代理未改。终态先完整模型release/逐文件SHA、PID/锁/source/GPU账本核验，再只关闭该owned forward，不停止共享路线。

GPU账本严格未变3.6512467238638138/4h，无新GPU工作。已确认Wan5B base11官方hash与header结构/16CPU，不叫L0完整READY；OMR公开release仍Coming soon，新4GPUh计时决定仍待用户。后续完整LoRA/真实CPU融合/隔离环境/任务接口检查独立推进，不自动跑L1或训练/付费/人评。

## 以下为历史快照

## 2026-10-01：L0 r1终态与真实CFG资源/完整融合CPU准备

L0 CPU获取r1因连接中断exit1/1218.181533秒终态，原3PIDs退出/CPU锁释放/账本不变；仅关闭本任务owned临时转发。CFG4文件完整官方hash、真实600tensor finite/300pair alpha-r通过，独立核验PIDs2495417/2495418退出；few-step保留167772160字节（160MiB），非完整payload。两配方分片CPU融合程序已实现，本地/Linux22同范围检查通过，尚未真实Wan5B融合/模型任务load/GPU。下一同固定release/cache/3600秒的新r2续传，不重启旧identity或改共享路线。

[准备与验收](34_L0_CPU_FUSION_PREPARATION_AND_CFG_PAYLOAD.md)，主线预算/质量边界保持。

## 后续同日r2实际续传

L0 CPU r2/source965a502已实际启动且3PIDs2496080/2496081/2496082均/proc核实live，独立CPU锁持有、3600秒上限、source/协议hash一致、CUDA空/账本不变。复用CFG全部已验收4文件，few-step由160MiB续到188743680字节（180MiB），仍非完整/hash验收/融合。r1原连接失败及160MiB保留不改。

接续同一组新r2 handles，不重复提交；[launch](../reports/l0_adapter_assets_r2_launch_20261001.json)/[live](../reports/l0_adapter_assets_r2_live_observation.json)。

## 2026-10-01：L0 r2终态与range39/真实CPU scheduler接口门

L0 r2因第二次HTTP流中断exit1/583.253381秒终态；3PIDs2496080/2496081/2496082已退出/CPU锁释放、原source/协议核验和GPU账本不变，owned r2转发在完整审计后关闭。few-step保留555745280字节（530MiB），CFG4文件继续官方hash PASS。新16MiB range/retry/rollback/fullSHA获取程序和完整融合监督已实现，本地/Linux39同范围CPU通过；还未r3提交/完整5B融合。

见[恢复与接口](35_L0_RANGE_RECOVERY_AND_INTERFACE_GATE.md)，GUIDE1不能靠参数推断单条件前向；无GPU新结果。

## 后续同日range-r3实际启动

L0 CPU range-r3/sourcebd8253d已唯一实际启动，3PIDs2498231/2498232/2498233都/proc verified live，CPU获取锁持有、CUDA空/source协议hash一致/账本未变。官方精确206/64KiB旧prefix边界preflight通过；已完成2个16MiB chunk、重试0次，已fsync字节589299712（562MiB），另有在途文件长度602931200（575MiB）。未完整1289824400/整SHA验收或两模型融合。复用原530MiB，不改r2失败或扩大GPU预算。

[r3 launch](../reports/l0_adapter_assets_r3_launch_20261001.json)/[live](../reports/l0_adapter_assets_r3_live_observation.json)。继续同handles/owned转发至终态，不重复提交，CPU partial不是L0完整READY。

## 2026-10-01：native条件分支公共管线CPU准备

已实现仅T2V的scope adaptation，guide1直接conditional、guide!=1保留原CFG运算，finally恢复，不改源文件/i2v。Local/Linux7检查通过；完整native T2V body+真实UniPC/CPU替身在4/50步guide5输入/timestep/输出bit equal，guide1分别4/50cond/0negative。不是实际模型/GPU parity；保留BF16guide1的stock抵消差异，不称guide1 OFF/ON bit invariant。

[准备与边界](36_L0_NATIVE_CONDITIONAL_CPU_PREPARATION.md)，不改在跑range-r3 source或部署GPU。

## 最新r3终态

L0 range-r3/sourcebd8253d已exit1/1216.976277秒终态；最后range三次URLError，已提交43个16MiB chunk，保留1277165568字节（1218MiB），仍缺12658832字节。CFG4文件/两few-step JSON官方digest PASS，few-step模型MISSING；原3PIDs退出/CPU锁释放/source与协议一致/账本不变，完整审计后仅关闭本任务owned r3转发。下一新唯一r4从保留prefix续传，同官方revision/16MiB/3600秒上限；未新GPU、未完整few-step hash/真实融合。

## 最新全部adapter CPU验收

L0 range-r4/source7c0f2ec唯一实际续传成功，exit0/31.271029秒，最后12658832字节一次range完成/0retry。全部7文件官方digest与实际1200张量CPU有限性、300×2目标/rank/alpha及825基座header匹配通过；原3PIDs2502124/2502125/2502126退出/CPU锁释放/source与协议一致/账本不变，审计后仅owned临时转发关闭。真实融合尚未提交，实际模型/GPU parity仍未通过；新4GPUh仍待用户重要预算决定。

最新真实CPU融合：真实Wan5B两臂CPU fusion-r1/sourcec69e492已唯一启动。supervisor2502473/timeout2502474/runner2502475实际/proc live，独立fusion锁持有、CUDA空/source固定与账本未变。准入时MemAvailable59360669696字节（55.3GiB）、磁盘720206147584字节（670.7GiB）；3600秒CPU cap，当前完整输入hash阶段/未创建模型目录，尚未完成merge或产物验收。 [运行卡](38_L0_FULL_ADAPTER_PAYLOAD_AND_REAL_CPU_FUSION.md)。

最新完整原生源码/环境准备：官方固定Wan运行源码60文件已独立部署/全Gitblob与SHA匹配；旧参考import观察超时、PID后续消失，结果UNKNOWN。参考环境满足官方requirements版本元数据；新隔离env/full native import尚未通过。带PID/阶段持久回执的CPU runtime probe已准备/仅语法检查，未执行。fusion-r1仍同handles/3600秒CPU cap，CFG-only已有413tensor/首shard验收，尚未全两臂验收。 [准备与边界](39_L0_NATIVE_SOURCE_AND_ENVIRONMENT_PREPARATION.md)。

最新CPU融合进度：fusion-r1/sourcec69e492同3PIDs实际live，CFG-only一臂已全部825张量/3分片完成融合、独立公式、有限性、未目标字节不变与序列化重读验收；完整两臂及末尾原输入hash尚未完成。CPU锁持有/source一致/账本未变，维持3600秒cap，不重复启动。

最新两臂/环境门：真实CPU两臂均已825/3分片内部验收；完整posthash/终态与独立fresh artifact审计仍待。新独立env已创建，实际offline缓存解析缺Torch2.4.1+cu121，未装包。独立CPU终态审计程序已准备/语法检查，待原3PIDs退出/锁释放后唯一timeout900秒执行，不重跑融合/改stage/新GPU。 [准备](40_L0_CPU_FUSION_AUDIT_AND_ENV_CACHE.md)。

最新CPU融合终态：CPU fusion-r1/sourcec69e492已exit0/1960.417015秒终态，peak RSS30.8287GiB；两臂各825tensor/3分片/300目标/525未目标完整，18原输入融合前后官方digest一致，3PIDs退出/CPU锁释放/source与GPU账本不变。完整独立fresh产物审计尚未执行，不能称模型/任务/GPU就绪。

最新独立审计/二进制资源：CPU audit-r1/sourcedbe863c已唯一实际启动，3PIDs2505483/2505484/2505485 live、900秒cap/锁持有/source与GPU账本不变。fresh18输入/CFG-only825tensor与3shard/525untargeted通过，few-step+CFG尚待。官方Torch三wheel SHA与Flash官方asset ID/size已锁，Flash官方digest UNKNOWN；均未下载/安装，实际ABI/fullruntime未通过。 [运行卡](41_L0_FRESH_AUDIT_AND_BINARY_SOURCE_LOCK.md)。

最新CPU完整验收：真实两臂CPU融合与独立fresh audit均终态通过：fusion1960.417015秒/peakRSS30.8287GiB，audit663.896945秒；18原输入融合前后及fresh官方digest一致，6输出shard/1650实际tensor全finite与dtype/shape/字节digest通过，1050未目标weight原字节不变，两臂各300目标实际bytes_changed。所有原fusion/审计6PIDs退出/CPU锁释放/source与GPU账本不变。仍未实际模型/T5/VAE加载或任务/GPU就绪。 [完整卡](42_L0_FULL_CPU_FUSION_ARTIFACT_ACCEPTANCE.md)。
