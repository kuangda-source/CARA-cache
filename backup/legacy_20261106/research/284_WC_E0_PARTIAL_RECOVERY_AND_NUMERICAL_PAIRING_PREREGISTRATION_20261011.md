# E0：原64已保存路径的CPU回收与配对合同

2026-10-11。在[283更新设计](283_WC_REVIEW_RECONCILIATION_AND_NEXT_DESIGN_20261011.md)范围内自主推进，独立CPU任务，不重投GPU、不改原卡。原完整64保持技术失败，14完整、1部分失败、49未开始与1.507741092GPUh原费用保持。

## 本次已有的新发现

14个完整行均可通过原逐路径动作、来源、D锚点、A读出、四检查点及当前P创建规则的元数据验证。原整批验证器的**逐行循环完整复用**，只隔离整卡数量约束；并未宣称原完整32／64验证通过。文件／真实tensor／视频还需服务器实际CPU审计。

原严格Native配对检查在14行均不通过，原因分为三类：

1. 全部新路径与旧Native的`gt_frames`哈希不同；除此之外的条件字段哈希一致。当前请求是T2V，两个分支的实际条件视频mask均为全零，finite=True，形状一致。冻结RF只在mask乘法处使用gt；冻结Minimal网络删除额外kwargs。原条件hash函数要求tensor有限。
2. 求解器原始配置的`_use_default_values`记录顺序不同，影响raw_sha256；**已记录的numerical_values／numerical_sha256一致**，没有数值参数变化。
3. Human请求在第七方法失败后，没有保存请求级prepared_input_calls，已有六完整行仍缺准备输入取证。该字段不得补造，缺失继续保留。

另外，新SOURCE_RA与旧已接受32卡RA在AV28、Human的36个guided哈希、最终latent哈希及视频文件哈希完全相同。这是目前基于已捕获原件的桥接事实；新CPU仍须核对真实文件和全部tensor，不单凭这条事实取消配对要求。

## 评分前登记的新数值配对规则

保留原严格逐字段比较的结果、所有不同字段与原raw配置，另记录数值等价判据：

- 当前与Native两CFG的mask均为全零且有限、形状一致，且冻结RF／网络／条件有限性源码hash及数据流检查通过，才可忽略**唯一不参与计算的gt_frames**字段差异。
- 所有其他条件字段、prepare调用参数／prepare数据、前七真实dense guided必须相同。非零mask、活跃条件变化、缺prepare均拒绝。
- 原solver raw／numerical字段结构及两个哈希必须可重建；只比较原numerical_values和numerical_sha256、默认名集合。只规范化取证记录顺序，绝不改真实solver或状态；未知字段／数值变化拒绝。
- 文件与tensor、全93帧与PTS、原Native绑定、实际LPIPS资产分别验收。保真协议和LPIPS归一化不变。

按当前原件，AV28八行可进入新数值配对检查；Human六行保留文件／来源有效性审计，但prepared证据仍缺失，**不评分**。最大评分8×93=744帧距离，原64全部位置照常输出。不是修改原评分器gate，也不是用8行宣称64成功或跨场景推广。未看新视频LPIPS，规则先于评分固定。

## CPU范围与结果要求

14个完整文件包全量检查36 guided＋final（共518 tensor）；14新视频与4匹配Native全解码。已有可用的RA/noP、CPD/OFF、CPD/full-GEMM参考两场景共六轨迹对照重读实际tensor。全部64位置标为已验证、无效、部分失败或未写；不补零，不删异常方法。

指标使用原CPU FP32 AlexNet LPIPS、原reader、同资产身份，CUDA不可初始化、下载不可执行。新输出只写独立`.sync/wc-full64-partial-recovery-cpu-r1-20261011`；原失败stage、模型、运行源、配置、产物及账本只读。CPU单进程两线程，不占GPU槽，不引入人评。

[元数据CPU控制](../reports/wc_full64_partial_recovery_metadata_cpu_20261011.json)在实际捕获receipt上验证14行／64分母与8数值配对候选；6种坏路径、4种坏配对拒绝。这里的源数据流证明fixture不是服务器实际证明。开发时最初派生器漏了`rows`局部赋值，随后发现solver还含嵌套raw默认名和raw_sha，已修复并保存原因；不把这些实现调试当科学负结果。

具体只读CPU登记见[manifest](../manifests/wc_full64_partial_recovery_cpu_r1_20261011.json)。下一：源码推送、独立CPU唯一部署，核对真文件、条件数据流和数值配对，再评分全部合格八行。E1仅同步进行原代码／回执容量分解，尚无新GPU或修复效果结论。
