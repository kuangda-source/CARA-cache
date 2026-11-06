# 成对probe生产接口CPU通过：实际全局绑定与显式观察补齐，2B一致性／成本仍待

2026-10-09。**本轮补齐了两个真实集成缺口：RF与WC各自的实际全局对象绑定，以及不会被编译函数体绕过的明确观察入口。** 已完成全范围CPU控制，为同动作的真实模型接口与成本实验做准备；原Common完整确认继续，没有新增GPU或修改其95源。

## 问题、方法与完整设计

H-T50的成对prototype保存原函数局部变量，让两侧浅层先完成，再共同选CC／DD并续算。它直接调用编译函数体，而已有采样记录是包装`net.forward`和`model.denoise`属性，不能假设这些包装仍会执行。Toy公用namespace同样不能默认代表实际RF／WC模块。

[H-T54完整登记](../plans/WORLD_CACHE_PAIRED_PROBE_PRODUCTION_CPU_20261009.md)的新编译器在原SHA／路径核对后，分别绑定实际导入WC／RF模块的所有LOAD_GLOBAL对象。WC／RF逆AST检查保持，原body只改变原决策暂停与net调用位置；上游文件不写。生产executor拒绝非原绑定的forward／denoise属性及既有外部net／global hook。输入和输出通过独立观察入口记录，选择器仍只收到两份PaidProbe，不获得当前深层教师。

两种执行顺序的观测时序如实不同：原顺序beforeC→afterC→beforeU→afterU；成对有效路径beforeC→beforeU→afterC→afterU。按分支比较输入／输出摘要，**不要求中间全缓存状态或日志时间顺序相同**；最终WC字段、buffer、输出、原FP32 CFG、RNG、计数和访问数仍须一致。

| 预登记CPU范围 | 实际终态 |
| --- | --- |
| flow OFF／ON，各22次更新建立双CFG缓存 | 两配置均完成，主起点计数44 |
| CC／DD×两重复×两flow | **8／8**原顺序与成对顺序主比较一致 |
| 初始化保护DD | **2／2**，不调用选择器 |
| 原4失败×两flow | **8／8**拒绝并poison，原控制保留 |
| 新4失败×两flow | **8／8**拒绝并poison |
| 每分支显式输入／输出观察 | 全8主比较一一相同，原时序各自保留 |
| 实际函数原路径／WC17个与RF2个全局名称绑定、逆AST | 两源契约行均通过 |

新失败为forward属性包装、denoise属性包装、第二侧before观察抛错、第一侧after观察抛错。失败后整个CPU副本弃用，不声称任意实际模型完整回滚。模型权重、attention、条件构造和父采样均为声明Toy；实际官方函数体及模块全局对象不等于真实2B推理。

## R1失败、修复与实际证据

R1 source `ce0cec45c669937fdeae264c0a4f1f2b6efb40a9`，原3431166／3431167已退出；61.894640秒，在RF导入链的Qwen `flash_attn_2 not available`断言停止，没有进入8组主比较。原源、失败、全范围与日志已[封存](../reports/wc_cfg_paired_probe_production_cpu_r1_terminal_20261009_capture_and_independent_audit.json)，CUDA未初始化、新GPU0。

只读核对FlashAttention实际已安装**2.6.3+cu128.torch27**。Transformers辅助函数还要求CUDA可用，因此CPU隐藏设备时返回false。R2复用此前[实际条件类CPU导入检查](../scripts/check_wc_rv0_video_condition_import.py)的退出子进程适配：按已安装包元数据允许导入，给未用构造默认值提供ordinal0，恢复原HF辅助函数和current_device后才执行Toy测试。CUDA硬件可用性未改变，权重加载／CUDA初始化／Triton执行被拒绝。它不是FlashAttention CPU执行、GPU能力验证或上游源码修补。

R2 source `006a6c6f9ad207c413aebea0edde10e1461828fa`在独立目录`.sync/wc-cfg-paired-probe-production-cpu-r2-20261009`实际执行；原3432494／3432495退出exit0。完整driver **32.203525秒**，fixture **4.400439秒**，全部28行（8主／2初始化／16失败／2源契约）通过。57载荷／8runtime源和账本原字节保持，没有Torch CUDA初始化、新GPU提交或CPU写账本。

[原字节捕获和独立完整检查](../reports/wc_cfg_paired_probe_production_cpu_r2_terminal_20261009_capture_and_independent_audit.json)保存原回执／结果／日志／登记，核对完整动作×重复×flow集合、16失败与poison、全部分支输入输出摘要、最终WC／buffer摘要、原FP32 guided、计数44／45→46与浅深访问数、导入适配恢复。服务器Torch进行了实际`torch.equal`比较；本地为原字节／分组／签名检查，**不是第二次张量加载**。旧R1没有补认通过或删掉。

## 接续与必要边界

这项结果证明声明CPU模型上的生产命名空间和观察方式可用，没有2B视频／显存／全36步或真实速度收益。哈希观察有开销，fixture时间不能换算GPU加速，实际成本还需观察开／关、同动作、相同状态和完整计费的对照。

下一先完成Common H-T52全部2父／5×4×2／两视频及完整审计，再把成对接口接入真实velocity／完整采样路径的CPU同动作控制，核对全状态恢复、条件、求解器和输出记录，然后准备真实模型完整一致性／成本卡。原WC、简单共同刷新和正确校准的RA联合基线仍须保留；本模型rho／传播先验、终点动作收益和未来真实成本标签尚缺，不训练Head／LoRA或运行新策略。

本轮没选择新GPU，不因为单次2h限制删除flow、父轨迹、重复、故障或视频。最终整卡预测超过2GPUh时，完成可审阅CPU准备后请求具体例外；累计50GPUh、旧正负／判据、不扩大稀疏／OMR／DRE／人评保持。总体goal active，本轮实际接口与完整CPU是progress。

## 原Common现场进展

[同原句柄核对](../reports/wc_other_scene_cfg_confirmation_r1_paired_production_cpu_live_20261009.json)确认3426296／3426308／3426297仍活，source c243d30／95载荷／最终配置不变。首OFF父完整72条net／36条solver及视频472,415字节已保存，SHA `cb8b06ab2e3c1af5333bcfab5628e058f83775f36fb4c25222e5263d59f0af6c`；第二ON父暂停于S22，进入自身S23_after_CC动作对照，观察时已6个完整pair，其余原全部范围待。

保存一个父视频或局部pair不代表Common机制确认，未加载在途教师评分或验收成功子集。只跟踪原句柄，不重启／复投或改95源；正常释放后自动完整120张量／20重复／两全93视频、224条件／76solver审计。实费底数27.644682758／50GPUh，第64在途used50只预留，终态全wall结算。飞书revision15完整科学成果与Common执行状态保持，本轮不把接口CPU当论文新结果追加。
