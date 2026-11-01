# P1生产绑定、146原件回读与52质量位置承接

P1已补出生产模型总CLI、固定源/原guardian/内部FIT队列绑定、完整146位置只读索引，以及52个最终质量位置的评分承接。21项本地控制通过，精确1406文件包在隔离目录再次通过同21项；新增真实文件与评分Linux CPU尚待原终态验收。**尚未启动P1 GPU、访问四卡或预约预算。**

## 新增行为

`run_cara_source_lifecycle_p1_r1.py`在原handoff、私有存储、GPU UUID和独占上下文通过后，才导入/加载Cosmos并调用已接受的完整算法。新绑定要求本卡直接审批、全部受影响CPU证据与完整报价；旧P0/M1许可、未定硬限和部分CPU证据均不能启动。固定上游`cosmos_oss/init.py`另有原字节SHA绑定，不修改上游。

完整索引直接读取原once操作，不调用生成、拟合或评分回调。146个逻辑位置包含真实请求、相同策略/输入的质量别名、预算未准入/未到达项。停止后的HC不冒充完成；OFF控制的`T_DD=null`保留，正式比较使用原clean双时钟。

释放后读者先验证原终态、释放和唯一实耗结算，再回读全64标签、每个物理latent/视频/保存的推理参数，以及12个完整latent/93RGB/RNG控制。重新恢复原host FIT返回并逐字节匹配collector已消费的原件；其原指标不计算第二次。五个非Native基线、六个V1预算/估值组合与两个新LPIPS搜索各对应四旧CAL，共52个逻辑质量位置；最多32个独立新对交给新的后置CPU，质量别名不计作独立样本。

新后置worker保持原Fidelity内核、93帧和Alex/PIQ离线权重。缺任一新评分、篡改任一旧行或原评分进程尚未终止时拒绝完整接受。其成功结果只进入完整分析/冻结的下一门，不会自行宣称方法有效。

## 验证与剩余工作

[隔离包回执](../reports/cara_v1_P1_release_packaged_local_CPU_r1_20261102.json)覆盖8项生产绑定、7项完整索引、6项评分门控制；不包含真实视频/模型/指标。新Linux CPU只运行这些新增控制，以及新建合成146原件/全93帧回读与新的最多32对真实Alex评分；已结束的算法R3/实际host broker/guardian组件按原SHA复用。内部host返回在本次文件夹具中明确模拟；真实host组件证据仍来自[848](848_CARA_P1_ALGORITHM_AND_ACTUAL_HOST_FIT_CPU_ACCEPTANCE_20261102.md)。原[849](849_CARA_P1_GUARDIAN_FIT_LINUX_CPU_AND_SNAPSHOT_COST_AUDIT_20261102.md)与旧失败保持。

生产GPU外层dispatch/资源准入/控制、后置评分一次派发/原容器回收、完整分析/图表/一次冻结仍待补齐；当前代码不是完整GPU卡准入。快照费用按[敏感性审计](../reports/cara_v1_P1_snapshot_cost_sensitivity_r1_20261102.json)继续论证，硬限仍为null。全部准备可审阅后，按原规则单独提交完整P1预算和本卡中央事务许可。没有改动146/top3范围、科学门槛、旧RGB-MSE搜索赢家或保护集。
