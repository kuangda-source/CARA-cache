# W3原生响应起点：新接口与受影响CPU验证

2026-10-07；接续已完成[148真实尾部响应结果](148_WC_W3_NATIVE_TAIL_RESPONSE_CPU_AND_EXECUTION.md)。上一轮完整GPU、终态审计和五终点损失均已结束，原句柄不重启。本轮依[v5.3计划](../plans/WORLD_CACHE_NATIVE_RESPONSE_ONSET_WINDOW_20261007.md)和[事前H-T36登记](../manifests/wc_w3_native_response_onset_r1_preregistration_20261007.json)比较共同61/63交换后65/67/69起点的原生响应，不扩训练、稀疏或人评。

## 当前实际进展

已实现六份独立新源：窗口控制、完整后缀执行、完整轨迹/状态审计、严格范围、CPU夹具和CPU执行入口。旧H-T35/R2代码与实际stage未修改。新范围和全部文件语法/SHA本地检查通过；**实际服务器CPU R1失败已保留，独立R2及原件审计已通过；新生产CPU配置已绑定，GPU尚未提交**。本地解析和纯范围检查不是CPU采样、真实视频或科学收益。

四模式FIXED61/LATE69/RESP65/RESP67保留同一61/63交换和22更新快照；FIXED保持20/18，响应只在登记窗口执行已付probe的原生建议。窗口内容/起点绑定不可变seal，原own-CFG缓存/年龄/有限性检查和70 reset/71–72 full保留，无当前teacher或配额修补。1父/10完整后缀/6编码/两主要比较及全部重复不缩减。

每次真正到达32/33/34更新时保存pre65/pre67/pre69完整latent/cache/solver/RNG/buffers/modes及自身CFG历史。四模式pre65、FIXED/LATE69/RESP67的pre67、FIXED/LATE69的pre69分别连同第一可变调用的输入严格比较；窗口以后的状态独立演化。OFF必须匹配完整父轨迹，全部first/second原始轨迹与终态严格核对。

新的实际CPU只调用受影响接口，复用192份已冻结基础源/九份上游，不复跑旧独立CPU或视频评分。夹具计划覆盖真实固定采样器/缓存/Video2World条件路径的三个完整CPU父、30后缀、18 mock写出，明确改变三窗口的动作；另记录非法own历史、窗口seal变更、非法起点和写出失败，检验完整恢复及失败分母。篡改两个重复使其仍相等，再核验窗口外动作、三个前缀状态/输入/历史、时间顺序与引用等破坏拒绝。**这些计划数尚待实际回执，不代表通过；mock写出不是视频。**

[独立核心CPU绑定](../manifests/wc_w3_native_response_onset_core_cpu_r1_20261007.json)含六份新源SHA、192旧源和九上游SHA及账本原件。下一冻结新提交，独立服务器stage执行禁CUDA/权重/下载的CPU；实际原件、退出码、PID退出、源/预算不变及三组真实CPU轨迹随后独立验收。失败保留，不自动重启原identity。

累计17.445531256/24GPUh、52jobs、无GPU在途、余额6.554468744h保持。本轮GPU新增0；下一完整GPU代理估计1.911160444h，不是硬截止，须实际CPU及生产配置/源/资源/锁/全预算准入后重核。完整≤2h按用户既有自主约定执行，>2h只询问该整卡，不缩拆对照。goal active，当前有可推进代码/CPU工作，非审批阻塞。

## CPU R1实际失败与独立修复

source f366fbf、独立CPU R1的driver3110022/child3110023已退出。44.519227秒内实际完成一组nonflow父36更新/72CFG、10完整后缀和6 mock，并保存原始记录；随后“双重复同时清空终态组件”破坏测试被错误接受，使整套CPU检查exit1。属于新审计实现缺口，不是刷新方法的负结果，亦不能将部分采样完成称为整套CPU通过。原失败[回执](../reports/wc_w3_native_response_onset_core_cpu_r1_native_20261007.json)、[原始记录](../reports/wc_w3_native_response_onset_core_cpu_r1_attempts_native_20261007.json.gz)、日志和源均保留；原失败回执最终CUDA标志为PENDING，不改写。服务器账本原SHA不变，无GPU在途/新增。

修复只修改新验证器、夹具与CPU入口：完整组件拓扑及必备状态族、64位hash格式、tree_digest总指纹、终态output与latent绑定分别验证；三个响应边界也必须具有完整拓扑。破坏检查扩充为20种/每成功组，含同步丢组件、伪造总哈希和更新总哈希但错误output。路由、实际响应动作与生成器不改。

[独立CPU R2绑定](../manifests/wc_w3_native_response_onset_core_cpu_r2_20261007.json)复制195份不变源、替换3份新验证源，并绑定R1原始记录SHA。R2先用新验证器和全部20种破坏检查重审R1真实nonflow记录，不重复其采样；再完成尚未执行的flow普通/故意响应差异两组，以及四个故障。覆盖仍为三父/30完整后缀/18 mock，但新执行为两父/20后缀/12 mock、复用一父/10后缀/6 mock；计划60次破坏拒绝。R1失败身份保持，R2只有实际exit0、独立原件/状态/重复/源/账本验收后才能称为CPU通过。

## CPU R2实际通过与生产入口

source d728afa的独立R2已exit0，driver3110803/child3110804均退出，CPU整过程163.328345秒。新执行两组完整父/20后缀/12 mock，重审R1保存的一组父/10后缀/6 mock，覆盖三组而不重复已完成采样；四故障和全部60次破坏拒绝、24个故意改变的原生响应动作通过。独立只读审计重新核验三组原始记录、全部破坏拒绝、旧记录原SHA与内容、全部源/上游/账本及PID退出；实际CUDA未初始化/GPU提交0。修复验证不是新视频效果。

[实际回执](../reports/wc_w3_native_response_onset_core_cpu_r2_native_20261007.json) · [独立审计](../reports/wc_w3_native_response_onset_core_cpu_r2_audit_20261007.json) · [原始记录](../reports/wc_w3_native_response_onset_core_cpu_r2_attempts_native_20261007.json.gz)。此前R1整体exit1保留，不追改为通过。

新生产入口绑定214文件、同一已登记1父/10后缀/6视频/两比较；官方WC/FIXED61/LATE69真实字节桥和三个响应起点完整状态门槛保持。评分复用三份同SHA同93帧协议的旧损失，仅新增RESP65/67两损失，同时报告对原WC、FIXED61和LATE69的保真及实际后缀成本。下一实际draft/contract/validate/import四步CPU和唯一selected复核，未通过前不启动GPU。
