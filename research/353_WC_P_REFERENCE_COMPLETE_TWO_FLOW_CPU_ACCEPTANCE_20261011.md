# P 工作参考完整 CPU 验收与下一实际诊断

**新的 P 工作参考已按设计进入完整采样：两 flow 下实际缓存、公式、候选 warp/head、D-only校准和完整状态恢复均通过。** 这把335的参考点对齐假设从数学组件推进到可运行候选。它仍是实现正结果；真实局部近似误差、最终视频质量和净速度均未由本次CPU证明。

## 验收结果

原 R3 source `a2f40f38e8a8f7a2f16b4e6c562cd3a42cfe424e`，独立stage `.sync/wc-p-working-reference-sampling-cpu-r3-20261011`，原监督4108321／子4108324退出0并消失，完整CPU耗时 **87.007254884秒**。440冻结来源前后一致；原R1路径同址比较和R2夹具请求绑定失败保持，不追认其采样或通过。候选数值模块在两次修复中没有变化。

| 检查 | 实际结果 |
|---|---:|
| flow OFF／ON，每组OFF＋旧/新W1＋旧/新beta=1 | 10/10完整路径 |
| 普通UniPC更新／CFG调用 | 360／720 |
| 独立再次实读原文件／有限FP32张量 | 10／370 |
| 完整物理和所属状态扰动恢复 | 40／40 |
| 读取P前首十更新的新旧直接相等 | 40／40 |
| 新P公式、真实cache、exact warp后实际native head输入检查 | 72次 |

两flow、两模式各18次P分支读出，覆盖两个CFG分支。后续solver返回实际改变，排除了候选没有接入却只通过旁路公式检查。所有实际C读出都核对完整真D状态、probe/residual物理缓存与RNG不变；P出生仍为UNKNOWN_NOT_ZERO且不能重置RA零风险。D来源沿原方法，控制动作没有改。两flow每个OFF72次head，各旧/新W1或beta=1均100次head；本候选保留原head与额外候选head全部费用，未混入E5省head优化。

独立证据：[完整capture](../reports/wc_p_working_reference_sampling_cpu_r3_terminal_20261011_capture.json)，同名目录四份原始launch/receipt/registration/result的gzip原件，绑定原SHA。原测试使用实际WC/RF、Block、完整guarded sampler与原生选择性checkpoint head的AdaLN LoRA/Wan FP32配置；小权重、attention、prepare/unpatchify、decoder/writer明确为Toy。CPU禁止CUDA与下载、没有GPU提交或账本写入。独立capture期间账本SHA保持；账本中仍有原E5在途预留，不称作P实际费用。

## 下一科学问题

在早／晚、两已曝光CAL、P/D出生来源条件下，从同一实际当前状态比较：官方C、旧D参考scalar、新P工作参考scalar，以及旧/新beta=1强对照。teacher只用于离线评分，每次同状态完整计算后完整恢复，候选不修改部署latent、缓存、D拟合、RNG或控制器。先区分改变参考点能否降低guided误差，以及收益是否依赖来源/年龄/flow，不先训练、不扫层数或阈值。

下一真实范围、全部配对、head/teacher及复制/加载费用还需具体实现和登记；不能凭本次CPU直接声称GPU ready，也不把该假设加入已冻结E2/E3或在途E5。完整实际受影响CPU、生产CPU与fresh资源通过后，按当前单张完整≤8GPUh直接推进，严格>8仍具体确认。真实误差与终点证据分别汇报，正负配置与缺证据保持，不以单项阈值否定整个方向。

## 原E5继续

Unix1791693058.613，原 GPU4103103/4103190及自动CPU4103104存活；eff2b71与456来源不变，唯一目标A6000app4103190/21274MiB。AV_R1的LEGACY_OFF和FAST_OFF均已有完整36步回执，LEGACY_W1_ONE_PHASE正在采样，其余三块未开始。全24／原888张量444新旧＋444重复／所有有效93帧的独立终态验收仍待；两个完成路径不冒充整卡结论。

当前累计前已结算41.908688946、cap77.895246590，新48余35.986557644；79次提交，只有原E5在途。现有预留不是已实耗，最终完整wall只结算一次。E2/E3原above8具体批准待，不重复询问或拆卡；无训练人评，目标active。
