# H-T63：真实完整原生政策接口的实际batch准备

继承[完整真实设计](../plans/WORLD_CACHE_REAL_COMPLETE_NATIVE_POLICY_INTERFACE_20261009.md)，新 `cfg_complete_native_policy_sampling` 实现两个输入×原／成对顺序×观察OFF／ON×两严格重复16条完整Inference.generate路径。源绑定、逐槽原native_cache政策、尾部两prefix、原CFG／完整36求解器和正常decode／guardrail／write保持；每条保留全部36个实际FP32 guided及最终latent文件，五完整状态／条件／RNG／分支层访问／动作／全视频记录，退出恢复原初始状态及方法绑定。观察开启使用显式回调，不让outer net wrapper绕过新接口源检查。所有费用带诊断，不宣称干净部署速度。

新batch验收从完整矩阵和实际文件出发，而非仅若干输出SHA：重读全部guided／latent直接torch.equal；完整动作、状态、输入准备、观察及重复覆盖。CPU低成本新增两flow，每flow完整成功batch16路径，再完整16路径最后向量写出失败；共4行／64完整路径／2304solver4608net，成功32路径1152 guided与32 latent实际重读、24记录破坏拒绝及2实际文件截断拒绝，2最后写出失败保留全部范围。旧H-T62全20、H-T60全112、H-T61负控制按未改源／回执SHA复用，不重跑未变整批。

当前是实现与执行前登记阶段，服务器实际新batch CPU及独立原件验收待，不是生产CPU、真实2B完整部署或新算法收益。新GPU0、CPU不写账本；50累计和单次2GPUh权限保持。完成实际新batch CPU、生产源资产／评分审计、整卡费用和资源后，再请求>2GPUh具体授权，不缩拆范围／训练／扩稀疏／OMR／DRE／人评。
