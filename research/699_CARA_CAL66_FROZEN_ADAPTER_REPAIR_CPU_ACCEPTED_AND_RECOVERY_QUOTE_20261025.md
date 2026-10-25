# CAL66冻结参数修复、CPU漏检归因与恢复报价

**修复与新的真实参数链CPU验收已完成；本轮没有重跑GPU。** 原R1的0/66科学失败与0.484958702187 GPUh精确结算保持，原α、强基线、输入、顺序和66路径不改。恢复方案见[完整R2计划](../plans/cara_policy_generator_20261020/CAL66_FROZEN_REQUEST_RECOVERY_R2_20261025.md)，预计6.880951 GPUh，单卡上限仍8、累计仍226、最终部署预算不变。

## 旧CPU为什么漏检

直接错误是 `Requests` 深复制真实Cosmos `InferenceArguments` 后给 `seed/num_steps` 赋值；复制不会解除其Pydantic冻结语义。第一处赋值即抛 `frozen_instance`，发生在昂贵模型加载之后。

旧验收并没有把关键接缝连起来：

| 旧检查 | 实际覆盖 | 漏掉的部分 |
|---|---|---|
| `check_cara_cal66_entry_cpu_r1.py` | 构造60个真实类；直接调用引擎，验证缺guardrail拒绝 | 未让真实类经过 `Requests` 的seed/steps适配 |
| `check_cara_cal66_sampling_cpu_r1.py` | 60条完整数值路径、原D/α与重复一致 | 请求来自 `check_full_sampling.py` 的可修改 `Sample` 夹具 |
| `check_cara_shared66_combination_cpu_r1.py` | 按5个源码SHA复用入口，加完整采集/评分/监督/终态组合 | 组合请求返回声明式端点，没有执行真实类适配 |
| 旧独立接受器 | 验证计数、SHA与完成标志 | 未要求“真实冻结类 → Requests → 两个生产引擎”的连通证据 |

因此是测试对象契约与生产对象不一致，以及验收组合缺少接缝要求；不是CPU不能发现，也不是GPU环境才触发。旧接受原件保留，并在新合并审核中明确将其入口结论标为superseded，不将旧CPU通过继续解释为完整入口已验证。

## 修复与新验证

- 新 `frozen_request_arguments.request_variant` 对完整dump仅覆盖登记seed/steps，用真实类 `model_validate` 重建，检查原对象不变、其余字段完全一致、返回仍是原冻结类；不改上游、不绕过验证。
- `Requests.prepare/validate_slots` 处理原role和schedule；生产runner在 `im.Inference(setup)` 加载权重前预检全部66槽位。失败尝试不能重放。
- 服务器CPU新注册加入真实类定义 `cosmos_predict2/config.py` 的SHA。完整分辨率66槽位预检、60个真实请求/角色边界、两种flow下15角色×两轮=60条数值路径均通过。原D/α、所有guided/final/RGB重复一致，guardrail/93帧codec/FD锁传递也通过。
- 失败边界包括非法override/真实Pydantic约束、错误步数网格、缺guardrail、writer异常、重复尝试；实际collector保留0完成/1失败/65未到达的66分母，不吞错或自动补跑。
- 新接受器10项反例测试通过：旧R1或新失败CPU、缺flow、可修改夹具、缺α/失败边界、源码/注册/原件SHA变化、GPU可见或非零退出均拒绝。

本轮第一次新CPU（stage frozen-r2）把派生属性 `num_input_frames` 加进了构造字典，真实类以extra-forbidden拒绝；原失败[回执](../reports/cara_CAL66_frozen_entry_CPU_check_r2_20261025_2017.json)保留，未产生GPU费用。修正后新stage **frozen-r3**，source `f35c826dc42e49db3e7b5465420eb1e33766810c`，容器实际20:20:38.154613开始、20:23:57.455413退出0，1CPU/4GiB、GPU隐藏、只读root。程序CPU墙钟194.699秒。

[完整终态原件](../reports/cara_CAL66_frozen_entry_CPU_progress_r3_20261025_2030.json)实际观察时间20:26:03；文件中的2030是标签，不是观察或完成时刻。已收完整原件，不另派CPU或重复终态收件。[新入口独立接受](../reports/cara_CAL66_frozen_entry_CPU_accepted_r3_20261025.json)、[修复/组件复用/报价合并审核](../reports/cara_CAL66_frozen_recovery_preparation_accepted_r2_20261025.json)。

数值CPU使用**真实冻结类和原采样器/RF/WC入口，但16×16几何、声明式微型权重/解码器**；没有加载完整Cosmos权重或CUDA。这证明请求链契约和数值执行，不是新视频质量、速度或真实GPU完整推理接受。

## 复用边界与剩余准入

合并审核核对144个执行/验收闭包文件，141个沿用原接受字节，变更只有 `Requests`、新冻结构造helper及runner的加载前预检。预算模块复用已经接受的SM89注册版本，不能替换成本地SM86文件。

监督10情景、存储/ENOSPC6情景、历史原件桥接、释放后48组LPIPS/156质量位置和失败恢复按原SHA复用。五真实质量模型与93帧三维度探针的既有独立接受保留；不把组合中的声明式评分当科学质量。

当前 `GPU_dispatch_ready=false`。未来执行还需要新R2身份与stage注册，绑定新CPU闭包及独立恢复报价、空输出卷与跨盘日志；旧控制器不能跳过旧SHA约束直接重放。fresh空闲UUID/硬独占、磁盘/内存、资源SHA和账本准入仍在实际启动前核验。用户本轮只授权准备，因此未注册GPU意图、未预约/改模式/创建检查。

旁支审计也看到旧 `p2_production_requests.py` 有直接赋值模式；它不在CAL66实际入口，本轮没有修改或宣布P2可执行。恢复P2时必须做相同真实类契约验证，不能沿用可修改夹具的结论。

## 完整费用

[报价原件](../manifests/cara_CAL66_full_recovery_quote_r2_20261025.json)：完整66生成5.133436 + 启动0.50 + 保存释放0.35，再加15% = **6.880951 GPUh**。原失败[加载技术原件](../reports/cara_CAL66_failed_loading_cost_readonly_20261025.json)显示模型加载22.04分钟；因此将原9分钟加载假设换为30分钟整段启动预留，其他逐臂价格和范围不变。

原失败已计0.484959，新卡仍上限8，失败加新预计7.365910；若新卡用尽上限，两卡总计8.484959。累计226不变，最近账本available52.879587（另有旧两卡16.5责任预约）；假设未来预留8后余额44.879587，本轮未写账。

GPU释放后评分仍2CPU/8GiB/最多6小时，规划约4.72小时。未来完整采集规划约6小时53分、之后评分约4小时43分；真实起点及资源准入尚未发生，当前不报完成日期。完整接受后沿原冻结科学合同分析，不从R1失败或本轮CPU夹具调参。
