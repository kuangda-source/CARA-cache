# 完整校准CPU验收与失败结算边界

2026-10-30。用户选择的14GPUh完整SA+HC方向保持；该选择不是GPU启动批准。四卡唯一完整校准CPU已于19:04正常退出并通过验收。本轮没有新增GPU派发、预算预约或中央账本写入。

## 原完整CPU验收

[原终态采集](../reports/cara_budget_calibration_four_card_CPU_complete_capture_r1_20261030.json)绑定18:46:12启动的同一stage、registration和容器，exit0、无OOM，实际1CPU/4GiB/零swap、无GPU/网络、只读根文件系统均符合登记。worker墙钟1037.99秒。

两种flow各完成112设计路径、51次双FIT查询，完整执行SA30与一轮HC20；合计224设计路径、102双FIT目标。每flow另有三个失败场景及前置路径：合计266成功物理路径、6预定失败、272物理尝试。93帧RGB、Native/allD及计时ON/OFF的CPU RNG一致性、完成恢复0新增生成均通过，原21项校准/生命周期控制通过。

这是tiny CPU模型的生产采样路由证据，不是真实权重、GPU速度或视频质量结果。两卡尚未执行这一完整组合，S优先保持，不能标为双端或GPU整卡接受。

[发布源复核R2](../reports/cara_budget_calibration_four_card_CPU_published_source_revalidation_r2_20261030.json)明确绑定实际运行版本`e31cc212836882e80f835bec0f0c9016a07b30af`。验收器支持完整不可变commit SHA，拒绝HEAD等移动引用；同一原证明不赋予后来修改的生命周期分支运行证据。原验收与R1复核保留，未重跑完整校准。原B36的62份关键源仍保持。

## 失败分支的独立修订

guardian若在尝试获取任何资源之前失败，不能依靠缺失锁文件推定释放。新验证分支仅在源绑定的明确见证证明未尝试模式锁、设备租约、模式修改或容器派发，并且不存在CLI/supervisor/runner、存在原错误与费用时，允许验证原费用结算。任何尝试、矛盾或缺失见证继续拒绝；不会解锁他人资源或将失败报告为执行成功。

[本地27项控制](../reports/cara_budget_lifecycle_preallocation_and_source_pin_local_CPU_r1_20261030.json)全部通过：生命周期15、只读采集7、完整校准验收器5。使用临时文件、合成身份与临时账本；新分支的实际Linux delta、生产guardian持久化见证生成器仍待，不将这27项写成原完整CPU已执行的测试。

## 完整费用与存储准备

[64GiB存储核算提案](../reports/cara_budget_14GPUh_storage_scope_r1_20261030.json)纳入112份RGB NPY、每路径128MiB生成文件额度、身份与结果、日志和源、单请求临时空间及失败余量，总计约58.98GiB，剩余约5.02GiB。旧FIT视频最大1,313,063字节仅为历史参考，不是未来上界。每路径额度与专用硬配额尚未实施或准入，不能称为已验证存储上界。

下一步复用原完整CPU结果，单独验证受影响生命周期路径；接通GPU guardian/只读采集、存储硬限制和完整科学验收，完成双端CPU与整卡报价，再提交超过4GPUh的单次启动方案审批。14GPUh下初始1+SA30+HC20共51次双FIT查询、112完整物理路径仍为设计候选，规划12.53GPUh不是实测整卡上界。
