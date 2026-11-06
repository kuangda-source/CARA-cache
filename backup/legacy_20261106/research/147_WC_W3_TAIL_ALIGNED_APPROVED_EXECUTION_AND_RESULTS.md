# W3-B 尾段执行约束对齐 R2：批准、执行与结果

日期：2026-10-07（Asia/Shanghai）。完整R2 GPU与CPU评分均已结束；以下初始/中途检查点保留其历史状态。

## 当前状态

完整卡 `WC-W3-PLACEMENT-TAIL-ALIGNED-R2-20261007-A` / `wc-w3-placement-tail-aligned-r2` 已完成。2条父轨迹、16条完整后缀、10个新视频、每CFG固定配额、全部重复/顺序和历史字节桥通过实际服务器独立验收；10新视频与2个Native参考均完整解码93帧。GPU与两个CPU步骤均exit0，五个原句柄均退出，目标GPU释放为24MiB/无计算进程，共享锁自由。

**Human的46/48交换取得同完整调用配额下的终点保真正信号：LPIPS降低1.4443%，65/93帧更接近匹配Native。其余三对退化，Human61/63退化明显。继续WorldCache/W3，先做一次尾段响应区分；不将当前结果视为稳定跨场景方法、在线路由或部署加速。** 原R1第70调用不可行结果、判据、费用和旧W1/A证据不改。

## 完整终点结果与价值

表中改善为 `(BASE−SWAP)/BASE`，正值表示更接近匹配Native。每行均使用完整93帧CPU FP32/Alex LPIPS；所有四对原分母和负值保留。

| 场景/CFG分支 | 交换调用 | 全轨迹CFG0/CFG1完整配额 | BASE LPIPS | SWAP LPIPS | 相对保真改善 | 改善/退化帧 |
|---|---|---|---:|---:|---:|---:|
| Common/CFG0 | 47/49 | 18/17 | 0.333153 | 0.343595 | −3.1341% | 1/92 |
| Common/CFG1 | 48/50 | 18/17 | 0.333153 | 0.365233 | −9.6292% | 0/93 |
| Human/CFG0 | 61/63 | 20/18 | 0.424745 | 0.668308 | −57.3431% | 0/93 |
| Human/CFG1 | 46/48 | 20/18 | 0.424745 | 0.418611 | **+1.4443%** | **65/28** |

Human46/48说明：相同的各CFG完整计算数量，放在不同位置能够改变终点保真，且该例收益不依赖完整调用次数下降。Human61/63则反证这一个晚位置交换配置的有利性，提示不能只凭“提前刷新”或局部缓存年龄选择位置。其余两个Common退化也保留；1/4正不被改写成全方向成功或失败。

该结果与W3-A的Human单动作、自适应后续LPIPS降低2.81%/全窗口完整调用18→16互补，二者目标不同。R2的双位置联合干预不是单动作收益标签，当前没有训练Head、LoRA或专家。

### 实际验收、成本与原件

- [GPU终态原件捕获](../reports/wc_w3_placement_tail_v2_gpu_terminal_capture_20261007.json)：source仍为e464272，exit0；完整wall **6886.682735秒 = 1.912967426 GPUh**，包含加载、诊断、编码与清理。实际小于2h，原完整规划2.596709750h与获批例外仍保留其事前身份。
- [独立服务器终态审计](../reports/wc_w3_placement_tail_v2_terminal_audit_native_20261007.json)：实际CPU **25.941812秒**、exit0；源、实费/退回预留、资源/锁释放、2父/16后缀/10输出、重复/配额及12份视频全93帧解码通过。
- [完整原始评分](../reports/wc_w3_placement_tail_v2_lpips_score_native_20261007.json) SHA `589511ee59cba7ff0d65d79543ca3aa501135932c7d88986ae4696f3648418e3`；评分步骤实际wall **111.679995秒**、exit0，内部计时105.554621秒，`CUDA_initialized=false`。6个Native-relative损失和4个signed联合诊断完整。
- [CPU终态原件](../reports/wc_w3_placement_tail_v2_cpu_terminal_capture_20261007.json)保留driver/auditor/scorer三个原PID3054488/3065859/3066068的实际退出及日志。[本地独立数据复核](../reports/wc_w3_placement_tail_v2_independent_score_analysis_20261007.json)核对原字节/GZIP SHA、费用公式、全部原始轨迹与signed/逐帧算术；服务器视频路径和解码由上面的实际服务器审计验证，不伪造本地路径。
- 第51次GPU任务结算后累计 **16.269307783/24 GPUh**，剩余 **7.730692217 GPUh**，无inflight。[原始结算账本](../reports/wc_w3_placement_tail_v2_budget_after_native_20261007.json)已回写本库当前budget；旧失败费用不清零。

诊断后缀wall包括恢复、输入/缓存/求解器哈希和记录开销，不是部署速度。首轮BASE/交换约Common271.19/271.64/271.99秒、Human280.61/280.19/281.22秒；全部两次记录在评分原件，不能凭微小差值宣称加速。OFF1的冷启动/编码开销也保留。

### 必要边界与下一步

只有2个已曝光CAL场景、seed0；四交换不是四独立场景，重复一致性不是新增seed，93帧不是93独立成功样本。LPIPS测匹配原生保真，物理/语义/运动质量和稳定端到端优势仍待。当前未形成可部署选择规则，不直接启动4新场景×2seed独立CONF，也不在本批上拟合Head。

当前晚尾段建议与冻结执行不一致，Common两交换均在70、Human61/63在69/70、Human46/48在69。Human正负例都存在差异，不能把“有尾段差异”直接当有害标签。下一[事前区分计划](../plans/WORLD_CACHE_POST_PLACEMENT_WINDOW_20261007.md)仅改变两个Human交换后69/70的后续响应，比较终点与真实新增计算成本；其余执行掩码、输入、求解器/缓存/RNG恢复和71/72原生reset保持。新GPU尚未执行；先完成受影响CPU及完整生产配置，再按≤2h自主执行政策准入，不复跑旧核心或增加人评。

## 批准与执行身份

- 本轮直接“允许”：thread `01a0f1eb-7894-7ed0-a186-d010111e14b1`，turn `01a115a3-fbef-77c1-9d5f-8f817b389fee`，user message `01a115a3-fc36-7350-8aad-bbf2d3eb2ae9`。原件见 [直接答复](../reports/wc_w3_placement_tail_v2_direct_approval_source_20261007.json)，对应此前已提报的新R2整卡例外，不重用已执行R1的批准。
- 完整范围保持：两个已曝光 CAL 场景、seed 0、2 条父轨迹、16 个完整后缀、10 个视频、4 对交换、6 个匹配 Native 的全93帧 LPIPS 损失；Common 配额18/17、Human20/18，各 CFG 分支分别固定。
- 规划名义2.156980347 GPUh、压力2.596709750 GPUh，均为费用代理，未当作硬截止。旧秒数限制取消，累计24 GPUh、全部失败/加载/清理费用和共享资源保护保持。
- 实际代码 source `e4642726754bba73b28c622856bafc3edc33508b`，与通过生产 CPU 的源一致；当前文档提交不替代实际源码身份。
- 执行目录 `.sync/wc-w3-placement-tail-approved-r1-20261007`，GPU UUID `GPU-cebf7119-cf03-23b9-e192-cd196332b704`。只新增直接授权并替换执行配置，保留通过 CPU 的源；原核心模型 fixture 和生产合同测试不重复。
- [执行配置](../configs/wc_w3_placement_tail_v2_approved_r1_20261007.json)及[文件/批准绑定](../manifests/wc_w3_placement_tail_v2_approved_r1_20261007.json)覆盖169份文件。原生产CPU原件SHA `1892b772325409a72ab5752202b89f82ee41e6b3b5d77f792f3582dbb2033567` 保持。

## 实际验证与启动

执行配置实际服务器 CPU 准入验证用时 **12.0568797588 秒**，exit 0，新增授权、原生产CPU、168份原源及9份上游源的闭包通过，账本未变。原件见 [服务器回执](../reports/wc_w3_placement_tail_v2_selected_preflight_native_20261007.json)，SHA `2ab6fa10f496be2683fe52189f80946e61a1daf128069b90961e8858df5e5475`；独立核对见 [审计](../reports/wc_w3_placement_tail_v2_selected_preflight_audit_20261007.json)。这仍属于 CPU 准入，不是视频方法收益。

[唯一启动记录](../reports/wc_w3_placement_tail_v2_launch_20261007.json)记录 supervisor **3040329**。现场读取确认该句柄及 runner **3040347** 均存活，cmdline 的 stage/run/source 与获批卡一致。启动时目标GPU24MiB、无计算应用；随后原 runner 正在初始化，尚无新视频。后续只跟踪这两个原进程，不因观察超时重启或修改在跑源码。

首次GPU现场确认见 [原运行观测](../reports/wc_w3_placement_tail_v2_initial_live_20261007.json)：模型加载 **86.6626909915 秒**，`CUDA_initialized=true`，实际网络为 `MinimalV1LVGDiT`，目标GPU计算PID **3040347**、显存24450MiB，与原runner一致；Common父轨迹已进入STARTED。尚无完整后缀、新视频或终点收益，这不是科学验收。

启动前实际已结算 **14.3563403569/24 GPUh**、50 jobs；新任务为第51次。服务器为保护累计预算先预留全部剩余 **9.6436596431 GPUh**，`used_gpu_hours=24` 的在途记录表示预留，并非实际已花完；结束按完整实际wall结算并退回差额。CPU评分在GPU释放后执行。

## 当前实验所回答的问题

### Common整场完成检查点

[原件捕获与冻结源独立验收](../reports/wc_w3_placement_tail_v2_common_complete_capture_20261007.json)覆盖Common完整36更新/72调用父轨迹、8条各14更新/28调用后缀及5份接受的视频。OFF、BASE、SWAP0和SWAP1四组重复均在8项原始字段上相同；OFF/BASE与父轨迹完整续接一致，各自父状态恢复通过，实际动作与登记掩码相符，每CFG全程完整调用保持18/17。父视频、OFF1和BASE1与历史官方WorldCache视频字节相同，另外两个交换视频的大小和SHA已核对。四条交换后缀均记录第70调用的原生建议与冻结执行差异，两个固定BASE没有该差异。

此检查点属于真实整场可行性和对照通过，范围仍为原2父/16后缀/10视频/4交换整卡；Human及独立终态验收和终点损失未完成，不将Common两对可执行交换记作两对已确认质量收益。

### Human首个61/63交换检查点

[原件捕获与检查](../reports/wc_w3_placement_tail_v2_human_first_swap_capture_20261007.json)确认四条完成后缀各14更新/28调用、父状态恢复通过、每CFG全程配额20/18。OFF1/OFF2八项原始字段相同，BASE1与OFF1七项相同；前两个接受视频与历史官方WC的SHA `4d0f0549dbabf04e7f217037c40f6a30f41cb240289162d6fb0fbec2dde982fb` 和1100497 bytes相同。交换输入签名到首个干预61调用相同，深层实际动作仅61/63改变，与冻结掩码一致；交换视频2107088 bytes、SHA `742771d11eecb8b32c0728d20d9ef5adcc5592c5e605459effdb9437029a3574` 已接受和核对。文件大小差异保留，不能据此判断质量、保真或运动收益。

该交换在61调用执行D、63执行C，两处均有已支付probe、各自CFG缓存年龄1、未读取当前深层真值；69/70调用均记录原生建议D与冻结执行C的差异，对应缓存年龄4/3，70的原生cycle reset保留。这是同配额下真实干预可执行的证据；整场重复、第二对交换、Human父轨迹及整卡终点验收仍待，不授予质量收益或RV训练标签。

### Common首个原策略重放检查点

[实际原件捕获](../reports/wc_w3_placement_tail_v2_first_off_capture_20261007.json)及保留的runner/supervisor原字节压缩快照确认：父状态22更新/44调用；OFF1完整14更新/28调用，父状态恢复通过，全程CFG完整配额18/17。输出经原管线接受，531916 bytes、SHA `fa7f466534e7e7984136dfaa9fb47794dedf0c81444229527b9722142715c379`，与已登记历史官方WorldCache视频字节相同。当前原句柄仍存活，正在OFF2；这一检查点是实际恢复/编码一致性证据，完整科学交换仍为0，不是新方法收益。

### 首个真实47/49交换通过原失败位置

[第二次原件捕获与独立检查](../reports/wc_w3_placement_tail_v2_first_swap_capture_20261007.json)确认：OFF1/OFF2八项、BASE1/OFF1七项输入/输出/深层覆盖/缓存/求解器轨迹及终态信息相同。四条完成续接均为14更新/28调用、父状态恢复通过、全程CFG配额18/17；首个交换实际掩码与冻结计划相同，只有47/49改变。OFF1、BASE1及SWAP0_first三个输出经原管线接受并核对SHA；前两个与历史官方WC字节一致。

第70调用（CFG1、solver step35）保存的实际事件为：原生建议D、计划和实际执行C、已支付probe、自己的CFG缓存年龄3；输入漂移0.015197754、probe漂移0.088378906、动态阈值0.34375、累计量0.36328125。原生cycle reset保留。尾段建议不一致列表只有 `[70]`，与前次失败机制相符，但当前合法缓存和实际配额约束允许完成分支。这是新尾段约束的真实可行性证据；第二次相同交换及全部整卡条件尚未验收，不能据此授予整卡通过、生成单步RV标签或宣称质量改善。

额外[跨运行签名分析](../reports/wc_w3_placement_tail_v2_cross_run_input_signature_analysis_20261007.json)属于探索性实现核对：R1已完成的45–69输出、深层覆盖、缓存及12次求解器更新与当前首个交换相同；原始全输入签名不完全相同，26条差异均仅为 `kwargs.gt_frames`。与实时验收SHA一致的MinimalV1源码丢弃额外kwargs，WorldCache mini-forward只读取额外的`timestep_scale`，不读取此`gt_frames`。其余输入签名字段相同。原签名差异和原件继续保留，当前R2内部的OFF重复/BASE完整签名判据不修改；这一观察不增加或替代科学验收条件。

R2 只改变原R1的尾段附加条件：69/70保留冻结的实际动作，记录原生建议与计划的差异；不再要求干预后的原生建议也相同。前缀、原生初始化/reset、71/72完整计算、缓存合法性、自己的CFG历史、有限性、年龄、不可变计划、全部重复对照和配额仍约束执行。

完整调用次数相同并不代表实际时间相同；本批为离线固定动作的位置干预，不能宣称形成了在线路由或单步刷新收益训练标签。通过CPU或进程健康也不证明真实四对交换可行。每对交换的正、负和不可行结果均按原分母保存，不补换场景/seed，也不缩减对照绕过2h门槛。

## 已完成的自动接续与原验收顺序

已部署唯一[CPU接续启动回执](../reports/wc_w3_placement_tail_v2_postrun_cpu_launch_20261007.json)，独立目录 `.sync/wc-w3-placement-tail-v2-postrun-cpu-r1-20261007`、PID **3054488**。现场确认原字节SHA与[接续脚本](../reports/wc_w3_placement_tail_v2_postrun_cpu_driver_20261007.py)相同、进程存活、处于等待原GPU终态；没有启动新GPU、终态验收或评分。它只跟踪原3040329/3040347，成功退出且原句柄消失后，依次执行原stage中已通过CPU验证的终态审计和全93帧评分；固定源SHA、原件身份与完整分母保持。任何非零终态保留回执和日志，不自动重启GPU或重试评分。接续部署与等待不计为科学通过。

上述接续现已完成，实际driver与两个CPU进程均exit0；原顺序为：原进程终态/实费/资源释放与源SHA→2父/16后缀/10输出/全部原始重复与配额→6全93帧损失/4signed诊断。原等待回执是历史检查点，完整终态与评分以本报告前述原件为准。下一低成本区分先登记并验证受影响代码，不自动加入训练、稀疏扩大搜索或人工评审。
