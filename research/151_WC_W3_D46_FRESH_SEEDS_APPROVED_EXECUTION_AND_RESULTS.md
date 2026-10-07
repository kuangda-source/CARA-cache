# W3 D46 两个新 seed 完整复验：直接批准与执行

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
