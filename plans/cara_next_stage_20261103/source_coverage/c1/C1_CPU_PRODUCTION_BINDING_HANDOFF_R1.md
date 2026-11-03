# C1 生产接线承接

> 当前执行状态：原166位置方案暂停。新的零GPU核验、预算优先级与19D条件草案见 [R2审阅](C1_REDUCED19_PROPOSAL_R2.md)。本文保留原范围历史，不继续据此接线或派发。

C1 的科学范围、候选生成、完整 FIT 选择与采集恢复已形成可审阅实现；生产接线沿用已验证的原生命周期机制，将本卡166语义／60正式质量位置明确绑定到新的入口。此文档不创建运行、预约或启动授权。

## 已完成的接口

- [卡片](../../../../src/wcomr/cara_source_coverage_card_r1.py)固定同8候选来源比较、同3候选阶段比较、19D/22D和166完整分母。
- [采集器](../../../../src/wcomr/cara_source_coverage_collection_r1.py)通过现有请求与评分回调执行、独立搜索命名空间、封存选择和无新回调恢复。
- [执行资源草案](C1_EXECUTION_PROFILE_DRAFT_R1.json)与[完整报价](C1_WHOLE_QUOTE_R1.json)已有对应范围，尚未形成生产执行授权。

## 要完成的组合

| 接线位置 | C1 的具体要求 |
|---|---|
| runner / service 的卡片与来源绑定 | 使用 C1 validator、166范围及独立新运行身份；不复用原 P1 固定146身份 |
| 内部 FIT broker | 将本卡56 cohort上界和独立搜索 query namespace 同时接入队列、请求校验、恢复和操作计数；原 P1 的42上界默认值保持 |
| guardian / 准入 | 将建议15GPUh、50GiB启动、40/8GiB无swap、每查询新鲜12GiB、90C、600秒释放余量绑定本卡；实际外部状态在启动前核验 |
| released reader | 原终态退出、释放与唯一实耗结算后，读取本卡完整166分母，校验12个身份关系，包括独立搜索Uniform的解码RGB桥 |
| 最终评分与分析 | 15角色×4输入＝60位置；最多24封存FIT复用、最多36新对；全93帧/双时钟/校准实际费用/失败分母完整保留 |
| 一次选择冻结与导出 | 只冻结本卡已封存的FIT选择，不用CHECK重新选择，不重选旧RGB-MSE赢家或覆盖旧冻结 |

对应旧接口为 `cara_source_lifecycle_p1_runner_binding_r1.py`、`cara_source_lifecycle_p1_service_r1.py`、`cara_source_lifecycle_fit_broker_r1.py` 与 `cara_source_lifecycle_p1_artifacts_r1.py`。这些模块的146、42、52/32与原来源身份不能仅改文档后视为接受；新绑定需要CPU组合覆盖成功、真实失败、未知句柄恢复与释放后接受。

完整组合通过后再生成新源包与独立存储回执，提交完整单次启动审阅。现有C1 CPU验证不加载真实Cosmos权重、不生成科学视频，不读取或更改中央账本。
