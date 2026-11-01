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

## 原R1终态与受影响路径修复

原source `3c8cbe8a70a09cc2708536f2ad23acfc1309cbf3`的两卡CPU在06:44:07启动、06:46:43退出1；[原终态](../reports/cara_v1_P1_release_Linux_CPU_capture_r2_20261102.json)及[失败记录](../reports/cara_v1_P1_release_Linux_CPU_original_failure_r1_20261102.json)保留。21控制原日志全部通过，随后媒体夹具未创建`outputs/<run>`父目录，尚未开始媒体回读或新真实评分；不能宣称完整CPU接受。修复仅在新夹具增加输出父目录，实际生产输出原由storage/init创建。两个旧检查已删除。

新增输入等权分析和原FIT计划一次冻结接口，通过4项本地控制：FIT/已曝光CHECK/四旧CAL分表、两时钟与93曲线、原实际校准cap和未结束HC分母、原FIT选择不可由CHECK重选、重复相同冻结保留原字节。它还未接正式生产CLI/图表，不是方法结果。

R2只运行原R1尚未到达的真实文件/新后置评分及4项分析控制；原21项以原失败容器的完整日志、注册source/SHA和终态复用，不重放。新[精确1412文件包](../reports/cara_v1_P1_release_packaged_local_CPU_r2_20261102.json)在隔离目录通过4项；其真实Linux终态仍待。内部host/内部指标明确模拟，真实host证据继续复用848。

补充：新P1容器命令与原supervisor接线已有4项本地控制，见[回执](../reports/cara_v1_P1_container_local_CPU_r1_20261102.json)，Linux生产worker仍待。R2在首次CPU派发前完成了合成启动回执admission SHA复核；原源码块传输已停止，保留[未派发记录](../reports/cara_v1_P1_release_R2_transfer_stopped_before_launch_r1_20261102.json)。新源包仅复制原R1控制的紧凑证据并只读绑定原stage，避免重复传输其1406文件注册表。原R1不变，未重派原CPU。

R2原CPU在06:58:37退出1，完整失败发生在合成账本schema，尚未运行新指标；[原件](../reports/cara_v1_P1_release_Linux_CPU_original_failure_r2_20261102.json)保留，两检查删除。夹具现复用真实`SCHEMA`常量，3项纯metadata释放/结算控制通过。R3新精确包在隔离目录通过4分析＋3夹具控制；旧21原控制继续只按原source/日志复用。GPU、中央账本与旧实验均未启动/访问/重派。
