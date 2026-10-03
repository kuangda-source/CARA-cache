# 完整输出首卡：先官方/D 等价，再两个 WC/S 闭环配对

2026-10-03。独立 card `WC-FULL-OUTPUT-R1-20261003-A`，唯一 run `wc-full-output-r1`。依据累计12GPUh授权与持续自主实验 goal 选定，不复用已消耗的104点/H0/H1单次窗口。承接[82 CPU接线](82_WC_COMPLETE_SAMPLING_AND_REFRESH_CPU.md)。本卡已唯一执行并完成全部终态审计，实计2442.346秒；下方冻结范围与准备/在跑条目保留历史身份，当前结论见末尾终态章节。

## 冻结范围与顺序

1. `common_sense_6487f37f-ef57-49ca-afdc-d898922b5191` 做完整 D/D 控制：官方无刷新适配器 baseline，随后安装 dense-only 来源适配器并在13/21/33/35/36进程内恢复。严格九项原生状态/输入/输出/trace/grid/condition门和最终sampler/decode/guardrail/write文件/RNG相等后才能进入S。
2. common和`human_199`各做官方WC、WC+S两个完整路径，seed0，共四输出。每对共享一次官方prepared batch与其RNG转移；D/D控制与随后common配对重新准备输入，因此前一个控制视频不复用为后一个对照。共六phase/六输出的计划分母保持，不替换失败样本或在该卡内重提。
3. Cosmos-Predict2.5-2B、原setup/输入、93帧/432×768、guidance7、35请求/36实际UniPC更新/72CFG、原WC horizon70保持。call70清空；最后两call计数0/1完整暖启动。明确shared eval和decoder_policy(True)共同使用，guardrail完整保留。两场景已曝光，只作开发诊断。
4. 只有官方已经决定刷新、paid probe、retention阶段、同CFG两次过去真D时允许S；probe2以及层6/23/27保持D，deep其余self-attention用现有sm86 routed/no-PV sim0.1/cdf0.98。MLP/cross/QKV/RoPE/head、Gamma/flow/OSI/官方判据保持。真实QKV为B1/N31104/H16/D128/BF16。S产物只进入标记为approximate的native forecast window，不能进入true-dense历史；绝对call/epoch/request/model/CFG/condition/group隔离。

原生九門只比较原来模型/求解器/RNG以及新增buffer/mode盘点；额外来源sidecar的五处签名单独存档，避免官方路径天然没有sidecar导致伪等价失败。恢复仍校验完整native+sidecar，不能遗漏来源状态。D/S记录真实改变的latent、输出、官方自适应trace、来源事件与kernel选择比例；不要求D/S哈希相等，不读取dense teacher或错误决定动作，不固定baseline刷新位置。

## CPU、实际加载与拒绝协议

先在实际Torch2.7.1+cu128中禁止CUDA，验证完整D/D、D/S恢复/来源与失败分母，新增同一生产函数的六输出组合（flow OFF/ON）及候选解码失败，另测固定scope/成本/预算拒绝控制。真实官方prepare/metadata、source/import/资产、现有package八文件SHA和meta原网络1173模块/shared eval/buffer inventory随后再验。stand-in 不代表CUDA/权重/VAE/视频；前一轮r5 source不能接受本轮修改。

每个phase必须普通返回并产生非空预期mp4。text/video guardrail拒绝不保存输出，不绕过；首个技术异常或缺少预期输出停止本卡，已有phase和六输出计划分母保留，未执行者记为未执行。DD不通过则不进入任何S，不自动第二卡。GPU中记录实际parameter对象/版本、真实named buffers/modes、hook和forward清理；不是独立序列化的整管线重启。

## 成本和准入

[完整成本包络](../reports/wc_full_output_r1_cost_20261003.json)：六次36更新各18秒规划、六套decode/guardrail/write各75秒、加载114秒、startup50秒、首次kernel/额外来源维护150秒，raw4752秒；20%余量为5702.4秒，另结算30秒，共5732.4秒。它是保守预测，不是耗时或显存保证；完整六输出不能塞回旧1800秒。最多一次6000秒全cost、5970秒child、kill-after5秒，累计12GPUh账本预留后按实际全wall（含失败/释放/flush）结算。

当前已用6.055044055960606/12h、36jobs，余5.944955944039394h；最大预付1.666667h后仍有余额。提交前须冻结source/payload并同步GitHub，实际全CPU/source/assets/import/package通过；重新核对指定sm86 GPU的VRAM/compute、全局f1锁、无inflight、磁盘≥15GB与账本余额。保持单昂贵任务，不停止他人进程。

此处逐步hash、checkpoint深拷贝、condition/finite/路由同步与prepared replay均影响wall及两臂工作量。全wall计费，但不作净E2E加速比较。若产物和闭环成立，随后再单独做真实两臂完整准备、冷/热口径/顺序/重复明确的轻量时间卡；不能拿当前debug两phase wall相除声称方法更快。

## 完成后的自动证据

先核对六文件路径/原件SHA、全93帧decode、432×768/fps16/finite/帧完整性、source、九门和provenance。D/S需要实际S调用、fallback无S、同CFG过去来源、call70来源失效、缓存命中使用标记近似等证据；仅加载或exit0不算闭环通过。

再报告每对RGB MSE/PSNR/SSIM、首末时间段保真、逐帧差分的运动能量/时序差分及相对变化。提前明确这些是描述性保真与运动代理，无语义/物理接受阈值；不将低RGB误差、像素运动或视频更静止称为质量提升。结构门失败不丢分母。当前不引入人评/付费评分/训练，也不把两个开发场景当CONF；方法接受仍缺调优WC、少步Native与独立数据的公平曲线。

## 实现阶段CPU记录

[初步实际CPU](../reports/wc_full_output_cpu_r1_20261003.json)229.492秒通过。生产函数原生50组件与sidecar五个checkpoint分开；无adapter→dense adapter严格九门/最终pipeline成立，flow OFF/ON各六phase432CFG/两个候选配对通过，候选decode失败保留DD及六输出分母。完整服务器部署阶段需将最终config/payload/资产/import绑定到新冻结source后再验，当前记录不是GPU准入。

实际部署准备r1/source34f2d86在CPU加载test_prepared_input时缺少打包依赖mid_parity_scope，未进入控制/模型/GPU。原stage与[失败回执](../reports/wc_full_output_r1_deployment_failure_20261003.json)保留；仅补齐纯Python依赖，在新deploy2 stage重新冻结验证。此为准备失败，非稀疏方法或视频结果；唯一GPU run尚未提交。

## 实际部署门终态

[deploy2回执](../reports/wc_full_output_r1_deployment_20261003.json)绑定冻结source`b3ed6b084b5e7bad5a242bd9a934a0d502e1ef6c`：完整CPU11/19/3、官方prepare与metadata、原网络meta/shared-eval/buffer inventory以及全部source/assets/import/package通过，无CUDA/权重模型执行，账本未变，现场全局锁可用、数据盘564GB余量。原缺依赖准备失败保留，唯一GPU run尚未提交；提交仍需再次现场准入。

S使用现有QK量化/选择与稀疏执行，S−D包括backend量化和稀疏效应；本视频卡不是纯稀疏因果分解。此前matched-full局部对照保留，不据该卡独占归因。

## 唯一实际启动与首视频现场

[启动原回执](../reports/wc_full_output_r1_launch_20261003.json)为dispatch短快照，当时 supervisor_state未写；[后续现场](../reports/wc_full_output_r1_live_observation_20261003.json)1791034388.669872确认原三PID2687791/2687807/2687809和指定GPU运行，baseline已完整36/72普通返回并写首个mp4，dense adapter控制在跑，尚无S结果。不可据launch空state重启，也不可把首个对照视频当成D/D通过。

实际全cost6000预付、child起算1791033603.3447514/最大北京时间23:00:03.344751；已结算6.055044055960606保持，含预留7.7217107226272725/12h、37jobs。仅跟踪原句柄，结束后按实际wall结算并独立核对全六输出/来源/视频/费用/释放。当前未声称质量或clean E2E收益。

## D/D独立原件门与自动指标CPU控制

[独立D/D审计](../reports/wc_full_output_r1_dd_audit_20261003.json)重算九项native与五项pipeline、prepared对应及全部来源事件；两个完整输出SHA均fa7f466534e7e7984136dfaa9fb47794dedf0c81444229527b9722142715c379，均531916bytes、768×432/16fps/93完整解码通过。[自动指标CPU控制](../reports/wc_full_output_r1_video_analysis_cpu_control_20261003.json)对真实D/D得到RGB MSE0/luma SSIM1/temporal差0/motion比1，合成运动vs静止候选、缺帧、多帧、结构门未过拒绝五控制通过。脚本在独立analysis目录，不改在跑冻结stage；所有CPU工作不新增GPUjob费用。

现场1791034920.0072188已有3/6mp4，第三是common配对官方WC，common S在生成；完整候选/六输出/费用释放仍待终态，不能据前三视频声称质量或净E2E。预登记编码RGB差/SSIM与帧差motion/temporal均为描述性代理，不是语义/物理接受门。

## 首个完整WC/S配对独立审计（整卡未终态）

[首配对回执](../reports/wc_full_output_r1_first_pair_cpu_20261003.json)：common两路径完整36/72与35次deep；S19次CFG/437算子，后续29次cache读取S来源，选择比例均值0.75306，来源/回退/重置与93完整解码通过。编码视频relative-WC PSNR24.9893dB、luma SSIM0.90118、motion帧差比0.98596、temporal差MSE0.00155664；不构成语义/物理接受或独立确认。

官方debug359.8905秒、S389.6099秒；不同调试/restore/ledger/prepare开销，不报净E2E加速。第二场景仍按原卡继续，4/6视频和6分母保持，等待终态完整source/assets/cost/release/两配对自动审计；不追加第二GPU卡。

## 六输出终态与当前研究结论

[完整摘要](../reports/wc_full_output_r1_summary_20261003.json)、[来源/费用/释放](../reports/wc_full_output_r1_terminal_audit_20261003.json)、[六视频独立审计](../reports/wc_full_output_r1_artifact_audit_20261003.json)、[自动视频指标](../reports/wc_full_output_r1_video_metrics_20261003.json)、[完整原回执gzip](../reports/wc_full_output_r1_runner_20261003.json.gz)。原件gzip解压SHA与远端原receipt SHA一致；原影片路径、大小和SHA均在六视频审计中，影片/权重/张量不入Git。

唯一run退出0，六phase各36更新/72CFG/93帧普通返回；严格D/D九门/五处恢复/最终pipeline和全部source/assets/import/package/来源/成本/释放通过。两个曝光CAL各19次S CFG、437个真实稀疏注意力算子、29次cache读取近似来源，warm/回退/call70重置/两尾部dense正确。这证明完整部署接线，不能直接证明质量或收益。

| 场景 | relative-WC PSNR dB | luma SSIM | 帧差运动量比 | deep调用 WC/S | debug wall WC/S 秒 |
|---|---:|---:|---:|---:|---:|
| common | 24.9893 | 0.90118 | 0.98596 | 35 / 35 | 359.8905 / 389.6099 |
| human_199 | 17.4794 | 0.70541 | 0.95216 | 38 / 35 | 381.7509 / 386.8368 |

人物差异明显更大，同时9次full/cache决策改变。两场景第一输出SHA分歧均call23，人物首次schedule分歧call46；这些不是因果归因。视频帧分段不能当去噪阶段，运动量比不能证明物理或语义保持；相对WC的代理不是原生full质量，曝光CAL不是CONF。该真实S路径同时改变backend和QK量化，不能归因于纯稀疏性。debug wall含恢复/ledger/hash/prepare差异，不能报净E2E加速或等成本质量前沿。

实际全wall2442.346019768156秒=0.678429450GPUh，累计6.733473505896205/12GPUh、37jobs，余5.266526494103795h；6000预付已结算，无inflight，原三PID/f1锁/GPU释放，24MiB/noapps，1144次monitor峰值26966MiB。本卡单次身份消耗，不自动重提或下一GPU卡。

继续WorldCache，但暂不将当前配置提升为质量保持方法，不扩样、叠学习器或训练。下一先按[84 CPU与测量方案](84_WC_VIDEO_GATE_AND_CLEAN_TIMING_NEXT.md)核查现有轨迹/成本并建立轻量路径，将人物保真与adaptive schedule反馈具体化；新的完整比较须另定质量/成本/范围与实际门，非必要不新增人评。goal尚未完成，缺少净部署收益、强基线和独立确认。
