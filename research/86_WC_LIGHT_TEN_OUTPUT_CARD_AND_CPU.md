# 独立十输出轻量卡：组合 CPU 通过，实际部署门待验证

2026-10-03。基于既有自主研究目标和累计12GPUh预算，选定 `WC-LIGHT-OUTPUT-R1-20261003-A` / `wc-light-output-r1`。这是 [84 测量方案](84_WC_VIDEO_GATE_AND_CLEAN_TIMING_NEXT.md)、[85 轻量 CPU 结果](85_WC_LIGHT_PIPELINE_CPU_AND_TRACE_RESULTS.md)之后的独立范围；原104点1800秒和原六输出6000秒单次身份均不复用。[执行依据](../manifests/wc_light_output_r1_execution_20261003.json)记录已有授权的来源，不称为用户本轮另授新权限。

## 输出与次序

共十次完整生成，35请求/36实际UniPC-Karras更新/72CFG、93帧/432×768、seed0、共用显式eval和已固定decoder policy、普通guardrail与writer：

1. common官方WC与dense adapter两输出。**使用轻量入口且每臂真实prepare**；外挂只读诊断验证原九项、五处状态观察和最终pipeline/文件SHA。没有状态恢复或共享prepared replay。这两次wall属于诊断控制，不进入部署速度统计。失败即止，后续八输出不开始。
2. common按 `官方、S、S、官方` 四次完整输出。
3. human_199按 `S、官方、官方、S` 四次完整输出。

两场景各两次官方/两次候选，ABBA/BAAB在场景内交错；全部分母事前保持，缺输出或技术错误不补选、不重提。两个场景都已曝光，只作开发测量，同seed重复不是独立质量样本。人物保真风险不能因为同配置重复成功或耗时减少而被接受。

S继续使用sim0.1/cdf0.98/no-PV，probe2 dense、6/23/27回退，以及既有真实D/近似来源隔离、过去同CFG/window/epoch绑定、warm/reset/nonfinite拒绝。候选使用自己的官方adaptive刷新决策；没有对照未来trace、额外teacher、学习器或训练。

主时间是每次完整原生 `Inference.generate` 的CUDA同步边界wall，包括真实prepare、采样、decode、guardrail和写文件。必要来源签名/账本/核入口在候选wall内；每臂共同的初始RNG/buffer设置与最终文件SHA位于主wall外，但仍计入整卡费用。分段只是未独立同步的host wall，不能给出各阶段CUDA延迟。

模型加载和首次核成本全部计费。D/D先执行，故后八次不是模型冷启动测试；首次真实S的完整pipeline要标记为该卡首次稀疏使用，不能静默删除它或只挑最快重复。保留各次原始wall、次数、顺序、调用数及离散情况，分别报告全部测量和首用/后续的描述性差别。两次重复只支持初步成本诊断，不支持统计泛化。

## 实现与 CPU 证据

[light_output.py](../src/wcomr/light_output.py)把两次真实prepare的D/D观察和八次无诊断观察的轻量测量接起来；观察hooks在D/D退出时关闭，不能带入后续测量。[新runner](../scripts/run_wc_light_output.py)沿用已验证的真实模型构建、资产、包、mode/注意力/WC参数绑定，调用新生产接口。[独立supervisor](../scripts/supervise_wc_light_output.py)保留全局锁、fresh VRAM/compute、唯一目录、预付后实费结算与5970秒child/kill5控制；未selected的config拒绝GPU执行。

[实际组合CPU r1](../reports/wc_light_output_cpu_r1_20261003.json)32.605秒通过四组控制：flow OFF/ON各十生成/十次prepare；D/D decode扰动拒绝且测量零开始；第二场景第二phase decode失败保留首场景四输出、该场景第一phase和十输出分母。D/D九项与最终pipeline、观察hooks清理、参数/mode/buffer和原生计数控制通过。24份payload SHA对应当时源码，CUDA初始化被禁止、预算保持。

[纯CPU scope门](../reports/wc_light_output_scope_cpu_20261003.json)11项通过：十输出/完整成本、改分母、共享prepare、减重复、未来truth、nonfinite/超上限成本，以及旧1800窗口、余额不足/inflight/旧4h账本拒绝。实际部署仍须验证当前配置/源哈希、已有轻量15控制与本组合4控制源一致、实际官方prepare、真实样本metadata、native-meta buffers/mode、source/assets/import/package；准备回执不能替代GPU执行。

CPU采样函数体固定，但net/noise/conditioning/prepare/VAE/writer和S核边界是toy；93×16×16 mock不是视频，2flow×10生成不是实际模型生成。这里没有新增GPU、实际核或端到端速度结果。

## 成本与准入

[冻结配置](../configs/wc_light_output_r1.json)、[完整成本包络](../reports/wc_light_output_r1_cost_20261003.json)：每输出450秒×10，加startup50、模型加载114、首次核/来源150，raw4814秒；20%余量为5776.8秒，再结算30秒，完整5806.8秒。450秒/输出高于此前最大debug配对389.61秒，但只是预测，不是保证。完整十输出不缩成少量视频来适配旧卡。

独立最多一次6000秒全cost/5970秒child，预付1.666667GPUh；当前已用6.733473505896205/12h、37jobs，余5.266526494103795h。新GPU尚未提交，无新增预付。启动前冻结当前source/payload并同步GitHub，实际全部部署门通过后重新核对UUID/sm86/VRAM/compute、无inflight/余额、全局f1锁和磁盘≥15GB。保留其他任务，单昂贵作业。

真实D/D输出等价是入场门；后八输出需普通完整返回、来源/计数/真实核完整，之后独立审计十文件SHA/完整93帧、指标、source/费用/释放。速度结果只来自无诊断观察的八次，不用之前debugwall，失败和启动开销不从总预算删掉。净速度、人物保真、原生完整/少步/调过WC强基线和独立CONF仍须分别验证。本卡不会自动触发第二次提交、训练、复杂H2/RV或新增人评。

## 实际部署门通过，待唯一现场提交

[实际部署回执](../reports/wc_light_output_r1_deployment_20261003.json)：冻结source `7bec5f84ac6eee1289780a574f86972d1d19f3af` 在独立deploy1 stage通过官方prepare/新scope、原生meta mode/buffers、双场景metadata、全部source/assets/import/package门。既有实际轻量15与组合4控制原回执SHA及21/24份payload逐一绑定到当前stage，未冗余重跑；固定五官方文件SHA再次匹配。共7项准备门（scope内部11控制），CUDA未初始化，账本保持，磁盘约564GB、全局锁可获取。当前未GPU/预付；接下来仅fresh UUID/sm86/VRAM/compute/锁/无inflight/余额后唯一提交，原stage/source不改。

## 唯一启动与现场句柄

[启动回执](../reports/wc_light_output_r1_launch_20261003.json)最初state null是监督器资产复核期间；[现场1791041279.33567](../reports/wc_light_output_r1_start_observation_20261003.json)确认supervisor2701874/timeout2701892/runner2701894均存在且命令行匹配唯一stage/run，指定A6000仅runner占用24514MiB。当前INITIALIZING、输出0/10；加载或PID存活不是D/D、视频或性能结果。只跟踪原stage/句柄，不改冻结source/payload或重提。

child起算1791041205.2434986，6000秒最大北京时间2026-10-04 01:06:45.243499（实际child5970秒、kill5）；已结算6.733473505896205/12h、37历史jobs保持，当前38job及6000秒预付后账本8.400140172562871/12h，可用3.599859827437129h，实际费用待终态结算。十输出、原失败历史及先D/D止步保留，结束后独立source/费用/释放/十视频与测量审计。

[现场1791041636.6374164](../reports/wc_light_output_r1_live_observation_20261003.json)：原三个准确命令行句柄仍live、预算预付不变，load95.9155秒；第一官方phase已进入完整生成，日志36/36但尚未普通返回/产物验收，当前0mp4/真实D/D待结果。phase中间计数只在保存回执时刷新，不能把暂存0误判为没有算或据日志当作普通完整返回；不改在跑源码来改善进度显示。

现场1791041804.5606267：第一官方D/D臂普通返回36更新/72CFG/一次真实prepare，非空mp4保存（全卡1/10），第二dense-adapter控制臂已进入生成。第一臂337.6564497174695秒含D/D诊断观察，不能进入八次部署速度统计；D/D九门尚未成对验收，S测量0。原三个准确命令行PID仍live、预付不变。
