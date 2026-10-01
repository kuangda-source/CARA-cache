## 最新接续 — v1.3来源与寿命设计，交叉QKV结果已归档

**执行顺序约束（用户2026-10-02）：当前工作不取消，先按原范围完成并审计，再考虑本轮新增设计。** 保留已冻结运行的配置、source、预算、失败和输出；当前S1结果归档/中间刷新覆盖准备优先，v1.3的寿命与分组卡后置。本次不终止进程、不重置运行或以新候选替代未完成工作。

2026-10-02：读取“调研两个研究方向”最新层级缓存轮次727c7f37。主问题收窄为刷新精度与缓存后续使用长度的联合选择，三动作/训练自由/模式复用本身不称创新。[分组来源与有效期设计](65_WC_HIERARCHICAL_PROVENANCE_LIFETIME_DESIGN.md)新增互补性、dense/同后端full/sparse来源×复用1/2/4步，以及静态分组、age-only、来源/计划寿命消融和动作数量/位置控制。先低侵入S/D，再有信号才两组；三组/模式独立刷新/PSA仅条件扩展。

已完成crossed-qkv-r1/source de6ea8d：72case审计通过；sim0.1/cdf0.98中位操作1.286×、两筛查6/12，layer27四输入均超5%误差；sim0.6/cdf0.9中位1.062×、两筛查3/12。[四组合结果](64_WC_S1_FACTORIAL_RESULTS.md)无统一全输入配置，首尾四CFG调用×三个采样层不能验证中间刷新与全26深层。

下一有序动作：①CPU准备中间刷新/全深层、原输出不变的有界诊断与状态恢复接口；②在具体范围/hash/预算门通过后补覆盖；③H0低侵入与互补性；④H1来源×寿命；⑤机制成立才H2少量分组及公平预算对照。S3按实测边际成本选项，不再作为进入寿命诊断的必做前置；S5保留条件诊断。当前真值只评分，局部D不恢复Native整轨迹。

账本3.9117525685110333/4GPUh、28jobs、余317.690753秒，无inflight；依据已归档fresh审计，不是本次服务器重新准入。新4GPUh/clean50仍未批准。此次仅设计与文档/已完成回执归档，没有新增GPU/runner/runtime/冻结协议修改，不默认人评/训练/付费。

## 以下为历史快照

## 最新验收与下一 — 真实QKV默认策略72case完成，交叉控制准备

S1 real-qkv-r1/sourcecab2b7c，真实12输入×6臂全部finite/3repeat与source/账本/释放审计通过。全mask最大RMSE0.753%；public默认中位1.019×/两筛查1/12，utils默认中位2.139×/两筛查2/12且最大RMSE24.04%，尚无稳定数值—净速度收益。

[结果/补交叉因子控制](63_WC_S1_REAL_QKV_RESULTS_AND_CROSSED_CONTROLS.md)。两默认同时改sim/cdf，下一sim0.1/cdf0.98与sim0.6/cdf0.9，相同12输入/6臂/no-PV，新job重测dense控制，120秒现余额内scope。新policy/cap与预算本地3检查通过，GPU尚未提交。账本3.8958064096647362/4GPUh，余375.096925秒、27jobs、无inflight；无人评/扩额/稀疏视频或方法质量—时间结论。

## 以下为历史快照

## 最新准备 — S1全12真实QKV路由与匹配full控制

冻结两组已有upstream参数（sim0.6/cdf0.98与0.1/0.9），每输入dense/vanilla全mask及两组routed-full/sparse，共72case，1warmup/3repeat；完全无PV，操作测速计完整routing/quant/packing/LUT/validation，额外IO/JIT等计总墙钟。新routing/预算与原no-PV本地7项CPU控制通过，实际GPU尚未提交。

[新有界门](62_WC_S1_REAL_QKV_ROUTING_GATE.md)。唯一180秒scope从余438.007060秒划拨，实际环境CPU/全输入SHA/准入后才launch；原4h/no-inflight，不扩额/人评。保持S0的47.37%瓶颈证据，无稀疏视频或方法质量—时间结论。

## 以下为历史快照

## 最新验收 — WC-S0官方剩余成本与12真实QKV

R3/sourcefb43d93，两轮官方WC完成/视频通过guardrail且SHA一致；72CFG、34full/38skip、trace/latent/sampling/outcome一致。profile去噪141.264395秒，deep self核心66.915474秒/47.369%，flow+warp2.245%，cross核心0.952%；7438原始events和12个实际BF16 QKV `[1,31104,16,128]` 的file/raw bytes/finite/CPU roundtrip已独立核验。

[结果与下一门](61_WC_S0_COST_REAL_QKV_RESULTS.md)。R3计账611.180967秒，两次失败均保留计账；账本3.8783313720900976/4GPUh，余438.007060秒、26jobs、无inflight、PIDs/锁/GPU释放。下一余额内最多180秒真实QKV选择/匹配full-mask/误差与净路由成本；尚未prepare/提交该新job，不重跑旧launch，不扩额/人评。无稀疏视频或新方法质量—时间结果。

## 以下为历史快照

## 最新接续 — WC-S0 R2缓存路径失败已结算，准备R3

R2 actual runtime来源门通过，但Inference初始化因默认HF缓存缺guardrail blocklist/custom退出，无完整pipeline/forward/profile/QKV；125.141735秒失败已计账/原PIDs与锁/GPU释放审计通过。恢复与历史F1/W1完全相同的project/hfhub缓存，新增完整Guardrail1所有Git/LFS bytes核验和实际import checkpoint路径门；不绕过guardrails。

[范围与保留失败](60_WC_S0_PROFILE_REAL_QKV.md)、[R2失败审计](../reports/wc_s0_profile_r2_failure_audit_20261001.json)。余额1049.188027秒，R3新identity按750秒原范围准备；先CPU核验全资产/来源，未R3 GPU/未扩额/无人评。R1/R2 launch不得重跑。

## 以下为历史快照

## 最新接续 — WC-S0 R1导入路径失败已结算，准备R2

R1在模型加载前读取native Cosmos包而无法导入WorldCache；无模型/forward/QKV/profile结果，69.455334秒失败墙钟已计账、退款680.544666秒，原PIDs/global锁/GPU释放审计通过。runner现明确runtime及两个package搜索路径、WC实际origin检查；supervisor复用历史PYTHONPATH并在验证后再次准入。

[诊断与范围](60_WC_S0_PROFILE_REAL_QKV.md)、[失败审计](../reports/wc_s0_profile_r1_failure_audit_20261001.json)。余额1174.329762秒，下一新stage R2先actual CPU import-origin检查，再750秒唯一两阶段任务；不重跑R1或扩额/人评。

## 以下为历史快照

## 最新准备 — WC-S0成本与真实QKV两阶段诊断

已冻结官方WC/首个CAL8场景seed0：先profile各组件，再独立capture调用1/2/71/72×层2/14/27的真实QKV；750秒唯一scope从既有4GPUh余额划拨。观察器/采集/预算本地6项CPU检查通过，未改变sparse/cache/RNG；实际Cosmos环境validate-only/准入与GPU尚待。

[冻结范围](60_WC_S0_PROFILE_REAL_QKV.md)。余额1243.785096秒、不扩额/无人评；下一hash部署与实际CPU复核后单次运行，结果须独立审计。旧kernel launch不可重跑。

## 以下为历史快照

## 最新结果 — WC-S1真实内核已执行，下一真实QKV与WC成本

A6000/kernel-gpu-r1/sourcecb80dd5实际8case完成，GPU墙钟11.726698秒、原PIDs退出/global锁与GPU释放、独立source/8case/raw5repeat审计通过。N31104 dense/full/约50%/约25%同步wall中位数70.35/71.64/39.77/23.65ms；全块RMSE1.32%通过技术筛查，固定稀疏mask约100%/174%误差，不能用作保质方案。

[真实内核结果与决策](59_WC_S1_REAL_KERNEL_RESULTS.md)。当前仍无模型QKV/profile/视频质量—时间收益，下一S0官方WC剩余成本及真实QKV采集；不直接自由三档或四臂。账本精确3.6545041399802236/4GPUh，余1243.785096秒，无inflight；未扩额/无人评。

## 以下为历史快照

## 最新进展 — WC-S1 动态导入通过，180秒内核范围已固定

实际Cosmos Torch下两扩展/no-PV callable动态导入R2通过（CPU3.119766秒，CUDA未初始化）；R1 guard/Dynamo冲突已修复并保留失败。真实GPUrunner和原4GPUh内180秒supervisor已准备，CPU预算门通过；GPU尚未启动。合成QKV的N31104来自真实hidden/checkpoint推导，不能称直接模型QKV或质量结果。

[动态导入、冻结范围与下一步](58_WC_S1_DYNAMIC_IMPORT_AND_KERNEL_GATE.md)。下一hash部署/actual validate-only/fresh GPU准入后唯一有限kernel门；不扩额或默认人评。

## 以下为历史快照

## 最新终态 — WC-S1 两扩展构建与无 PV 接口 CPU 检查

完整上游build-r1/source8047b15实际exit0/CPU648.948283秒，两个sm86扩展完整产出；fresh80 source/两binary SHA/8-file独立package审计通过。原build/entry/wrapper CPU PID均退出、构建锁释放、CUDA未初始化，Cosmos runtime与GPU账本不变。无PV wrapper在本地与实际Cosmos Torch的同3项CPU契约通过；不是GPUkernel或模型parity。

[构建结果、警告与接续](57_WC_S1_ISOLATED_UPSTREAM_BUILD.md)。下一guarded package动态导入/ABI与no-PV binding门、有界GPUrunner准备；实际QKV/profile/误差/净速度仍待。原余额1255.511794秒、新4GPUh提案未批准；不重跑旧build或默认人评，无方法质量—时间收益。

## 以下为历史快照

## 最新准备 — WC-S1 完整源码与有界 CPU 构建

完整 SpargeAttn ae5b629 的80文件已逐Git blob/SHA通过，构建依赖与CUDA12.2实际清单已核对。隔离构建监督/CPU CUDA guard已实现，本地3个负控制通过；尚未提交真实编译。下一固定完整tree部署/服务器CPU控制/唯一900秒upstream build_ext，原Cosmos环境/runtime/账本不改，GPU内核与速度未验收。

[构建准备与接续](57_WC_S1_ISOLATED_UPSTREAM_BUILD.md)。原GPU余额1255.511794秒，新4GPUh未批准；保持S0/S1逐门推进，无人评。

## 以下为历史快照

## 最新 CPU 进展 — WC-S0 源码与实际 checkpoint 接口审计

2026-10-01：实际 Cosmos2B checkpoint 完整 SHA/meta689 读取通过，28 层注意力 336 个权重形状符合 2048/16heads/head128；历史 hidden `[1,24,27,48,2048]` 推导 QKV `[1,31104,16,128]`，尚未直接 QKV hook。六个 runtime 文件本地/服务器 SHA 一致，CPU R1/R2 均退出、CUDA 未初始化、账本未变。

固定 SpargeAttn commit ae5b629 的 11 个源码文件已审计。初版只接 deep self-attention2..27，保留 probe/cross/QKV/RoPE，并展平候选输出。公开 full-mask 默认仍 PV 跳过；S1 改用已确认的 no-PV binding，dense/full-QK-no-PV/sparse-QK-no-PV 分离块稀疏与量化/PV 混杂。默认 nvcc10.1，但另有 CUDA12.2；只满足最低构建要求，未 build/install/kernel/profile。

[完整 S0 CPU 审计与下一步](56_WC_S0_SOURCE_SHAPE_AND_KERNEL_AUDIT.md)。下一非GPU步骤为固定完整源码/隔离环境/有界构建与 wrapper 准备；S0成本 profile/S1实际误差和净速度仍需 GPU 范围决策。没有新方法质量—时间结果；预算仍3.6512467238638138/4GPUh，余1255.511794秒，原新4GPUh未批准。无人工评审或新GPU任务。

## 以下为历史快照

## 最新设计 — WC-S有界计算压缩分支（v1.2）

2026-10-01最新讨论已整合为长程计划v1.2：受质量与行为保持约束的计算压缩。下一非GPU方法准备为WC-S0源码/真实shape/成本方案，之后按依赖做S1真实kernel（dense/full-mask/sparse）→S2四臂固定轨迹→S3单模块替换与便宜刷新；有机制缺口才S4三档/S5稀疏增量。稀疏刷新不能作true dense anchor。

W1保持CAL8机制only/MUSIQ混合/开发VQA无一致收益，暂停scalar/W2复杂化。F1/W1及L0已完成资产不重跑。预算仍3.6512467238638138/4GPUh、余1255.511794秒，原新4GPUh/clean50成本提案待决策；本次只有设计更新，未GPU/未扩额/未训练/未付费/未默认人评。下一窗口按实际profile/kernel成本提议，不机械追加全部卡。

[完整设计与逐门执行卡](55_WC_SPARSE_COMPUTE_COMPRESSION_DESIGN.md)。L0已通过实际93包/guarded native import/meta/tokenizer，真实DiT/T5/VAE load仍待；这是保留的资源门，不是主方法收益。历史运行状态以下文各自终态回执为准，禁止按旧RUNNING快照重提交。

## 以下为历史快照

## 最新CPU终态 — 实际原生导入、meta架构与tokenizer

原生probe-r1/source0da2b73已exit0/CPU20.307796秒，独立终态审计通过；actual Torch/Torch._C/Flash Python与extension origins/SHA、CPPABI false、pinned60完整Wan import（明确仅T5默认设备CPU guard）通过，825meta结构对实际base headers一致、真实tokenizer512与conditional scope签名/恢复通过。原3PIDs退出/环境锁释放，native60/installed93/source与GPU账本未变、CUDA未初始化。没有实际DiT/T5/VAE权重load、forward、完整任务或GPU parity。

[验收与下一CPU门](54_L0_ACTUAL_NATIVE_CPU_IMPORT_ACCEPTANCE.md)。当前无在途CPU/GPU作业，owned16501/16502已在各自终态审计后关闭，Shared FRPC/Clash未改。下一准备actual component CPU load；所有旧下载/resolve/install/fusion/audit/probe launch均不可重跑。不要重复本次审计。

## 以下为历史快照

## 最新安装终态 — 实际93包完整验收

隔离install-r2/source960a57e已exit0/CPU51.886223秒终态；fresh实际93 inventory逐版本符合原图，0缺包/0extra/0wrong。原4+新6 wheel完整SHA不变，4PIDs退出/环境锁释放/source与GPU账本不变，仅owned16502关闭。installed_lock已写入；actual native import/ABI/825meta/tokenizer/任务与GPU尚未验收。

[验收与下一CPU门](53_L0_LOCAL93_INSTALL_ACCEPTANCE.md)。下一新native probe-r1尚未提交；旧install/resolve/download/审计launch均不可重跑。

## 以下为历史快照

## 最新CPU运行 — local93独立安装r2

隔离install-r2/source960a57e已唯一启动，4PIDs 2515483/2515484/2515485/2515492 实际live/环境锁持有，CPU1800秒cap。原4+新6实际payload fresh hash、原解析input与derived93重组成校验已过，UV确认93包/1.15秒，安装仍进行中；尚未安装终态/native import/模型/GPU。新stage8 files固定，source与GPU账本不变。

[运行与接续](52_L0_LOCAL93_ENV_INSTALL_R2_RUN.md)。只观察ignored .sync/observe_l0_env_install_r2.py；旧launch/audit helpers不要重跑，native probe未提交。

## 以下为历史快照

## 最新完整验收 — 六包fresh与实际derived93锁

六个大transitive wheel全部下载并独立fresh审计通过：1781156006字节、CPU2752.631111秒，六包完整官方SHA/实际metadata/exact tag一致，原3PIDs退出/锁释放/source与GPU账本不变，仅owned16501关闭。实际audit数据已离线绑定原93包锁：仅替换六个下载位置，93版本/coverage保留、其余87个block字节不变；新TXT SHA=d4296654b79e26616963df01b4fd15eda29d344bf2d7efb2fcf6840d7ff38abe。这是transport derivation，没有重新resolve或安装/native import/GPU。

[验收与安装重试门](51_L0_ALL6_TRANSITIVE_ACCEPTANCE_AND_LOCAL93_LOCK.md)。下一install-r2尚未launch；旧任务均不要重启。

## 以下为历史快照

## 最新准备 — 原93包local6绑定契约

原93包local6 transport绑定程序及安装校验门已准备，本地/Linux同4契约测试通过（fixture，不是实际六包绑定或安装）。六包range-r1同handle仍运行，已3/6完整官方SHA/meta通过；其余尚待全量审计。新stage安装将fresh全6 bytes并重组成原93版本图；旧安装/source与shared连接不动，无新GPU。

[准备与下一门](50_L0_LOCAL93_BINDING_PREPARATION.md)。同download handle观察；完整6 terminal audit前不能执行真实binding/install-r2。

## 以下为历史快照

## 最新CPU运行 — 六个大依赖可续传获取

六个大transitive wheel分段获取transitive-wheels-r1/sourceffaf53f 已唯一启动，3PIDs 2512783/2512784/2512785 实际live/下载锁持有；服务器6个official PyPI URL均exact206/64KiB前缀通过，CPU3600秒cap。当前cublas410594774字节完整官方SHA与metadata通过，cudnn已持久提交83886080字节/0retry，完整6包/fullSHA/meta尚未完成。旧UV install-r1已终态且新env仍空/source与GPU账本不变，无新GPU workload。

[当前运行卡](49_L0_TRANSITIVE_WHEEL_RANGE_ACQUISITION_RUN.md)。只观察同transitive handle，不重复安装或launch。

## 以下为历史快照

## 最新终态与修复准备 — 安装资源超时

隔离install-r1因下载未完到CPU cap退出：1755.194480秒、UV被TERM，全部4PIDs退出/环境锁释放；fresh93安装清单仍0包，原4 wheel payload hash未变/source与GPU账本不变，仅此次owned forward16500关闭。原93包hash lock保持，6个未完成大包已锁官方PyPI URL/size/SHA（均在原hash lock内），共1781156006字节。分段续传程序及精确vendor tag检查本地/Linux15同范围通过，六个完整payload尚未获取。

[终态与六包获取准备](48_L0_INSTALL_TIMEOUT_AND_TRANSITIVE_RANGE_PREPARATION.md)。旧安装/下载/审计launch均不可重复；下一新transitive CPU获取，未再提交安装或native probe。

## 以下为历史快照

## 最新CPU运行 — 隔离原生环境安装

隔离env-install-r1/sourcee95adcb 已唯一启动，4PIDs 2510384/2510385/2510386/2510389 实际live/环境锁持有；CPU1800秒上限，固定93包hash lock安装到新env，NVIDIA运行库等transitive获取进行中。未完成安装/native import/ABI或模型验收；source与GPU账本不变，无新GPU workload。

[安装运行卡](47_L0_NATIVE_ENV_INSTALLATION_RUN.md)。同handle观察，禁止重复launch。

## 以下为历史快照

## 最新CPU终态 — 完整原生依赖hash lock

完整原生依赖图93包已解析并hash lock验收，CPU r2退出0/4.079835秒、全部4PIDs退出/环境锁释放；新env安装前后仍空/source与GPU账本不变。R1因ANTLR无wheel技术退出，R2仅准许纯Python ANTLR4.9.3 source，Torch/Flash不编译。实际安装/native import/模型与GPU仍待。

[解析与下一安装门](46_L0_NATIVE_ENV_DEPENDENCY_RESOLUTION_RUN.md)。owned forward16500仍由此环境任务持有；下一唯一env-install-r1/CPU1800，不能重跑resolve或wheel获取。

## 以下为历史快照

## 最新CPU运行 — 原生完整依赖解析

隔离env-resolve-r1/source78308f9 已唯一启动，4PIDs 2509814/2509815/2509816/2509822 实际live/环境锁持有；CPU600秒上限，官方PyPI TLS metadata预检通过。四个已审计local wheel是固定输入，完整transitive hash lock尚未完成；新env仍未安装/source与GPU账本不变。

[运行卡](46_L0_NATIVE_ENV_DEPENDENCY_RESOLUTION_RUN.md)。同handle观察，不重复launch。

## 以下为历史快照

## 最新资源终态 — 四个native binary完整通过

四个native binary全部获取并fresh审计通过：997270087字节，CPU1533.184018秒；三PyTorch官方SHA匹配，Flash官方asset ID/name/size/URL和actual local SHA/CRC/metadata通过（官方digest仍UNKNOWN）。全部3PIDs退出/下载锁释放/source与GPU账本不变，仅此次owned forward已关闭。隔离env仍空，未安装/import或新GPU。

[完整验收与下一CPU门](45_L0_NATIVE_BINARY_ACCEPTANCE_AND_CPU_IMPORT_GUARD.md)。下一新owned forward16500/唯一env-resolve-r1，不重复下载。

## 以下为历史快照

## 最新运行 — 四个native binary CPU获取

native-wheels-r1/source e7338fe 已唯一启动，3PIDs 2507524/2507525/2507526 实际live/下载锁持有；四个源exact206/64KiB前缀通过。当前Torch已持久提交 167772160 字节，完整4 wheel/hash尚未完成；CPU3600秒cap/source与GPU账本不变，无安装/import/GPU。

[运行卡](44_L0_NATIVE_WHEEL_ACQUISITION_RUN.md)。同handle观察，旧launch不可重复。

## 以下为历史快照

# Next actions — 输入对照终态，下一预算/范围决定

1. controls-r1/source72c9e24原8/126全有效，repeat0/42变、blank14/42、cyclic14/42；全PIDs退出/锁/GPU释放/模型输入raw/hash/本地重算通过。[结果](30_W1_VQA_INPUT_CONTROLS_RESULTS.md)/[审计](../reports/w1_vqa_controls_r1_audit.json)。只证重复稳定/内容响应，不证明物理准确，不再重复控制或调prompt。
2. 实际累计3.6512467238638138/4GPUh，余1255.511794秒，无在途；不扩额或提交新生成。原VQA6平1misc降、MUSIQ3升4降/robot拒绝/CAL8机制信号保持，无质量—时间收益。
3. [成本与重要决策卡](31_W1_NEXT_WINDOW_COST_AND_DECISION.md)：原8两臂旧诊断3141.247秒，并非clean下界；现余额不足以稳妥完整计时。提议新4GPUh原8×两臂×3repeat clean成本门，或先CPU准备替代资源，待用户选择；不以好子集代替原8/冒充F2或DEV。
4. [计时程序准备](32_W1_CLEAN_TIMING_CPU_PREPARATION.md)已完成：原8/50协议runner实现/本地Linux48 CPU与真实validate-only/旧4h拒绝通过，新代码仅staging、主ledger与runtime未变。若批准新窗口，再记录授权/版本化额度、source同步/hash部署/最终CPU/fresh预算锁和GPU准入后唯一新身份。48计时尝试/2预热/失败/flush都计费，partial不完整结论。未批准则只读/CPU资源工作，不据弱proxy切OMR/W2。
5. 若成本门通过也需更强质量证据/新明确机制，不能仅速度/当前CAL稳定认方法接受；后续调优WC/原生少步曲线、DEV/CONF仍需设计与独立资源。无非必要人评/付费/训练，meaningful代码/回执/docs同步GitHub。

6. [L0部分资源验收](33_L0_WAN_LONGLIVE_OMR_RESOURCE_AUDIT.md)：Wan5B11文件完整hash/两套LoRA header结构与16CPU通过，非完整adapter或真实融合/GPU。下一可独立CPU下载锁定2适配器1.802GiB/逐SHA、真实融合新输出和隔离环境/任务接口验收；OMR公开入口仍BLOCKED。保持主线，不自动转L1/训练/扩额。

7. L0 CPU获取r1因连接中断exit1/1218.181533秒终态，原3PIDs退出/CPU锁释放/账本不变；仅关闭本任务owned临时转发。CFG4文件完整官方hash、真实600tensor finite/300pair alpha-r通过，独立核验PIDs2495417/2495418退出；few-step保留167772160字节（160MiB），非完整payload。两配方分片CPU融合程序已实现，本地/Linux22同范围检查通过，尚未真实Wan5B融合/模型任务load/GPU。下一同固定release/cache/3600秒的新r2续传，不重启旧identity或改共享路线。

8. [真实CFG验收/完整融合准备](34_L0_CPU_FUSION_PREPARATION_AND_CFG_PAYLOAD.md)：two-recipe runner/协议/本地Linux22已齐，full5B fusion尚未执行。r2完整release后先逐全SHA/finite，再新CPU identity/bounded3600/hash-deploy/32GiB+80GiB准入，全825×2融合及原条件权重/序列化检查；后续隔离任务环境/接口。无新GPU或重要预算答案。

9. L0 CPU r2/source965a502已实际启动且3PIDs2496080/2496081/2496082均/proc核实live，独立CPU锁持有、3600秒上限、source/协议hash一致、CUDA空/账本不变。复用CFG全部已验收4文件，few-step由160MiB续到188743680字节（180MiB），仍非完整/hash验收/融合。r1原连接失败及160MiB保留不改。 继续同r2 handles/owned转发至终态；前述r2准备项已实际启动，以最新launch/live为准。

10. L0 r2因第二次HTTP流中断exit1/583.253381秒终态；3PIDs2496080/2496081/2496082已退出/CPU锁释放、原source/协议核验和GPU账本不变，owned r2转发在完整审计后关闭。few-step保留555745280字节（530MiB），CFG4文件继续官方hash PASS。新16MiB range/retry/rollback/fullSHA获取程序和完整融合监督已实现，本地/Linux39同范围CPU通过；还未r3提交/完整5B融合。 [range恢复与接口门](35_L0_RANGE_RECOVERY_AND_INTERFACE_GATE.md)：下一r3小段续传，完整/finite后真实有界全模型融合，再共同native管线任务/noise/条件与单分支验收；不将CPU scheduler或spy计数当GPU。r2旧live已被终态覆盖。

11. L0 CPU range-r3/sourcebd8253d已唯一实际启动，3PIDs2498231/2498232/2498233都/proc verified live，CPU获取锁持有、CUDA空/source协议hash一致/账本未变。官方精确206/64KiB旧prefix边界preflight通过；已完成2个16MiB chunk、重试0次，已fsync字节589299712（562MiB），另有在途文件长度602931200（575MiB）。未完整1289824400/整SHA验收或两模型融合。复用原530MiB，不改r2失败或扩大GPU预算。 当前r3已启动，前述准备项是历史步骤；继续同handles和owned forward，不再跑旧r2观察/settle。

12. [native T2V scope准备](36_L0_NATIVE_CONDITIONAL_CPU_PREPARATION.md)Local/Linux7及真实CPU UniPC fullbody probe通过；guide5 reference bit equal/guide1cond only，明确BF16guide1非stockbitparity。等待fullweights/真实CPU融合，再隔离全包/load/任务/GPU门；不重跑旧GPU控制或自动扩额。

13. r3已审计终态/仅owned forward关闭；同步后新r4补12658832字节，同revision/cache/cap，完整7 SHA/实际1200finite后才真实CPU fusion。

## 最新全部adapter CPU验收

L0 range-r4/source7c0f2ec唯一实际续传成功，exit0/31.271029秒，最后12658832字节一次range完成/0retry。全部7文件官方digest与实际1200张量CPU有限性、300×2目标/rank/alpha及825基座header匹配通过；原3PIDs2502124/2502125/2502126退出/CPU锁释放/source与协议一致/账本不变，审计后仅owned临时转发关闭。真实融合尚未提交，实际模型/GPU parity仍未通过；新4GPUh仍待用户重要预算决定。

14. 实际CPU fusion-r1/sourcec69e492同3handles观察至终态；输入hash/每臂3shard/825tensor两臂完整审计，不能重复launch/改stage。下一独立官方runtime/实际任务接口准备，无新GPU预算授权。

最新完整原生源码/环境准备：官方固定Wan运行源码60文件已独立部署/全Gitblob与SHA匹配；旧参考import观察超时、PID后续消失，结果UNKNOWN。参考环境满足官方requirements版本元数据；新隔离env/full native import尚未通过。带PID/阶段持久回执的CPU runtime probe已准备/仅语法检查，未执行。fusion-r1仍同handles/3600秒CPU cap，CFG-only已有413tensor/首shard验收，尚未全两臂验收。 [准备与边界](39_L0_NATIVE_SOURCE_AND_ENVIRONMENT_PREPARATION.md)。

最新CPU融合进度：fusion-r1/sourcec69e492同3PIDs实际live，CFG-only一臂已全部825张量/3分片完成融合、独立公式、有限性、未目标字节不变与序列化重读验收；完整两臂及末尾原输入hash尚未完成。CPU锁持有/source一致/账本未变，维持3600秒cap，不重复启动。

最新两臂/环境门：真实CPU两臂均已825/3分片内部验收；完整posthash/终态与独立fresh artifact审计仍待。新独立env已创建，实际offline缓存解析缺Torch2.4.1+cu121，未装包。独立CPU终态审计程序已准备/语法检查，待原3PIDs退出/锁释放后唯一timeout900秒执行，不重跑融合/改stage/新GPU。 [准备](40_L0_CPU_FUSION_AUDIT_AND_ENV_CACHE.md)。

最新CPU融合终态：CPU fusion-r1/sourcec69e492已exit0/1960.417015秒终态，peak RSS30.8287GiB；两臂各825tensor/3分片/300目标/525未目标完整，18原输入融合前后官方digest一致，3PIDs退出/CPU锁释放/source与GPU账本不变。完整独立fresh产物审计尚未执行，不能称模型/任务/GPU就绪。

最新独立审计/二进制资源：CPU audit-r1/sourcedbe863c已唯一实际启动，3PIDs2505483/2505484/2505485 live、900秒cap/锁持有/source与GPU账本不变。fresh18输入/CFG-only825tensor与3shard/525untargeted通过，few-step+CFG尚待。官方Torch三wheel SHA与Flash官方asset ID/size已锁，Flash官方digest UNKNOWN；均未下载/安装，实际ABI/fullruntime未通过。 [运行卡](41_L0_FRESH_AUDIT_AND_BINARY_SOURCE_LOCK.md)。

最新CPU完整验收：真实两臂CPU融合与独立fresh audit均终态通过：fusion1960.417015秒/peakRSS30.8287GiB，audit663.896945秒；18原输入融合前后及fresh官方digest一致，6输出shard/1650实际tensor全finite与dtype/shape/字节digest通过，1050未目标weight原字节不变，两臂各300目标实际bytes_changed。所有原fusion/审计6PIDs退出/CPU锁释放/source与GPU账本不变。仍未实际模型/T5/VAE加载或任务/GPU就绪。 [完整卡](42_L0_FULL_CPU_FUSION_ARTIFACT_ACCEPTANCE.md)。

最新native binary获取准备：四个固定native binary获取程序已实现；本地/Linux11同范围CPU检查通过（不是22项独立证据），涵盖range/rollback/完整SHA、错误wheel名称版本平台、Flash断流续传/冻结local SHA/损坏cache拒绝及官方asset身份改变拒绝。完整wheel尚未下载、依赖未安装/native ABI未验收。 [准备卡](43_L0_NATIVE_WHEEL_ACQUISITION_PREPARATION.md)。
