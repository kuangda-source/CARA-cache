# N10共用模型构造与逐维评分准备

2026-10-16。**CPU模型验证与正式评分现在共用同一份模型构造代码，相关54项本地CPU控制通过。** 新工厂可接入513完整960位置批处理，逐维加载、推理、释放；尚未执行真实五模型验证或质量评分。

## 本轮接线

新增[`automatic_quality_models_r1.py`](../src/wcomr/automatic_quality_models_r1.py)，提供原DINO、AMT-S、RAFT-Things、ViCLIP和MUSIQ-SPAQ构造入口。CPU探针直接调用该入口，避免CPU验了一份模型构造、正式评分却使用另一份。模型源码、五套固定权重、原BPE、FP32/eval/关闭梯度及原采样定义保持。

- DINO先构造原本地ViT-B/16结构，再严格加载指定检查点，避免依赖Hub默认下载/缓存路径；没有训练或改换检查点。
- AMT和RAFT保留原wrapper、配置与精度设置；AMT单次插值和RAFT20次迭代仍由原评分器执行。
- ViCLIP保留原模型与词表；MUSIQ保留原PyIQA0.1.10、架构SHA与固定SPAQ权重。
- CPU输出新增实际共用构造源码SHA。原独立接受器逐角色核对并传递此证明，新工厂要求五角色全部接受、相同构造SHA和实际参数数量。
- 工厂在原模型CPU接受后检查每份已登记源码、当前权重和词表，拒绝混入已安装的其他VBench代码。各维共享同一已登记源码/缓存位置，推理放在inference模式内。
- 每个上下文完成后清除模型、wrapper和tokenizer引用并回收；GPU上下文还同步并回收空闲分配块。释放失败时不能继续加载新模型。

五模型CPU部署包已纳入共用构造及其评分依赖，模型CPU矩阵仍为原五角色，未缩减。真实部署仍待主线空档、原完整资源及新的Git绑定阶段。

## 验证范围

54项全部通过：新工厂10、导入前边界5、原生工具4、逐视频入口8、完整960批处理11、模型bundle/部署/独立接受16。

新控制验证了固定构造参数、严格DINO加载、推理模式、模型逐个释放、源码/权重变更拒绝、五模型证明不足拒绝、已安装VBench混入拒绝，以及工厂实际驱动全部960合成位置（800可评分＋160静态不适用）。独立CPU接受器的新构造SHA分支同时验证全五接受与单角色不一致保留。

首版只有Mac临时目录`/var`与`/private/var`别名的测试预期不一致，生产工厂已规范化；原失败与测试源保留，夹具统一真实路径后通过。R2相关51项先通过，增加全批处理接线和新证明分支后R3为54项。

这些测试使用微型Torch参数/合成检查点和显式模块、评分器替身，未运行原指标模型前向、真实视频或codec。54项不是五个真实模型的CPU接受，更不是质量或加速结果。原真实五模型CPU、生产评分驱动/完整费用和GPU卡仍未完成。

## 提交后的打包复核

在构造代码提交`420b003`后，实际构造并展开232份本地CPU部署payload，逐份SHA与Git绑定复核通过，其中12份项目源码、216份固定官方代码以及原词表、资源元数据和引用。另12份DINO服务器缓存源码仍由原部署入口按既有SHA复制，未在本轮远程执行。

在独立临时目录、禁用site-packages的Python中，仅使用展开包导入新工厂/评分入口/原接受器成功，Torch和NumPy均未导入。该检查的资源回执是显式合成元数据，只验证包接口和依赖闭合，不证明真实ViCLIP已收到；没有调用SSH或派发CPU模型。

## 当前接续

N10资源仍按原source`129577b`/PID19489，**今天15:50一次收**；本轮未提前查看。原N07/source`140d0a6`完整180不变，**今天21:30半程技术检查、明早05:30完整验收**。主线N07→N08→N09/10，重模型CPU避开主线生成/重复clean测速。

本轮0SSH、0新GPU、0服务器/账本写入；同一累计cap113与原origin保持，F/B关闭，无训练、OMR或人评。新增工厂不授予GPU权限；正式评分仍须完整生产CPU、整卡费用、预算余额和UUID锁准入。

原件：[232包与隔离冷导入](../reports/wc_paper_N10_shared_constructor_packet_and_cold_import_CPU_20261016.json)、[54项CPU](../reports/wc_paper_N10_shared_constructor_factory_related_CPU_R3_20261016.json)、[R2的51项](../reports/wc_paper_N10_shared_constructor_factory_related_CPU_R2_20261016.json)、[原夹具别名失败](../reports/wc_paper_N10_shared_constructor_factory_CPU_R1_20261016.json)、[514两次检查安排](514_WC_N07_MIDPOINT_HEALTH_CHECK_AND_FINAL_COLLECTION_SCHEDULE_20261016.md)、[513完整批处理](513_WC_N10_COMPLETE960_BATCH_CORE_AND_INTERRUPTION_JOURNAL_CPU_READY_20261016.md)。
