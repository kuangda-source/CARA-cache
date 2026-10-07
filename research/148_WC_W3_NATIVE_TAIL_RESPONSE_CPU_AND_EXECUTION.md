# WC-W3 Native Tail Response：受影响CPU验证与完整执行

更新于2026-10-07。**继续WorldCache/W3。上一R2已有一对固定配额位置交换的终点保真正结果；本轮已完成新接口和实际生产CPU验证，唯一GPU卡在跑，新尾部响应的科学结果仍待。**

## 发现与本轮要区分的问题

[147完整R2结果](147_WC_W3_TAIL_ALIGNED_APPROVED_EXECUTION_AND_RESULTS.md)保留完整2父/16后缀/10视频/四交换。Human46/48在全程CFG完整调用20/18下，LPIPS由0.424745降至0.418611，改善1.4443%，65/93帧改善；Common47/49、48/50和Human61/63分别退化3.1341%、9.6292%、57.3431%。一正三负说明刷新位置确有条件化价值，不能据此宣称普适刷新规则或否定W3。

Human61/63在晚期69/70的原生建议与固定动作均不一致，而较好的46/48只在69出现不一致。这是观测信号，尚不能把61/63退化唯一归因于尾部固定。新假设H-T35已在结果曝光后、下一实验前登记于[v5.2安排](../plans/WORLD_CACHE_POST_PLACEMENT_WINDOW_20261007.md)和[原始登记](../manifests/wc_w3_native_tail_response_r1_preregistration_20261007.json)。旧R2、R1失败、W1混合结果和W3-A自适应总效果均保留。

本轮只问：**在相同已登记联合交换之后，允许调用69/70依当前自身状态响应原生WorldCache建议，相对继续固定掩码，会怎样改变终点保真与实际计算需求？**

## 完整范围与比较口径

卡WC-W3-NATIVE-TAIL-RESPONSE-R1-20261007-A；run `wc-w3-native-tail-response-r1`。仅Human199/seed0，Cosmos-Predict2.5-2B，768×432、93帧、16fps，guidance7，35请求/UniPC-Karras实际36更新、72次CFG，dense/eager、原WorldCache近似器。

完整范围为1父、10条完整后缀、6个新视频、2对尾部比较。顺序：OFF1、OFF2、FIXED46_first、TAIL46_first、FIXED61_first、TAIL61_first、TAIL61_second、FIXED61_second、TAIL46_second、FIXED46_second。父、OFF1及四条first均走原decode/guardrail/write；两种交换和两种模式各保留两重复，不缩拆对照。

FIXED保留R2全掩码及20/18独立CFG配额。TAIL仅69/70采用当前已付probe的原生建议，完整数允许改变并计费。1–68动作及71/72初始化/reset完整动作不变，无配额修复、额外教师、回退改动作或标签筛选。FIXED/TAIL在call69之前额外记录完整latent/cache/RNG/solver/buffers/modes状态及自身CFG历史并验证一致。

父/OFF须与历史官方WC编码字节相同；两个FIXED须与R2对应视频编码字节相同。独立终态审计会检查6新+4历史视频全93帧解码、轨迹/重复/状态恢复/原始资源与费用。旧BASE和两个FIXED损失只在候选/Native SHA和完整LPIPS协议一致时复用，另外只对两个TAIL计算全93帧新损失，共五损失、两个有符号质量效应与成本效应。负值、失败、拒绝均保留完整分母。

这属于后续策略响应的总效果比较，允许成本变化；不是第二个固定预算实验、单动作RV训练标签、独立CONF、已部署在线路由、物理质量接受或干净端到端速度结论。

## 实际CPU与源身份

| 步骤 | 实际证据 | 状态 |
|---|---|---|
| 新受影响完整核心 | dc613373；服务器driver167.750620秒、夹具163.754452秒；3个完整CPU父/30后缀/18 mock输出，8次明确尾部动作变化、39破坏拒绝、3预期故障 | exit0；CUDA未初始化，GPU提交0 |
| 独立原件审计 | 六组尝试完整保存，三成功组逐轨迹重算；非法尾部历史/模式篡改/写出失败保持，恢复与失败分母完整；源/上游/预算不变 | 通过；mock不是视频 |
| 实际新生产CPU | source9c321b5658a28502937ed28e1526ad067de48b16；192份闭包；四步draft/contract/validate/import共58.864380秒；16合同/计费/旧损失兼容拒绝，有符号正负及额外调用成本CPU控制 | 四步exit0；实际资产/导入来源通过，无CUDA/权重 |
| selected实际检查 | 同一通过生产源，仅选择配置与实际CPU证明；12.454930秒 | exit0；原CPU与源不重跑 |

[核心实际回执](../reports/wc_w3_native_tail_response_core_cpu_r1_native_20261007.json)、[原件独立审计](../reports/wc_w3_native_tail_response_core_cpu_r1_audit_20261007.json)、[生产实际回执](../reports/wc_w3_native_tail_response_production_cpu_r1_native_20261007.json)、[生产审计](../reports/wc_w3_native_tail_response_production_cpu_r1_audit_20261007.json)。所有旧CPU夹具、LPIPS资源审计和旧视频评分均复用既有证明，不重复运行。

CPU核心原件SHA1dc459626747042dc6ce9cb42fc4a8dd3bfba8c6389631dbf6458deaa0dc471e；生产原件SHA26447e46eb6339d63e9ccd7f2a970726bbcd40ddb9ea4671ffec7e809a729ba2；selected原件SHA22cb12698f99a21464268c394584d653c26390cc124e707ce9de7b239c7ce063。旧代码、旧stage及预登记均未修改；CPU通过不等于真实GPU可行或新科学收益。

准备过程有两次额外本地核查把当前检出误当成冻结旧stage，以及一次本地合同调用未提供stage别名路径，均在server任务外停止。改用冻结服务器stage与独立本地别名后通过；这些额外调用不追认为通过、不改变旧科学或费用。实际新核心/生产/selected所需步骤均exit0。

## 费用、权限与唯一执行

本轮完整规划由R2实际Human父/八控制费用加两完整后缀、一编码、四TAIL各一整条最慢旧后缀的额外计算预留、加载/其他费用及20%余量推导。名义5480.776404秒=1.522437890GPUh，规划6606.931685秒=1.835258801GPUh；属于代理估计，非硬时限或保证上界。新增pre69状态签名/复制计入实际wall；成本预留与余量保持，最终按完整加载/失败/清理实费结算。

依用户直接执行约定：已有设计内完整≤2GPUh自主准入，>2才询问具体整卡例外；累计24h保持，旧秒数截止不恢复，不缩拆对照。新卡不需要复用已消耗R2例外。

现场启动前目标A6000为24MiB/noapps，f1共享锁自由、磁盘/根预算/无inflight/source/配置均通过。唯一supervisor3089695、runner3089728于1791374937/1791374950开始；source9c321b5、独立stage `.sync/wc-w3-native-tail-response-selected-r1-20261007`。现场cmdline和目标GPU上的3089728已核实，另一GPU342MiB未使用。起始检查为INITIALIZING、0视频，随后进展以实际观察回执为准，不能据live进程报收益。

上一已实计为16.269307783/24GPUh、51jobs，余额7.730692217h。服务器本次第52job暂记24h是预留剩余余额，带 `wc_w3_native_tail_response_inflight`，**不是已花完24h**。仓库根预算保留最近已结算原字节，另存本次现场预留回执；结束退回未花预留，再按服务器实际账本更新根预算。

独立CPU后处理driver3090203已绑定本次两个原GPU句柄、source和审核/评分文件SHA，只等待成功退出与释放后执行终态审计和两个新全帧评分。等待状态不等于已审计/评分，失败保留原件且不自动重试GPU。[提交回执](../reports/wc_w3_native_tail_response_launch_20261007.json)、[后处理提交](../reports/wc_w3_native_tail_response_postrun_cpu_launch_20261007.json)。

当前goal active；只跟踪该原run，不重复提交或修改在跑代码。下一完成全范围、实际费用/释放、六新视频与历史字节桥、五终点损失/两有符号质量及成本判读。重大方向或训练另讨论；本轮无Head/LoRA/专家、稀疏搜索、独立CONF或人评。

## 启动后的实际进展检查

现场1791375220：原supervisor3089695和runner3089728仍是同一stage/source/cmdline，目标GPU只有runner3089728，另一GPU342MiB不变。真实模型加载88.019036秒完成，CUDA已初始化；日志通过prompt guardrail并进入Human原生父采样，已记录4/36更新。runner JSON尚保留请求起点计数，不能把该保存检查点当成实时逐步计数；完整输出、10后缀、尾部响应和LPIPS结果仍未完成。独立CPU driver3090203的同SHA/绑定句柄现场存活，状态WAITING_ORIGINAL_GPU_TERMINAL_NOT_CPU_AUDIT_OR_SCORE，未开始终态审计/评分。[现场观察](../reports/wc_w3_native_tail_response_start_observation_20261007.json)与[服务器预留原账本](../reports/wc_w3_native_tail_response_budget_inflight_native_20261007.json)已保存。

## OFF严格重放与首个固定分支历史桥

现场1791376652，原supervisor3089695/runner3089728及CPU等待driver3090203存活。两个OFF均完成剩余14更新/28 CFG，完整调用20/18，父状态均恢复。十一类记录逐项严格一致：输入、输出、deep、缓存bank、求解器输出、call69前1216状态组件及自身CFG历史、最终latent、动作报告、终态组件和终态SHA。首次OFF后缀337.269208秒，第二次284.496714秒；这是重复的实际wall记录，不能选较快一次宣称方法加速。

OFF1经原decode/guardrail/write接受，1100497字节/SHA4d0f0549…982fb与历史官方WC完全一致。FIXED46_first已完成和接受，1060326字节/SHAa9423dc7…e9366与登记R2 CFG1视频一致，完整调用20/18；已进入TAIL46_first。对应[OFF严格重放原件](../reports/wc_w3_native_tail_response_off_replay_checkpoint_native_20261007.json.gz)、[重放审计](../reports/wc_w3_native_tail_response_off_replay_audit_20261007.json)和[固定视频桥](../reports/wc_w3_native_tail_response_first_fixed46_byte_bridge_20261007.json)。全父、其余分支及重复、尾部效应、实费和终态评分仍待；本节不是新方法结果。

### 附加跨批次原始字段检查的边界

[首OFF与R2逐字段核查](../reports/wc_w3_native_tail_response_first_off_prior_R2_raw_audit_20261007.json)保留两个未相等项：28次输入只有名为gt_frames的kwarg摘要变化；终态组件只有solver._internal_dict摘要变化。输出、deep、缓存bank、全部求解器输出、最终latent、实际动作及动作报告均相等。冻结官方前向AST仅读取kwargs.get('timestep_scale')，不读取gt_frames，见[原始源读取](../reports/wc_w3_native_tail_response_cross_batch_source_read_20261007.jsonl)。旧_internal_dict未保存完整内容，具体变化原因UNKNOWN；安装的ConfigMixin以set差集生成默认值列表，仅提供顺序差异候选，不能据此宣布实际原因。

此附加跨批次检查最初的全字段等同断言，以及后续错误预期“kwargs零读取”的断言均失败，原件如实保留；实际只读一次timestep_scale已定位。它们发生在附加本地/只读核查，没有停止GPU、改变冻结源或追认失败通过。历史字节桥和本轮内部十一类严格重放已各自通过；不降低本轮完整状态、输入或重复检查，也不声称跨批次全部元数据相同。
