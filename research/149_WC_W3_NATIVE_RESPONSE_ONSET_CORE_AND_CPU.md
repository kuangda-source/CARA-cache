# W3原生响应起点：完整结果、成本与下一步

## 2026-10-08 完整终点结果：响应时机有条件价值，净收益仍待复验

**继续WorldCache/W3。本轮发现：在同一61/63退化交换后，提前恢复原生自身状态响应能明显修复终点失真；其中67与69起点的实际完整调用数相同，保真差异仍然存在。** 本轮定位已完成，下一步回到原始WC上已有净正收益动作的复验，不继续无限修补该坏配置。

| 分支 | Native相对全93帧LPIPS↓ | 相对LATE69改善 | 全程完整调用CFG0/1 | 两重复平均诊断后缀wall |
|---|---:|---:|---:|---:|
| 原始WorldCache | 0.424745424 | — | 20/18 | 本表不跨协议比较 |
| FIXED61共同交换 | 0.668307815 | — | 20/18 | 保留原回执 |
| LATE69（69–70响应） | 0.610756127 | 参考 | 21/19 | 363.557616秒 |
| RESP67（67–70响应） | 0.531047669 | 13.0508% | 21/19 | 363.568715秒 |
| RESP65（65–70响应） | 0.447063151 | 26.8017% | 22/20 | 369.263159秒 |

RESP67相对LATE69只改变67/68两个实际动作，平均wall多0.011099秒（0.00305%）；RESP65改变65/66/69/70，增加两次完整调用，平均多5.705543秒（1.56936%）。响应次数本是政策结果；67实际与69配额相同属于附加观察，不追认为预登记的固定配额比较，也不称相同秒数或干净加速。

两响应分支均93/93帧优于FIXED61和LATE69；分别修复FIXED61相对原WC额外失真的56.3552%和90.8370%。但RESP67仍比原WC差25.0273%，RESP65差5.2544%，相对原WC均0帧改善、93帧退化。正结果属于条件化位置与响应机制；共同61/63交换本身依然不划算。保真是接近原生参考，不能代替物理、语义、运动或绝对质量的接受；单个已曝光Human199/seed0也不是独立CONF。

## 完整执行和证据

科学card `WC-W3-NATIVE-RESPONSE-ONSET-R1-20261007-A`，执行独立R3/source `a8dd451e8f2a7b65d98a14fef4f6c75b7b222739`，原1父/10后缀/6新视频/两比较完整保留。父36更新/72CFG，10后缀各14更新/28CFG，五组九项原始严格重复、pre65四模式/pre67三模式/pre69两模式共36项比较、1216项完整状态组件及终态指纹/output绑定通过；已付probe、合法own-CFG真full历史/age1–33、70reset与71/72D保持。父/OFF/历史FIXED61/LATE69编码字节桥通过。

服务器终态审计独立验收6新+4参考、全部93帧完整解码；评分CPU FP32/Alex LPIPS，五损失中三项仅在Native/候选SHA、协议、PTS相同后复用，新增两项。GPU exit0，终态审计35.882620秒exit0、评分51.122685秒exit0，CPU未初始化CUDA；五原GPU/CPU PID均退出，目标GPU24MiB/noapps、f1共享锁释放。没有新在线策略、单动作RV训练标签或干净端到端加速结论。

- [GPU终态原件捕获](../reports/wc_w3_native_response_onset_r3_gpu_terminal_capture_20261007.json)与[CPU终态原件捕获](../reports/wc_w3_native_response_onset_r3_cpu_terminal_capture_20261007.json)：原字节、压缩归档和SHA交叉绑定。
- [服务器全视频/成本审计](../reports/wc_w3_native_response_onset_r3_terminal_audit_native_20261007.json)；[全93帧五损失与两signed结果](../reports/wc_w3_native_response_onset_r3_lpips_score_native_20261007.json)。
- [本地独立归档复算](../reports/wc_w3_native_response_onset_r3_independent_results_20261008.json)：stdlib，无Torch/视频重评分/服务器提交，复核原始五组重复、前缀、非空完整组件及指纹、动作/计费、逐帧均值和有符号差值；不声称重新计算原张量哈希。

## 费用和下一步

本卡5080.824055889621秒=1.4113400155248947GPUh，低于完整规划1.9111604441544041h；累计18.906279765920353/24GPUh、55jobs、无在途，余5.093720234079647h。[budget](../reports/budget.json)复制服务器结算原字节。R1入口失败与R2context失败的0.049408494386977204h费用、CPU失败原件、旧负结果与原判据全部保留，不重启已完成身份。

下一以已曝光D46原生自适应正例为依据，预登记新seed净效果复验；同时保持原生参考、原WC、完整重复/恢复和失败分母。先完整设计/成本与必要CPU，整卡估计>2GPUh时按用户约定只请求该卡例外，不以拆分/删对照绕过门槛。不给67/65事后调阈值、训练Head/LoRA或扩大稀疏搜索；重大方向选择仍共同讨论。

以下为原CPU修复和运行过程的历史快照，旧pending/running不代表当前状态。


2026-10-07；接续已完成[148真实尾部响应结果](148_WC_W3_NATIVE_TAIL_RESPONSE_CPU_AND_EXECUTION.md)。上一轮完整GPU、终态审计和五终点损失均已结束，原句柄不重启。本轮依[v5.3计划](../plans/WORLD_CACHE_NATIVE_RESPONSE_ONSET_WINDOW_20261007.md)和[事前H-T36登记](../manifests/wc_w3_native_response_onset_r1_preregistration_20261007.json)比较共同61/63交换后65/67/69起点的原生响应，不扩训练、稀疏或人评。

## 首轮实现记录（后续实际执行见文末）

已实现六份独立新源：窗口控制、完整后缀执行、完整轨迹/状态审计、严格范围、CPU夹具和CPU执行入口。旧H-T35/R2代码与实际stage未修改。新范围和全部文件语法/SHA本地检查通过；**实际服务器CPU R1失败已保留，独立R2及原件审计已通过；新生产CPU配置已绑定，GPU尚未提交**。本地解析和纯范围检查不是CPU采样、真实视频或科学收益。

四模式FIXED61/LATE69/RESP65/RESP67保留同一61/63交换和22更新快照；FIXED保持20/18，响应只在登记窗口执行已付probe的原生建议。窗口内容/起点绑定不可变seal，原own-CFG缓存/年龄/有限性检查和70 reset/71–72 full保留，无当前teacher或配额修补。1父/10完整后缀/6编码/两主要比较及全部重复不缩减。

每次真正到达32/33/34更新时保存pre65/pre67/pre69完整latent/cache/solver/RNG/buffers/modes及自身CFG历史。四模式pre65、FIXED/LATE69/RESP67的pre67、FIXED/LATE69的pre69分别连同第一可变调用的输入严格比较；窗口以后的状态独立演化。OFF必须匹配完整父轨迹，全部first/second原始轨迹与终态严格核对。

新的实际CPU只调用受影响接口，复用192份已冻结基础源/九份上游，不复跑旧独立CPU或视频评分。夹具计划覆盖真实固定采样器/缓存/Video2World条件路径的三个完整CPU父、30后缀、18 mock写出，明确改变三窗口的动作；另记录非法own历史、窗口seal变更、非法起点和写出失败，检验完整恢复及失败分母。篡改两个重复使其仍相等，再核验窗口外动作、三个前缀状态/输入/历史、时间顺序与引用等破坏拒绝。**这些计划数尚待实际回执，不代表通过；mock写出不是视频。**

[独立核心CPU绑定](../manifests/wc_w3_native_response_onset_core_cpu_r1_20261007.json)含六份新源SHA、192旧源和九上游SHA及账本原件。下一冻结新提交，独立服务器stage执行禁CUDA/权重/下载的CPU；实际原件、退出码、PID退出、源/预算不变及三组真实CPU轨迹随后独立验收。失败保留，不自动重启原identity。

累计17.445531256/24GPUh、52jobs、无GPU在途、余额6.554468744h保持。本轮GPU新增0；下一完整GPU代理估计1.911160444h，不是硬截止，须实际CPU及生产配置/源/资源/锁/全预算准入后重核。完整≤2h按用户既有自主约定执行，>2h只询问该整卡，不缩拆对照。goal active，当前有可推进代码/CPU工作，非审批阻塞。

## CPU R1实际失败与独立修复

source f366fbf、独立CPU R1的driver3110022/child3110023已退出。44.519227秒内实际完成一组nonflow父36更新/72CFG、10完整后缀和6 mock，并保存原始记录；随后“双重复同时清空终态组件”破坏测试被错误接受，使整套CPU检查exit1。属于新审计实现缺口，不是刷新方法的负结果，亦不能将部分采样完成称为整套CPU通过。原失败[回执](../reports/wc_w3_native_response_onset_core_cpu_r1_native_20261007.json)、[原始记录](../reports/wc_w3_native_response_onset_core_cpu_r1_attempts_native_20261007.json.gz)、日志和源均保留；原失败回执最终CUDA标志为PENDING，不改写。服务器账本原SHA不变，无GPU在途/新增。

修复只修改新验证器、夹具与CPU入口：完整组件拓扑及必备状态族、64位hash格式、tree_digest总指纹、终态output与latent绑定分别验证；三个响应边界也必须具有完整拓扑。破坏检查扩充为20种/每成功组，含同步丢组件、伪造总哈希和更新总哈希但错误output。路由、实际响应动作与生成器不改。

[独立CPU R2绑定](../manifests/wc_w3_native_response_onset_core_cpu_r2_20261007.json)复制195份不变源、替换3份新验证源，并绑定R1原始记录SHA。R2先用新验证器和全部20种破坏检查重审R1真实nonflow记录，不重复其采样；再完成尚未执行的flow普通/故意响应差异两组，以及四个故障。覆盖仍为三父/30完整后缀/18 mock，但新执行为两父/20后缀/12 mock、复用一父/10后缀/6 mock；计划60次破坏拒绝。R1失败身份保持，R2只有实际exit0、独立原件/状态/重复/源/账本验收后才能称为CPU通过。

## CPU R2实际通过与生产入口

source d728afa的独立R2已exit0，driver3110803/child3110804均退出，CPU整过程163.328345秒。新执行两组完整父/20后缀/12 mock，重审R1保存的一组父/10后缀/6 mock，覆盖三组而不重复已完成采样；四故障和全部60次破坏拒绝、24个故意改变的原生响应动作通过。独立只读审计重新核验三组原始记录、全部破坏拒绝、旧记录原SHA与内容、全部源/上游/账本及PID退出；实际CUDA未初始化/GPU提交0。修复验证不是新视频效果。

[实际回执](../reports/wc_w3_native_response_onset_core_cpu_r2_native_20261007.json) · [独立审计](../reports/wc_w3_native_response_onset_core_cpu_r2_audit_20261007.json) · [原始记录](../reports/wc_w3_native_response_onset_core_cpu_r2_attempts_native_20261007.json.gz)。此前R1整体exit1保留，不追改为通过。

新生产入口绑定214文件、同一已登记1父/10后缀/6视频/两比较；官方WC/FIXED61/LATE69真实字节桥和三个响应起点完整状态门槛保持。评分复用三份同SHA同93帧协议的旧损失，仅新增RESP65/67两损失，同时报告对原WC、FIXED61和LATE69的保真及实际后缀成本。下一实际draft/contract/validate/import四步CPU和唯一selected复核，未通过前不启动GPU。

生产CPU R1 source d17cd95的draft/contract已exit0（16拒绝和两signed正负/计费/旧损失复用检查）；validate由于driver误拼输出目录，与冻结run_id不符而exit1，仅0.348340秒，import尚未执行。原失败回执/三log/driver保存，预算及214源不变、driver和三children退出、GPU新增0。新独立生产CPU R2修正driver目录绑定，214源与配置不变；绑定原成功draft/contract原SHA重用，只实际执行未完成的validate/import。不得重启R1或把R1原失败称为通过。

生产CPU R2实际完成，source49d1be6、67.362928秒/exit0；两未完成validate/import新执行，原两draft/contract同214源原SHA复用，完整四步覆盖/16拒绝/正负signed计费/损失复用/真实资产与源及独立回执审计通过。3111847/3111848/3111859和复用旧两PID均退出，CUDA未初始化、源/上游/账本未变。GPU仍0。CPU后完整成本以H-T35实计和最大完整后缀重核，仍6880.177599秒=1.911160444h、整卡未拆、累计可容纳；这是带余量代理，不是实际速度或时限。

## 首次真实执行入口失败，独立恢复登记

R1已进入监督计费，但在模型加载前因生产GPU入口导入run_native_onset_causal_batch（实际名称为run_native_response_causal_batch）退出1。此前CPU模块导入未检查具体GPU分支调用符号，这是生产检查遗漏。没有初始化CUDA/父轨迹/后缀/视频/评分；不得算作方向或方法负结果。3112329/3112346均已退出，目标24MiB/noapps、锁释放；全wall35.867029秒=0.009963064GPUh已计入，累计17.455494320/24h、53jobs、noinflight，账本按服务器原字节同步。原失败源、原回执、日志与释放/计费独立审计保存，不重启R1或覆盖其目录。post-CPU未提交。

修复仅更新三个生产文件：正确的具体函数导入及调用、CPU callable/AST绑定检查、独立恢复run身份。六份已经验收的核心源不改，不重跑其CPU采样。独立技术恢复登记绑定原失败原SHA与全费用，保留H-T36原科学scope/prereg1父10后缀6视频两比较，使用wc-w3-native-response-onset-r2执行目录；新完整成本仍约1.911160444h。需要新实际生产四步CPU/selected/fresh锁资源预算后才能执行。

修复后的独立生产CPU source1a19ed9实际54.132049秒/四步骤exit0，具体函数导入与两个分支AST绑定检查、同六核心源/三旧同SHA损失、完整scope/计费/参考/资源原件核对以及独立捕获通过。215文件、CUDA未初始化/预算不变、原driver及四children退出；仅生产检查，未重复旧CPU采样。下一R2 selected与freshGPU准入，完整1父10后缀6视频两比较保持。

## 独立恢复任务已实际进入GPU初始化

R2科学范围同事前H-T36，source f7ac858，独立selected-r2与wc-w3-native-response-onset-r2。selected真实预检12.173986秒通过；fresh目标A6000空闲24MiB、锁与53jobs账本通过完整1.911160444h准入。supervisor3113526/runner3113545实际命令与source/stage匹配；现场GPU进程为该runner，目标已占24514MiB，正在模型初始化，尚无父/后缀/视频/科学结果。初始runner回执CUDA字段尚未在load结束时更新，现场进程/显存另记录，不将初始false当作当前无GPU。

启动前已结算17.455494320/24h；服务器第54job将剩余余额暂预留至24，非实际耗尽。根budget保留最近已结算原件，R2最终按包括加载/失败/清理的全wall实计。旧秒数截止取消；单次2GPUh与累计24约定保持，不缩拆对照。R1失败来源/35.867029秒/原目录继续保留，不重启旧任务。

R2已实际完成模型加载（90.983788秒、CUDA true），但生成前context门槛因执行runR2与冻结科学scope R1的前缀不同而退出1；没有父/后缀/视频，属于恢复身份绑定错误。runner3113545/supervisor3113526及postCPU3113976已退出，postCPU正确拒绝失败GPU、零审计/评分步骤。目标24MiB/noapps、锁释放，全部142.003551秒=0.039445431GPUh计入，累计17.494939750/24h、54jobs/noinflight；原失败回执/源/加载费和CPU终态保留，不重启R2。

新R3技术恢复只修正生产上下文构造：执行目录runR3，科学上下文用原scope R1；六核心源不变。生产CPU新增调用真实核心至context通过后的受控停止点，分别验证接受/拒绝和完整状态恢复，两个flow接口均不调用forward/solver/生成/解码/写出；此前已完成的三组采样不重跑。原GPU两次失败计费保持，完整scope/成本/指标/历史桥不变，等待新CPU/selected及唯一资源准入。

R3上下文修复的实际生产CPU sourcecf42bfb、68.373400秒/四步exit0、216源及九上游/预算不变，独立原件捕获通过。两个flow共四次实际核心早期门槛（正确上下文接受、错误上下文拒绝）及完整状态恢复通过；受控停止于apply_worldcache入口，forward/solver/生成/解码/写出均未发生，没有重跑旧CPU采样。具体入口/AST检查、16范围/计费/评分复用拒绝、source/reference/import也通过；CUDA未初始化，driver及四children退出。下一唯一R3 selected/fresh资源准入，原两次GPU失败合计0.049408494h继续保留。

## 当前R3实际采样进度

source a8dd451、独立selected-r3与wc-w3-native-response-onset-r3；实际selected预检12.257327秒与fresh锁/目标A6000/54jobs账本准入通过。supervisor3115400/runner3115418的原命令、source/stage及目标GPU进程现场确认，模型加载75.516691秒/CUDA true，prompt guard通过，实际父采样9/36步。此9/36只属于父进度；完整1父/10后缀/6视频/两终点比较尚未完成，尚无新科学结果。JSON请求初始保存时calls0、日志actual9/36都保留，不把旧标量INITIALIZING等同于当前未采样。

post-CPU3115990实际存活，冻结source/binding SHA和原3115400/3115418句柄核对，当前WAITING、零审计/评分步骤；只有原GPU成功exit0/源/计费/释放符合才执行全6新+4参考解码、五Native损失（3同SHA协议复用+2新）/两signed及真实成本。旧R2post失败也保留。已结算17.494939750/24h、54jobs，根budget为该原件；服务器第55job预留余额至24代表在途保护、非实际花完。本卡完整规划1.911160444h，单次2GPUh/累计24保持，前两次失败全费0.049408494h不清零。

## R3首条完整后缀及视频已保存

2026-10-07 23:20–23:22本地时区现场只读核对：原supervisor3115400/runner3115418仍在source a8dd451的独立selected-r3运行。父前缀已22更新/44CFG；OFF1完整后缀14更新/28CFG完成，原生视频guard通过并保存第一段MP4，OFF2开始。仍须父最终36更新/72CFG、其余九后缀、其余五视频、完整重复/恢复/字节桥及CPU评分，不能将首视频保存称为整批完成或新保真收益。

[现场原件](../reports/wc_w3_native_response_onset_r3_live_off1_20261007.json)同时保存GPU进程/trace/预算及postCPU现场。冻结postCPU3115990、真实continue.py路径、原始driver/binding和审计/评分源SHA均一致，仍WAITING、评分步骤0；无新增GPU提交。已结算17.494939750/24GPUh、54jobs保持，第55job在途保护预留至24不代表实际花完。此前GitHub服务端临时错误已恢复，执行代码和启动/早期采样回执66eec6b已成功推送。

## 两条OFF重放实际一致与历史视频字节桥

2026-10-07 23:28:50现场只读捕获：OFF1/OFF2均完成14更新/28CFG。输入、输出、深层执行、缓存banks、求解器输出、最终latent、65/67/69响应边界、完整终态组件和动作报告九项原始比较全部严格相同，两个record均记载parent_restored true。OFF1实际文件SHA/大小与冻结历史官方WC相同（SHA4d0f0549…dde982fb）。原supervisor3115400/runner3115418及postCPU3115990实际命令核对存活，FIXED61_first已开始；原postCPU等待、零评分步骤。

[实际只读检查](../reports/wc_w3_native_response_onset_r3_off_repeat_live_20261007.json)绑定[原字节在途快照](../reports/wc_w3_native_response_onset_r3_off_repeat_snapshot_native_20261007.json.gz)，原receipt SHAac507fca…9374de0；本地从原件重新计算九项比较，与回执逐项一致。此仅证明已完成的两个OFF重复和历史视频桥；父仍只有22更新前缀，其余8后缀/5视频、完整响应门与评分尚待。新科学收益未知，预算最近结算17.494939750/24h保持，无新增GPU或评分提交。两份终态只读取回脚本已准备，尚未产生终态结果或改在跑代码。

## 首条FIXED61与历史固定分支字节一致

2026-10-07 23:34:49现场独立只读检查：FIXED61_first完成14更新/28CFG，完整逐CFG调用配额20/18、parent_restored true；保存视频的实际文件SHA742771d1…29a3574及大小2107088均与冻结历史FIXED61相同。[实际桥检查](../reports/wc_w3_native_response_onset_r3_fixed61_history_bridge_live_20261007.json)保留原路径、大小、SHA和两个原GPU进程现场存活。当前3/10后缀、2/6视频完成，LATE69_first已开始。固定桥支持后续同SHA旧损失复用，尚不代表新响应收益；完整重复/三个响应起点状态门、父桥与终点评分仍待。没有新GPU或评分提交，现有源/stage与计费政策保持。

## LATE69历史视频桥和实际响应前状态一致

2026-10-07 23:43:05现场只读核对：LATE69_first完成14更新/28CFG并保存，实际视频SHAf013ab67…668cb8fb及大小2107535与冻结H-T35的TAIL61完全相同；OFF/FIXED61/LATE69三份旧损失候选的编码字节桥均已完成，最终同协议/PTS复用仍由原postCPU在完整GPU结束后验收。

FIXED61与LATE69的pre65/pre67/pre69完整组件与自身CFG历史均严格一致，响应第69调用输入也相同；此前输出/深层执行/banks/求解器前缀一致，实际动作只在69/70变化，LATE全程完整调用21/19、固定20/18。[现场八项检查及真实文件桥](../reports/wc_w3_native_response_onset_r3_late69_history_and_pre69_bridge_live_20261007.json)绑定[原字节快照](../reports/wc_w3_native_response_onset_r3_late69_prefix_snapshot_native_20261007.json.gz)，SHA084afd3e…9de0704；本地从原件再次核对全部八比较和两动作变化。只检查已完成的这两模式，不追认RESP65/67尚未完成的四/三模式前缀门。

原两个GPU进程及postCPU3115990命令现场存活、source一致，postCPU仍WAITING/零步骤；当前4/10后缀、3/6视频，RESP65_first已开始，无新终点指标或质量/速度结论。预算最近结算与全scope保持，没有新GPU/评分提交。

## 首个RESP65：新动作已发生，质量与重复尚待

2026-10-07 23:49:42实际只读核对：RESP65_first完成14更新/28CFG及视频保存，SHA799ba87c…0b4d9ccd。窗口65–70的六次决策均使用已付probe/自身原生建议、无当前deep真值；实际相对共同固定掩码的变化是65/66/69/70，其余67/68保持cache。因此全程CFG完整数22/20，晚响应21/19，新增两次deep完整调用，并未用事后配额修补保持相同预算。首条控制wall369.374434秒只属一次诊断成本，不是两重复均值或干净速度。

[真实动作/部分前缀检查](../reports/wc_w3_native_response_onset_r3_resp65_action_live_20261007.json)绑定[原字节快照](../reports/wc_w3_native_response_onset_r3_resp65_snapshot_native_20261007.json.gz)，原receipt SHAb2ccc327…37a6f451。FIXED61/LATE69/RESP65三已完成模式的pre65完整组件/own历史及第一可变输入、此前所有输出/深层/banks/求解器前缀严格一致；本地从原件重新核对两组各六比较、实际两CFG次数和四动作变化。RESP67这一第四模式的门尚未完成，不将三模式检查称为完整四模式验收。

当前5/10后缀、4/6视频，RESP67_first已开始；原supervisor3115400/runner3115418实际命令存活/source不变。新两个主要终点比较、全部五组重复、父完成/旧桥/状态恢复和CPU全93评分仍待，不能据已保存候选判断保真或质量收益。预算最近结算/当前在途及完整范围保持，没有新GPU或评分提交。

## 四个first完整结束，全部响应起点前状态门通过

2026-10-07 23:56:54实际现场：四模式first均完成14更新/28CFG和视频编码。注册的pre65四模式、pre67三模式、pre69两模式完整状态/own-CFG历史、第一可变调用输入及所有此前输出/深层/banks/求解器更新一致；组件具备必备族、非空历史和完整64位SHA形式。两原GPU句柄及postCPU3115990命令现场存活/source一致，postCPU WAITING/零评分步骤。

首轮全程完整数FIXED20/18、LATE21/19、RESP65 22/20、RESP67 21/19；RESP67窗口四次均为已付probe/自身原生建议，实际只将67/68由C改D，69/70原生仍C。它与LATE首轮有相同完整数、不同刷新位置，这是事后观测到的附加条件，不改主要窗口比较或追认预先匹配配额。首轮控制wall依次359.028889/363.556817/369.374434/363.465239秒，只是单次诊断成本，不能称相同秒数或干净速度。

[全起点门与RESP67真实动作](../reports/wc_w3_native_response_onset_r3_all_first_gates_and_resp67_live_20261007.json)绑定[原字节快照](../reports/wc_w3_native_response_onset_r3_all_first_gates_snapshot_native_20261007.json.gz)及[只读检查源码](../reports/wc_w3_native_response_onset_r3_all_first_gates_readonly_driver_20261007.py)。本地从原件独立重新计算三个门的36项比较及四模式计数，一致。当前6/10后缀、5/6视频，RESP67_second已开始；四个second/父最终/全部严格重复恢复及CPU终点评分仍待，没有新质量或净收益结论。全scope、现有预算/费用、原判据与负例保持，无新增GPU或评分提交。

## 2026-10-08：RESP67两次完整后缀严格一致

00:06:08本地时区现场捕获，原20261007科学卡/执行runR3/source a8dd451不变。RESP67_first/second两条14更新/28CFG后缀完成；输入、输出、深层执行、banks、求解器输出、终态latent、三个响应边界、完整终态组件和动作报告九项严格相同，两个parent_restored true。两次均仅改变67/68、完整数21/19，控制wall363.465239/363.672190秒，均值363.568715秒仅作诊断成本。

[实际严格重复核验](../reports/wc_w3_native_response_onset_r3_resp67_repeat_live_20261008.json)绑定[原字节在途快照](../reports/wc_w3_native_response_onset_r3_resp67_repeat_snapshot_native_20261008.json.gz)及[只读检查代码](../reports/wc_w3_native_response_onset_r3_resp67_repeat_readonly_driver_20261008.py)；本地重新计算原件九比较与回执一致。原两个GPU句柄与postCPU3115990实际命令存活、source相同，postCPU仍WAITING/零步骤。

当前7/10后缀、5/6视频，RESP65_second已开始；其余三个second、父最终、完整释放/计费/全93审计及两个主要评分仍待，没有新终点质量/净收益或物理结论。预算最近结算17.494939750/24h保持、当前第55job预留非实计，全scope和旧负例/费用不变，无新增GPU或评分提交。
