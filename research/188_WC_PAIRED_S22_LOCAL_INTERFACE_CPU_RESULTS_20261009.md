# 同S22成对接口：完整CPU父轨迹与恢复集成通过

2026-10-09。**真实成对执行的接线进一步完成：临时解除父轨迹forward／denoise包装，原顺序与两侧浅层先行的同动作输出、状态和后续父轨迹一致。** 这是下一次2B接口／显存／成本测试的实现准备，不是新的模型质量、速度或终点收益结果。

## 目标、方法与设计

Common完整结果支持两CFG误差抵消；真正共同选择动作时，需要先拿到两侧的浅层信息。H-T57a在本轮实现和CPU执行前登记：同一个原实际S22状态的CC／DD，原顺序与成对顺序应保持分支、原FP32 guided输出和状态一致，观察开关、严格重复和父轨迹继续也应一致。

新`PairedLocalInterface`复用原完整状态及冻结条件恢复，显式替换本卡持有的函数包装，退出时恢复原对象。两侧浅层均运行后，选择器只收到不可变的paid-probe统计；CC只走浅层，DD两侧完整运行。每行只测当前速度，不更新solver、不改父latent、不写teacher入父轨迹；局部计时包住同步的当前速度和可选观察，clone／恢复／写盘在外，仍包含层hook和控制开销，不能充当无仪器部署延迟或未来成本标签。

完整范围不缩减：原H-T55的60行控制重跑；新flow OFF／ON各两完整原父、每父36实际UniPC更新／72 net，到latent。在每条ON父的实际S22／44调用，同CC／DD×局部观察OFF／ON×两严格重复×两执行顺序＝16局部pair／8比较；两flow共32pair／16比较。新增每flow的selector异常与首分支观察异常，共4声明覆盖的失败恢复，然后原父继续到终点。首次H-T55尾部控制不同的旧失败和旧回执保持。

实际服务器使用Torch、原WC／RF生产模块和源固定UniPC；模型权重、attention、conditioner构造、noise／规范化等仍是已声明Toy CPU。完整到latent，未调用VAE／writer或生成视频。

## 实际结果与证据

冻结source **0f6dbac3a7e5c99a5ed8dcf28910254b64163286**，75载荷／8上游源；独立stage `.sync/wc-cfg-paired-local-interface-cpu-r1-20261009`。CPU supervisor3441993／child3441994均退出0并消失，driver **206.954659秒**／fixture **180.055308秒**。新GPU提交0、CUDA未初始化、权重加载／下载禁止，预算前后原字节SHA相同。

| 完整检查 | 已确认结果 |
| --- | --- |
| 原H-T55范围 | 60行、完整24比较／48父、尾部动作／逐步状态、重复／观察及旧故障全部重新通过 |
| 新同S22比较 | 两flow各16pair，CC／DD两顺序、两观察、二重复全量通过 |
| 分支与guided | 服务器直接`torch.equal`核对，跨顺序／观察／重复均逐值相同；本地核对全部原摘要和集合 |
| 两侧浅层与实际层数 | 选择时仅两侧probe已经支付；Toy CC访问[2,2,0,0]、DD[2,2,2,2]，仅两不可变统计包输入 |
| 原函数与恢复 | 每行恢复原forward／denoise／scheduler函数对象，50状态组件／条件／RNG／generator／参数版本保持 |
| 新四完整父 | 144更新／288父net；OFF／ON全部72输入与输出、36速度／solver、五检查点及最终latent一致 |
| 新四声明故障 | selector及首观察器失败拒绝，executor中毒，原状态与绑定恢复后父继续；不承诺任意故障回滚 |

完整顶层64行及嵌套32pair／4失败无遗漏。独立原字节捕获核对了全范围、观察事件、paid-probe、顺序／重复／开关摘要和两完整父；本地未第二次加载Torch张量。CPU成功属于实现证据，不能把64行当64个独立科学样本。

## 继续推进

下一步准备独立真实2B单S22接口卡：两原完整父／视频、CC／DD×观察OFF／ON×二重复＝8原／成对比较、16局部pair，保留原FP32分支张量、完整条件／状态、原父非干扰、显存与真实费用。先做生产配置／资产／源绑定的实际CPU，再以旧完整实费和新collector开销构建整卡成本；当前尚未选择或提交新GPU，1.2905h草案不直接准入。

完整单次≤2GPUh且50GPUh有余额后自主执行；超过2GPUh具体确认，不缩拆旧冻结卡。之后取得终点刷新价值及真实未来成本，与原生WC、简单共同刷新和正确校准RA基线比较。全36步候选策略的GPU一致性、质量—时间前沿和独立CONF仍待；不训练Head／LoRA、不扩稀疏或切换OMR／DRE，不引入人工评审。

Common完整机制结果与组会文档保持最新科学证据；累计仍为**29.027073215／50GPUh、余20.972926785GPUh、64历史GPU提交，无本轮新增GPU**。本轮完整实现、实际CPU执行和原件独立核对是新进展，长期goal active。

- [执行前设计](../plans/WORLD_CACHE_PAIRED_LOCAL_INTERFACE_CPU_20261009.md)
- [冻结75源与完整范围](../manifests/wc_cfg_paired_local_interface_cpu_r1_preregistration_20261009.json)
- [原CPU派发](../reports/wc_cfg_paired_local_interface_cpu_r1_launch_20261009.json)
- [完整捕获与独立核对](../reports/wc_cfg_paired_local_interface_cpu_r1_terminal_20261009_capture_and_independent_audit.json)
- [Common完整科学结果](187_WC_COMMON_COMPLETE_CFG_MECHANISM_RESULTS_20261009.md)
- [飞书组会报告](https://lcnssrlun9lz.feishu.cn/docx/HTSIdK0uLofCG5xUI1IcTKaCnAh)，revision18完整科学正文和原阶段结果已回读验证；本CPU准备不冒充新科学收益。
