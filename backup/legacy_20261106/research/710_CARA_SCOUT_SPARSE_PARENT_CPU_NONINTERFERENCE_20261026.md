# E1完整稀疏父轨迹采集与无干扰CPU控制

本地新增Shared25-C采集owner，接通六预登记状态、两真D锚点、同状态dense oracle和六读出。完整36步采集开关控制已通过：8条小模型CPU路径、24状态、144读出位置；逐步guided、最终latent和模拟视频均逐位相等。实际噪声网格绑定原CAL66，P0 teacher/P1原生head重放/P2实际C输出等价均通过。

完整入口暴露了小张量测试没有覆盖的teacher投影适配边界：使用已有只读teacher模式并恢复整个owner状态后解决；原始失败保留。两种flow共6次中断/最后写盘/内存限额故障检查通过，原错误没有被清理误报覆盖。最终证据与生产边界见[准备说明R2](../plans/cara_predictor_refresh_scout_v2_20261026/E1_PARENT_COLLECTOR_PREPARATION_R2.md)和[R7 CPU回执](../reports/cara_scout_parent_CPU_v22_r7_20261026.json)。

当前通过的是源码精确路径加小模型替身的本地控制，不是实际权重或双服务器整卡验收。下一步准备去重writer、真实冻结请求/双端生产CPU及完整报价；当前快照会重复存储大张量，旧64GiB容量只作历史规划，尚不能准入。新资源补充另存，不覆盖旧草案。

本轮无服务器操作、无GPU提交或预算预约；DEV128的原源码、launch、资源预约、半程和全程验收安排均不变。没有读取部分科学结果，也没有调整alpha、强基线或部署预算。
