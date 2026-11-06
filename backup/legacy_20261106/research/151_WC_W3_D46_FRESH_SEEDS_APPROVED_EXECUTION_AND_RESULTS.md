# W3 D46 两个新 seed 完整复验：直接批准与执行

## 完整执行、终点评分与阶段结论

本卡已完整结束：2条Native父、2条WC父、12条完整后缀、10段新视频、两组signed比较全部完成。source `5143d464faebeaeffad7a9500b048977089561ab`保持；GPU exit0，原GPU/CPU四PID退出、目标GPU释放、共享锁可用。17项选择载荷、216项基础载荷及输入SHA、三个严格重复/seed、同状态/current-input、父/OFF/BASE实际及编码桥、Native/WC初始状态、10视频全93帧解码与四组LPIPS均通过。CPU评分118.049033秒exit0，CUDA未初始化。原件和独立重算已归档，不重启本卡身份。

**阶段发现：固定D46刷新未在本次eligible新seed上复现旧收益；出现明确适用条件差异，值得用低成本联合CFG对照继续W3。** 这是当前操作的负结果，不否定整个刷新调度方向。两个新seed的原分母保持，no-op不算策略成功。

| 新seed | 原生call46 | BASE LPIPS | REFRESH LPIPS | 相对保真变化 | 改善/退化/持平帧 | 全程完整调用 |
|---|---|---:|---:|---|---|---|
| 1 | D，no-op | 0.357724721 | 0.357724721 | 持平 | 0/0/93 | 37→37（19/18→19/18） |
| 2 | C，可干预 | 0.415138287 | 0.427260689 | 失真增加2.9201% | 1/92/0 | 35→36（18/17→18/18） |

seed2当前多1次完整计算、严格未来calls47–72仍为8/7、净多1；诊断wall多3.315082秒。seed1实际状态/动作/编码全相同，却有3.060161秒诊断差值，该差值不能算计算节省或抵消seed2的真增算。两新seed等权signed LPIPS均值−0.006061201，场景内相对改善均值−1.4600%；eligible子集只有seed2，signed−0.012122402。旧seed0的+2.8080%和净省2仍保留，不能把被选中的旧正例并入新seed均值形成无偏确认。

完整GPU成功wall7689.045155秒=2.135845876GPUh；加上本卡两个旧初始化失败306.626201秒=0.085173945GPUh，合计2.221019821GPUh。账本原字节已复制，累计21.127299587/24GPUh、58jobs、无在途，余2.872700413GPUh。旧秒数deadline不恢复。本地只读归档首次因服务器默认Python3.8缺少Path.is_relative_to而exit1，未写输出或改账本；保留失败回执，改用等价严格后代路径检查后成功，不改原GPU或评分。

[完整signed原件](../reports/wc_w3_d46_r3_signed_summary_20261008.json) · [原件终态/源/释放/费用捕获](../reports/wc_w3_d46_r3_complete_20261008_terminal_capture.json) · [独立逐帧/符号/费用重算](../reports/wc_w3_d46_r3_independent_reconstruction_cpu_20261008.json) · [只读归档兼容失败](../reports/wc_w3_d46_r3_capture_cpu_r1_failure_20261008.json)。

随后先登记并完成[既有记录CPU条件分析](152_WC_W3_D46_EXISTING_CONDITION_CPU_RESULTS.md)：旧正例缓存年龄2、此前CFG0本步D；新负例年龄1、此前CFG0本步C。固定D46在前者形成D/D、后者形成C/D；年龄与CFG联合状态同时不同，尚不能因果归因。原配对、重复、Native参考和指标协议对齐；同状态D臂在动作前已记录数值probe信号，见152追加更正（原CPU R1保留）。下一项只准备同seed/同状态的原C/C、单槽C/D、联合D/D区分，以检验两CFG误差组合；不训练Head/LoRA或增加稀疏、人评。

同prompt新seed仍为已曝光CAL复验；LPIPS为Native相对保真，不提供物理/语义非劣；诊断wall不是干净端到端速度。goal active，继续按实验设计准备有限区分，当前所有旧运行/CPU/评分/捕获身份均已消耗。

## 以下为保留的历史执行记录

2026-10-08。用户直接答复“好的 允许这次实验”，对应已说明的完整卡 `WC-W3-D46-FRESH-SEEDS-R1-20261008-A`：seed1/2、2条Native+2条WC父轨迹、12条完整后缀、10段新视频和两组有符号质量/成本比较。单次预计2.422930905 GPUh的例外已经获得，累计24 GPUh及18.906279766h旧费用保持，不再等待该卡授权。

冻结的新科学/运行/监督/评分源码与实际CPU通过原件保持；本次只新增具体批准、选择配置和部署绑定。BASE保留原生自适应，REFRESH只在call46完整计算一次后继续同一策略；原生已D的no-op、失败和拒绝保留，不换seed/调用，不增加训练、稀疏搜索或人评。LPIPS为原生相对保真，诊断wall不作干净加速，同prompt新seed不作跨场景独立CONF。

[直接授权](../manifests/wc_w3_d46_fresh_seeds_gpu_authorization_20261008.json) · [选择配置](../configs/wc_w3_d46_fresh_seeds_r1_selected_20261008.json) · [完整准备与设计](150_WC_W3_D46_FRESH_SEEDS_CPU_AND_CARD.md)。下一步为选择配置的实际授权/source/CPU原件门，以及fresh GPU/锁/预算的唯一准入；当前尚未GPU提交，无新科学结果。旧blocked为授权到达前的历史，goal工具当前active。

## 选择门通过，原GPU进程已启动

选择配置的实际source/assets/具体批准/同源CPU原件门exit0，19.415571秒，CUDA未初始化，未重复旧核心夹具或模型。source `fb890da58a21d7403ce23f98d2ca1b173cc69b25`，科学运行代码SHA与原实际CPU通过源保持。完整2Native+2WC父/12后缀/10新视频/两signed不缩减。

唯一run `wc-w3-d46-fresh-seeds-r1` 已按fresh目标A6000 24MiB/noapps、共享锁及18.906279766/24h账本准入提交。原supervisor **3190813** / runner **3190976** 的真实CLI、stage/source/目标GPU进程均确认，当前模型初始化中，目标占用24514MiB；未生成新视频或科学结果。具体GPU运行已开始，不把批准或healthy进程当成方法有效。

原CPU后处理driver **3193255** 只绑定这两个原GPU句柄和冻结13项载荷；当前WAITING、零评分。仅在原GPU成功结束、原PID退出、锁及GPU释放后，自动执行完整源/费用/状态恢复/视频审计与全部可用的93帧LPIPS，保留no-op/拒绝/负例。CPU失败也保留日志，不重复提交GPU。

服务器第56job在途，used=24h是持锁期间预留全部剩余余额的保护状态，非实际耗尽；最近已结算实费18.906279766h保持，结束后按全部wall实际结算。旧秒数deadline不恢复，累计24h保护仍在。goal active，仅跟踪本次原run，不修改冻结源或重启旧任务。

[实际选择CPU原件](../reports/wc_w3_d46_selected_preflight_native_20261008.json) · [唯一GPU提交](../reports/wc_w3_d46_fresh_seeds_gpu_launch_20261008.json) · [PID/GPU现场](../reports/wc_w3_d46_fresh_seeds_gpu_start_live_20261008.json) · [CPU接续绑定](../reports/wc_w3_d46_postrun_cpu_launch_20261008.json)。

## R1初始化失败已完整结算；同一批准卡的环境修复

原source fb890da在模型初始化的Blocklist构造处exit1：监督入口漏了旧成功入口的`HF_HUB_CACHE=project/hfhub`，实际导入查找了默认缓存中不存在的`blocklist/custom`。正确项目缓存的资产原验收通过且未变；这属于入口环境实现问题，未进入任何Native/WC父轨迹或后缀，视频0。不能解释成新seed方法失败。

3190813/3190976/3193255全部退出、GPU24MiB/noapps、锁释放；原日志、回执、全部费用及CPU后处理拒绝保留，未评分。[失败原件审计](../reports/wc_w3_d46_r1_failure_audit_20261008.json)：172.163342秒=0.047823151GPUh，累计18.954102917/24h、56jobs/noinflight，余5.045897083h，根budget复制原字节。旧R1不重启。

必要技术恢复仍服务用户本次“好的 允许这次实验”的完整2Native+2WC父/12后缀/10视频/两signed，不另开科研卡或缩拆对照；科学scope R1保持，独立执行身份R2避免覆盖失败目录。只修缓存环境/增加实际Blocklist CPU构造核验/分离执行输出目录，四个科学core源码SHA不变；guardrails不关闭、无新权重下载或训练。完整剩余规划2.422930905h，包含已发生失败的本次规划2.470754056h，原预测不是硬deadline或清零费用。实际受影响CPU/source/assets/provenance及fresh准入通过后继续同一已批准实验，累计24h保持。

## 缓存环境修复的实际CPU通过

新增实际Blocklist CPU构造首次29.063036秒exit1，因为Transformer Engine导入阶段请求Triton benchmarker；原回执/日志保留，无GPU或账本变化。采用已有S0 CPU源检查的ImportOnlyDriver：只返回禁止执行的benchmarker，不运行kernel、不改变真实GPU路径。新的独立production CPU r3实际34.160311秒exit0，source2fcabc1，真实HF缓存常量/Guardrail1目录/Blocklist读取、seed1/2解析和全部真实Native/causal/portfolio导入、原失败SHA/同一科学scope均通过，CUDA false。

原CPU两个句柄3205110/3205111退出，14项新载荷及216项基础源码前后SHA相同，预算18.954102917/24h未变，独立执行R2的GPU输出不存在。没有重跑旧核心Toy或生成。生产配置选择与fresh准入待；用户对完整本次实验的直接批准保持，仅修复必要环境实现，不另开方向或执行完整重复卡。

[实际CPU原件/审核](../reports/wc_w3_d46_recovery_cpu_r3_audit_20261008.json) · [CPU导入失败原件](../reports/wc_w3_d46_recovery_cpu_r2_failure_audit_20261008.json) · [恢复绑定](../manifests/wc_w3_d46_r2_technical_recovery_20261008.json) · [独立选择配置](../configs/wc_w3_d46_fresh_seeds_r2_selected_20261008.json)。

## R2加载成功但Native延迟导入缺依赖；完整闭包CPU通过

R2缓存修复已生效，模型97.476849秒实际加载成功；进入seed1 Native函数后，在采样前因部署包缺少`wcomr.guardrail_observation`退出1。三个原PID3209212/3209383/3211505退出、GPU24MiB/noapps、锁释放；原件与134.462859秒=0.037350794GPUh全部保留，仍0视频/0采样。累计18.991453711/24h、57jobs/noinflight，根budget已复制服务器原字节。两次失败费用总0.085173945h，不是新seed收益的负结果。

Native延迟导入的完整本地闭包检查发现三个既有文件未部署：guardrail_observation.py、protocol.py和w1_native_reference_scope.py。只补齐既有源码，不修改Native采样、缓存算法或四个D46科学core。新增CPU检查直接调用真实Native入口，执行所有延迟导入后在生产前置条件处明确停止，不构造模型或采样；递归核对29个本地模块均在stage内。缓存常量与真实Blocklist构造继续检查，CPU ImportOnlyDriver仅用于退出的CPU进程。

新production CPU r4 source913b1a6实际32.152926秒exit0：Native延迟导入、29模块闭包、原失败SHA、解析seed1/2、实际缓存/安全词表和真实函数导入均通过，CUDA false、17新载荷/216基础源码SHA前后保持、两个CPU PID3222809/3222812退出、预算不变。原GPU未重启，核心Toy未重跑。独立执行R3与冻结科学scope R1分离，仍为同一用户直接批准卡的2Native+2WC父/12后缀/10视频/两signed；含已发生失败的完整预测2.508104850h，原24h累计不变。下一selected与fresh准入，不扩大方向或缩拆对照。

[R2失败审计](../reports/wc_w3_d46_r2_failure_audit_20261008.json) · [实际闭包CPU](../reports/wc_w3_d46_recovery_cpu_r4_audit_20261008.json) · [R3恢复绑定](../manifests/wc_w3_d46_r3_technical_recovery_20261008.json) · [选择配置](../configs/wc_w3_d46_fresh_seeds_r3_selected_20261008.json)。

## 完整依赖修复后的独立R3已实际启动

actual selected CPU门12.126459秒通过，source `5143d464faebeaeffad7a9500b048977089561ab`，与实际闭包CPU代码一致；科学scope仍为原登记R1，本次只分离失败后的执行目录R3。fresh A6000 24MiB/noapps、共享锁和18.991453711/24h账本准入后，run `wc-w3-d46-fresh-seeds-r3` 唯一提交。原supervisor **3224687** / runner **3224830** 的真实CLI/source/stage/目标GPU进程均确认，24514MiB模型加载中，实际子环境使用正确HF_HUB_CACHE、offline1和OMP2。当前尚无新科学结果。

新CPU driver **3225754** 只绑定这两个原GPU句柄和17项载荷。GPU成功结束/原PID退出/释放后自动做源、实际费用、完整恢复、重复、每seed分母、10段视频全93帧解码及四组可用Native相对LPIPS/两signed比较；当前WAITING、零评分。不重启旧R1/R2/CPU或改在跑源。用户完整卡批准及原24h累计保持，两个旧失败全费保留。

服务器第58job在途，used=24为持锁预留剩余余额，非实际耗尽；最近已结算18.991453711h/57jobs保持，结束按全wall实际结算。goal active，只观察三个当前原句柄，不扩大训练、稀疏或人评。

[实际selected门](../reports/wc_w3_d46_r3_selected_preflight_native_20261008.json) · [唯一R3提交](../reports/wc_w3_d46_fresh_seeds_r3_gpu_launch_20261008.json) · [真实PID/HF环境/GPU](../reports/wc_w3_d46_r3_gpu_start_live_20261008.json) · [CPU接续](../reports/wc_w3_d46_r3_postrun_cpu_launch_20261008.json) 。

## 已通过初始化并进入真实Native采样

最新原现场：模型86.212327秒加载完成，seed1 Native35已通过prompt guardrail，实际生成日志到1/36更新。原3224687/3224830存活且匹配stage/source/HF环境，目标GPU上的compute PID为原runner；CPU3225754仍只等待原GPU，零评分。真实首条父生成已开始，两个旧入口故障已解决；完整两seed卡及后缀、视频、全93帧质量/成本结论仍未完成。过程中durable Native计数只在阶段边界保存，不能把当前回执的0计数当作日志已发生采样不存在。

[真实Native采样现场](../reports/wc_w3_d46_r3_actual_native_sampling_20261008.json)。仅跟踪runR3三个原句柄，保持运行源不变，继续完成后缀和自动CPU审计/评分；累计费用最终按原监督回执结算，当前第58job在途预留不是已花24h。

## seed1原生参考已保存；旧计数边界CPU核对

原runR3/source5143d46保持，seed1 Native已ACCEPTED并保存原文件，完整36更新/72 full调用；文件890682字节、SHA `5f5d6489252995d06c83cdc01d5ba02da271beb1e4eaf7132573cdae0b9daac9`。Native输出尚待整卡释放后的全93帧解码与LPIPS，保存不代表新刷新方法正结果。当前相同seed的WC父生成已实际到10/36，尚未完成任何新suffix；原supervisor3224687/runner3224830存活，CPU3225754只待原GPU终态。未重提交/修改在跑source。

CPU只读旧Human/seed0原始trace，将“当前”和“未来”成本拆开：C/D快照后calls45–72完整数18→16；严格未来calls47–72为17→14（CFG由9/8→7/7），当前call46由0→1。因此当前增加1、未来节省3、全路径净省2；全路径CFG20/18→18/18。原LPIPS和科学结论未变，旧“后续18→16”更准确指包括当前附近两调用的后缀。本次新seed的事前signed终点不改，只在最终报告额外明确当前/未来/全路径边界。

新增纯标准库CPU结果汇总器，结束后从原runner/CPU评分/监督器原件输出两个seed逐个有符号结果、原D no-op与Native拒绝分母、等seed均值及当前/未来/全路径完整次数。已用旧真实记录核对上述18/16、17/14和全路径38/36及严格重复，不重跑GPU/旧LPIPS；当前新seed终点仍为0，不能把该分析当新生成收益。

[首条Native现场](../reports/wc_w3_d46_r3_first_native_accepted_live_20261008.json) · [旧原件计数核对](../reports/wc_w3_d46_current_future_cost_boundary_cpu_20261008.json) · [最终CPU汇总器](../scripts/summarize_wc_w3_d46_fresh_seeds_cpu.py)。

## seed1首条完整后缀结束；原件终态捕获准备

当前原runR3已在登记快照22更新/44调用后完成OFF1的14更新/28调用，保存完整record，正在原decoder/guardrail输出流程；仍只有已保存的首条Native视频，BASE/REFRESH有符号终点未完成。原两个GPU句柄与CPU等待driver保持，source5143d46未改，未新增GPU提交。完整卡按原两seed范围继续。[首条完整后缀现场](../reports/wc_w3_d46_r3_first_suffix_complete_live_20261008.json)。

新增标准库只读[终态捕获器](../scripts/capture_wc_w3_d46_terminal_cpu.py)，本地及嵌入远程源码均语法解析通过；尚未对live卡执行。它要求原GPU成功退出、CPU全93解码/LPIPS完成、原四PID退出、锁/目标GPU释放、全部新/基础/输入哈希不变、实际费用结算后才归档原JSON/日志/监视器/绑定/评分的压缩字节并复制已结算budget。Native拒绝仍保留两seed分母，实际视频数按8+接受Native数核对。捕获成功不是新的研究结论；随后从同一原件执行已有signed汇总器。

结束后的唯一捕获命令（未执行）：

```sh
python3 scripts/capture_wc_w3_d46_terminal_cpu.py --manifest manifests/wc_w3_d46_fresh_seeds_selected_r3_20261008.json --launch reports/wc_w3_d46_fresh_seeds_r3_gpu_launch_20261008.json --ssh-target gkd_minchen --postrun .sync/wc-w3-d46-fresh-seeds-postrun-cpu-r3-20261008 --prefix reports/wc_w3_d46_r3_complete_20261008
```

捕获后用`scripts/summarize_wc_w3_d46_fresh_seeds_cpu.py`读取`*_runner_json_native.gz`、`*_CPU_score_json_native.gz`、`*_supervisor_json_native.gz`与两次失败audit，保留全部signed结果/当前与严格未来计算边界/诊断时间及费用；不重跑GPU、旧LPIPS、训练或人评。当前最近实费18.991453711h保持，58th在途24预留不作花完。

## seed1原生D46条件已观察到；按登记保留no-op

只读首条OFF1完整原始record表明，seed1在call46/CFG1的paid probe原生建议已是D（native_skip=false、requested=null、actual_action=D），后缀45–72完整CFG数为8/8。因此该seed的REFRESH请求按预登记应为no-op；最终严格重复、BASE/REFRESH原始与编码一致及全93评分仍待，不能凭首条OFF把整卡验收完成或报策略成功。[原事件/现场审计](../reports/wc_w3_d46_seed1_native_D46_live_20261008.json)绑定当时runner压缩原字节SHA和真实原PID，不修改在跑源。

这增加了对干预适用范围的证据：同一已曝光prompt换seed后，既有call46并非必然是可改变的C点。它不否定W3，保留两个预定seed/位置/原分母，完成全部控制和seed2，不为制造效果换位置或强制C。若最终两个seed均no-op，按v5.4说明未检验eligible动作泛化，并另登记低成本区分实验；当前只知道seed1，尚不选择下一卡。

## 终态汇总的成本分母补齐（纯CPU报告层）

既有终态汇总器补齐两个登记seed的等权诊断时间/全路径完整数及no-op耗时子集；即使某条Native参考被安全管线拒绝，已执行的BASE/REFRESH时间和完整次数仍保留，只有Native相对质量缺失。每臂两次耗时范围同时报告；原生D46的实际动作/轨迹一致时，非零诊断时间差只作条件或运行波动，不能计为节省模型计算。以上沿用冻结Δq/Δt及拒绝/no-op分母，不增加生成或修改在跑的GPU/CPU评分源。

Python语法解析通过；只读旧Human原始两重复实际wall复核C=[326.503529,328.487381]、D=[321.037228,320.992239]，同一算式输出既有Δt=6.480721秒，不重跑旧GPU/LPIPS，也不当成新seed结果。新卡完整终态仍待。

## seed1首组真实完整后缀严格重复核对通过

OFF1与OFF2均完成14更新/28调用。纯标准库CPU读取当前原回执，按冻结base源码的TRACE_KEYS核对全部输入、输出、deep、cache banks、求解器输出，以及pre46完整状态、最终latent、最终状态组件和动作报告，九项完全一致；两次parent恢复标志均为true。绑定当时原runner压缩字节及SHA，真实原GPU进程仍在执行BASE_first，CPU终态driver仍等待。[两完整重复原件/CPU核对](../reports/wc_w3_d46_seed1_OFF_repeat_live_cpu_20261008.json)。

这验证了新seed第一组状态恢复与重复，尚不替代剩余BASE/REFRESH重复、父编码字节桥、整卡验收或终点质量。没有Torch导入、GPU新增或旧评分复跑，冻结source5143d46保持。

同一组真实严格重复的诊断wall为475.162955秒和365.819382秒，相差109.343573秒。输入/状态/输出及实际动作一致的前提下，这说明当前诊断计时对首次执行、恢复/哈希开销或运行条件敏感；具体来源未拆测，不唯一归因于暖机或其他负载。原登记Δt继续保留，但不据小幅时差宣称稳定净加速；结合实际完整次数、当前/严格未来边界和整卡全wall费用判断。此发现不取消批准的完整复验，也不临时增加GPU计时卡。

## seed1完整生成与对照完成，seed2已进入原生采样

第一个新seed的Native35、原WC父、全部六条完整后缀和五段视频已完成。原case status为SEED_NATIVE_AND_WC_CONTROLS_COMPLETE_SCORING_PENDING，父36更新/72CFG；第二个seed已列入并开始实际Native采样。原两个GPU句柄/source5143d46保持，CPU3225754继续等待完整两seed结束，未评分。未重提交GPU或修改运行源。

标准库CPU只读原件核对三组严格重复、BASE/REFRESH no-op实际状态、全部六后缀与原WC父尾段及终态、Native/WC初始完整指纹均相同；父/OFF1/BASE_first/REFRESH_first编码SHA也完全一致。当前call46原生已D，因此当前增加、严格未来节省和全路径净节省完整调用均为0。这是完整可用的no-op条件与实现对照，不计为新策略成功；原生相对LPIPS仍由整卡后CPU统一93帧验证。

[完整seed1原件与只读核对](../reports/wc_w3_d46_seed1_complete_live_cpu_20261008.json)绑定当前runner压缩原字节及SHA，保留所有动作/计数/诊断wall。当前5新视频，第二seed的结果与整卡终态尚待；最近结算仍18.991453711/24h，第58job在途24是预留非实际花完。

## seed2原生C46已观察到：预登记干预具备适用条件

seed2首条OFF1完整后缀已完成14更新/28调用。call46/CFG1的paid probe原生建议C（native_skip=true、requested=null、actual_action=C），真实完整历史为两CFG各[18,22]，后缀完整数8/7，OFF1诊断wall338.279605秒。因此两预定新seed目前包含一个原生D46 no-op（seed1）和一个原生C46可干预点（seed2），未换seed/位置或强制C制造对照。这个条件意味着本卡能够实际检验新seed上的单点刷新，不意味着已经改善质量或成本。

原source5143d46/runR3和原GPU3224687/3224830保持，CPU3225754等待整卡。第二seed的BASE/REFRESH成对结果、全部严格重复、父编码桥及终点评分仍待；完整两seed原分母继续保留，不追认为跨场景独立CONF，也不启动训练或新的GPU实验。[原生C46原事件/现场](../reports/wc_w3_d46_seed2_original_C46_live_20261008.json)绑定当时runner原字节与SHA。
