# W3真实恢复诊断准备：修复冻结条件对象，明确两场景3900秒预案

2026-10-04。承接[109单次动作CPU接口](109_WC_RV0_ONE_ACTION_CPU_CONTROLS.md)。上一轮是有效progress；本轮核对实际官方源码，发现并修复条件恢复的真实接口缺口，完成新恢复入口CPU验证和成本预案。GPU任务仍未选择或提交，真实RV0验收与收益标签仍为0。

## 发现的接口问题及修正

官方 `BaseCondition` 和 `Text2WorldCondition` 是 `@dataclass(frozen=True)`，源码SHA `47554e88f2a5d5157e30b18b1d7ad4a4ee55a99dfbaf7071f680c7acf438843a`。原[SamplerSuffixControl](../src/wcomr/rv0_fork.py)恢复时对条件对象直接 `setattr`；Toy条件对象允许这一操作，但官方对象会抛 `FrozenInstanceError`。因此109的CPU通过不能升级为真实模型条件恢复通过。

新增 `restore_object_state`：只针对冻结dataclass，使用Python对象重建的 `object.__setattr__`/`object.__delattr__` 恢复已捕获属性；普通对象沿用原方式。保留原实例身份和类型、复制保存的tensor值、清理child新增属性，不改dataclass的冻结标志。恢复后普通赋值仍须抛FrozenInstanceError。官方源码和类定义未修改，原closure不替换成新函数或独立重启checkpoint。

[新测试](../tests/check_rv0_restore_cpu.py)从固定官方源码复制完整Base/Text2WorldCondition类AST和其冻结行为，使用原CPU夹具DataType枚举与Toy网络。它验证tensor漂移/额外属性恢复、实例身份和冻结行为，并在这类条件下跑完整父轨迹与未干预后缀。当前C/D动作回归仍使用原Toy条件；尚无真实网络、实际Video2World条件全路径或冻结条件+C/D的GPU联合验收。

## 明确下一诊断范围，保留完整RV0缺口

[run_restore_controls](../src/wcomr/rv0_restore.py)及[未选择配置](../configs/wc_rv0_restore_r1.json)明确为：两个已曝光CAL场景，各一次完整原WorldCache父采样；step22双CFG更新后分别从相同状态跑两条未干预后缀A/B，再恢复父状态并继续普通pipeline到编码视频。合计**两父轨迹、四条14更新/28CFG后缀、两个93帧父视频**。

每条后缀与恢复后实际父轨迹的剩余全部输入/输出、deep调用、solver输出、最终latent、完整状态组件逐项相等；每个父视频另须复现已冻结的官方WC编码SHA。每个场景只有一次fresh prepare，不在child中调用VAE或编码器。A/B相同动作重复在这里用于恢复控制，不能冒称交换不同C/D动作。

本卡没有另跑新无观察器父phase，其对照是独立生成的历史官方视频桥和本次恢复后live parent continuation。这与“新无观察器/有观察器全pipeline逐项等价”的证据不同，必须单列。完整RV0仍要求C/C、D/D、交换C/D顺序、开关等价、合法点和对应参考/后缀口径；本卡通过也不验收这些剩余项，更不解锁Head训练或正式标签。两个场景不删为一个场景来适配预算。

## 实际CPU验证与失败保留

[R3实际CPU](../reports/wc_rv0_frozen_restore_cpu_r3_20261004.json)/[原件独立审计](../reports/wc_rv0_restore_preparation_audit_20261004.json)：**197.132755秒**，Torch2.7.1+cu128，CUDA不可见且lazy init被禁止，35份当前测试依赖与六份官方源码绑定。服务器原件SHA `20f247f3aca5b6479eda9ba64a22564adaa8b2111d98b64b218f1d04dbce2f6e`。

| 本轮控制 | 实际结果 |
|---|---|
| 冻结条件对象 | 普通赋值拒绝；tensor和额外属性恢复后身份/值/冻结行为保持 |
| 新恢复入口 | flow OFF/ON两组，每组两个父36/72及四条14/28后缀；全部后缀和父continuation/状态相等，ordinary mock视频桥相等 |
| 原接口回归 | 未干预四组及C/D四组、两CFG槽位、48条动作后缀与原保护/失败恢复检查通过；绑定当前修复后的fork源码 |
| 分叉前内存门 | 只遍历metadata，拒绝逻辑副本超过cap及GPU free不足的合成门输入，在任何snapshot clone前停止 |
| 具体卡范围/预算 | [本地16项CPU控制](../reports/wc_rv0_restore_scope_cpu_20261004.json)通过，拒绝删场景/后缀、换step/动作、改copy cap/超时、假标签或完整RV0标志及错预算/inflight |

[R1](../reports/wc_rv0_frozen_restore_cpu_r1_20261004.json)182.663841秒在新测试读取 `Inference.generate` 的字符串路径时失败；[R2](../reports/wc_rv0_frozen_restore_cpu_r2_20261004.json)7.863912秒发现新入口把 `stat().st_size` 整数当函数调用。改为Path归一化和属性读取后，以新R3目录完整通过。两个失败不是科学负结果，不覆盖或追认为通过；它们和原件SHA全部保留。没有GPU重试或费用。

## 显存和费用的可核查估算

[CPU host profile](../reports/wc_rv0_host_cost_cpu_r1_20261004.json)在服务器CPU使用已记录QKV元素数与父latent尺寸。父latent `[1,16,24,54,96]` float32有真实历史回执；hidden轴 `[1,24,27,48,2048]` 由31104 token、16×128通道及patching推导，**不是保存的真实WC字段shape**。每个BF16/FP32 hidden分别127,401,984/254,803,968 bytes；三次CPU finite+SHA最大0.599441/1.023549秒，clone最大0.051659/0.140416秒。总CPU profile6.057秒、峰值RSS1,441,173,504 bytes，无CUDA。

官方window在 `len <= 2` 时继续append，实际最多三个槽位；不能按两个槽位估价。把所有逻辑tensor出现计入而不依赖alias去重，WC大tensor最多22项。按FP32估、另给两条件128MiB、小embedding16MiB、solver/output/noise五个latent及712 bytes已记录native buffers，capture代理共**5,796,496,072 bytes（5.398GiB）**。这些条件/小embedding额度仍是假设，现场metadata必须核对。

分叉前现场门要求逻辑tensor副本≤**6GiB**，GPU free≥**2×当前GPU逻辑副本＋4GiB余量**；按cap最坏为16GiB free。副本metadata检查不clone、不hash或转CPU，也不遍历/复制模型权重。两个copy量级覆盖保存副本和restore期间副本，4GiB另留瞬时final快照、有限性检查等。它是条件准入和停止门，**不是真实总峰值上界**；实际GPU峰值、D2H/H2D和每段完整wall仍须在首次诊断记录。

[3900秒费用预案](../reports/wc_rv0_restore_cost_proposal_20261004.json)明确六个完整视频费用等价代理，不按剩余14步折扣。原known项含加载/余量/释放为2988.379秒；从当前fork源码操作次数和FP32 host max构造CPU proxy468.646秒，额外给未测GPU传输/上下文/IO等231.354秒，总增量700秒再乘1.2。条件总估算**3828.379秒**，拟单次完整wall **3900秒**、child3870秒、kill5秒、释放余量30秒。

这些proxy不证明GPU完成时间上界。硬超时限制预算风险，但不能保证届时完整四后缀和两个视频都完成；失败必须保留原分母、已有产物和实际费用，不自动重试。当前scope/core/成本已可审查，独立生产runner/监督器、source冻结部署、实际资产/import/官方prepare/native-meta门和fresh UUID/VRAM/apps/全局锁/余额准入仍待完成，**配置selected=false、预付与提交0**。

原服务器账本经本轮独立审计仍**10.713586944446/12GPUh、44jobs**，无inflight，余**4631.087秒**。3900+15秒单独算术可容纳，原4500秒动作/Native草案不与本卡共同承诺，后序按实际结算退款重算。104点单次授权及全部旧终态run保持，不复用身份或1800秒授权。下一先具体化该恢复与成本诊断的独立执行器和部署门；真实GPU恢复通过后才决定C/D收益采集，不引入人评或付费评分。
