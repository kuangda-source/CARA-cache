# E1第一步：附加状态CPU存储的独立等价控制

2026-10-11。在[当前E1设计](../plans/WORLD_CACHE_A_CONFIRMATION_AND_P_RECOVERY_20261011.md)范围内，先测试最小存储部件，再接真实owner／sampler；不修改旧完整64、保护门槛或部署方法。

## 要检验的具体修改

新`CPUOwnedStateImage`按唯一untyped storage直接复制到CPU，记录原device，恢复时每storage仅重新分配一次。原值、dtype、shape、stride、storage_offset、重复Tensor对象、Python容器与storage别名均须保持；快照与live状态、两次恢复结果之间必须独立。只支持普通无梯度strided CPU／CUDA张量；拒绝未知状态类型、循环、稀疏、量化和非有限tensor。

源GPU storage不先作GPU deepcopy；hash必要的短暂contiguous／CPU传输仍单列，不能声称所有取证峰值消失。只冻结Torch2.7.1+cu128，storage._cdata作为当前版本alias标识，CPU控制验证它在wrapper／view／零storage下的行为，不承诺其他Torch版本。

`CPUDeploymentRoundtrip`保持原owner健康、installation／parameter version、完整状态fingerprint与原logical cap；CPU唯一storage另有明确cap。该新类**尚未接入CurrentBirthSamplingOwner**，原physical RNG／solver快照不改，原GPU guard不改。CPU通过只代表这个存储部件的值与别名合同，不是原第12步问题已修复。

## 本次受影响CPU范围

固定四个正控制：①转置／切片／stride0／scalar／跨dtype视图／重复对象／metadata和NumPy独立性；②重叠view的24后续更新，与原正常状态相同；③对照原DeploymentRoundtrip，在状态／history扰动后恢复，后续算术相同；④不消耗Torch／Python／NumPy RNG。

固定十一拒绝：poison、parameter修改、installation修改、logical cap、CPU storage cap、requires_grad、非有限tensor、未知对象、稀疏tensor、循环状态、已保存image污染。fixture含实际ProjectionCache dataclass和D历史／P工作源／A与head字段；不是Cosmos真实owner或GPU数据。

真实CPU使用服务器已有pinned Python，两线程、CUDA不可初始化、下载禁止、独立stage；不得更改模型／Torch／旧源／账本。源推送后登记payloadhash，独立一次执行，保留错误及结果原件。GPU0、视频0，无人工资源。

## 后续必须补的验证

1. 将新类绑定到独立CurrentBirth owner版本，保留算法与物理执行原字节，受影响CPU完整恢复／poison／来源／head／solver／RNG控制。
2. 明确physical快照、physical恢复、own恢复的先后容量账，观察actual allocated／reserved／free与唯一storage，按剩余待执行复制保留workspace／prefix reserves。不能降低旧保护来掩盖峰值。
3. 冻结失败方法冷启动及预先指定短前序后的完整GPU范围／费用，按≤4自主／>4完整确认执行。只在真实等价与容量结果成立后进入E3复用／补齐原64。

[285新增单场景保真信号](285_WC_E0_REAL_PARTIAL_RECOVERY_RESULTS_AND_MEMORY_NEXT_STEP_20261011.md)保持，不因CPU部件通过就称P成本或生命周期问题解决。阶段A独立确认同步准备。
