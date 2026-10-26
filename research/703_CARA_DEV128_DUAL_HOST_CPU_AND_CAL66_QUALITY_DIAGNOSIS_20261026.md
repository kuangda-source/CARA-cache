# 703 · Shared25-C新DEV128：双端生产CPU接受与CAL66质量诊断

2026-10-26实际收件。用户要求先准备、不要启动GPU。本轮完成固定16新输入的双服务器曝光核查、六角色128路径生产入口、受影响采集/释放后评分组合CPU验收及两端完整报价；GPU提交0、预约0、新DEV推理0。原CAL66完整接受、失败与费用均保持。

## 完整范围与真实验收

科学清单：[DEV128](../manifests/cara_DEV128_scope_r1_20261026.json)；详细协议：[双端准备合同](../plans/cara_policy_generator_20261020/SHARED25_DEV128_DUAL_HOST_PREPARATION_R1_20261026.md)。六角色Native35、Native26、S25-C、S25-A-phase、Shared25-C、Shared25-A-phase-age3；96正式+24计时重复+6旧CAL预热+2旧CAL诊断=128，4419pairs/8838CFG/单load。原α与所有强基线字节保持。正式质量为80组LPIPS/7440帧及96视频×3指标=288位置；16prompt为统计单位。

[曝光原件](../reports/cara_DEV128_dual_host_exposure_20261026.json)核对原48保护组及源SHA，覆盖本地4227文档、四卡当前695输出JSON、两卡当前136及旧workspace1299输出JSON，记录范围内无已使用命中/读取错误，不外推未知外部目录。首次GPU启动前须再增量核查，新准备文件的身份元数据与真实执行记录应按来源区分，不能将本次审计当永久有效。

| 主机 | R4容器实际退出（北京时间） | 独立接受 |
|---|---|---|
| 四卡Ada，默认 | 12:31:00.930，exit0 | [原件](../reports/cara_DEV128_four_card_CPU_complete_r4_20261026.json) / [接受](../reports/cara_DEV128_four_card_CPU_accepted_r4_20261026.json) |
| 两卡A6000 | 12:28:16.876，exit0 | [原件](../reports/cara_DEV128_two_card_CPU_complete_r4_20261026.json) / [接受](../reports/cara_DEV128_two_card_CPU_accepted_r4_20261026.json) |

执行source `d39abcbb26b7ec1ac36855c06b65b0c83d1fc8c2`；两个stage独立不可变、各2CPU/8GiB、只读容器、GPU隐藏。102个真实冻结请求及128位置预检；24条两flow小模型路径；失败128分母/127未到达、禁止原位置重放；128合成采集/26数值控制/80与288释放后评分组合；真实93帧LPIPS及MUSIQ/主体一致性/运动平滑三模型CPU探针均通过。CPU数值用旧CAL，合成端点明确标注，不构成新DEV质量或速度证据。

本地6项合同测试通过；[独立接受故障注入](../reports/cara_DEV128_acceptance_failure_boundaries_20261026.json)对两端原件分别拒绝GPU可见、运行中、非零退出、缺路径、缺评分、缺模型、源码改变、新DEV推理、非法复用9类异常。

## 故障、修复和复用边界

四卡首次打包时主机默认Python3.8缺少路径API，尚未创建容器；使用既有接受的Python3.10桥接。后续CPU依次发现缺guardrail依赖、动态导入测试模块，源码闭包已纳入AST导入/文件字面量；没有GPU提交。双端R3均完成参数链和128组合，真实质量模型探针因从新stage导入代码而触发原指标源码身份拒绝。

R4将原模型加载固定回已接受的质量资源目录，仅新DEV评分编排使用新模块。独立核对源码/权重SHA；原身份检查未放宽。R3已通过的入口/组合只在整条依赖闭包与runtime不变、原容器退出/GPU隐藏的前提下复用，R4重跑受影响的真实质量模型。所有旧失败/中途快照保留，文件名不代替实际退出状态。

**本轮接受范围是生产入口及采集/释放后评分CPU；不是128整卡GPU监督/财务终态/双端调度接受。** 新128专用supervisor、存储/预算异常、真实账单与中央结算绑定仍待组合检查。首次执行还须fresh曝光/资源/账本与独占准入，以及明确GPU授权。不得拿旧CAL66监督接受冒充128已可派发。

## 完整报价与当前约束

[机器报价](../manifests/cara_DEV128_dual_host_whole_quote_r1_20261026.json)逐角色覆盖全部128路径，加0.5h启动、0.35h保存/释放及15%余量。

| 主机 | 预计GPUh | 原12GPUh设计子池 |
|---|---:|---|
| 四卡Ada | 12.349232 | 超0.349232，未准入，未提高上限 |
| 两卡A6000 | 11.618228 | 能容纳，仍未授权执行 |

四卡未测Native26/Shared25角色使用该机已接受PG全D时钟保守计价；不能把A6000结果当Ada同角色速度，也不削减余量凑报价。两卡使用CAL66同机同角色完整时钟。默认四卡偏好保持，但不等于可以越过报价。

GPU释放后CPU评分拟2CPU/8GiB，保守约8.56h、10h停止上限，单列不计GPUh。中央最近已用161.396620633628、旧未知责任16.5、可用48.103379366372、累计226不变；本轮无账本写入。最终部署仍为min(257.7712338712067秒,0.8×freshNative)。

## 新反馈处理与零GPU诊断

[完整反馈处理](../plans/cara_policy_generator_20261020/CAL66_FEEDBACK_AND_DEV128_BOUNDARIES_20261026.md)：当前主线采用“刷新放置与输出保真”，Shared25-C不含A；A保留机制对照。跨24/25/26D同向不是三个独立输入集的泛化复现，Native26的MUSIQ优势也保留。LPIPS低不等于逐位不变或已证明下游世界模型收益。

已对接受的旧CAL四输入S25-C/A共8视频全部744帧作CPU诊断，逐视频SHA与终态核对。A/C的Laplacian方差比0.665–0.778，高频能量比0.725–0.895，四输入同向降低；支持细节减少/平滑与MUSIQ下降有关，不能证明它是唯一因果因素。逐帧MUSIQ显示大部分均值下降来自AV28和AV51，帧不算独立样本。见[锐度原件](../reports/cara_CAL66_sharpness_diagnosis_r2_20261026.json)、[逐帧MUSIQ](../reports/cara_CAL66_MUSIQ_frame_diagnosis_20261026.json)、[固定帧对照](../reports/cara_CAL66_S25_C_A_fixed_frames_r2_20261026.jpg)。

不增加Shared24自动退路、不改变原质量门、不换输入/α/默认主机。额外质量维度可作为后续释放GPU后的CPU扩展；Q5先登记新网格/模板与能量可辨识性，缺新Native轨迹时不能称已证明能量迁移。这些建议不暗中增加当前128范围或GPU授权。
