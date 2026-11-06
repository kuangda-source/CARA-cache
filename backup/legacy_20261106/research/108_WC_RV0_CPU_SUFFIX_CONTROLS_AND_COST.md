# W3/RV0第一关：官方后缀CPU复现通过，尚无C/D收益标签

2026-10-04。承接[107公平完整结果与方向门](107_WC_FAIR_CAL_RESULTS_AND_DIRECTION_GATE.md)和[68刷新收益设计](68_WC_COUNTERFACTUAL_REFRESH_VALUE_DESIGN.md)。上一目标轮次属于**progress**：完成十四输出/十组指标/实费释放与GitHub同步，证据使“直接确认稀疏候选”不再是优先行动。本轮继续已有W3的CPU因果接口与成本准备，未选择下一GPU卡、采标签、拟合Head或训练。

## 新增接口及实际证据

[SamplerSuffixControl](../src/wcomr/rv0_fork.py)在实际完成的solver更新之后保存latent、完整UniPC字典/历史、WC状态、buffer值/身份、module模式、全局和显式generator RNG，以及固定条件/噪声/配置/模型参数版本。上下文必须有request/model/condition标识，当前只支持单进程、eval、WC70、Karras36网格、无LoRA/稀疏adapter的偶数CFG边界。条件闭包仍在原进程中，不是可独立重启的序列化checkpoint。

续推循环直接从SHA固定的官方 `generate_samples_from_batch` 复制完整loop AST，不重写UniPC更新，不重新set_timesteps，不按Euler近似；使用原velocity closure、同一个显式generator和剩余实际时间网格。每条控制完成原36网格与WC70尾部后，恢复原父状态；返回的child latent为独立副本。额外保护调用方仍持有的真实parent latent，错误、顺序交换或非有限输出不得回写父轨迹。当前接口只重复**未干预后缀**，没有C/D动作参数或收益collector。

[当前R3实际CPU报告](../reports/wc_rv0_suffix_cpu_r3_20261004.json)、[服务器原件/来源独立审计](../reports/wc_rv0_suffix_cpu_audit_20261004.json)、[控制源](../tests/check_rv0_fork_cpu.py)。Torch2.7.1+cu128，CUDA不可见且lazy init被禁止；耗时31.469935秒，31个当前文件与五个官方源逐SHA绑定，服务器原件SHA `8cd9b64975d5c5cf8d24c088ce8977d3d73dbc5dfacf91822ea850a229c569ef`。独立审计不导入Torch、不重跑测试或GPU。

| CPU控制组 | 父采样 | 每条后缀 | 同状态重复/顺序 | 结果 |
|---|---|---|---|---|
| flow OFF / forced full | 36更新/72CFG | step22之后14更新/28CFG | A→B、B→A，共四条 | 每输入/输出/deep调用、最终latent及状态组件与原路径相等 |
| flow OFF / forced cache | 36更新/72CFG | 同上 | 同上 | 相等；确认包含真实WC复用分支 |
| flow ON / forced full | 36更新/72CFG | 同上 | 同上 | 相等 |
| flow ON / forced cache | 36更新/72CFG | 同上 | 同上 | 相等；确认包含真实WC复用分支 |

每组父轨迹在加/不加后缀控制时，全36/72输入、输出、solver输出、最终latent、解码输入、mock产物、RNG与状态相等。拒绝检查覆盖缺上下文、改变续推code、半个CFG边界、改写父latent、缩短网格、条件漂移、非有限child及重复label；非有限child保留TECH_BLOCKED记录后恢复父状态。最终测试调用方的cache/solver/RNG/buffer/mode/config和函数绑定也恢复。loop AST SHA `b0b85fe9b0aefad24d4cf958cdac01c16a521e438581d9750c7bcc1e6f8f9971`。

forced full/cache的全局阈值只构造两种CPU恢复控制，不是生产策略、同预算刷新算法或同状态C/D干预。模型、conditioner、noise准备、patch/block算子、tokenizer与writer为明确Toy边界；没有权重、真实VAE/稀疏核、编码视频或真实GPU分叉。因此**CPU接口通过不等于完整RV0验收，更不等于刷新有正收益**。

R1在来源校验处失败（10.176780秒）：`marshal.dumps(code)`包含引用/驻留信息，同一code对象两次结果可不同，误拒绝后停止。该失败与原SHA保留。[R2](../reports/wc_rv0_suffix_cpu_r2_20261004.json)改用稳定字节码/常量/名字/参数清单且固定官方源码SHA后四组通过（30.645966秒）；R3新增真实parent latent、网格拒绝及调用方恢复检查后另跑通过。R2不追认后来源码，三个CPU目录均未覆写；全部新增GPU费用为0。

## 当前状态缺口与在线特征位置

| 对象 | 当前可用事实 | 下一接口必须处理 |
|---|---|---|
| sampler续推 | 双CFG都完成后的边界已CPU复现 | 真实网络/条件/显存状态的GPU同路径控制仍缺 |
| C/D选择位置 | 官方forward的probe在deep之前已支付，阈值判断之后执行cache或deep | 在官方decision副作用之前介入；强制C/D不能只事后改skip标志或伪造锚点 |
| step/噪声时间/CFG身份 | 来自当前scheduler及WC计数器 | 不把72次branch调用当36次同成本刷新；采标签前冻结branch或联动单位 |
| age/最近true-full | 历史动作可以维护；官方残差窗口没有完整刷新时间戳 | 新元数据随request/CFG/恢复状态隔离，计入成本，不用未来trace作在线age |
| 当前浅层漂移/accumulator | probe后才已产生；只能读取当前已付probe与过去锚点 | 归约、clone、访存/同步开销需记录；before-forward接口不能冒称取得当前probe |
| 历史残差norm/输入变化 | 可由过去锚点或当前已有输入计算 | 记录额外成本，优先缓存历史统计；不能先执行当前deep来决定是否跳过 |
| attention drift/当前deep误差/未来视频 | 当前决策前未产生 | 只可离线诊断/标签，不作为部署输入 |
| 有符号收益 | 当前0条；旧整轨迹stage/WC指标不是同状态反事实 | 对相同Native参考比较J(C)−J(D)，保留负收益；C/D互距不是收益 |

下一CPU工作应补两动作及保护/失败合同：warm/tail、合法缓存历史、request/model/condition/CFG隔离、最大age及预算可行性。先固定原WC近似器和dense算子，Head-off等价、C/C、D/D与交换C/D顺序控制必需；不先加第三动作或Head。标签类型和后缀必须在采集前冻结：固定动作后缀的边际收益与预算匹配策略收益分别报告，不能把额外一次full的改善称等预算优化。

## 实际账本和费用提案

fresh SSH只读核验及R3独立审计再次确认：累计 **10.713586944446/12GPUh、44jobs**，余 **1.286413055554h = 4631.087秒**，无inflight。所有CPU轮次账本未变；没有新GPU任务、预付、标签或训练。

[费用草案](../reports/wc_rv0_suffix_cost_draft_20261004.json)保留现有完整视频381.750898秒代理、原fair卡实际加载99.810262秒、bookkeeping75秒、1.2余量和30秒释放，不按剩余步数折扣、不把31秒Toy CPU时长换算为真实GPU时长。

| 未选择范围 | 完整视频费用等价代理 | 已知项加余量秒 | 拟cap | 单独cap+15秒算术可容纳 |
|---|---:|---:|---:|---|
| 两父轨迹+四条未干预后缀，仅恢复控制 | 6 | 2988.379 | 3300 | 是 |
| 上述控制+一对同状态C/D+Native参考 | 9 | 4362.682 | 4500 | 是 |

第一项只需两个父采样普通视频及child latent/状态回执，child不另decode，避免把未经恢复验证的VAE缓存/offload副作用带入父状态。第二项仍缺动作接口、合法点、固定后缀与主要损失定义。两拟cap共7800秒，不能同时承诺。

**这不是完整已验证成本上界或准入。** 新快照/条件恢复/哈希传输与额外峰值显存尚UNKNOWN，381.75秒代理没有覆盖这些新增操作的实测上界；必须在具体方案内补开销和内存包络、source/实际门及fresh资源/余额准入，再决定是否选择一张有界诊断卡。后续RV1更大样本、budget-matched标签、自动语义/物理评估与拟合不在这两项中，不默认免费。

继续WorldCache的CPU准备，当前科学goal active；没有重启旧104/任何终态卡，不新增人工评审或付费评分。重要方向取舍保持[107](107_WC_FAIR_CAL_RESULTS_AND_DIRECTION_GATE.md)结论：稀疏净收益尚未成立，W3只是下一候选路线，不能把本轮工程通过写成方法有效或论文接受。
