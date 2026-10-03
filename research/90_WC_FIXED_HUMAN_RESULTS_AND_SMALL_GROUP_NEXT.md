# 人物固定刷新结果：调度固定化略有改善，稀疏近似保真仍待解决

2026-10-04。独立 WC-FIXED-HUMAN-R1-20261004-A/wc-fixed-human-r1/source4bd8951 正常退出0，四输出全分母、源码资产、严格D/D、实际来源/核与视频、费用/释放全部独立通过。该卡完成[89](89_WC_FIXED_HUMAN_FOUR_OUTPUT_CARD.md)的单次1800秒范围；原104点授权早已完成，不重跑。本次仅一个曝光人物样本human_199/seed0，离线官方掩码是诊断对照，不是可部署调度策略或CONF。

## 实际完成与证据

[四输出审计](../reports/wc_fixed_human_r1_audit_20261004.json)、[终态源码/费用/释放](../reports/wc_fixed_human_r1_terminal_20261004.json)、[机器摘要](../reports/wc_fixed_human_r1_summary_20261004.json)。每条视频都完成36个UniPC更新/72次CFG、一次真实prepare、93帧768×432/16fps完整解码。四条trace都等于同一38-deep官方掩码；官方D、fixed-D诊断和fixed-D测量三份视频SHA均为4d0f0549dbabf04e7f217037c40f6a30f41cb240289162d6fb0fbec2dde982fb。

严格D/D九门和prepared/pipeline/artifact/mode/RNG控制一致；step13/21/33/35/36各1216个原生组件独立重算一致。两控制视频CPU全帧MSE0/SSIM1/temporal0。实际固定D来源记录重建及15项合同拒绝控制通过；合同控制不替代视频IO审计。诊断D/D wall350.517/336.221秒含观察成本，排除部署耗时比较。

fixed-S在22次CFG刷新中执行506个真实S注意力算子，26次后续cache调用读取近似来源；层6/23/27仍dense回退。核元数据、CFG/group/epoch、过去来源、call70清空和尾部dense独立验证通过；S不写入true-dense历史。固定S视频SHA为8113659676684a91ce1e8d070e9893f7d1fa3d2f6e8e58191b1218a1f1ac90e1。

## 同一官方视频参考下的开发比较

[固定D/S全帧指标](../reports/wc_fixed_human_r1_metrics_20261004.json)/[旧adaptive-S与fixed-S协议和视频绑定](../reports/wc_fixed_human_r1_cross_metrics_20261004.json)。模型/条件、采样、WC配置、固定上游源码和共同资产检查匹配，旧官方视频与当前三份D字节SHA相同，才复用旧曝光adaptive-S。不是新独立场景，也不是Native全算参考。

| 相对相同官方WC视频 | 原adaptive-S | 当前fixed-S |
|---|---:|---:|
| RGB MSE（0到1） | 0.01786721 | 0.01650696 |
| RGB PSNR（dB） | 17.4794 | 17.8233 |
| 平均luma SSIM（win7） | 0.705409 | 0.726741 |
| temporal difference MSE | 0.02149043 | 0.02089140 |
| 帧差运动量比 | 0.952159 | 0.966809 |
| 实际deep CFG次数 | 35 | 38 |

固定化伴随RGB MSE下降7.613%、PSNR升0.3439dB、SSIM升0.02133，但保真差异仍明显。旧adaptive与新fixed的实际deep差异为calls46/47/48/51/52/56/57/58/69；fixed-S本轨迹上的原adaptive predicate仅在46/55与强制掩码不同。这是各自真实状态的诊断，不能把后者作为旧adaptive轨迹的预测或反事实收益标签。

两S视频彼此PSNR19.3147dB/SSIM0.774501，说明调度和后续状态确实改变了输出；非线性latent/cache反馈与35/38计算次数差异，使7.6%不能解释为调度贡献百分比，也不能把误差拆成可加的两项。当前证据只能排除“固定调度即可消除全部差异”这一解释。视频帧early/middle/late分段均有差异，帧序号不是去噪步骤；代理指标不证明语义或物理正确性。

## 描述性耗时与完整预算

固定D/S单次完整Inference.generate的CUDA边界wall为212.221173/204.658102秒，少7.563秒（3.5638%，D/S比1.03695）。每臂真实prepare并计入必要mask/来源/核检查、decode、guardrail和write，保留首次S成本。只有一对，不能称重复确认的加速或质量—时间前沿；host分段未经独立CUDA同步，不作阶段归因。原adaptive人物7.922%来自另一组35-deep输出，不能与固定38-deep耗时直接相减来分配加速贡献。

全卡包括加载、四臂、退出/flush/释放的实费1237.699305秒=0.343805362GPUh≤1800秒，0.5GPUh预付已按实际替换。累计7.7514316824275165/12GPUh、39jobs，余4.2485683175724835GPUh，无inflight。原PID2714273/2714291/2714293消失、共享f1锁可获取、指定GPU24MiB/noapps；580条monitor峰值26796MiB。权威账本结算字符串保持，验收由独立报告给出。

终态原件3199307bytes，SHA9f1418d55f297f62f5ce8868759de983e0df736185bb939f06b86357eab0f4e5；[gzip原件](../reports/wc_fixed_human_r1_runner_20261004.json.gz)SHAa19990b32693317d8bd1ee5b4200069b6ac4b03ba5fd026b03dc260f71d0c65f。D/D时点原件另存，未被终态覆盖。视频/权重/大张量保持服务器，不入Git。CPU分析未新开GPU、修改在跑stage或账本。

## 下一步：先缩小稀疏更新范围，学习型调度仍后置

继续WorldCache，暂不把当前23层同时S刷新作为质量保持候选。固定动作已有实际等价控制，下一应先区分较少S层/较少S刷新是否能保住同一官方参考下的输出，再扩大压缩程度；不直接加入Trust Head、LoRA、多模态模块或新的训练。

已用原104点/312case做[CPU层组排序](../reports/wc_fixed_human_next_layer_shortlist_cpu_20261004.json)，重算三次hot中位计时和每层四输入的最坏RMSE/最小速度比。沿原RMSE≤5%、速度≥1.1的局部门，14层四输入都通过；按最坏误差升序的前三层是2/5/3，可把{2,3,5}作为小组草案。排序仅来自已曝光单场景算子，不是人物视频安全层或泛化证据；算子省时不等于端到端收益。首个小组对照的作用是机制定位，可能只有很小的净耗时收益。

接下来仅CPU准备可选S层集合与刷新频率接口，保持完整官方掩码、dense对照/真D隔离和失败分母；对照应包含全D、原23层S、小组S，并明确必要选择成本。参数、同预算、完整输出数量和加载成本具体化后另设唯一GPU卡、freeze及实际门/fresh准入；当前没有下一卡、reservation或运行。不能自动重提本卡，也不因本轮小幅改善扩样或接受候选。

如果小组/低频仍不保持保真，优先回到近似与缓存寿命，减少S状态后续复用或安排真正D锚点；若基本近似已可靠，再进入[68 W3有符号、同状态、预算匹配的刷新价值](68_WC_COUNTERFACTUAL_REFRESH_VALUE_DESIGN.md)。本轮掩码/两类predicate不是RV标签，没有collector、Head拟合或训练。Native/少步/合理调过WC的强基线前沿与独立CONF仍缺，完整科学goal保持active。
