# H-T60：四动作完整36步CPU结果

**已完成：CC／DC／CD／DD在实际WC／RF／UniPC函数、Toy CPU模型中的完整求解器对照通过。** 三条旧完整动作mask及一条四动作循环的32比较／64路径，原顺序与成对顺序的每步FP32 guided、全部状态和最终latent相同。这解决了仅CC／DD不能覆盖旧混合DC动作的问题；没有证明真实2B全36步部署、新风险政策、终点收益或速度。

设计及首次失败见[192执行报告](192_WC_FOUR_ACTION_FULL_SAMPLER_CPU_EXECUTION_20261009.md)和[原计划](../plans/WORLD_CACHE_PAIRED_FOUR_ACTION_FULL_SAMPLER_CPU_20261009.md)。实际R2 source`43e4306d23c5f5fdc38460cf019e84eea04cdc57`、92文件载荷／8源码，独立`.sync/wc-cfg-paired-four-action-full-sampler-cpu-r2-20261009`。R1的汇总NameError完整原件保留，R2只修该字段及独立部署／捕获身份，控制器、数据、范围、所有旧判据保持。

## 全量完成及独立核对

| 范围 | 完整结果 |
|---|---|
| 旧H-T58完整控制 | 全68行重跑，包含原60行、S22接口／父对照、实际batch／writer失败、20证据破坏拒绝、96自产Toy张量实际重读 |
| 新完整矩阵 | 4 mask×两flow×观察OFF／ON×二重复，32原／成对比较、64完整路径、2304新solver更新、4608新net调用 |
| 原FP32／终点 | 每比较直接torch.equal全部36 guided，共1152次，最终latent直接相同；全36solver输出、条件／RNG／counter／cache状态相同 |
| 实际动作与层访问 | 四动作均覆盖，原记录混合位置不丢；每pair前两浅层各2次，深层次数为动作中D的数量 |
| 因果边界 | 合法区两侧prefix都已支付、深层未开始才执行选择器，各完整路径27次；固定mask不是在线新风险政策 |
| 完整恢复 | 每路径step22真实扰动latent／counter／buffer／条件，完整恢复继续；五检查点及最终各50状态组件、原条件／RNG和参数版本保持 |
| 观察与重复 | 全分支144事件／完整路径比较，OFF无事件，ON每call的输入／输出相同；每flow／mask四个观察／重复组合一致 |
| 新失败控制 | 两flow各6类，共12，selector／非法动作／RNG故障在22步、solver尾故障在35步、绑定／条件构造故障在0步，完整计划和整fixture弃置保持，不声称任意异常全部回滚 |

共**112行**，没有按成功子集验收。严格保留保护区联合DD（counter0—12、68及下一周期0）；其中35步的联合保护是当前控制器合同，CPU固定mask对照不是证明所有新输入的原生阈值政策等价。

原supervisor／child3455392／3455393均退出0且消失；fixture492.909743秒、driver全wall**525.024606秒**。全部载荷／runtime SHA前后一致，CUDA未初始化、新GPU0、本driver不写账本，前后预算SHA均为`1d2cf34794e0ce808bbd57e34a162ba3d1b19017410e656309c92347f4e8e5a1`。期间原H-T58已正常结算，账本为29.895246590／50GPUh／65次提交／无GPU在途。

[完整原件与本地独立验收](../reports/wc_cfg_paired_four_action_full_sampler_cpu_r2_terminal_20261009_capture_and_independent_audit.json)核对全部旧68行、新32矩阵／12失败、完整各路径与观察／重复分组，原件gz和首次失败仍在仓库。源静态逆AST与真实执行分开：实际CPU通过是本报告结论，模块静态proof中的`actual_model_or_full_sampler_parity_verified=false`未被篡改追认GPU通过。

## 与真实接口结果的关系及下一步

[193真实模型结果](193_WC_REAL_PAIRED_INTERFACE_COMPLETE_RESULTS_20261009.md)已经证明一个曝光Common S22同CC／DD动作的真实接口等价和完整父无扰动。H-T60补充的是四动作与完整求解器CPU能力；两者合起来仍不是完整真实候选策略的终点确认。

下一真实36步卡先明确比较对象：原生自适应政策、固定旧mask回放、或新的共同刷新政策不能混写。当前控制器在末尾联合DD，可能与另一个新输入的原生条件分支C／无条件分支D不同，须先用低成本完整CPU对照区分／登记边界，而非默认为任意原生全轨迹等价。完整部署、终点／未来真实成本标签和WC／简单共同刷新／Cosmos校准RA仍待；不再扩大局部机制评分或用旧曝光mask当泛化证据。

组会文档保留全部旧科学结果与判据，报告先讲发现与价值，再讲边界。goal active，无预算或授权阻塞；下一完整GPU forecast未选择，整卡≤2GPUh且有余额自主，>2GPUh具体确认，不缩拆、训练、扩稀疏／OMR／DRE或引入人评。
