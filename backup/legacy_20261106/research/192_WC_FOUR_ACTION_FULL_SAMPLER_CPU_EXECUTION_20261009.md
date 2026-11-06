# H-T60：完整四动作CPU对照、失败与独立重试

## 目标及完整设计

H-T59核对的Human seed2、Human seed3、Common seed3三条完整原生轨迹都含DC。下一完整部署必须支持CC／DC／CD／DD，不能把共同OR刷新当作原生动作回放。当前H-T58只验真实S22的CC／DD成对接线，仍按冻结source9f01274、156文件、两完整父／两93帧视频和16局部pair完成；本CPU批次不改它的运行源或范围。

H-T60使用独立四动作控制器、实际生产WC／RF函数和官方完整36步UniPC求解器。固定输入是三条已完成轨迹的完整动作mask与一条合法区内四动作循环mask，绑定H-T59完整结果SHA。两种flow×观察OFF／ON×两次严格重复，共32比较、64完整路径、2304 solver更新、4608 net调用；每比较直接torch.equal核对全部36个原FP32 guided张量与最终latent。各路径保留输入／条件／RNG、实际层访问、五检查点和step22完整状态／条件扰动恢复后继续。

旧H-T58完整68行及96个自产Toy张量CPU重读不删；新增12声明失败控制，共112行。此处Toy四层CPU权重、注意力／准备／归一化／broadcast到latent，不加载2B权重或CUDA，不产生视频质量、速度、风险政策、终点／未来成本标签。

## R1实际执行及失败

- 执行source：`56f7faf49ee6684d435f33540f39c10daed8a7c2`，92文件载荷／8实际runtime源码。
- 独立目录：`.sync/wc-cfg-paired-four-action-full-sampler-cpu-r1-20261009`。
- 原supervisor／child：3452912／3452913，已退出1且句柄消失；driver全wall **331.658825秒**。
- 在第一条新完整比较的汇总字段`full_action_sequence`写出位置，使用了仅在内层`run_path`存在的局部变量`sequence`，触发`NameError`。本轮完整范围未结束、没有验收通过，不将此前执行片段追认为通过子集。
- [完整原件捕获](../reports/wc_cfg_paired_four_action_full_sampler_cpu_r1_terminal_20261009_capture_and_independent_audit.json)保留原失败、core／driver日志、源／登记／计划和回执压缩原字节；92载荷／8源码前后SHA一致，CUDA未初始化／新增GPU0／本driver不写账本，前后预算SHA同为604d7fcaad50…。

这是测试记录实现错误，不能据此否定四动作接口或科学方向；原失败、源和分母均保留。

## R2预登记修复与接续

只将该汇总字段改为`action_schedules[schedule].copy()`；部署与捕获工具增加独立`r2`身份。控制器、原WC／RF／solver、输入mask、完整112行、所有恢复／重复／观察／失败及旧结果标准不变。R2在新目录执行全部范围，禁止复用R1片段、不改R1原件，也不改变当前GPU冻结源。

R2已完整结束并独立验收通过，完整结果见[194](194_WC_FOUR_ACTION_COMPLETE_SAMPLER_CPU_RESULTS_20261009.md)：112行／新32比较64全36路径／12失败及旧68控制保持，driver525.024606秒退出0、3455392／3455393消失；不是2B或新政策收益。H-T58原GPU与后CPU亦已完整结束，见[193](193_WC_REAL_PAIRED_INTERFACE_COMPLETE_RESULTS_20261009.md)，原身份不复投。上述R1失败及其完整登记不变。

组会飞书已由CLI完成并回读，最新完整接口结果在更新；新CPU准备不冒充新科学结果。原GPU结算后实计29.895246590／50GPUh，65提交／无GPU在途；旧在途`used=50`只是预留。整卡≤2GPUh且有余额自主、>2GPUh具体确认，不缩拆／训练／扩稀疏／OMR／DRE／人评；goal active。
